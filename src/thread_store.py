"""
Thread management for stateful conversations.

This module provides thread-based chat history management for LangChain agents,
enabling stateful conversations across multiple MCP tool invocations.
"""

from __future__ import annotations

import json
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory

from src.state_store import StateStore, InMemoryStateStore, RedisStateStore


@dataclass
class ThreadRecord:
    """Represents a conversation thread with metadata."""
    thread_id: str
    created_at: float
    updated_at: float
    message_count: int
    last_message_preview: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
            "last_message_preview": self.last_message_preview,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ThreadRecord":
        return ThreadRecord(
            thread_id=str(data["thread_id"]),
            created_at=float(data["created_at"]),
            updated_at=float(data["updated_at"]),
            message_count=int(data.get("message_count", 0)),
            last_message_preview=data.get("last_message_preview"),
        )


class ThreadStore:
    """
    Manages conversation threads and their chat histories.
    
    Threads allow stateful conversations where the agent can remember
    previous interactions within the same thread_id.
    """
    
    def __init__(self, state_store: StateStore):
        self._state_store = state_store
        self._histories: Dict[str, BaseChatMessageHistory] = {}
    
    def _thread_key(self, thread_id: str) -> str:
        return f"thread:{thread_id}"
    
    def _thread_meta_key(self, thread_id: str) -> str:
        return f"thread_meta:{thread_id}"
    
    def get_history(self, thread_id: str) -> BaseChatMessageHistory:
        """
        Get or create a chat history for the given thread_id.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            
        Returns:
            BaseChatMessageHistory instance for this thread
        """
        if thread_id in self._histories:
            return self._histories[thread_id]
        
        # Try to load from persistent store
        if isinstance(self._state_store, RedisStateStore):
            history = self._load_from_redis(thread_id)
        else:
            history = self._load_from_memory(thread_id)
        
        if history is None:
            # Create new history
            history = InMemoryChatMessageHistory()
        
        self._histories[thread_id] = history
        return history
    
    def _load_from_redis(self, thread_id: str) -> Optional[BaseChatMessageHistory]:
        """Load chat history from Redis."""
        try:
            if not isinstance(self._state_store, RedisStateStore):
                return None
            
            raw = self._state_store._r.get(self._thread_key(thread_id))
            if not raw:
                return None
            
            messages_data = json.loads(raw)
            history = InMemoryChatMessageHistory()
            
            for msg_data in messages_data:
                msg_type = msg_data.get("type")
                content = msg_data.get("content", "")
                
                if msg_type == "human":
                    history.add_message(HumanMessage(content=content))
                elif msg_type == "ai":
                    history.add_message(AIMessage(content=content))
                elif msg_type == "system":
                    history.add_message(SystemMessage(content=content))
            
            return history
        except Exception as e:
            logger.warning(f"Failed to load thread {thread_id} from Redis: {e}")
            return None
    
    def _load_from_memory(self, thread_id: str) -> Optional[BaseChatMessageHistory]:
        """Load chat history from in-memory store (not persisted)."""
        # For in-memory store, we just return None to create a new history
        return None
    
    def save_history(self, thread_id: str, history: BaseChatMessageHistory, ttl_seconds: int = 86400):
        """
        Save chat history to persistent store.
        
        Args:
            thread_id: Unique identifier for the conversation thread
            history: The chat history to save
            ttl_seconds: Time-to-live in seconds (default: 24 hours)
        """
        messages = history.messages
        
        # Update thread metadata
        thread_meta = ThreadRecord(
            thread_id=thread_id,
            created_at=time.time(),
            updated_at=time.time(),
            message_count=len(messages),
            last_message_preview=messages[-1].content[:200] if messages else None
        )
        
        # Save to Redis if available
        if isinstance(self._state_store, RedisStateStore):
            try:
                # Serialize messages
                messages_data = []
                for msg in messages:
                    msg_type = "human" if isinstance(msg, HumanMessage) else "ai" if isinstance(msg, AIMessage) else "system"
                    messages_data.append({
                        "type": msg_type,
                        "content": msg.content
                    })
                
                self._state_store._r.set(self._thread_key(thread_id), json.dumps(messages_data), ex=ttl_seconds)
                self._state_store._r.set(self._thread_meta_key(thread_id), json.dumps(thread_meta.to_dict()), ex=ttl_seconds)
            except Exception as e:
                logger.warning(f"Failed to save thread {thread_id} to Redis: {e}")
        
        # Keep in memory cache
        self._histories[thread_id] = history
    
    def get_thread_meta(self, thread_id: str) -> Optional[ThreadRecord]:
        """Get thread metadata."""
        if isinstance(self._state_store, RedisStateStore):
            try:
                raw = self._state_store._r.get(self._thread_meta_key(thread_id))
                if raw:
                    return ThreadRecord.from_dict(json.loads(raw))
            except Exception:
                pass
        return None
    
    def list_threads(self, limit: int = 50) -> List[str]:
        """List recent thread IDs."""
        # This would need to be implemented based on your state store
        # For now, return threads from memory cache
        return list(self._histories.keys())[:limit]


import logging
logger = logging.getLogger(__name__)

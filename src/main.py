"""
FastAPI Application - LangChain Agent MCP Server

This module implements the FastAPI application with MCP endpoints.
"""

import hashlib
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import anyio
import asyncio

# Set event loop policy for Windows compatibility with Playwright
# MUST use ProactorEventLoop on Windows because Playwright requires subprocess support
# SelectorEventLoop does NOT support subprocess creation (asyncio.create_subprocess_exec)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Playwright imports (optional - will fail gracefully if not installed)
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

from src.agent import get_agent
from src.config import load_config, RuntimeConfig
from src.policy import evaluate_invoke_policy
from src.state_store import (
    InMemoryStateStore,
    RedisStateStore,
    StateStore,
    TaskRecord,
    now_ts,
)

# Load environment variables from project root
project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Fallback to current directory
    load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Log Playwright availability
if not PLAYWRIGHT_AVAILABLE:
    logger.warning("Playwright not available. Playwright sandbox features will be disabled.")

# Initialize FastAPI app
app = FastAPI(
    title="LangChain Agent MCP Server",
    description="MCP-compliant server exposing LangChain agent capabilities",
    version="1.1.0"
)

# Global runtime config/state
_config: RuntimeConfig = load_config()
_state_store: StateStore = InMemoryStateStore()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class MCPInvokeRequest(BaseModel):
    """MCP Invoke Request Model"""
    tool: str = Field(..., description="The name of the tool to invoke")
    arguments: Dict[str, Any] = Field(..., description="Tool arguments")


class MCPErrorResponse(BaseModel):
    """MCP Error Response Model"""
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class MCPSuccessResponse(BaseModel):
    """MCP Success Response Model"""
    content: list = Field(..., description="Response content")
    isError: bool = Field(False, description="Whether this is an error response")


class PlaywrightSnapshotRequest(BaseModel):
    """Playwright Snapshot Request Model"""
    url: str = Field(..., description="The URL to snapshot")
    use_cache: bool = Field(True, description="Whether to use cached results")


class PlaywrightSnapshotResponse(BaseModel):
    """Playwright Snapshot Response Model"""
    snapshot: str = Field(..., description="The structured accessibility snapshot")
    url: str = Field(..., description="The URL that was snapshotted")
    cached: bool = Field(False, description="Whether this result was cached")
    token_count: Optional[int] = Field(None, description="Estimated token count of the snapshot")


def _mcp_error(text: str, code: Optional[str] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "content": [{"type": "text", "text": text}],
        "isError": True,
    }
    if code:
        payload["code"] = code
    return payload


def _preview(text: str, limit: int = 500) -> str:
    if text is None:
        return ""
    t = str(text)
    return t if len(t) <= limit else (t[:limit] + "…")


def _sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8", errors="ignore")).hexdigest()


@app.middleware("http")
async def glazyr_policy_middleware(request: Request, call_next):
    """
    Policy gate for /mcp/invoke.

    NOTE: We must buffer+replay the request body so FastAPI can still parse it.
    """
    if request.url.path != "/mcp/invoke" or request.method.upper() != "POST":
        return await call_next(request)

    if not _config.policy_enforcement:
        return await call_next(request)

    body_bytes = await request.body()

    async def _receive():
        return {"type": "http.request", "body": body_bytes, "more_body": False}

    # Replay body for downstream request parsing
    request._receive = _receive  # type: ignore[attr-defined]

    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        return JSONResponse(
            status_code=400,
            content=_mcp_error("Invalid JSON body", code="INVALID_JSON"),
        )

    arguments = payload.get("arguments") or {}
    query = arguments.get("query")
    decision = evaluate_invoke_policy(
        query=str(query) if query is not None else "",
        max_query_chars=_config.max_query_chars,
        allowlisted_domains=_config.allowlisted_domains,
    )
    if not decision.allowed:
        return JSONResponse(
            status_code=decision.status_code,
            content=_mcp_error(decision.reason or "Policy violation", code=decision.code),
        )

    return await call_next(request)


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on server startup"""
    logger.info("Starting LangChain Agent MCP Server...")
    try:
        global _config, _state_store
        _config = load_config()

        if _config.redis_url:
            try:
                _state_store = RedisStateStore(_config.redis_url)
                logger.info("State store: Redis enabled")
            except Exception as e:
                _state_store = InMemoryStateStore()
                logger.warning(f"Failed to initialize Redis state store, using in-memory: {e}")
        else:
            _state_store = InMemoryStateStore()
            logger.info("State store: in-memory")

        # Initialize the agent (lazy loading - will initialize on first use)
        # Don't fail startup if API key is missing - will fail on first request instead
        if os.getenv("OPENAI_API_KEY"):
            agent = get_agent()
            logger.info("Server started successfully. Agent ready.")
        else:
            logger.warning("OPENAI_API_KEY not set. Agent will initialize on first request.")
            logger.info("Server started successfully. Agent will initialize on first use.")
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        # Don't raise - allow server to start, will fail on first request
        logger.warning("Server starting without agent pre-initialization")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "LangChain Agent MCP Server",
        "version": "1.1.0",
        "status": "running",
        "endpoints": {
            "manifest": "/mcp/manifest",
            "invoke": "/mcp/invoke"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/mcp/manifest")
async def get_manifest():
    """
    MCP Manifest Endpoint (FR1)
    
    Returns the MCP manifest JSON declaring the wrapped LangChain agent as a tool.
    """
    logger.info("GET /mcp/manifest - Returning manifest")
    try:
        manifest_path = os.path.join(
            os.path.dirname(__file__),
            "mcp_manifest.json"
        )
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        logger.error("Manifest file not found")
        raise HTTPException(status_code=500, detail="Manifest file not found")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest: {e}")
        raise HTTPException(status_code=500, detail="Invalid manifest format")
    except Exception as e:
        logger.error(f"Error loading manifest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks")
async def list_tasks(
    authorization: Optional[str] = Header(None),
    limit: int = 50,
):
    """
    Glazyr monitoring endpoint: returns safe task summaries.
    Never returns raw screenshot/base64 data.
    """
    api_key = _config.api_key
    if api_key and authorization != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid or missing API key")

    limit = max(1, min(200, int(limit)))
    task_ids = _state_store.list_recent(limit)
    tasks = []
    for tid in task_ids:
        rec = _state_store.get_task(tid)
        if rec:
            tasks.append(rec.to_dict())
    return {"tasks": tasks}


@app.get("/api/tasks/{task_id}")
async def get_task(
    task_id: str,
    authorization: Optional[str] = Header(None),
):
    """
    Glazyr monitoring endpoint: returns a safe single-task summary.
    Never returns raw screenshot/base64 data.
    """
    api_key = _config.api_key
    if api_key and authorization != f"Bearer {api_key}":
        raise HTTPException(status_code=401, detail="Unauthorized - Invalid or missing API key")

    rec = _state_store.get_task(task_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Task not found")
    return rec.to_dict()


@app.post("/mcp/invoke")
async def invoke_tool(
    request: MCPInvokeRequest,
    authorization: Optional[str] = Header(None)
):
    """
    MCP Invoke Endpoint (FR2, FR3, FR4, FR6)
    
    Accepts a POST request with MCP invocation payload, executes the LangChain agent,
    and returns the result in MCP response format.
    """
    logger.info(f"POST /mcp/invoke - Tool: {request.tool}")
    
    # Optional API key authentication (NFR2)
    api_key = _config.api_key
    if api_key and authorization != f"Bearer {api_key}":
        logger.warning("Unauthorized request - invalid or missing API key")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - Invalid or missing API key"
        )
    
    # Validate tool name
    if request.tool != "agent_executor":
        logger.warning(f"Unknown tool requested: {request.tool}")
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unknown tool: {request.tool}",
                "code": "UNKNOWN_TOOL"
            }
        )
    
    # Extract user query from arguments (FR3)
    query = request.arguments.get("query")
    if not query:
        logger.warning("Missing 'query' in arguments")
        return JSONResponse(
            status_code=400,
            content={
                "error": "Missing required argument: 'query'",
                "code": "MISSING_ARGUMENT"
            }
        )
    
    # Extract optional system_instruction from arguments
    system_instruction = request.arguments.get("system_instruction")
    if system_instruction:
        logger.info(f"Using custom system instruction (length: {len(str(system_instruction))})")

    # Optional task_id for workflow resumption/monitoring (Glazyr)
    task_id = request.arguments.get("task_id") or str(uuid.uuid4())
    task_id = str(task_id)
    
    logger.info(f"Executing agent with query: {query[:100]}...")
    
    try:
        # Get the agent executor (with custom instruction if provided)
        agent_executor = get_agent(system_instruction=system_instruction)

        # Track task state without storing raw query (no screenshot/base64 persistence)
        started = now_ts()
        existing = _state_store.get_task(task_id)
        record = TaskRecord(
            task_id=task_id,
            created_at=existing.created_at if existing else started,
            updated_at=started,
            status="running",
            attempts=(existing.attempts + 1) if existing else 1,
            query_preview=_preview(str(query), 500),
            query_sha256=_sha256(str(query)),
            last_output_preview=None,
            last_error=None,
        )
        _state_store.put_task(record, ttl_seconds=_config.task_ttl_seconds)
        _state_store.add_recent(task_id, max_items=_config.recent_tasks_max)

        # Execute the agent (FR3) with retries and without blocking the event loop
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type(Exception),
            reraise=True,
        )
        def _invoke_sync(q: str):
            return agent_executor.invoke({"input": q})

        result = await anyio.to_thread.run_sync(_invoke_sync, str(query))
        
        # Extract the final answer
        final_answer = result.get("output", "No output generated")
        
        logger.info("Agent execution completed successfully")

        finished = now_ts()
        record.updated_at = finished
        record.status = "succeeded"
        record.last_output_preview = _preview(final_answer, 1000)
        record.last_error = None
        _state_store.put_task(record, ttl_seconds=_config.task_ttl_seconds)
        
        # Map result to MCP response format (FR4)
        return {
            "content": [
                {
                    "type": "text",
                    "text": final_answer
                }
            ],
            "isError": False
        }
        
    except Exception as e:
        # Error handling (FR6)
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        try:
            finished = now_ts()
            rec = _state_store.get_task(task_id)
            if rec:
                rec.updated_at = finished
                rec.status = "failed"
                rec.last_error = _preview(str(e), 1000)
                _state_store.put_task(rec, ttl_seconds=_config.task_ttl_seconds)
        except Exception:
            # Never fail the request due to monitoring/state
            pass

        return JSONResponse(
            status_code=500,
            content={
                "content": [
                    {
                        "type": "text",
                        "text": f"Agent execution failed: {str(e)}"
                    }
                ],
                "isError": True
            }
        )


# Simple in-memory cache for Playwright snapshots
_playwright_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_POPULAR_SITES = ["amazon.com", "github.com", "google.com", "stackoverflow.com"]


def _get_cache_key(url: str) -> str:
    """Generate a cache key from URL"""
    # Normalize URL
    url_lower = url.lower().strip()
    if not url_lower.startswith(("http://", "https://")):
        url_lower = "https://" + url_lower
    return url_lower


def _is_popular_site(url: str) -> bool:
    """Check if URL is a popular site that should be cached"""
    url_lower = url.lower()
    return any(site in url_lower for site in _CACHE_POPULAR_SITES)


def _generate_accessibility_snapshot_sync(url: str) -> str:
    """
    Synchronous wrapper for generating accessibility snapshot.
    This runs in a separate thread to avoid event loop conflicts on Windows.
    Uses sync Playwright API to avoid async issues.
    """
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                # Navigate to the page
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Get accessibility snapshot using JavaScript evaluation
                ax_tree = page.evaluate("""
                    () => {
                        function getAccessibilityInfo(element) {
                            if (!element) return null;
                            
                            const role = element.getAttribute('role') || 
                                         (element.tagName ? element.tagName.toLowerCase() : 'unknown');
                            const name = element.getAttribute('aria-label') || 
                                        element.getAttribute('alt') ||
                                        element.textContent?.trim().substring(0, 100) || '';
                            const description = element.getAttribute('aria-description') || '';
                            const value = element.value || element.getAttribute('value') || '';
                            const checked = element.checked !== undefined ? element.checked : null;
                            const selected = element.selected !== undefined ? element.selected : null;
                            
                            const info = {
                                role: role,
                                name: name,
                                description: description,
                                tag: element.tagName ? element.tagName.toLowerCase() : 'unknown'
                            };
                            
                            if (value) info.value = value;
                            if (checked !== null) info.checked = checked;
                            if (selected !== null) info.selected = selected;
                            
                            // Get children
                            const children = [];
                            for (let child of element.children || []) {
                                const childInfo = getAccessibilityInfo(child);
                                if (childInfo) children.push(childInfo);
                            }
                            
                            if (children.length > 0) info.children = children;
                            return info;
                        }
                        
                        return getAccessibilityInfo(document.body);
                    }
                """)
                
                # Format the accessibility tree
                def format_node(node: Dict[str, Any], indent: int = 0) -> str:
                    """Recursively format accessibility tree nodes"""
                    if not node:
                        return ""
                    
                    prefix = "  " * indent
                    role = node.get("role", "unknown")
                    name = node.get("name", "")
                    description = node.get("description", "")
                    
                    lines = [f"{prefix}[{role}]"]
                    if name:
                        lines.append(f"{prefix}  Name: {name}")
                    if description:
                        lines.append(f"{prefix}  Description: {description}")
                    
                    # Add other relevant properties
                    for prop_key in ["value", "checked", "selected"]:
                        if prop_key in node and node[prop_key] is not None:
                            lines.append(f"{prefix}  {prop_key.capitalize()}: {node[prop_key]}")
                    
                    # Recursively process children
                    children = node.get("children", [])
                    for child in children:
                        child_output = format_node(child, indent + 1)
                        if child_output:
                            lines.append(child_output)
                    
                    return "\n".join(lines)
                
                formatted_snapshot = format_node(ax_tree) if ax_tree else "No accessibility tree available"
                return formatted_snapshot
                
            finally:
                browser.close()
    except Exception as e:
        # Re-raise to be caught by outer handler
        raise


async def _generate_accessibility_snapshot_async(url: str) -> str:
    """
    Generate a structured accessibility snapshot using Playwright.
    Returns a text representation of the page's accessibility tree.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise Exception("Playwright is not available. Please install playwright: pip install playwright && playwright install")
    
    try:
        # Launch Playwright - the event loop policy is already set at module level
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                # Navigate to the page
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Get accessibility snapshot using JavaScript evaluation
                # This extracts structured information from the DOM
                ax_tree = await page.evaluate("""
                    () => {
                        function getAccessibilityInfo(element) {
                            if (!element) return null;
                            
                            const role = element.getAttribute('role') || 
                                         (element.tagName ? element.tagName.toLowerCase() : 'unknown');
                            const name = element.getAttribute('aria-label') || 
                                        element.getAttribute('alt') ||
                                        element.textContent?.trim().substring(0, 100) || '';
                            const description = element.getAttribute('aria-description') || '';
                            const value = element.value || element.getAttribute('value') || '';
                            const checked = element.checked !== undefined ? element.checked : null;
                            const selected = element.selected !== undefined ? element.selected : null;
                            
                            const info = {
                                role: role,
                                name: name,
                                description: description,
                                tag: element.tagName ? element.tagName.toLowerCase() : 'unknown'
                            };
                            
                            if (value) info.value = value;
                            if (checked !== null) info.checked = checked;
                            if (selected !== null) info.selected = selected;
                            
                            // Get children
                            const children = [];
                            for (let child of element.children || []) {
                                const childInfo = getAccessibilityInfo(child);
                                if (childInfo) children.push(childInfo);
                            }
                            
                            if (children.length > 0) info.children = children;
                            return info;
                        }
                        
                        return getAccessibilityInfo(document.body);
                    }
                """)
                
                # Format the accessibility tree
                def format_node(node: Dict[str, Any], indent: int = 0) -> str:
                    """Recursively format accessibility tree nodes"""
                    if not node:
                        return ""
                    
                    prefix = "  " * indent
                    role = node.get("role", "unknown")
                    name = node.get("name", "")
                    description = node.get("description", "")
                    
                    lines = [f"{prefix}[{role}]"]
                    if name:
                        lines.append(f"{prefix}  Name: {name}")
                    if description:
                        lines.append(f"{prefix}  Description: {description}")
                    
                    # Add other relevant properties
                    for prop_key in ["value", "checked", "selected"]:
                        if prop_key in node and node[prop_key] is not None:
                            lines.append(f"{prefix}  {prop_key.capitalize()}: {node[prop_key]}")
                    
                    # Recursively process children
                    children = node.get("children", [])
                    for child in children:
                        child_output = format_node(child, indent + 1)
                        if child_output:
                            lines.append(child_output)
                    
                    return "\n".join(lines)
                
                formatted_snapshot = format_node(ax_tree) if ax_tree else "No accessibility tree available"
                return formatted_snapshot
                
            finally:
                await browser.close()
    except Exception as e:
        # Re-raise to be caught by outer handler
        raise


async def _generate_accessibility_snapshot(url: str) -> str:
    """
    Generate a structured accessibility snapshot using Playwright.
    Now uses async Playwright directly since we're using ProactorEventLoop on Windows.
    """
    if not PLAYWRIGHT_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Playwright is not available. Please install playwright: pip install playwright && playwright install"
        )
    
    try:
        # Use async Playwright directly - ProactorEventLoop supports subprocesses
        return await _generate_accessibility_snapshot_async(url)
    except Exception as e:
        error_msg = str(e) or repr(e) or "Unknown error"
        error_type = type(e).__name__
        
        # Get full traceback for logging
        import traceback
        full_traceback = traceback.format_exc()
        logger.error(f"Error generating Playwright snapshot ({error_type}): {error_msg}\n{full_traceback}")
        
        # Provide more helpful error messages
        if "Executable doesn't exist" in error_msg or "browserType.launch" in error_msg or "Executable" in error_msg:
            error_msg = "Chromium browser not installed. Run: playwright install chromium"
        elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
            error_msg = f"Request timed out after 30 seconds. The website may be slow or unreachable: {error_msg}"
        elif "net::" in error_msg.lower() or "dns" in error_msg.lower() or "ERR_" in error_msg:
            error_msg = f"Network error accessing the website: {error_msg}"
        elif error_type == "NotImplementedError":
            error_msg = f"Playwright compatibility issue: {error_msg or 'Windows event loop policy may need adjustment'}"
        elif not error_msg or error_msg == "Unknown error":
            error_msg = f"{error_type}: Check server logs for details. Full error: {full_traceback[:200]}"
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate snapshot: {error_msg}"
        )


def _estimate_token_count(text: str) -> int:
    """Rough estimate of token count (4 characters ≈ 1 token)"""
    return len(text) // 4


@app.post("/api/playwright/snapshot", response_model=PlaywrightSnapshotResponse)
async def get_playwright_snapshot(request: PlaywrightSnapshotRequest):
    """
    Generate a structured accessibility snapshot of a webpage using Playwright.
    
    This endpoint is used by the Playwright Sandbox preview feature to show
    how the AI "views" a website through structured accessibility data.
    """
    logger.info(f"POST /api/playwright/snapshot - URL: {request.url}")
    
    # Normalize URL
    url = request.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Add protocol if missing
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    cache_key = _get_cache_key(url)
    cached = False
    
    # Check cache if enabled and for popular sites
    if request.use_cache and _is_popular_site(url):
        if cache_key in _playwright_cache:
            cached_data = _playwright_cache[cache_key]
            logger.info(f"Returning cached snapshot for {url}")
            return PlaywrightSnapshotResponse(
                snapshot=cached_data["snapshot"],
                url=cached_data["url"],
                cached=True,
                token_count=cached_data.get("token_count")
            )
    
    # Generate snapshot
    snapshot = await _generate_accessibility_snapshot(url)
    token_count = _estimate_token_count(snapshot)
    
    # Cache if popular site
    if request.use_cache and _is_popular_site(url):
        _playwright_cache[cache_key] = {
            "snapshot": snapshot,
            "url": url,
            "token_count": token_count
        }
        # Limit cache size (keep last 50 entries)
        if len(_playwright_cache) > 50:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(_playwright_cache))
            del _playwright_cache[oldest_key]
    
    return PlaywrightSnapshotResponse(
        snapshot=snapshot,
        url=url,
        cached=False,
        token_count=token_count
    )


@app.post("/api/playwright/test-prompt")
async def test_playwright_prompt(request: Dict[str, Any]):
    """
    Test a prompt against a snapshot to find elements.
    This is a simplified version that searches the snapshot text for keywords.
    """
    snapshot = request.get("snapshot", "")
    prompt = request.get("prompt", "")
    
    if not snapshot or not prompt:
        raise HTTPException(status_code=400, detail="Both snapshot and prompt are required")
    
    # Simple keyword matching (in a real implementation, this would use an LLM)
    prompt_lower = prompt.lower()
    keywords = []
    
    # Extract keywords from prompt
    if "login" in prompt_lower or "sign in" in prompt_lower:
        keywords.extend(["button", "login", "sign in", "submit"])
    if "button" in prompt_lower:
        keywords.append("button")
    if "link" in prompt_lower:
        keywords.append("link")
    if "input" in prompt_lower or "field" in prompt_lower:
        keywords.extend(["input", "textbox", "field"])
    
    # Find matching lines in snapshot
    lines = snapshot.split("\n")
    matches = []
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            matches.append({
                "line": i + 1,
                "content": line.strip(),
                "context": "\n".join(lines[max(0, i-2):min(len(lines), i+3)])
            })
    
    return {
        "matches": matches[:10],  # Limit to 10 matches
        "prompt": prompt,
        "total_matches": len(matches)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)


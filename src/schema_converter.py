"""
Pydantic to JSON Schema conversion utilities.

This module provides robust conversion from LangChain Pydantic models
to MCP-compliant JSON Schema, handling Optional, Union, Enum, and nested types.
"""

from typing import Any, Dict, List, Optional, Union, get_origin, get_args
from pydantic import BaseModel
from pydantic._internal._generate_schema import GenerateSchema
import json


def pydantic_to_json_schema(model: type) -> Dict[str, Any]:
    """
    Convert a Pydantic model to JSON Schema.
    
    Args:
        model: Pydantic model class
        
    Returns:
        JSON Schema dictionary compatible with MCP
    """
    if not issubclass(model, BaseModel):
        raise ValueError(f"{model} is not a Pydantic model")
    
    schema = model.model_json_schema()
    
    # Clean up the schema for MCP compatibility
    cleaned = _clean_schema(schema)
    
    return cleaned


def _clean_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and normalize a JSON schema for MCP compatibility.
    
    Handles:
    - Removing Pydantic-specific fields
    - Converting $defs to definitions (if needed)
    - Ensuring required fields are properly marked
    - Handling Optional types
    """
    if not isinstance(schema, dict):
        return schema
    
    cleaned = {}
    
    # Copy basic fields
    for key in ["type", "properties", "required", "description", "title"]:
        if key in schema:
            cleaned[key] = schema[key]
    
    # Handle $defs (Pydantic's definition references)
    if "$defs" in schema:
        cleaned["$defs"] = {k: _clean_schema(v) for k, v in schema["$defs"].items()}
    
    # Handle allOf, anyOf, oneOf (for Union types)
    for key in ["allOf", "anyOf", "oneOf"]:
        if key in schema:
            cleaned[key] = [_clean_schema(item) for item in schema[key]]
    
    # Handle items (for arrays)
    if "items" in schema:
        cleaned["items"] = _clean_schema(schema["items"])
    
    # Handle enum
    if "enum" in schema:
        cleaned["enum"] = schema["enum"]
    
    # Handle default values
    if "default" in schema:
        cleaned["default"] = schema["default"]
    
    # Ensure properties are cleaned
    if "properties" in cleaned:
        cleaned["properties"] = {
            k: _clean_schema(v) for k, v in cleaned["properties"].items()
        }
    
    return cleaned


def tool_to_mcp_schema(tool) -> Dict[str, Any]:
    """
    Convert a LangChain Tool to MCP tool schema.
    
    Args:
        tool: LangChain Tool instance
        
    Returns:
        MCP tool definition dictionary
    """
    # Get the tool's input schema from its args_schema if available
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    # Try to extract schema from tool's args_schema (Pydantic model)
    if hasattr(tool, 'args_schema') and tool.args_schema:
        try:
            pydantic_schema = pydantic_to_json_schema(tool.args_schema)
            input_schema.update(pydantic_schema)
        except Exception as e:
            logger.warning(f"Failed to convert tool {tool.name} args_schema: {e}")
    
    # If no args_schema, try to infer from function signature
    if not input_schema.get("properties") and hasattr(tool, 'func'):
        import inspect
        sig = inspect.signature(tool.func)
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            
            param_type = param.annotation
            param_default = param.default
            
            # Convert Python type to JSON Schema type
            json_type = _python_type_to_json_type(param_type)
            
            prop_schema = {"type": json_type}
            
            # Add description from docstring if available
            if tool.description and param_name in tool.description.lower():
                # Try to extract param description (simplified)
                prop_schema["description"] = f"Parameter: {param_name}"
            
            properties[param_name] = prop_schema
            
            if param_default == inspect.Parameter.empty:
                required.append(param_name)
        
        input_schema["properties"] = properties
        input_schema["required"] = required
    
    return {
        "name": tool.name,
        "description": tool.description or f"Tool: {tool.name}",
        "inputSchema": input_schema
    }


def _python_type_to_json_type(python_type: type) -> str:
    """Convert Python type to JSON Schema type string."""
    origin = get_origin(python_type)
    
    if origin is Union:
        args = get_args(python_type)
        # Handle Optional[T] which is Union[T, None]
        non_none_args = [a for a in args if a is not type(None)]
        if non_none_args:
            return _python_type_to_json_type(non_none_args[0])
        return "string"  # fallback
    
    if python_type == str or python_type == Optional[str]:
        return "string"
    elif python_type == int or python_type == Optional[int]:
        return "integer"
    elif python_type == float or python_type == Optional[float]:
        return "number"
    elif python_type == bool or python_type == Optional[bool]:
        return "boolean"
    elif python_type == list or python_type == List:
        return "array"
    elif python_type == dict or python_type == Dict:
        return "object"
    else:
        return "string"  # default fallback


import logging
logger = logging.getLogger(__name__)

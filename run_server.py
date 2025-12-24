#!/usr/bin/env python3
"""
Simple script to run the LangChain Agent MCP Server
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import uvicorn

if __name__ == "__main__":
    # Load .env file from project root
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment variables from {env_file}")
    else:
        # Also try loading from current directory
        load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY not set. The agent may not work correctly.")
        print("Please set it in your environment or .env file.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting LangChain Agent MCP Server on {host}:{port}")
    print(f"API Documentation: http://{host}:{port}/docs")
    print(f"Health Check: http://{host}:{port}/health")
    print(f"MCP Manifest: http://{host}:{port}/mcp/manifest")
    
    # Disable reload on Windows when using Playwright to avoid SelectorEventLoop conflicts
    # Reload can force SelectorEventLoop which doesn't support subprocesses
    use_reload = os.getenv("RELOAD", "false").lower() == "true"
    if sys.platform == 'win32':
        use_reload = False  # Disable reload on Windows for Playwright compatibility
        print("Note: Auto-reload disabled on Windows for Playwright compatibility")
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=use_reload,
        log_level="info"
    )


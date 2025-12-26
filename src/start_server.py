#!/usr/bin/env python3
"""
Startup script for Cloud Run deployment.
Reads PORT from environment and starts FastAPI server.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

if __name__ == "__main__":
    # Get PORT from environment (Cloud Run sets this automatically)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting FastAPI server on {host}:{port}")
    print(f"Environment: PORT={port}, HOST={host}")
    
    # Run FastAPI application
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        log_level="info"
    )


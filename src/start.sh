#!/bin/sh
# Startup script for Cloud Run
# Reads PORT from environment (set by Cloud Run) or defaults to 8000
# Runs FastAPI server for Cloud Run deployment

# Get PORT from environment (Cloud Run sets this automatically)
PORT=${PORT:-8000}
HOST=${HOST:-0.0.0.0}

# Run FastAPI server using uvicorn
# Use exec to replace shell process with uvicorn
exec python -m uvicorn src.main:app --host "$HOST" --port "$PORT"


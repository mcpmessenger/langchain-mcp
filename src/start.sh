#!/bin/sh
# Startup script for Cloud Run
# Reads PORT from environment (set by Cloud Run) or defaults to 8000
# Runs FastAPI server for Cloud Run deployment

PORT=${PORT:-8000}
export HOST=0.0.0.0
export PORT=$PORT

# Run FastAPI server using uvicorn
exec python -m uvicorn src.main:app --host $HOST --port $PORT


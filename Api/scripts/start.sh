#!/bin/bash

# Start the FastAPI server with UV environment
export PATH="/Users/siva/.local/bin:$PATH"
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8001
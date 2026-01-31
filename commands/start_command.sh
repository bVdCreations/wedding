#!/bin/bash
set -e

echo "Starting the application..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

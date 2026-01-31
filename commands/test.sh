#!/bin/bash
set -e

echo "Running tests..."
pytest src/ -v --tb=short

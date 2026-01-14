#!/bin/bash

# Start the Reading Coach backend server with sample data

echo "🚀 Starting Reading Coach Backend..."
echo ""

# Navigate to project root
cd "$(dirname "$0")/.."

# Run the setup and server script
uv run python examples/setup_and_run.py

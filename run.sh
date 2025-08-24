#!/bin/bash

# Set error handling
set -e

# Print header
echo "====================================="
echo "  Learning Agent Web Interface Setup"
echo "====================================="

# Load environment variables if .env file exists
if [ -f .env ]; then
    echo "✓ Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
else
    echo "⚠️ No .env file found. Using default environment variables."
    echo "   You can create a .env file based on .env.example if needed."
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
else
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found $PYTHON_VERSION"
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 and try again."
    exit 1
else
    PIP_VERSION=$(pip3 --version | awk '{print $2}')
    echo "✓ Found pip version $PIP_VERSION"
fi

# Install dependencies if not already installed
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Check if JAF is installed
if ! python3 -c "import jaf" &> /dev/null; then
    echo "⚠️ JAF framework not found. Make sure it's installed and in your Python path."
    echo "   The application may not work correctly without it."
fi

# Check if LiteLLM is configured
if [ -z "$LITELLM_URL" ]; then
    echo "⚠️ LITELLM_URL is not set. Using default: http://localhost:4000/"
fi

echo "====================================="
echo "  Starting the Learning Agent Web Interface"
echo "====================================="
echo "Open your browser and navigate to http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo "====================================="

# Run the web interface with better error handling
python3 app.py || {
    echo "❌ Error starting the server. Check the error message above."
    exit 1
}

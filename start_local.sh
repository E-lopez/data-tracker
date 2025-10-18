#!/bin/bash

# Score Handler Local Development Setup
echo "🔧 Setting up Score Handler for local development..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Set environment variables (modify these as needed)


echo "✅ Setup complete!"
echo ""

# Start the local server
python run_local.py
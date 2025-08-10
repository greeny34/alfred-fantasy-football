#!/bin/bash

echo "🏈 Fantasy Football Draft Assistant 2025"
echo "========================================"
echo ""

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

echo "📍 Running from: $DIR"
echo "🚀 Starting Fantasy Football Draft Assistant..."
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3 from python.org"
    read -p "Press Enter to exit..."
    exit 1
fi

# Run the app
python3 draft_assistant_app.py

echo ""
echo "👋 Thanks for using Fantasy Football Draft Assistant!"
read -p "Press Enter to close..."
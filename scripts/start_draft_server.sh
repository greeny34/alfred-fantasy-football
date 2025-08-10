#!/bin/bash

echo "🏈 Starting Fantasy Football Draft Engine..."
echo ""

# Check if we're in the right directory
if [ ! -f "data_viewer.py" ]; then
    echo "❌ Error: data_viewer.py not found!"
    echo "Please run this script from the ff_draft_vibe directory"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 not found!"
    echo "Please install Python 3"
    exit 1
fi

# Check if Flask is installed
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Flask not found. Installing..."
    pip3 install flask
fi

# Check if psycopg2 is installed
python3 -c "import psycopg2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  psycopg2 not found. Installing..."
    pip3 install psycopg2-binary
fi

echo "🚀 Starting Flask server on http://127.0.0.1:5001"
echo ""
echo "📌 Important:"
echo "   - Your draft UI is at: simple_draft_ui.html"
echo "   - The optimizer will be at: http://127.0.0.1:5001/optimizer"
echo "   - Press Ctrl+C to stop the server"
echo ""

# Start the server
python3 data_viewer.py
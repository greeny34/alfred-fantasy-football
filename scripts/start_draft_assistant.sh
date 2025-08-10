#!/bin/bash

echo "🏈 Fantasy Football Draft Assistant 2025"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "data_viewer.py" ]; then
    echo "❌ Error: data_viewer.py not found!"
    echo "Please run this script from the ff_draft_vibe directory"
    exit 1
fi

# Kill any existing processes on ports 5001-5003
echo "🧹 Cleaning up any existing processes..."
for port in 5001 5002 5003; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo "   Stopping process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null
    fi
done

echo ""
echo "🚀 Starting Fantasy Football Draft Server on port 5002..."
echo ""
echo "📱 After the server starts:"
echo "   1. Open: real_draft_assistant.html in your browser"
echo "   2. Click 'Connect to Database'"
echo "   3. Set up your league and start drafting!"
echo ""
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask server
python3 data_viewer.py
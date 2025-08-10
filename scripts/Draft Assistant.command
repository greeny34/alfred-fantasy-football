#!/bin/bash

echo "🏈 Fantasy Football Draft Assistant 2025"
echo "========================================"

# Get the directory where this script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$DIR"

# Check for required files
if [ ! -f "data_viewer.py" ]; then
    osascript -e 'display dialog "data_viewer.py not found!\n\nMake sure this app is in the same folder as your draft files." with title "Missing Files" with icon stop'
    exit 1
fi

if [ ! -f "real_draft_assistant.html" ]; then
    osascript -e 'display dialog "real_draft_assistant.html not found!\n\nMake sure this app is in the same folder as your draft files." with title "Missing Files" with icon stop'
    exit 1
fi

# Find a free port
echo "🔍 Finding available port..."
PORT=5002
while lsof -i:$PORT &>/dev/null; do
    PORT=$((PORT + 1))
done

echo "🔧 Using port $PORT"

# Update HTML file with correct port
sed -i '' "s/const API_BASE = 'http:\/\/127\.0\.0\.1:[0-9]*'/const API_BASE = 'http:\/\/127.0.0.1:$PORT'/" real_draft_assistant.html

# Update Python file with correct port
sed -i '' "s/port=[0-9]*/port=$PORT/" data_viewer.py

echo "🚀 Starting Fantasy Football Draft Server..."

# Start the server in background
python3 data_viewer.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 3

echo "🌐 Opening Draft Assistant..."

# Open the HTML file in default browser
open real_draft_assistant.html

echo ""
echo "✅ Fantasy Football Draft Assistant is running!"
echo ""
echo "📱 Your browser should open automatically."
echo "   If not, open: real_draft_assistant.html"
echo ""
echo "🛑 Press Ctrl+C or close this window to stop."
echo ""

# Keep the script running and monitor the server
trap "echo '🛑 Shutting down...'; kill $SERVER_PID 2>/dev/null; exit 0" INT TERM

# Wait for the server process
wait $SERVER_PID
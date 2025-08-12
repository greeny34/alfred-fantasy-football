#!/bin/bash
# Simple ALFRED Test - Minimal version to isolate the issue

PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"
cd "$PROJECT_DIR"

echo "🧪 ALFRED Simple Test"
echo "===================="
echo ""
echo "Starting server in background..."

# Start server in background
python3 alfred_clean.py &
SERVER_PID=$!

echo "Server PID: $SERVER_PID"
echo "Waiting 5 seconds for server to start..."
sleep 5

echo ""
echo "Testing connection with curl..."
curl -s http://localhost:5555/ | head -5
CURL_EXIT=$?

echo ""
echo "Curl exit code: $CURL_EXIT"

if [ $CURL_EXIT -eq 0 ]; then
    echo "✅ Server is responding! Opening browser..."
    open http://localhost:5555/
else
    echo "❌ Server is not responding"
    echo ""
    echo "Server logs:"
    echo "============"
    # Show any output from the server
    sleep 2
    kill -0 $SERVER_PID 2>/dev/null && echo "Server process is still running" || echo "Server process has died"
fi

echo ""
echo "Press any key to stop server and exit..."
read -n 1

# Clean up
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

echo ""
echo "Server stopped."
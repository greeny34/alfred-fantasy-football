#!/bin/bash
# Script to fix the ALFRED desktop app

echo "🔧 Fixing ALFRED Desktop App..."
echo "================================"
echo ""

# Create proper launcher script
cat > alfred_launcher.sh << 'EOF'
#!/bin/bash
# ALFRED Fantasy Football Draft Assistant

# Configuration
PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"
PORT=5555

# Change to project directory
cd "$PROJECT_DIR" || {
    osascript -e 'display alert "ALFRED Error" message "Cannot find project directory. Please reinstall ALFRED." as critical'
    exit 1
}

# Check if server is already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    # Server already running, just open browser
    open "http://localhost:$PORT/"
    exit 0
fi

# Start the server in background and open browser
python3 alfred_clean.py &
SERVER_PID=$!

# Wait a moment for server to start
sleep 2

# Open browser
open "http://localhost:$PORT/"

# Wait for server to finish
wait $SERVER_PID
EOF

chmod +x alfred_launcher.sh

echo "✅ Launcher script created"
echo ""
echo "To fix your desktop app, you need to:"
echo ""
echo "1. Right-click on the ALFRED app in /Applications"
echo "2. Select 'Show Package Contents'"
echo "3. Navigate to Contents/MacOS/"
echo "4. Replace the script there with alfred_launcher.sh"
echo ""
echo "Or simply use the ALFRED_Launcher.command file instead:"
echo "cp ALFRED_Launcher.command ~/Desktop/"
echo ""
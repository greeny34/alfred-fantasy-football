#!/bin/bash
# ALFRED Fantasy Football Draft Assistant - Desktop Launcher
# This launcher can be placed anywhere on your system

# Always change to the project directory first
PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"
cd "$PROJECT_DIR"

echo "🏈 ALFRED - Fantasy Football Draft Assistant"
echo "============================================"
echo ""
echo "Starting ALFRED from: $PROJECT_DIR"
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "Installing required dependencies..."
    pip3 install flask psycopg2-binary pandas numpy
fi

# Run the clean server
echo "Launching ALFRED..."
python3 alfred_clean.py

# Keep terminal open if there's an error
if [ $? -ne 0 ]; then
    echo ""
    echo "Press any key to close..."
    read -n 1
fi
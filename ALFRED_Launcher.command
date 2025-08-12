#!/bin/bash
# ALFRED Fantasy Football Draft Assistant - Universal Launcher
# This launcher can be placed anywhere on your system (Desktop, Applications, etc.)

# Configuration
PROJECT_DIR="/Users/jeffgreenfield/dev/ff_draft_vibe"
PORT=5555
BROWSER_DELAY=3  # Seconds to wait before opening browser

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "Error: Cannot find ALFRED project directory at $PROJECT_DIR"
    echo "Please update PROJECT_DIR in this script"
    echo "Press any key to exit..."
    read -n 1
    exit 1
}

# Clear screen and show header
clear
echo "╔════════════════════════════════════════════════════════╗"
echo "║       🏈 ALFRED - Fantasy Football Draft Assistant      ║"
echo "║           Analytical League Fantasy Resource            ║"
echo "║              for Elite Drafting                         ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if server is already running
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  ALFRED is already running on port $PORT"
    echo ""
    echo "Opening browser to existing instance..."
    sleep 1
    open "http://localhost:$PORT/"
    echo ""
    echo "To restart ALFRED, first stop the existing instance."
    echo "Press any key to exit..."
    read -n 1
    exit 0
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check and install dependencies
echo "🔍 Checking dependencies..."
python3 -c "import flask, psycopg2, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install flask psycopg2-binary pandas numpy requests beautifulsoup4
    echo ""
fi

# Check database connection
echo "🔗 Checking database connection..."
python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(database='fantasy_draft_db', host='localhost')
    conn.close()
    print('✅ Database connected successfully')
except:
    print('⚠️  Database connection failed - some features may be unavailable')
" 

echo ""
echo "🚀 Starting ALFRED server..."
echo "════════════════════════════════════════════════════════"
echo ""

# Open browser after delay (in background)
(sleep $BROWSER_DELAY && open "http://localhost:$PORT/") &

# Run the server
python3 alfred_clean.py

# If we get here, the server was stopped
echo ""
echo "════════════════════════════════════════════════════════"
echo "ALFRED has been stopped."
echo "Press any key to close this window..."
read -n 1
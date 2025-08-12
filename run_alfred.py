#!/usr/bin/env python3
"""
ALFRED - Simple Draft Assistant Runner
This opens the spreadsheet interface directly
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

# Change to script directory
os.chdir(Path(__file__).parent)

print("🏈 ALFRED Fantasy Football Draft Assistant")
print("=" * 50)

# First, let's use the simple draft server instead
print("Starting simple draft server...")

# Kill any existing servers
subprocess.run(["pkill", "-f", "simple_draft_server.py"], capture_output=True)
time.sleep(1)

# Start the simple draft server
server_process = subprocess.Popen(
    [sys.executable, "src/engines/simple_draft_server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
print("Waiting for server to start...")
time.sleep(2)

# Open the spreadsheet interface
url = "http://localhost:8000/templates/spreadsheet.html"
print(f"Opening browser to {url}")
webbrowser.open(url)

print("\nDraft Assistant is running!")
print("Press Ctrl+C to stop the server")

try:
    # Keep running until interrupted
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
    server_process.terminate()
    print("Server stopped.")
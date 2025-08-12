#!/usr/bin/env python3
"""
ALFRED - Start with Built-in Interface
"""

import subprocess
import webbrowser
import time
import sys
import os

# Change to project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("🏈 Starting ALFRED Fantasy Football Draft Assistant...")
print("=" * 50)

# Kill any existing servers
subprocess.run(["pkill", "-f", "draft_assistant_app.py"], capture_output=True)
time.sleep(1)

# Start the draft assistant app
process = subprocess.Popen(
    [sys.executable, "src/engines/draft_assistant_app.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

# Wait for server to start
print("Waiting for server to start...")
for i in range(10):
    line = process.stdout.readline()
    print(line.strip())
    if "Server starting" in line:
        break
    time.sleep(0.5)

# The app automatically opens a browser, just keep it running
print("\nALFRED is running!")
print("\nUsing the built-in interface:")
print("1. Click 'Start New Draft'")
print("2. Configure your draft settings")
print("3. Begin drafting!")
print("\nPress Ctrl+C to stop")

try:
    # Keep running and show output
    while True:
        output = process.stdout.readline()
        if output:
            print(output.strip())
        if process.poll() is not None:
            break
except KeyboardInterrupt:
    print("\nShutting down...")
    process.terminate()
    print("Done!")
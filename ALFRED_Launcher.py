#!/usr/bin/env python3
"""
ALFRED Fantasy Football Draft Assistant - Simple Launcher
Double-click this file to start the app
"""

import os
import sys
import subprocess
import webbrowser
import time

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Change to project directory
os.chdir(script_dir)

print("🏈 ALFRED Fantasy Football Draft Assistant")
print("=" * 50)
print("Starting application...")

# Launch the main app
try:
    # Try to activate virtual environment if it exists
    venv_python = os.path.join(script_dir, '.venv', 'bin', 'python')
    if os.path.exists(venv_python):
        python_cmd = venv_python
    else:
        python_cmd = sys.executable
    
    # Run the draft assistant
    subprocess.run([python_cmd, 'src/engines/draft_assistant_app.py'])
    
except KeyboardInterrupt:
    print("\n\nShutting down ALFRED...")
except Exception as e:
    print(f"\nError: {e}")
    print("\nPress Enter to close...")
    input()
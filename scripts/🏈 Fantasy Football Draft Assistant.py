#!/usr/bin/env python3
"""
Fantasy Football Draft Assistant 2025 - Launcher
Double-click to run!
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from draft_assistant_app import DraftAssistantApp
    
    print("🏈 Fantasy Football Draft Assistant 2025")
    print("========================================")
    print("Starting application...")
    
    app = DraftAssistantApp()
    app.run()
    
except Exception as e:
    print(f"Error starting application: {e}")
    input("Press Enter to exit...")
except KeyboardInterrupt:
    print("\n👋 Thanks for using Fantasy Football Draft Assistant!")
    sys.exit(0)
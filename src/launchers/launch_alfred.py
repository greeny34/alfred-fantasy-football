#!/usr/bin/env python3
"""
Simple ALFRED Launcher - Just starts the professional server
"""

import subprocess
import sys
import webbrowser
import time
import os

def main():
    print("🏈 ALFRED - Fantasy Football Draft Assistant")
    print("=" * 50)
    print("Starting your professional interface...")
    
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Start the professional server
        print("🚀 Launching Flask server with your database...")
        process = subprocess.Popen([
            sys.executable, "alfred_main_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Wait for server to be ready
        print("⏳ Waiting for server to start...")
        for i in range(15):
            line = process.stdout.readline()
            if line:
                print(line.strip())
            if "Running on" in line:
                print("✅ Server is ready!")
                break
            time.sleep(0.5)
        
        # Open browser
        print("🌐 Opening your professional interface...")
        webbrowser.open('http://localhost:5555/')
        
        print("\n" + "="*60)
        print("🎉 ALFRED is now running!")
        print("📍 Dashboard: http://localhost:5555/")
        print("🏈 Draft Board: http://localhost:5555/draft_board") 
        print("📊 Spreadsheet: http://localhost:5555/spreadsheet")
        print("="*60)
        print("\nPress Ctrl+C to stop the server")
        
        # Keep the server running and show output
        try:
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    print(f"[SERVER] {line.strip()}")
                if process.poll() is not None:
                    break
        except KeyboardInterrupt:
            print("\n🛑 Shutting down ALFRED...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            print("✅ ALFRED stopped successfully!")
            
    except Exception as e:
        print(f"❌ Error starting ALFRED: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
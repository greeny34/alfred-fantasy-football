#!/usr/bin/env python3
"""
Fantasy Football Draft Assistant 2025
Double-click to run - no terminal needed!
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
HTML_FILE = SCRIPT_DIR / "real_draft_assistant.html"

def show_message(title, message, error=False):
    """Show a message to the user"""
    try:
        if sys.platform == "darwin":  # macOS
            icon = "stop" if error else "note"
            subprocess.run([
                "osascript", "-e", 
                f'display dialog "{message}" with title "{title}" with icon {icon} buttons {{"OK"}} default button "OK"'
            ])
        else:
            print(f"{title}: {message}")
    except:
        print(f"{title}: {message}")

def check_requirements():
    """Check if Flask is installed"""
    try:
        import flask
        import psycopg2
        return True
    except ImportError as e:
        missing = str(e).split("'")[1] if "'" in str(e) else "required packages"
        show_message(
            "Missing Requirements", 
            f"Installing {missing}...\n\nThis may take a moment.", 
            False
        )
        
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "psycopg2-binary", "--user", "--quiet"])
            return True
        except subprocess.CalledProcessError:
            show_message(
                "Installation Failed", 
                f"Could not install {missing}.\n\nPlease run in Terminal:\npip3 install flask psycopg2-binary", 
                True
            )
            return False

def find_free_port(start_port=5002):
    """Find a free port starting from start_port"""
    import socket
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

def update_html_port(port):
    """Update the HTML file with the correct port"""
    try:
        with open(HTML_FILE, 'r') as f:
            content = f.read()
        
        # Update API_BASE URL
        import re
        content = re.sub(r"const API_BASE = 'http://127\.0\.0\.1:\d+'", 
                        f"const API_BASE = 'http://127.0.0.1:{port}'", content)
        
        with open(HTML_FILE, 'w') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"Error updating HTML file: {e}")
        return False

def start_flask_server(port):
    """Start the Flask server in a separate thread"""
    def run_server():
        try:
            # Change to the script directory
            os.chdir(SCRIPT_DIR)
            
            # Import and run the Flask app
            sys.path.insert(0, str(SCRIPT_DIR))
            
            # Modify the data_viewer.py port dynamically
            with open('data_viewer.py', 'r') as f:
                server_code = f.read()
            
            # Replace the port in the code
            import re
            server_code = re.sub(r"port=\d+", f"port={port}", server_code)
            
            # Execute the modified server code
            exec_globals = {'__name__': '__main__'}
            exec(server_code, exec_globals)
            
        except Exception as e:
            print(f"Server error: {e}")
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    return server_thread

def open_browser(port):
    """Open the browser after a delay"""
    def delayed_open():
        time.sleep(3)  # Wait for server to start
        url = f"file://{HTML_FILE.absolute()}"
        webbrowser.open(url)
    
    browser_thread = threading.Thread(target=delayed_open, daemon=True)
    browser_thread.start()

def main():
    """Main application entry point"""
    print("🏈 Fantasy Football Draft Assistant 2025")
    print("========================================")
    
    # Check if required files exist
    if not os.path.exists(SCRIPT_DIR / "data_viewer.py"):
        show_message(
            "Missing Files", 
            "data_viewer.py not found!\n\nMake sure this app is in the same folder as your draft files.", 
            True
        )
        return
    
    if not HTML_FILE.exists():
        show_message(
            "Missing Files", 
            "real_draft_assistant.html not found!\n\nMake sure this app is in the same folder as your draft files.", 
            True
        )
        return
    
    # Check requirements
    print("📦 Checking requirements...")
    if not check_requirements():
        return
    
    # Find free port
    print("🔍 Finding available port...")
    port = find_free_port()
    if not port:
        show_message("Port Error", "Could not find an available port!", True)
        return
    
    # Update HTML file with correct port
    print(f"🔧 Configuring for port {port}...")
    if not update_html_port(port):
        show_message("Configuration Error", "Could not update HTML file!", True)
        return
    
    # Start Flask server
    print(f"🚀 Starting server on port {port}...")
    server_thread = start_flask_server(port)
    
    # Open browser
    print("🌐 Opening browser...")
    open_browser(port)
    
    print(f"""
✅ Fantasy Football Draft Assistant is running!

🌐 URL: http://127.0.0.1:{port}
📁 Draft UI: file://{HTML_FILE.absolute()}

📱 Your browser should open automatically.
   If not, open: real_draft_assistant.html

🛑 Close this window to stop the server.
""")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()
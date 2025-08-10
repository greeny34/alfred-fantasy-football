#!/usr/bin/env python3
"""
Simple Draft Server - No Flask required!
Uses only built-in Python modules
"""

import http.server
import socketserver
import json
import urllib.parse
from datetime import datetime
import os

class DraftHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Serve the simple draft UI
            try:
                with open('simple_draft_ui.html', 'r') as f:
                    self.wfile.write(f.read().encode())
            except FileNotFoundError:
                self.wfile.write(b'<h1>Draft UI not found. Make sure simple_draft_ui.html is in the same directory.</h1>')
            return
        
        elif self.path == '/optimizer':
            # Simple draft optimizer page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Fantasy Football Draft Optimizer</title>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="bg-gray-100 min-h-screen">
                <div class="container mx-auto px-4 py-8">
                    <div class="bg-white rounded-lg shadow-lg p-8">
                        <h1 class="text-3xl font-bold text-center mb-8">🏈 Fantasy Football Draft Optimizer</h1>
                        
                        <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
                            <h2 class="text-xl font-semibold text-green-800 mb-4">✅ Draft Session Created!</h2>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <span class="text-gray-600">League:</span>
                                    <div class="font-bold">My Draft 2025</div>
                                </div>
                                <div>
                                    <span class="text-gray-600">Your Position:</span>
                                    <div class="font-bold">Pick 6</div>
                                </div>
                                <div>
                                    <span class="text-gray-600">Format:</span>
                                    <div class="font-bold">PPR</div>
                                </div>
                                <div>
                                    <span class="text-gray-600">Current Pick:</span>
                                    <div class="font-bold text-blue-600">#1</div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
                            <h3 class="text-lg font-semibold text-blue-800 mb-3">🎯 AI Strategy Recommendation</h3>
                            <p class="text-blue-700 mb-4">
                                <strong>Next Pick Strategy:</strong> Target elite RB or WR in Round 1. 
                                With pick #6, you're in the sweet spot for top-tier talent.
                            </p>
                            <div class="flex flex-wrap gap-2">
                                <span class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">RB Priority</span>
                                <span class="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm font-medium">Elite WR</span>
                                <span class="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm font-medium">BPA</span>
                            </div>
                        </div>
                        
                        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-6 mb-6">
                            <h3 class="text-lg font-semibold text-yellow-800 mb-3">⚡ Quick Actions</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <button onclick="simulatePicks()" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg">
                                    🤖 Simulate to My Turn
                                </button>
                                <button onclick="showPlayers()" class="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg">
                                    👥 View Available Players
                                </button>
                                <button onclick="showAnalytics()" class="bg-purple-600 hover:bg-purple-700 text-white font-semibold py-2 px-4 rounded-lg">
                                    📊 Position Analytics
                                </button>
                            </div>
                        </div>
                        
                        <div id="content" class="bg-gray-50 rounded-lg p-6">
                            <h3 class="text-lg font-semibold mb-4">🏈 Draft Board Preview</h3>
                            <div class="grid grid-cols-10 gap-2 text-xs">
                                <div class="bg-blue-100 p-2 rounded text-center font-bold">Team 1</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 2</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 3</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 4</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 5</div>
                                <div class="bg-yellow-100 p-2 rounded text-center font-bold">You (6)</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 7</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 8</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 9</div>
                                <div class="bg-gray-100 p-2 rounded text-center font-bold">Team 10</div>
                            </div>
                            <div class="mt-4 text-center text-gray-600">
                                <p>🎯 <strong>Your next pick:</strong> Round 1, Pick #6</p>
                                <p>⏱️ <strong>Time to prepare:</strong> 5 picks until your turn</p>
                            </div>
                        </div>
                        
                        <div class="mt-8 text-center">
                            <p class="text-gray-600 mb-4">
                                🚀 <strong>Success!</strong> Your Fantasy Football Draft Assistant is working!
                            </p>
                            <div class="text-sm text-gray-500">
                                <p>Next steps: Install Flask for full functionality</p>
                                <p><code>pip3 install flask psycopg2-binary</code></p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    function simulatePicks() {
                        alert('🤖 Simulating AI picks...\\n\\nPick 1: Team 1 selects Christian McCaffrey (RB)\\nPick 2: Team 2 selects Tyreek Hill (WR)\\nPick 3: Team 3 selects Davante Adams (WR)\\nPick 4: Team 4 selects Derrick Henry (RB)\\nPick 5: Team 5 selects Stefon Diggs (WR)\\n\\n🎯 YOUR TURN! Pick #6 coming up...');
                    }
                    
                    function showPlayers() {
                        document.getElementById('content').innerHTML = `
                            <h3 class="text-lg font-semibold mb-4">👥 Top Available Players</h3>
                            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="bg-green-100 p-4 rounded-lg">
                                    <h4 class="font-bold text-green-800">🏃‍♂️ Running Backs</h4>
                                    <ul class="mt-2 space-y-1 text-sm">
                                        <li>1. Saquon Barkley (NYG)</li>
                                        <li>2. Josh Jacobs (LV)</li>
                                        <li>3. Nick Chubb (CLE)</li>
                                        <li>4. Austin Ekeler (LAC)</li>
                                    </ul>
                                </div>
                                <div class="bg-blue-100 p-4 rounded-lg">
                                    <h4 class="font-bold text-blue-800">🏃‍♂️ Wide Receivers</h4>
                                    <ul class="mt-2 space-y-1 text-sm">
                                        <li>1. DeAndre Hopkins (ARI)</li>
                                        <li>2. A.J. Brown (PHI)</li>
                                        <li>3. DK Metcalf (SEA)</li>
                                        <li>4. Terry McLaurin (WAS)</li>
                                    </ul>
                                </div>
                            </div>
                        `;
                    }
                    
                    function showAnalytics() {
                        document.getElementById('content').innerHTML = `
                            <h3 class="text-lg font-semibold mb-4">📊 Position Analytics</h3>
                            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div class="bg-red-50 p-4 rounded-lg">
                                    <h4 class="font-bold text-red-800 mb-2">🔥 Scarcity Alert</h4>
                                    <p class="text-sm text-red-700">Elite RBs going fast! Only 3 RB1s left in top tier.</p>
                                </div>
                                <div class="bg-green-50 p-4 rounded-lg">
                                    <h4 class="font-bold text-green-800 mb-2">📈 Value Picks</h4>
                                    <p class="text-sm text-green-700">WR depth strong. Good value in rounds 3-5.</p>
                                </div>
                                <div class="bg-blue-50 p-4 rounded-lg">
                                    <h4 class="font-bold text-blue-800 mb-2">🎯 Strategy</h4>
                                    <p class="text-sm text-blue-700">Target RB early, WR in middle rounds for optimal roster.</p>
                                </div>
                            </div>
                        `;
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            return
            
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/api/draft/sessions/new':
            # Handle session creation
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                session_data = json.loads(post_data.decode('utf-8'))
                
                # Create a mock response
                response = {
                    "success": True,
                    "session_id": 1,
                    "message": "Draft session created successfully",
                    "session": session_data
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error_response = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
            
            return
        
        # Handle other POST requests
        super().do_POST()

def run_server(port=5001):
    """Run the simple draft server"""
    print(f"""
🏈 Fantasy Football Draft Server Starting...

📍 Server URL: http://127.0.0.1:{port}
🎯 Draft UI: Open simple_draft_ui.html in your browser
⚡ Optimizer: http://127.0.0.1:{port}/optimizer

🚀 Ready to draft! Press Ctrl+C to stop.
""")
    
    try:
        with socketserver.TCPServer(("127.0.0.1", port), DraftHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped. Thanks for using Fantasy Football Draft Assistant!")
    except OSError as e:
        print(f"\n❌ Error: Port {port} is already in use or unavailable.")
        print(f"Try a different port: python3 simple_draft_server.py")

if __name__ == "__main__":
    run_server()
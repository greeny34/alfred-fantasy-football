#!/usr/bin/env python3
"""
ALFRED - Basic Draft Assistant
No external dependencies required!
"""

import http.server
import socketserver
import json
import webbrowser
from urllib.parse import urlparse, parse_qs

PORT = 8888

# Simple player data
PLAYERS = [
    {"id": 1, "name": "Josh Allen", "pos": "QB", "team": "BUF", "adp": 1},
    {"id": 2, "name": "Lamar Jackson", "pos": "QB", "team": "BAL", "adp": 2},
    {"id": 3, "name": "Jonathan Taylor", "pos": "RB", "team": "IND", "adp": 3},
    {"id": 4, "name": "Austin Ekeler", "pos": "RB", "team": "LAC", "adp": 4},
    {"id": 5, "name": "Justin Jefferson", "pos": "WR", "team": "MIN", "adp": 5},
    {"id": 6, "name": "Ja'Marr Chase", "pos": "WR", "team": "CIN", "adp": 6},
    {"id": 7, "name": "Travis Kelce", "pos": "TE", "team": "KC", "adp": 7},
    {"id": 8, "name": "Stefon Diggs", "pos": "WR", "team": "BUF", "adp": 8},
    {"id": 9, "name": "Nick Chubb", "pos": "RB", "team": "CLE", "adp": 9},
    {"id": 10, "name": "Davante Adams", "pos": "WR", "team": "LV", "adp": 10},
]

# Draft state
drafted = []
my_team = []

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Basic Draft Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #2563eb; text-align: center; }
        .players { margin: 20px 0; }
        .player { 
            padding: 10px; 
            margin: 5px 0; 
            background: #f0f0f0; 
            border-radius: 5px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
        }
        .drafted { background: #ffcccc; text-decoration: line-through; }
        button { 
            background: #2563eb; 
            color: white; 
            border: none; 
            padding: 5px 15px; 
            border-radius: 3px; 
            cursor: pointer; 
        }
        button:hover { background: #1d4ed8; }
        .my-team { background: #ccffcc; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🏈 ALFRED - Basic Draft Assistant</h1>
    <h2>Available Players</h2>
    <div id="players" class="players"></div>
    <h2>My Team</h2>
    <div id="myTeam" class="players"></div>
    
    <script>
        async function loadPlayers() {
            const response = await fetch('/api/players');
            const data = await response.json();
            
            const playersDiv = document.getElementById('players');
            playersDiv.innerHTML = data.available.map(p => `
                <div class="player">
                    <span>${p.name} (${p.pos}) - ${p.team}</span>
                    <button onclick="draftPlayer(${p.id})">Draft</button>
                </div>
            `).join('');
            
            const myTeamDiv = document.getElementById('myTeam');
            myTeamDiv.innerHTML = data.my_team.map(p => `
                <div class="player my-team">
                    ${p.name} (${p.pos}) - ${p.team}
                </div>
            `).join('');
        }
        
        async function draftPlayer(id) {
            await fetch(`/api/draft?id=${id}`);
            loadPlayers();
        }
        
        loadPlayers();
    </script>
</body>
</html>
"""

class DraftHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif parsed_path.path == '/api/players':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            available = [p for p in PLAYERS if p['id'] not in drafted]
            data = {
                'available': available,
                'my_team': my_team
            }
            self.wfile.write(json.dumps(data).encode())
            
        elif parsed_path.path == '/api/draft':
            params = parse_qs(parsed_path.query)
            player_id = int(params['id'][0])
            
            # Draft the player
            for p in PLAYERS:
                if p['id'] == player_id and player_id not in drafted:
                    drafted.append(player_id)
                    my_team.append(p)
                    break
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_error(404)
            
    def log_message(self, format, *args):
        # Suppress logs for cleaner output
        pass

if __name__ == '__main__':
    print("🏈 ALFRED Basic Draft Assistant")
    print("=" * 50)
    print(f"Starting server on http://localhost:{PORT}")
    print("Opening browser...")
    print("\nPress Ctrl+C to stop")
    
    # Open browser
    webbrowser.open(f'http://localhost:{PORT}')
    
    # Start server
    with socketserver.TCPServer(("", PORT), DraftHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            httpd.shutdown()
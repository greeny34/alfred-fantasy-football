#!/usr/bin/env python3
"""
ALFRED - Improved Draft Assistant with Real Data
"""

import http.server
import socketserver
import json
import webbrowser
import csv
import os
from urllib.parse import urlparse, parse_qs

PORT = 8890

# Draft state
drafted = []
my_team = []
all_picks = []
current_pick = 1

def load_players_from_csv():
    """Try to load real player data from CSV files"""
    players = []
    
    # Try to find player data files
    csv_files = [
        'data/rankings/FF_2025_COMPLETE_DATA_REPOSITORY.csv',
        'data/rankings/players_export.csv',
        'data/rankings/rankings_export.csv'
    ]
    
    for csv_file in csv_files:
        if os.path.exists(csv_file):
            print(f"Loading players from {csv_file}")
            try:
                with open(csv_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Try different column name variations
                        name = row.get('Player') or row.get('player') or row.get('Name') or row.get('name', '')
                        pos = row.get('Position') or row.get('position') or row.get('Pos') or row.get('pos', '')
                        team = row.get('Team') or row.get('team', 'UNK')
                        
                        if name and pos:
                            players.append({
                                "id": len(players) + 1,
                                "name": name,
                                "pos": pos.upper(),
                                "team": team.upper()[:3],
                                "adp": len(players) + 1
                            })
                            
                if players:
                    print(f"Loaded {len(players)} players")
                    return players
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
    
    # Fallback to hardcoded players
    print("Using default player list")
    return [
        {"id": 1, "name": "Christian McCaffrey", "pos": "RB", "team": "SF", "adp": 1},
        {"id": 2, "name": "Justin Jefferson", "pos": "WR", "team": "MIN", "adp": 2},
        {"id": 3, "name": "Ja'Marr Chase", "pos": "WR", "team": "CIN", "adp": 3},
        {"id": 4, "name": "Austin Ekeler", "pos": "RB", "team": "LAC", "adp": 4},
        {"id": 5, "name": "Josh Allen", "pos": "QB", "team": "BUF", "adp": 5},
        {"id": 6, "name": "Travis Kelce", "pos": "TE", "team": "KC", "adp": 6},
        {"id": 7, "name": "Stefon Diggs", "pos": "WR", "team": "BUF", "adp": 7},
        {"id": 8, "name": "Saquon Barkley", "pos": "RB", "team": "NYG", "adp": 8},
        {"id": 9, "name": "Tyreek Hill", "pos": "WR", "team": "MIA", "adp": 9},
        {"id": 10, "name": "Patrick Mahomes", "pos": "QB", "team": "KC", "adp": 10},
        {"id": 11, "name": "Lamar Jackson", "pos": "QB", "team": "BAL", "adp": 11},
        {"id": 12, "name": "Jonathan Taylor", "pos": "RB", "team": "IND", "adp": 12},
        {"id": 13, "name": "Cooper Kupp", "pos": "WR", "team": "LAR", "adp": 13},
        {"id": 14, "name": "Davante Adams", "pos": "WR", "team": "LV", "adp": 14},
        {"id": 15, "name": "Nick Chubb", "pos": "RB", "team": "CLE", "adp": 15},
        {"id": 16, "name": "Mark Andrews", "pos": "TE", "team": "BAL", "adp": 16},
        {"id": 17, "name": "Derrick Henry", "pos": "RB", "team": "TEN", "adp": 17},
        {"id": 18, "name": "CeeDee Lamb", "pos": "WR", "team": "DAL", "adp": 18},
        {"id": 19, "name": "Joe Burrow", "pos": "QB", "team": "CIN", "adp": 19},
        {"id": 20, "name": "AJ Brown", "pos": "WR", "team": "PHI", "adp": 20},
    ]

# Load players
PLAYERS = load_players_from_csv()

def get_recommendation():
    """Get draft recommendation based on team needs"""
    available = [p for p in PLAYERS if p['id'] not in drafted]
    if not available:
        return None
    
    # Count positions on my team
    my_positions = {}
    for p in my_team:
        pos = p['pos']
        my_positions[pos] = my_positions.get(pos, 0) + 1
    
    # Ideal roster construction (for first 10 picks)
    if len(my_team) < 10:
        # Priority order based on picks made
        if my_positions.get('RB', 0) < 2:
            # Need RBs
            rbs = [p for p in available if p['pos'] == 'RB']
            if rbs:
                return {"player": rbs[0], "reason": f"Fill RB spot ({my_positions.get('RB', 0)}/2)"}
        
        if my_positions.get('WR', 0) < 2:
            # Need WRs
            wrs = [p for p in available if p['pos'] == 'WR']
            if wrs:
                return {"player": wrs[0], "reason": f"Fill WR spot ({my_positions.get('WR', 0)}/2)"}
        
        if my_positions.get('QB', 0) == 0 and len(my_team) >= 4:
            # Need QB after getting some RB/WR
            qbs = [p for p in available if p['pos'] == 'QB']
            if qbs:
                return {"player": qbs[0], "reason": "Need a QB"}
        
        if my_positions.get('TE', 0) == 0 and len(my_team) >= 5:
            # Consider TE
            tes = [p for p in available if p['pos'] == 'TE'][:3]  # Only top 3 TEs
            if tes:
                return {"player": tes[0], "reason": "Elite TE available"}
    
    # Default: best available
    return {"player": available[0], "reason": "Best player available"}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Fantasy Draft Assistant</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        h1 { 
            color: #1e3a8a; 
            margin: 0;
            font-size: 2.5em;
        }
        .pick-info {
            background: #3b82f6;
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
            font-size: 1.2em;
        }
        .main-grid {
            display: grid;
            grid-template-columns: 300px 1fr 300px;
            gap: 20px;
        }
        .panel {
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .recommendation {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .recommendation h3 {
            margin: 0 0 10px 0;
            color: #d97706;
        }
        .players { 
            max-height: 600px;
            overflow-y: auto;
        }
        .player { 
            padding: 10px; 
            margin: 5px 0; 
            background: #f9fafb; 
            border: 1px solid #e5e7eb;
            border-radius: 5px; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            transition: all 0.2s;
        }
        .player:hover {
            background: #eff6ff;
            border-color: #3b82f6;
        }
        .player-info {
            flex: 1;
        }
        .player-name {
            font-weight: 600;
            color: #1f2937;
        }
        .player-details {
            font-size: 0.9em;
            color: #6b7280;
        }
        .position {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.85em;
            font-weight: 600;
            margin-right: 5px;
        }
        .position.QB { background: #fee2e2; color: #dc2626; }
        .position.RB { background: #dcfce7; color: #16a34a; }
        .position.WR { background: #dbeafe; color: #2563eb; }
        .position.TE { background: #fef3c7; color: #d97706; }
        .drafted { 
            background: #f3f4f6; 
            opacity: 0.6;
        }
        button { 
            background: #3b82f6; 
            color: white; 
            border: none; 
            padding: 8px 16px; 
            border-radius: 5px; 
            cursor: pointer;
            font-weight: 600;
            transition: background 0.2s;
        }
        button:hover { 
            background: #2563eb; 
        }
        button:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }
        .my-team .player { 
            background: #ecfdf5; 
            border-color: #10b981;
        }
        .recent-pick {
            padding: 8px;
            margin: 4px 0;
            background: #f9fafb;
            border-radius: 4px;
            font-size: 0.9em;
        }
        h2 {
            margin: 0 0 15px 0;
            color: #1f2937;
            font-size: 1.3em;
        }
        .position-summary {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f9fafb;
            border-radius: 8px;
        }
        .position-count {
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 ALFRED - Fantasy Draft Assistant</h1>
    </div>
    
    <div class="pick-info">
        <strong>Round <span id="round">1</span> - Pick <span id="currentPick">1</span></strong>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>My Team</h2>
            <div id="positionSummary" class="position-summary"></div>
            <div id="myTeam" class="my-team"></div>
        </div>
        
        <div class="panel">
            <div id="recommendation" class="recommendation"></div>
            <h2>Available Players</h2>
            <div id="players" class="players"></div>
        </div>
        
        <div class="panel">
            <h2>Recent Picks</h2>
            <div id="recentPicks"></div>
        </div>
    </div>
    
    <script>
        async function loadPlayers() {
            const response = await fetch('/api/state');
            const data = await response.json();
            
            // Update pick info
            document.getElementById('currentPick').textContent = data.current_pick;
            document.getElementById('round').textContent = Math.ceil(data.current_pick / 12);
            
            // Update recommendation
            const recDiv = document.getElementById('recommendation');
            if (data.recommendation) {
                recDiv.innerHTML = `
                    <h3>📊 Recommendation</h3>
                    <div class="player-name">${data.recommendation.player.name}</div>
                    <div>${data.recommendation.reason}</div>
                `;
            }
            
            // Update available players
            const playersDiv = document.getElementById('players');
            playersDiv.innerHTML = data.available.slice(0, 50).map(p => `
                <div class="player">
                    <div class="player-info">
                        <div class="player-name">${p.name}</div>
                        <div class="player-details">
                            <span class="position ${p.pos}">${p.pos}</span>
                            ${p.team}
                        </div>
                    </div>
                    <button onclick="draftPlayer(${p.id})">Draft</button>
                </div>
            `).join('');
            
            // Update my team
            const myTeamDiv = document.getElementById('myTeam');
            myTeamDiv.innerHTML = data.my_team.map(p => `
                <div class="player">
                    <div class="player-info">
                        <div class="player-name">${p.name}</div>
                        <div class="player-details">
                            <span class="position ${p.pos}">${p.pos}</span>
                            ${p.team}
                        </div>
                    </div>
                </div>
            `).join('');
            
            // Update position summary
            const positions = {};
            data.my_team.forEach(p => {
                positions[p.pos] = (positions[p.pos] || 0) + 1;
            });
            
            const summaryDiv = document.getElementById('positionSummary');
            summaryDiv.innerHTML = ['QB', 'RB', 'WR', 'TE'].map(pos => `
                <div class="position-count">
                    <span class="position ${pos}">${pos}</span>: ${positions[pos] || 0}
                </div>
            `).join('');
            
            // Update recent picks
            const picksDiv = document.getElementById('recentPicks');
            picksDiv.innerHTML = data.recent_picks.map(p => `
                <div class="recent-pick">
                    <strong>Pick ${p.pick}:</strong> ${p.name} (${p.pos})
                </div>
            `).join('');
        }
        
        async function draftPlayer(id) {
            await fetch(`/api/draft?id=${id}`);
            loadPlayers();
        }
        
        // Auto-refresh every 2 seconds
        loadPlayers();
        setInterval(loadPlayers, 2000);
    </script>
</body>
</html>
"""

class DraftHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global current_pick
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
            
        elif parsed_path.path == '/api/state':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            available = [p for p in PLAYERS if p['id'] not in drafted]
            recent = all_picks[-10:] if all_picks else []
            
            data = {
                'available': available,
                'my_team': my_team,
                'recent_picks': recent,
                'current_pick': current_pick,
                'recommendation': get_recommendation()
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
                    all_picks.append({
                        'pick': current_pick,
                        'name': p['name'],
                        'pos': p['pos'],
                        'team': 'user'
                    })
                    current_pick += 1
                    
                    # Simulate other teams drafting
                    if current_pick % 12 != 6:  # Not user's turn
                        available = [p for p in PLAYERS if p['id'] not in drafted]
                        if available:
                            cpu_pick = available[0]
                            drafted.append(cpu_pick['id'])
                            all_picks.append({
                                'pick': current_pick,
                                'name': cpu_pick['name'],
                                'pos': cpu_pick['pos'],
                                'team': 'cpu'
                            })
                            current_pick += 1
                    break
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode())
        else:
            self.send_error(404)
            
    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    print("🏈 ALFRED Improved Draft Assistant")
    print("=" * 50)
    print(f"Starting server on http://localhost:{PORT}")
    print("Opening browser...")
    print("\nPress Ctrl+C to stop")
    
    webbrowser.open(f'http://localhost:{PORT}')
    
    with socketserver.TCPServer(("", PORT), DraftHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            httpd.shutdown()
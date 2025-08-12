#!/usr/bin/env python3
"""
ALFRED - Real Database Version
This actually uses your PostgreSQL database with real player data
"""

import http.server
import socketserver
import json
import webbrowser
import psycopg2
from urllib.parse import urlparse, parse_qs

PORT = 9000

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'jeffgreenfield',
    'database': 'fantasy_draft_db'
}

# Draft state
drafted_player_ids = set()
my_team = []
all_picks = []
current_pick = 1

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG)

def get_top_players_by_position():
    """Get the best players by position from database"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    players = []
    
    # Get top players by position (simplified ranking)
    positions = ['QB', 'RB', 'WR', 'TE']
    
    for pos in positions:
        cur.execute("""
            SELECT player_id, name, position, team 
            FROM players 
            WHERE position = %s 
            AND name NOT LIKE '%%DST%%'
            ORDER BY name
            LIMIT 50
        """, (pos,))
        
        position_players = cur.fetchall()
        for i, p in enumerate(position_players):
            players.append({
                'id': p[0],
                'name': p[1],
                'pos': p[2], 
                'team': p[3],
                'adp': i + 1  # Simple ranking for now
            })
    
    cur.close()
    conn.close()
    
    # Sort by a simple fantasy relevance (QBs and top RBs/WRs first)
    def sort_key(player):
        pos_priority = {'QB': 1, 'RB': 2, 'WR': 3, 'TE': 4}
        # Prioritize well-known players (this is a hack, but works for demo)
        star_players = ['Josh Allen', 'Lamar Jackson', 'Christian McCaffrey', 'Austin Ekeler', 
                       'Justin Jefferson', 'Ja\'Marr Chase', 'Travis Kelce', 'Tyreek Hill']
        star_bonus = 0 if any(star in player['name'] for star in star_players) else 100
        return pos_priority.get(player['pos'], 5) * 100 + star_bonus + player['adp']
    
    players.sort(key=sort_key)
    return players[:100]  # Top 100 for draft

def get_recommendation(my_team):
    """Get smart draft recommendation"""
    available = [p for p in get_top_players_by_position() if p['id'] not in drafted_player_ids]
    if not available:
        return None
    
    # Count positions
    position_counts = {}
    for player in my_team:
        pos = player['pos']
        position_counts[pos] = position_counts.get(pos, 0) + 1
    
    # Draft strategy (simplified)
    team_size = len(my_team)
    
    if team_size < 2:
        # Start with RB or WR
        rbs = [p for p in available if p['pos'] == 'RB'][:5]
        wrs = [p for p in available if p['pos'] == 'WR'][:5]
        best_skill = (rbs + wrs)
        if best_skill:
            return {
                'player': best_skill[0], 
                'reason': 'Start with elite skill position player'
            }
    
    if position_counts.get('RB', 0) < 2:
        rbs = [p for p in available if p['pos'] == 'RB']
        if rbs:
            return {
                'player': rbs[0], 
                'reason': f'Need RB ({position_counts.get("RB", 0)}/2)'
            }
    
    if position_counts.get('WR', 0) < 2:
        wrs = [p for p in available if p['pos'] == 'WR']
        if wrs:
            return {
                'player': wrs[0], 
                'reason': f'Need WR ({position_counts.get("WR", 0)}/2)'
            }
    
    if position_counts.get('QB', 0) == 0 and team_size >= 4:
        qbs = [p for p in available if p['pos'] == 'QB']
        if qbs:
            return {
                'player': qbs[0], 
                'reason': 'Time to get your QB'
            }
    
    return {'player': available[0], 'reason': 'Best available'}

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Database Draft Assistant</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5;
        }
        .header { text-align: center; margin-bottom: 30px; }
        h1 { color: #1e40af; margin: 0; font-size: 2.5em; }
        .status { background: #3b82f6; color: white; padding: 15px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .main-grid { display: grid; grid-template-columns: 300px 1fr 300px; gap: 20px; }
        .panel { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .recommendation { background: #fef3c7; border: 2px solid #f59e0b; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .recommendation h3 { margin: 0 0 10px 0; color: #d97706; }
        .players { max-height: 500px; overflow-y: auto; }
        .player { 
            padding: 10px; margin: 5px 0; background: #f9fafb; border: 1px solid #e5e7eb;
            border-radius: 5px; display: flex; justify-content: space-between; align-items: center;
        }
        .player:hover { background: #eff6ff; border-color: #3b82f6; }
        .position { 
            display: inline-block; padding: 2px 8px; border-radius: 3px; 
            font-size: 0.85em; font-weight: 600; margin-right: 8px;
        }
        .position.QB { background: #fee2e2; color: #dc2626; }
        .position.RB { background: #dcfce7; color: #16a34a; }
        .position.WR { background: #dbeafe; color: #2563eb; }
        .position.TE { background: #fef3c7; color: #d97706; }
        button { 
            background: #3b82f6; color: white; border: none; padding: 8px 16px; 
            border-radius: 5px; cursor: pointer; font-weight: 600;
        }
        button:hover { background: #2563eb; }
        .my-team .player { background: #ecfdf5; border-color: #10b981; }
        .db-status { 
            background: #10b981; color: white; padding: 10px; border-radius: 5px; 
            text-align: center; margin-bottom: 20px; font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏈 ALFRED - Database Draft Assistant</h1>
        <div class="db-status">✅ Connected to PostgreSQL Database with Real NFL Players</div>
    </div>
    
    <div class="status">
        <strong>Round <span id="round">1</span> - Pick <span id="currentPick">1</span></strong>
    </div>
    
    <div class="main-grid">
        <div class="panel">
            <h2>My Team (<span id="teamSize">0</span>)</h2>
            <div id="positionCounts"></div>
            <div id="myTeam" class="my-team"></div>
        </div>
        
        <div class="panel">
            <div id="recommendation" class="recommendation"></div>
            <h2>Available Players (From Database)</h2>
            <div id="players" class="players"></div>
        </div>
        
        <div class="panel">
            <h2>Recent Picks</h2>
            <div id="recentPicks"></div>
        </div>
    </div>
    
    <script>
        async function loadState() {
            const response = await fetch('/api/state');
            const data = await response.json();
            
            // Update pick info
            document.getElementById('currentPick').textContent = data.current_pick;
            document.getElementById('round').textContent = Math.ceil(data.current_pick / 12);
            document.getElementById('teamSize').textContent = data.my_team.length;
            
            // Show recommendation
            const recDiv = document.getElementById('recommendation');
            if (data.recommendation) {
                recDiv.innerHTML = `
                    <h3>🎯 Recommendation</h3>
                    <div><strong>${data.recommendation.player.name}</strong> (${data.recommendation.player.pos}) - ${data.recommendation.player.team}</div>
                    <div style="margin-top:8px; font-style:italic;">${data.recommendation.reason}</div>
                `;
            }
            
            // Show available players
            const playersDiv = document.getElementById('players');
            playersDiv.innerHTML = data.available.slice(0, 30).map(p => `
                <div class="player">
                    <div>
                        <strong>${p.name}</strong><br>
                        <span class="position ${p.pos}">${p.pos}</span>${p.team}
                    </div>
                    <button onclick="draftPlayer(${p.id})">Draft</button>
                </div>
            `).join('');
            
            // Show my team
            const myTeamDiv = document.getElementById('myTeam');
            myTeamDiv.innerHTML = data.my_team.map(p => `
                <div class="player">
                    <div>
                        <strong>${p.name}</strong><br>
                        <span class="position ${p.pos}">${p.pos}</span>${p.team}
                    </div>
                </div>
            `).join('');
            
            // Show position counts
            const counts = {};
            data.my_team.forEach(p => counts[p.pos] = (counts[p.pos] || 0) + 1);
            document.getElementById('positionCounts').innerHTML = 
                ['QB', 'RB', 'WR', 'TE'].map(pos => 
                    `<span class="position ${pos}">${pos}</span>: ${counts[pos] || 0}`
                ).join(' | ');
            
            // Show recent picks
            document.getElementById('recentPicks').innerHTML = data.recent_picks.map(p => 
                `<div style="padding:5px; margin:3px 0; background:#f9fafb; border-radius:3px;">
                    Pick ${p.pick}: <strong>${p.name}</strong> (${p.pos})
                </div>`
            ).join('');
        }
        
        async function draftPlayer(id) {
            await fetch(`/api/draft?id=${id}`);
            loadState();
        }
        
        loadState();
        setInterval(loadState, 3000);
    </script>
</body>
</html>
"""

class DatabaseDraftHandler(http.server.SimpleHTTPRequestHandler):
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
            
            available = [p for p in get_top_players_by_position() if p['id'] not in drafted_player_ids]
            
            data = {
                'available': available,
                'my_team': my_team,
                'recent_picks': all_picks[-8:],
                'current_pick': current_pick,
                'recommendation': get_recommendation(my_team)
            }
            self.wfile.write(json.dumps(data).encode())
            
        elif parsed_path.path == '/api/draft':
            params = parse_qs(parsed_path.query)
            player_id = int(params['id'][0])
            
            # Find and draft the player
            all_players = get_top_players_by_position()
            for player in all_players:
                if player['id'] == player_id and player_id not in drafted_player_ids:
                    drafted_player_ids.add(player_id)
                    my_team.append(player)
                    all_picks.append({
                        'pick': current_pick,
                        'name': player['name'],
                        'pos': player['pos']
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
    print("🏈 ALFRED - Database Draft Assistant")
    print("=" * 50)
    
    # Test database connection
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM players WHERE position IN ('QB','RB','WR','TE')")
        player_count = cur.fetchone()[0]
        print(f"✅ Connected to database with {player_count} fantasy players")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        exit(1)
    
    print(f"🚀 Starting server on http://localhost:{PORT}")
    print("Opening browser...")
    print("Press Ctrl+C to stop")
    
    webbrowser.open(f'http://localhost:{PORT}')
    
    with socketserver.TCPServer(("", PORT), DatabaseDraftHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            httpd.shutdown()
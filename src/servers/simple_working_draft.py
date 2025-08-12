#!/usr/bin/env python3
"""
ALFRED - Simple Working Draft Assistant
A simplified version that just works
"""

from flask import Flask, render_template, jsonify, request
import random
import json
import os

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# Simple in-memory data
players = []
draft_state = {
    'picks': [],
    'current_pick': 1,
    'user_team': []
}

def load_players():
    """Load some sample players"""
    global players
    positions = ['QB', 'RB', 'WR', 'TE']
    
    # Top players for 2025
    top_players = [
        {'name': 'Josh Allen', 'pos': 'QB', 'team': 'BUF', 'adp': 1},
        {'name': 'Lamar Jackson', 'pos': 'QB', 'team': 'BAL', 'adp': 2},
        {'name': 'Jonathan Taylor', 'pos': 'RB', 'team': 'IND', 'adp': 3},
        {'name': 'Austin Ekeler', 'pos': 'RB', 'team': 'LAC', 'adp': 4},
        {'name': 'Justin Jefferson', 'pos': 'WR', 'team': 'MIN', 'adp': 5},
        {'name': 'Ja\'Marr Chase', 'pos': 'WR', 'team': 'CIN', 'adp': 6},
        {'name': 'Travis Kelce', 'pos': 'TE', 'team': 'KC', 'adp': 7},
        {'name': 'Stefon Diggs', 'pos': 'WR', 'team': 'BUF', 'adp': 8},
    ]
    
    # Add more random players
    for i in range(len(top_players), 200):
        pos = random.choice(positions)
        players.append({
            'id': i + 1,
            'name': f'{pos} Player {i}',
            'pos': pos,
            'team': random.choice(['SF', 'DAL', 'GB', 'KC', 'BUF']),
            'adp': i + 1,
            'available': True
        })
    
    # Add top players
    for i, p in enumerate(top_players):
        p['id'] = i + 1
        p['available'] = True
        players.insert(i, p)

@app.route('/')
def index():
    """Serve a simple working interface"""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>ALFRED - Fantasy Draft Assistant</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
        h1 { color: #2563eb; text-align: center; }
        .draft-board { display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 20px; margin-top: 20px; }
        .panel { background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .player { padding: 8px; margin: 5px 0; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
        .player:hover { background: #e3f2fd; }
        .drafted { background: #ffebee; text-decoration: line-through; }
        button { background: #2563eb; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #1d4ed8; }
        .pick-info { text-align: center; font-size: 18px; margin: 20px 0; }
        .my-team { background: #e8f5e9; }
        .recommendation { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏈 ALFRED Fantasy Draft Assistant</h1>
        
        <div class="pick-info">
            <strong>Current Pick: <span id="currentPick">1</span></strong>
        </div>
        
        <div class="draft-board">
            <div class="panel">
                <h3>My Team</h3>
                <div id="myTeam"></div>
            </div>
            
            <div class="panel">
                <h3>Available Players</h3>
                <div class="recommendation">
                    <strong>Recommendation:</strong> <span id="recommendation">Loading...</span>
                </div>
                <div id="availablePlayers"></div>
            </div>
            
            <div class="panel">
                <h3>Recent Picks</h3>
                <div id="recentPicks"></div>
            </div>
        </div>
    </div>
    
    <script>
        let currentPick = 1;
        
        async function loadPlayers() {
            const response = await fetch('/api/players');
            const players = await response.json();
            displayPlayers(players);
            updateRecommendation();
        }
        
        function displayPlayers(players) {
            const container = document.getElementById('availablePlayers');
            container.innerHTML = players
                .filter(p => p.available)
                .slice(0, 50)
                .map(p => `
                    <div class="player" onclick="draftPlayer(${p.id})">
                        ${p.name} (${p.pos}) - ${p.team}
                    </div>
                `).join('');
        }
        
        async function draftPlayer(playerId) {
            const response = await fetch('/api/draft', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({player_id: playerId})
            });
            const result = await response.json();
            
            if (result.success) {
                loadPlayers();
                updateMyTeam();
                updateRecentPicks();
                document.getElementById('currentPick').textContent = result.current_pick;
            }
        }
        
        async function updateMyTeam() {
            const response = await fetch('/api/my-team');
            const team = await response.json();
            const container = document.getElementById('myTeam');
            container.innerHTML = team.map(p => `
                <div class="player my-team">
                    ${p.name} (${p.pos})
                </div>
            `).join('');
        }
        
        async function updateRecentPicks() {
            const response = await fetch('/api/recent-picks');
            const picks = await response.json();
            const container = document.getElementById('recentPicks');
            container.innerHTML = picks.map(p => `
                <div class="player drafted">
                    Pick ${p.pick}: ${p.name}
                </div>
            `).join('');
        }
        
        async function updateRecommendation() {
            const response = await fetch('/api/recommendation');
            const rec = await response.json();
            document.getElementById('recommendation').textContent = 
                rec.player ? `${rec.player.name} (${rec.reason})` : 'No recommendation';
        }
        
        // Initialize
        loadPlayers();
        setInterval(() => {
            updateRecommendation();
        }, 5000);
    </script>
</body>
</html>
    '''

@app.route('/api/players')
def get_players():
    return jsonify(players)

@app.route('/api/draft', methods=['POST'])
def draft_player():
    data = request.json
    player_id = data['player_id']
    
    # Find and draft player
    for p in players:
        if p['id'] == player_id:
            p['available'] = False
            draft_state['picks'].append({
                'pick': draft_state['current_pick'],
                'player': p,
                'team': 'user' if draft_state['current_pick'] % 12 == 6 else 'cpu'
            })
            if draft_state['current_pick'] % 12 == 6:
                draft_state['user_team'].append(p)
            draft_state['current_pick'] += 1
            break
    
    # Simulate CPU picks
    if draft_state['current_pick'] % 12 != 6:
        available = [p for p in players if p['available']]
        if available:
            cpu_pick = available[0]  # Simple: take best available
            cpu_pick['available'] = False
            draft_state['picks'].append({
                'pick': draft_state['current_pick'],
                'player': cpu_pick,
                'team': 'cpu'
            })
            draft_state['current_pick'] += 1
    
    return jsonify({
        'success': True,
        'current_pick': draft_state['current_pick']
    })

@app.route('/api/my-team')
def my_team():
    return jsonify(draft_state['user_team'])

@app.route('/api/recent-picks')
def recent_picks():
    recent = draft_state['picks'][-10:]
    return jsonify([{
        'pick': p['pick'],
        'name': p['player']['name']
    } for p in reversed(recent)])

@app.route('/api/recommendation')
def recommendation():
    available = [p for p in players if p['available']]
    if not available:
        return jsonify({'player': None})
    
    # Simple recommendation logic
    my_positions = [p['pos'] for p in draft_state['user_team']]
    
    # Recommend based on need
    if 'RB' not in my_positions:
        rbs = [p for p in available if p['pos'] == 'RB']
        if rbs:
            return jsonify({'player': rbs[0], 'reason': 'You need a RB'})
    
    if 'WR' not in my_positions:
        wrs = [p for p in available if p['pos'] == 'WR']
        if wrs:
            return jsonify({'player': wrs[0], 'reason': 'You need a WR'})
    
    # Default: best available
    return jsonify({'player': available[0], 'reason': 'Best available'})

if __name__ == '__main__':
    load_players()
    print("🏈 ALFRED Draft Assistant")
    print("=" * 50)
    print("Opening http://localhost:5000")
    print("Press Ctrl+C to stop")
    
    # Try to open browser
    import webbrowser
    webbrowser.open('http://localhost:5000')
    
    app.run(port=5000, debug=False)
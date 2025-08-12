#!/usr/bin/env python3
"""
Fantasy Football Draft Assistant - Standalone Desktop App
Double-click to run - completely self-contained with embedded server
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import json
import sqlite3
import random
import time
from datetime import datetime
import os
from pathlib import Path

# Simple HTTP server for the web interface
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse as urlparse
from urllib.parse import parse_qs

class DraftAssistantServer:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.draft_engine = DraftEngine()
        
    def start_server(self):
        """Start the embedded web server"""
        handler = self.create_handler()
        self.server = HTTPServer(('localhost', self.port), handler)
        print(f"🚀 Server starting on http://localhost:{self.port}")
        self.server.serve_forever()
    
    def create_handler(self):
        """Create request handler with API endpoints"""
        draft_engine = self.draft_engine
        
        class APIHandler(SimpleHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith('/api/'):
                    self.handle_api_request()
                else:
                    self.serve_html()
            
            def do_POST(self):
                if self.path.startswith('/api/'):
                    self.handle_api_request()
                else:
                    self.send_error(404)
            
            def serve_html(self):
                """Serve the main HTML interface"""
                html_content = get_draft_interface_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-Length', len(html_content))
                self.end_headers()
                self.wfile.write(html_content.encode())
            
            def handle_api_request(self):
                """Handle API requests"""
                try:
                    if self.path == '/api/players':
                        players = draft_engine.get_available_players()
                        self.send_json_response(players)
                    
                    elif self.path == '/api/draft/new':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode())
                        session = draft_engine.create_session(data)
                        self.send_json_response(session)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/pick'):
                        session_id = self.path.split('/')[3]
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode())
                        result = draft_engine.make_pick(session_id, data['player_id'])
                        self.send_json_response(result)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/simulate'):
                        session_id = self.path.split('/')[3]
                        result = draft_engine.simulate_to_user_turn(session_id)
                        self.send_json_response(result)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/status'):
                        session_id = self.path.split('/')[3]
                        status = draft_engine.get_session_status(session_id)
                        self.send_json_response(status)
                    
                    else:
                        self.send_error(404)
                        
                except Exception as e:
                    print(f"API Error: {e}")
                    self.send_json_response({"error": str(e)}, 500)
            
            def send_json_response(self, data, status=200):
                """Send JSON response"""
                response = json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Length', len(response))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response)
        
        return APIHandler

class DraftEngine:
    def __init__(self):
        self.sessions = {}
        self.players = self.load_players()
        
    def load_players(self):
        """Load 2025 player data"""
        # This would connect to your real database
        # For now, creating sample 2025 data
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT', 'HOU', 'IND', 'JAX', 'TEN']
        
        players = []
        player_id = 1
        
        # Generate realistic 2025 players
        qb_names = ['Josh Allen', 'Lamar Jackson', 'Joe Burrow', 'Tua Tagovailoa', 'Aaron Rodgers']
        rb_names = ['Jonathan Taylor', 'Austin Ekeler', 'Nick Chubb', 'Joe Mixon', 'Saquon Barkley']
        wr_names = ['Stefon Diggs', 'Tyreek Hill', 'Ja\'Marr Chase', 'Mike Evans', 'DeAndre Hopkins']
        te_names = ['Travis Kelce', 'Mark Andrews', 'George Kittle', 'Kyle Pitts', 'T.J. Hockenson']
        
        all_names = qb_names + rb_names + wr_names + te_names
        
        for i, name in enumerate(all_names):
            if i < 5:
                pos = 'QB'
            elif i < 10:
                pos = 'RB'
            elif i < 15:
                pos = 'WR'
            else:
                pos = 'TE'
                
            players.append({
                'id': player_id,
                'name': name,
                'position': pos,
                'team': random.choice(teams),
                'adp': i + 1 + random.randint(-3, 3),
                'projected_points': 300 - (i * 10) + random.randint(-20, 20),
                'bye_week': random.randint(4, 14)
            })
            player_id += 1
        
        # Add more players to reach 200+
        for i in range(len(all_names), 200):
            pos = random.choice(positions)
            players.append({
                'id': player_id,
                'name': f'Player {player_id}',
                'position': pos,
                'team': random.choice(teams),
                'adp': i + 1,
                'projected_points': max(50, 250 - i + random.randint(-30, 30)),
                'bye_week': random.randint(4, 14)
            })
            player_id += 1
        
        return players
    
    def get_available_players(self):
        """Get all available players"""
        return sorted(self.players, key=lambda x: x['adp'])
    
    def create_session(self, data):
        """Create new draft session"""
        session_id = f"draft_{int(time.time())}"
        
        session = {
            'id': session_id,
            'name': data.get('league_name', 'My Draft 2025'),
            'user_position': data.get('draft_position', 6),
            'scoring': data.get('scoring', 'ppr'),
            'teams': 10,
            'rounds': 16,
            'current_pick': 1,
            'picks': [],
            'rosters': {i: [] for i in range(1, 11)},
            'available_players': [p['id'] for p in self.players],
            'created': datetime.now().isoformat()
        }
        
        self.sessions[session_id] = session
        return {'success': True, 'session_id': session_id, 'session': session}
    
    def make_pick(self, session_id, player_id):
        """Make a draft pick"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        # Find player
        player = next((p for p in self.players if p['id'] == player_id), None)
        if not player:
            return {'success': False, 'error': 'Player not found'}
        
        # Check if player is available
        if player_id not in session['available_players']:
            return {'success': False, 'error': 'Player already drafted'}
        
        # Determine which team is picking
        current_pick = session['current_pick']
        picking_team = self.get_picking_team(current_pick)
        
        # Make the pick
        pick = {
            'pick_number': current_pick,
            'round': (current_pick - 1) // 10 + 1,
            'team': picking_team,
            'player': player,
            'timestamp': datetime.now().isoformat()
        }
        
        session['picks'].append(pick)
        session['rosters'][picking_team].append(player)
        session['available_players'].remove(player_id)
        session['current_pick'] += 1
        
        return {'success': True, 'pick': pick}
    
    def simulate_to_user_turn(self, session_id):
        """Simulate AI picks until it's the user's turn"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        user_position = session['user_position']
        picks_made = 0
        
        while session['current_pick'] <= 160:  # 16 rounds * 10 teams
            current_pick = session['current_pick']
            picking_team = self.get_picking_team(current_pick)
            
            # If it's user's turn, stop
            if picking_team == user_position:
                break
            
            # AI makes pick
            ai_pick = self.get_ai_pick(session, picking_team)
            if ai_pick:
                self.make_pick(session_id, ai_pick['id'])
                picks_made += 1
            else:
                break  # No more players available
        
        return {'success': True, 'picks_simulated': picks_made, 'current_pick': session['current_pick']}
    
    def get_ai_pick(self, session, team):
        """Get AI's pick for a team"""
        available = [p for p in self.players if p['id'] in session['available_players']]
        if not available:
            return None
        
        # Simple AI: pick best available by ADP with some position logic
        team_roster = session['rosters'][team]
        positions_needed = self.get_positions_needed(team_roster)
        
        # Filter by position need
        preferred_players = [p for p in available if p['position'] in positions_needed]
        if not preferred_players:
            preferred_players = available
        
        # Pick best available (lowest ADP)
        return min(preferred_players, key=lambda x: x['adp'])
    
    def get_positions_needed(self, roster):
        """Determine what positions a team needs"""
        position_counts = {}
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Basic needs (this would be more sophisticated in real app)
        needs = []
        if position_counts.get('QB', 0) < 2:
            needs.append('QB')
        if position_counts.get('RB', 0) < 4:
            needs.append('RB')
        if position_counts.get('WR', 0) < 5:
            needs.append('WR')
        if position_counts.get('TE', 0) < 2:
            needs.append('TE')
        if position_counts.get('K', 0) < 1:
            needs.append('K')
        if position_counts.get('DST', 0) < 1:
            needs.append('DST')
        
        return needs if needs else ['RB', 'WR', 'QB', 'TE']
    
    def get_picking_team(self, pick_number):
        """Get which team is picking (snake draft)"""
        round_num = (pick_number - 1) // 10 + 1
        pick_in_round = (pick_number - 1) % 10 + 1
        
        if round_num % 2 == 1:  # Odd rounds go 1-10
            return pick_in_round
        else:  # Even rounds go 10-1
            return 11 - pick_in_round
    
    def get_session_status(self, session_id):
        """Get current session status"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        current_pick = session['current_pick']
        picking_team = self.get_picking_team(current_pick) if current_pick <= 160 else None
        is_user_turn = picking_team == session['user_position'] if picking_team else False
        
        return {
            'success': True,
            'session': session,
            'current_pick': current_pick,
            'picking_team': picking_team,
            'is_user_turn': is_user_turn,
            'draft_complete': current_pick > 160
        }

def get_draft_interface_html():
    """Return the HTML interface"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏈 Fantasy Football Draft Assistant 2025</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .gradient-bg { background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%); }
        .card { backdrop-filter: blur(10px); background: rgba(255, 255, 255, 0.95); }
        .hidden { display: none; }
        .animate-fadeIn { animation: fadeIn 0.5s ease-in; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="min-h-screen gradient-bg">
    
    <!-- Welcome Screen -->
    <div id="welcomeScreen" class="min-h-screen flex items-center justify-center p-8">
        <div class="max-w-4xl mx-auto text-center animate-fadeIn">
            <h1 class="text-6xl font-bold text-white mb-6">
                🏈 Fantasy Football<br>
                <span class="text-yellow-300">Draft Assistant 2025</span>
            </h1>
            <p class="text-xl text-green-100 max-w-2xl mx-auto mb-12">
                Standalone desktop app with sophisticated AI opponents and real-time draft modeling
            </p>
            
            <div class="space-y-6">
                <button onclick="showSetup()" class="bg-yellow-400 hover:bg-yellow-300 text-gray-900 font-bold py-4 px-8 rounded-full text-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
                    🚀 Start New Draft
                </button>
            </div>
        </div>
    </div>

    <!-- Setup Screen -->
    <div id="setupScreen" class="hidden min-h-screen flex items-center justify-center p-8">
        <div class="max-w-2xl mx-auto animate-fadeIn">
            <div class="text-center mb-8">
                <button onclick="showWelcome()" class="text-white hover:text-yellow-300 mb-6 inline-flex items-center font-semibold">
                    ← Back
                </button>
                <h2 class="text-4xl font-bold text-white mb-4">Draft Setup 2025</h2>
            </div>

            <div class="card rounded-2xl p-8 border border-white/20 shadow-xl">
                <div class="space-y-6">
                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-3">League Name</label>
                        <input type="text" id="leagueName" value="My Draft 2025" 
                               class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg">
                    </div>

                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-3">Your Draft Position</label>
                        <select id="draftPosition" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg">
                            <option value="1">Pick 1 - First Overall</option>
                            <option value="2">Pick 2 - Early Pick</option>
                            <option value="3">Pick 3 - Early Pick</option>
                            <option value="4">Pick 4 - Middle Pick</option>
                            <option value="5">Pick 5 - Middle Pick</option>
                            <option value="6" selected>Pick 6 - Middle Pick</option>
                            <option value="7">Pick 7 - Middle Pick</option>
                            <option value="8">Pick 8 - Late Pick</option>
                            <option value="9">Pick 9 - Late Pick</option>
                            <option value="10">Pick 10 - Last Pick</option>
                        </select>
                    </div>

                    <div>
                        <label class="block text-sm font-bold text-gray-700 mb-3">Scoring Format</label>
                        <select id="scoringFormat" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all text-lg">
                            <option value="ppr">PPR (Point Per Reception)</option>
                            <option value="half_ppr">Half PPR (0.5 Points)</option>
                            <option value="standard">Standard (No Reception Points)</option>
                        </select>
                    </div>

                    <button onclick="createSession()" class="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-4 px-6 rounded-lg text-xl transition-all duration-300 transform hover:scale-105 shadow-lg">
                        🎯 Create Draft Session
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Draft Screen -->
    <div id="draftScreen" class="hidden min-h-screen p-4">
        <div class="container mx-auto max-w-7xl animate-fadeIn">
            <!-- Header -->
            <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h1 class="text-2xl font-bold text-gray-900">🏈 <span id="draftLeagueName">My Draft 2025</span></h1>
                        <p class="text-gray-600">Pick #<span id="currentPick">1</span> • Round <span id="currentRound">1</span> • Your Position: <span id="yourPosition">6</span></p>
                    </div>
                    <div class="flex space-x-2">
                        <button onclick="simulateToMyTurn()" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
                            🤖 Simulate to My Turn
                        </button>
                        <button onclick="showWelcome()" class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg">
                            ← New Draft
                        </button>
                    </div>
                </div>
                
                <!-- Status -->
                <div class="bg-blue-50 rounded-lg p-4">
                    <div id="turnStatus" class="text-blue-800 font-semibold">
                        🎯 Loading draft session...
                    </div>
                </div>
            </div>
            
            <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
                <!-- Available Players -->
                <div class="xl:col-span-2">
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h2 class="text-xl font-bold mb-4">👥 Available Players</h2>
                        <div id="availablePlayers" class="space-y-2 max-h-96 overflow-y-auto">
                            <!-- Players populated by JavaScript -->
                        </div>
                    </div>
                </div>
                
                <!-- Draft Info -->
                <div class="space-y-6">
                    <!-- Your Team -->
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h3 class="text-lg font-bold mb-4">🏆 Your Team</h3>
                        <div id="userRoster" class="space-y-2">
                            <!-- Roster populated by JavaScript -->
                        </div>
                    </div>
                    
                    <!-- Draft History -->
                    <div class="bg-white rounded-lg shadow-lg p-6">
                        <h3 class="text-lg font-bold mb-4">📜 Recent Picks</h3>
                        <div id="recentPicks" class="space-y-2 max-h-64 overflow-y-auto">
                            <!-- Recent picks populated by JavaScript -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let currentSession = null;
        let userPosition = 6;
        let isMyTurn = false;
        
        // Screen management
        function showScreen(screenId) {
            const screens = ['welcomeScreen', 'setupScreen', 'draftScreen'];
            screens.forEach(id => {
                document.getElementById(id).classList.add('hidden');
            });
            document.getElementById(screenId).classList.remove('hidden');
        }

        function showWelcome() { showScreen('welcomeScreen'); }
        function showSetup() { showScreen('setupScreen'); }
        function showDraft() { showScreen('draftScreen'); }
        
        // API functions
        async function createSession() {
            const data = {
                league_name: document.getElementById('leagueName').value,
                draft_position: parseInt(document.getElementById('draftPosition').value),
                scoring: document.getElementById('scoringFormat').value
            };
            
            try {
                const response = await fetch('/api/draft/new', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentSession = result.session_id;
                    userPosition = data.draft_position;
                    
                    // Update UI
                    document.getElementById('draftLeagueName').textContent = data.league_name;
                    document.getElementById('yourPosition').textContent = userPosition;
                    
                    showDraft();
                    await loadDraftState();
                } else {
                    alert('Failed to create session: ' + result.error);
                }
            } catch (error) {
                alert('Error creating session: ' + error.message);
            }
        }
        
        async function loadDraftState() {
            if (!currentSession) return;
            
            try {
                // Load session status
                const statusResponse = await fetch(`/api/draft/${currentSession}/status`);
                const status = await statusResponse.json();
                
                if (status.success) {
                    document.getElementById('currentPick').textContent = status.current_pick;
                    document.getElementById('currentRound').textContent = Math.ceil(status.current_pick / 10);
                    
                    isMyTurn = status.is_user_turn;
                    updateTurnStatus();
                    
                    // Load available players
                    await loadPlayers();
                    
                    // Update displays
                    updateRosterDisplay(status.session);
                    updateRecentPicks(status.session);
                }
            } catch (error) {
                console.error('Failed to load draft state:', error);
            }
        }
        
        async function loadPlayers() {
            try {
                const response = await fetch('/api/players');
                const players = await response.json();
                
                const container = document.getElementById('availablePlayers');
                container.innerHTML = players.slice(0, 50).map(player => `
                    <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-blue-50 cursor-pointer transition-colors ${isMyTurn ? 'hover:shadow-md' : ''}" 
                         ${isMyTurn ? `onclick="makePick(${player.id}, '${player.name}')"` : ''}>
                        <div class="flex-1">
                            <div class="font-semibold text-sm">${player.name}</div>
                            <div class="text-xs text-gray-600">${player.position} - ${player.team}</div>
                        </div>
                        <div class="text-right">
                            <div class="text-xs text-gray-500">ADP: ${player.adp}</div>
                            <div class="text-xs text-blue-600">${player.projected_points} pts</div>
                            ${isMyTurn ? '<div class="text-xs text-green-600 font-medium">Click to Draft</div>' : ''}
                        </div>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Failed to load players:', error);
            }
        }
        
        async function makePick(playerId, playerName) {
            if (!currentSession || !isMyTurn) return;
            
            if (!confirm(`Draft ${playerName}?`)) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/pick`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ player_id: playerId })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    await loadDraftState();
                    
                    // Auto-simulate to next user turn after a brief delay
                    if (!isMyTurn) {
                        setTimeout(simulateToMyTurn, 2000);
                    }
                } else {
                    alert('Failed to make pick: ' + result.error);
                }
            } catch (error) {
                alert('Error making pick: ' + error.message);
            }
        }
        
        async function simulateToMyTurn() {
            if (!currentSession) return;
            
            document.getElementById('turnStatus').innerHTML = '🤖 <strong>AI opponents are drafting...</strong>';
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/simulate`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    await loadDraftState();
                } else {
                    alert('Simulation failed: ' + result.error);
                }
            } catch (error) {
                console.error('Simulation error:', error);
            }
        }
        
        function updateTurnStatus() {
            const statusEl = document.getElementById('turnStatus');
            if (isMyTurn) {
                statusEl.innerHTML = '🎯 <strong>YOUR TURN!</strong> Select a player to draft';
                statusEl.className = 'text-green-800 font-bold';
            } else {
                statusEl.innerHTML = '🤖 <strong>AI opponents are picking...</strong>';
                statusEl.className = 'text-blue-800 font-semibold';
            }
        }
        
        function updateRosterDisplay(session) {
            if (!session || !session.rosters) return;
            
            const userRoster = session.rosters[userPosition] || [];
            const container = document.getElementById('userRoster');
            
            if (userRoster.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-sm">No players drafted yet</p>';
                return;
            }
            
            container.innerHTML = userRoster.map(player => `
                <div class="flex justify-between items-center p-2 bg-green-50 rounded border-l-4 border-green-500">
                    <div>
                        <div class="font-semibold text-sm">${player.name}</div>
                        <div class="text-xs text-gray-600">${player.position} - ${player.team}</div>
                    </div>
                    <div class="text-xs text-green-600 font-medium">${player.projected_points} pts</div>
                </div>
            `).join('');
        }
        
        function updateRecentPicks(session) {
            if (!session || !session.picks) return;
            
            const recentPicks = session.picks.slice(-10).reverse();
            const container = document.getElementById('recentPicks');
            
            if (recentPicks.length === 0) {
                container.innerHTML = '<p class="text-gray-500 text-sm">No picks yet</p>';
                return;
            }
            
            container.innerHTML = recentPicks.map(pick => `
                <div class="flex justify-between items-center p-2 bg-gray-50 rounded">
                    <div>
                        <div class="font-semibold text-sm">${pick.player.name}</div>
                        <div class="text-xs text-gray-600">${pick.player.position} - ${pick.player.team}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs text-gray-500">Pick ${pick.pick_number}</div>
                        <div class="text-xs text-blue-600">Team ${pick.team}</div>
                    </div>
                </div>
            `).join('');
        }
        
        // Auto-refresh draft state every 5 seconds
        setInterval(() => {
            if (currentSession && document.getElementById('draftScreen').classList.contains('hidden') === false) {
                loadDraftState();
            }
        }, 5000);
        
        console.log('🏈 Fantasy Football Draft Assistant 2025 - Standalone App Ready!');
    </script>
</body>
</html>'''

class DraftAssistantApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏈 Fantasy Football Draft Assistant 2025")
        self.root.geometry("600x400")
        self.root.configure(bg='#1f2937')
        
        self.server = None
        self.server_thread = None
        self.port = 8080
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the desktop app UI"""
        # Title
        title_frame = tk.Frame(self.root, bg='#1f2937')
        title_frame.pack(pady=40)
        
        title_label = tk.Label(
            title_frame, 
            text="🏈 Fantasy Football\nDraft Assistant 2025",
            font=('Arial', 24, 'bold'),
            fg='white',
            bg='#1f2937',
            justify='center'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Professional Interface with Database Integration",
            font=('Arial', 12),
            fg='#10b981',
            bg='#1f2937'
        )
        subtitle_label.pack(pady=(10, 0))
        
        # Status
        self.status_frame = tk.Frame(self.root, bg='#1f2937')
        self.status_frame.pack(pady=20)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready to start your draft!",
            font=('Arial', 11),
            fg='#d1d5db',
            bg='#1f2937'
        )
        self.status_label.pack()
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#1f2937')
        button_frame.pack(pady=30)
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Launch Draft Assistant",
            font=('Arial', 14, 'bold'),
            bg='#fbbf24',
            fg='#1f2937',
            activebackground='#f59e0b',
            activeforeground='#1f2937',
            padx=30,
            pady=15,
            cursor='hand2',
            command=self.launch_draft
        )
        self.start_button.pack(pady=10)
        
        self.quit_button = tk.Button(
            button_frame,
            text="❌ Quit",
            font=('Arial', 11),
            bg='#6b7280',
            fg='white',
            activebackground='#4b5563',
            activeforeground='white',
            padx=20,
            pady=10,
            cursor='hand2',
            command=self.quit_app
        )
        self.quit_button.pack(pady=(20, 0))
        
        # Info
        info_frame = tk.Frame(self.root, bg='#1f2937')
        info_frame.pack(side='bottom', pady=20)
        
        info_text = "✅ Professional web interface\n✅ PostgreSQL database integration\n✅ Advanced draft analytics\n✅ Multiple ranking sources"
        info_label = tk.Label(
            info_frame,
            text=info_text,
            font=('Arial', 9),
            fg='#9ca3af',
            bg='#1f2937',
            justify='left'
        )
        info_label.pack()
        
    def launch_draft(self):
        """Launch the draft assistant"""
        self.start_button.config(state='disabled', text='🔄 Starting...')
        self.status_label.config(text="Starting professional server...")
        
        # Start the professional Flask server instead
        import subprocess
        import sys
        import os
        
        # Get the correct path to alfred_main_server.py
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        server_path = os.path.join(project_root, "alfred_main_server.py")
        
        # Start server in background thread
        def start_professional_server():
            try:
                subprocess.run([sys.executable, server_path], 
                             cwd=project_root, 
                             capture_output=False)
            except Exception as e:
                print(f"Error starting professional server: {e}")
        
        self.server_thread = threading.Thread(target=start_professional_server, daemon=True)
        self.server_thread.start()
        
        # Update port to match professional server
        self.port = 5555
        
        # Wait a moment then open browser
        self.root.after(3000, self.open_browser)
        
    def open_browser(self):
        """Open the draft interface in browser"""
        try:
            url = f"http://localhost:{self.port}"
            webbrowser.open(url)
            
            self.status_label.config(text=f"✅ Draft Assistant running at {url}")
            self.start_button.config(text='🌐 Open in Browser Again', state='normal', command=self.open_browser)
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error opening browser: {e}")
            self.start_button.config(text='🚀 Launch Draft Assistant', state='normal')
    
    def quit_app(self):
        """Quit the application"""
        if self.server:
            try:
                self.server.server.shutdown()
            except:
                pass
        self.root.quit()
        
    def run(self):
        """Run the application"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🏈 Fantasy Football Draft Assistant 2025")
    print("========================================")
    print("Starting desktop application...")
    
    app = DraftAssistantApp()
    app.run()
#!/usr/bin/env python3
"""
ALFRED Main Server - Serves Your Professional Templates with Database
This is the server that provides access to your existing sophisticated work
"""

from flask import Flask, render_template, jsonify, request, redirect
import psycopg2
import os
import sys
import webbrowser
from datetime import datetime
import json
import signal
import threading

# Import our validation system
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.db.player_validation import PlayerValidator

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static'
)

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': os.environ.get('USER', 'jeffgreenfield'),
    'database': 'fantasy_draft_db'
}

def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def test_database():
    """Test database connection and return stats from master index"""
    validator = PlayerValidator()
    
    try:
        # Get all players from master index
        all_players = validator.get_all_players()
        
        # Calculate position counts
        position_counts = {}
        teams = set()
        
        for player in all_players:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
            teams.add(player['team'])
        
        # Convert to list format expected by template
        position_list = [(pos, count) for pos, count in sorted(position_counts.items())]
        
        # Get ranking source counts (separate from master index)
        conn = get_db_connection()
        source_counts = []
        if conn:
            try:
                cur = conn.cursor()
                cur.execute("""
                    SELECT rs.source_name, COUNT(pr.ranking_id)
                    FROM ranking_sources rs
                    LEFT JOIN player_rankings pr ON rs.source_id = pr.source_id
                    GROUP BY rs.source_name
                    ORDER BY COUNT(pr.ranking_id) DESC
                """)
                source_counts = cur.fetchall()
                cur.close()
            except Exception as e:
                print(f"Ranking source query error: {e}")
            finally:
                conn.close()
        
        return {
            'position_counts': position_list,
            'team_count': len(teams),
            'source_counts': source_counts,
            'teams': sorted(list(teams)),
            'total_players': len(all_players)
        }
        
    except Exception as e:
        print(f"Master index error: {e}")
        return None

@app.route('/')
def dashboard():
    """Serve the professional dashboard template"""
    stats = test_database()
    if not stats:
        return "Database connection failed. Make sure PostgreSQL is running and database exists.", 500
    
    return render_template('dashboard.html', 
                         position_counts=stats['position_counts'],
                         team_count=stats['team_count'],
                         source_counts=stats['source_counts'],
                         teams=stats['teams'])

@app.route('/draft_board')
def draft_board():
    """Serve the professional draft board template"""
    return render_template('draft_board.html')

@app.route('/spreadsheet')
def spreadsheet():
    """Serve the spreadsheet template if it exists"""
    try:
        return render_template('spreadsheet.html')
    except:
        return "Spreadsheet template not found", 404

# API Endpoints for the templates

@app.route('/api/players')
def api_players():
    """Get players with filters from master index + rankings"""
    validator = PlayerValidator()
    
    try:
        search = request.args.get('search', '').lower()
        position = request.args.get('position', '').upper()
        team = request.args.get('team', '').upper()
        
        # Get all players from master index
        all_players = validator.get_all_players()
        
        # Apply filters
        filtered_players = []
        for player in all_players:
            # Apply search filter
            if search and search not in player['name'].lower():
                continue
                
            # Apply position filter  
            if position and player['position'] != position:
                continue
                
            # Apply team filter
            if team and player['team'] != team:
                continue
                
            filtered_players.append(player)
        
        # Get ranking data for filtered players
        if filtered_players:
            conn = get_db_connection()
            if conn:
                try:
                    cur = conn.cursor()
                    
                    # Get rankings for these players
                    player_ids = [p['player_id'] for p in filtered_players]
                    placeholders = ','.join(['%s'] * len(player_ids))
                    
                    cur.execute(f"""
                        SELECT pr.player_id, rs.source_name, pr.position_rank
                        FROM player_rankings pr
                        JOIN ranking_sources rs ON pr.source_id = rs.source_id
                        WHERE pr.player_id IN ({placeholders})
                        ORDER BY pr.player_id, rs.source_name
                    """, player_ids)
                    
                    # Organize rankings by player
                    rankings_by_player = {}
                    for row in cur.fetchall():
                        player_id, source, rank = row
                        if player_id not in rankings_by_player:
                            rankings_by_player[player_id] = []
                        rankings_by_player[player_id].append({
                            'source': source,
                            'rank': rank
                        })
                    
                    cur.close()
                    
                    # Add rankings to player data
                    for player in filtered_players:
                        player['rankings'] = rankings_by_player.get(player['player_id'], [])
                    
                finally:
                    conn.close()
        
        # Sort by best average ranking, then name
        def sort_key(player):
            rankings = player.get('rankings', [])
            if rankings:
                avg_rank = sum(r['rank'] for r in rankings) / len(rankings)
                return (avg_rank, player['name'])
            else:
                return (999, player['name'])  # Unranked players last
        
        filtered_players.sort(key=sort_key)
        
        # Limit results
        return jsonify(filtered_players[:100])
        
    except Exception as e:
        print(f"API error: {e}")
        return jsonify([])

@app.route('/api/team_analysis/<team>')
def api_team_analysis(team):
    """Get team analysis (for dashboard)"""
    conn = get_db_connection()
    if not conn:
        return jsonify({})
    
    try:
        cur = conn.cursor()
        
        # Get players by position for this team
        cur.execute("""
            SELECT p.player_id, p.name, p.position,
                   array_agg(
                       json_build_object(
                           'source', rs.source_name,
                           'rank', pr.position_rank
                       )
                   ) FILTER (WHERE pr.position_rank IS NOT NULL) as rankings
            FROM players p
            LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
            LEFT JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE p.team = %s
            GROUP BY p.player_id, p.name, p.position
            ORDER BY p.position, p.name
        """, (team,))
        
        rows = cur.fetchall()
        
        team_data = {}
        for row in rows:
            position = row[2]
            if position not in team_data:
                team_data[position] = []
            
            rankings = row[3] if row[3] and row[3][0] is not None else []
            team_data[position].append({
                'name': row[1],
                'rankings': rankings
            })
        
        cur.close()
        conn.close()
        return jsonify(team_data)
        
    except Exception as e:
        print(f"Team analysis error: {e}")
        if conn:
            conn.close()
        return jsonify({})

# Draft Board API endpoints
@app.route('/api/draft/sessions', methods=['POST'])
def create_draft_session():
    """Create new draft session"""
    try:
        data = request.json
        # For now, return a simple success response
        # In a full implementation, this would create a database record
        return jsonify({
            'success': True,
            'session_id': f'draft_{int(datetime.now().timestamp())}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft/available-players/<session_id>')
def get_available_players(session_id):
    """Get available players for draft"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection failed'})
    
    try:
        cur = conn.cursor()
        
        # Get players with ADP (using a simple ranking as ADP for now)
        cur.execute("""
            SELECT p.player_id, p.name, p.position, p.team,
                   COALESCE(MIN(pr.position_rank), 999) as adp
            FROM players p
            LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
            WHERE p.position IN ('QB', 'RB', 'WR', 'TE')
            GROUP BY p.player_id, p.name, p.position, p.team
            ORDER BY adp, p.name
            LIMIT 200
        """)
        
        rows = cur.fetchall()
        players = []
        for i, row in enumerate(rows):
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'adp': row[4] if row[4] != 999 else i + 1
            })
        
        cur.close()
        conn.close()
        return jsonify({
            'success': True,
            'players': players
        })
        
    except Exception as e:
        print(f"Available players error: {e}")
        if conn:
            conn.close()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft/recommendations/<session_id>')
def get_draft_recommendations(session_id):
    """Get draft recommendations"""
    # Simple mock recommendations - would be more sophisticated in full implementation
    return jsonify({
        'success': True,
        'our_recommendations': [
            {
                'name': 'Christian McCaffrey',
                'position': 'RB',
                'reasoning': 'Elite RB1 with high floor and ceiling'
            }
        ],
        'adp_value_picks': [
            {
                'name': 'Josh Jacobs',
                'position': 'RB',
                'value_reason': 'Falling below ADP, great value'
            }
        ],
        'likely_next_picks': [
            {
                'name': 'Tyreek Hill',
                'position': 'WR',
                'adp': 8,
                'likelihood': 'High'
            }
        ]
    })

# Spreadsheet and Settings API endpoints
@app.route('/api/players/list')
def api_players_list():
    """Get all players with rankings for spreadsheet view - from master index"""
    validator = PlayerValidator()
    
    try:
        # Get all players from master index
        all_players = validator.get_all_players()
        
        # Filter to main fantasy positions for spreadsheet
        fantasy_players = [p for p in all_players if p['position'] in ('QB', 'RB', 'WR', 'TE')]
        
        if not fantasy_players:
            return jsonify([])
        
        conn = get_db_connection()
        result_players = []
        
        if conn:
            try:
                cur = conn.cursor()
                
                # Get all rankings for these players
                player_ids = [p['player_id'] for p in fantasy_players]
                placeholders = ','.join(['%s'] * len(player_ids))
                
                cur.execute(f"""
                    SELECT pr.player_id, rs.source_name, pr.position_rank, pr.overall_rank
                    FROM player_rankings pr
                    JOIN ranking_sources rs ON pr.source_id = rs.source_id
                    WHERE pr.player_id IN ({placeholders})
                    ORDER BY pr.player_id, rs.source_name
                """, player_ids)
                
                # Organize rankings by player and source
                rankings_by_player = {}
                for row in cur.fetchall():
                    player_id, source, pos_rank, overall_rank = row
                    if player_id not in rankings_by_player:
                        rankings_by_player[player_id] = {}
                    rankings_by_player[player_id][source] = pos_rank
                
                cur.close()
                
                # Process each player
                for player in fantasy_players:
                    player_rankings = rankings_by_player.get(player['player_id'], {})
                    
                    # Calculate stats if rankings exist
                    if player_rankings:
                        ranks = list(player_rankings.values())
                        mean_rank = sum(ranks) / len(ranks)
                        min_rank = min(ranks)
                        max_rank = max(ranks)
                        
                        # Calculate standard deviation
                        variance = sum((r - mean_rank) ** 2 for r in ranks) / len(ranks)
                        stdev = variance ** 0.5
                    else:
                        mean_rank = 999
                        min_rank = 999
                        max_rank = 999
                        stdev = 0
                    
                    result_players.append({
                        'id': player['player_id'],
                        'name': player['name'],
                        'position': player['position'],
                        'team': player['team'],
                        'rankings': player_rankings,
                        'stats': {
                            'mean': round(mean_rank, 1),
                            'min': int(min_rank),
                            'max': int(max_rank),
                            'stdev': round(stdev, 1)
                        }
                    })
                
            finally:
                conn.close()
        else:
            # Return players without rankings if DB connection fails
            for player in fantasy_players:
                result_players.append({
                    'id': player['player_id'],
                    'name': player['name'],
                    'position': player['position'],
                    'team': player['team'],
                    'rankings': {},
                    'stats': {
                        'mean': 999.0,
                        'min': 999,
                        'max': 999,
                        'stdev': 0.0
                    }
                })
        
        # Sort by mean ranking (best first), then by name
        result_players.sort(key=lambda p: (p['stats']['mean'], p['name']))
        
        return jsonify(result_players[:500])  # Limit to 500 for performance
        
    except Exception as e:
        print(f"Players list error: {e}")
        return jsonify([])

@app.route('/api/settings')
def api_settings():
    """Get current settings"""
    # Return default settings for now
    return jsonify({
        'scoring': 'ppr',
        'league_size': 12,
        'roster_positions': {
            'QB': 1,
            'RB': 2, 
            'WR': 2,
            'TE': 1,
            'FLEX': 1,
            'K': 1,
            'DST': 1,
            'BENCH': 6
        },
        'draft_position': 6
    })

@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    """Update settings"""
    # For now just return success
    return jsonify({'success': True})

@app.route('/api/team-preferences')
def api_team_preferences():
    """Get team preferences"""
    return jsonify({})

@app.route('/api/team-preferences', methods=['POST'])
def api_update_team_preferences():
    """Update team preferences"""
    return jsonify({'success': True})

@app.route('/api/team-preferences/<team>/<pref_type>', methods=['DELETE'])
def api_delete_team_preference(team, pref_type):
    """Delete team preference"""
    return jsonify({'success': True})

@app.route('/api/player-adjustments')
def api_player_adjustments():
    """Get player adjustments"""
    return jsonify({})

@app.route('/api/player-adjustments', methods=['POST'])
def api_add_player_adjustment():
    """Add player adjustment"""
    return jsonify({'success': True})

@app.route('/api/player-adjustments/<player_id>/<adj_type>', methods=['DELETE'])
def api_delete_player_adjustment(player_id, adj_type):
    """Delete player adjustment"""
    return jsonify({'success': True})

@app.route('/api/settings/reset', methods=['POST'])
def api_reset_settings():
    """Reset all settings"""
    return jsonify({'success': True})

# ADP and additional routes
@app.route('/adp')
def adp_view():
    """ADP rankings view"""
    try:
        return render_template('adp_rankings.html')
    except:
        return "ADP template not found", 404

@app.route('/draft')
def draft_redirect():
    """Redirect to draft board"""
    return redirect('/draft_board')

# Additional API endpoints that your templates might need
@app.route('/api/draft/pick', methods=['POST'])
def make_draft_pick():
    """Make a draft pick"""
    try:
        # This would integrate with your draft logic
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/draft/undo', methods=['POST'])
def undo_draft_pick():
    """Undo last draft pick"""
    try:
        # This would integrate with your draft logic
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Shutdown endpoint
@app.route('/shutdown', methods=['GET', 'POST'])
def shutdown():
    """Shutdown the server gracefully"""
    if request.method == 'GET':
        # Show confirmation page
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Shutdown ALFRED</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-danger text-white">
                                <h4 class="mb-0">🛑 Shutdown ALFRED</h4>
                            </div>
                            <div class="card-body">
                                <p>Are you sure you want to shut down the ALFRED server?</p>
                                <form method="POST">
                                    <button type="submit" class="btn btn-danger">Yes, Shutdown</button>
                                    <a href="/" class="btn btn-secondary">Cancel</a>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''
    else:
        # Perform shutdown
        def shutdown_server():
            os.kill(os.getpid(), signal.SIGINT)
        
        threading.Timer(1.0, shutdown_server).start()
        
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ALFRED Shutting Down</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        </head>
        <body>
            <div class="container mt-5">
                <div class="row justify-content-center">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header bg-success text-white">
                                <h4 class="mb-0">👋 ALFRED Shutting Down</h4>
                            </div>
                            <div class="card-body text-center">
                                <p>The ALFRED server is shutting down...</p>
                                <p>You can close this browser window.</p>
                                <hr>
                                <p class="text-muted">Thank you for using ALFRED!</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

if __name__ == '__main__':
    print("🏈 ALFRED - Professional Fantasy Football Assistant")
    print("=" * 60)
    
    # Test database connection
    stats = test_database()
    if not stats:
        print("❌ Database connection failed!")
        print("Make sure PostgreSQL is running and 'fantasy_draft_db' exists")
        sys.exit(1)
    
    print("✅ Master Player Index validated successfully!")
    print(f"📊 ALFRED contains {stats['total_players']} total players:")
    for pos, count in stats['position_counts']:
        print(f"   {pos}: {count} players")
    print(f"   Teams: {stats['team_count']}")
    print(f"   Ranking sources: {len(stats['source_counts'])}")
    print("   Data integrity: All external rankings validated against master index")
    
    print("\n🌐 Starting Flask server...")
    print(f"📍 Dashboard: http://localhost:5555/")
    print(f"🏈 Draft Board: http://localhost:5555/draft_board")
    print(f"📊 Spreadsheet: http://localhost:5555/spreadsheet")
    print(f"🛑 Shutdown: http://localhost:5555/shutdown")
    print("\nPress Ctrl+C to stop (or use the Shutdown button in the web interface)")
    
    # Open browser to dashboard
    webbrowser.open('http://localhost:5555/')
    
    try:
        app.run(host='127.0.0.1', port=5555, debug=False)
    except KeyboardInterrupt:
        print("\n👋 ALFRED shutting down...")
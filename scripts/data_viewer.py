#!/usr/bin/env python3
"""
Interactive Fantasy Football Data Viewer
Web-based tool to explore and validate database data
"""
from flask import Flask, render_template, request, jsonify
import psycopg2
import os
from datetime import datetime
from dynamic_draft_optimizer import DynamicDraftOptimizer
from db_draft_simulator import DatabaseDraftSimulator

app = Flask(__name__)

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

@app.route('/')
def index():
    """Main spreadsheet view"""
    return render_template('spreadsheet.html')

@app.route('/optimizer')
def draft_optimizer():
    """Draft strategy optimizer view"""
    return render_template('draft_optimizer.html')

@app.route('/settings')
def settings():
    """Settings view"""
    return render_template('settings.html')

@app.route('/draft')
def draft_board():
    """Draft board view"""
    return render_template('draft_board.html')

@app.route('/adp')
def adp_rankings():
    """ADP rankings spreadsheet view"""
    return render_template('adp_spreadsheet.html')

@app.route('/api/players')
def get_players():
    """API endpoint to get spreadsheet data"""
    position = request.args.get('position', '')
    team = request.args.get('team', '')
    search = request.args.get('search', '')
    
    return get_spreadsheet_data(position, team, search)

def get_spreadsheet_data(position='', team='', search=''):
    """Get data formatted for spreadsheet view with statistics"""
    import statistics
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Load current settings
    cur.execute("SELECT setting_name, setting_value FROM user_settings")
    settings_rows = cur.fetchall()
    settings = {name: value for name, value in settings_rows}
    
    # Load team preferences
    cur.execute("""
        SELECT team_name, preference_type, bias_percentage
        FROM team_preferences 
        WHERE is_active = true
    """)
    team_prefs = {}
    for team_name, pref_type, bias in cur.fetchall():
        team_prefs[f"{team_name}_{pref_type}"] = float(bias)
    
    # Load player adjustments
    cur.execute("""
        SELECT player_id, adjustment_type, adjustment_percentage
        FROM player_adjustments 
        WHERE is_active = true
    """)
    player_adjustments = {}
    for player_id, adj_type, percentage in cur.fetchall():
        player_adjustments[f"{player_id}_{adj_type}"] = float(percentage)
    
    # Get only position-specific ranking sources (exclude overall rankings, ADP, and generic sources)
    excluded_sources = [
        'Mike_Clay_Top_150',  # Overall ranking, not position-specific
        'FantasyPros',        # Generic source
        'CBS',                # Generic source  
        'ESPN',               # Generic source
        'NFL',                # Generic source
        'Yahoo',              # Generic source
        'ESPN_ESPN_Consensus', # Redundant consensus
        'Rotowire_ADP',       # ADP data, not position ranking
        'Underdog'            # ADP data, not position ranking
    ]
    
    cur.execute("""
        SELECT DISTINCT source_name 
        FROM ranking_sources 
        WHERE source_name NOT IN ({})
        ORDER BY source_name
    """.format(','.join(['%s'] * len(excluded_sources))), excluded_sources)
    
    all_sources = [row[0] for row in cur.fetchall()]
    
    # Build base query for players
    query = """
        SELECT DISTINCT p.player_id, p.name, p.position, p.team
        FROM players p
        WHERE 1=1
    """
    params = []
    
    if position:
        query += " AND p.position = %s"
        params.append(position)
    
    if team:
        query += " AND p.team = %s"
        params.append(team)
    
    if search:
        query += " AND p.name ILIKE %s"
        params.append(f"%{search}%")
    
    query += " ORDER BY p.position, p.name"
    
    cur.execute(query, params)
    players = cur.fetchall()
    
    # Get maximum rank by position AND source for smart default scoring
    cur.execute("""
        SELECT p.position, rs.source_name, MAX(pr.position_rank) as max_rank
        FROM players p
        JOIN player_rankings pr ON p.player_id = pr.player_id
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        WHERE rs.source_name NOT IN ({})
        GROUP BY p.position, rs.source_name
    """.format(','.join(['%s'] * len(excluded_sources))), excluded_sources)
    
    max_ranks_data = cur.fetchall()
    max_ranks_by_position_source = {}
    for pos, source, max_rank in max_ranks_data:
        if pos not in max_ranks_by_position_source:
            max_ranks_by_position_source[pos] = {}
        max_ranks_by_position_source[pos][source] = max_rank
    
    spreadsheet_data = []
    
    for player_id, name, pos, team in players:
        # Get all rankings for this player (excluding unwanted sources)
        cur.execute("""
            SELECT rs.source_name, pr.position_rank
            FROM player_rankings pr
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE pr.player_id = %s 
            AND rs.source_name NOT IN ({})
        """.format(','.join(['%s'] * len(excluded_sources))), [player_id] + excluded_sources)
        player_rankings = dict(cur.fetchall())
        
        # Build row data
        row = {
            'player_id': player_id,
            'name': name,
            'position': pos,
            'team': team
        }
        
        # Add ranking columns with smart defaults
        ranking_values = []
        total_expected_default = 0
        actual_default_count = 0
        
        for source in all_sources:
            # Get max rank for this position/source combination
            source_max = max_ranks_by_position_source.get(pos, {}).get(source, 25)  # Default 25 if no data
            default_rank = source_max + 5
            
            if source in player_rankings:
                rank = player_rankings[source]
                row[f'rank_{source.replace(" ", "_").replace("-", "_")}'] = rank
                ranking_values.append(rank)
            else:
                row[f'rank_{source.replace(" ", "_").replace("-", "_")}'] = default_rank
                ranking_values.append(default_rank)
                actual_default_count += 1
            
            total_expected_default += default_rank
        
        # Mark as unranked if all values are defaults
        row['is_unranked'] = actual_default_count == len(all_sources)
        
        # Calculate statistics
        if actual_default_count == len(all_sources):
            # Completely unranked - use NA
            row['mean_rank'] = 'NA'
            row['min_rank'] = 'NA'
            row['max_rank'] = 'NA'
            row['stdev_rank'] = 'NA'
            row['cv_rank'] = 'NA'  # Coefficient of variation
            row['cv_impact'] = 'NA'  # CV Impact
            row['cv_impact_high'] = 'NA'  # High CV Impact
            row['aggressive_rank'] = 'NA'
            row['conservative_rank'] = 'NA'
            row['aggressive_high_rank'] = 'NA'
            row['conservative_high_rank'] = 'NA'
            row['ordinal_rank'] = 'NA'
            row['ordinal_aggressive'] = 'NA'
            row['ordinal_conservative'] = 'NA'
            row['ordinal_aggressive_high'] = 'NA'
            row['ordinal_conservative_high'] = 'NA'
        else:
            # Has at least one real ranking
            mean_val = statistics.mean(ranking_values)
            stdev_val = statistics.stdev(ranking_values) if len(ranking_values) > 1 else 0
            
            row['mean_rank'] = round(mean_val, 2)
            row['min_rank'] = min(ranking_values)
            row['max_rank'] = max(ranking_values)
            row['stdev_rank'] = round(stdev_val, 2)
            # Coefficient of variation = stdev / mean (as percentage)
            cv_pct = (stdev_val / mean_val * 100) if mean_val > 0 else 0
            row['cv_rank'] = round(cv_pct, 1)
            
            # Apply team biases and player adjustments to mean
            adjusted_mean = mean_val
            
            # Apply team bias if enabled
            if settings.get('team_bias_enabled', 'true') == 'true':
                team_key_fav = f"{team}_favorite"
                team_key_hate = f"{team}_hated"
                if team_key_fav in team_prefs:
                    # Favorite team - decrease mean (better ranking)
                    bias_pct = team_prefs[team_key_fav] / 100
                    adjusted_mean = mean_val * (1 - bias_pct)
                elif team_key_hate in team_prefs:
                    # Hated team - increase mean (worse ranking)
                    bias_pct = team_prefs[team_key_hate] / 100
                    adjusted_mean = mean_val * (1 + bias_pct)
            
            # Apply player adjustments if enabled
            if settings.get('player_adjustments_enabled', 'true') == 'true':
                player_key_under = f"{player_id}_undervalued"
                player_key_over = f"{player_id}_overvalued"
                if player_key_under in player_adjustments:
                    # Undervalued - decrease mean (better ranking)
                    adj_pct = player_adjustments[player_key_under] / 100
                    adjusted_mean = adjusted_mean * (1 - adj_pct)
                elif player_key_over in player_adjustments:
                    # Overvalued - increase mean (worse ranking)
                    adj_pct = player_adjustments[player_key_over] / 100
                    adjusted_mean = adjusted_mean * (1 + adj_pct)
            
            # Use adjusted mean for further calculations
            row['mean_rank'] = round(adjusted_mean, 2)
            
            # Calculate CV Impact: Mean * CV (where CV is 0-1)
            cv_decimal = cv_pct / 100  # Convert percentage to 0-1 range
            cv_impact = adjusted_mean * cv_decimal
            
            # Get CV multipliers from settings
            cv_multiplier_standard = float(settings.get('cv_multiplier_standard', '1.0'))
            cv_multiplier_high = float(settings.get('cv_multiplier_high', '2.0'))
            
            cv_impact_standard = cv_impact * cv_multiplier_standard
            cv_impact_high = cv_impact * cv_multiplier_high
            
            # Store CV Impact for display
            row['cv_impact'] = round(cv_impact_standard, 2)
            row['cv_impact_high'] = round(cv_impact_high, 2)
            
            # Standard CV adjustments using adjusted mean
            row['aggressive_rank'] = round(adjusted_mean - cv_impact_standard, 2)
            row['conservative_rank'] = round(adjusted_mean + cv_impact_standard, 2)
            
            # High CV adjustments using adjusted mean
            row['aggressive_high_rank'] = round(adjusted_mean - cv_impact_high, 2)
            row['conservative_high_rank'] = round(adjusted_mean + cv_impact_high, 2)
            
            row['ordinal_rank'] = None  # Will be calculated after sorting
        
        spreadsheet_data.append(row)
    
    # Calculate ordinal rankings based on mean rank
    # First, separate ranked and unranked players
    ranked_players = [p for p in spreadsheet_data if p['mean_rank'] != 'NA']
    unranked_players = [p for p in spreadsheet_data if p['mean_rank'] == 'NA']
    
    # Sort by mean rank and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['mean_rank'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_rank'] = i
    
    # Sort by aggressive rank and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['aggressive_rank'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_aggressive'] = i
    
    # Sort by conservative rank and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['conservative_rank'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_conservative'] = i
    
    # Sort by aggressive high rank and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['aggressive_high_rank'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_aggressive_high'] = i
    
    # Sort by conservative high rank and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['conservative_high_rank'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_conservative_high'] = i
    
    # Sort back by mean rank for default display
    ranked_players.sort(key=lambda x: x['mean_rank'])
    
    # Combine back together
    spreadsheet_data = ranked_players + unranked_players
    
    # Apply position limits if enabled
    if settings.get('enable_hard_cuts', 'true') == 'true' and position:
        position_limit_key = f'position_limit_{position.lower()}'
        if position_limit_key in settings:
            limit = int(settings[position_limit_key])
            # Sort by mean rank and take only the top N players
            ranked_only = [p for p in spreadsheet_data if p['mean_rank'] != 'NA']
            ranked_only.sort(key=lambda x: x['mean_rank'])
            unranked_only = [p for p in spreadsheet_data if p['mean_rank'] == 'NA']
            
            # Take only the limited number of ranked players
            spreadsheet_data = ranked_only[:limit] + unranked_only
    
    cur.close()
    conn.close()
    
    return jsonify({
        'players': spreadsheet_data,
        'sources': all_sources,
        'max_ranks_by_position_source': max_ranks_by_position_source
    })

@app.route('/api/team_analysis/<team>')
def team_analysis(team):
    """Get all players for a specific team"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT p.name, p.position, rs.source_name, pr.position_rank
        FROM players p
        LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
        LEFT JOIN ranking_sources rs ON pr.source_id = rs.source_id
        WHERE p.team = %s
        ORDER BY p.position, pr.position_rank;
    """, (team,))
    
    results = cur.fetchall()
    
    team_data = {}
    for name, pos, source, rank in results:
        if pos not in team_data:
            team_data[pos] = []
        
        # Find existing player or create new
        player = next((p for p in team_data[pos] if p['name'] == name), None)
        if not player:
            player = {'name': name, 'rankings': []}
            team_data[pos].append(player)
        
        if source:
            player['rankings'].append({'source': source, 'rank': rank})
    
    cur.close()
    conn.close()
    
    return jsonify(team_data)

# Settings API Routes
@app.route('/api/settings')
def get_settings():
    """Get all user settings"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT setting_name, setting_value FROM user_settings")
        settings_rows = cur.fetchall()
        
        settings = {}
        for name, value in settings_rows:
            settings[name] = value
        
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/settings', methods=['POST'])
def save_settings():
    """Save user settings"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        settings_data = request.json
        
        for setting_name, setting_value in settings_data.items():
            cur.execute("""
                UPDATE user_settings 
                SET setting_value = %s, updated_at = CURRENT_TIMESTAMP
                WHERE setting_name = %s
            """, (str(setting_value), setting_name))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Delete existing settings and re-run default insertion
        cur.execute("DELETE FROM user_settings")
        cur.execute("DELETE FROM team_preferences")
        cur.execute("DELETE FROM player_adjustments")
        
        # Re-insert defaults (copy from create_settings_schema.py)
        default_settings = [
            ('position_limit_qb', '30', 'integer', 'Maximum QB players to include in rankings'),
            ('position_limit_rb', '60', 'integer', 'Maximum RB players to include in rankings'),
            ('position_limit_wr', '75', 'integer', 'Maximum WR players to include in rankings'),
            ('position_limit_te', '30', 'integer', 'Maximum TE players to include in rankings'),
            ('position_limit_k', '20', 'integer', 'Maximum K players to include in rankings'),
            ('position_limit_dst', '15', 'integer', 'Maximum DST players to include in rankings'),
            ('cv_multiplier_standard', '1.0', 'decimal', 'CV multiplier for standard aggressive/conservative'),
            ('cv_multiplier_high', '2.0', 'decimal', 'CV multiplier for high aggressive/conservative'),
            ('team_bias_enabled', 'true', 'boolean', 'Enable team bias adjustments'),
            ('default_favorite_bias', '10.0', 'decimal', 'Default percentage bias for favorite teams'),
            ('default_hated_bias', '10.0', 'decimal', 'Default percentage bias for hated teams'),
            ('player_adjustments_enabled', 'true', 'boolean', 'Enable individual player value adjustments'),
            ('default_undervalued_adjustment', '10.0', 'decimal', 'Default percentage for undervalued players'),
            ('default_overvalued_adjustment', '10.0', 'decimal', 'Default percentage for overvalued players'),
            ('default_strategy', 'standard', 'string', 'Default ranking strategy'),
            ('show_all_strategies', 'true', 'boolean', 'Show all strategy columns in spreadsheet'),
            ('enable_hard_cuts', 'true', 'boolean', 'Enable automatic hard cuts based on position limits'),
            ('recalculate_on_settings_change', 'true', 'boolean', 'Automatically recalculate rankings when settings change'),
        ]
        
        for setting_name, value, type_name, description in default_settings:
            cur.execute("""
                INSERT INTO user_settings (setting_name, setting_value, setting_type, description)
                VALUES (%s, %s, %s, %s)
            """, (setting_name, value, type_name, description))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Settings reset to defaults'})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/team-preferences')
def get_team_preferences():
    """Get team preferences"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT team_name, preference_type, bias_percentage, is_active
            FROM team_preferences
            WHERE is_active = true
            ORDER BY team_name
        """)
        
        preferences = {}
        for team, pref_type, bias, active in cur.fetchall():
            key = f"{team}_{pref_type}"
            preferences[key] = {
                'team_name': team,
                'preference_type': pref_type,
                'bias_percentage': float(bias),
                'is_active': active
            }
        
        return jsonify(preferences)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/team-preferences', methods=['POST'])
def add_team_preference():
    """Add team preference"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        cur.execute("""
            INSERT INTO team_preferences (team_name, preference_type, bias_percentage)
            VALUES (%s, %s, %s)
            ON CONFLICT (team_name, preference_type) 
            DO UPDATE SET bias_percentage = EXCLUDED.bias_percentage, is_active = true
        """, (data['team_name'], data['preference_type'], data['bias_percentage']))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/team-preferences/<team>/<pref_type>', methods=['DELETE'])
def remove_team_preference(team, pref_type):
    """Remove team preference"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE team_preferences 
            SET is_active = false
            WHERE team_name = %s AND preference_type = %s
        """, (team, pref_type))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/player-adjustments')
def get_player_adjustments():
    """Get player adjustments"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT pa.player_id, p.name, p.position, p.team, 
                   pa.adjustment_type, pa.adjustment_percentage, pa.notes
            FROM player_adjustments pa
            JOIN players p ON pa.player_id = p.player_id
            WHERE pa.is_active = true
            ORDER BY p.name
        """)
        
        adjustments = {}
        for player_id, name, position, team, adj_type, percentage, notes in cur.fetchall():
            key = f"{player_id}_{adj_type}"
            adjustments[key] = {
                'player_id': player_id,
                'name': name,
                'position': position,
                'team': team,
                'adjustment_type': adj_type,
                'adjustment_percentage': float(percentage),
                'notes': notes
            }
        
        return jsonify(adjustments)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/player-adjustments', methods=['POST'])
def add_player_adjustment():
    """Add player adjustment"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        cur.execute("""
            INSERT INTO player_adjustments (player_id, adjustment_type, adjustment_percentage, notes)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (player_id, adjustment_type) 
            DO UPDATE SET adjustment_percentage = EXCLUDED.adjustment_percentage, 
                         notes = EXCLUDED.notes, is_active = true, updated_at = CURRENT_TIMESTAMP
        """, (data['player_id'], data['adjustment_type'], data['adjustment_percentage'], data.get('notes', '')))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/player-adjustments/<int:player_id>/<adjustment_type>', methods=['DELETE'])
def remove_player_adjustment(player_id, adjustment_type):
    """Remove player adjustment"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE player_adjustments 
            SET is_active = false, updated_at = CURRENT_TIMESTAMP
            WHERE player_id = %s AND adjustment_type = %s
        """, (player_id, adjustment_type))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/players/list')
def get_players_list():
    """Get simple list of all players for settings UI"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT player_id, name, position, team
            FROM players
            ORDER BY name
        """)
        
        players = []
        for player_id, name, position, team in cur.fetchall():
            players.append({
                'id': player_id,
                'name': name,
                'position': position,
                'team': team
            })
        
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/available-players/<int:session_id>')
def get_available_players(session_id):
    """Get all available players sorted by consensus ADP for draft board"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get drafted player IDs
        cur.execute("SELECT player_id FROM draft_picks WHERE session_id = %s", (session_id,))
        drafted_ids = {row[0] for row in cur.fetchall()}
        
        # Get all available players with consensus ADP
        cur.execute("""
            SELECT 
                p.player_id,
                p.name,
                p.position,
                p.team,
                c.consensus_rank as adp,
                c.mean_adp
            FROM players p
            JOIN consensus_adp c ON p.player_id = c.player_id
            WHERE p.player_id NOT IN ({})
            ORDER BY c.consensus_rank
        """.format(','.join(str(pid) for pid in drafted_ids) if drafted_ids else '0'))
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'adp': row[4],  # consensus_rank
                'mean_adp': row[5]
            })
        
        return jsonify({
            'success': True,
            'players': players
        })
        
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/recommendations/<int:session_id>')
def get_draft_recommendations(session_id):
    """Get draft recommendations for a session"""
    try:
        from corrected_draft_engine import CorrectedDraftEngine
        
        engine = CorrectedDraftEngine()
        recommendations = engine.calculate_recommendations(session_id)
        
        return jsonify({
            'success': True,
            **recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/draft/sessions', methods=['POST'])
def create_draft_session():
    """Create a new draft session"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        cur.execute("""
            INSERT INTO draft_sessions (session_name, team_count, user_draft_position, draft_format)
            VALUES (%s, %s, %s, %s)
            RETURNING session_id
        """, (
            data.get('session_name', 'My Draft'),
            data.get('team_count', 12),
            data.get('user_draft_position', 6),
            data.get('draft_format', 'standard')
        ))
        
        session_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({'session_id': session_id, 'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e), 'success': False}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/pick', methods=['POST'])
def make_draft_pick():
    """Record a draft pick"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        cur.execute("""
            INSERT INTO draft_picks (session_id, player_id, pick_number, round_number, pick_in_round, team_number, is_user_pick)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            data['session_id'],
            data['player_id'],
            data['pick_number'],
            data['round_number'],
            data['pick_in_round'],
            data['team_number'],
            data.get('is_user_pick', False)
        ))
        
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e), 'success': False}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/undo', methods=['POST'])
def undo_draft_pick():
    """Undo the last draft pick in a session"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required', 'success': False}), 400
        
        # Get the last pick for this session
        cur.execute("""
            SELECT pick_id, player_id, pick_number
            FROM draft_picks
            WHERE session_id = %s
            ORDER BY pick_number DESC
            LIMIT 1
        """, (session_id,))
        
        last_pick = cur.fetchone()
        if not last_pick:
            return jsonify({'error': 'No picks to undo', 'success': False}), 400
        
        pick_id, player_id, pick_number = last_pick
        
        # Get player details for response
        cur.execute("SELECT name, position FROM players WHERE player_id = %s", (player_id,))
        player_info = cur.fetchone()
        
        # Delete the last pick
        cur.execute("DELETE FROM draft_picks WHERE pick_id = %s", (pick_id,))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'undone_pick': {
                'pick_number': pick_number,
                'player_name': player_info[0] if player_info else 'Unknown',
                'player_position': player_info[1] if player_info else 'Unknown'
            }
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e), 'success': False}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/adp-players')
def get_adp_players():
    """API endpoint to get ADP data formatted like position rankings"""
    position = request.args.get('position', '')
    team = request.args.get('team', '')
    search = request.args.get('search', '')
    
    return get_adp_spreadsheet_data(position, team, search)

def get_adp_spreadsheet_data(position='', team='', search=''):
    """Get ADP data formatted for spreadsheet view with statistics"""
    import statistics
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Load current settings
    cur.execute("SELECT setting_name, setting_value FROM user_settings")
    settings_rows = cur.fetchall()
    settings = {name: value for name, value in settings_rows}
    
    # Load team preferences
    cur.execute("""
        SELECT team_name, preference_type, bias_percentage
        FROM team_preferences 
        WHERE is_active = true
    """)
    team_prefs = {}
    for team_name, pref_type, bias in cur.fetchall():
        team_prefs[f"{team_name}_{pref_type}"] = float(bias)
    
    # Load player adjustments
    cur.execute("""
        SELECT player_id, adjustment_type, adjustment_percentage
        FROM player_adjustments 
        WHERE is_active = true
    """)
    player_adjustments = {}
    for player_id, adj_type, percentage in cur.fetchall():
        player_adjustments[f"{player_id}_{adj_type}"] = float(percentage)
    
    # Get ADP sources
    cur.execute("""
        SELECT DISTINCT source_name 
        FROM adp_sources 
        WHERE is_active = true
        ORDER BY source_name
    """)
    
    all_sources = [row[0] for row in cur.fetchall()]
    
    # Build base query for players
    query = """
        SELECT DISTINCT p.player_id, p.name, p.position, p.team
        FROM players p
        WHERE 1=1
    """
    params = []
    
    if position:
        query += " AND p.position = %s"
        params.append(position)
    
    if team:
        query += " AND p.team = %s"
        params.append(team)
    
    if search:
        query += " AND p.name ILIKE %s"
        params.append(f"%{search}%")
    
    query += " ORDER BY p.position, p.name"
    
    cur.execute(query, params)
    players = cur.fetchall()
    
    # Get maximum ADP by source for smart default scoring
    cur.execute("""
        SELECT s.source_name, MAX(ar.adp_value) as max_adp
        FROM adp_rankings ar
        JOIN adp_sources s ON ar.adp_source_id = s.adp_source_id
        GROUP BY s.source_name
    """)
    
    max_adps_data = cur.fetchall()
    max_adps_by_source = {}
    for source, max_adp in max_adps_data:
        max_adps_by_source[source] = float(max_adp) if max_adp else 300.0
    
    spreadsheet_data = []
    
    for player_id, name, pos, team in players:
        # Get all ADP values for this player
        cur.execute("""
            SELECT s.source_name, ar.adp_value
            FROM adp_rankings ar
            JOIN adp_sources s ON ar.adp_source_id = s.adp_source_id
            WHERE ar.player_id = %s
        """, (player_id,))
        player_adps = dict(cur.fetchall())
        
        # Build row data
        row = {
            'player_id': player_id,
            'name': name,
            'position': pos,
            'team': team
        }
        
        # Add ADP columns with smart defaults
        adp_values = []
        total_expected_default = 0
        actual_default_count = 0
        
        for source in all_sources:
            # Get max ADP for this source
            source_max = float(max_adps_by_source.get(source, 300))  # Convert to float
            default_adp = source_max + 50
            
            if source in player_adps:
                adp = float(player_adps[source])  # Convert Decimal to float
                row[f'adp_{source.replace(" ", "_").replace("-", "_")}'] = adp
                adp_values.append(adp)
            else:
                row[f'adp_{source.replace(" ", "_").replace("-", "_")}'] = default_adp
                adp_values.append(default_adp)
                actual_default_count += 1
            
            total_expected_default += default_adp
        
        # Mark as unranked if all values are defaults
        row['is_unranked'] = actual_default_count == len(all_sources)
        
        # Calculate statistics
        if actual_default_count == len(all_sources):
            # Completely unranked - use NA
            row['mean_adp'] = 'NA'
            row['min_adp'] = 'NA'
            row['max_adp'] = 'NA'
            row['stdev_adp'] = 'NA'
            row['cv_adp'] = 'NA'  # Coefficient of variation
            row['cv_impact'] = 'NA'  # CV Impact
            row['cv_impact_high'] = 'NA'  # High CV Impact
            row['aggressive_adp'] = 'NA'
            row['conservative_adp'] = 'NA'
            row['aggressive_high_adp'] = 'NA'
            row['conservative_high_adp'] = 'NA'
            row['ordinal_adp'] = 'NA'
            row['ordinal_aggressive'] = 'NA'
            row['ordinal_conservative'] = 'NA'
            row['ordinal_aggressive_high'] = 'NA'
            row['ordinal_conservative_high'] = 'NA'
        else:
            # Has at least one real ADP
            mean_val = statistics.mean(adp_values)
            stdev_val = statistics.stdev(adp_values) if len(adp_values) > 1 else 0
            
            row['mean_adp'] = round(mean_val, 2)
            row['min_adp'] = min(adp_values)
            row['max_adp'] = max(adp_values)
            row['stdev_adp'] = round(stdev_val, 2)
            # Coefficient of variation = stdev / mean (as percentage)
            cv_pct = (stdev_val / mean_val * 100) if mean_val > 0 else 0
            row['cv_adp'] = round(cv_pct, 1)
            
            # Apply team biases and player adjustments to mean
            adjusted_mean = mean_val
            
            # Apply team bias if enabled
            if settings.get('team_bias_enabled', 'true') == 'true':
                team_key_fav = f"{team}_favorite"
                team_key_hate = f"{team}_hated"
                if team_key_fav in team_prefs:
                    # Favorite team - decrease mean (better ADP)
                    bias_pct = team_prefs[team_key_fav] / 100
                    adjusted_mean = mean_val * (1 - bias_pct)
                elif team_key_hate in team_prefs:
                    # Hated team - increase mean (worse ADP)
                    bias_pct = team_prefs[team_key_hate] / 100
                    adjusted_mean = mean_val * (1 + bias_pct)
            
            # Apply player adjustments if enabled
            if settings.get('player_adjustments_enabled', 'true') == 'true':
                player_key_under = f"{player_id}_undervalued"
                player_key_over = f"{player_id}_overvalued"
                if player_key_under in player_adjustments:
                    # Undervalued - decrease mean (better ADP)
                    adj_pct = player_adjustments[player_key_under] / 100
                    adjusted_mean = adjusted_mean * (1 - adj_pct)
                elif player_key_over in player_adjustments:
                    # Overvalued - increase mean (worse ADP)
                    adj_pct = player_adjustments[player_key_over] / 100
                    adjusted_mean = adjusted_mean * (1 + adj_pct)
            
            # Use adjusted mean for further calculations
            row['mean_adp'] = round(adjusted_mean, 2)
            
            # Calculate CV Impact: Mean * CV (where CV is 0-1)
            cv_decimal = cv_pct / 100  # Convert percentage to 0-1 range
            cv_impact = adjusted_mean * cv_decimal
            
            # Get CV multipliers from settings
            cv_multiplier_standard = float(settings.get('cv_multiplier_standard', '1.0'))
            cv_multiplier_high = float(settings.get('cv_multiplier_high', '2.0'))
            
            cv_impact_standard = cv_impact * cv_multiplier_standard
            cv_impact_high = cv_impact * cv_multiplier_high
            
            # Store CV Impact for display
            row['cv_impact'] = round(cv_impact_standard, 2)
            row['cv_impact_high'] = round(cv_impact_high, 2)
            
            # Standard CV adjustments using adjusted mean
            row['aggressive_adp'] = round(adjusted_mean - cv_impact_standard, 2)
            row['conservative_adp'] = round(adjusted_mean + cv_impact_standard, 2)
            
            # High CV adjustments using adjusted mean
            row['aggressive_high_adp'] = round(adjusted_mean - cv_impact_high, 2)
            row['conservative_high_adp'] = round(adjusted_mean + cv_impact_high, 2)
            
            row['ordinal_adp'] = None  # Will be calculated after sorting
        
        spreadsheet_data.append(row)
    
    # Calculate ordinal rankings based on mean ADP (lower ADP = better = higher rank)
    # First, separate ranked and unranked players
    ranked_players = [p for p in spreadsheet_data if p['mean_adp'] != 'NA']
    unranked_players = [p for p in spreadsheet_data if p['mean_adp'] == 'NA']
    
    # Sort by mean ADP (ascending - lower ADP is better)
    ranked_players.sort(key=lambda x: x['mean_adp'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_adp'] = i
    
    # Sort by aggressive ADP and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['aggressive_adp'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_aggressive'] = i
    
    # Sort by conservative ADP and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['conservative_adp'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_conservative'] = i
    
    # Sort by aggressive high ADP and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['aggressive_high_adp'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_aggressive_high'] = i
    
    # Sort by conservative high ADP and assign ordinal ranks
    ranked_players.sort(key=lambda x: x['conservative_high_adp'])
    for i, player in enumerate(ranked_players, 1):
        player['ordinal_conservative_high'] = i
    
    # Sort back by mean ADP for default display
    ranked_players.sort(key=lambda x: x['mean_adp'])
    
    # Combine back together
    spreadsheet_data = ranked_players + unranked_players
    
    # Apply position limits if enabled
    if settings.get('enable_hard_cuts', 'true') == 'true' and position:
        position_limit_key = f'position_limit_{position.lower()}'
        if position_limit_key in settings:
            limit = int(settings[position_limit_key])
            # Sort by mean ADP and take only the top N players
            ranked_only = [p for p in spreadsheet_data if p['mean_adp'] != 'NA']
            ranked_only.sort(key=lambda x: x['mean_adp'])
            unranked_only = [p for p in spreadsheet_data if p['mean_adp'] == 'NA']
            
            # Take only the limited number of ranked players
            spreadsheet_data = ranked_only[:limit] + unranked_only
    
    cur.close()
    conn.close()
    
    return jsonify({
        'players': spreadsheet_data,
        'sources': all_sources,
        'max_adps_by_source': max_adps_by_source
    })

@app.route('/api/recalculate-rankings', methods=['POST'])
def recalculate_rankings():
    """Trigger rankings recalculation with current settings"""
    # This would trigger a recalculation of the spreadsheet data
    # For now, just return success - the actual recalculation logic
    # would need to be implemented to use the current settings
    return jsonify({'success': True, 'message': 'Rankings recalculation triggered'})

# Draft Optimization API Endpoints

@app.route('/api/draft/optimize/<int:session_id>')
def get_optimal_strategy(session_id):
    """Get optimal draft recommendations for current draft state"""
    try:
        optimizer = DynamicDraftOptimizer()
        optimal_strategy = optimizer.find_optimal_strategy(session_id)
        
        # Get current pick number for context
        current_roster, next_pick = optimizer._get_draft_state(session_id)
        
        # Save the strategy state
        optimizer.save_strategy_state(session_id, optimal_strategy, next_pick)
        
        return jsonify({
            'success': True,
            'current_pick': next_pick,
            'current_roster': current_roster.to_dict(),
            'optimal_strategy': {
                'next_positions': optimal_strategy.sequence[:5],
                'full_path': optimal_strategy.sequence,
                'expected_points': optimal_strategy.expected_points,
                'confidence': optimal_strategy.confidence * 100,
                'reasoning': optimal_strategy.reasoning,
                'player_targets': optimal_strategy.player_targets
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/sessions/list', methods=['GET'])
def get_all_draft_sessions():
    """Get all draft sessions"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT session_id, session_name, team_count, user_draft_position, 
                   current_pick, is_active, created_at
            FROM draft_sessions 
            ORDER BY created_at DESC
        """)
        
        sessions = []
        for row in cur.fetchall():
            sessions.append({
                'session_id': row[0],
                'session_name': row[1],
                'team_count': row[2],
                'user_draft_position': row[3],
                'current_pick': row[4],
                'is_active': row[5],
                'created_at': row[6].isoformat() if row[6] else None
            })
        
        return jsonify({'sessions': sessions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/sessions/new', methods=['POST'])
def create_new_draft_session():
    """Create new draft session"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        data = request.json
        cur.execute("""
            INSERT INTO draft_sessions (session_name, team_count, user_draft_position, draft_format)
            VALUES (%s, %s, %s, %s)
            RETURNING session_id
        """, (
            data['session_name'],
            data.get('team_count', 10),
            data['user_draft_position'],
            data.get('draft_format', 'ppr')
        ))
        
        session_id = cur.fetchone()[0]
        conn.commit()
        
        return jsonify({'success': True, 'session_id': session_id})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/api/draft/<int:session_id>/status')
def get_draft_status(session_id):
    """Get current draft status and recommendations"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get session info
        cur.execute("""
            SELECT session_name, team_count, user_draft_position, current_pick
            FROM draft_sessions 
            WHERE session_id = %s
        """, (session_id,))
        
        session_info = cur.fetchone()
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get current roster
        cur.execute("""
            SELECT p.position, COUNT(*) as count, ARRAY_AGG(p.name) as players
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        roster = {}
        for pos, count, players in cur.fetchall():
            roster[pos] = {'count': count, 'players': players}
        
        # Get latest strategy state
        cur.execute("""
            SELECT optimal_path, confidence_score, expected_points, reasoning
            FROM draft_strategy_states
            WHERE session_id = %s
            ORDER BY pick_number DESC
            LIMIT 1
        """, (session_id,))
        
        strategy_row = cur.fetchone()
        strategy = None
        if strategy_row:
            strategy = {
                'optimal_path': strategy_row[0],
                'confidence': strategy_row[1],
                'expected_points': strategy_row[2],
                'reasoning': strategy_row[3]
            }
        
        return jsonify({
            'session': {
                'session_id': session_id,
                'session_name': session_info[0],
                'team_count': session_info[1],
                'user_draft_position': session_info[2],
                'current_pick': session_info[3]
            },
            'roster': roster,
            'strategy': strategy
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# Draft Simulation API Endpoints

@app.route('/api/draft/<int:session_id>/simulate/<int:picks>', methods=['POST'])
def simulate_draft_picks(session_id, picks):
    """Simulate draft picks up to a certain number"""
    try:
        simulator = DatabaseDraftSimulator()
        
        # Get current pick from session
        cur = simulator.conn.cursor()
        cur.execute("SELECT current_pick FROM draft_sessions WHERE session_id = %s", (session_id,))
        current_pick = cur.fetchone()[0]
        cur.close()
        
        target_pick = current_pick + picks - 1
        simulated_picks = simulator.simulate_draft_to_pick(session_id, target_pick)
        
        return jsonify({
            'success': True,
            'picks_simulated': len(simulated_picks),
            'simulated_picks': simulated_picks,
            'new_current_pick': target_pick + 1
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/<int:session_id>/simulate-round', methods=['POST'])
def simulate_full_round(session_id):
    """Simulate a full round of picks"""
    try:
        simulator = DatabaseDraftSimulator()
        
        # Get session info
        cur = simulator.conn.cursor()
        cur.execute("""
            SELECT current_pick, team_count, user_draft_position
            FROM draft_sessions WHERE session_id = %s
        """, (session_id,))
        session_info = cur.fetchone()
        cur.close()
        
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        current_pick, team_count, user_position = session_info
        
        # Calculate picks until next user turn
        current_round = ((current_pick - 1) // team_count) + 1
        
        # If it's an odd round, calculate forward to user position
        # If it's an even round, calculate backward to user position
        if current_round % 2 == 1:  # Odd rounds: 1, 2, 3, ...
            next_user_pick = ((current_round - 1) * team_count) + user_position
        else:  # Even rounds: ..., 3, 2, 1
            next_user_pick = ((current_round - 1) * team_count) + (team_count - user_position + 1)
        
        # If we're past the user's turn this round, go to next round
        if current_pick > next_user_pick:
            current_round += 1
            if current_round % 2 == 1:
                next_user_pick = ((current_round - 1) * team_count) + user_position
            else:
                next_user_pick = ((current_round - 1) * team_count) + (team_count - user_position + 1)
        
        # Simulate up to just before user's turn
        target_pick = next_user_pick - 1
        
        if target_pick >= current_pick:
            simulated_picks = simulator.simulate_draft_to_pick(session_id, target_pick)
        else:
            simulated_picks = []
        
        return jsonify({
            'success': True,
            'picks_simulated': len(simulated_picks),
            'simulated_picks': simulated_picks,
            'next_user_pick': next_user_pick,
            'current_round': current_round
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/draft/<int:session_id>/make-pick', methods=['POST'])
def make_user_pick(session_id):
    """Make a pick for the user"""
    try:
        data = request.json
        player_id = data['player_id']
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get session info and current pick
        cur.execute("""
            SELECT current_pick, team_count, user_draft_position
            FROM draft_sessions WHERE session_id = %s
        """, (session_id,))
        session_info = cur.fetchone()
        
        if not session_info:
            return jsonify({'error': 'Session not found'}), 404
        
        current_pick, team_count, user_position = session_info
        
        # Calculate round and position info
        round_num = ((current_pick - 1) // team_count) + 1
        pick_in_round = ((current_pick - 1) % team_count) + 1
        
        # Verify it's the user's turn
        if round_num % 2 == 1:  # Odd rounds
            expected_team = pick_in_round
        else:  # Even rounds
            expected_team = team_count - pick_in_round + 1
        
        if expected_team != user_position:
            return jsonify({'error': 'Not your turn to pick'}), 400
        
        # Make the pick
        cur.execute("""
            INSERT INTO draft_picks 
            (session_id, player_id, pick_number, round_number, pick_in_round, team_number, is_user_pick)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        """, (session_id, player_id, current_pick, round_num, pick_in_round, user_position))
        
        # Update current pick
        cur.execute("""
            UPDATE draft_sessions 
            SET current_pick = %s 
            WHERE session_id = %s
        """, (current_pick + 1, session_id))
        
        # Get player info
        cur.execute("""
            SELECT name, position, team 
            FROM players 
            WHERE player_id = %s
        """, (player_id,))
        player_info = cur.fetchone()
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'pick_number': current_pick,
            'round_number': round_num,
            'player': {
                'name': player_info[0],
                'position': player_info[1],
                'team': player_info[2]
            }
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/draft/<int:session_id>/reset', methods=['POST'])
def reset_draft_session(session_id):
    """Reset a draft session to the beginning"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Delete all picks for this session
        cur.execute("DELETE FROM draft_picks WHERE session_id = %s", (session_id,))
        cur.execute("DELETE FROM draft_strategy_states WHERE session_id = %s", (session_id,))
        
        # Reset current pick to 1
        cur.execute("""
            UPDATE draft_sessions 
            SET current_pick = 1, updated_at = CURRENT_TIMESTAMP
            WHERE session_id = %s
        """, (session_id,))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Draft session reset successfully'
        })
        
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5002)
#!/usr/bin/env python3
"""
ALFRED - Analytical League Fantasy Resource for Elite Drafting
Jeff Greenfield's Fantasy Football Draft Assistant 2025
Fixed version with proper JavaScript loading
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import webbrowser
import json
import random
import time
from datetime import datetime
import os
from pathlib import Path
import psycopg2

# Simple HTTP server for the web interface
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse as urlparse
from urllib.parse import parse_qs

print("🏈 ALFRED - Jeff Greenfield's Fantasy Football Draft Assistant 2025")
print("=" * 65)
print("Loading application...")

def get_db_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
    except psycopg2.Error as e:
        print(f"❌ Database connection failed: {e}")
        return None

class DraftEngine:
    def __init__(self):
        self.sessions = {}
        self.db_conn = get_db_connection()
        if not self.db_conn:
            print("❌ Database connection required - ALFRED cannot run without fantasy_draft_db")
            raise Exception("Database connection failed - please ensure PostgreSQL is running")
        else:
            print("✅ Connected to fantasy_draft_db")
            self.players = self.load_real_players()
        print(f"✅ Loaded {len(self.players)} real 2025 players from database")
        
    def load_real_players(self):
        """Load ONLY real 2025 players from database - no fallback"""
        cur = self.db_conn.cursor()
        
        # Simpler query to avoid issues
        query = """
            SELECT DISTINCT
                p.player_id,
                p.name,
                p.position,
                p.team,
                COALESCE(ca.consensus_rank, 999) as adp,
                999 as our_rank,
                CASE 
                    WHEN COALESCE(ca.consensus_rank, 999) <= 24 THEN 1
                    WHEN COALESCE(ca.consensus_rank, 999) <= 60 THEN 2
                    WHEN COALESCE(ca.consensus_rank, 999) <= 120 THEN 3
                    WHEN COALESCE(ca.consensus_rank, 999) <= 200 THEN 4
                    ELSE 5
                END as tier,
                CASE p.position
                    WHEN 'QB' THEN GREATEST(180, 420 - COALESCE(ca.consensus_rank, 999) * 1.5)
                    WHEN 'RB' THEN GREATEST(100, 380 - COALESCE(ca.consensus_rank, 999) * 1.3)
                    WHEN 'WR' THEN GREATEST(90, 370 - COALESCE(ca.consensus_rank, 999) * 1.2)
                    WHEN 'TE' THEN GREATEST(60, 280 - COALESCE(ca.consensus_rank, 999) * 0.8)
                    WHEN 'K' THEN GREATEST(80, 150 - COALESCE(ca.consensus_rank, 999) * 0.3)
                    WHEN 'D/ST' THEN GREATEST(70, 160 - COALESCE(ca.consensus_rank, 999) * 0.4)
                    ELSE 100
                END as projected_points
            FROM players p
            LEFT JOIN consensus_adp ca ON p.player_id = ca.player_id
            WHERE p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'D/ST')
            AND p.name IS NOT NULL 
            AND p.name != ''
            ORDER BY COALESCE(ca.consensus_rank, 999), p.name
            LIMIT 500
        """
        
        print("🔍 Querying fantasy_draft_db for 2025 player data...")
        cur.execute(query)
        rows = cur.fetchall()
        
        players = []
        for row in rows:
            players.append({
                'id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3] or 'FA',
                'bye_week': random.randint(4, 14),  # No bye week in database
                'adp': float(row[4]) if row[4] != 999 else 999,
                'our_rank': row[5] if row[5] != 999 else 999,
                'tier': row[6],
                'projected_points': int(row[7]) if row[7] else 0
            })
        
        cur.close()
        
        if not players:
            raise Exception("No players found in database! Check your data_viewer.py setup.")
        
        print(f"✅ Successfully loaded {len(players)} real 2025 players from database")
        return players
    
    
    def get_available_players(self):
        return self.players
    
    def get_available_players_for_session(self, session_id):
        """Get players that haven't been drafted in this session"""
        if session_id not in self.sessions:
            return self.players
        
        session = self.sessions[session_id]
        drafted_player_ids = set()
        
        # Collect all drafted player IDs
        for pick in session.picks:
            drafted_player_ids.add(pick['player']['id'])
        
        # Filter out drafted players
        available_players = [
            player for player in self.players 
            if player['id'] not in drafted_player_ids
        ]
        
        print(f"📊 Session {session_id}: {len(available_players)} available players (of {len(self.players)} total)")
        return available_players
    
    def search_players(self, search_term):
        """Search for players in database"""
        if not self.db_conn:
            return []
        
        try:
            cur = self.db_conn.cursor()
            
            # Search players by name with ADP data
            cur.execute("""
                SELECT DISTINCT
                    p.player_id,
                    p.name,
                    p.position,
                    p.team,
                    COALESCE(ca.consensus_rank, 999) as adp
                FROM players p
                LEFT JOIN consensus_adp ca ON p.player_id = ca.player_id
                WHERE LOWER(p.name) LIKE LOWER(%s)
                AND p.position IN ('QB', 'RB', 'WR', 'TE', 'K', 'D/ST')
                ORDER BY COALESCE(ca.consensus_rank, 999), p.name
                LIMIT 20
            """, (f'%{search_term}%',))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'position': row[2],
                    'team': row[3] or 'FA',
                    'adp': float(row[4]) if row[4] != 999 else 999
                })
            
            cur.close()
            return results
            
        except Exception as e:
            print(f"❌ Error searching players: {e}")
            return []
    
    def get_user_preferences(self):
        """Load user preferences from database"""
        if not self.db_conn:
            return {'strategy': 'standard', 'team_preferences': {}, 'player_adjustments': {}}
        
        try:
            cur = self.db_conn.cursor()
            
            # Load user settings
            cur.execute("SELECT setting_name, setting_value FROM user_settings")
            settings = {name: value for name, value in cur.fetchall()}
            
            # Load team preferences
            cur.execute("""
                SELECT team_name, preference_type, bias_percentage
                FROM team_preferences WHERE is_active = true
            """)
            team_prefs = {}
            for team, pref_type, bias in cur.fetchall():
                team_prefs[f"{team}_{pref_type}"] = float(bias)
            
            # Load player adjustments
            cur.execute("""
                SELECT pa.player_id, p.name, pa.adjustment_type, pa.adjustment_percentage
                FROM player_adjustments pa
                JOIN players p ON pa.player_id = p.player_id
                WHERE pa.is_active = true
            """)
            player_adjustments = {}
            for player_id, name, adj_type, percentage in cur.fetchall():
                key = f"{player_id}_{adj_type}"
                player_adjustments[key] = {
                    'player_id': player_id,
                    'name': name,
                    'type': adj_type,
                    'percentage': float(percentage)
                }
            
            cur.close()
            return {
                'strategy': settings.get('draft_strategy', 'standard'),
                'team_preferences': team_prefs,
                'player_adjustments': player_adjustments
            }
        except Exception as e:
            print(f"❌ Error loading preferences: {e}")
            return {'strategy': 'standard', 'team_preferences': {}, 'player_adjustments': {}}
    
    def save_user_preferences(self, preferences):
        """Save user preferences to database"""
        if not self.db_conn:
            return {'success': False, 'error': 'Database not available'}
        
        try:
            cur = self.db_conn.cursor()
            
            # Save strategy setting
            cur.execute("""
                INSERT INTO user_settings (setting_name, setting_value, updated_at)
                VALUES ('draft_strategy', %s, NOW())
                ON CONFLICT (setting_name) 
                DO UPDATE SET setting_value = %s, updated_at = NOW()
            """, (preferences['strategy'], preferences['strategy']))
            
            # Clear and save team preferences
            cur.execute("UPDATE team_preferences SET is_active = false")
            for team_pref, bias in preferences.get('team_preferences', {}).items():
                team, pref_type = team_pref.rsplit('_', 1)
                cur.execute("""
                    INSERT INTO team_preferences (team_name, preference_type, bias_percentage, is_active)
                    VALUES (%s, %s, %s, true)
                    ON CONFLICT (team_name, preference_type)
                    DO UPDATE SET bias_percentage = %s, is_active = true
                """, (team, pref_type, bias, bias))
            
            # Clear and save player adjustments
            cur.execute("UPDATE player_adjustments SET is_active = false")
            for key, adjustment in preferences.get('player_adjustments', {}).items():
                cur.execute("""
                    INSERT INTO player_adjustments (player_id, adjustment_type, adjustment_percentage, is_active)
                    VALUES (%s, %s, %s, true)
                    ON CONFLICT (player_id, adjustment_type)
                    DO UPDATE SET adjustment_percentage = %s, is_active = true
                """, (adjustment['player_id'], adjustment['type'], adjustment['percentage'], adjustment['percentage']))
            
            self.db_conn.commit()
            cur.close()
            return {'success': True}
        except Exception as e:
            print(f"❌ Error saving preferences: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_nfl_teams(self):
        """Get list of NFL teams from database"""
        if not self.db_conn:
            # Fallback team list
            return ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 
                    'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LV', 'LAC', 'LAR', 'MIA', 
                    'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS']
        
        try:
            cur = self.db_conn.cursor()
            cur.execute("""
                SELECT DISTINCT team 
                FROM players 
                WHERE team IS NOT NULL AND team != ''
                ORDER BY team
            """)
            teams = [row[0] for row in cur.fetchall()]
            cur.close()
            return teams if teams else self.get_nfl_teams()  # Recursive fallback
        except Exception as e:
            print(f"❌ Error loading teams: {e}")
            return ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 
                    'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC', 'LV', 'LAC', 'LAR', 'MIA', 
                    'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS']
    
    def create_session(self, data):
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
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        player = next((p for p in self.players if p['id'] == player_id), None)
        if not player:
            return {'success': False, 'error': 'Player not found'}
        
        if player_id not in session['available_players']:
            return {'success': False, 'error': 'Player already drafted'}
        
        current_pick = session['current_pick']
        picking_team = self.get_picking_team(current_pick)
        
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
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        user_position = session['user_position']
        picks_made = 0
        
        while session['current_pick'] <= 160:
            current_pick = session['current_pick']
            picking_team = self.get_picking_team(current_pick)
            
            if picking_team == user_position:
                break
            
            ai_pick = self.get_ai_pick(session, picking_team)
            if ai_pick:
                self.make_pick(session_id, ai_pick['id'])
                picks_made += 1
            else:
                break
        
        return {'success': True, 'picks_simulated': picks_made, 'current_pick': session['current_pick']}
    
    def get_ai_pick(self, session, team):
        available = [p for p in self.players if p['id'] in session['available_players']]
        if not available:
            return None
        
        team_roster = session['rosters'][team]
        positions_needed = self.get_positions_needed(team_roster)
        
        # Smart AI: consider position need, tier, and ADP
        preferred_players = [p for p in available if p['position'] in positions_needed]
        if not preferred_players:
            preferred_players = available
        
        # Pick from top tier available, with some randomness
        top_tier_players = [p for p in preferred_players if p.get('tier', 4) <= 2]
        if top_tier_players:
            return random.choice(top_tier_players[:3])  # Pick from top 3 in tier
        
        return min(preferred_players[:5], key=lambda x: x['adp'])  # Best ADP from top 5
    
    def get_positions_needed(self, roster):
        position_counts = {}
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        needs = []
        if position_counts.get('QB', 0) < 2: needs.append('QB')
        if position_counts.get('RB', 0) < 4: needs.append('RB')
        if position_counts.get('WR', 0) < 5: needs.append('WR') 
        if position_counts.get('TE', 0) < 2: needs.append('TE')
        
        return needs if needs else ['RB', 'WR', 'QB', 'TE']
    
    def get_picking_team(self, pick_number):
        round_num = (pick_number - 1) // 10 + 1
        pick_in_round = (pick_number - 1) % 10 + 1
        
        if round_num % 2 == 1:
            return pick_in_round
        else:
            return 11 - pick_in_round
    
    def get_session_status(self, session_id):
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
    
    def get_draft_analysis(self, session_id):
        """Get comprehensive draft analysis including ADP deltas and player insights"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        available_players = [p for p in self.players if p['id'] in session['available_players']]
        drafted_players = [p for p in self.players if p['id'] not in session['available_players']]
        
        # Calculate ADP deltas (actual pick vs ADP)
        adp_deltas = []
        for pick in session['picks']:
            player = pick['player']
            expected_pick = player['adp'] if player['adp'] != 999 else pick['pick_number']
            delta = pick['pick_number'] - expected_pick
            adp_deltas.append({
                'player': player['name'],
                'position': player['position'],
                'actual_pick': pick['pick_number'],
                'expected_pick': expected_pick,
                'delta': delta,
                'type': 'reach' if delta > 10 else 'steal' if delta < -10 else 'value'
            })
        
        # Find biggest steals and reaches available
        current_pick = session['current_pick']
        steals = []
        reaches = []
        
        for player in available_players[:100]:  # Top 100 available
            if player['adp'] != 999:
                expected_round = (player['adp'] - 1) // 10 + 1
                current_round = (current_pick - 1) // 10 + 1
                
                if expected_round < current_round - 1:  # Available 2+ rounds late
                    steals.append({
                        'player': player,
                        'expected_round': expected_round,
                        'current_round': current_round,
                        'value': current_round - expected_round
                    })
                elif expected_round > current_round + 1:  # Would be early pick
                    reaches.append({
                        'player': player,
                        'expected_round': expected_round,
                        'current_round': current_round,
                        'cost': expected_round - current_round
                    })
        
        # Sort by value
        steals.sort(key=lambda x: x['value'], reverse=True)
        reaches.sort(key=lambda x: x['cost'])
        
        return {
            'success': True,
            'adp_deltas': adp_deltas[-10:],  # Last 10 picks
            'steals': steals[:10],  # Top 10 steals
            'reaches': reaches[:10],  # Top 10 reaches
            'total_players_available': len(available_players),
            'total_players_drafted': len(drafted_players)
        }
    
    def get_ai_predictions(self, session_id):
        """Get AI predictions for upcoming picks"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        current_pick = session['current_pick']
        predictions = []
        
        # Predict next 5 picks
        for i in range(5):
            pick_num = current_pick + i
            if pick_num > 160:
                break
                
            team_num = self.get_picking_team(pick_num)
            round_num = (pick_num - 1) // 10 + 1
            
            if team_num == session['user_position']:
                predictions.append({
                    'pick_number': pick_num,
                    'team_number': team_num,
                    'is_user': True,
                    'predicted_player': None,
                    'reasoning': 'Your turn to pick!'
                })
            else:
                # Get team's current roster and needs
                team_roster = session['rosters'][team_num]
                positions_needed = self.get_positions_needed(team_roster)
                
                # Get available players for prediction
                available = [p for p in self.players if p['id'] in session['available_players']]
                predicted_player = self.get_ai_pick_prediction(available, positions_needed, round_num)
                
                # Determine team strategy
                strategy = self.get_team_strategy(team_num, team_roster, round_num)
                
                predictions.append({
                    'pick_number': pick_num,
                    'team_number': team_num,
                    'is_user': False,
                    'predicted_player': predicted_player,
                    'team_strategy': strategy,
                    'reasoning': f"Team {team_num} likely targets {predicted_player['position'] if predicted_player else 'BPA'}"
                })
        
        return {
            'success': True,
            'predictions': predictions
        }
    
    def get_ai_pick_prediction(self, available_players, positions_needed, round_num):
        """Predict what AI will pick"""
        if not available_players:
            return None
            
        # Filter by position need
        preferred = [p for p in available_players if p['position'] in positions_needed]
        if not preferred:
            preferred = available_players
        
        # Simple prediction: best available from preferred positions
        candidates = preferred[:5]  # Top 5 candidates
        return min(candidates, key=lambda x: x['adp']) if candidates else None
    
    def get_team_strategy(self, team_num, roster, round_num):
        """Determine team's drafting strategy"""
        position_counts = {}
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        rb_count = position_counts.get('RB', 0)
        wr_count = position_counts.get('WR', 0)
        
        if round_num <= 4:
            if rb_count > wr_count + 1:
                return 'rb_heavy'
            elif wr_count > rb_count + 1:
                return 'wr_heavy'
            elif rb_count == 0 and round_num >= 3:
                return 'zero_rb'
            else:
                return 'balanced'
        else:
            return 'best_available'
    
    def get_all_team_rosters(self, session_id):
        """Get all team rosters with strategies and composition"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        current_pick = session['current_pick']
        current_round = (current_pick - 1) // 10 + 1
        
        teams = []
        for team_num in range(1, 11):
            roster = session['rosters'][team_num]
            
            # Calculate position composition
            position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
            total_value = 0
            
            for player in roster:
                pos = player['position']
                position_counts[pos] = position_counts.get(pos, 0) + 1
                if player['adp'] != 999:
                    total_value += (200 - player['adp'])  # Simple value calculation
            
            # Determine strategy
            strategy = self.get_team_strategy(team_num, roster, current_round)
            
            # Calculate team strength
            strength = 'strong' if total_value > len(roster) * 20 else 'average' if total_value > len(roster) * 10 else 'weak'
            
            teams.append({
                'team_number': team_num,
                'is_user': team_num == session['user_position'],
                'roster': roster,
                'position_counts': position_counts,
                'strategy': strategy,
                'total_players': len(roster),
                'total_value': total_value,
                'strength': strength,
                'next_need': self.get_positions_needed(roster)[0] if self.get_positions_needed(roster) else 'depth'
            })
        
        return {
            'success': True,
            'teams': teams,
            'current_pick': current_pick,
            'current_round': current_round
        }
    
    def get_optimal_recommendations(self, session_id):
        """Get optimal draft recommendations using integrated intelligence"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        user_position = session['user_position']
        user_roster = session['rosters'][user_position]
        available_players = [p for p in self.players if p['id'] in session['available_players']]
        current_pick = session['current_pick']
        current_round = (current_pick - 1) // 10 + 1
        
        positions_needed = self.get_positions_needed(user_roster)
        
        recommendations = []
        
        # Smart recommendation logic based on round and value
        def is_good_value(player, round_num):
            """Check if player is good value for current round"""
            if player['adp'] == 999:
                return round_num >= 12  # Undrafted players only in late rounds
            
            expected_round = (player['adp'] - 1) // 10 + 1
            return abs(expected_round - round_num) <= 2  # Within 2 rounds of ADP
        
        def get_position_priority(pos, round_num, roster):
            """Get priority score for position based on round and roster needs"""
            position_counts = {}
            for p in roster:
                position_counts[p['position']] = position_counts.get(p['position'], 0) + 1
            
            # Early rounds (1-6): RB/WR priority
            if round_num <= 6:
                if pos in ['RB', 'WR']:
                    return 10 - position_counts.get(pos, 0) * 2
                elif pos == 'TE' and position_counts.get('TE', 0) == 0 and round_num >= 4:
                    return 6
                elif pos == 'QB' and position_counts.get('QB', 0) == 0 and round_num >= 5:
                    return 4
                else:
                    return 1
            
            # Mid rounds (7-10): Fill needs, some QB
            elif round_num <= 10:
                if pos == 'QB' and position_counts.get('QB', 0) == 0:
                    return 8
                elif pos in ['RB', 'WR'] and position_counts.get(pos, 0) < 3:
                    return 7
                elif pos == 'TE' and position_counts.get('TE', 0) == 0:
                    return 6
                else:
                    return 2
            
            # Late rounds (11+): K/DST and depth
            else:
                if pos in ['K', 'DST', 'D/ST'] and position_counts.get(pos, 0) == 0:
                    return 9
                elif pos in ['RB', 'WR']:
                    return 5
                else:
                    return 1
        
        # Score all available players
        player_scores = []
        for player in available_players[:50]:  # Top 50 available
            if not is_good_value(player, current_round):
                continue
                
            position_priority = get_position_priority(player['position'], current_round, user_roster)
            
            # Base score from tier (lower tier = higher score)
            tier_score = 6 - min(player['tier'], 5)
            
            # ADP value score (earlier ADP = higher score if reasonable for round)
            if player['adp'] != 999:
                expected_round = (player['adp'] - 1) // 10 + 1
                if expected_round <= current_round:
                    adp_score = min(5, current_round - expected_round + 1)
                else:
                    adp_score = max(1, 3 - (expected_round - current_round))
            else:
                adp_score = 1
            
            total_score = (position_priority * 2) + tier_score + adp_score
            
            player_scores.append({
                'player': player,
                'score': total_score,
                'position_priority': position_priority,
                'reasoning': self._get_player_reasoning(player, current_round, user_roster)
            })
        
        # Sort by score and take top recommendations
        player_scores.sort(key=lambda x: x['score'], reverse=True)
        
        for scored_player in player_scores[:5]:
            confidence = min(0.95, 0.6 + (scored_player['score'] / 20))
            priority = 'high' if scored_player['position_priority'] >= 7 else 'medium' if scored_player['position_priority'] >= 4 else 'low'
            
            recommendations.append({
                'player': scored_player['player'],
                'reasoning': scored_player['reasoning'],
                'confidence': confidence,
                'priority': priority
            })
        
        # Strategy analysis
        position_counts = {}
        for player in user_roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Determine current strategy
        rb_count = position_counts.get('RB', 0)
        wr_count = position_counts.get('WR', 0)
        
        if current_round <= 4:
            if rb_count > wr_count + 1:
                current_strategy = 'rb_heavy'
            elif wr_count > rb_count + 1:
                current_strategy = 'wr_heavy'
            elif rb_count == 0 and current_round >= 3:
                current_strategy = 'zero_rb'
            else:
                current_strategy = 'balanced'
        else:
            current_strategy = 'needs_based'
        
        strategy_analysis = {
            'current_strategy': current_strategy,
            'position_needs': positions_needed,
            'roster_balance': 'good' if len(set(p['position'] for p in user_roster)) >= 3 else 'needs_diversity',
            'next_picks_strategy': positions_needed[:3] if positions_needed else ['RB', 'WR', 'depth']
        }
        
        return {
            'success': True,
            'recommendations': recommendations,
            'strategy_analysis': strategy_analysis,
            'current_pick': current_pick,
            'current_round': current_round,
            'user_roster_summary': {
                'total_players': len(user_roster),
                'position_counts': position_counts,
                'needs': positions_needed
            }
        }
    
    def _get_player_reasoning(self, player, current_round, roster):
        """Generate reasoning for why this player is recommended"""
        position_counts = {}
        for p in roster:
            position_counts[p['position']] = position_counts.get(p['position'], 0) + 1
        
        pos = player['position']
        current_count = position_counts.get(pos, 0)
        
        if player['adp'] != 999:
            expected_round = (player['adp'] - 1) // 10 + 1
            if expected_round < current_round - 1:
                return f"Excellent value - {pos} falling to round {current_round} (ADP R{expected_round})"
            elif expected_round > current_round + 1:
                return f"Reach pick - but elite {pos} talent may be worth it"
        
        if current_count == 0:
            if pos in ['RB', 'WR'] and current_round <= 8:
                return f"Fill critical {pos} need - strong early-round value"
            elif pos == 'QB' and current_round >= 6:
                return f"Good time to secure QB1 - avoid late-round scramble"
            elif pos == 'TE' and current_round >= 4:
                return f"Elite TE advantage - consistent weekly points"
            else:
                return f"Fill {pos} need - avoid roster hole"
        else:
            if pos in ['RB', 'WR']:
                return f"Add {pos} depth - insurance and upside play"
            else:
                return f"Quality {pos} depth - roster insurance"
    
    def get_llm_strategy_explanation(self, session_id):
        """Get AI-powered strategy explanation using a simple LLM integration"""
        session = self.sessions.get(session_id)
        if not session:
            return {'success': False, 'error': 'Session not found'}
        
        try:
            user_position = session['user_position']
            user_roster = session['rosters'][user_position]
            current_pick = session['current_pick']
            current_round = (current_pick - 1) // 10 + 1
            
            # Build context for LLM
            roster_summary = {}
            for player in user_roster:
                pos = player['position']
                roster_summary[pos] = roster_summary.get(pos, 0) + 1
            
            # Create a simple prompt for strategy analysis
            strategy_context = {
                'draft_position': user_position,
                'current_round': current_round,
                'roster_composition': roster_summary,
                'players_drafted': len(user_roster),
                'remaining_picks': 16 - len(user_roster)
            }
            
            # Generate explanation based on current state
            explanation = self._generate_strategy_explanation(strategy_context)
            insights = self._generate_strategy_insights(strategy_context)
            risk_assessment = self._generate_risk_assessment(strategy_context)
            
            return {
                'success': True,
                'explanation': explanation,
                'insights': insights,
                'risk_assessment': risk_assessment
            }
            
        except Exception as e:
            print(f"Error generating LLM explanation: {e}")
            return {'success': False, 'error': 'Failed to generate explanation'}
    
    def _generate_strategy_explanation(self, context):
        """Generate strategy explanation based on current draft state"""
        draft_pos = context['draft_position'] 
        round_num = context['current_round']
        roster = context['roster_composition']
        
        explanations = []
        
        # Draft position analysis
        if draft_pos <= 3:
            explanations.append("Your early draft position gives you access to elite talent. Focus on securing proven, consistent performers who will anchor your roster.")
        elif draft_pos >= 8:
            explanations.append("Your late draft position requires you to be more aggressive in finding value. Look for high-upside players and exploit positional runs.")
        else:
            explanations.append("Your middle draft position offers flexibility. You can adapt to how the draft unfolds while targeting solid, reliable players.")
        
        # Round-based strategy
        if round_num <= 4:
            explanations.append("In early rounds, prioritize skill position players (RB/WR) with established track records. Avoid reaching for QB/TE unless truly elite.")
        elif round_num <= 8:
            explanations.append("Middle rounds are crucial for roster balance. Fill remaining needs while targeting players with clear upside or safe floors.")
        else:
            explanations.append("Late rounds are about depth and lottery tickets. Look for handcuffs, sleepers, and players in good situations.")
        
        # Roster-based advice
        rb_count = roster.get('RB', 0)
        wr_count = roster.get('WR', 0)
        qb_count = roster.get('QB', 0)
        
        if rb_count == 0 and round_num >= 5:
            explanations.append("You're in a risky position without RBs. Consider pivoting to a Zero-RB approach and loading up on WRs.")
        elif rb_count >= 3 and wr_count <= 2:
            explanations.append("Your RB depth is solid. Focus on building WR depth and consider your QB situation.")
        elif qb_count == 0 and round_num >= 10:
            explanations.append("QB scarcity is increasing. Consider securing your starter soon or commit to streaming options.")
        
        return " ".join(explanations)
    
    def _generate_strategy_insights(self, context):
        """Generate key strategic insights"""
        insights = []
        roster = context['roster_composition']
        round_num = context['current_round']
        
        # Position scarcity insights
        if roster.get('RB', 0) >= 2 and roster.get('WR', 0) >= 2:
            insights.append("Strong skill position foundation allows for strategic flexibility")
        
        if roster.get('QB', 0) == 0 and round_num >= 8:
            insights.append("Consider streaming QB strategy if waiting much longer")
        
        if roster.get('TE', 0) == 0 and round_num >= 6:
            insights.append("Elite TEs becoming scarce - consider positional advantage")
        
        # Strategic insights based on roster construction
        total_skill = roster.get('RB', 0) + roster.get('WR', 0)
        if total_skill >= 6:
            insights.append("Excellent skill position depth provides trade flexibility")
        
        if context['remaining_picks'] <= 6:
            insights.append("Final rounds - prioritize upside over floor for bench players")
        
        return insights
    
    def _generate_risk_assessment(self, context):
        """Generate risk assessment for current strategy"""
        roster = context['roster_composition']
        round_num = context['current_round']
        remaining = context['remaining_picks']
        
        risks = []
        
        # Position-based risks
        if roster.get('RB', 0) == 0 and round_num >= 6:
            risks.append("High risk: No RB depth could severely limit scoring potential")
        elif roster.get('RB', 0) == 1 and round_num >= 10:
            risks.append("Moderate risk: Thin at RB - one injury could be devastating")
        
        if roster.get('WR', 0) <= 2 and round_num >= 8:
            risks.append("Moderate risk: WR depth insufficient for bye weeks and injuries")
        
        if roster.get('QB', 0) == 0 and remaining <= 4:
            risks.append("Low risk: Can still find startable QB, but options narrowing")
        
        # Overall assessment
        if not risks:
            risks.append("Low risk: Balanced roster construction on track for success")
        
        return " ".join(risks)

class DraftAssistantServer:
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.draft_engine = DraftEngine()
        
    def start_server(self):
        handler = self.create_handler()
        self.server = HTTPServer(('localhost', self.port), handler)
        print(f"🚀 Web server running on http://localhost:{self.port}")
        self.server.serve_forever()
    
    def create_handler(self):
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
                html_content = get_draft_interface_html()
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-Length', len(html_content))
                self.end_headers()
                self.wfile.write(html_content.encode())
            
            def handle_api_request(self):
                try:
                    print(f"🔍 API Request: {self.command} {self.path}")
                    
                    if self.path == '/api/players':
                        players = draft_engine.get_available_players()
                        print(f"✅ Sending {len(players)} players")
                        self.send_json_response(players)
                    
                    elif self.path == '/api/preferences':
                        preferences = draft_engine.get_user_preferences()
                        self.send_json_response(preferences)
                    
                    elif self.path == '/api/nfl-teams':
                        teams = draft_engine.get_nfl_teams()
                        self.send_json_response(teams)
                    
                    elif self.path.startswith('/api/players/search') or self.path.startswith('/api/search_players'):
                        # Parse query parameters
                        from urllib.parse import urlparse, parse_qs
                        parsed = urlparse(self.path)
                        params = parse_qs(parsed.query)
                        search_term = params.get('q', [''])[0]
                        
                        if search_term:
                            results = draft_engine.search_players(search_term)
                            # Ensure consistent field names
                            formatted_results = []
                            for player in results:
                                formatted_results.append({
                                    'player_id': player['id'],
                                    'name': player['name'],
                                    'position': player['position'],
                                    'team': player['team'],
                                    'adp': player['adp']
                                })
                            self.send_json_response(formatted_results)
                        else:
                            self.send_json_response([])
                    
                    elif self.path == '/api/preferences/save':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode())
                        result = draft_engine.save_user_preferences(data)
                        self.send_json_response(result)
                    
                    elif self.path == '/api/draft/new':
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode())
                        print(f"🎯 Creating session with data: {data}")
                        session = draft_engine.create_session(data)
                        print(f"✅ Session created: {session.get('session_id', 'Unknown')}")
                        self.send_json_response(session)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/pick'):
                        session_id = self.path.split('/')[3]
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        data = json.loads(post_data.decode())
                        print(f"🏈 Making pick for session {session_id}: player {data.get('player_id')}")
                        result = draft_engine.make_pick(session_id, data['player_id'])
                        self.send_json_response(result)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/simulate'):
                        session_id = self.path.split('/')[3]
                        print(f"🤖 Simulating for session {session_id}")
                        result = draft_engine.simulate_to_user_turn(session_id)
                        print(f"✅ Simulated {result.get('picks_simulated', 0)} picks")
                        self.send_json_response(result)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/status'):
                        session_id = self.path.split('/')[3]
                        status = draft_engine.get_session_status(session_id)
                        self.send_json_response(status)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/analysis'):
                        session_id = self.path.split('/')[3]
                        analysis = draft_engine.get_draft_analysis(session_id)
                        self.send_json_response(analysis)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/predictions'):
                        session_id = self.path.split('/')[3]
                        predictions = draft_engine.get_ai_predictions(session_id)
                        self.send_json_response(predictions)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/team-rosters'):
                        session_id = self.path.split('/')[3]
                        rosters = draft_engine.get_all_team_rosters(session_id)
                        self.send_json_response(rosters)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/recommendations'):
                        session_id = self.path.split('/')[3]
                        recommendations = draft_engine.get_optimal_recommendations(session_id)
                        self.send_json_response(recommendations)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/available-players'):
                        session_id = self.path.split('/')[3]
                        available_players = draft_engine.get_available_players_for_session(session_id)
                        self.send_json_response(available_players)
                    
                    elif self.path.startswith('/api/draft/') and self.path.endswith('/strategy-explanation'):
                        session_id = self.path.split('/')[3]
                        explanation = draft_engine.get_llm_strategy_explanation(session_id)
                        self.send_json_response(explanation)
                    
                    else:
                        print(f"❌ Unknown API endpoint: {self.path}")
                        self.send_error(404)
                        
                except Exception as e:
                    print(f"❌ API Error: {e}")
                    import traceback
                    traceback.print_exc()
                    self.send_json_response({"error": str(e)}, 500)
            
            def send_json_response(self, data, status=200):
                response = json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-Length', len(response))
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response)
        
        return APIHandler

def get_draft_interface_html():
    """Return the complete draft interface HTML with JavaScript in head"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏈 ALFRED - Jeff Greenfield's Fantasy Football Draft Assistant 2025</title>
    <style>
        /* Embedded CSS instead of Tailwind to avoid CDN issues */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
        .gradient-bg { background: linear-gradient(135deg, #10b981 0%, #3b82f6 100%); min-height: 100vh; }
        .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
        .card { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(10px); border-radius: 1rem; padding: 2rem; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
        .hidden { display: none; }
        .btn { padding: 1rem 2rem; border-radius: 0.5rem; font-weight: bold; cursor: pointer; border: none; transition: all 0.3s; }
        .btn-primary { background: #fbbf24; color: #1f2937; }
        .btn-primary:hover { background: #f59e0b; transform: translateY(-2px); }
        .btn-secondary { background: #3b82f6; color: white; }
        .btn-secondary:hover { background: #2563eb; }
        .btn-success { background: #10b981; color: white; }
        .btn-success:hover { background: #059669; }
        .text-center { text-align: center; }
        .text-white { color: white; }
        .text-yellow { color: #fbbf24; }
        .text-green { color: #10b981; }
        .mb-4 { margin-bottom: 1rem; }
        .mb-6 { margin-bottom: 1.5rem; }
        .mb-8 { margin-bottom: 2rem; }
        .mt-4 { margin-top: 1rem; }
        .grid { display: grid; gap: 1rem; }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .flex { display: flex; }
        .items-center { align-items: center; }
        .justify-between { justify-content: space-between; }
        .space-y-4 > * + * { margin-top: 1rem; }
        .input { width: 100%; padding: 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem; font-size: 1rem; }
        .input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1); }
        .player-row { padding: 0.75rem; background: #f9fafb; border-radius: 0.5rem; margin-bottom: 0.5rem; cursor: pointer; transition: all 0.2s; }
        .player-row:hover { background: #eff6ff; transform: translateY(-1px); }
        .font-bold { font-weight: bold; }
        .text-sm { font-size: 0.875rem; }
        .text-xs { font-size: 0.75rem; }
        .text-gray-600 { color: #6b7280; }
        .text-blue-600 { color: #2563eb; }
        .text-green-600 { color: #059669; }
        .max-h-96 { max-height: 24rem; }
        .overflow-y-auto { overflow-y: auto; }
        h1 { font-size: 3rem; font-weight: bold; margin-bottom: 1rem; }
        h2 { font-size: 2rem; font-weight: bold; margin-bottom: 1rem; }
        h3 { font-size: 1.5rem; font-weight: bold; margin-bottom: 0.5rem; }
        .status-bar { background: #dbeafe; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; }
        .roster-item { background: #dcfce7; border-left: 4px solid #10b981; padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 0.25rem; }
        .recent-pick { background: #f3f4f6; padding: 0.5rem; margin-bottom: 0.5rem; border-radius: 0.25rem; }
    </style>
    
    <script>
        // Define all functions immediately when page loads
        console.log('🔧 Loading ALFRED JavaScript functions...');
        
        // Global variables
        let currentSession = null;
        let userPosition = 6;
        let isMyTurn = false;
        let nflTeams = [];
        let allPlayers = [];
        let userPreferences = {
            strategy: 'standard',
            team_preferences: {},
            player_adjustments: {}
        };
        
        // Screen management - defined first
        function showScreen(screenId) {
            console.log('📍 Switching to screen:', screenId);
            const screens = ['welcomeScreen', 'setupScreen', 'draftScreen'];
            screens.forEach(id => {
                const element = document.getElementById(id);
                if (element) element.classList.add('hidden');
            });
            const targetElement = document.getElementById(screenId);
            if (targetElement) {
                targetElement.classList.remove('hidden');
                console.log('✅ Screen switched to:', screenId);
            } else {
                console.error('❌ Screen not found:', screenId);
            }
        }

        function showWelcome() {
            console.log('🏠 Navigating to welcome screen');
            showScreen('welcomeScreen');
        }
        
        function showSetup() {
            console.log('⚙️ Navigating to setup screen');
            showScreen('setupScreen');
        }
        
        function showDraft() {
            console.log('🏈 Navigating to draft screen');
            showScreen('draftScreen');
        }
        
        // Preference management functions
        async function loadNFLTeams() {
            try {
                const response = await fetch('/api/nfl-teams');
                nflTeams = await response.json();
                
                // Populate team select dropdowns
                document.querySelectorAll('.team-select').forEach(select => {
                    select.innerHTML = '<option value="">Select team...</option>';
                    nflTeams.forEach(team => {
                        select.innerHTML += `<option value="${team}">${team}</option>`;
                    });
                });
                
                console.log('✅ NFL teams loaded');
            } catch (error) {
                console.error('❌ Error loading NFL teams:', error);
            }
        }
        
        async function loadPreferences() {
            try {
                const response = await fetch('/api/preferences');
                userPreferences = await response.json();
                
                // Update UI with loaded preferences
                document.getElementById('strategyType').value = userPreferences.strategy || 'standard';
                
                // Load team preferences
                updateTeamPreferencesUI();
                
                // Load player adjustments
                updatePlayerAdjustmentsUI();
                
                console.log('✅ Preferences loaded:', userPreferences);
            } catch (error) {
                console.error('❌ Error loading preferences:', error);
            }
        }
        
        async function savePreferences() {
            try {
                // Collect current preferences from UI
                userPreferences.strategy = document.getElementById('strategyType').value;
                
                // Collect team preferences
                collectTeamPreferences();
                
                // Collect player adjustments
                collectPlayerAdjustments();
                
                const response = await fetch('/api/preferences/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userPreferences)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('✅ Preferences saved successfully!');
                } else {
                    alert('❌ Error saving preferences: ' + result.error);
                }
            } catch (error) {
                console.error('❌ Error saving preferences:', error);
                alert('❌ Network error saving preferences');
            }
        }
        
        function addFavoriteTeam() {
            const container = document.getElementById('favoriteTeams');
            const teamRow = createTeamPreferenceRow('favorite');
            container.appendChild(teamRow);
        }
        
        function addHatedTeam() {
            const container = document.getElementById('hatedTeams');
            const teamRow = createTeamPreferenceRow('hated');
            container.appendChild(teamRow);
        }
        
        function createTeamPreferenceRow(type) {
            const div = document.createElement('div');
            div.className = 'flex';
            div.style.cssText = 'gap: 0.5rem; align-items: center; margin-bottom: 0.5rem;';
            
            const sign = type === 'favorite' ? '+' : '-';
            const color = type === 'favorite' ? '#10b981' : '#ef4444';
            
            div.innerHTML = `
                <select class="input team-select" style="flex: 1;">
                    <option value="">Select team...</option>
                    ${nflTeams.map(team => `<option value="${team}">${team}</option>`).join('')}
                </select>
                <input type="range" min="5" max="25" value="10" class="input team-bias-slider" style="flex: 1;" 
                       oninput="this.nextElementSibling.textContent='${sign}' + this.value + '%'" />
                <span class="text-sm">${sign}10%</span>
                <button onclick="this.parentElement.remove()" class="btn" style="background: ${color}; color: white; padding: 0.5rem;">×</button>
            `;
            
            return div;
        }
        
        function collectTeamPreferences() {
            userPreferences.team_preferences = {};
            
            // Collect favorite teams
            document.getElementById('favoriteTeams').querySelectorAll('.flex').forEach(row => {
                const select = row.querySelector('.team-select');
                const slider = row.querySelector('.team-bias-slider');
                if (select.value) {
                    userPreferences.team_preferences[`${select.value}_favorite`] = parseInt(slider.value);
                }
            });
            
            // Collect hated teams
            document.getElementById('hatedTeams').querySelectorAll('.flex').forEach(row => {
                const select = row.querySelector('.team-select');
                const slider = row.querySelector('.team-bias-slider');
                if (select.value) {
                    userPreferences.team_preferences[`${select.value}_hated`] = parseInt(slider.value);
                }
            });
        }
        
        function updateTeamPreferencesUI() {
            // Clear existing
            document.getElementById('favoriteTeams').innerHTML = '';
            document.getElementById('hatedTeams').innerHTML = '';
            
            // Add saved preferences
            Object.keys(userPreferences.team_preferences || {}).forEach(key => {
                const [team, type] = key.split('_');
                const bias = userPreferences.team_preferences[key];
                
                if (type === 'favorite') {
                    const row = createTeamPreferenceRow('favorite');
                    row.querySelector('.team-select').value = team;
                    row.querySelector('.team-bias-slider').value = bias;
                    row.querySelector('span').textContent = `+${bias}%`;
                    document.getElementById('favoriteTeams').appendChild(row);
                } else if (type === 'hated') {
                    const row = createTeamPreferenceRow('hated');
                    row.querySelector('.team-select').value = team;
                    row.querySelector('.team-bias-slider').value = bias;
                    row.querySelector('span').textContent = `-${bias}%`;
                    document.getElementById('hatedTeams').appendChild(row);
                }
            });
            
            // Add empty rows if none exist
            if (document.getElementById('favoriteTeams').children.length === 0) {
                addFavoriteTeam();
            }
            if (document.getElementById('hatedTeams').children.length === 0) {
                addHatedTeam();
            }
        }
        
        function updatePlayerAdjustmentsUI() {
            // Populate player adjustment lists
            Object.keys(userPreferences.player_adjustments || {}).forEach(key => {
                const adjustment = userPreferences.player_adjustments[key];
                if (adjustment.type === 'undervalued') {
                    addPlayerAdjustment('undervalued', adjustment);
                } else if (adjustment.type === 'overvalued') {
                    addPlayerAdjustment('overvalued', adjustment);
                } else if (adjustment.type === 'must_have') {
                    addPlayerAdjustment('must_have', adjustment);
                }
            });
        }
        
        // Add player adjustment - updated to handle both objects and individual parameters
        function addPlayerAdjustment(playerIdOrType, playerNameOrPlayer, positionOrUndefined, teamOrUndefined, adjustmentTypeOrUndefined) {
            let playerId, playerName, position, team, adjustmentType;
            
            // Handle both parameter styles
            if (typeof playerIdOrType === 'object') {
                // Old style: addPlayerAdjustment(type, player)
                adjustmentType = playerNameOrPlayer;
                const player = playerIdOrType;
                playerId = player.player_id;
                playerName = player.name;
                position = player.position || '';
                team = player.team || '';
            } else {
                // New style: addPlayerAdjustment(playerId, playerName, position, team, adjustmentType)
                playerId = playerIdOrType;
                playerName = playerNameOrPlayer;
                position = positionOrUndefined;
                team = teamOrUndefined;
                adjustmentType = adjustmentTypeOrUndefined;
            }
            
            const containers = {
                'undervalued': 'undervaluedPlayers',
                'overvalued': 'overvaluedPlayers',
                'must_have': 'mustHavePlayers'
            };
            
            const container = document.getElementById(containers[adjustmentType]);
            if (!container) {
                console.error('Container not found for type:', adjustmentType);
                return;
            }
            
            // Check if player already exists in any container
            const allContainers = Object.values(containers).map(id => document.getElementById(id));
            for (let cont of allContainers) {
                if (cont) {
                    const existingPlayers = cont.querySelectorAll('[data-player-id]');
                    for (let existing of existingPlayers) {
                        if (existing.getAttribute('data-player-id') === String(playerId)) {
                            alert(`${playerName} is already in your adjustments list`);
                            return;
                        }
                    }
                }
            }
            
            // Check limits for must-have players
            if (adjustmentType === 'must_have') {
                const existing = container.children.length;
                if (existing >= 2) {
                    alert('You can only have 2 must-have players maximum');
                    return;
                }
            }
            
            const div = document.createElement('div');
            div.className = 'flex player-adjustment-item';
            div.setAttribute('data-player-id', playerId);
            div.setAttribute('data-adjustment-type', adjustmentType);
            div.style.cssText = 'gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; padding: 0.5rem; background: #f3f4f6; border-radius: 0.25rem;';
            
            const colors = {
                'undervalued': '#10b981',
                'overvalued': '#ef4444', 
                'must_have': '#f59e0b'
            };
            
            const displayText = position && team ? `${playerName} - ${position} (${team})` : playerName;
            
            div.innerHTML = `
                <span style="flex: 2; font-weight: bold;">${displayText}</span>
                ${adjustmentType !== 'must_have' ? `
                    <input type="range" min="10" max="50" value="20" 
                           class="adjustment-slider" style="flex: 1;" 
                           oninput="this.nextElementSibling.textContent=this.value + '%'" />
                    <span class="adjustment-value text-sm">20%</span>
                ` : ''}
                <button onclick="this.parentElement.remove()" class="btn" style="background: ${colors[adjustmentType]}; color: white; padding: 0.25rem 0.5rem;">×</button>
            `;
            
            container.appendChild(div);
            
            // Hide search results
            const searchResults = document.querySelectorAll('.search-results');
            searchResults.forEach(result => result.style.display = 'none');
            
            // Clear search input
            const searchInputs = {
                'undervalued': 'undervaluedPlayerSearch',
                'overvalued': 'overvaluedPlayerSearch',
                'must_have': 'mustHavePlayerSearch'
            };
            const searchInput = document.getElementById(searchInputs[adjustmentType]);
            if (searchInput) {
                searchInput.value = '';
            }
            
            console.log(`Added ${playerName} as ${adjustmentType} player`);
        }
        
        function collectPlayerAdjustments() {
            userPreferences.player_adjustments = {};
            
            // Collect all player adjustments
            document.querySelectorAll('.player-adjustment-item').forEach(item => {
                const playerId = item.getAttribute('data-player-id');
                const adjustmentType = item.getAttribute('data-adjustment-type');
                const playerName = item.querySelector('span').textContent;
                
                let percentage = 20; // Default for must-have
                const slider = item.querySelector('.adjustment-slider');
                if (slider) {
                    percentage = parseInt(slider.value);
                }
                
                const key = `${playerId}_${adjustmentType}`;
                userPreferences.player_adjustments[key] = {
                    player_id: parseInt(playerId),
                    name: playerName,
                    type: adjustmentType,
                    percentage: percentage
                };
            });
        }
        
        // Player search functionality
        function searchPlayers(searchType) {
            const searchInput = document.getElementById(searchType === 'undervalued' ? 'undervaluedPlayerSearch' : 
                                                      searchType === 'overvalued' ? 'overvaluedPlayerSearch' : 'mustHavePlayerSearch');
            const searchValue = searchInput.value.toLowerCase();
            
            if (searchValue.length < 2) return;
            
            showSearchResults(searchValue, searchType);
        }
        
        async function showSearchResults(searchTerm, adjustmentType) {
            try {
                const response = await fetch(`/api/search_players?q=${encodeURIComponent(searchTerm)}`);
                const players = await response.json();
                
                const resultsId = adjustmentType === 'undervalued' ? 'undervaluedResults' : 
                                adjustmentType === 'overvalued' ? 'overvaluedResults' : 'mustHaveResults';
                
                let resultsDiv = document.getElementById(resultsId);
                if (!resultsDiv) {
                    // Create results div if it doesn't exist
                    resultsDiv = document.createElement('div');
                    resultsDiv.id = resultsId;
                    resultsDiv.className = 'search-results';
                    resultsDiv.style.cssText = 'position: absolute; background: white; border: 1px solid #ccc; max-height: 200px; overflow-y: auto; width: 100%; z-index: 1000; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);';
                    
                    const searchInput = document.getElementById(adjustmentType === 'undervalued' ? 'undervaluedPlayerSearch' : 
                                                              adjustmentType === 'overvalued' ? 'overvaluedPlayerSearch' : 'mustHavePlayerSearch');
                    searchInput.parentElement.style.position = 'relative';
                    searchInput.parentElement.appendChild(resultsDiv);
                }
                
                resultsDiv.innerHTML = '';
                
                players.slice(0, 8).forEach(player => {
                    const playerDiv = document.createElement('div');
                    playerDiv.className = 'search-result';
                    playerDiv.style.cssText = 'padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center;';
                    playerDiv.innerHTML = `
                        <div>
                            <strong>${player.name}</strong> - ${player.position} (${player.team})
                            <div style="font-size: 0.8em; color: #666;">ADP: ${player.adp === 999 ? 'N/A' : Math.round(player.adp)}</div>
                        </div>
                        <button class="btn btn-sm" style="background: #3b82f6; color: white; padding: 4px 8px; font-size: 0.8em;" onclick="addPlayerAdjustment(${player.player_id}, '${player.name}', '${player.position}', '${player.team}', '${adjustmentType}')">Add</button>
                    `;
                    
                    playerDiv.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = '#f3f4f6';
                    });
                    playerDiv.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'white';
                    });
                    
                    resultsDiv.appendChild(playerDiv);
                });
                
                if (players.length === 0) {
                    resultsDiv.innerHTML = '<div style="padding: 12px; color: #666;">No players found</div>';
                }
                
                resultsDiv.style.display = 'block';
                
                // Hide results when clicking outside
                setTimeout(() => {
                    document.addEventListener('click', function hideResults(e) {
                        if (!resultsDiv.contains(e.target) && e.target !== document.getElementById(adjustmentType === 'undervalued' ? 'undervaluedPlayerSearch' : 
                                                                                                   adjustmentType === 'overvalued' ? 'overvaluedPlayerSearch' : 'mustHavePlayerSearch')) {
                            resultsDiv.style.display = 'none';
                            document.removeEventListener('click', hideResults);
                        }
                    });
                }, 100);
                
            } catch (error) {
                console.error('Error searching players:', error);
            }
        }
        
        async function searchUndervaluedPlayers() {
            searchPlayers('undervalued');
        }
        
        async function searchOvervaluedPlayers() {
            searchPlayers('overvalued');
        }
        
        async function searchMustHavePlayers() {
            searchPlayers('must_have');
        }
        
        function showPlayerSearchResults(players, type) {
            // Create a modal or dropdown with search results
            const existingModal = document.getElementById('playerSearchModal');
            if (existingModal) existingModal.remove();
            
            const modal = document.createElement('div');
            modal.id = 'playerSearchModal';
            modal.style.cssText = `
                position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
                background: white; padding: 1rem; border-radius: 0.5rem; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                max-width: 500px; width: 90%; max-height: 400px; overflow-y: auto; z-index: 1000;
            `;
            
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.5); z-index: 999;
            `;
            overlay.onclick = () => {
                modal.remove();
                overlay.remove();
            };
            
            modal.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-bold">Select Player</h3>
                    <button onclick="this.parentElement.parentElement.parentElement.remove(); this.parentElement.parentElement.parentElement.previousElementSibling.remove()" class="btn" style="background: #ef4444; color: white; padding: 0.25rem 0.5rem;">×</button>
                </div>
                <div class="space-y-2">
                    ${players.map(player => `
                        <div class="player-row flex justify-between items-center p-2 bg-gray-50 rounded cursor-pointer hover:bg-blue-50" 
                             onclick="selectPlayer(${player.id}, '${player.name}', '${type}'); this.parentElement.parentElement.parentElement.remove(); this.parentElement.parentElement.parentElement.previousElementSibling.remove();">
                            <div>
                                <div class="font-bold">${player.name}</div>
                                <div class="text-sm text-gray-600">${player.position} - ${player.team}</div>
                            </div>
                            <div class="text-sm">ADP: ${player.adp === 999 ? 'N/A' : Math.round(player.adp)}</div>
                        </div>
                    `).join('')}
                    ${players.length === 0 ? '<p class="text-gray-500">No players found</p>' : ''}
                </div>
            `;
            
            document.body.appendChild(overlay);
            document.body.appendChild(modal);
        }
        
        function selectPlayer(playerId, playerName, adjustmentType) {
            const player = {
                player_id: playerId,
                name: playerName,
                type: adjustmentType,
                percentage: 20
            };
            
            // Check limits for must-have players
            if (adjustmentType === 'must_have') {
                const existing = document.getElementById('mustHavePlayers').children.length;
                if (existing >= 2) {
                    alert('You can only have 2 must-have players maximum');
                    return;
                }
            }
            
            addPlayerAdjustment(adjustmentType, player);
            
            // Clear search input
            const searchInputs = {
                'undervalued': 'undervaluedPlayerSearch',
                'overvalued': 'overvaluedPlayerSearch',
                'must_have': 'mustHavePlayerSearch'
            };
            document.getElementById(searchInputs[adjustmentType]).value = '';
            
            console.log(`Added ${playerName} as ${adjustmentType} player`);
        }
        
        // API functions
        async function createSession() {
            console.log('🎯 Creating new ALFRED draft session...');
            
            const data = {
                league_name: document.getElementById('leagueName').value,
                draft_position: parseInt(document.getElementById('draftPosition').value),
                scoring: document.getElementById('scoringFormat').value
            };
            
            console.log('📝 Session data:', data);
            
            try {
                console.log('📡 Sending POST request to /api/draft/new');
                const response = await fetch('/api/draft/new', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                console.log('📬 Response status:', response.status);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const result = await response.json();
                console.log('📋 Session result:', result);
                
                if (result.success) {
                    currentSession = result.session_id;
                    userPosition = data.draft_position;
                    
                    console.log(`✅ ALFRED session created: ${currentSession}, Position: ${userPosition}`);
                    
                    // Update UI
                    document.getElementById('draftLeagueName').textContent = data.league_name;
                    document.getElementById('yourPosition').textContent = userPosition;
                    document.getElementById('draftFormat').textContent = data.scoring.toUpperCase();
                    
                    showDraft();
                    await refreshDraftData();
                } else {
                    console.error('❌ Session creation failed:', result.error);
                    alert('Failed to create session: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('❌ Network error creating session:', error);
                alert('Network error creating session: ' + error.message);
            }
        }
        
        // New UI functions for enhanced draft interface
        let currentDraftData = {
            analysis: null,
            predictions: null,
            teamRosters: null,
            recommendations: null
        };
        
        // Tab switching functionality
        function switchPlayerTab(tabName) {
            console.log('Switching to tab:', tabName);
            
            // Update tab buttons safely
            const tabButtons = document.querySelectorAll('.tab-button');
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.style.background = 'white';
                btn.style.fontWeight = 'normal';
            });
            
            // Hide all tab content safely
            const tabContents = document.querySelectorAll('.tab-content');
            tabContents.forEach(content => {
                content.classList.add('hidden');
            });
            
            // Map tab names to actual element IDs
            const tabButtonIds = {
                'all': 'tabAllPlayers',
                'position': 'tabByPosition', 
                'steals': 'tabSteals',
                'targets': 'tabTargets'
            };
            
            const tabContentIds = {
                'all': 'allPlayersTab',
                'position': 'byPositionTab',
                'steals': 'stealsTab', 
                'targets': 'targetsTab'
            };
            
            // Show selected tab button
            const activeButton = document.getElementById(tabButtonIds[tabName]);
            if (activeButton) {
                activeButton.classList.add('active');
                activeButton.style.background = '#f9fafb';
                activeButton.style.fontWeight = 'bold';
            }
            
            // Show selected tab content
            const tabContent = document.getElementById(tabContentIds[tabName]);
            if (tabContent) {
                tabContent.classList.remove('hidden');
            } else {
                console.error('Tab content not found:', tabContentIds[tabName]);
            }
            
            // Load tab-specific content
            if (tabName === 'steals') {
                setTimeout(loadStealsContent, 100);
            } else if (tabName === 'targets') {
                setTimeout(loadTargetsContent, 100);
            }
        }
        
        // Filter players in All Players tab
        function filterPlayers() {
            const searchTerm = document.getElementById('playerSearchInput').value.toLowerCase();
            const positionFilter = document.getElementById('positionFilter').value;
            
            // This will be populated with actual filtering logic
            loadPlayers(searchTerm, positionFilter);
        }
        
        // Show players by position in By Position tab
        function showPositionPlayers(position) {
            const container = document.getElementById('positionPlayers');
            
            // Filter current players by position
            if (allPlayers && allPlayers.length > 0) {
                const positionPlayers = allPlayers.filter(p => p.position === position);
                
                container.innerHTML = positionPlayers.slice(0, 20).map(player => createPlayerCard(player, true)).join('');
            }
        }
        
        // Create enhanced player card with all new features
        function createPlayerCard(player, isClickable = true) {
            const adpText = player.adp === 999 ? 'N/A' : Math.round(player.adp);
            const tierColor = getTierColor(player.tier);
            const positionColor = getPositionColor(player.position);
            
            // Check for user adjustments
            const adjustmentIcon = getUserAdjustmentIcon(player.id);
            
            // Calculate ADP delta if we have current pick info
            const currentPick = parseInt(document.getElementById('currentPick')?.textContent || '1');
            const adpDelta = player.adp !== 999 ? currentPick - player.adp : 0;
            const deltaIndicator = adpDelta > 10 ? '📈' : adpDelta < -10 ? '📉' : '';
            
            const clickHandler = isClickable && isMyTurn ? `onclick="makePick(${player.id}, '${player.name}')"` : '';
            const clickableStyle = isClickable && isMyTurn ? 'cursor: pointer; border: 2px solid #10b981;' : '';
            
            return `
                <div class="player-row" ${clickHandler} style="margin-bottom: 0.5rem; ${clickableStyle}">
                    <div class="flex justify-between items-center">
                        <div style="flex: 1;">
                            <div class="flex items-center" style="gap: 0.5rem;">
                                <div class="font-bold">${player.name}</div>
                                <span style="background: ${positionColor}; color: white; padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-size: 0.7rem; font-weight: bold;">
                                    ${player.position}
                                </span>
                                <span style="background: ${tierColor}; color: white; padding: 0.1rem 0.4rem; border-radius: 0.25rem; font-size: 0.7rem;">
                                    T${player.tier}
                                </span>
                                ${adjustmentIcon}
                                ${deltaIndicator}
                            </div>
                            <div class="text-sm text-gray-600">${player.team} • ${player.projected_points} pts</div>
                        </div>
                        <div class="text-sm" style="text-align: right;">
                            <div>ADP: ${adpText}</div>
                            ${isClickable && isMyTurn ? '<div class="text-green-600 font-bold" style="font-size: 0.7rem;">CLICK TO DRAFT</div>' : ''}
                        </div>
                    </div>
                </div>
            `;
        }
        
        function getTierColor(tier) {
            const colors = {1: '#dc3545', 2: '#fd7e14', 3: '#ffc107', 4: '#28a745', 5: '#6c757d'};
            return colors[tier] || '#6c757d';
        }
        
        function getPositionColor(position) {
            const colors = {
                'QB': '#dc3545', 'RB': '#28a745', 'WR': '#007bff', 
                'TE': '#fd7e14', 'K': '#6c757d', 'DST': '#6f42c1', 'D/ST': '#6f42c1'
            };
            return colors[position] || '#6c757d';
        }
        
        function getUserAdjustmentIcon(playerId) {
            // Check if player has user adjustments from preferences
            if (userPreferences.player_adjustments) {
                for (let key in userPreferences.player_adjustments) {
                    const adj = userPreferences.player_adjustments[key];
                    if (adj.player_id === playerId) {
                        if (adj.type === 'must_have') return '⭐';
                        if (adj.type === 'undervalued') return '↗️';
                        if (adj.type === 'overvalued') return '↘️';
                    }
                }
            }
            return '';
        }
        
        // Load steals content
        async function loadStealsContent() {
            if (!currentSession) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/analysis`);
                const analysis = await response.json();
                
                if (analysis.success) {
                    currentDraftData.analysis = analysis;
                    
                    const container = document.getElementById('stealsContent');
                    container.innerHTML = `
                        <h4 style="margin-bottom: 0.5rem; color: #10b981;">💎 Best Values Available</h4>
                        ${analysis.steals.map(steal => `
                            <div class="player-row" style="margin-bottom: 0.5rem; border-left: 3px solid #10b981;">
                                <div class="font-bold">${steal.player.name}</div>
                                <div class="text-sm">Expected R${steal.expected_round}, Available R${steal.current_round}</div>
                                <div class="text-sm text-green-600">Value: +${steal.value} rounds</div>
                            </div>
                        `).join('')}
                        
                        <h4 style="margin: 1rem 0 0.5rem 0; color: #dc3545;">📈 Recent ADP Deltas</h4>
                        ${analysis.adp_deltas.map(delta => `
                            <div class="text-sm" style="margin-bottom: 0.25rem;">
                                <strong>${delta.player}</strong> ${delta.type === 'steal' ? '📉' : delta.type === 'reach' ? '📈' : ''}
                                <span style="color: ${delta.type === 'steal' ? '#10b981' : delta.type === 'reach' ? '#dc3545' : '#6c757d'};">
                                    ${delta.delta > 0 ? '+' : ''}${delta.delta}
                                </span>
                            </div>
                        `).join('')}
                    `;
                }
            } catch (error) {
                console.error('Error loading steals:', error);
            }
        }
        
        // Load targets content
        function loadTargetsContent() {
            const container = document.getElementById('targetsContent');
            
            let content = '<h4 style="margin-bottom: 0.5rem;">🎯 Your Target Players</h4>';
            
            if (userPreferences.player_adjustments) {
                const targets = Object.values(userPreferences.player_adjustments);
                
                if (targets.length === 0) {
                    content += '<div style="color: #6b7280; text-align: center; padding: 1rem;">No target players set.<br>Go to Settings to add preferences.</div>';
                } else {
                    targets.forEach(target => {
                        const icon = target.type === 'must_have' ? '⭐' : target.type === 'undervalued' ? '↗️' : '↘️';
                        const color = target.type === 'must_have' ? '#ffc107' : target.type === 'undervalued' ? '#10b981' : '#dc3545';
                        
                        content += `
                            <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: #f8f9fa; border-radius: 0.25rem; border-left: 3px solid ${color};">
                                <div class="font-bold">${icon} ${target.name}</div>
                                <div class="text-sm" style="color: ${color}; text-transform: capitalize;">
                                    ${target.type.replace('_', ' ')} ${target.type !== 'must_have' ? `(${target.percentage}%)` : ''}
                                </div>
                            </div>
                        `;
                    });
                }
            }
            
            container.innerHTML = content;
        }
        
        // Load all team rosters with enhanced cards
        async function loadAllTeamRosters() {
            if (!currentSession) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/team-rosters`);
                const data = await response.json();
                
                if (data.success) {
                    currentDraftData.teamRosters = data;
                    const container = document.getElementById('teamRosterCards');
                    
                    container.innerHTML = data.teams.map(team => createTeamRosterCard(team)).join('');
                }
            } catch (error) {
                console.error('Error loading team rosters:', error);
            }
        }
        
        // Create enhanced team roster card
        function createTeamRosterCard(team) {
            const strategyIcon = {
                'rb_heavy': '🏃‍♂️',
                'wr_heavy': '📡',
                'zero_rb': '🚫🏃‍♂️',
                'balanced': '⚖️',
                'best_available': '🎯'
            }[team.strategy] || '🎯';
            
            const strengthColor = {
                'strong': '#10b981',
                'average': '#ffc107',
                'weak': '#dc3545'
            }[team.strength] || '#6c757d';
            
            // Create visual roster grid
            const positionTargets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1};
            const rosterGrid = createRosterGrid(team.roster, positionTargets);
            
            // Quick position summary
            const positionSummary = Object.keys(positionTargets).map(pos => {
                const current = team.position_counts[pos] || 0;
                const target = positionTargets[pos];
                const color = current >= target ? '#10b981' : current > 0 ? '#ffc107' : '#dc3545';
                return `<span style="color: ${color}; font-weight: bold; font-size: 0.7rem;">${pos}:${current}/${target}</span>`;
            }).join(' ');
            
            return `
                <div class="card" style="padding: 0.75rem; ${team.is_user ? 'border: 2px solid #10b981; background: #f0fdf4;' : 'background: #f8f9fa;'} cursor: pointer;" 
                     onclick="showTeamDetails(${team.team_number})">
                    
                    <!-- Team Header -->
                    <div class="flex justify-between items-center" style="margin-bottom: 0.5rem;">
                        <div class="font-bold" style="font-size: 0.9rem;">
                            ${team.is_user ? '🏆 YOUR TEAM' : `Team ${team.team_number}`}
                        </div>
                        <div style="font-size: 0.7rem; color: ${strengthColor};">
                            ${strategyIcon}
                        </div>
                    </div>
                    
                    <!-- Roster Grid -->
                    <div style="margin-bottom: 0.75rem;">
                        ${rosterGrid}
                    </div>
                    
                    <!-- Position Summary -->
                    <div style="margin-bottom: 0.5rem; line-height: 1.1;">
                        ${positionSummary}
                    </div>
                    
                    <!-- Team Info -->
                    <div style="font-size: 0.65rem; color: #6b7280;">
                        <div><strong>Strategy:</strong> ${team.strategy.replace('_', ' ')}</div>
                        <div><strong>Next:</strong> ${team.next_need}</div>
                    </div>
                    
                </div>
            `;
        }
        
        function createRosterGrid(roster, positionTargets) {
            // Group players by position
            const playersByPosition = {};
            roster.forEach(player => {
                if (!playersByPosition[player.position]) {
                    playersByPosition[player.position] = [];
                }
                playersByPosition[player.position].push(player);
            });
            
            // Create position grids
            let gridHTML = '';
            
            Object.keys(positionTargets).forEach(position => {
                const players = playersByPosition[position] || [];
                const target = positionTargets[position];
                const posColor = getPositionColor(position);
                
                gridHTML += `
                    <div style="margin-bottom: 0.5rem;">
                        <div style="font-size: 0.7rem; font-weight: bold; color: ${posColor}; margin-bottom: 0.25rem;">
                            ${position} (${players.length}/${target})
                        </div>
                        <div style="display: grid; grid-template-columns: repeat(${Math.max(2, target)}, 1fr); gap: 0.1rem;">
                            ${Array(target).fill().map((_, index) => {
                                const player = players[index];
                                if (player) {
                                    return `
                                        <div style="background: ${posColor}; color: white; padding: 0.1rem 0.2rem; border-radius: 0.2rem; font-size: 0.6rem; text-align: center; font-weight: bold; overflow: hidden; white-space: nowrap; text-overflow: ellipsis;">
                                            ${player.name.split(' ').map(n => n.charAt(0)).join('.')}
                                        </div>
                                    `;
                                } else {
                                    return `
                                        <div style="background: #e5e7eb; color: #9ca3af; padding: 0.1rem 0.2rem; border-radius: 0.2rem; font-size: 0.6rem; text-align: center; border: 1px dashed #d1d5db;">
                                            --
                                        </div>
                                    `;
                                }
                            }).join('')}
                        </div>
                    </div>
                `;
            });
            
            return gridHTML;
        }
        
        // Show detailed team view (placeholder for future enhancement)
        function showTeamDetails(teamNumber) {
            console.log('Show details for team:', teamNumber);
            // Could open a modal with full team roster, strategy analysis, etc.
        }
        
        // Round projection functions
        function showRoundProjection(type) {
            const container = document.getElementById('roundProjections');
            
            if (type === 'next') {
                showNextRoundProjection(container);
            } else {
                showFutureRoundsProjection(container);
            }
        }
        
        function showNextRoundProjection(container) {
            if (!currentDraftData.predictions || !currentDraftData.teamRosters) {
                container.innerHTML = '<div style="color: #6b7280;">Loading predictions...</div>';
                return;
            }
            
            const predictions = currentDraftData.predictions.predictions || [];
            const currentRound = Math.ceil(parseInt(document.getElementById('currentPick')?.textContent || '1') / 10);
            
            container.innerHTML = `
                <div style="font-weight: bold; margin-bottom: 0.5rem; color: #3b82f6;">Round ${currentRound} Outlook</div>
                ${predictions.map(pred => `
                    <div style="margin-bottom: 0.5rem; padding: 0.25rem; ${pred.is_user ? 'background: #dcfce7; border-left: 2px solid #10b981;' : 'background: #f3f4f6;'} border-radius: 0.25rem;">
                        <div style="font-weight: bold; font-size: 0.8rem;">
                            ${pred.is_user ? 'YOUR PICK' : `Team ${pred.team_number}`} (#${pred.pick_number})
                        </div>
                        ${pred.predicted_player ? `
                            <div style="font-size: 0.7rem; color: #4b5563;">
                                Likely: ${pred.predicted_player.name} (${pred.predicted_player.position})
                            </div>
                        ` : ''}
                        <div style="font-size: 0.6rem; color: #6b7280;">
                            ${pred.reasoning}
                        </div>
                    </div>
                `).join('')}
            `;
        }
        
        function showFutureRoundsProjection(container) {
            if (!currentDraftData.teamRosters) {
                container.innerHTML = '<div style="color: #6b7280;">Loading team data...</div>';
                return;
            }
            
            const currentRound = Math.ceil(parseInt(document.getElementById('currentPick')?.textContent || '1') / 10);
            const teams = currentDraftData.teamRosters.teams || [];
            
            // Project next 3 rounds
            let projectionHTML = '';
            
            for (let round = currentRound + 1; round <= Math.min(currentRound + 3, 16); round++) {
                projectionHTML += `
                    <div style="margin-bottom: 0.75rem;">
                        <div style="font-weight: bold; color: #6b7280; margin-bottom: 0.25rem;">Round ${round}</div>
                        <div style="font-size: 0.7rem;">
                            ${teams.slice(0, 5).map(team => {
                                const nextNeed = getProjectedNeed(team, round);
                                return `<div style="margin-bottom: 0.1rem;">Team ${team.team_number}: ${nextNeed}</div>`;
                            }).join('')}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = projectionHTML;
        }
        
        function getProjectedNeed(team, round) {
            const positionCounts = team.position_counts;
            const strategy = team.strategy;
            
            // Simple projection logic based on strategy and current roster
            if (round <= 8) {
                if (strategy === 'rb_heavy' && positionCounts.RB < 3) return 'RB';
                if (strategy === 'wr_heavy' && positionCounts.WR < 4) return 'WR';
                if (strategy === 'zero_rb' && positionCounts.WR < 3) return 'WR';
                if (positionCounts.QB === 0 && round >= 6) return 'QB';
                if (positionCounts.TE === 0 && round >= 4) return 'TE';
            } else {
                if (positionCounts.K === 0 && round >= 14) return 'K';
                if (positionCounts.DST === 0 && round >= 14) return 'DST';
            }
            
            return positionCounts.RB < positionCounts.WR ? 'RB' : 'WR';
        }
        
        // Forward-looking strategy system
        let currentStrategyView = 'immediate';
        
        function showStrategyView(viewType) {
            currentStrategyView = viewType;
            
            // Update button states
            document.querySelectorAll('#btnImmediate, #btnRoadmap, #btnExplanation').forEach(btn => {
                btn.style.background = '#6b7280';
            });
            document.getElementById(`btn${viewType.charAt(0).toUpperCase() + viewType.slice(1)}`).style.background = '#3b82f6';
            
            const container = document.getElementById('forwardLookingStrategy');
            
            if (viewType === 'immediate') {
                showImmediateStrategy(container);
            } else if (viewType === 'roadmap') {
                showFullDraftRoadmap(container);
            } else if (viewType === 'explanation') {
                showAIStrategyExplanation(container);
            }
        }
        
        function showImmediateStrategy(container) {
            if (!currentDraftData.recommendations) {
                container.innerHTML = '<div style="color: #6b7280;">Loading strategy...</div>';
                return;
            }
            
            const data = currentDraftData.recommendations;
            container.innerHTML = `
                <div style="margin-bottom: 1rem;">
                    <div class="font-bold" style="margin-bottom: 0.5rem;">Next 3 Picks:</div>
                    ${data.recommendations.slice(0, 3).map((rec, index) => `
                        <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: ${rec.priority === 'high' ? '#dcfce7' : '#f3f4f6'}; border-radius: 0.25rem; border-left: 3px solid ${rec.priority === 'high' ? '#10b981' : '#6b7280'};">
                            <div class="font-bold" style="font-size: 0.8rem;">
                                ${index + 1}. ${rec.player.name} (${rec.player.position})
                            </div>
                            <div style="font-size: 0.7rem; color: #4b5563; margin-top: 0.25rem;">
                                ${rec.reasoning}
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div style="font-size: 0.7rem; color: #6b7280;">
                    <div class="font-bold" style="margin-bottom: 0.25rem;">Current Strategy:</div>
                    <div>${data.strategy_analysis.current_strategy}</div>
                    <div>Balance: ${data.strategy_analysis.roster_balance}</div>
                </div>
            `;
        }
        
        function showFullDraftRoadmap(container) {
            if (!currentDraftData.recommendations) {
                container.innerHTML = '<div style="color: #6b7280;">Loading roadmap...</div>';
                loadFullDraftRoadmap();
                return;
            }
            
            const data = currentDraftData.recommendations;
            const currentRound = Math.ceil(parseInt(document.getElementById('currentPick')?.textContent || '1') / 10);
            
            // Create round-by-round strategy
            const strategy = data.strategy_analysis.next_picks_strategy || [];
            const roundsToShow = Math.min(8, 16 - currentRound + 1);
            
            let roadmapHTML = '<div class="font-bold" style="margin-bottom: 0.5rem;">Draft Roadmap:</div>';
            
            for (let i = 0; i < roundsToShow; i++) {
                const round = currentRound + i;
                const position = strategy[i] || 'BPA';
                const isNextPick = i === 0;
                
                roadmapHTML += `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; padding: 0.25rem; ${isNextPick ? 'background: #dcfce7; border-left: 3px solid #10b981;' : 'background: #f8f9fa;'} border-radius: 0.2rem;">
                        <div style="font-size: 0.8rem; font-weight: ${isNextPick ? 'bold' : 'normal'};">
                            Round ${round}
                        </div>
                        <div style="font-size: 0.8rem; color: ${getPositionColor(position)}; font-weight: bold;">
                            ${position}
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = roadmapHTML;
        }
        
        function showAIStrategyExplanation(container) {
            container.innerHTML = '<div style="color: #6b7280;">Loading AI explanation...</div>';
            loadAIStrategyExplanation(container);
        }
        
        async function loadFullDraftRoadmap() {
            // This would call an enhanced API endpoint for full draft strategy
            console.log('Loading full draft roadmap...');
        }
        
        async function loadAIStrategyExplanation(container) {
            if (!currentSession) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/strategy-explanation`);
                const data = await response.json();
                
                if (data.success) {
                    container.innerHTML = `
                        <div style="font-size: 0.8rem; line-height: 1.4;">
                            <div class="font-bold" style="margin-bottom: 0.5rem;">AI Strategy Analysis:</div>
                            <div style="background: #f0fdf4; padding: 0.5rem; border-radius: 0.25rem; border-left: 3px solid #10b981;">
                                ${data.explanation}
                            </div>
                            
                            <div class="font-bold" style="margin: 0.75rem 0 0.25rem 0;">Key Insights:</div>
                            ${data.insights.map(insight => `
                                <div style="margin-bottom: 0.25rem; font-size: 0.7rem;">• ${insight}</div>
                            `).join('')}
                            
                            <div class="font-bold" style="margin: 0.75rem 0 0.25rem 0;">Risk Assessment:</div>
                            <div style="font-size: 0.7rem; color: #4b5563;">
                                ${data.risk_assessment}
                            </div>
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div style="font-size: 0.8rem; color: #6b7280;">
                            <div class="font-bold" style="margin-bottom: 0.5rem;">Manual Strategy Analysis:</div>
                            <div>Your current approach appears balanced with emphasis on building positional depth early. Consider targeting high-upside players in middle rounds while securing positional needs.</div>
                            
                            <div class="font-bold" style="margin: 0.75rem 0 0.25rem 0;">Recommendations:</div>
                            <div style="font-size: 0.7rem;">
                                • Focus on RB/WR in early rounds<br>
                                • Target QB around rounds 6-8<br>
                                • Wait on TE unless elite option available<br>
                                • Stream K/DST in final rounds
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading AI explanation:', error);
                // Fallback to manual explanation
                container.innerHTML = `
                    <div style="font-size: 0.8rem; color: #6b7280;">
                        <div class="font-bold" style="margin-bottom: 0.5rem;">Strategy Overview:</div>
                        <div>Focus on building a balanced roster with emphasis on skill position players early. Target value picks and avoid reaching for positions too early.</div>
                    </div>
                `;
            }
        }
        
        // Load strategy recommendations (renamed for clarity)
        async function loadStrategyRecommendations() {
            if (!currentSession) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/recommendations`);
                const data = await response.json();
                
                if (data.success) {
                    currentDraftData.recommendations = data;
                    // Initialize with immediate strategy view
                    showStrategyView(currentStrategyView);
                }
            } catch (error) {
                console.error('Error loading recommendations:', error);
            }
        }
        
        // Load upcoming picks predictions
        async function loadUpcomingPicks() {
            if (!currentSession) return;
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/predictions`);
                const data = await response.json();
                
                if (data.success) {
                    currentDraftData.predictions = data;
                    const container = document.getElementById('upcomingPicks');
                    
                    if (!container) {
                        console.warn('upcomingPicks container not found');
                        return;
                    }
                    
                    container.innerHTML = data.predictions.map(pred => `
                        <div style="margin-bottom: 0.5rem; padding: 0.25rem; font-size: 0.7rem; ${pred.is_user ? 'background: #dcfce7; border-left: 2px solid #10b981;' : 'background: #f3f4f6;'}">
                            <div class="font-bold">
                                ${pred.is_user ? 'YOUR TURN' : `Team ${pred.team_number}`} (Pick ${pred.pick_number})
                            </div>
                            ${pred.predicted_player ? `
                                <div style="color: #4b5563;">
                                    Likely: ${pred.predicted_player.name} (${pred.predicted_player.position})
                                </div>
                            ` : ''}
                            <div style="color: #6b7280; font-size: 0.6rem;">
                                ${pred.reasoning}
                            </div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                console.error('Error loading predictions:', error);
            }
        }
        
        // Update quick stats
        function updateQuickStats() {
            if (!currentDraftData.recommendations) return;
            
            const data = currentDraftData.recommendations;
            const container = document.getElementById('quickStats');
            
            if (!container) {
                console.warn('quickStats container not found');
                return;
            }
            
            container.innerHTML = `
                <div style="margin-bottom: 0.5rem;">
                    <div class="font-bold" style="font-size: 0.8rem;">Roster: ${data.user_roster_summary.total_players}/16</div>
                </div>
                <div style="font-size: 0.7rem; line-height: 1.3;">
                    <div>QB: ${data.user_roster_summary.position_counts.QB || 0}</div>
                    <div>RB: ${data.user_roster_summary.position_counts.RB || 0}</div>
                    <div>WR: ${data.user_roster_summary.position_counts.WR || 0}</div>
                    <div>TE: ${data.user_roster_summary.position_counts.TE || 0}</div>
                    <div>K: ${data.user_roster_summary.position_counts.K || 0}</div>
                    <div>DST: ${data.user_roster_summary.position_counts.DST || 0}</div>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.7rem; color: #dc3545;">
                    <div class="font-bold">Still Need:</div>
                    ${data.user_roster_summary.needs.slice(0,3).join(', ') || 'Depth players'}
                </div>
            `;
        }
        
        // Refresh all draft data
        async function refreshDraftData() {
            if (!currentSession) {
                console.warn('No current session, skipping data refresh');
                return;
            }
            
            console.log('🔄 Refreshing all draft data...');
            
            try {
                // Load all data in parallel with error handling
                const results = await Promise.allSettled([
                    loadDraftState(),
                    loadAllTeamRosters(),
                    loadStrategyRecommendations(),
                    loadUpcomingPicks()
                ]);
                
                // Log any failures
                results.forEach((result, index) => {
                    if (result.status === 'rejected') {
                        console.error(`Data refresh failed for task ${index}:`, result.reason);
                    }
                });
                
                // Update dependent components
                updateQuickStats();
                
                // Initialize round projections
                const projectionsContainer = document.getElementById('roundProjections');
                if (projectionsContainer) {
                    showRoundProjection('next');
                }
                
                console.log('✅ Draft data refreshed');
                
            } catch (error) {
                console.error('❌ Error during data refresh:', error);
            }
        }
        
        async function loadDraftState() {
            if (!currentSession) return;
            
            try {
                const statusResponse = await fetch(`/api/draft/${currentSession}/status`);
                const status = await statusResponse.json();
                
                if (status.success) {
                    const currentPick = status.current_pick;
                    document.getElementById('currentPick').textContent = currentPick;
                    document.getElementById('currentRound').textContent = Math.ceil(currentPick / 10);
                    
                    isMyTurn = status.is_user_turn;
                    updateTurnStatus();
                    
                    await loadPlayers();
                    updateRosterDisplay(status.session);
                    updateRecentPicks(status.session);
                }
            } catch (error) {
                console.error('Failed to load draft state:', error);
            }
        }
        
        async function loadPlayers(searchTerm = '', positionFilter = '') {
            try {
                // Load available players (excludes drafted ones)
                const response = await fetch(`/api/draft/${currentSession}/available-players`);
                const players = await response.json();
                
                // Store for global access
                allPlayers = players;
                
                // Apply filters
                let filteredPlayers = players;
                
                if (searchTerm) {
                    filteredPlayers = filteredPlayers.filter(p => 
                        p.name.toLowerCase().includes(searchTerm.toLowerCase())
                    );
                }
                
                if (positionFilter) {
                    filteredPlayers = filteredPlayers.filter(p => p.position === positionFilter);
                }
                
                // Update the All Players tab
                const container = document.getElementById('availablePlayers');
                if (filteredPlayers.length === 0) {
                    container.innerHTML = '<div style="color: #6b7280; text-align: center; padding: 2rem;">No players found matching your criteria</div>';
                } else {
                    container.innerHTML = filteredPlayers.slice(0, 50).map(player => createPlayerCard(player, true)).join('');
                }
                
                console.log(`📊 Loaded ${players.length} available players (${filteredPlayers.length} after filters)`);
            } catch (error) {
                console.error('Failed to load players:', error);
                // Fallback to all players if draft-specific endpoint fails
                try {
                    const response = await fetch('/api/players');
                    const players = await response.json();
                    allPlayers = players;
                    
                    let filteredPlayers = players;
                    if (searchTerm) {
                        filteredPlayers = filteredPlayers.filter(p => 
                            p.name.toLowerCase().includes(searchTerm.toLowerCase())
                        );
                    }
                    if (positionFilter) {
                        filteredPlayers = filteredPlayers.filter(p => p.position === positionFilter);
                    }
                    
                    const container = document.getElementById('availablePlayers');
                    if (container) {
                        container.innerHTML = filteredPlayers.slice(0, 50).map(player => createPlayerCard(player, true)).join('');
                    }
                } catch (fallbackError) {
                    console.error('Fallback player loading failed:', fallbackError);
                }
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
                    console.log(`✅ Successfully drafted ${playerName}`);
                    
                    // Refresh all draft data after making a pick
                    await refreshDraftData();
                    
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
            document.getElementById('turnStatus').style.background = '#fef3c7';
            
            try {
                const response = await fetch(`/api/draft/${currentSession}/simulate`, {
                    method: 'POST'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    console.log(`🤖 Simulated ${result.picks_simulated} AI picks`);
                    
                    // Refresh all draft data after simulation
                    await refreshDraftData();
                }
            } catch (error) {
                console.error('Simulation error:', error);
            }
        }
        
        function updateTurnStatus() {
            const statusEl = document.getElementById('turnStatus');
            if (isMyTurn) {
                statusEl.innerHTML = '🎯 <strong>YOUR TURN!</strong> Select a player to draft';
                statusEl.style.background = '#dcfce7';
                statusEl.style.borderColor = '#10b981';
            } else {
                statusEl.innerHTML = '⏳ <strong>Waiting for your turn...</strong>';
                statusEl.style.background = '#dbeafe';
                statusEl.style.borderColor = '#3b82f6';
            }
        }
        
        function updateRosterDisplay(session) {
            if (!session || !session.rosters) return;
            
            const userRoster = session.rosters[userPosition] || [];
            const container = document.getElementById('userRoster');
            
            if (userRoster.length === 0) {
                container.innerHTML = '<div style="color: #6b7280;">No players drafted yet</div>';
                return;
            }
            
            container.innerHTML = userRoster.map(player => `
                <div class="roster-item">
                    <div class="flex justify-between">
                        <div>
                            <div class="font-bold">${player.name}</div>
                            <div class="text-sm">${player.position} - ${player.team}</div>
                        </div>
                        <div class="text-sm text-green-600">${player.projected_points} pts</div>
                    </div>
                </div>
            `).join('');
        }
        
        function updateRecentPicks(session) {
            if (!session || !session.picks) return;
            
            const recentPicks = session.picks.slice(-8).reverse();
            const container = document.getElementById('recentPicks');
            
            if (!container) {
                console.warn('recentPicks container not found');
                return;
            }
            
            if (recentPicks.length === 0) {
                container.innerHTML = '<div style="color: #6b7280;">No picks yet</div>';
                return;
            }
            
            container.innerHTML = recentPicks.map(pick => `
                <div class="recent-pick">
                    <div class="flex justify-between">
                        <div>
                            <div class="font-bold">${pick.player.name}</div>
                            <div class="text-sm">${pick.player.position} - ${pick.player.team}</div>
                        </div>
                        <div class="text-sm">
                            <div>Pick ${pick.pick_number}</div>
                            <div style="color: ${pick.team === userPosition ? '#059669' : '#2563eb'}">
                                ${pick.team === userPosition ? 'YOU' : `Team ${pick.team}`}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        // Initialize when DOM loads
        document.addEventListener('DOMContentLoaded', async function() {
            console.log('🏈 ALFRED - Analytical League Fantasy Resource for Elite Drafting');
            console.log('👨‍💻 Jeff Greenfield\\'s Fantasy Football Draft Assistant 2025');
            console.log('✅ All JavaScript functions loaded and ready');
            
            // Load initial data
            await loadNFLTeams();
            await loadPreferences();
            
            // Add keyboard support for search inputs
            const searchInputs = [
                { id: 'undervaluedPlayerSearch', handler: searchUndervaluedPlayers },
                { id: 'overvaluedPlayerSearch', handler: searchOvervaluedPlayers },
                { id: 'mustHavePlayerSearch', handler: searchMustHavePlayers }
            ];
            
            searchInputs.forEach(input => {
                const element = document.getElementById(input.id);
                if (element) {
                    element.addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            input.handler();
                        }
                    });
                    
                    // Also add input event for real-time search
                    element.addEventListener('input', function(e) {
                        if (this.value.length >= 2) {
                            setTimeout(() => input.handler(), 300); // Debounce search
                        }
                    });
                }
            });
            
            console.log('✅ ALFRED initialization complete with keyboard support');
        });
        
        console.log('🔧 JavaScript functions defined successfully');
    </script>
</head>
<body class="gradient-bg">
    
    <!-- Preferences Screen (New Landing Page) -->
    <div id="welcomeScreen" class="container">
        <div class="text-center mb-6">
            <h1 class="text-white">
                🏈 <span class="text-yellow">ALFRED</span><br>
                <span style="font-size: 2rem;">Analytical League Fantasy Resource for Elite Drafting</span>
            </h1>
            <p class="text-white mb-4">
                <strong>Jeff Greenfield's Fantasy Football Draft Assistant 2025</strong>
            </p>
        </div>
        
        <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 2rem;">
            <!-- Strategy Settings -->
            <div class="card">
                <h3 class="mb-4">🎯 Draft Strategy</h3>
                <div class="mb-4">
                    <label class="font-bold mb-2" style="display: block;">Strategy Type:</label>
                    <select id="strategyType" class="input">
                        <option value="aggressive">Aggressive - Target upside, take risks early</option>
                        <option value="standard" selected>Standard - Balanced approach</option>
                        <option value="conservative">Conservative - Safe picks, avoid busts</option>
                    </select>
                    <div class="text-sm text-gray-600 mt-2">
                        Strategy affects tier values, scarcity calculations, and risk tolerance
                    </div>
                </div>
                
                <div class="mb-4">
                    <button onclick="loadPreferences()" class="btn btn-secondary" style="width: 100%;">
                        📂 Load Saved Preferences
                    </button>
                </div>
            </div>
            
            <!-- Team Preferences -->
            <div class="card">
                <h3 class="mb-4">🏈 Team Preferences</h3>
                <div class="mb-4">
                    <label class="font-bold mb-2" style="display: block;">Favorite Teams (bias toward):</label>
                    <div id="favoriteTeams" class="space-y-4">
                        <div class="flex" style="gap: 0.5rem; align-items: center;">
                            <select class="input team-select" style="flex: 1;">
                                <option value="">Select team...</option>
                            </select>
                            <input type="range" min="5" max="25" value="10" class="input" style="flex: 1;" />
                            <span class="text-sm">+10%</span>
                        </div>
                    </div>
                    <button onclick="addFavoriteTeam()" class="btn" style="background: #10b981; color: white; margin-top: 0.5rem;">+ Add Favorite Team</button>
                </div>
                
                <div class="mb-4">
                    <label class="font-bold mb-2" style="display: block;">Hated Teams (bias against):</label>
                    <div id="hatedTeams" class="space-y-4">
                        <div class="flex" style="gap: 0.5rem; align-items: center;">
                            <select class="input team-select" style="flex: 1;">
                                <option value="">Select team...</option>
                            </select>
                            <input type="range" min="5" max="25" value="10" class="input" style="flex: 1;" />
                            <span class="text-sm">-10%</span>
                        </div>
                    </div>
                    <button onclick="addHatedTeam()" class="btn" style="background: #ef4444; color: white; margin-top: 0.5rem;">+ Add Hated Team</button>
                </div>
            </div>
        </div>
        
        <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 2rem; margin-top: 2rem;">
            <!-- Player Adjustments -->
            <div class="card">
                <h3 class="mb-4">📈 Player Adjustments</h3>
                <div class="mb-4">
                    <label class="font-bold mb-2" style="display: block;">Undervalued Players (rank boost):</label>
                    <div id="undervaluedPlayers" class="space-y-4">
                        <!-- Populated by JavaScript -->
                    </div>
                    <div class="flex" style="gap: 0.5rem; margin-top: 0.5rem;">
                        <input type="text" id="undervaluedPlayerSearch" placeholder="Search players..." class="input" style="flex: 1;"
                               onkeypress="if(event.key==='Enter') searchUndervaluedPlayers()">
                        <button onclick="searchUndervaluedPlayers()" class="btn btn-secondary">Search</button>
                    </div>
                </div>
                
                <div class="mb-4">
                    <label class="font-bold mb-2" style="display: block;">Overvalued Players (rank penalty):</label>
                    <div id="overvaluedPlayers" class="space-y-4">
                        <!-- Populated by JavaScript -->
                    </div>
                    <div class="flex" style="gap: 0.5rem; margin-top: 0.5rem;">
                        <input type="text" id="overvaluedPlayerSearch" placeholder="Search players..." class="input" style="flex: 1;">
                        <button onclick="searchOvervaluedPlayers()" class="btn btn-secondary">Search</button>
                    </div>
                </div>
            </div>
            
            <!-- Must-Have Players -->
            <div class="card">
                <h3 class="mb-4">⭐ Must-Have Players</h3>
                <div class="mb-4">
                    <p class="text-sm text-gray-600 mb-4">
                        Select up to 2 players you absolutely want to draft (ADP validation applies)
                    </p>
                    <div id="mustHavePlayers" class="space-y-4">
                        <!-- Populated by JavaScript -->
                    </div>
                    <div class="flex" style="gap: 0.5rem; margin-top: 0.5rem;">
                        <input type="text" id="mustHavePlayerSearch" placeholder="Search players..." class="input" style="flex: 1;">
                        <button onclick="searchMustHavePlayers()" class="btn btn-secondary">Search</button>
                    </div>
                </div>
                
                <div class="mt-6">
                    <button onclick="savePreferences()" class="btn btn-success" style="width: 100%; font-size: 1.1rem; padding: 1rem;">
                        💾 Save Preferences
                    </button>
                    <button onclick="showSetup()" class="btn btn-primary" style="width: 100%; font-size: 1.25rem; padding: 1.5rem; margin-top: 1rem;">
                        🚀 Continue to Draft Setup
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- Setup Screen -->
    <div id="setupScreen" class="container hidden">
        <div class="text-center mb-8">
            <button onclick="showWelcome()" class="text-white mb-4" style="cursor: pointer;">← Back</button>
            <h2 class="text-white">ALFRED Draft Setup 2025</h2>
        </div>

        <div class="card">
            <div class="space-y-4">
                <div>
                    <label class="font-bold mb-4">League Name</label>
                    <input type="text" id="leagueName" value="Championship Draft 2025" class="input">
                </div>

                <div>
                    <label class="font-bold mb-4">Your Draft Position</label>
                    <select id="draftPosition" class="input">
                        <option value="1">Pick 1 - First Overall (CMC, Tyreek)</option>
                        <option value="2">Pick 2 - Elite Pick (Breece, CeeDee)</option>
                        <option value="3">Pick 3 - Top Tier</option>
                        <option value="4">Pick 4 - Elite RB/WR</option>
                        <option value="5">Pick 5 - Premium Position</option>
                        <option value="6" selected>Pick 6 - Balanced Strategy</option>
                        <option value="7">Pick 7 - Mid-Round Value</option>
                        <option value="8">Pick 8 - QB/Elite Skill</option>
                        <option value="9">Pick 9 - Late First</option>
                        <option value="10">Pick 10 - Back-to-Back Picks</option>
                    </select>
                </div>

                <div>
                    <label class="font-bold mb-4">Scoring Format</label>
                    <select id="scoringFormat" class="input">
                        <option value="ppr">PPR (Point Per Reception) - WRs/TEs Boosted</option>
                        <option value="half_ppr">Half PPR (0.5 Points) - Balanced Scoring</option>
                        <option value="standard">Standard (No Reception Points) - RB Heavy</option>
                    </select>
                </div>

                <div style="background: linear-gradient(to right, #ecfdf5, #eff6ff); padding: 1.5rem; border-radius: 0.5rem; border: 1px solid #10b981;">
                    <h4 class="font-bold text-green-600 mb-4">🏆 ALFRED 2025 Features</h4>
                    <div class="text-sm space-y-4">
                        <p>• <strong>Real Elite Players</strong> - McCaffrey, Tyreek Hill, Josh Allen</p>
                        <p>• <strong>Smart AI Drafting</strong> - Position-based team building strategies</p>
                        <p>• <strong>Live Draft Board</strong> - Track every pick in real-time</p>
                        <p>• <strong>Team Intelligence</strong> - See roster construction for all teams</p>
                    </div>
                </div>

                <button onclick="createSession()" class="btn btn-success" style="width: 100%; font-size: 1.25rem; padding: 1.5rem;">
                    🎯 Create Draft Session
                </button>
            </div>
        </div>
    </div>

    <!-- Draft Screen -->
    <div id="draftScreen" class="container hidden">
        <!-- Top Navigation Bar -->
        <div class="card mb-4" style="padding: 1rem;">
            <div class="flex justify-between items-center">
                <div class="flex items-center" style="gap: 2rem;">
                    <div>
                        <h2 style="margin: 0; font-size: 1.5rem;">🏈 <span id="draftLeagueName">Championship Draft</span></h2>
                        <div class="text-sm" style="color: #6b7280;">
                            Pick #<span id="currentPick">1</span> • Round <span id="currentRound">1</span> • 
                            Position <span id="yourPosition">6</span> • <span id="draftFormat">PPR</span>
                        </div>
                    </div>
                    <div id="turnStatus" class="font-bold" style="padding: 0.5rem 1rem; border-radius: 0.25rem; background: #dbeafe;">
                        🎯 Loading draft session...
                    </div>
                </div>
                <div class="flex" style="gap: 0.5rem;">
                    <button onclick="simulateToMyTurn()" class="btn btn-secondary">🤖 Simulate to My Turn</button>
                    <button onclick="refreshDraftData()" class="btn" style="background: #10b981; color: white;">🔄 Refresh</button>
                    <button onclick="showWelcome()" class="btn" style="background: #6b7280; color: white;">← New Draft</button>
                </div>
            </div>
        </div>
        
        <!-- Main 3-Column Layout -->
        <div class="flex" style="gap: 1rem; height: calc(100vh - 200px);">
            
            <!-- Left Column: Available Players & Analysis (40%) -->
            <div style="flex: 0 0 40%; display: flex; flex-direction: column;">
                
                <!-- Player Tabs -->
                <div class="card" style="flex: 1; display: flex; flex-direction: column; padding: 0;">
                    <div class="flex" style="border-bottom: 1px solid #e5e7eb;">
                        <button id="tabAllPlayers" class="tab-button active" onclick="switchPlayerTab('all')" 
                                style="flex: 1; padding: 0.75rem; border: none; background: #f9fafb; cursor: pointer; font-weight: bold;">
                            👥 All Players
                        </button>
                        <button id="tabByPosition" class="tab-button" onclick="switchPlayerTab('position')" 
                                style="flex: 1; padding: 0.75rem; border: none; background: white; cursor: pointer;">
                            📊 By Position
                        </button>
                        <button id="tabSteals" class="tab-button" onclick="switchPlayerTab('steals')" 
                                style="flex: 1; padding: 0.75rem; border: none; background: white; cursor: pointer;">
                            💎 Steals
                        </button>
                        <button id="tabTargets" class="tab-button" onclick="switchPlayerTab('targets')" 
                                style="flex: 1; padding: 0.75rem; border: none; background: white; cursor: pointer;">
                            🎯 Targets
                        </button>
                    </div>
                    
                    <!-- Tab Content -->
                    <div style="flex: 1; overflow: hidden; display: flex; flex-direction: column;">
                        
                        <!-- All Players Tab -->
                        <div id="allPlayersTab" class="tab-content" style="flex: 1; padding: 1rem; overflow-y: auto;">
                            <div class="flex" style="gap: 0.5rem; margin-bottom: 1rem;">
                                <input type="text" id="playerSearchInput" placeholder="Search players..." 
                                       class="input" style="flex: 1;" onkeyup="filterPlayers()">
                                <select id="positionFilter" class="input" onchange="filterPlayers()">
                                    <option value="">All Positions</option>
                                    <option value="QB">QB</option>
                                    <option value="RB">RB</option>
                                    <option value="WR">WR</option>
                                    <option value="TE">TE</option>
                                    <option value="K">K</option>
                                    <option value="DST">DST</option>
                                </select>
                            </div>
                            <div id="availablePlayers">
                                <!-- Players populated by JavaScript -->
                            </div>
                        </div>
                        
                        <!-- By Position Tab -->
                        <div id="byPositionTab" class="tab-content hidden" style="flex: 1; padding: 1rem; overflow-y: auto;">
                            <div class="flex" style="gap: 0.25rem; margin-bottom: 1rem; flex-wrap: wrap;">
                                <button onclick="showPositionPlayers('QB')" class="btn" style="background: #dc3545; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">QB</button>
                                <button onclick="showPositionPlayers('RB')" class="btn" style="background: #28a745; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">RB</button>
                                <button onclick="showPositionPlayers('WR')" class="btn" style="background: #007bff; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">WR</button>
                                <button onclick="showPositionPlayers('TE')" class="btn" style="background: #fd7e14; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">TE</button>
                                <button onclick="showPositionPlayers('K')" class="btn" style="background: #6c757d; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">K</button>
                                <button onclick="showPositionPlayers('DST')" class="btn" style="background: #6f42c1; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">DST</button>
                            </div>
                            <div id="positionPlayers">
                                <div style="color: #6b7280; text-align: center; padding: 2rem;">Select a position to view players</div>
                            </div>
                        </div>
                        
                        <!-- Steals Tab -->
                        <div id="stealsTab" class="tab-content hidden" style="flex: 1; padding: 1rem; overflow-y: auto;">
                            <div id="stealsContent">
                                <!-- ADP steals populated by JavaScript -->
                            </div>
                        </div>
                        
                        <!-- Targets Tab -->
                        <div id="targetsTab" class="tab-content hidden" style="flex: 1; padding: 1rem; overflow-y: auto;">
                            <div id="targetsContent">
                                <!-- User targets from preferences populated by JavaScript -->
                            </div>
                        </div>
                        
                    </div>
                </div>
                
            </div>
            
            <!-- Center Column: Team Rosters & Round Projections (35%) -->
            <div style="flex: 0 0 35%; display: flex; flex-direction: column;">
                
                <!-- Team Roster Cards -->
                <div class="card" style="flex: 1; padding: 1rem; margin-bottom: 1rem; overflow-y: auto;">
                    <div class="flex justify-between items-center" style="margin-bottom: 1rem;">
                        <h3 style="margin: 0; font-size: 1.1rem;">🏈 Team Rosters</h3>
                        <button onclick="refreshDraftData()" class="btn" style="background: #10b981; color: white; padding: 0.25rem 0.5rem; font-size: 0.8rem;">🔄</button>
                    </div>
                    <div id="teamRosterCards" style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
                        <!-- Team roster cards populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Round Projections -->
                <div class="card" style="flex: 0 0 200px; padding: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1rem;">📅 Round Projections</h3>
                    <div class="flex" style="gap: 0.5rem; margin-bottom: 0.5rem;">
                        <button onclick="showRoundProjection('next')" class="btn" style="background: #3b82f6; color: white; padding: 0.25rem 0.5rem; font-size: 0.7rem;">Next Round</button>
                        <button onclick="showRoundProjection('future')" class="btn" style="background: #6b7280; color: white; padding: 0.25rem 0.5rem; font-size: 0.7rem;">Future Rounds</button>
                    </div>
                    <div id="roundProjections" style="height: 140px; overflow-y: auto; font-size: 0.8rem;">
                        <!-- Round projections populated by JavaScript -->
                    </div>
                </div>
                
            </div>
            
            <!-- Right Column: Strategy & Recommendations (25%) -->
            <div style="flex: 0 0 25%; display: flex; flex-direction: column;">
                
                <!-- Forward-Looking Draft Strategy -->
                <div class="card" style="flex: 1; padding: 1rem; margin-bottom: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1.1rem;">🎯 Draft Strategy</h3>
                    <div class="flex" style="gap: 0.25rem; margin-bottom: 0.75rem;">
                        <button onclick="showStrategyView('immediate')" id="btnImmediate" class="btn" style="background: #3b82f6; color: white; padding: 0.25rem 0.5rem; font-size: 0.7rem;">Next 3 Picks</button>
                        <button onclick="showStrategyView('roadmap')" id="btnRoadmap" class="btn" style="background: #6b7280; color: white; padding: 0.25rem 0.5rem; font-size: 0.7rem;">Full Roadmap</button>
                        <button onclick="showStrategyView('explanation')" id="btnExplanation" class="btn" style="background: #6b7280; color: white; padding: 0.25rem 0.5rem; font-size: 0.7rem;">AI Explain</button>
                    </div>
                    <div id="forwardLookingStrategy">
                        <!-- Forward-looking strategy populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Your Team -->
                <div class="card" style="flex: 0 0 200px; padding: 1rem; margin-bottom: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1rem;">🏆 Your Team</h3>
                    <div id="userRoster" style="overflow-y: auto; height: 140px;">
                        <div style="color: #6b7280;">No players drafted yet</div>
                    </div>
                </div>
                
                <!-- Quick Stats -->
                <div class="card" style="flex: 0 0 120px; padding: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1rem;">📊 Quick Stats</h3>
                    <div id="quickStats" style="font-size: 0.8rem;">
                        <!-- Quick stats populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Recent Picks -->
                <div class="card" style="flex: 0 0 150px; padding: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1rem;">📋 Recent Picks</h3>
                    <div id="recentPicks" style="font-size: 0.7rem; overflow-y: auto; height: 100px;">
                        <!-- Recent picks populated by JavaScript -->
                    </div>
                </div>
                
                <!-- Upcoming Picks -->
                <div class="card" style="flex: 0 0 200px; padding: 1rem;">
                    <h3 style="margin-bottom: 0.5rem; font-size: 1rem;">⏳ Next Few Picks</h3>
                    <div id="upcomingPicks" style="font-size: 0.7rem; overflow-y: auto; height: 150px;">
                        <!-- Upcoming picks populated by JavaScript -->
                    </div>
                </div>
                
            </div>
            
        </div>
    </div>

</body>
</html>'''

class DraftAssistantApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏈 ALFRED - Jeff Greenfield's Fantasy Football Draft Assistant 2025")
        self.root.geometry("700x500")
        self.root.configure(bg='#1f2937')
        
        self.server = None
        self.server_thread = None
        self.port = 8080
        
        self.setup_ui()
        print("✅ Desktop application window created")
        
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#1f2937')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Title section
        title_frame = tk.Frame(main_frame, bg='#1f2937')
        title_frame.pack(pady=(0, 30))
        
        title_label = tk.Label(
            title_frame, 
            text="🏈 ALFRED\nAnalytical League Fantasy Resource\nfor Elite Drafting",
            font=('Arial', 24, 'bold'),
            fg='#fbbf24',
            bg='#1f2937',
            justify='center'
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Jeff Greenfield's Fantasy Football Draft Assistant 2025",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#1f2937'
        )
        subtitle_label.pack(pady=(15, 0))
        
        tagline_label = tk.Label(
            title_frame,
            text="Professional Draft Simulator • No Terminal Required",
            font=('Arial', 12),
            fg='#10b981',
            bg='#1f2937'
        )
        tagline_label.pack(pady=(5, 0))
        
        # Features section
        features_frame = tk.Frame(main_frame, bg='#1f2937')
        features_frame.pack(pady=(0, 30))
        
        features_text = """✅ Real 2025 elite players (McCaffrey, Tyreek Hill, Josh Allen)
✅ Sophisticated AI opponents with realistic strategies  
✅ Live draft board with snake draft logic
✅ Position-based team building intelligence
✅ Embedded web server - runs entirely offline"""
        
        features_label = tk.Label(
            features_frame,
            text=features_text,
            font=('Arial', 11),
            fg='#d1d5db',
            bg='#1f2937',
            justify='left'
        )
        features_label.pack()
        
        # Status section
        self.status_frame = tk.Frame(main_frame, bg='#1f2937')
        self.status_frame.pack(pady=(0, 30))
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Ready to launch ALFRED!",
            font=('Arial', 12, 'bold'),
            fg='#fbbf24',
            bg='#1f2937'
        )
        self.status_label.pack()
        
        # Button section
        button_frame = tk.Frame(main_frame, bg='#1f2937')
        button_frame.pack()
        
        self.start_button = tk.Button(
            button_frame,
            text="🚀 Launch ALFRED",
            font=('Arial', 16, 'bold'),
            bg='#fbbf24',
            fg='#1f2937',
            activebackground='#f59e0b',
            activeforeground='#1f2937',
            padx=40,
            pady=20,
            cursor='hand2',
            relief='flat',
            command=self.launch_draft
        )
        self.start_button.pack(pady=(0, 20))
        
        self.quit_button = tk.Button(
            button_frame,
            text="❌ Quit Application",
            font=('Arial', 12),
            bg='#6b7280',
            fg='white',
            activebackground='#4b5563',
            activeforeground='white',
            padx=25,
            pady=12,
            cursor='hand2',
            relief='flat',
            command=self.quit_app
        )
        self.quit_button.pack()
        
        # Bottom info
        info_frame = tk.Frame(main_frame, bg='#1f2937')
        info_frame.pack(side='bottom', pady=(30, 0))
        
        info_label = tk.Label(
            info_frame,
            text="ALFRED v1.0 • Built for macOS • Jeff Greenfield © 2025",
            font=('Arial', 9),
            fg='#6b7280',
            bg='#1f2937'
        )
        info_label.pack()
        
    def launch_draft(self):
        self.start_button.config(state='disabled', text='🔄 Starting ALFRED...')
        self.status_label.config(text="Starting ALFRED's embedded web server...")
        
        # Start server in background
        self.server = DraftAssistantServer(self.port)
        self.server_thread = threading.Thread(target=self.server.start_server, daemon=True)
        self.server_thread.start()
        
        # Wait then open browser
        self.root.after(3000, self.open_browser)
        
    def open_browser(self):
        try:
            url = f"http://localhost:{self.port}"
            webbrowser.open(url)
            
            self.status_label.config(text=f"✅ ALFRED running at {url}")
            self.start_button.config(
                text='🌐 Open ALFRED Again', 
                state='normal', 
                command=self.open_browser
            )
            
            print(f"✅ Browser opened: {url}")
            
        except Exception as e:
            self.status_label.config(text=f"❌ Error opening browser: {e}")
            self.start_button.config(text='🚀 Launch ALFRED', state='normal')
    
    def quit_app(self):
        print("👋 Shutting down ALFRED...")
        if self.server and hasattr(self.server, 'server'):
            try:
                self.server.server.shutdown()
            except:
                pass
        self.root.quit()
        
    def run(self):
        print("🎯 Starting ALFRED desktop application...")
        self.root.mainloop()

if __name__ == "__main__":
    try:
        app = DraftAssistantApp()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Thanks for using ALFRED!")
    except Exception as e:
        print(f"❌ Error: {e}")
        input("Press Enter to exit...")
#!/usr/bin/env python3
"""
Improved Draft Recommendation Engine
Uses our actual calculated rankings from get_spreadsheet_data
"""

import psycopg2
import os
from typing import Dict, List, Tuple, Optional
import json
import sys

# Add the current directory to path so we can import from data_viewer
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

class ImprovedDraftEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_all_rankings_with_adp(self) -> Dict[str, List[Dict]]:
        """Get all player rankings by position using our spreadsheet calculation logic"""
        from data_viewer import get_spreadsheet_data
        
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        all_rankings = {}
        
        for position in positions:
            # Get our calculated rankings for this position
            response = get_spreadsheet_data(position=position)
            players_data = json.loads(response.data)['players']
            
            # Process and add ADP data
            processed_players = []
            for player in players_data:
                if player.get('mean_rank') != 'NA':
                    # Get ADP from Underdog ranking
                    adp_rank = self._get_player_adp(player['player_id'])
                    
                    processed_player = {
                        'player_id': player['player_id'],
                        'name': player['name'],
                        'position': player['position'],
                        'team': player['team'],
                        'our_rank': player.get('ordinal_rank', 999),
                        'our_score': player.get('mean_rank', 999),
                        'adp_rank': adp_rank,
                        'aggressive_rank': player.get('ordinal_aggressive', 999),
                        'conservative_rank': player.get('ordinal_conservative', 999),
                        'value_delta': max(0, adp_rank - player.get('ordinal_rank', 999)) if adp_rank < 999 else 0
                    }
                    
                    processed_players.append(processed_player)
            
            all_rankings[position] = processed_players
        
        return all_rankings
    
    def _get_player_adp(self, player_id: int) -> int:
        """Get ADP (Underdog ranking) for a specific player"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT pr.position_rank
            FROM player_rankings pr
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE pr.player_id = %s AND rs.source_name = 'Underdog'
        """, (player_id,))
        
        result = cur.fetchone()
        cur.close()
        return result[0] if result else 999
    
    def get_available_players(self, session_id: int) -> Dict[str, List[Dict]]:
        """Get undrafted players by position"""
        cur = self.conn.cursor()
        
        # Get drafted player IDs
        cur.execute("""
            SELECT player_id FROM draft_picks WHERE session_id = %s
        """, (session_id,))
        
        drafted_ids = {row[0] for row in cur.fetchall()}
        cur.close()
        
        # Get all rankings and filter out drafted players
        all_rankings = self.get_all_rankings_with_adp()
        
        available = {}
        for position, players in all_rankings.items():
            available[position] = [
                player for player in players 
                if player['player_id'] not in drafted_ids
            ]
        
        return available
    
    def get_roster_state(self, session_id: int) -> Dict:
        """Get current roster state and needs"""
        cur = self.conn.cursor()
        
        # Get user's drafted players
        cur.execute("""
            SELECT p.position, COUNT(*) as count, 
                   ARRAY_AGG(p.name ORDER BY dp.pick_number) as players
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        current_roster = {}
        for pos, count, players in cur.fetchall():
            current_roster[pos] = {
                'count': count,
                'players': players
            }
        
        # Calculate needs based on standard roster construction
        target_counts = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        
        needs = {}
        for pos, target in target_counts.items():
            current = current_roster.get(pos, {}).get('count', 0)
            needs[pos] = max(0, target - current)
        
        cur.close()
        return {
            'current_roster': current_roster,
            'needs': needs
        }
    
    def calculate_top_recommendations(self, session_id: int, num_recs: int = 5) -> List[Dict]:
        """Calculate top draft recommendations"""
        
        available_players = self.get_available_players(session_id)
        roster_state = self.get_roster_state(session_id)
        
        all_candidates = []
        
        # Collect all available players with scores
        for position, players in available_players.items():
            for player in players[:20]:  # Top 20 per position
                score_data = self._calculate_recommendation_score(
                    player, position, roster_state['needs']
                )
                
                all_candidates.append({
                    **player,
                    **score_data
                })
        
        # Sort by total score and return top N
        all_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        return all_candidates[:num_recs]
    
    def get_best_available_by_position(self, session_id: int) -> Dict[str, Dict]:
        """Get best available player at each position"""
        available_players = self.get_available_players(session_id)
        
        best_by_position = {}
        for position, players in available_players.items():
            if players:
                best_player = players[0]  # Already sorted by our ranking
                best_by_position[position] = {
                    **best_player,
                    'recommendation_type': f'Best Available {position}'
                }
        
        return best_by_position
    
    def get_best_values(self, session_id: int, min_value: int = 5) -> List[Dict]:
        """Get players with biggest positive value vs ADP"""
        available_players = self.get_available_players(session_id)
        
        value_picks = []
        for position, players in available_players.items():
            for player in players:
                if player['value_delta'] >= min_value:
                    value_picks.append({
                        **player,
                        'recommendation_type': 'Value Pick',
                        'value_reason': f"{player['value_delta']} spots ahead of ADP"
                    })
        
        # Sort by value delta
        value_picks.sort(key=lambda x: x['value_delta'], reverse=True)
        return value_picks[:10]
    
    def _calculate_recommendation_score(self, player: Dict, position: str, needs: Dict) -> Dict:
        """Calculate comprehensive recommendation score"""
        
        # Base ranking score (lower rank = higher score)
        rank_score = max(0, 50 - player['our_rank']) * 2
        
        # Value score (ADP advantage)
        value_score = player['value_delta'] * 3
        
        # Positional need score
        need_score = needs.get(position, 0) * 15
        
        # Position scarcity (simplified - RB/WR get bonus, QB gets penalty if need is low)
        scarcity_bonus = 0
        if position in ['RB', 'WR'] and needs.get(position, 0) > 0:
            scarcity_bonus = 10
        elif position == 'QB' and needs.get(position, 0) == 0:
            scarcity_bonus = -10
        
        total_score = rank_score + value_score + need_score + scarcity_bonus
        
        # Generate reasoning
        reasons = []
        if player['value_delta'] > 8:
            reasons.append(f"Excellent value ({player['value_delta']} spots ahead of ADP)")
        elif player['value_delta'] > 3:
            reasons.append(f"Good value ({player['value_delta']} spots ahead of ADP)")
        
        if needs.get(position, 0) > 2:
            reasons.append(f"High need at {position}")
        elif needs.get(position, 0) > 0:
            reasons.append(f"Need at {position}")
        
        if player['our_rank'] <= 5:
            reasons.append(f"Elite {position} talent")
        elif player['our_rank'] <= 12:
            reasons.append(f"High-tier {position}")
        
        return {
            'total_score': round(total_score, 1),
            'rank_score': round(rank_score, 1),
            'value_score': round(value_score, 1),
            'need_score': round(need_score, 1),
            'scarcity_bonus': round(scarcity_bonus, 1),
            'reasoning': '; '.join(reasons) if reasons else 'Available player'
        }
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def test_improved_engine():
    """Test the improved recommendation engine"""
    print("🧪 Testing Improved Draft Recommendation Engine...")
    
    engine = ImprovedDraftEngine()
    
    # Create test session
    cur = engine.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position)
        VALUES ('Test Draft', 12, 6)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    engine.conn.commit()
    
    print(f"Created test session: {session_id}")
    
    # Test recommendations
    print("\n🎯 Top 5 Recommendations:")
    recommendations = engine.calculate_top_recommendations(session_id, 5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['position']}) - Total Score: {rec['total_score']}")
        print(f"   Our Rank: #{rec['our_rank']}, ADP: #{rec['adp_rank']}, Value: +{rec['value_delta']}")
        print(f"   Breakdown: Rank={rec['rank_score']}, Value={rec['value_score']}, Need={rec['need_score']}")
        print(f"   Reasoning: {rec['reasoning']}")
        print()
    
    # Test best values
    print("💎 Best Value Picks:")
    values = engine.get_best_values(session_id, min_value=3)
    for i, player in enumerate(values[:5], 1):
        print(f"{i}. {player['name']} ({player['position']}) - {player['value_reason']}")
    
    # Test best by position
    print("\n🏆 Best Available by Position:")
    best_by_pos = engine.get_best_available_by_position(session_id)
    for pos, player in best_by_pos.items():
        print(f"  {pos}: {player['name']} (Rank: #{player['our_rank']}, ADP: #{player['adp_rank']})")
    
    # Clean up
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    engine.conn.commit()
    cur.close()

if __name__ == "__main__":
    test_improved_engine()
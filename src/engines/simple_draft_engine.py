#!/usr/bin/env python3
"""
Simple Draft Recommendation Engine
Direct database access version
"""

import psycopg2
import os
from typing import Dict, List, Tuple, Optional
import json

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

class SimpleDraftEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_position_rankings(self, position: str) -> List[Dict]:
        """Get rankings for a specific position with ADP"""
        cur = self.conn.cursor()
        
        # Get position-specific Mike Clay rankings and ADP
        cur.execute("""
            SELECT 
                p.player_id,
                p.name,
                p.position,
                p.team,
                our_rank.position_rank as our_rank,
                adp.position_rank as adp_rank,
                CASE 
                    WHEN adp.position_rank > our_rank.position_rank 
                    THEN adp.position_rank - our_rank.position_rank
                    ELSE 0
                END as value_delta
            FROM players p
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank,
                       ROW_NUMBER() OVER (ORDER BY pr.position_rank) as ordinal_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = %s
            ) our_rank ON p.player_id = our_rank.player_id
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = 'Underdog'
            ) adp ON p.player_id = adp.player_id
            WHERE p.position = %s 
            AND (our_rank.position_rank IS NOT NULL OR adp.position_rank IS NOT NULL)
            ORDER BY COALESCE(our_rank.ordinal_rank, 999), COALESCE(our_rank.position_rank, 999)
            LIMIT 50
        """, (f'Mike_Clay_{position}', position))
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'our_rank': row[4] if row[4] else 999,
                'adp_rank': row[5] if row[5] else 999,
                'value_delta': row[6] if row[6] else 0
            })
        
        cur.close()
        return players
    
    def get_available_players(self, session_id: int) -> Dict[str, List[Dict]]:
        """Get undrafted players by position"""
        cur = self.conn.cursor()
        
        # Get drafted player IDs
        cur.execute("""
            SELECT player_id FROM draft_picks WHERE session_id = %s
        """, (session_id,))
        
        drafted_ids = {row[0] for row in cur.fetchall()}
        cur.close()
        
        # Get rankings for each position
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        available = {}
        
        for position in positions:
            all_players = self.get_position_rankings(position)
            available[position] = [
                player for player in all_players 
                if player['player_id'] not in drafted_ids
            ]
        
        return available
    
    def get_roster_needs(self, session_id: int) -> Dict[str, int]:
        """Calculate roster needs"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT p.position, COUNT(*) as count
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        current_roster = {pos: count for pos, count in cur.fetchall()}
        
        # Standard needs
        target_counts = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        
        needs = {}
        for pos, target in target_counts.items():
            current = current_roster.get(pos, 0)
            needs[pos] = max(0, target - current)
        
        cur.close()
        return needs
    
    def calculate_recommendations(self, session_id: int, num_recs: int = 5) -> List[Dict]:
        """Calculate draft recommendations"""
        
        available_players = self.get_available_players(session_id)
        needs = self.get_roster_needs(session_id)
        
        all_candidates = []
        
        for position, players in available_players.items():
            for player in players[:15]:  # Top 15 per position
                score = self._calculate_score(player, position, needs)
                
                all_candidates.append({
                    **player,
                    'total_score': score['total'],
                    'reasoning': score['reasoning'],
                    'breakdown': score['breakdown']
                })
        
        # Sort by score and return top recommendations
        all_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        return all_candidates[:num_recs]
    
    def get_best_values(self, session_id: int, min_value: int = 5) -> List[Dict]:
        """Get best value picks (ADP vs our ranking)"""
        available_players = self.get_available_players(session_id)
        
        value_picks = []
        for position, players in available_players.items():
            for player in players:
                if player['value_delta'] >= min_value:
                    value_picks.append({
                        **player,
                        'value_reason': f"{player['value_delta']} spots better than ADP"
                    })
        
        value_picks.sort(key=lambda x: x['value_delta'], reverse=True)
        return value_picks[:10]
    
    def get_best_by_position(self, session_id: int) -> Dict[str, Dict]:
        """Get best available at each position"""
        available_players = self.get_available_players(session_id)
        
        best_by_position = {}
        for position, players in available_players.items():
            if players:
                best_by_position[position] = players[0]
        
        return best_by_position
    
    def _calculate_score(self, player: Dict, position: str, needs: Dict) -> Dict:
        """Calculate recommendation score with breakdown"""
        
        # Ranking score (better rank = higher score)
        rank_score = max(0, 30 - player['our_rank']) * 2
        
        # Value score (ADP advantage)
        value_score = player['value_delta'] * 4
        
        # Need score (how much we need this position)
        need_multiplier = needs.get(position, 0)
        need_score = need_multiplier * 20
        
        # Position strategy bonuses
        strategy_bonus = 0
        if position in ['RB', 'WR'] and need_multiplier > 0:
            strategy_bonus = 10  # Skill position bonus when needed
        elif position == 'QB' and need_multiplier == 0:
            strategy_bonus = -15  # Penalty for QB when not needed
        
        total = rank_score + value_score + need_score + strategy_bonus
        
        # Build reasoning
        reasons = []
        if player['value_delta'] > 10:
            reasons.append(f"Excellent value (+{player['value_delta']} vs ADP)")
        elif player['value_delta'] > 5:
            reasons.append(f"Good value (+{player['value_delta']} vs ADP)")
        
        if need_multiplier > 2:
            reasons.append(f"High need at {position}")
        elif need_multiplier > 0:
            reasons.append(f"Moderate need at {position}")
        
        if player['our_rank'] <= 5:
            reasons.append(f"Elite {position}")
        elif player['our_rank'] <= 12:
            reasons.append(f"High-tier {position}")
        
        return {
            'total': round(total, 1),
            'breakdown': {
                'rank': round(rank_score, 1),
                'value': round(value_score, 1), 
                'need': round(need_score, 1),
                'strategy': round(strategy_bonus, 1)
            },
            'reasoning': '; '.join(reasons) if reasons else 'Available player'
        }
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def test_simple_engine():
    """Test the simple draft engine"""
    print("🧪 Testing Simple Draft Recommendation Engine...")
    
    engine = SimpleDraftEngine()
    
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
    print("\n🎯 Top 5 Overall Recommendations:")
    recommendations = engine.calculate_recommendations(session_id, 5)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['position']}) - Score: {rec['total_score']}")
        print(f"   Our Rank: #{rec['our_rank']}, ADP: #{rec['adp_rank']}, Value: +{rec['value_delta']}")
        print(f"   Breakdown: Rank={rec['breakdown']['rank']}, Value={rec['breakdown']['value']}, Need={rec['breakdown']['need']}")
        print(f"   Reasoning: {rec['reasoning']}")
        print()
    
    # Test best values
    print("💎 Best Value Picks:")
    values = engine.get_best_values(session_id, min_value=3)
    for i, player in enumerate(values[:5], 1):
        print(f"{i}. {player['name']} ({player['position']}) - {player['value_reason']}")
    print()
    
    # Test best by position
    print("🏆 Best Available by Position:")
    best_by_pos = engine.get_best_by_position(session_id)
    for pos, player in best_by_pos.items():
        value_text = f", Value: +{player['value_delta']}" if player['value_delta'] > 0 else ""
        print(f"  {pos}: {player['name']} (Rank: #{player['our_rank']}, ADP: #{player['adp_rank']}{value_text})")
    
    # Clean up
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    engine.conn.commit()
    cur.close()

if __name__ == "__main__":
    test_simple_engine()
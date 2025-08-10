#!/usr/bin/env python3
"""
Draft Recommendation Engine
Calculates optimal draft picks based on value, position needs, and strategy
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

class DraftRecommendationEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_available_players(self, session_id: int, position: str = None) -> List[Dict]:
        """Get all available (undrafted) players with rankings and ADP"""
        cur = self.conn.cursor()
        
        # Get our ranking strategy from settings
        cur.execute("SELECT setting_value FROM user_settings WHERE setting_name = 'default_strategy'")
        strategy_result = cur.fetchone()
        strategy = strategy_result[0] if strategy_result else 'standard'
        
        # Map strategy to column name
        rank_column_map = {
            'standard': 'mean_rank',
            'aggressive': 'aggressive_rank', 
            'conservative': 'conservative_rank',
            'aggressive_high': 'aggressive_high_rank',
            'conservative_high': 'conservative_high_rank'
        }
        
        # Build the query - get players not yet drafted with our rankings and ADP
        position_filter = "AND p.position = %s" if position else ""
        
        query = f"""
            WITH player_data AS (
                SELECT 
                    p.player_id,
                    p.name,
                    p.position,
                    p.team,
                    -- Our rankings from spreadsheet calculation (simplified for now)
                    COALESCE(our_rank.position_rank, 999) as our_rank,
                    -- ADP from Underdog
                    COALESCE(adp.position_rank, 999) as adp_rank,
                    -- Calculate value (lower our_rank vs higher adp_rank = better value)
                    CASE 
                        WHEN COALESCE(our_rank.position_rank, 999) < COALESCE(adp.position_rank, 999)
                        THEN COALESCE(adp.position_rank, 999) - COALESCE(our_rank.position_rank, 999)
                        ELSE 0
                    END as value_delta
                FROM players p
                LEFT JOIN (
                    SELECT pr.player_id, pr.position_rank
                    FROM player_rankings pr
                    JOIN ranking_sources rs ON pr.source_id = rs.source_id
                    WHERE rs.source_name = 'Mike_Clay_QB'  -- Use Mike Clay as our ranking for now
                ) our_rank ON p.player_id = our_rank.player_id
                LEFT JOIN (
                    SELECT pr.player_id, pr.position_rank
                    FROM player_rankings pr
                    JOIN ranking_sources rs ON pr.source_id = rs.source_id
                    WHERE rs.source_name = 'Underdog'
                ) adp ON p.player_id = adp.player_id
                WHERE p.player_id NOT IN (
                    SELECT player_id FROM draft_picks WHERE session_id = %s
                )
                {position_filter}
            )
            SELECT * FROM player_data
            WHERE our_rank < 999 OR adp_rank < 999  -- Only players with some ranking
            ORDER BY our_rank, value_delta DESC
            LIMIT 100
        """
        
        params = [session_id]
        if position:
            params.append(position)
            
        cur.execute(query, params)
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'our_rank': row[4],
                'adp_rank': row[5],
                'value_delta': row[6]
            })
        
        cur.close()
        return players
    
    def get_roster_needs(self, session_id: int) -> Dict[str, int]:
        """Calculate current roster needs based on drafted players"""
        cur = self.conn.cursor()
        
        # Get current roster
        cur.execute("""
            SELECT p.position, COUNT(*) as count
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        current_roster = {pos: count for pos, count in cur.fetchall()}
        
        # Standard roster needs (can be made configurable)
        standard_needs = {
            'QB': 2,
            'RB': 4, 
            'WR': 5,
            'TE': 2,
            'K': 1,
            'DST': 1
        }
        
        needs = {}
        for pos, target in standard_needs.items():
            current = current_roster.get(pos, 0)
            needs[pos] = max(0, target - current)
        
        cur.close()
        return needs
    
    def get_positional_scarcity(self) -> Dict[str, float]:
        """Calculate positional scarcity based on quality drop-off"""
        cur = self.conn.cursor()
        
        # Simple scarcity calculation - difference between top 12 and next 12 players
        scarcity = {}
        positions = ['QB', 'RB', 'WR', 'TE']
        
        for pos in positions:
            cur.execute("""
                WITH ranked_players AS (
                    SELECT 
                        pr.position_rank,
                        ROW_NUMBER() OVER (ORDER BY pr.position_rank) as overall_rank
                    FROM player_rankings pr
                    JOIN ranking_sources rs ON pr.source_id = rs.source_id
                    JOIN players p ON pr.player_id = p.player_id
                    WHERE rs.source_name = 'Mike_Clay_QB' AND p.position = %s
                    ORDER BY pr.position_rank
                    LIMIT 24
                )
                SELECT 
                    AVG(CASE WHEN overall_rank <= 12 THEN position_rank END) as top_12_avg,
                    AVG(CASE WHEN overall_rank > 12 THEN position_rank END) as next_12_avg
                FROM ranked_players
            """, (pos,))
            
            result = cur.fetchone()
            if result and result[0] and result[1]:
                # Higher scarcity = bigger difference between tiers
                scarcity[pos] = result[1] - result[0]
            else:
                scarcity[pos] = 1.0
        
        cur.close()
        return scarcity
    
    def calculate_recommendations(self, session_id: int, num_recommendations: int = 5) -> List[Dict]:
        """Main recommendation algorithm"""
        
        # Get current draft state
        available_players = self.get_available_players(session_id)
        roster_needs = self.get_roster_needs(session_id)
        scarcity = self.get_positional_scarcity()
        
        recommendations = []
        
        for player in available_players[:50]:  # Consider top 50 available
            score = self._calculate_player_score(player, roster_needs, scarcity)
            
            recommendations.append({
                **player,
                'recommendation_score': score,
                'reasoning': self._get_recommendation_reasoning(player, roster_needs, scarcity)
            })
        
        # Sort by recommendation score and return top N
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        return recommendations[:num_recommendations]
    
    def _calculate_player_score(self, player: Dict, needs: Dict[str, int], scarcity: Dict[str, float]) -> float:
        """Calculate overall recommendation score for a player"""
        
        # Base value score (ADP vs our ranking)
        value_score = player.get('value_delta', 0) * 0.4
        
        # Position need multiplier
        position = player['position']
        need_multiplier = needs.get(position, 0) * 0.3
        
        # Scarcity bonus
        scarcity_bonus = scarcity.get(position, 1.0) * 0.2
        
        # Ranking quality (lower rank = higher score)
        rank_score = max(0, 100 - player.get('our_rank', 99)) * 0.1
        
        total_score = value_score + need_multiplier + scarcity_bonus + rank_score
        
        return round(total_score, 2)
    
    def _get_recommendation_reasoning(self, player: Dict, needs: Dict[str, int], scarcity: Dict[str, float]) -> str:
        """Generate human-readable reasoning for recommendation"""
        reasons = []
        
        # Value reasoning
        value_delta = player.get('value_delta', 0)
        if value_delta > 10:
            reasons.append(f"Excellent value ({value_delta} spots ahead of ADP)")
        elif value_delta > 5:
            reasons.append(f"Good value ({value_delta} spots ahead of ADP)")
        
        # Position need reasoning
        position = player['position']
        need = needs.get(position, 0)
        if need > 2:
            reasons.append(f"High positional need ({need} {position}s still needed)")
        elif need > 0:
            reasons.append(f"Positional need ({need} {position}s still needed)")
        
        # Scarcity reasoning
        if scarcity.get(position, 0) > 5:
            reasons.append(f"{position} position has high scarcity")
        
        # Ranking reasoning
        our_rank = player.get('our_rank', 999)
        if our_rank <= 5:
            reasons.append(f"Top-tier {position} (#{our_rank} overall)")
        elif our_rank <= 12:
            reasons.append(f"High-tier {position} (#{our_rank} overall)")
        
        return "; ".join(reasons) if reasons else "Available player"
    
    def get_best_by_position(self, session_id: int) -> Dict[str, Dict]:
        """Get the best available player at each position"""
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'DST']
        best_by_position = {}
        
        for position in positions:
            players = self.get_available_players(session_id, position)
            if players:
                best_by_position[position] = players[0]
        
        return best_by_position
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

def test_recommendations():
    """Test the recommendation engine"""
    print("🧪 Testing Draft Recommendation Engine...")
    
    engine = DraftRecommendationEngine()
    
    # Create a test draft session
    cur = engine.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position)
        VALUES ('Test Draft', 12, 6)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    engine.conn.commit()
    
    print(f"Created test session: {session_id}")
    
    # Get recommendations
    recommendations = engine.calculate_recommendations(session_id, 5)
    
    print("\n🎯 Top 5 Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['name']} ({rec['position']}) - Score: {rec['recommendation_score']}")
        print(f"   Our Rank: {rec['our_rank']}, ADP: {rec['adp_rank']}, Value: +{rec['value_delta']}")
        print(f"   Reasoning: {rec['reasoning']}")
        print()
    
    # Get best by position
    best_by_pos = engine.get_best_by_position(session_id)
    print("🏆 Best Available by Position:")
    for pos, player in best_by_pos.items():
        print(f"  {pos}: {player['name']} (Rank: {player['our_rank']}, ADP: {player['adp_rank']})")
    
    # Clean up test session
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    engine.conn.commit()
    cur.close()

if __name__ == "__main__":
    test_recommendations()
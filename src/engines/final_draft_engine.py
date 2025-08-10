#!/usr/bin/env python3
"""
Final Draft Recommendation Engine
Uses Mike_Clay_Position_Rankings and Underdog ADP for recommendations
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

class FinalDraftEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_position_rankings(self, position: str) -> List[Dict]:
        """Get rankings for a specific position"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT 
                p.player_id,
                p.name,
                p.position,
                p.team,
                our_rank.position_rank as our_rank,
                adp.position_rank as adp_rank,
                CASE 
                    WHEN adp.position_rank > our_rank.position_rank AND our_rank.position_rank IS NOT NULL
                    THEN adp.position_rank - our_rank.position_rank
                    ELSE 0
                END as value_delta
            FROM players p
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = 'Mike_Clay_Position_Rankings'
            ) our_rank ON p.player_id = our_rank.player_id
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = 'Underdog'
            ) adp ON p.player_id = adp.player_id
            WHERE p.position = %s 
            AND (our_rank.position_rank IS NOT NULL OR adp.position_rank IS NOT NULL)
            ORDER BY COALESCE(our_rank.position_rank, 999), COALESCE(adp.position_rank, 999)
            LIMIT 50
        """, (position,))
        
        players = []
        ordinal_rank = 1
        for row in cur.fetchall():
            our_rank = row[4] if row[4] else 999
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'our_rank': our_rank,
                'our_ordinal': ordinal_rank if our_rank < 999 else 999,
                'adp_rank': row[5] if row[5] else 999,
                'value_delta': row[6] if row[6] else 0
            })
            if our_rank < 999:
                ordinal_rank += 1
        
        cur.close()
        return players
    
    def get_available_players(self, session_id: int) -> Dict[str, List[Dict]]:
        """Get undrafted players by position"""
        cur = self.conn.cursor()
        
        # Get drafted player IDs
        cur.execute("SELECT player_id FROM draft_picks WHERE session_id = %s", (session_id,))
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
    
    def get_roster_needs(self, session_id: int) -> Dict:
        """Get current roster and calculate needs"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT p.position, COUNT(*) as count, ARRAY_AGG(p.name) as players
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s AND dp.is_user_pick = TRUE
            GROUP BY p.position
        """, (session_id,))
        
        current_roster = {}
        for pos, count, players in cur.fetchall():
            current_roster[pos] = {'count': count, 'players': players}
        
        # Standard roster targets
        targets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        
        needs = {}
        for pos, target in targets.items():
            current = current_roster.get(pos, {}).get('count', 0)
            needs[pos] = max(0, target - current)
        
        cur.close()
        return {'current': current_roster, 'needs': needs}
    
    def calculate_recommendations(self, session_id: int) -> Dict:
        """Main recommendation function"""
        available = self.get_available_players(session_id)
        roster_info = self.get_roster_needs(session_id)
        needs = roster_info['needs']
        
        # 1. Overall top recommendations
        top_recommendations = self._get_top_overall(available, needs, 5)
        
        # 2. Best available by position
        best_by_position = self._get_best_by_position(available)
        
        # 3. Best value picks
        best_values = self._get_best_values(available, 5)
        
        # 4. Positional recommendations based on need
        positional_recs = self._get_positional_recommendations(available, needs)
        
        return {
            'top_recommendations': top_recommendations,
            'best_by_position': best_by_position,
            'best_values': best_values,
            'positional_recommendations': positional_recs,
            'roster_state': roster_info
        }
    
    def _get_top_overall(self, available: Dict, needs: Dict, count: int) -> List[Dict]:
        """Get top overall recommendations"""
        all_candidates = []
        
        for position, players in available.items():
            for player in players[:20]:  # Top 20 per position
                score_data = self._calculate_player_score(player, position, needs)
                all_candidates.append({**player, **score_data})
        
        all_candidates.sort(key=lambda x: x['total_score'], reverse=True)
        return all_candidates[:count]
    
    def _get_best_by_position(self, available: Dict) -> Dict:
        """Best available player at each position"""
        best = {}
        for pos, players in available.items():
            if players:
                player = players[0]
                best[pos] = {
                    **player,
                    'recommendation_type': f'Best {pos} Available',
                    'tier': self._get_player_tier(player['our_ordinal'])
                }
        return best
    
    def _get_best_values(self, available: Dict, count: int) -> List[Dict]:
        """Best value picks (biggest ADP advantage)"""
        value_candidates = []
        
        for position, players in available.items():
            for player in players:
                if player['value_delta'] >= 3:  # At least 3 spots better than ADP
                    value_candidates.append({
                        **player,
                        'recommendation_type': 'Value Pick',
                        'value_reason': f"{player['value_delta']} spots ahead of ADP"
                    })
        
        value_candidates.sort(key=lambda x: x['value_delta'], reverse=True)
        return value_candidates[:count]
    
    def _get_positional_recommendations(self, available: Dict, needs: Dict) -> Dict:
        """Position-specific recommendations based on need"""
        recs = {}
        
        for position, need_count in needs.items():
            if need_count > 0 and position in available:
                players = available[position][:5]  # Top 5 available
                
                recs[position] = {
                    'need_level': 'High' if need_count > 2 else 'Medium' if need_count > 1 else 'Low',
                    'players': [{
                        **player,
                        'tier': self._get_player_tier(player['our_ordinal']),
                        'recommendation_reason': self._get_position_reason(player, position, need_count)
                    } for player in players]
                }
        
        return recs
    
    def _calculate_player_score(self, player: Dict, position: str, needs: Dict) -> Dict:
        """Calculate comprehensive player score"""
        
        # Base ranking score (better our rank = higher score)
        if player['our_rank'] < 999:
            rank_score = max(0, 50 - player['our_rank']) * 1.5
        else:
            rank_score = 0
        
        # Value score (ADP advantage)
        value_score = player['value_delta'] * 3
        
        # Need score
        need_multiplier = needs.get(position, 0)
        need_score = need_multiplier * 25
        
        # Position-specific bonuses
        position_bonus = 0
        if position in ['RB', 'WR'] and need_multiplier > 0:
            position_bonus = 15  # Skill positions when needed
        elif position == 'QB' and need_multiplier == 0:
            position_bonus = -20  # Penalty for QB when full
        elif position in ['K', 'DST'] and need_multiplier == 0:
            position_bonus = -30  # Big penalty for K/DST when not needed
        
        # Tier bonus (elite players get extra points)
        tier_bonus = 0
        if player['our_ordinal'] <= 3:
            tier_bonus = 20  # Elite tier
        elif player['our_ordinal'] <= 8:
            tier_bonus = 10  # High tier
        elif player['our_ordinal'] <= 15:
            tier_bonus = 5   # Mid tier
        
        total = rank_score + value_score + need_score + position_bonus + tier_bonus
        
        # Generate reasoning
        reasons = []
        if player['value_delta'] > 10:
            reasons.append(f"Excellent value (+{player['value_delta']} vs ADP)")
        elif player['value_delta'] > 5:
            reasons.append(f"Good value (+{player['value_delta']} vs ADP)")
        
        if need_multiplier > 2:
            reasons.append(f"High need at {position}")
        elif need_multiplier > 0:
            reasons.append(f"Roster need at {position}")
        
        tier = self._get_player_tier(player['our_ordinal'])
        if tier != 'Available':
            reasons.append(f"{tier} tier {position}")
        
        return {
            'total_score': round(total, 1),
            'breakdown': {
                'rank_score': round(rank_score, 1),
                'value_score': round(value_score, 1),
                'need_score': round(need_score, 1),
                'position_bonus': round(position_bonus, 1),
                'tier_bonus': round(tier_bonus, 1)
            },
            'tier': tier,
            'reasoning': '; '.join(reasons) if reasons else 'Available player'
        }
    
    def _get_player_tier(self, ordinal_rank: int) -> str:
        """Get tier description for player"""
        if ordinal_rank <= 3:
            return 'Elite'
        elif ordinal_rank <= 8:
            return 'High'
        elif ordinal_rank <= 15:
            return 'Mid'
        elif ordinal_rank <= 25:
            return 'Low'
        else:
            return 'Available'
    
    def _get_position_reason(self, player: Dict, position: str, need_count: int) -> str:
        """Get position-specific recommendation reason"""
        reasons = []
        
        if need_count > 2:
            reasons.append(f"Fill {need_count} {position} spots")
        elif need_count > 0:
            reasons.append(f"Need {need_count} more {position}")
        
        if player['value_delta'] > 5:
            reasons.append(f"Great value vs ADP")
        
        tier = self._get_player_tier(player['our_ordinal'])
        if tier in ['Elite', 'High']:
            reasons.append(f"{tier} talent")
        
        return '; '.join(reasons) if reasons else 'Available option'
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def test_final_engine():
    """Test the final engine"""
    print("🧪 Testing Final Draft Recommendation Engine...")
    
    engine = FinalDraftEngine()
    
    # Create test session
    cur = engine.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position)
        VALUES ('Test Draft', 12, 6)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    engine.conn.commit()
    
    print(f"✅ Created test session: {session_id}")
    
    # Get comprehensive recommendations
    recommendations = engine.calculate_recommendations(session_id)
    
    print("\n🎯 Top 5 Overall Recommendations:")
    for i, rec in enumerate(recommendations['top_recommendations'], 1):
        print(f"{i}. {rec['name']} ({rec['position']}) - Score: {rec['total_score']} ({rec['tier']})")
        print(f"   Our Rank: #{rec['our_rank']}, ADP: #{rec['adp_rank']}, Value: +{rec['value_delta']}")
        print(f"   {rec['reasoning']}")
        print()
    
    print("💎 Best Value Picks:")
    for i, val in enumerate(recommendations['best_values'], 1):
        print(f"{i}. {val['name']} ({val['position']}) - {val['value_reason']}")
    print()
    
    print("🏆 Best Available by Position:")
    for pos, player in recommendations['best_by_position'].items():
        value_text = f", +{player['value_delta']} vs ADP" if player['value_delta'] > 0 else ""
        print(f"  {pos}: {player['name']} ({player['tier']} tier{value_text})")
    print()
    
    print("📊 Positional Needs Analysis:")
    for pos, info in recommendations['positional_recommendations'].items():
        print(f"  {pos} ({info['need_level']} need): {info['players'][0]['name']} - {info['players'][0]['recommendation_reason']}")
    
    # Clean up
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    engine.conn.commit()
    cur.close()
    
    print(f"\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_final_engine()
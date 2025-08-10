#!/usr/bin/env python3
"""
Corrected Draft Recommendation Engine
Proper ADP usage: identify players available past their expected draft position
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

class CorrectedDraftEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def get_current_pick_number(self, session_id: int) -> int:
        """Get the current pick number in the draft"""
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT COALESCE(MAX(pick_number), 0) + 1 as next_pick
            FROM draft_picks 
            WHERE session_id = %s
        """, (session_id,))
        
        result = cur.fetchone()
        cur.close()
        return result[0] if result else 1
    
    def get_available_players_with_adp(self, session_id: int) -> List[Dict]:
        """Get all available players with their ADP"""
        cur = self.conn.cursor()
        
        # Get drafted player IDs
        cur.execute("SELECT player_id FROM draft_picks WHERE session_id = %s", (session_id,))
        drafted_ids = {row[0] for row in cur.fetchall()}
        
        # Get all players with our rankings and consensus ADP
        cur.execute("""
            SELECT 
                p.player_id,
                p.name,
                p.position,
                p.team,
                our_rank.position_rank as our_position_rank,
                adp.consensus_rank as adp
            FROM players p
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = 'Mike_Clay_Position_Rankings'
            ) our_rank ON p.player_id = our_rank.player_id
            LEFT JOIN consensus_adp adp ON p.player_id = adp.player_id
            WHERE p.player_id NOT IN ({})
            AND (our_rank.position_rank IS NOT NULL OR adp.consensus_rank IS NOT NULL)
            ORDER BY COALESCE(adp.consensus_rank, 999), COALESCE(our_rank.position_rank, 999)
        """.format(','.join(str(pid) for pid in drafted_ids) if drafted_ids else '0'))
        
        players = []
        for row in cur.fetchall():
            players.append({
                'player_id': row[0],
                'name': row[1],
                'position': row[2],
                'team': row[3],
                'our_position_rank': row[4] if row[4] else 999,
                'adp': row[5] if row[5] else 999
            })
        
        cur.close()
        return players
    
    def get_roster_needs(self, session_id: int) -> Dict:
        """Get current roster and needs"""
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
        
        # Standard targets
        targets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        
        needs = {}
        for pos, target in targets.items():
            current = current_roster.get(pos, {}).get('count', 0)
            needs[pos] = max(0, target - current)
        
        cur.close()
        return {'current': current_roster, 'needs': needs}
    
    def calculate_recommendations(self, session_id: int) -> Dict:
        """Main recommendation function"""
        current_pick = self.get_current_pick_number(session_id)
        available_players = self.get_available_players_with_adp(session_id)
        roster_info = self.get_roster_needs(session_id)
        
        # 1. Our algorithm recommendations (no ADP involved)
        our_recommendations = self._get_our_algorithm_recommendations(available_players, roster_info['needs'])
        
        # 2. ADP-based value picks (players available past their ADP)
        adp_values = self._get_adp_value_picks(available_players, current_pick) 
        
        # 3. Next likely picks by ADP (for matching real draft)
        likely_next_picks = self._get_likely_next_picks(available_players, current_pick)
        
        # 4. Best available by position (our rankings)
        best_by_position = self._get_best_by_position(available_players)
        
        return {
            'current_pick': current_pick,
            'our_recommendations': our_recommendations,
            'adp_value_picks': adp_values,
            'likely_next_picks': likely_next_picks,
            'best_by_position': best_by_position,
            'roster_state': roster_info
        }
    
    def _get_our_algorithm_recommendations(self, available_players: List[Dict], needs: Dict) -> List[Dict]:
        """Get recommendations based purely on our ranking algorithm"""
        recommendations = []
        
        for player in available_players:
            if player['our_position_rank'] < 999:  # Only players we have ranked
                score = self._calculate_our_score(player, needs)
                recommendations.append({
                    **player,
                    **score
                })
        
        recommendations.sort(key=lambda x: x['total_score'], reverse=True)
        return recommendations[:5]
    
    def _get_adp_value_picks(self, available_players: List[Dict], current_pick: int) -> List[Dict]:
        """Get players who should have been drafted already based on ADP"""
        value_picks = []
        
        for player in available_players:
            if player['adp'] < 999:  # Only players with ADP
                # If current pick is past their ADP, they're a value
                picks_past_adp = current_pick - player['adp']
                if picks_past_adp > 0:
                    value_picks.append({
                        **player,
                        'picks_past_adp': picks_past_adp,
                        'value_reason': f"Available {picks_past_adp} picks past ADP #{player['adp']}"
                    })
        
        value_picks.sort(key=lambda x: x['picks_past_adp'], reverse=True)
        return value_picks[:10]
    
    def _get_likely_next_picks(self, available_players: List[Dict], current_pick: int) -> List[Dict]:
        """Get players likely to be drafted next based on ADP"""
        likely_picks = []
        
        for player in available_players:
            if player['adp'] < 999:  # Only players with ADP
                # Players with ADP near current pick are likely to go soon
                adp_distance = abs(player['adp'] - current_pick)
                if adp_distance <= 10:  # Within 10 picks of their ADP
                    likely_picks.append({
                        **player,
                        'adp_distance': adp_distance,
                        'likelihood': 'High' if adp_distance <= 3 else 'Medium' if adp_distance <= 6 else 'Low'
                    })
        
        likely_picks.sort(key=lambda x: x['adp'])
        return likely_picks[:15]
    
    def _get_best_by_position(self, available_players: List[Dict]) -> Dict:
        """Best available by position using our rankings"""
        best = {}
        
        # Group by position
        by_position = {}
        for player in available_players:
            pos = player['position']
            if pos not in by_position:
                by_position[pos] = []
            by_position[pos].append(player)
        
        for pos, players in by_position.items():
            # Sort by our ranking
            players_with_rank = [p for p in players if p['our_position_rank'] < 999]
            if players_with_rank:
                players_with_rank.sort(key=lambda x: x['our_position_rank'])
                best[pos] = players_with_rank[0]
        
        return best
    
    def _calculate_our_score(self, player: Dict, needs: Dict) -> Dict:
        """Calculate score based purely on our algorithm (no ADP)"""
        position = player['position']
        
        # Base ranking score
        rank_score = max(0, 50 - player['our_position_rank']) * 2
        
        # Need multiplier
        need_multiplier = needs.get(position, 0)
        need_score = need_multiplier * 25
        
        # Position strategy
        position_bonus = 0
        if position in ['RB', 'WR'] and need_multiplier > 0:
            position_bonus = 15
        elif position == 'QB' and need_multiplier == 0:
            position_bonus = -20
        
        total = rank_score + need_score + position_bonus
        
        # Reasoning
        reasons = []
        if need_multiplier > 2:
            reasons.append(f"High need at {position}")
        elif need_multiplier > 0:
            reasons.append(f"Roster need at {position}")
        
        if player['our_position_rank'] <= 5:
            reasons.append(f"Elite {position} talent")
        elif player['our_position_rank'] <= 12:
            reasons.append(f"High-tier {position}")
        
        return {
            'total_score': round(total, 1),
            'reasoning': '; '.join(reasons) if reasons else 'Available player'
        }
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def test_corrected_engine():
    """Test the corrected engine"""
    print("🧪 Testing Corrected Draft Recommendation Engine...")
    
    engine = CorrectedDraftEngine()
    
    # Create test session
    cur = engine.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position)
        VALUES ('Test Draft', 12, 6)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    engine.conn.commit()
    
    # Simulate we're at pick 25 by drafting some top ADP players
    cur.execute("""
        SELECT p.player_id 
        FROM players p
        JOIN player_rankings pr ON p.player_id = pr.player_id
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        WHERE rs.source_name = 'Underdog'
        ORDER BY pr.position_rank
        LIMIT 24
    """)
    
    top_players = cur.fetchall()
    
    # Insert draft picks for these players
    for i, (player_id,) in enumerate(top_players, 1):
        cur.execute("""
            INSERT INTO draft_picks (session_id, player_id, pick_number, round_number, pick_in_round, team_number, is_user_pick)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (session_id, player_id, i, ((i-1) // 12) + 1, ((i-1) % 12) + 1, ((i-1) % 12) + 1, False))
    engine.conn.commit()
    
    print(f"✅ Created test session: {session_id} (simulated 24 picks)")
    
    # Get recommendations
    recommendations = engine.calculate_recommendations(session_id)
    
    print(f"\n📊 Current Pick: #{recommendations['current_pick']}")
    
    print("\n🎯 Our Algorithm Recommendations:")
    for i, rec in enumerate(recommendations['our_recommendations'][:3], 1):
        print(f"{i}. {rec['name']} ({rec['position']}) - Score: {rec['total_score']}")
        print(f"   Our Rank: #{rec['our_position_rank']}")
        print(f"   {rec['reasoning']}")
    
    print("\n💎 ADP Value Picks (Available Past Their ADP):")
    for i, val in enumerate(recommendations['adp_value_picks'][:5], 1):
        print(f"{i}. {val['name']} ({val['position']}) - {val['value_reason']}")
    
    print("\n📈 Likely Next Picks (By ADP):")
    for i, likely in enumerate(recommendations['likely_next_picks'][:5], 1):
        print(f"{i}. {likely['name']} ({likely['position']}) - ADP #{likely['adp']} ({likely['likelihood']} likelihood)")
    
    # Clean up
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    engine.conn.commit()
    cur.close()
    
    print(f"\n✅ Test completed!")


if __name__ == "__main__":
    test_corrected_engine()
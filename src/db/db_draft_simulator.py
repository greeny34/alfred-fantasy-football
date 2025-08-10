#!/usr/bin/env python3
"""
Database-driven Fantasy Football Draft Simulator
Simulates realistic draft scenarios to test the optimizer
"""

import psycopg2
import os
import random
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
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

@dataclass
class DraftedPlayer:
    """Information about a drafted player"""
    player_id: int
    name: str
    position: str
    team: str
    adp: float
    our_rank: int

@dataclass
class AITeam:
    """AI team drafting behavior"""
    team_number: int
    strategy: str  # 'rb_heavy', 'wr_heavy', 'balanced', 'zero_rb', 'bpa'
    risk_tolerance: float  # 0.0 = conservative, 1.0 = risky
    current_roster: Dict[str, int]
    targets: List[str]  # Position targets
    
    def __post_init__(self):
        if not self.current_roster:
            self.current_roster = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}

class DatabaseDraftSimulator:
    def __init__(self):
        self.conn = get_db_connection()
        self.available_players = []
        self.ai_teams = {}
        self.roster_targets = {'QB': 2, 'RB': 4, 'WR': 5, 'TE': 2, 'K': 1, 'DST': 1}
        
    def load_available_players(self, session_id: int = None) -> List[DraftedPlayer]:
        """Load all available players with ADP and rankings"""
        cur = self.conn.cursor()
        
        # Get drafted players if session exists
        drafted_ids = set()
        if session_id:
            cur.execute("SELECT player_id FROM draft_picks WHERE session_id = %s", (session_id,))
            drafted_ids = {row[0] for row in cur.fetchall()}
        
        # Get all players with consensus ADP and our rankings
        cur.execute("""
            SELECT 
                p.player_id,
                p.name,
                p.position,
                p.team,
                COALESCE(ca.consensus_rank, 999) as adp,
                COALESCE(pr.position_rank, 999) as our_rank
            FROM players p
            LEFT JOIN consensus_adp ca ON p.player_id = ca.player_id
            LEFT JOIN (
                SELECT pr.player_id, pr.position_rank
                FROM player_rankings pr
                JOIN ranking_sources rs ON pr.source_id = rs.source_id
                WHERE rs.source_name = 'Mike_Clay_Position_Rankings'
            ) pr ON p.player_id = pr.player_id
            WHERE p.player_id NOT IN ({})
            AND (ca.consensus_rank IS NOT NULL OR pr.position_rank IS NOT NULL)
            ORDER BY COALESCE(ca.consensus_rank, 999), COALESCE(pr.position_rank, 999)
        """.format(','.join(str(pid) for pid in drafted_ids) if drafted_ids else '0'))
        
        players = []
        for row in cur.fetchall():
            players.append(DraftedPlayer(
                player_id=row[0],
                name=row[1],
                position=row[2],
                team=row[3],
                adp=float(row[4]) if row[4] != 999 else 999.0,
                our_rank=row[5] if row[5] != 999 else 999
            ))
        
        cur.close()
        self.available_players = players
        return players
    
    def create_ai_teams(self, team_count: int, user_position: int) -> Dict[int, AITeam]:
        """Create AI teams with different strategies"""
        strategies = ['rb_heavy', 'wr_heavy', 'balanced', 'zero_rb', 'bpa']
        ai_teams = {}
        
        for team_num in range(1, team_count + 1):
            if team_num == user_position:
                continue  # Skip user's team
            
            # Assign strategy based on draft position
            if team_num <= 3:  # Early picks
                strategy = random.choice(['rb_heavy', 'balanced', 'bpa'])
                risk_tolerance = 0.3  # Conservative
            elif team_num <= 7:  # Middle picks
                strategy = random.choice(['wr_heavy', 'balanced', 'zero_rb'])
                risk_tolerance = 0.6  # Moderate risk
            else:  # Late picks
                strategy = random.choice(['zero_rb', 'wr_heavy', 'bpa'])
                risk_tolerance = 0.8  # Higher risk for upside
            
            ai_teams[team_num] = AITeam(
                team_number=team_num,
                strategy=strategy,
                risk_tolerance=risk_tolerance,
                current_roster={'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0},
                targets=self._get_strategy_targets(strategy)
            )
        
        self.ai_teams = ai_teams
        return ai_teams
    
    def _get_strategy_targets(self, strategy: str) -> List[str]:
        """Get position targets for a strategy"""
        if strategy == 'rb_heavy':
            return ['RB', 'RB', 'RB', 'WR', 'WR', 'QB', 'TE']
        elif strategy == 'wr_heavy':
            return ['WR', 'WR', 'WR', 'RB', 'RB', 'QB', 'TE']
        elif strategy == 'zero_rb':
            return ['WR', 'WR', 'TE', 'QB', 'WR', 'RB', 'RB']
        elif strategy == 'balanced':
            return ['RB', 'WR', 'RB', 'WR', 'QB', 'TE', 'RB']
        else:  # bpa (best player available)
            return ['BPA'] * 7
    
    def simulate_ai_pick(self, team_num: int, round_num: int, available_players: List[DraftedPlayer]) -> Optional[DraftedPlayer]:
        """Simulate an AI team making a pick"""
        if team_num not in self.ai_teams:
            return None
        
        ai_team = self.ai_teams[team_num]
        
        # Get position need based on strategy and current roster
        target_position = self._get_ai_target_position(ai_team, round_num)
        
        # Find best available player for target position
        candidates = []
        
        if target_position == 'BPA':
            # Best player available regardless of position
            candidates = available_players[:20]  # Top 20 available
        else:
            # Position-specific targets
            position_players = [p for p in available_players if p.position == target_position]
            candidates = position_players[:10]  # Top 10 at position
            
            # If no good options at target position, fall back to BPA
            if not candidates and round_num <= 8:
                candidates = available_players[:15]
        
        if not candidates:
            return available_players[0] if available_players else None
        
        # Apply AI decision logic
        selected_player = self._ai_player_selection(ai_team, candidates, round_num)
        
        # Update AI team roster
        if selected_player:
            ai_team.current_roster[selected_player.position] += 1
        
        return selected_player
    
    def _get_ai_target_position(self, ai_team: AITeam, round_num: int) -> str:
        """Get the position the AI team should target this round"""
        strategy = ai_team.strategy
        roster = ai_team.current_roster
        
        # Late round positions
        if round_num >= 14:
            if roster['K'] == 0:
                return 'K'
            elif roster['DST'] == 0:
                return 'DST'
            else:
                return 'RB' if random.random() < 0.6 else 'WR'
        
        # QB targeting (usually rounds 6-10)
        if roster['QB'] == 0 and round_num >= 6 and round_num <= 10:
            if random.random() < 0.4:  # 40% chance to take QB
                return 'QB'
        
        # Strategy-based targeting
        if strategy == 'rb_heavy':
            if roster['RB'] < 2 and round_num <= 5:
                return 'RB'
            elif roster['WR'] < 2:
                return 'WR'
            elif roster['RB'] < 4:
                return 'RB'
        
        elif strategy == 'wr_heavy':
            if roster['WR'] < 3 and round_num <= 6:
                return 'WR'
            elif roster['RB'] < 2:
                return 'RB'
            elif roster['WR'] < 5:
                return 'WR'
        
        elif strategy == 'zero_rb':
            if round_num <= 4:
                if roster['WR'] < 3:
                    return 'WR'
                elif roster['TE'] == 0:
                    return 'TE'
            elif roster['RB'] < 2:
                return 'RB'
        
        elif strategy == 'balanced':
            # Alternate RB/WR early, fill needs
            if round_num <= 6:
                if roster['RB'] < roster['WR']:
                    return 'RB'
                elif roster['WR'] < roster['RB']:
                    return 'WR'
                else:
                    return 'RB' if round_num % 2 == 1 else 'WR'
        
        # Default to BPA
        return 'BPA'
    
    def _ai_player_selection(self, ai_team: AITeam, candidates: List[DraftedPlayer], round_num: int) -> DraftedPlayer:
        """AI logic for selecting from candidate players"""
        if not candidates:
            return None
        
        # Early rounds: prefer ADP-based selections
        if round_num <= 6:
            # Sort by ADP with some randomness
            weights = []
            for i, player in enumerate(candidates):
                # Better ADP (lower number) = higher weight
                adp_weight = max(1, 50 - player.adp) if player.adp < 999 else 1
                position_weight = 10 if len(candidates) > 5 else 5  # Position scarcity
                randomness = random.uniform(0.5, 1.5)  # Add some unpredictability
                
                weight = adp_weight * position_weight * randomness
                weights.append(weight)
            
            # Weighted random selection (favors better players but allows surprises)
            total_weight = sum(weights)
            if total_weight > 0:
                r = random.uniform(0, total_weight)
                cumulative = 0
                for i, weight in enumerate(weights):
                    cumulative += weight
                    if r <= cumulative:
                        return candidates[i]
        
        # Later rounds: more randomness, target upside
        else:
            # Favor players with decent rankings
            viable_players = [p for p in candidates[:15] if p.our_rank < 50 or p.adp < 100]
            if not viable_players:
                viable_players = candidates[:5]
            
            # Apply risk tolerance
            if ai_team.risk_tolerance > 0.7:
                # High risk: prefer later candidates (more upside)
                return random.choice(viable_players[2:7] if len(viable_players) > 7 else viable_players)
            else:
                # Conservative: prefer safer picks
                return random.choice(viable_players[:3] if len(viable_players) > 3 else viable_players)
        
        # Fallback
        return candidates[0]
    
    def simulate_draft_to_pick(self, session_id: int, target_pick: int) -> List[Dict]:
        """Simulate draft up to a specific pick number"""
        cur = self.conn.cursor()
        
        # Get session info
        cur.execute("""
            SELECT team_count, user_draft_position, current_pick
            FROM draft_sessions 
            WHERE session_id = %s
        """, (session_id,))
        
        session_info = cur.fetchone()
        if not session_info:
            raise ValueError(f"Session {session_id} not found")
        
        team_count, user_position, current_pick = session_info
        
        print(f"🏈 Simulating draft from pick {current_pick} to pick {target_pick}")
        print(f"📊 Teams: {team_count}, User Position: {user_position}")
        
        # Load available players and create AI teams
        self.load_available_players(session_id)
        self.create_ai_teams(team_count, user_position)
        
        simulated_picks = []
        
        # Simulate picks from current_pick to target_pick
        for pick_num in range(current_pick, target_pick + 1):
            round_num = ((pick_num - 1) // team_count) + 1
            pick_in_round = ((pick_num - 1) % team_count) + 1
            
            # Determine team number (snake draft)
            if round_num % 2 == 1:  # Odd rounds: 1, 2, 3, ...
                team_num = pick_in_round
            else:  # Even rounds: ..., 3, 2, 1
                team_num = team_count - pick_in_round + 1
            
            # Skip user picks
            if team_num == user_position:
                print(f"⏭️  Pick {pick_num}: User's turn (Team {team_num}) - SKIPPED")
                continue
            
            # AI makes pick
            selected_player = self.simulate_ai_pick(team_num, round_num, self.available_players)
            
            if selected_player:
                # Remove player from available list
                self.available_players = [p for p in self.available_players if p.player_id != selected_player.player_id]
                
                # Insert pick into database
                cur.execute("""
                    INSERT INTO draft_picks 
                    (session_id, player_id, pick_number, round_number, pick_in_round, team_number, is_user_pick)
                    VALUES (%s, %s, %s, %s, %s, %s, FALSE)
                """, (session_id, selected_player.player_id, pick_num, round_num, pick_in_round, team_num))
                
                pick_info = {
                    'pick_number': pick_num,
                    'round_number': round_num,
                    'team_number': team_num,
                    'player': {
                        'name': selected_player.name,
                        'position': selected_player.position,
                        'team': selected_player.team,
                        'adp': selected_player.adp
                    },
                    'ai_strategy': self.ai_teams[team_num].strategy
                }
                
                simulated_picks.append(pick_info)
                
                print(f"🤖 Pick {pick_num}: Team {team_num} ({self.ai_teams[team_num].strategy}) selects {selected_player.name} ({selected_player.position}, {selected_player.team}) - ADP: {selected_player.adp}")
            
            else:
                print(f"❌ Pick {pick_num}: No player available for Team {team_num}")
        
        # Update current pick in session
        cur.execute("""
            UPDATE draft_sessions 
            SET current_pick = %s 
            WHERE session_id = %s
        """, (target_pick + 1, session_id))
        
        self.conn.commit()
        cur.close()
        
        print(f"✅ Simulation complete! Generated {len(simulated_picks)} picks")
        return simulated_picks
    
    def simulate_full_draft(self, session_id: int) -> List[Dict]:
        """Simulate an entire draft"""
        return self.simulate_draft_to_pick(session_id, 160)  # 16 rounds * 10 teams
    
    def get_simulation_summary(self, session_id: int) -> Dict:
        """Get summary of simulated draft"""
        cur = self.conn.cursor()
        
        # Get all picks with AI strategy info
        cur.execute("""
            SELECT 
                dp.pick_number,
                dp.round_number,
                dp.team_number,
                dp.is_user_pick,
                p.name,
                p.position,
                p.team
            FROM draft_picks dp
            JOIN players p ON dp.player_id = p.player_id
            WHERE dp.session_id = %s
            ORDER BY dp.pick_number
        """, (session_id,))
        
        picks = cur.fetchall()
        
        # Analyze draft by team strategy
        team_summaries = {}
        for pick_num, round_num, team_num, is_user, name, position, team in picks:
            if team_num not in team_summaries:
                if not is_user and team_num in self.ai_teams:
                    strategy = self.ai_teams[team_num].strategy
                else:
                    strategy = 'user'
                team_summaries[team_num] = {
                    'strategy': strategy,
                    'picks': [],
                    'roster': {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'DST': 0}
                }
            
            team_summaries[team_num]['picks'].append({
                'pick': pick_num,
                'round': round_num,
                'player': name,
                'position': position,
                'team': team
            })
            team_summaries[team_num]['roster'][position] += 1
        
        cur.close()
        return {
            'total_picks': len(picks),
            'teams': team_summaries,
            'available_players': len(self.available_players)
        }


def test_simulator():
    """Test the draft simulator"""
    print("🧪 Testing Database Draft Simulator...\n")
    
    simulator = DatabaseDraftSimulator()
    
    # Create test session
    cur = simulator.conn.cursor()
    cur.execute("""
        INSERT INTO draft_sessions (session_name, team_count, user_draft_position, current_pick)
        VALUES ('Simulation Test', 10, 6, 1)
        RETURNING session_id
    """)
    session_id = cur.fetchone()[0]
    simulator.conn.commit()
    
    print(f"📊 Created test session: {session_id}")
    
    # Simulate first 25 picks
    picks = simulator.simulate_draft_to_pick(session_id, 25)
    
    # Get summary
    summary = simulator.get_simulation_summary(session_id)
    print(f"\n📈 Draft Summary:")
    print(f"   Total picks simulated: {summary['total_picks']}")
    print(f"   Teams with picks: {len(summary['teams'])}")
    print(f"   Available players remaining: {summary['available_players']}")
    
    # Show team strategies
    print(f"\n🤖 AI Team Strategies:")
    for team_num, team_info in summary['teams'].items():
        if team_info['strategy'] != 'user':
            picks_summary = [f"{p['player']} ({p['position']})" for p in team_info['picks'][:3]]
            print(f"   Team {team_num} ({team_info['strategy']}): {', '.join(picks_summary)}")
    
    # Clean up
    cur.execute("DELETE FROM draft_picks WHERE session_id = %s", (session_id,))
    cur.execute("DELETE FROM draft_sessions WHERE session_id = %s", (session_id,))
    simulator.conn.commit()
    cur.close()
    
    print("\n✅ Simulation test complete!")


if __name__ == "__main__":
    test_simulator()
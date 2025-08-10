import os
import time
import random
from dotenv import load_dotenv
from espn_api.football import League
from datetime import datetime

class DraftSimulator:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        
        # Draft state
        self.teams = 10
        self.my_team_id = 0  # Jeff's Scary Team
        self.drafted_players = set()
        self.team_rosters = {i: [] for i in range(self.teams)}
        self.available_players = []
        self.current_pick = 0
        
        # Load player pool
        self.load_player_pool()
        
    def load_player_pool(self):
        """Load available players from ESPN API"""
        try:
            players = self.league.free_agents(size=300)
            self.available_players = [{
                'name': player.name,
                'position': player.position,
                'projected_points': getattr(player, 'projected_total_points', 0),
                'adp': self.estimate_adp(player.position, getattr(player, 'projected_total_points', 0))
            } for player in players]
            
            # Sort by projected points for better draft simulation
            self.available_players.sort(key=lambda x: x['projected_points'], reverse=True)
            print(f"✅ Loaded {len(self.available_players)} players for simulation")
            
        except Exception as e:
            print(f"Error loading players: {e}")
            self.available_players = []
    
    def estimate_adp(self, position, projected_points):
        """Estimate Average Draft Position based on position and points"""
        position_multipliers = {
            'QB': 0.8,  # QBs tend to go later
            'RB': 1.2,  # RBs go early
            'WR': 1.1,  # WRs go early
            'TE': 0.9,  # TEs go mid-late
            'K': 0.3,   # Kickers go very late
            'D/ST': 0.3 # Defense goes very late
        }
        
        multiplier = position_multipliers.get(position, 1.0)
        base_adp = max(1, 200 - (projected_points * multiplier * 0.5))
        return base_adp + random.uniform(-20, 20)  # Add some randomness
    
    def get_draft_position(self, pick_number):
        """Calculate draft position using snake draft"""
        round_num = (pick_number // self.teams) + 1
        
        if round_num % 2 == 1:  # Odd rounds: 1,2,3...10
            position = (pick_number % self.teams)
        else:  # Even rounds: 9,8,7...0 (reverse)
            position = self.teams - 1 - (pick_number % self.teams)
        
        return position, round_num
    
    def analyze_team_needs(self, team_id):
        """Analyze what positions a team needs"""
        roster = self.team_rosters[team_id]
        position_counts = {}
        
        for player in roster:
            pos = player['position']
            position_counts[pos] = position_counts.get(pos, 0) + 1
        
        # Position priorities by round
        round_num = (len(roster) // self.teams) + 1
        
        if round_num <= 4:
            # Early rounds: prioritize skill positions
            needs = ['RB', 'WR', 'RB', 'WR', 'QB']
        elif round_num <= 8:
            # Mid rounds: fill core positions
            needs = ['QB', 'TE', 'RB', 'WR']
        else:
            # Late rounds: depth and specials
            needs = ['K', 'D/ST', 'RB', 'WR', 'QB']
        
        # Filter needs based on what team already has
        filtered_needs = []
        for need in needs:
            current_count = position_counts.get(need, 0)
            max_needed = 3 if need in ['RB', 'WR'] else (2 if need == 'QB' else 1)
            
            if current_count < max_needed:
                filtered_needs.append(need)
        
        return filtered_needs[:3]  # Top 3 needs
    
    def simulate_pick(self, team_id):
        """Simulate a realistic pick for a team"""
        if not self.available_players:
            return None
        
        needs = self.analyze_team_needs(team_id)
        
        # Create candidate list based on needs and ADP
        candidates = []
        
        # Look for players at needed positions
        for need in needs:
            position_players = [p for p in self.available_players[:50] if p['position'] == need]
            candidates.extend(position_players[:3])  # Top 3 at each needed position
        
        # Add some best available regardless of position
        candidates.extend(self.available_players[:10])
        
        # Remove duplicates
        seen = set()
        unique_candidates = []
        for player in candidates:
            if player['name'] not in seen:
                seen.add(player['name'])
                unique_candidates.append(player)
        
        if not unique_candidates:
            return self.available_players[0] if self.available_players else None
        
        # Weight selection by projected points (better players more likely)
        weights = [max(1, p['projected_points']) for p in unique_candidates]
        selected = random.choices(unique_candidates, weights=weights, k=1)[0]
        
        return selected
    
    def make_pick(self, player, team_id):
        """Execute a draft pick"""
        # Add to team roster
        self.team_rosters[team_id].append(player)
        
        # Remove from available players
        self.available_players = [p for p in self.available_players if p['name'] != player['name']]
        self.drafted_players.add(player['name'])
        
        return player
    
    def get_my_recommendations(self):
        """Get recommendations for my team"""
        if not self.available_players:
            return []
        
        needs = self.analyze_team_needs(self.my_team_id)
        recommendations = []
        
        # Best at each needed position
        for need in needs:
            position_players = [p for p in self.available_players if p['position'] == need]
            if position_players:
                best = max(position_players, key=lambda x: x['projected_points'])
                recommendations.append({
                    'player': best,
                    'reason': f"Best {need} available (team need)"
                })
        
        # Best overall
        if self.available_players:
            best_overall = max(self.available_players, key=lambda x: x['projected_points'])
            if not any(rec['player']['name'] == best_overall['name'] for rec in recommendations):
                recommendations.append({
                    'player': best_overall,
                    'reason': "Best player available"
                })
        
        return recommendations[:5]
    
    def display_status(self):
        """Display current draft status"""
        position, round_num = self.get_draft_position(self.current_pick)
        is_my_turn = position == self.my_team_id
        team_name = self.league.teams[position].team_name
        
        print(f"\n{'='*60}")
        print(f"🎯 PICK #{self.current_pick + 1} - ROUND {round_num}")
        
        if is_my_turn:
            print(f"🚨 YOUR TURN! ({team_name})")
        else:
            print(f"⏳ {team_name}'s turn")
        
        # Show recent picks
        recent_picks = []
        for team_id, roster in self.team_rosters.items():
            if roster:
                last_pick = roster[-1]
                team_name = self.league.teams[team_id].team_name
                recent_picks.append(f"{team_name}: {last_pick['name']} ({last_pick['position']})")
        
        if recent_picks:
            print(f"\n📝 Recent picks:")
            for pick in recent_picks[-3:]:
                print(f"   {pick}")
        
        # Show my team
        my_roster = self.team_rosters[self.my_team_id]
        if my_roster:
            print(f"\n👤 Your team ({len(my_roster)} picks):")
            by_pos = {}
            for player in my_roster:
                pos = player['position']
                if pos not in by_pos:
                    by_pos[pos] = []
                by_pos[pos].append(player['name'])
            
            for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
                if pos in by_pos:
                    print(f"   {pos}: {', '.join(by_pos[pos])}")
        
        # Show recommendations
        if is_my_turn:
            print(f"\n💡 RECOMMENDATIONS:")
            recommendations = self.get_my_recommendations()
            
            for i, rec in enumerate(recommendations, 1):
                player = rec['player']
                print(f"   {i}. {player['name']} ({player['position']}) - {rec['reason']}")
                print(f"      Projected: {player['projected_points']:.1f} pts")
        
        return is_my_turn
    
    def run_simulation(self, rounds=5, auto_pick_for_me=True):
        """Run draft simulation"""
        print("🏈 FF Draft Vibe - Live Draft Simulation")
        print("=" * 50)
        print("This simulates a real draft with team needs analysis")
        print(f"Your team: {self.league.teams[self.my_team_id].team_name}")
        print()
        
        total_picks = rounds * self.teams
        
        try:
            while self.current_pick < total_picks and self.available_players:
                position, round_num = self.get_draft_position(self.current_pick)
                is_my_turn = self.display_status()
                
                if is_my_turn:
                    if auto_pick_for_me:
                        # Auto-pick best recommendation
                        recommendations = self.get_my_recommendations()
                        if recommendations:
                            selected = recommendations[0]['player']
                            print(f"\n🎯 Auto-selecting: {selected['name']} ({selected['position']})")
                        else:
                            selected = self.available_players[0] if self.available_players else None
                    else:
                        # Wait for user input
                        input("\nPress Enter to make your pick...")
                        recommendations = self.get_my_recommendations()
                        selected = recommendations[0]['player'] if recommendations else None
                else:
                    # Simulate other team's pick
                    selected = self.simulate_pick(position)
                
                if selected:
                    self.make_pick(selected, position)
                    team_name = self.league.teams[position].team_name
                    print(f"✅ DRAFTED: {team_name} selects {selected['name']} ({selected['position']})")
                
                self.current_pick += 1
                
                # Pause between picks
                time.sleep(2 if is_my_turn else 1)
                
        except KeyboardInterrupt:
            print("\n👋 Simulation stopped")
        
        print(f"\n🎉 Draft simulation complete!")
        print(f"Your final team:")
        for player in self.team_rosters[self.my_team_id]:
            print(f"   {player['name']} ({player['position']}) - {player['projected_points']:.1f} pts")

def main():
    simulator = DraftSimulator()
    
    if not simulator.available_players:
        print("❌ Could not load player data")
        return
    
    print("Choose simulation mode:")
    print("1. Auto-draft (fast simulation)")
    print("2. Manual picks (you choose)")
    
    try:
        mode = input("Enter choice (1 or 2): ").strip()
        auto_mode = mode != "2"
        
        simulator.run_simulation(rounds=5, auto_pick_for_me=auto_mode)
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environment
        print("Running auto-simulation...")
        simulator.run_simulation(rounds=5, auto_pick_for_me=True)

if __name__ == "__main__":
    main()
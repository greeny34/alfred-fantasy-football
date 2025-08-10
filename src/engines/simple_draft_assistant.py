import os
import time
from datetime import datetime
from dotenv import load_dotenv
from espn_api.football import League

class SimpleDraftAssistant:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.drafted_players = set()
        self.round_num = 1
        self.pick_num = 1
        
    def get_available_players(self):
        """Get currently available players from ESPN API"""
        try:
            available = self.league.free_agents(size=200)
            return [{
                'name': player.name,
                'position': player.position,
                'projected_points': getattr(player, 'projected_total_points', 0),
                'percent_owned': getattr(player, 'percent_owned', 0),
                'avg_points': getattr(player, 'avg_points', 0)
            } for player in available if player.name not in self.drafted_players]
        except Exception as e:
            print(f"Error getting available players: {e}")
            return []
    
    def analyze_team_needs(self):
        """Analyze what positions you still need based on standard roster"""
        # Standard roster needs
        needs = ['QB', 'RB', 'RB', 'WR', 'WR', 'TE', 'FLEX', 'K', 'D/ST']
        
        # Early rounds focus on skill positions
        if self.round_num <= 6:
            return ['RB', 'WR', 'QB', 'TE']
        elif self.round_num <= 10:
            return ['RB', 'WR', 'QB', 'TE', 'FLEX']
        else:
            return ['K', 'D/ST', 'QB', 'RB', 'WR', 'TE']
    
    def get_tier_rankings(self, available_players):
        """Create simple tier rankings based on projected points"""
        if not available_players:
            return {}
        
        # Sort by projected points
        sorted_players = sorted(available_players, key=lambda x: x['projected_points'], reverse=True)
        
        tiers = {}
        positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']
        
        for pos in positions:
            pos_players = [p for p in sorted_players if p['position'] == pos]
            tiers[pos] = pos_players[:15]  # Top 15 at each position
        
        return tiers
    
    def get_recommendations(self):
        """Get smart player recommendations"""
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs()
        tiers = self.get_tier_rankings(available_players)
        
        if not available_players:
            return []
        
        recommendations = []
        
        # Strategy based on draft round
        if self.round_num <= 3:
            # Early rounds: Best RB/WR available
            focus_positions = ['RB', 'WR']
        elif self.round_num <= 6:
            # Mid rounds: Fill QB, TE, more RB/WR
            focus_positions = ['QB', 'RB', 'WR', 'TE']
        elif self.round_num <= 12:
            # Late rounds: Depth and sleepers
            focus_positions = ['RB', 'WR', 'QB', 'TE']
        else:
            # Final rounds: K, D/ST, handcuffs
            focus_positions = ['K', 'D/ST', 'RB', 'WR']
        
        # Get best available at each focus position
        for pos in focus_positions:
            if pos in tiers and tiers[pos]:
                best_at_pos = tiers[pos][0]
                recommendations.append({
                    'player': best_at_pos,
                    'reason': f"Best {pos} available",
                    'tier': 1
                })
        
        # Add overall best available
        all_sorted = sorted(available_players, key=lambda x: x['projected_points'], reverse=True)
        if all_sorted:
            best_overall = all_sorted[0]
            if not any(rec['player']['name'] == best_overall['name'] for rec in recommendations):
                recommendations.append({
                    'player': best_overall,
                    'reason': "Highest projected points",
                    'tier': 1
                })
        
        # Add value picks (high projected points, low ownership)
        value_picks = [p for p in available_players if p['percent_owned'] < 50 and p['projected_points'] > 100]
        if value_picks:
            value_sorted = sorted(value_picks, key=lambda x: x['projected_points'], reverse=True)
            if value_sorted and not any(rec['player']['name'] == value_sorted[0]['name'] for rec in recommendations):
                recommendations.append({
                    'player': value_sorted[0],
                    'reason': f"Value pick ({value_sorted[0]['percent_owned']:.0f}% owned)",
                    'tier': 2
                })
        
        return recommendations[:6]  # Top 6 recommendations
    
    def add_drafted_player(self, player_name):
        """Add a player to the drafted list"""
        self.drafted_players.add(player_name)
        print(f"✅ Added {player_name} to drafted players")
    
    def advance_pick(self):
        """Advance to next pick"""
        self.pick_num += 1
        if self.pick_num > 10:  # Assuming 10 team league
            self.pick_num = 1
            self.round_num += 1
        print(f"📊 Now at Round {self.round_num}, Pick {self.pick_num}")
    
    def display_recommendations(self):
        """Display current recommendations"""
        print(f"\n{'='*60}")
        print(f"🎯 ROUND {self.round_num} - PICK {self.pick_num}")
        print(f"📋 Drafted Players: {len(self.drafted_players)}")
        
        recommendations = self.get_recommendations()
        
        print(f"\n💡 TOP RECOMMENDATIONS:")
        if not recommendations:
            print("   No recommendations available")
            return
        
        for i, rec in enumerate(recommendations, 1):
            player = rec['player']
            tier_emoji = "🔥" if rec['tier'] == 1 else "💎"
            print(f"   {tier_emoji} {i}. {player['name']} ({player['position']}) - {rec['reason']}")
            print(f"      Projected: {player['projected_points']:.1f} pts | Owned: {player['percent_owned']:.0f}%")
        
        print(f"\n🎲 Quick position breakdown:")
        available = self.get_available_players()
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_players = [p for p in available if p['position'] == pos]
            if pos_players:
                best = max(pos_players, key=lambda x: x['projected_points'])
                print(f"   {pos}: {best['name']} ({best['projected_points']:.1f} pts)")
    
    def interactive_mode(self):
        """Interactive draft assistant"""
        print("🏈 FF Draft Vibe - Simple Mock Draft Assistant")
        print("=" * 60)
        print("Commands:")
        print("  - Press Enter: Get recommendations for current pick")
        print("  - 'draft [player name]': Mark player as drafted")
        print("  - 'next': Advance to next pick")
        print("  - 'round [number]': Jump to specific round")
        print("  - 'quit': Exit")
        print()
        
        while True:
            try:
                self.display_recommendations()
                
                command = input(f"\n🎯 Round {self.round_num}, Pick {self.pick_num} > ").strip()
                
                if command.lower() == 'quit':
                    break
                elif command.lower() == 'next':
                    self.advance_pick()
                elif command.lower() == '' or command.lower() == 'rec':
                    continue  # Just refresh recommendations
                elif command.startswith('draft '):
                    player_name = command[6:].strip()
                    self.add_drafted_player(player_name)
                    self.advance_pick()
                elif command.startswith('round '):
                    try:
                        round_num = int(command[6:].strip())
                        if 1 <= round_num <= 15:
                            self.round_num = round_num
                            print(f"📊 Jumped to Round {round_num}")
                        else:
                            print("Round must be between 1-15")
                    except ValueError:
                        print("Invalid round number")
                else:
                    print("Unknown command. Try 'draft [player]', 'next', or just press Enter")
                    
            except KeyboardInterrupt:
                break
        
        print("\n👋 Thanks for using FF Draft Vibe!")

def main():
    assistant = SimpleDraftAssistant()
    assistant.interactive_mode()

if __name__ == "__main__":
    main()
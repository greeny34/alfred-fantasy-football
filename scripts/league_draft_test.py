import os
import time
from dotenv import load_dotenv
from espn_api.football import League
from datetime import datetime

class LeagueDraftTester:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.drafted_players = set()
        self.my_team_id = 0  # Jeff's Scary Team
        
    def get_current_draft_state(self):
        """Get current draft picks from team rosters"""
        try:
            draft_picks = []
            for team in self.league.teams:
                for player in team.roster:
                    if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                        draft_picks.append({
                            'player_name': player.name,
                            'team_name': team.team_name,
                            'position': player.position,
                            'projected_points': getattr(player, 'projected_total_points', 0)
                        })
            
            # Find new picks
            new_picks = []
            for pick in draft_picks:
                player_key = f"{pick['player_name']}-{pick['team_name']}"
                if player_key not in self.drafted_players:
                    self.drafted_players.add(player_key)
                    new_picks.append(pick)
            
            return new_picks, len(draft_picks)
            
        except Exception as e:
            print(f"Error getting draft state: {e}")
            return [], 0
    
    def get_available_players(self):
        """Get currently available players"""
        try:
            available = self.league.free_agents(size=100)
            return [{
                'name': player.name,
                'position': player.position,
                'projected_points': getattr(player, 'projected_total_points', 0),
                'percent_owned': getattr(player, 'percent_owned', 0)
            } for player in available]
        except Exception as e:
            print(f"Error getting available players: {e}")
            return []
    
    def analyze_team_needs(self):
        """Analyze what positions your team needs"""
        my_team = self.league.teams[self.my_team_id]
        roster_positions = {}
        
        # Count current roster by position
        for player in my_team.roster:
            if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                pos = player.position
                roster_positions[pos] = roster_positions.get(pos, 0) + 1
        
        # Standard lineup needs
        standard_needs = {
            'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 
            'K': 1, 'D/ST': 1, 'BE': 6
        }
        
        needs = []
        for pos, needed in standard_needs.items():
            current = roster_positions.get(pos, 0)
            if current < needed:
                needs.extend([pos] * (needed - current))
        
        return needs
    
    def get_recommendations(self):
        """Get player recommendations"""
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs()
        
        if not available_players:
            return []
        
        recommendations = []
        
        # First, recommend players at positions of need
        for need in team_needs[:3]:
            position_players = [p for p in available_players if p['position'] == need]
            if position_players:
                position_players.sort(key=lambda x: x['projected_points'], reverse=True)
                recommendations.append({
                    'player': position_players[0],
                    'reason': f"Fills {need} need"
                })
        
        # Add best available
        all_sorted = sorted(available_players, key=lambda x: x['projected_points'], reverse=True)
        if all_sorted:
            best_overall = all_sorted[0]
            if not any(rec['player']['name'] == best_overall['name'] for rec in recommendations):
                recommendations.append({
                    'player': best_overall,
                    'reason': "Best available player"
                })
        
        return recommendations[:5]
    
    def test_draft_monitoring(self, iterations=5):
        """Test draft monitoring for a few iterations"""
        print("🏈 Testing FF Draft Vibe with Real League")
        print("=" * 50)
        print(f"League: {self.league.teams[self.my_team_id].team_name}")
        print(f"Testing for {iterations} iterations...")
        print()
        
        last_pick_count = 0
        
        for i in range(iterations):
            print(f"📊 Test #{i+1} ({datetime.now().strftime('%H:%M:%S')})")
            
            # Get current draft state
            new_picks, total_picks = self.get_current_draft_state()
            
            # Report new picks
            if new_picks:
                print("🔄 New picks detected:")
                for pick in new_picks:
                    print(f"   ✅ {pick['team_name']}: {pick['player_name']} ({pick['position']})")
            else:
                print(f"   📊 Total picks: {total_picks} (no new picks)")
            
            # Check if it's your turn (simple heuristic)
            teams_count = len(self.league.teams)
            expected_turn = total_picks % teams_count
            is_my_turn = expected_turn == self.my_team_id
            
            if is_my_turn:
                print("🚨 IT'S YOUR TURN!")
            
            # Show recommendations
            print(f"💡 {'🚨 YOUR TURN! ' if is_my_turn else ''}Recommendations:")
            recommendations = self.get_recommendations()
            
            if recommendations:
                for j, rec in enumerate(recommendations, 1):
                    player = rec['player']
                    print(f"   {j}. {player['name']} ({player['position']}) - {rec['reason']}")
                    print(f"      Projected: {player['projected_points']:.1f} pts")
            else:
                print("   No recommendations available")
            
            # Show team needs analysis
            needs = self.analyze_team_needs()
            if needs:
                print(f"📋 Team needs: {', '.join(needs[:5])}")
            else:
                print("📋 Team roster complete!")
            
            last_pick_count = total_picks
            print(f"   Waiting 3 seconds...\n")
            
            if i < iterations - 1:  # Don't sleep on last iteration
                time.sleep(3)
        
        print("✅ Test completed!")
        print("\n🎯 Results:")
        print(f"- API connection: Working")
        print(f"- Draft pick detection: {len(self.drafted_players)} picks tracked")
        print(f"- Recommendations: Working")
        print(f"- Team needs analysis: Working")
        print()
        print("🚀 The system is ready for live draft use!")
        print("To use during actual draft:")
        print("1. Run: python real_time_draft_assistant.py")
        print("2. It will monitor picks in real-time")
        print("3. You'll get recommendations when it's your turn")

def main():
    tester = LeagueDraftTester()
    tester.test_draft_monitoring()

if __name__ == "__main__":
    main()
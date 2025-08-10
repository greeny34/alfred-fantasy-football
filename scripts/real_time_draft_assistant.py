import os
import time
from dotenv import load_dotenv
from espn_api.football import League
from datetime import datetime

class RealTimeDraftAssistant:
    def __init__(self):
        load_dotenv()
        self.league = League(
            league_id=os.getenv('LEAGUE_ID'),
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.drafted_players = set()
        self.my_team_id = None
        self.current_pick = 0
        self.is_my_turn = False
        
    def initialize_draft(self):
        """Initialize draft state and find your team"""
        print("🏈 Initializing ESPN Draft Assistant...")
        
        # Get your team ID
        teams = self.league.teams
        print("\nTeams in your league:")
        for i, team in enumerate(teams):
            owners = getattr(team, 'owners', ['Unknown'])
            if isinstance(owners, list) and owners:
                owner_name = owners[0]
                if isinstance(owner_name, dict):
                    owner_name = owner_name.get('firstName', 'Unknown')
            else:
                owner_name = 'Unknown'
            print(f"{i+1}. {team.team_name} (Owner: {owner_name})")
        
        # For now, auto-select team 1 (Jeff's team) for testing
        print(f"\n🎯 Auto-selecting Team 1: {teams[0].team_name}")
        self.my_team_id = 0
        my_team = teams[self.my_team_id]
        print(f"✅ You are: {my_team.team_name}")
        return my_team
        
    def get_current_draft_state(self):
        """Get current draft picks and determine whose turn it is"""
        try:
            # Get draft picks from the league
            draft_picks = []
            for team in self.league.teams:
                for player in team.roster:
                    if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                        draft_picks.append({
                            'player_name': player.name,
                            'team_name': team.team_name,
                            'position': player.position
                        })
            
            # Update drafted players set
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
            available = self.league.free_agents(size=200)  # Get top 200 available
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
        """Analyze what positions you still need"""
        my_team = self.league.teams[self.my_team_id]
        roster_positions = {}
        
        # Count current roster by position
        for player in my_team.roster:
            pos = player.position
            roster_positions[pos] = roster_positions.get(pos, 0) + 1
        
        # Standard lineup needs (adjust for your league)
        standard_needs = {
            'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 
            'K': 1, 'D/ST': 1, 'BE': 6  # bench spots
        }
        
        needs = []
        for pos, needed in standard_needs.items():
            current = roster_positions.get(pos, 0)
            if current < needed:
                needs.extend([pos] * (needed - current))
        
        return needs
    
    def get_recommendations(self):
        """Get player recommendations based on available players and team needs"""
        available_players = self.get_available_players()
        team_needs = self.analyze_team_needs()
        
        if not available_players:
            return []
        
        # Simple recommendation: best available at needed positions
        recommendations = []
        
        # First, recommend players at positions of need
        for need in team_needs[:3]:  # Top 3 needs
            position_players = [p for p in available_players if p['position'] == need]
            if position_players:
                # Sort by projected points (or percent owned as proxy for ranking)
                position_players.sort(key=lambda x: x['projected_points'], reverse=True)
                recommendations.append({
                    'player': position_players[0],
                    'reason': f"Fills {need} need"
                })
        
        # Add best available regardless of position
        all_sorted = sorted(available_players, key=lambda x: x['projected_points'], reverse=True)
        if all_sorted:
            recommendations.append({
                'player': all_sorted[0],
                'reason': "Best available player"
            })
        
        return recommendations[:5]  # Top 5 recommendations
    
    def monitor_draft(self):
        """Main loop to monitor draft and provide recommendations"""
        print("\n🎯 Starting draft monitoring...")
        print("Press Ctrl+C to stop when draft is done\n")
        
        last_pick_count = 0
        iteration = 0
        
        try:
            while True:
                iteration += 1
                print(f"📊 Check #{iteration} ({datetime.now().strftime('%H:%M:%S')})")
                
                # Get current draft state
                new_picks, total_picks = self.get_current_draft_state()
                print(f"   Total picks so far: {total_picks}")
                
                # Check if new picks were made
                if new_picks:
                    print(f"🔄 New picks detected:")
                    for pick in new_picks:
                        print(f"   ✅ {pick['team_name']} drafted {pick['player_name']} ({pick['position']})")
                else:
                    print("   No new picks since last check")
                
                # Check if it might be your turn (simple heuristic)
                teams_count = len(self.league.teams)
                expected_pick_position = total_picks % teams_count
                self.is_my_turn = (expected_pick_position == self.my_team_id)
                
                print(f"💡 Recommendations (Your turn: {self.is_my_turn}):")
                recommendations = self.get_recommendations()
                
                for i, rec in enumerate(recommendations, 1):
                    player = rec['player']
                    print(f"   {i}. {player['name']} ({player['position']}) - {rec['reason']}")
                    print(f"      Projected: {player['projected_points']:.1f} pts")
                
                if not recommendations:
                    print("   No recommendations available")
                
                last_pick_count = total_picks
                print(f"   Waiting 5 seconds...\n")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n👋 Draft monitoring stopped")
            print("🏁 Thanks for using FF Draft Vibe!")

def main():
    assistant = RealTimeDraftAssistant()
    assistant.initialize_draft()
    assistant.monitor_draft()

if __name__ == "__main__":
    main()
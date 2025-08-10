import os
import time
from dotenv import load_dotenv
from espn_api.football import League
from datetime import datetime

class MockDraftAPIAssistant:
    def __init__(self, league_id=None):
        load_dotenv()
        
        # Use provided mock draft league ID or fall back to env
        self.league_id = league_id or os.getenv('LEAGUE_ID')
        
        self.league = League(
            league_id=self.league_id,
            year=int(os.getenv('YEAR')),
            espn_s2=os.getenv('ESPN_S2'),
            swid=os.getenv('SWID')
        )
        self.drafted_players = set()
        self.my_team_id = None
        self.last_draft_check = 0
        
    def test_league_access(self):
        """Test what we can access from this league"""
        print(f"🔍 Testing ESPN API access for league {self.league_id}")
        print("=" * 60)
        
        try:
            print(f"League name: {getattr(self.league, 'name', 'Unknown')}")
            print(f"Number of teams: {len(self.league.teams)}")
            print(f"Current week: {getattr(self.league, 'current_week', 'Unknown')}")
            
            # Check if this is a draft-enabled league
            print(f"Draft complete: {getattr(self.league, 'draft_complete', 'Unknown')}")
            
            # List teams
            print(f"\n👥 Teams:")
            for i, team in enumerate(self.league.teams):
                owner_info = "Unknown"
                if hasattr(team, 'owners') and team.owners:
                    owner = team.owners[0]
                    if isinstance(owner, dict):
                        owner_info = owner.get('firstName', 'Unknown')
                print(f"   {i+1}. {team.team_name} (Owner: {owner_info})")
                print(f"      Roster size: {len(team.roster)}")
                
                # Check for draft picks in roster
                if team.roster:
                    draft_picks = []
                    for player in team.roster:
                        if hasattr(player, 'acquisition_type'):
                            if player.acquisition_type == 'DRAFT':
                                draft_picks.append(f"{player.name} ({player.position})")
                    
                    if draft_picks:
                        print(f"      Draft picks: {', '.join(draft_picks[:3])}{'...' if len(draft_picks) > 3 else ''}")
            
            # Try to access draft data directly
            print(f"\n📊 Draft Data Access:")
            try:
                if hasattr(self.league, 'draft') and self.league.draft:
                    print(f"✅ Draft object found: {len(self.league.draft)} picks")
                    
                    # Show first few picks
                    for i, pick in enumerate(self.league.draft[:5]):
                        print(f"   Pick {i+1}: {pick}")
                else:
                    print("❌ No draft object found")
            except Exception as e:
                print(f"❌ Error accessing draft: {e}")
            
            # Check for any players drafted across all teams
            total_drafted = 0
            all_drafted_players = []
            
            for team in self.league.teams:
                for player in team.roster:
                    if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                        total_drafted += 1
                        all_drafted_players.append(f"{player.name} ({player.position}) -> {team.team_name}")
            
            print(f"\n📋 Total drafted players found: {total_drafted}")
            if all_drafted_players:
                print("Recent draft picks:")
                for pick in all_drafted_players[-5:]:  # Show last 5
                    print(f"   {pick}")
            
            return total_drafted > 0
            
        except Exception as e:
            print(f"❌ Error testing league access: {e}")
            return False
    
    def get_mock_draft_league_id(self):
        """Get the league ID from user for mock draft"""
        print("🎯 Mock Draft Setup")
        print("=" * 30)
        print("1. Go to ESPN Fantasy Football Mock Draft Lobby")
        print("2. Join a mock draft")
        print("3. Once in the draft, look at the URL")
        print("4. Find the league ID in the URL (format: leagueId=XXXXXXX)")
        print()
        
        while True:
            mock_league_id = input("Enter the mock draft league ID: ").strip()
            if mock_league_id.isdigit():
                return mock_league_id
            else:
                print("Please enter a valid numeric league ID")
    
    def monitor_mock_draft(self):
        """Monitor the mock draft for real-time picks"""
        print("\n🎯 Starting mock draft monitoring...")
        print("Press Ctrl+C to stop\n")
        
        # Test initial access
        has_draft_data = self.test_league_access()
        
        if not has_draft_data:
            print("\n⚠️  No draft data found yet. This could mean:")
            print("   - Draft hasn't started")
            print("   - API can't access this mock draft")
            print("   - Wrong league ID")
            print("\nContinuing to monitor for changes...")
        
        # Ask which team is yours
        print(f"\nWhich team are you in this mock draft?")
        for i, team in enumerate(self.league.teams):
            print(f"{i+1}. {team.team_name}")
        
        while True:
            try:
                choice = int(input("Enter team number: "))
                if 1 <= choice <= len(self.league.teams):
                    self.my_team_id = choice - 1
                    break
                else:
                    print(f"Please enter a number between 1-{len(self.league.teams)}")
            except ValueError:
                print("Please enter a valid number")
        
        my_team = self.league.teams[self.my_team_id]
        print(f"✅ Monitoring {my_team.team_name}")
        
        # Main monitoring loop
        iteration = 0
        last_total_picks = 0
        
        try:
            while True:
                iteration += 1
                print(f"\n📊 Check #{iteration} ({datetime.now().strftime('%H:%M:%S')})")
                
                # Count total picks across all teams
                current_picks = []
                total_picks = 0
                
                for team in self.league.teams:
                    for player in team.roster:
                        if hasattr(player, 'acquisition_type') and player.acquisition_type == 'DRAFT':
                            total_picks += 1
                            pick_info = f"{player.name} ({player.position}) -> {team.team_name}"
                            if pick_info not in self.drafted_players:
                                current_picks.append(pick_info)
                                self.drafted_players.add(pick_info)
                
                # Report changes
                if current_picks:
                    print("🔄 New picks detected:")
                    for pick in current_picks:
                        print(f"   ✅ {pick}")
                elif total_picks > last_total_picks:
                    print(f"   📈 Total picks: {total_picks} (up from {last_total_picks})")
                else:
                    print(f"   📊 Total picks: {total_picks} (no change)")
                
                # Check if it's your turn (simple heuristic)
                teams_count = len(self.league.teams)
                expected_turn = total_picks % teams_count
                is_my_turn = expected_turn == self.my_team_id
                
                if is_my_turn:
                    print("🚨 IT MIGHT BE YOUR TURN!")
                
                # Show recommendations (using available players)
                try:
                    available = self.league.free_agents(size=50)
                    print(f"💡 Top recommendations:")
                    
                    for i, player in enumerate(available[:5], 1):
                        print(f"   {i}. {player.name} ({player.position}) - {getattr(player, 'projected_total_points', 0):.1f} pts")
                        
                except Exception as e:
                    print(f"   Error getting recommendations: {e}")
                
                last_total_picks = total_picks
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n👋 Mock draft monitoring stopped")

def main():
    print("🏈 ESPN Mock Draft API Assistant")
    print("=" * 40)
    
    # Option to use custom league ID
    use_custom = input("Use custom mock draft league ID? (y/n): ").lower().startswith('y')
    
    if use_custom:
        assistant = MockDraftAPIAssistant()
        mock_league_id = assistant.get_mock_draft_league_id()
        assistant = MockDraftAPIAssistant(league_id=mock_league_id)
    else:
        assistant = MockDraftAPIAssistant()
    
    assistant.monitor_mock_draft()

if __name__ == "__main__":
    main()
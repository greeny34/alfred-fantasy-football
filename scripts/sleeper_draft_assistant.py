import requests
import time
from datetime import datetime
import json

class SleeperDraftAssistant:
    def __init__(self):
        self.base_url = "https://api.sleeper.app/v1"
        self.mock_draft_url = "https://api.sleeper.app/mockdraft"
        self.drafted_players = set()
        self.draft_picks = []
        self.my_user_id = None
        self.draft_id = None
        self.league_id = None
        
    def find_user(self, username):
        """Find user ID by username"""
        try:
            url = f"{self.base_url}/user/{username}"
            response = requests.get(url)
            
            if response.status_code == 200:
                user_data = response.json()
                self.my_user_id = user_data.get('user_id')
                print(f"✅ Found user: {user_data.get('display_name')} (ID: {self.my_user_id})")
                return user_data
            else:
                print(f"❌ User not found: {username}")
                return None
                
        except Exception as e:
            print(f"Error finding user: {e}")
            return None
    
    def get_user_leagues(self, season=2025):
        """Get all leagues for a user"""
        if not self.my_user_id:
            print("❌ Need to find user first")
            return []
        
        try:
            url = f"{self.base_url}/user/{self.my_user_id}/leagues/nfl/{season}"
            response = requests.get(url)
            
            if response.status_code == 200:
                leagues = response.json()
                print(f"✅ Found {len(leagues)} leagues for 2025")
                
                for i, league in enumerate(leagues):
                    print(f"   {i+1}. {league.get('name', 'Unknown')} (ID: {league.get('league_id')})")
                    print(f"      Status: {league.get('status', 'Unknown')}")
                    print(f"      Draft ID: {league.get('draft_id', 'None')}")
                
                return leagues
            else:
                print(f"❌ Error getting leagues: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"Error getting leagues: {e}")
            return []
    
    def get_draft_info(self, draft_id):
        """Get detailed draft information"""
        try:
            url = f"{self.base_url}/draft/{draft_id}"
            response = requests.get(url)
            
            if response.status_code == 200:
                draft_data = response.json()
                print(f"✅ Draft Info:")
                print(f"   Status: {draft_data.get('status', 'Unknown')}")
                print(f"   Type: {draft_data.get('type', 'Unknown')}")
                print(f"   Rounds: {draft_data.get('settings', {}).get('rounds', 'Unknown')}")
                print(f"   Teams: {draft_data.get('settings', {}).get('teams', 'Unknown')}")
                print(f"   Started: {draft_data.get('start_time', 'Not started')}")
                
                return draft_data
            else:
                print(f"❌ Error getting draft info: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting draft info: {e}")
            return None
    
    def get_draft_picks(self, draft_id):
        """Get all current draft picks"""
        try:
            url = f"{self.base_url}/draft/{draft_id}/picks"
            response = requests.get(url)
            
            if response.status_code == 200:
                picks = response.json()
                print(f"✅ Found {len(picks)} draft picks")
                
                # Find new picks
                new_picks = []
                for pick in picks:
                    pick_key = f"{pick.get('player_id', '')}-{pick.get('picked_by', '')}"
                    if pick_key not in self.drafted_players:
                        self.drafted_players.add(pick_key)
                        new_picks.append(pick)
                
                return new_picks, len(picks)
            else:
                print(f"❌ Error getting draft picks: {response.status_code}")
                return [], 0
                
        except Exception as e:
            print(f"Error getting draft picks: {e}")
            return [], 0
    
    def get_player_info(self, player_id):
        """Get player information"""
        try:
            # Sleeper stores all players in a large JSON file
            # For now, we'll just return the player_id as name
            # In a full implementation, you'd load the players JSON
            return f"Player_{player_id}"
        except Exception as e:
            print(f"Error getting player info: {e}")
            return f"Unknown_{player_id}"
    
    def get_nfl_players(self):
        """Get all NFL players (this is a large file, ~10MB)"""
        try:
            url = f"{self.base_url}/players/nfl"
            print("📥 Downloading NFL players database (this may take a moment)...")
            response = requests.get(url)
            
            if response.status_code == 200:
                players = response.json()
                print(f"✅ Loaded {len(players)} NFL players")
                return players
            else:
                print(f"❌ Error getting players: {response.status_code}")
                return {}
                
        except Exception as e:
            print(f"Error getting players: {e}")
            return {}
    
    def explore_mock_draft_api(self):
        """Explore what's available at the mock draft endpoint"""
        try:
            print("🔍 Exploring Sleeper Mock Draft API...")
            
            # Try different mock draft endpoints
            endpoints_to_try = [
                "/mockdraft",
                "/mockdraft/lobby",
                "/mockdraft/active",
                "/v1/mockdraft",
                "/v1/draft/mock"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    if endpoint.startswith('/v1/'):
                        url = f"https://api.sleeper.app{endpoint}"
                    else:
                        url = f"https://api.sleeper.app{endpoint}"
                    
                    print(f"   Trying: {url}")
                    response = requests.get(url, timeout=5)
                    
                    if response.status_code == 200:
                        print(f"   ✅ Success: {response.status_code}")
                        data = response.json()
                        print(f"   📊 Response type: {type(data)}")
                        if isinstance(data, list):
                            print(f"   📋 Items: {len(data)}")
                        elif isinstance(data, dict):
                            print(f"   🔑 Keys: {list(data.keys())[:5]}...")
                    else:
                        print(f"   ❌ Failed: {response.status_code}")
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
            
        except Exception as e:
            print(f"Error exploring mock draft API: {e}")
    
    def monitor_draft(self, draft_id, rounds=5):
        """Monitor draft for new picks and provide recommendations"""
        print(f"\n🎯 Starting draft monitoring for draft {draft_id}")
        print("Press Ctrl+C to stop\n")
        
        iteration = 0
        last_pick_count = 0
        
        try:
            while iteration < rounds * 10:  # Limit iterations for testing
                iteration += 1
                print(f"📊 Check #{iteration} ({datetime.now().strftime('%H:%M:%S')})")
                
                # Get current picks
                new_picks, total_picks = self.get_draft_picks(draft_id)
                
                # Show new picks
                if new_picks:
                    print("🔄 New picks detected:")
                    for pick in new_picks:
                        player_name = self.get_player_info(pick.get('player_id', ''))
                        team_name = f"Team {pick.get('picked_by', 'Unknown')}"
                        round_num = pick.get('round', '?')
                        pick_num = pick.get('pick_no', '?')
                        
                        print(f"   ✅ Round {round_num}, Pick {pick_num}: {team_name} - {player_name}")
                else:
                    print(f"   📊 Total picks: {total_picks} (no new picks)")
                
                # Check if it's potentially your turn (basic heuristic)
                if total_picks != last_pick_count:
                    print("💡 Draft activity detected - this is where recommendations would appear")
                
                last_pick_count = total_picks
                print("   Waiting 5 seconds...\n")
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n👋 Draft monitoring stopped")
    
    def setup_draft_monitoring(self):
        """Interactive setup for draft monitoring"""
        print("🏈 Sleeper Draft Assistant Setup")
        print("=" * 40)
        
        # Get username
        username = input("Enter your Sleeper username: ").strip()
        if not username:
            print("❌ Username required")
            return
        
        # Find user
        user_data = self.find_user(username)
        if not user_data:
            return
        
        # Get leagues
        leagues = self.get_user_leagues()
        if not leagues:
            print("❌ No leagues found. Make sure you have joined leagues for 2025.")
            return
        
        # Select league
        if len(leagues) == 1:
            selected_league = leagues[0]
            print(f"✅ Auto-selected only league: {selected_league.get('name')}")
        else:
            try:
                choice = int(input(f"\nSelect league (1-{len(leagues)}): ")) - 1
                if 0 <= choice < len(leagues):
                    selected_league = leagues[choice]
                else:
                    print("❌ Invalid choice")
                    return
            except ValueError:
                print("❌ Please enter a number")
                return
        
        # Get draft info
        draft_id = selected_league.get('draft_id')
        if not draft_id:
            print("❌ No draft found for this league")
            return
        
        self.draft_id = draft_id
        self.league_id = selected_league.get('league_id')
        
        draft_info = self.get_draft_info(draft_id)
        if not draft_info:
            return
        
        # Check if draft is active
        draft_status = draft_info.get('status', '')
        if draft_status == 'complete':
            print("ℹ️  Draft is complete. Showing final results...")
        elif draft_status == 'drafting':
            print("🚨 Draft is LIVE!")
        else:
            print(f"ℹ️  Draft status: {draft_status}")
        
        # Start monitoring
        print(f"\n🎯 Ready to monitor draft!")
        proceed = input("Start monitoring? (y/n): ").lower().startswith('y')
        
        if proceed:
            self.monitor_draft(draft_id)
        else:
            print("👋 Setup complete. Run monitor_draft() when ready.")

def main():
    assistant = SleeperDraftAssistant()
    
    print("🏈 Sleeper Draft Assistant")
    print("=" * 30)
    print("Options:")
    print("1. Setup draft monitoring")
    print("2. Explore mock draft API")
    print("3. Load NFL players database")
    
    try:
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            assistant.setup_draft_monitoring()
        elif choice == "2":
            assistant.explore_mock_draft_api()
        elif choice == "3":
            players = assistant.get_nfl_players()
            if players:
                print(f"Sample players:")
                for i, (player_id, player_data) in enumerate(list(players.items())[:5]):
                    name = player_data.get('full_name', 'Unknown')
                    pos = player_data.get('position', 'Unknown')
                    team = player_data.get('team', 'Unknown')
                    print(f"   {name} ({pos}) - {team}")
        else:
            print("Invalid choice")
            
    except (EOFError, KeyboardInterrupt):
        # Handle non-interactive environment
        print("Running API exploration...")
        assistant.explore_mock_draft_api()

if __name__ == "__main__":
    main()
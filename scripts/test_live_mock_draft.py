import requests
import time
from datetime import datetime

def test_live_mock_draft():
    """Test connection to your specific mock draft"""
    draft_id = "1256093340819001344"  # From your URL
    
    print("🎯 Testing Your Live Mock Draft")
    print("=" * 40)
    print(f"Draft ID: {draft_id}")
    
    # Test draft info
    try:
        url = f"https://api.sleeper.app/v1/draft/{draft_id}"
        response = requests.get(url)
        
        print(f"\n📊 Draft Info:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            draft_data = response.json()
            
            print(f"✅ Connected to draft!")
            print(f"   Status: {draft_data.get('status', 'Unknown')}")
            print(f"   Type: {draft_data.get('type', 'Unknown')}")
            print(f"   Rounds: {draft_data.get('settings', {}).get('rounds', 'Unknown')}")
            print(f"   Teams: {draft_data.get('settings', {}).get('teams', 'Unknown')}")
            
            # Test getting picks
            picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
            picks_response = requests.get(picks_url)
            
            print(f"\n📋 Draft Picks:")
            print(f"Status: {picks_response.status_code}")
            
            if picks_response.status_code == 200:
                picks = picks_response.json()
                print(f"✅ Found {len(picks)} picks so far")
                
                # Show recent picks
                if picks:
                    print(f"\nRecent picks:")
                    for pick in picks[-5:]:  # Last 5 picks
                        round_num = pick.get('round', '?')
                        pick_num = pick.get('pick_no', '?')
                        player_id = pick.get('player_id', 'Unknown')
                        picked_by = pick.get('picked_by', 'Unknown')
                        
                        print(f"   Round {round_num}, Pick {pick_num}: Team {picked_by} - Player {player_id}")
                
                # Check if draft is live
                if draft_data.get('status') == 'drafting':
                    print(f"\n🚨 DRAFT IS LIVE! Perfect for real-time monitoring!")
                    return True
                else:
                    print(f"\n📊 Draft status: {draft_data.get('status')}")
                    print(f"   Still good for testing pick detection")
                    return True
            else:
                print(f"❌ Error getting picks: {picks_response.status_code}")
                return False
                
        else:
            print(f"❌ Error connecting to draft: {response.status_code}")
            if response.status_code == 404:
                print("   Draft might be private or ID incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def monitor_live_draft():
    """Monitor your mock draft in real-time"""
    draft_id = "1256093340819001344"
    
    print(f"\n🎯 LIVE MONITORING: Your Mock Draft")
    print("=" * 50)
    print("Watching for new picks every 2 seconds...")
    print("This will show exactly what your FF Draft Vibe system will see!")
    print()
    
    seen_picks = set()
    iteration = 0
    
    try:
        while iteration < 30:  # Limit for testing (1 minute)
            iteration += 1
            
            # Get current picks
            url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
            response = requests.get(url)
            
            if response.status_code == 200:
                picks = response.json()
                
                # Check for new picks
                new_picks = []
                for pick in picks:
                    pick_key = f"{pick.get('round')}-{pick.get('pick_no')}"
                    if pick_key not in seen_picks:
                        seen_picks.add(pick_key)
                        new_picks.append(pick)
                
                # Show status
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                if new_picks:
                    print(f"🔄 NEW PICKS DETECTED! ({timestamp})")
                    for pick in new_picks:
                        round_num = pick.get('round', '?')
                        pick_num = pick.get('pick_no', '?') 
                        player_id = pick.get('player_id', 'Unknown')
                        picked_by = pick.get('picked_by', 'Unknown')
                        
                        print(f"   ✅ Round {round_num}, Pick {pick_num}: Team {picked_by} selected Player {player_id}")
                        
                        # This is where your recommendation engine would kick in!
                        print(f"      💡 [This is where recommendations would appear]")
                    print()
                else:
                    print(f"📊 {timestamp} | Total picks: {len(picks)} | No new activity")
                
            else:
                print(f"❌ API Error: {response.status_code}")
            
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitoring stopped")
    
    print(f"\n🎉 Test complete! The API can see your mock draft picks in real-time!")

def get_player_names():
    """Load player database to show actual names instead of IDs"""
    print(f"\n📥 Loading player database...")
    
    try:
        url = "https://api.sleeper.app/v1/players/nfl"
        response = requests.get(url)
        
        if response.status_code == 200:
            players = response.json()
            print(f"✅ Loaded {len(players)} players")
            return players
        else:
            print(f"❌ Error loading players: {response.status_code}")
            return {}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    print("🏈 Live Mock Draft Test")
    print("=" * 30)
    
    # Test 1: Can we connect?
    connected = test_live_mock_draft()
    
    if connected:
        print(f"\n🚀 SUCCESS! The Sleeper API can see your mock draft!")
        print(f"   ✅ Draft info accessible")
        print(f"   ✅ Pick data available") 
        print(f"   ✅ Real-time monitoring possible")
        
        # Test 2: Live monitoring
        print(f"\n🎯 Starting live monitoring test...")
        print(f"   Make some picks in your mock draft to see them appear here!")
        
        monitor_live_draft()
        
    else:
        print(f"\n❌ Could not connect to mock draft")
        print(f"   Check if the draft is still active")
        print(f"   Draft might be private or completed")
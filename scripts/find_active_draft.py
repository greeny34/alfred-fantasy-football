import requests
import time
from datetime import datetime

def find_active_drafts():
    """Find any active drafts for your user"""
    user_id = "352200144369963008"  # Your Sleeper user ID
    
    print("🔍 Searching for Active Drafts")
    print("=" * 40)
    
    # Check 2025 leagues first
    try:
        url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2025"
        response = requests.get(url)
        
        if response.status_code == 200:
            leagues = response.json()
            print(f"📋 Checking {len(leagues)} leagues...")
            
            for league in leagues:
                draft_id = league.get('draft_id')
                if draft_id:
                    print(f"\n✅ Found draft in league: {league.get('name', 'Unknown')}")
                    test_draft_status(draft_id)
        
        # Also check 2024 in case mock draft is there
        url_2024 = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2024"
        response_2024 = requests.get(url_2024)
        
        if response_2024.status_code == 200:
            leagues_2024 = response_2024.json()
            if leagues_2024:
                print(f"\n📋 Also checking {len(leagues_2024)} leagues from 2024...")
                for league in leagues_2024:
                    draft_id = league.get('draft_id')
                    if draft_id:
                        print(f"\n✅ Found 2024 draft in league: {league.get('name', 'Unknown')}")
                        test_draft_status(draft_id)
        
        # If no leagues found, mock drafts might be standalone
        print(f"\n🎯 Mock Draft Detection:")
        print(f"   Mock drafts might not show up in your leagues list")
        print(f"   They could be standalone draft IDs")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_draft_status(draft_id):
    """Test a specific draft ID"""
    print(f"   🎯 Testing Draft ID: {draft_id}")
    
    try:
        # Get draft info
        url = f"https://api.sleeper.app/v1/draft/{draft_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            draft_data = response.json()
            status = draft_data.get('status', 'Unknown')
            draft_type = draft_data.get('type', 'Unknown')
            
            print(f"   Status: {status}")
            print(f"   Type: {draft_type}")
            
            if status == 'drafting':
                print(f"   🚨 LIVE DRAFT FOUND!")
                return draft_id
            elif status == 'complete':
                print(f"   ✅ Complete draft (good for testing)")
            
            # Get picks to see activity
            picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
            picks_response = requests.get(picks_url)
            
            if picks_response.status_code == 200:
                picks = picks_response.json()
                print(f"   Picks: {len(picks)} completed")
                
                if picks:
                    last_pick = picks[-1]
                    print(f"   Last pick: Round {last_pick.get('round')}, Pick {last_pick.get('pick_no')}")
        else:
            print(f"   ❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return None

def try_common_draft_ids():
    """Try some common draft ID patterns"""
    print(f"\n🔍 Trying Common Draft ID Patterns")
    print("=" * 40)
    
    # Mock drafts might have different ID patterns
    # This is a long shot, but let's try some recent patterns
    
    import random
    
    # Generate some potential draft IDs (this is speculative)
    current_time = int(time.time())
    
    # Try some IDs around current timestamp
    test_ids = []
    for i in range(-100, 101, 20):
        test_id = str(current_time + i)
        test_ids.append(test_id)
    
    print(f"Testing {len(test_ids)} potential draft IDs...")
    
    for test_id in test_ids[:5]:  # Limit to first 5 to avoid spam
        try:
            url = f"https://api.sleeper.app/v1/draft/{test_id}"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                print(f"✅ Found draft: {test_id}")
                test_draft_status(test_id)
                return test_id
            
        except:
            continue
    
    print("❌ No active drafts found with common patterns")
    return None

def manual_draft_id_test():
    """Allow manual input of draft ID"""
    print(f"\n🎯 Manual Draft ID Test")
    print("=" * 30)
    print("If you're on a Sleeper mock draft page, look at the URL.")
    print("It might contain a draft ID like: sleeper.com/draft/[DRAFT_ID]")
    print()
    
    draft_id = input("Enter draft ID from URL (or press Enter to skip): ").strip()
    
    if draft_id:
        print(f"Testing draft ID: {draft_id}")
        test_draft_status(draft_id)
        return draft_id
    
    return None

def monitor_draft_live(draft_id):
    """Monitor a specific draft in real-time"""
    if not draft_id:
        print("❌ No draft ID provided")
        return
    
    print(f"\n🎯 LIVE MONITORING: Draft {draft_id}")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    
    seen_picks = set()
    
    try:
        while True:
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
                
                if new_picks:
                    print(f"\n🔄 NEW PICKS ({datetime.now().strftime('%H:%M:%S')}):")
                    for pick in new_picks:
                        round_num = pick.get('round', '?')
                        pick_num = pick.get('pick_no', '?')
                        player_id = pick.get('player_id', 'Unknown')
                        picked_by = pick.get('picked_by', 'Unknown')
                        
                        print(f"   Round {round_num}, Pick {pick_num}: Team {picked_by} - Player {player_id}")
                
                print(f"📊 Total picks: {len(picks)} | Checking again in 3 seconds...")
                
            else:
                print(f"❌ Error getting picks: {response.status_code}")
            
            time.sleep(3)
            
    except KeyboardInterrupt:
        print(f"\n👋 Stopped monitoring")

if __name__ == "__main__":
    print("🎯 Finding Your Active Mock Draft")
    print("=" * 40)
    
    # Try to find drafts automatically
    active_draft = find_active_drafts()
    
    if not active_draft:
        # Try manual input
        active_draft = manual_draft_id_test()
    
    if active_draft:
        print(f"\n🚀 Ready to monitor draft: {active_draft}")
        start_monitoring = input("Start live monitoring? (y/n): ").lower().startswith('y')
        
        if start_monitoring:
            monitor_draft_live(active_draft)
    else:
        print(f"\n💡 To connect to your mock draft:")
        print(f"   1. Look at the URL of your mock draft page")
        print(f"   2. Find the draft ID in the URL")
        print(f"   3. Run this script again with the draft ID")
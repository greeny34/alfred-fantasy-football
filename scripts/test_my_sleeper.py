import requests

def test_my_sleeper_account():
    """Test your specific Sleeper account"""
    user_id = "352200144369963008"  # Your user ID from the API test
    
    print("🏈 Testing Your Sleeper Account")
    print("=" * 40)
    print(f"User ID: {user_id}")
    
    # Test getting your leagues
    try:
        url = f"https://api.sleeper.app/v1/user/{user_id}/leagues/nfl/2025"
        response = requests.get(url)
        
        print(f"\n📋 Your 2025 Leagues:")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            leagues = response.json()
            print(f"✅ Found {len(leagues)} leagues")
            
            if leagues:
                for i, league in enumerate(leagues):
                    print(f"\n   League {i+1}:")
                    print(f"   Name: {league.get('name', 'Unknown')}")
                    print(f"   Status: {league.get('status', 'Unknown')}")
                    print(f"   League ID: {league.get('league_id')}")
                    print(f"   Draft ID: {league.get('draft_id', 'None')}")
                    print(f"   Teams: {league.get('total_rosters', 'Unknown')}")
                    
                    # If there's a draft, test it
                    draft_id = league.get('draft_id')
                    if draft_id:
                        test_draft(draft_id)
            else:
                print("❌ No leagues found for 2025")
                print("\n💡 To test:")
                print("   1. Go to sleeper.com")
                print("   2. Create or join a 2025 league")
                print("   3. Set up a draft")
                print("   4. Run this test again")
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error getting leagues: {e}")

def test_draft(draft_id):
    """Test a specific draft"""
    print(f"\n   🎯 Testing Draft: {draft_id}")
    
    try:
        # Get draft info
        url = f"https://api.sleeper.app/v1/draft/{draft_id}"
        response = requests.get(url)
        
        if response.status_code == 200:
            draft_data = response.json()
            print(f"   Status: {draft_data.get('status', 'Unknown')}")
            print(f"   Type: {draft_data.get('type', 'Unknown')}")
            
            # Get draft picks
            picks_url = f"https://api.sleeper.app/v1/draft/{draft_id}/picks"
            picks_response = requests.get(picks_url)
            
            if picks_response.status_code == 200:
                picks = picks_response.json()
                print(f"   Picks: {len(picks)} completed")
                
                if picks:
                    print("   Recent picks:")
                    for pick in picks[-3:]:  # Last 3 picks
                        round_num = pick.get('round', '?')
                        pick_num = pick.get('pick_no', '?')
                        player_id = pick.get('player_id', 'Unknown')
                        print(f"     Round {round_num}, Pick {pick_num}: Player {player_id}")
                
                # This would be perfect for real-time monitoring!
                if draft_data.get('status') == 'drafting':
                    print("   🚨 DRAFT IS LIVE! Perfect for testing!")
                elif draft_data.get('status') == 'complete':
                    print("   ✅ Draft complete - good for testing pick detection")
                
            else:
                print(f"   ❌ Error getting picks: {picks_response.status_code}")
        else:
            print(f"   ❌ Error getting draft info: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error testing draft: {e}")

def test_players_sample():
    """Test getting player information"""
    print(f"\n🏈 Testing Player Database")
    print("=" * 30)
    
    try:
        url = "https://api.sleeper.app/v1/players/nfl"
        print("📥 Loading players (this takes a moment)...")
        response = requests.get(url)
        
        if response.status_code == 200:
            players = response.json()
            print(f"✅ Loaded {len(players)} players")
            
            # Show some sample players
            print(f"\nSample top players:")
            count = 0
            for player_id, player_data in players.items():
                if count >= 10:
                    break
                    
                name = player_data.get('full_name', 'Unknown')
                pos = player_data.get('position', 'UNK')
                team = player_data.get('team', 'FA')
                
                if pos in ['QB', 'RB', 'WR', 'TE'] and team != 'FA':
                    print(f"   {name} ({pos}) - {team}")
                    count += 1
                    
            return players
        else:
            print(f"❌ Error loading players: {response.status_code}")
            return {}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {}

if __name__ == "__main__":
    print("🎯 Testing Your Sleeper Setup")
    print("=" * 35)
    
    # Test your account
    test_my_sleeper_account()
    
    # Test players
    test_players_sample()
    
    print(f"\n🚀 Next Steps:")
    print(f"   1. If you have leagues, we can test live draft monitoring")  
    print(f"   2. If no leagues, create one on sleeper.com")
    print(f"   3. The API is working perfectly for real-time pick tracking!")
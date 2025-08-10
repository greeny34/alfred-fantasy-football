#!/usr/bin/env python3
"""
Debug defense/D/ST data from Sleeper API
"""
import requests
import json

def debug_defenses():
    print("🔍 DEBUGGING DEFENSE DATA FROM SLEEPER API")
    print("=" * 50)
    
    try:
        url = "https://api.sleeper.app/v1/players/nfl"
        response = requests.get(url)
        
        if response.status_code == 200:
            all_players = response.json()
            print(f"✅ Loaded {len(all_players)} total players")
            
            # Look for defenses
            defenses = []
            defense_positions = []
            
            for player_id, player_data in all_players.items():
                position = player_data.get('position', '')
                team = player_data.get('team', '')
                name = player_data.get('full_name', '')
                
                # Check for any defense-related positions
                if position and ('DEF' in position or 'D/ST' in position or position == 'DST'):
                    defenses.append({
                        'id': player_id,
                        'name': name,
                        'position': position,
                        'team': team,
                        'status': player_data.get('status', ''),
                        'data': player_data
                    })
                
                # Track all unique positions that might be defense
                if position and ('D' in position or 'DEF' in position or 'ST' in position):
                    if position not in defense_positions:
                        defense_positions.append(position)
            
            print(f"\n📊 Defense-related positions found: {defense_positions}")
            print(f"🛡️ Total defense entries: {len(defenses)}")
            
            if defenses:
                print("\n🛡️ Defense entries found:")
                for i, defense in enumerate(defenses[:10]):  # Show first 10
                    print(f"  {i+1}. {defense['name']} ({defense['position']}) - {defense['team']}")
            else:
                print("\n❌ No defense entries found!")
                
                # Let's look for team-based data instead
                print("\n🔍 Looking for team-based defense data...")
                
                # Check if there are team abbreviations we can use
                teams = set()
                for player_id, player_data in list(all_players.items())[:1000]:  # Sample first 1000
                    team = player_data.get('team', '')
                    if team and len(team) <= 3 and team != 'FA':
                        teams.add(team)
                
                print(f"📋 Found {len(teams)} unique teams: {sorted(list(teams))}")
                
                # Manually create defense entries for each team
                if teams:
                    print("\n💡 We can manually create defense entries for each team")
                    for team in sorted(list(teams))[:10]:  # Show first 10
                        print(f"  {team} Defense")
            
            # Also check for kickers to see the pattern
            print(f"\n🦶 Checking kickers for comparison:")
            kickers = []
            for player_id, player_data in all_players.items():
                if player_data.get('position') == 'K':
                    kickers.append({
                        'name': player_data.get('full_name', ''),
                        'team': player_data.get('team', ''),
                        'status': player_data.get('status', '')
                    })
            
            print(f"Found {len(kickers)} kickers")
            if kickers:
                for i, kicker in enumerate(kickers[:5]):  # Show first 5
                    print(f"  {i+1}. {kicker['name']} - {kicker['team']} ({kicker['status']})")
            
        else:
            print(f"❌ Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_defenses()
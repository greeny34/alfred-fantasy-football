#!/usr/bin/env python3
"""
Show all player rankings from the expert consensus data
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

from complete_sleeper_assistant import CompleteDraftAssistant

def show_all_rankings():
    assistant = CompleteDraftAssistant("dummy_id")
    
    print("🏈 2025 FANTASY FOOTBALL EXPERT CONSENSUS RANKINGS")
    print("=" * 80)
    print("Format: Rank | Player Name (Position) - Team | Range | Std Dev | VORP")
    print("-" * 80)
    
    # Get all players with rankings (create dummy available list for VORP calc)
    dummy_available = []
    all_rankings = []
    
    # Create test players to get all rankings
    test_names = [
        "Ja'Marr Chase", "Bijan Robinson", "Justin Jefferson", "CeeDee Lamb", 
        "Saquon Barkley", "Jahmyr Gibbs", "Amon-Ra St. Brown", "Puka Nacua",
        "Malik Nabers", "De'Von Achane", "Brian Thomas Jr.", "Ashton Jeanty",
        "Nico Collins", "Brock Bowers", "Christian McCaffrey", "Drake London",
        "A.J. Brown", "Josh Jacobs", "Derrick Henry", "Ladd McConkey",
        "Jaxon Smith-Njigba", "Breece Hall", "Chase Brown", "Tee Higgins",
        "Kenneth Walker III", "James Cook", "Trey McBride", "George Kittle",
        "Cooper Kupp", "Davante Adams", "D.K. Metcalf", "Rome Odunze",
        "Marvin Harrison Jr.", "Stefon Diggs", "Mike Evans", "Chris Godwin",
        "Calvin Ridley", "Jaylen Waddle", "Devon Singletary", "Jordan Mason",
        "Sam LaPorta", "T.J. Hockenson", "Travis Kelce", "Keon Coleman",
        "Jayden Reed", "DJ Moore", "Courtland Sutton", "Jerry Jeudy",
        "Amari Cooper", "Tyler Lockett", "Josh Allen", "Lamar Jackson",
        "Jayden Daniels", "Jalen Hurts", "Bo Nix", "Joe Burrow",
        "Baker Mayfield", "Patrick Mahomes", "Caleb Williams", "Justin Herbert",
        "Rachaad White", "Javonte Williams", "D'Andre Swift", "Najee Harris",
        "Aaron Jones", "Alvin Kamara", "Austin Ekeler", "Tony Pollard",
        "Zack Moss", "DeAndre Hopkins", "Keenan Allen", "Brandon Aiyuk",
        "Diontae Johnson", "Terry McLaurin", "Michael Pittman Jr.", "Tank Dell",
        "Jordan Addison", "Jameson Williams", "Evan Engram", "Tucker Kraft",
        "David Njoku", "Kyle Pitts", "Jake Ferguson", "Jonnu Smith",
        "Bucky Irving", "Ty Chandler", "Blake Corum", "Braelon Allen",
        "Kimani Vidal", "Ray Davis", "Tyjae Spears", "Jaylen Warren",
        "Jerome Ford", "Alexander Mattison", "Devin Singletary", "Rico Dowdle",
        "Josh Downs", "Wan'Dale Robinson", "Darnell Mooney", "Xavier Legette"
    ]
    
    # Get rankings for all test players
    for name in test_names:
        # Try different position/team combinations to get the ranking
        for pos in ['QB', 'RB', 'WR', 'TE']:
            test_player = {"name": name, "position": pos, "team": "TEST"}
            consensus, high, low, std = assistant.get_player_expert_data(test_player)
            if consensus < 999:  # Found ranking
                all_rankings.append({
                    'name': name,
                    'position': pos,
                    'consensus': consensus,
                    'high': high,
                    'low': low,
                    'std': std,
                    'range': low - high,
                    'player_obj': test_player
                })
                dummy_available.append(test_player)
                break  # Found it, move to next player
    
    # Sort by consensus ranking
    all_rankings.sort(key=lambda x: x['consensus'])
    
    # Display rankings with VORP
    for i, player_data in enumerate(all_rankings, 1):
        name = player_data['name']
        pos = player_data['position']
        consensus = player_data['consensus']
        high = player_data['high']
        low = player_data['low']
        std = player_data['std']
        range_val = player_data['range']
        
        # Calculate VORP (using all available players for context)
        vorp = assistant.calculate_value_over_replacement(player_data['player_obj'], dummy_available)
        
        print(f"{consensus:3d} | {name:<22} ({pos}) | {high:2d}-{low:2d} | {std:4.1f} | {vorp:5.1f}")
        
        # Add position separators for readability
        if i < len(all_rankings):
            next_consensus = all_rankings[i]['consensus'] if i < len(all_rankings) else 999
            if consensus <= 15 and next_consensus > 15:
                print("    " + "-" * 70 + " [ELITE TIER]")
            elif consensus <= 30 and next_consensus > 30:
                print("    " + "-" * 70 + " [TIER 2]")
            elif consensus <= 50 and next_consensus > 50:
                print("    " + "-" * 70 + " [TIER 3]")
    
    print("\n📊 LEGEND:")
    print("• Rank: Expert consensus ranking (lower = better)")
    print("• Range: Best case - Worst case expert rankings")
    print("• Std Dev: Expert disagreement (lower = more consensus)")
    print("• VORP: Value Over Replacement Player score")
    
    print("\n🔍 KEY INSIGHTS:")
    print("• Players ranked 1-15: Elite tier, minimal expert disagreement")
    print("• Players ranked 16-30: High-end tier, some disagreement")
    print("• Players ranked 31-50: Solid tier, moderate disagreement")
    print("• Players ranked 51+: Later rounds, high disagreement")

if __name__ == "__main__":
    show_all_rankings()
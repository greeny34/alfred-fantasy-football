#!/usr/bin/env python3
"""
Show all player rankings with correct positions
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

from complete_sleeper_assistant import CompleteDraftAssistant

def show_correct_rankings():
    assistant = CompleteDraftAssistant("dummy_id")
    
    print("🏈 2025 FANTASY FOOTBALL EXPERT CONSENSUS RANKINGS")
    print("=" * 85)
    print("Format: Rank | Player Name (Position) - Team | Range | Std Dev | VORP")
    print("-" * 85)
    
    # Players with their correct positions and teams
    players_data = [
        # Top WRs
        ("Ja'Marr Chase", "WR", "CIN"),
        ("Justin Jefferson", "WR", "MIN"), 
        ("CeeDee Lamb", "WR", "DAL"),
        ("Amon-Ra St. Brown", "WR", "DET"),
        ("Puka Nacua", "WR", "LAR"),
        ("Malik Nabers", "WR", "NYG"),
        ("Brian Thomas Jr.", "WR", "JAX"),
        ("Nico Collins", "WR", "HOU"),
        ("Drake London", "WR", "ATL"),
        ("A.J. Brown", "WR", "PHI"),
        ("Ladd McConkey", "WR", "LAC"),
        ("Jaxon Smith-Njigba", "WR", "SEA"),
        ("Tee Higgins", "WR", "CIN"),
        ("D.K. Metcalf", "WR", "SEA"),
        ("Rome Odunze", "WR", "CHI"),
        ("Marvin Harrison Jr.", "WR", "ARI"),
        ("Stefon Diggs", "WR", "HOU"),
        ("Mike Evans", "WR", "TB"),
        ("Chris Godwin", "WR", "TB"),
        ("Calvin Ridley", "WR", "TEN"),
        ("Jaylen Waddle", "WR", "MIA"),
        ("Keon Coleman", "WR", "BUF"),
        ("Jayden Reed", "WR", "GB"),
        ("DJ Moore", "WR", "CHI"),
        ("Courtland Sutton", "WR", "DEN"),
        ("Jerry Jeudy", "WR", "CLE"),
        ("Amari Cooper", "WR", "BUF"),
        ("Tyler Lockett", "WR", "SEA"),
        
        # Top RBs
        ("Bijan Robinson", "RB", "ATL"),
        ("Saquon Barkley", "RB", "PHI"),
        ("Jahmyr Gibbs", "RB", "DET"),
        ("De'Von Achane", "RB", "MIA"),
        ("Ashton Jeanty", "RB", "LV"),
        ("Christian McCaffrey", "RB", "SF"),
        ("Josh Jacobs", "RB", "GB"),
        ("Derrick Henry", "RB", "BAL"),
        ("Breece Hall", "RB", "NYJ"),
        ("Chase Brown", "RB", "CIN"),
        ("Kenneth Walker III", "RB", "SEA"),
        ("James Cook", "RB", "BUF"),
        ("Devon Singletary", "RB", "NYG"),
        ("Jordan Mason", "RB", "SF"),
        ("Rachaad White", "RB", "TB"),
        ("Javonte Williams", "RB", "DEN"),
        ("D'Andre Swift", "RB", "CHI"),
        ("Najee Harris", "RB", "PIT"),
        ("Aaron Jones", "RB", "MIN"),
        ("Alvin Kamara", "RB", "NO"),
        ("Austin Ekeler", "RB", "WAS"),
        ("Tony Pollard", "RB", "TEN"),
        ("Zack Moss", "RB", "CIN"),
        
        # TEs
        ("Brock Bowers", "TE", "LV"),
        ("Trey McBride", "TE", "ARI"),
        ("George Kittle", "TE", "SF"),
        ("Sam LaPorta", "TE", "DET"),
        ("T.J. Hockenson", "TE", "MIN"),
        ("Travis Kelce", "TE", "KC"),
        ("Evan Engram", "TE", "JAX"),
        ("Tucker Kraft", "TE", "GB"),
        ("David Njoku", "TE", "CLE"),
        ("Kyle Pitts", "TE", "ATL"),
        ("Jake Ferguson", "TE", "DAL"),
        ("Jonnu Smith", "TE", "MIA"),
        
        # QBs
        ("Josh Allen", "QB", "BUF"),
        ("Lamar Jackson", "QB", "BAL"),
        ("Jayden Daniels", "QB", "WAS"),
        ("Jalen Hurts", "QB", "PHI"),
        ("Bo Nix", "QB", "DEN"),
        ("Joe Burrow", "QB", "CIN"),
        ("Baker Mayfield", "QB", "TB"),
        ("Patrick Mahomes", "QB", "KC"),
        ("Caleb Williams", "QB", "CHI"),
        ("Justin Herbert", "QB", "LAC"),
        
        # More WRs
        ("Cooper Kupp", "WR", "LAR"),
        ("Davante Adams", "WR", "LV"),
        ("DeAndre Hopkins", "WR", "KC"),
        ("Keenan Allen", "WR", "CHI"),
        ("Brandon Aiyuk", "WR", "SF"),
        ("Diontae Johnson", "WR", "CAR"),
        ("Terry McLaurin", "WR", "WAS"),
        ("Michael Pittman Jr.", "WR", "IND"),
        ("Tank Dell", "WR", "HOU"),
        ("Jordan Addison", "WR", "MIN"),
        ("Jameson Williams", "WR", "DET"),
        
        # More RBs
        ("Bucky Irving", "RB", "TB"),
        ("Ty Chandler", "RB", "MIN"),
        ("Blake Corum", "RB", "LAR"),
        ("Braelon Allen", "RB", "NYJ"),
        ("Kimani Vidal", "RB", "LAC"),
        ("Ray Davis", "RB", "BUF"),
        ("Tyjae Spears", "RB", "TEN"),
        ("Jaylen Warren", "RB", "PIT"),
        ("Jerome Ford", "RB", "CLE"),
        ("Alexander Mattison", "RB", "LV"),
        ("Devin Singletary", "RB", "NYG"),
        ("Rico Dowdle", "RB", "DAL"),
        
        # More WRs
        ("Josh Downs", "WR", "IND"),
        ("Wan'Dale Robinson", "WR", "NYG"),
        ("Darnell Mooney", "WR", "ATL"),
        ("Xavier Legette", "WR", "CAR"),
    ]
    
    # Get rankings and VORP for all players
    all_rankings = []
    dummy_available = []
    
    for name, pos, team in players_data:
        player_obj = {"name": name, "position": pos, "team": team, "player_id": f"test_{name.replace(' ', '_')}"}
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        if consensus < 999:  # Has ranking data
            all_rankings.append({
                'name': name,
                'position': pos,
                'team': team,
                'consensus': consensus,
                'high': high,
                'low': low,
                'std': std,
                'range': low - high,
                'player_obj': player_obj
            })
            dummy_available.append(player_obj)
    
    # Sort by consensus ranking
    all_rankings.sort(key=lambda x: x['consensus'])
    
    # Display rankings with VORP
    for i, player_data in enumerate(all_rankings):
        name = player_data['name']
        pos = player_data['position']
        team = player_data['team']
        consensus = player_data['consensus']
        high = player_data['high']
        low = player_data['low']
        std = player_data['std']
        
        # Calculate VORP
        vorp = assistant.calculate_value_over_replacement(player_data['player_obj'], dummy_available)
        
        print(f"{consensus:3d} | {name:<22} ({pos}) - {team} | {high:2d}-{low:3d} | {std:4.1f} | {vorp:5.1f}")
        
        # Add tier separators
        if i < len(all_rankings) - 1:
            next_consensus = all_rankings[i + 1]['consensus']
            if consensus <= 15 and next_consensus > 15:
                print("    " + "-" * 75 + " [ELITE TIER]")
            elif consensus <= 30 and next_consensus > 30:
                print("    " + "-" * 75 + " [TIER 2]")
            elif consensus <= 50 and next_consensus > 50:
                print("    " + "-" * 75 + " [TIER 3]")
    
    print("\n📊 KEY INSIGHTS FROM RANKINGS:")
    
    # Show position breakdowns
    by_position = {}
    for player in all_rankings[:30]:  # Top 30 picks
        pos = player['position']
        if pos not in by_position:
            by_position[pos] = []
        by_position[pos].append(player['name'])
    
    print("\n🎯 TOP 30 PICKS BY POSITION:")
    for pos in ['WR', 'RB', 'TE', 'QB']:
        if pos in by_position:
            count = len(by_position[pos])
            print(f"  {pos}: {count} players - {', '.join(by_position[pos][:5])}{'...' if count > 5 else ''}")
    
    print("\n💡 DRAFTING STRATEGY INSIGHTS:")
    print("• WR heavy in early rounds - load up on elite talent")
    print("• RB scarcity creates value gaps - Josh Jacobs vs Aaron Jones")
    print("• TE has clear tier breaks - Brock Bowers, then big drop")
    print("• QB can wait - even elite QBs ranked 50+")

if __name__ == "__main__":
    show_correct_rankings()
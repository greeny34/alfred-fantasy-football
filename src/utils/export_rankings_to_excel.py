#!/usr/bin/env python3
"""
Export all fantasy football rankings to Excel file
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
from complete_sleeper_assistant import CompleteDraftAssistant

def export_all_rankings_to_excel():
    assistant = CompleteDraftAssistant("dummy_id")
    
    print("🏈 EXPORTING ALL 2025 FANTASY FOOTBALL RANKINGS TO EXCEL")
    print("=" * 60)
    
    # Comprehensive player database with positions and teams
    all_players = [
        # Elite WRs
        ("Ja'Marr Chase", "WR", "CIN"), ("Justin Jefferson", "WR", "MIN"), ("CeeDee Lamb", "WR", "DAL"),
        ("Amon-Ra St. Brown", "WR", "DET"), ("Puka Nacua", "WR", "LAR"), ("Malik Nabers", "WR", "NYG"),
        ("Brian Thomas Jr.", "WR", "JAX"), ("Nico Collins", "WR", "HOU"), ("Drake London", "WR", "ATL"),
        ("A.J. Brown", "WR", "PHI"), ("Ladd McConkey", "WR", "LAC"), ("Jaxon Smith-Njigba", "WR", "SEA"),
        ("Tee Higgins", "WR", "CIN"), ("D.K. Metcalf", "WR", "SEA"), ("Rome Odunze", "WR", "CHI"),
        ("Marvin Harrison Jr.", "WR", "ARI"), ("Stefon Diggs", "WR", "HOU"), ("Mike Evans", "WR", "TB"),
        ("Chris Godwin", "WR", "TB"), ("Calvin Ridley", "WR", "TEN"), ("Jaylen Waddle", "WR", "MIA"),
        ("Cooper Kupp", "WR", "LAR"), ("Davante Adams", "WR", "LV"), ("Keon Coleman", "WR", "BUF"),
        ("Jayden Reed", "WR", "GB"), ("DJ Moore", "WR", "CHI"), ("Courtland Sutton", "WR", "DEN"),
        ("Jerry Jeudy", "WR", "CLE"), ("Amari Cooper", "WR", "BUF"), ("Tyler Lockett", "WR", "SEA"),
        ("DeAndre Hopkins", "WR", "KC"), ("Keenan Allen", "WR", "CHI"), ("Brandon Aiyuk", "WR", "SF"),
        ("Diontae Johnson", "WR", "CAR"), ("Terry McLaurin", "WR", "WAS"), ("Michael Pittman Jr.", "WR", "IND"),
        ("Tank Dell", "WR", "HOU"), ("Jordan Addison", "WR", "MIN"), ("Jameson Williams", "WR", "DET"),
        ("Josh Downs", "WR", "IND"), ("Wan'Dale Robinson", "WR", "NYG"), ("Darnell Mooney", "WR", "ATL"),
        ("Xavier Legette", "WR", "CAR"), ("Cedrick Wilson Jr.", "WR", "NO"), ("Tutu Atwell", "WR", "LAR"),
        ("Demario Douglas", "WR", "NE"), ("Jalen McMillan", "WR", "TB"), ("Malachi Corley", "WR", "NYJ"),
        ("Troy Franklin", "WR", "DEN"), ("Ja'Lynn Polk", "WR", "NE"), ("Ricky Pearsall", "WR", "SF"),
        ("Javon Baker", "WR", "NE"), ("Luke McCaffrey", "WR", "WAS"), ("Adonai Mitchell", "WR", "IND"),
        
        # Elite RBs
        ("Bijan Robinson", "RB", "ATL"), ("Saquon Barkley", "RB", "PHI"), ("Jahmyr Gibbs", "RB", "DET"),
        ("De'Von Achane", "RB", "MIA"), ("Ashton Jeanty", "RB", "LV"), ("Christian McCaffrey", "RB", "SF"),
        ("Josh Jacobs", "RB", "GB"), ("Derrick Henry", "RB", "BAL"), ("Breece Hall", "RB", "NYJ"),
        ("Chase Brown", "RB", "CIN"), ("Kenneth Walker III", "RB", "SEA"), ("James Cook", "RB", "BUF"),
        ("Devon Singletary", "RB", "NYG"), ("Jordan Mason", "RB", "SF"), ("Rachaad White", "RB", "TB"),
        ("Javonte Williams", "RB", "DEN"), ("D'Andre Swift", "RB", "CHI"), ("Najee Harris", "RB", "PIT"),
        ("Aaron Jones", "RB", "MIN"), ("Alvin Kamara", "RB", "NO"), ("Austin Ekeler", "RB", "WAS"),
        ("Tony Pollard", "RB", "TEN"), ("Zack Moss", "RB", "CIN"), ("Bucky Irving", "RB", "TB"),
        ("Ty Chandler", "RB", "MIN"), ("Blake Corum", "RB", "LAR"), ("Braelon Allen", "RB", "NYJ"),
        ("Kimani Vidal", "RB", "LAC"), ("Ray Davis", "RB", "BUF"), ("Tyjae Spears", "RB", "TEN"),
        ("Jaylen Warren", "RB", "PIT"), ("Jerome Ford", "RB", "CLE"), ("Alexander Mattison", "RB", "LV"),
        ("Devin Singletary", "RB", "NYG"), ("Rico Dowdle", "RB", "DAL"), ("Quinshon Judkins", "RB", "DET"),
        ("Trey Benson", "RB", "ARI"), ("Jaylen Wright", "RB", "MIA"), ("Isaac Guerendo", "RB", "SF"),
        ("Cam Akers", "RB", "HOU"), ("Justice Hill", "RB", "BAL"), ("Samaje Perine", "RB", "KC"),
        ("Tyler Allgeier", "RB", "ATL"), ("A.J. Dillon", "RB", "GB"), ("Roschon Johnson", "RB", "CHI"),
        
        # TEs
        ("Brock Bowers", "TE", "LV"), ("Trey McBride", "TE", "ARI"), ("George Kittle", "TE", "SF"),
        ("Sam LaPorta", "TE", "DET"), ("T.J. Hockenson", "TE", "MIN"), ("Travis Kelce", "TE", "KC"),
        ("Evan Engram", "TE", "JAX"), ("Tucker Kraft", "TE", "GB"), ("David Njoku", "TE", "CLE"),
        ("Kyle Pitts", "TE", "ATL"), ("Jake Ferguson", "TE", "DAL"), ("Jonnu Smith", "TE", "MIA"),
        ("Tyler Higbee", "TE", "LAR"), ("Hunter Henry", "TE", "NE"), ("Noah Fant", "TE", "SEA"),
        ("Pat Freiermuth", "TE", "PIT"), ("Cole Kmet", "TE", "CHI"), ("Dalton Kincaid", "TE", "BUF"),
        ("Mark Andrews", "TE", "BAL"), ("Dalton Schultz", "TE", "HOU"), ("Mike Gesicki", "TE", "CIN"),
        
        # QBs
        ("Josh Allen", "QB", "BUF"), ("Lamar Jackson", "QB", "BAL"), ("Jayden Daniels", "QB", "WAS"),
        ("Jalen Hurts", "QB", "PHI"), ("Bo Nix", "QB", "DEN"), ("Joe Burrow", "QB", "CIN"),
        ("Baker Mayfield", "QB", "TB"), ("Patrick Mahomes", "QB", "KC"), ("Caleb Williams", "QB", "CHI"),
        ("Justin Herbert", "QB", "LAC"), ("Dak Prescott", "QB", "DAL"), ("Tua Tagovailoa", "QB", "MIA"),
        ("Anthony Richardson", "QB", "IND"), ("Kirk Cousins", "QB", "ATL"), ("Aaron Rodgers", "QB", "NYJ"),
        ("Russell Wilson", "QB", "PIT"), ("Kyler Murray", "QB", "ARI"), ("Geno Smith", "QB", "SEA"),
        ("Daniel Jones", "QB", "NYG"), ("Drake Maye", "QB", "NE"), ("Michael Penix Jr.", "QB", "ATL"),
        ("J.J. McCarthy", "QB", "MIN"), ("Malik Willis", "QB", "GB"), ("Sam Darnold", "QB", "MIN"),
        ("Gardner Minshew", "QB", "LV"), ("Justin Fields", "QB", "PIT"), ("Jacoby Brissett", "QB", "NE"),
        
        # Add some Kickers and Defenses for completeness
        ("Justin Tucker", "K", "BAL"), ("Harrison Butker", "K", "KC"), ("Tyler Bass", "K", "BUF"),
        ("Brandon McManus", "K", "GB"), ("Younghoe Koo", "K", "ATL"), ("Chris Boswell", "K", "PIT"),
        ("49ers", "D/ST", "SF"), ("Ravens", "D/ST", "BAL"), ("Bills", "D/ST", "BUF"),
        ("Eagles", "D/ST", "PHI"), ("Cowboys", "D/ST", "DAL"), ("Steelers", "D/ST", "PIT"),
    ]
    
    # Process all players
    rankings_data = []
    dummy_available = []
    
    print(f"📊 Processing {len(all_players)} players...")
    
    for name, pos, team in all_players:
        player_obj = {"name": name, "position": pos, "team": team, "player_id": f"export_{name.replace(' ', '_')}"}
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        # Include all players, even those without rankings
        if consensus < 999:  # Has ranking data
            dummy_available.append(player_obj)
            has_ranking = True
        else:
            has_ranking = False
            consensus = high = low = std = None
        
        rankings_data.append({
            'Player_Name': name,
            'Position': pos,
            'Team': team,
            'Consensus_Rank': consensus,
            'Best_Case_Rank': high,
            'Worst_Case_Rank': low,
            'Expert_Std_Dev': std,
            'Range': (low - high) if (high is not None and low is not None) else None,
            'Has_Expert_Ranking': has_ranking,
            'player_obj': player_obj if has_ranking else None
        })
    
    # Calculate VORP for ranked players
    print("🧮 Calculating VORP scores...")
    for i, player_data in enumerate(rankings_data):
        if player_data['Has_Expert_Ranking'] and player_data['player_obj']:
            vorp = assistant.calculate_value_over_replacement(player_data['player_obj'], dummy_available)
            player_data['VORP_Score'] = round(vorp, 1)
        else:
            player_data['VORP_Score'] = None
        
        # Remove player_obj for Excel export
        del player_data['player_obj']
    
    # Create DataFrame
    df = pd.DataFrame(rankings_data)
    
    # Sort by consensus rank (NaN values go to end)
    df = df.sort_values(['Consensus_Rank', 'Player_Name'], na_position='last')
    
    # Add positional rankings
    print("🏆 Adding positional rankings...")
    df['Position_Rank'] = df.groupby('Position')['Consensus_Rank'].rank(method='min', na_option='bottom').astype('Int64')
    
    # Create separate sheets for each position
    with pd.ExcelWriter('/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_Rankings.xlsx', engine='openpyxl') as writer:
        
        # Overall rankings sheet
        overall_df = df[df['Has_Expert_Ranking'] == True].copy()
        overall_df = overall_df[['Consensus_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank', 
                                'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 'VORP_Score']]
        overall_df.to_excel(writer, sheet_name='Overall_Rankings', index=False)
        
        # Position-specific sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos].copy()
            if not pos_df.empty:
                pos_df = pos_df[['Position_Rank', 'Player_Name', 'Team', 'Consensus_Rank', 
                               'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 'VORP_Score', 'Has_Expert_Ranking']]
                # Fix sheet name for D/ST
                sheet_name = pos.replace('/', '_') + '_Rankings'
                pos_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # All players sheet (including unranked)
        all_df = df[['Player_Name', 'Position', 'Team', 'Consensus_Rank', 'Position_Rank',
                    'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 'VORP_Score', 'Has_Expert_Ranking']]
        all_df.to_excel(writer, sheet_name='All_Players', index=False)
        
        # Summary statistics sheet
        summary_data = []
        for pos in ['QB', 'RB', 'WR', 'TE']:
            pos_players = df[df['Position'] == pos]
            ranked_players = pos_players[pos_players['Has_Expert_Ranking'] == True]
            
            if not ranked_players.empty:
                summary_data.append({
                    'Position': pos,
                    'Total_Players': len(pos_players),
                    'Ranked_Players': len(ranked_players),
                    'Top_Player': ranked_players.iloc[0]['Player_Name'],
                    'Top_Rank': ranked_players.iloc[0]['Consensus_Rank'],
                    'Avg_VORP': round(ranked_players['VORP_Score'].mean(), 1),
                    'Max_VORP': round(ranked_players['VORP_Score'].max(), 1),
                    'Min_VORP': round(ranked_players['VORP_Score'].min(), 1)
                })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Position_Summary', index=False)
    
    print(f"✅ Excel file created: FF_2025_Rankings.xlsx")
    print(f"📊 Total players exported: {len(df)}")
    print(f"🏆 Players with expert rankings: {len(df[df['Has_Expert_Ranking'] == True])}")
    
    print(f"\n📋 Excel file contains:")
    print(f"  • Overall_Rankings: Top 100 ranked players")
    print(f"  • QB_Rankings: All quarterbacks")  
    print(f"  • RB_Rankings: All running backs")
    print(f"  • WR_Rankings: All wide receivers")
    print(f"  • TE_Rankings: All tight ends")
    print(f"  • All_Players: Every player in database")
    print(f"  • Position_Summary: Stats by position")
    
    print(f"\n🎯 Columns included:")
    print(f"  • Consensus_Rank: Expert average ranking")
    print(f"  • Position_Rank: Rank within position")
    print(f"  • Best/Worst_Case_Rank: Expert range")
    print(f"  • Expert_Std_Dev: Expert disagreement")
    print(f"  • VORP_Score: Value Over Replacement Player")
    print(f"  • Range: Difference between best and worst expert rankings")

if __name__ == "__main__":
    export_all_rankings_to_excel()
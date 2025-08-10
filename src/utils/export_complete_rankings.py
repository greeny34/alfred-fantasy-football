#!/usr/bin/env python3
"""
Export comprehensive fantasy football rankings using ALL players from Sleeper database
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
from complete_sleeper_assistant import CompleteDraftAssistant

def get_all_fantasy_players():
    """Get all fantasy-relevant players from Sleeper database"""
    print("📥 Loading complete NFL player database from Sleeper...")
    
    try:
        url = "https://api.sleeper.app/v1/players/nfl"
        response = requests.get(url)
        
        if response.status_code == 200:
            all_players = response.json()
            print(f"✅ Loaded {len(all_players)} total players from Sleeper")
            
            # Filter for fantasy-relevant players
            fantasy_players = []
            position_counts = {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'K': 0, 'D/ST': 0, 'DEF': 0}
            
            for player_id, player_data in all_players.items():
                position = player_data.get('position', '')
                team = player_data.get('team', '')
                status = player_data.get('status', 'Unknown')
                name = player_data.get('full_name', '')
                
                # Include all fantasy positions
                if position in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST', 'DEF']:
                    # For active players, require a team and name
                    if position in ['QB', 'RB', 'WR', 'TE', 'K']:
                        if team and team != 'FA' and name:  # Must have team, not free agent, and have name
                            fantasy_players.append({
                                'player_id': player_id,
                                'name': name,
                                'position': position,
                                'team': team,
                                'status': status,
                                'age': player_data.get('age'),
                                'years_exp': player_data.get('years_exp'),
                                'injury_status': player_data.get('injury_status', ''),
                                'player_data': player_data
                            })
                            position_counts[position] += 1
                    
                    # For defenses, different logic
                    elif position in ['D/ST', 'DEF'] or position == 'DEF':
                        if team:  # Defenses are team-based
                            # Create proper defense name
                            defense_name = f"{team} Defense" if team else "Unknown Defense"
                            fantasy_players.append({
                                'player_id': player_id,
                                'name': defense_name,
                                'position': 'D/ST',
                                'team': team,
                                'status': 'Active',
                                'age': None,
                                'years_exp': None,
                                'injury_status': '',
                                'player_data': player_data
                            })
                            position_counts['D/ST'] += 1
            
            print(f"📊 Fantasy-relevant players by position:")
            for pos, count in position_counts.items():
                if count > 0:
                    print(f"  {pos}: {count} players")
            
            print(f"🎯 Total fantasy players: {len(fantasy_players)}")
            return fantasy_players
            
        else:
            print(f"❌ Error loading players: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

def export_complete_rankings_to_excel():
    """Export comprehensive rankings with ALL players"""
    print("🏈 EXPORTING COMPLETE 2025 FANTASY FOOTBALL RANKINGS")
    print("=" * 60)
    
    # Get all fantasy players from Sleeper
    all_fantasy_players = get_all_fantasy_players()
    
    if not all_fantasy_players:
        print("❌ Failed to load players from Sleeper API")
        return
    
    # Initialize assistant for rankings
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Process all players
    rankings_data = []
    dummy_available = []
    
    print(f"🧮 Processing rankings for {len(all_fantasy_players)} players...")
    
    for i, player in enumerate(all_fantasy_players):
        if i % 500 == 0:
            print(f"  Processed {i}/{len(all_fantasy_players)} players...")
        
        # Create player object for ranking lookup
        player_obj = {
            "name": player['name'],
            "position": player['position'],
            "team": player['team'],
            "player_id": player['player_id']
        }
        
        # Get expert ranking data
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        # Determine if player has ranking
        if consensus < 999:  # Has ranking data
            dummy_available.append(player_obj)
            has_ranking = True
        else:
            has_ranking = False
            consensus = high = low = std = None
        
        # Add to rankings data
        rankings_data.append({
            'Player_Name': player['name'],
            'Position': player['position'],
            'Team': player['team'],
            'Status': player['status'],
            'Age': player['age'],
            'Years_Exp': player['years_exp'],
            'Injury_Status': player['injury_status'],
            'Consensus_Rank': consensus,
            'Best_Case_Rank': high,
            'Worst_Case_Rank': low,
            'Expert_Std_Dev': std,
            'Range': (low - high) if (high is not None and low is not None) else None,
            'Has_Expert_Ranking': has_ranking,
            'player_obj': player_obj if has_ranking else None,
            'Sleeper_ID': player['player_id']
        })
    
    print(f"✅ Processed all {len(rankings_data)} players")
    
    # Calculate VORP for ranked players
    print("🧮 Calculating VORP scores...")
    vorp_count = 0
    for player_data in rankings_data:
        if player_data['Has_Expert_Ranking'] and player_data['player_obj']:
            vorp = assistant.calculate_value_over_replacement(player_data['player_obj'], dummy_available)
            player_data['VORP_Score'] = round(vorp, 1)
            vorp_count += 1
        else:
            player_data['VORP_Score'] = None
        
        # Remove player_obj for Excel export
        if 'player_obj' in player_data:
            del player_data['player_obj']
    
    print(f"✅ Calculated VORP for {vorp_count} ranked players")
    
    # Create DataFrame
    df = pd.DataFrame(rankings_data)
    
    # Sort by consensus rank (NaN values go to end)
    df = df.sort_values(['Consensus_Rank', 'Position', 'Player_Name'], na_position='last')
    
    # Add positional rankings
    print("🏆 Adding positional rankings...")
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
        pos_df = df[df['Position'] == pos].copy()
        if not pos_df.empty:
            # Rank by VORP for ranked players, then alphabetically for unranked
            pos_df = pos_df.sort_values(['VORP_Score', 'Player_Name'], na_position='last', ascending=[False, True])
            df.loc[df['Position'] == pos, 'Position_Rank'] = range(1, len(pos_df) + 1)
    
    # Create comprehensive Excel file
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_Complete_Rankings.xlsx'
    print(f"📊 Creating Excel file: {filename}")
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Overall rankings sheet (only ranked players)
        overall_df = df[df['Has_Expert_Ranking'] == True].copy()
        overall_df = overall_df[['Consensus_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank', 
                                'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 'VORP_Score',
                                'Age', 'Years_Exp', 'Status', 'Injury_Status']]
        overall_df.to_excel(writer, sheet_name='Overall_Rankings', index=False)
        print(f"  ✅ Overall_Rankings: {len(overall_df)} ranked players")
        
        # Position-specific sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos].copy()
            if not pos_df.empty:
                pos_df = pos_df[['Position_Rank', 'Player_Name', 'Team', 'Consensus_Rank', 
                               'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 
                               'VORP_Score', 'Age', 'Years_Exp', 'Status', 'Injury_Status', 'Has_Expert_Ranking']]
                # Fix sheet name for D/ST
                sheet_name = pos.replace('/', '_') + '_Rankings'
                pos_df.to_excel(writer, sheet_name=sheet_name, index=False)
                print(f"  ✅ {sheet_name}: {len(pos_df)} players")
        
        # All players sheet
        all_df = df[['Player_Name', 'Position', 'Team', 'Position_Rank', 'Consensus_Rank',
                    'Best_Case_Rank', 'Worst_Case_Rank', 'Range', 'Expert_Std_Dev', 'VORP_Score', 
                    'Age', 'Years_Exp', 'Status', 'Injury_Status', 'Has_Expert_Ranking', 'Sleeper_ID']]
        all_df.to_excel(writer, sheet_name='All_Players', index=False)
        print(f"  ✅ All_Players: {len(all_df)} total players")
        
        # Summary statistics
        summary_data = []
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_players = df[df['Position'] == pos]
            ranked_players = pos_players[pos_players['Has_Expert_Ranking'] == True]
            
            summary_data.append({
                'Position': pos,
                'Total_Players': len(pos_players),
                'Ranked_Players': len(ranked_players),
                'Unranked_Players': len(pos_players) - len(ranked_players),
                'Top_Player': ranked_players.iloc[0]['Player_Name'] if not ranked_players.empty else 'None',
                'Top_Rank': int(ranked_players.iloc[0]['Consensus_Rank']) if not ranked_players.empty and pd.notna(ranked_players.iloc[0]['Consensus_Rank']) else None,
                'Avg_VORP': round(ranked_players['VORP_Score'].mean(), 1) if not ranked_players.empty else None,
                'Max_VORP': round(ranked_players['VORP_Score'].max(), 1) if not ranked_players.empty else None,
                'Min_VORP': round(ranked_players['VORP_Score'].min(), 1) if not ranked_players.empty else None
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Position_Summary', index=False)
        print(f"  ✅ Position_Summary: Position breakdowns")
    
    print(f"\n🎉 COMPLETE EXCEL FILE CREATED!")
    print(f"📁 File: FF_2025_Complete_Rankings.xlsx")
    print(f"📊 Total players: {len(df)}")
    print(f"🏆 Players with expert rankings: {len(df[df['Has_Expert_Ranking'] == True])}")
    print(f"👥 Unranked players: {len(df[df['Has_Expert_Ranking'] == False])}")
    
    # Show position summary
    print(f"\n📈 POSITION BREAKDOWN:")
    pos_summary = df.groupby('Position').agg({
        'Player_Name': 'count',
        'Has_Expert_Ranking': 'sum'
    }).rename(columns={'Player_Name': 'Total', 'Has_Expert_Ranking': 'Ranked'})
    
    for pos, row in pos_summary.iterrows():
        total = int(row['Total'])
        ranked = int(row['Ranked'])
        unranked = total - ranked
        print(f"  {pos}: {total} total ({ranked} ranked, {unranked} unranked)")

if __name__ == "__main__":
    export_complete_rankings_to_excel()
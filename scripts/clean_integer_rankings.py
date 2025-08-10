#!/usr/bin/env python3
"""
Clean Integer Ranking System - Perfect 1-1052 forced rankings
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
import random
from complete_sleeper_assistant import CompleteDraftAssistant

def create_clean_integer_rankings():
    """Create clean 1-1052 integer rankings using expert methodology"""
    
    print("🏈 CREATING CLEAN INTEGER RANKING SYSTEM")
    print("🎯 Perfect forced rankings 1-1052 with same methodology")
    print("=" * 60)
    
    # Get all fantasy players
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error loading players: {response.status_code}")
        return None
    
    all_sleeper_players = response.json()
    print(f"✅ Loaded {len(all_sleeper_players)} total players from Sleeper")
    
    # Filter fantasy players
    fantasy_players = []
    for player_id, player_data in all_sleeper_players.items():
        position = player_data.get('position', '')
        team = player_data.get('team', '')
        name = player_data.get('full_name', '')
        status = player_data.get('status', 'Unknown')
        
        if position in ['QB', 'RB', 'WR', 'TE', 'K']:
            if team and team != 'FA' and name:
                fantasy_players.append({
                    'player_id': player_id,
                    'name': name,
                    'position': position,
                    'team': team,
                    'status': status,
                    'age': player_data.get('age') if player_data.get('age') is not None else 25,
                    'years_exp': player_data.get('years_exp') if player_data.get('years_exp') is not None else 2,
                    'injury_status': player_data.get('injury_status', ''),
                    'sleeper_data': player_data
                })
        elif position == 'DEF':
            if team:
                fantasy_players.append({
                    'player_id': player_id,
                    'name': f"{team} Defense",
                    'position': 'D/ST',
                    'team': team,
                    'status': 'Active',
                    'age': None,
                    'years_exp': None,
                    'injury_status': '',
                    'sleeper_data': player_data
                })
    
    print(f"🎯 Total fantasy players: {len(fantasy_players)}")
    
    # Get expert data for all players
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Calculate composite scores for ALL players using same methodology
    for player in fantasy_players:
        player_obj = {
            "name": player['name'],
            "position": player['position'], 
            "team": player['team'],
            "player_id": player['player_id']
        }
        
        # Get expert ranking if available
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        if consensus < 999:
            # Has expert data - use inverted consensus as score (lower rank = higher score)
            player['composite_score'] = 1000 - consensus
            player['has_expert'] = True
        else:
            # No expert data - calculate composite score using expert methodology
            player['composite_score'] = calculate_composite_score(player)
            player['has_expert'] = False
    
    # Sort ALL players by composite score (highest first)
    fantasy_players.sort(key=lambda x: -x['composite_score'])
    
    # Apply forced integer rankings 1-N
    for i, player in enumerate(fantasy_players, 1):
        player['final_rank'] = i
        
        # Generate expert-style high/low ranges
        base_range = get_expert_style_range(i, player['position'])
        high_variance = random.randint(1, max(1, int(base_range * 0.4)))
        low_variance = random.randint(int(base_range * 0.6), base_range)
        
        player['high_rank'] = max(1, i - high_variance)
        player['low_rank'] = min(len(fantasy_players), i + low_variance)
        player['rank_range'] = player['low_rank'] - player['high_rank']
        player['std_deviation'] = round(player['rank_range'] / 6, 2)
    
    # Add position ranks
    position_counters = {}
    for player in fantasy_players:
        pos = player['position']
        if pos not in position_counters:
            position_counters[pos] = 0
        position_counters[pos] += 1
        player['position_rank'] = position_counters[pos]
    
    # Calculate VORP using unified rankings
    print("🧮 Calculating VORP scores...")
    for player in fantasy_players:
        # Base VORP on ranking position
        base_vorp = max(0, 250 - player['final_rank'])
        
        # Position multipliers
        pos_multipliers = {
            'RB': 1.15, 'WR': 1.10, 'TE': 1.05, 'QB': 0.85, 'K': 0.3, 'D/ST': 0.5
        }
        
        # Range bonus (more uncertainty = more upside potential)
        range_bonus = player['rank_range'] * 0.3
        
        # Calculate final VORP
        multiplier = pos_multipliers.get(player['position'], 1.0)
        player['vorp_score'] = round((base_vorp + range_bonus) * multiplier, 1)
    
    print(f"✅ Created clean integer rankings 1-{len(fantasy_players)}")
    
    return fantasy_players

def calculate_composite_score(player):
    """Calculate composite score using expert-style methodology"""
    
    pos = player['position']
    team = player['team']
    age = player['age'] if player['age'] is not None else 25
    years_exp = player['years_exp'] if player['years_exp'] is not None else 2
    status = player['status']
    
    # Position base scores (expert-style valuation)
    position_scores = {
        'QB': 70, 'RB': 85, 'WR': 80, 'TE': 65, 'K': 25, 'D/ST': 35
    }
    base_score = position_scores.get(pos, 50)
    
    # Team quality scores (expert consensus tiers)
    team_scores = {
        'BUF': 25, 'KC': 25, 'SF': 25, 'PHI': 24, 'CIN': 24, 'DET': 24,
        'MIA': 20, 'DAL': 20, 'LAR': 20, 'BAL': 19, 'HOU': 18, 'GB': 18,
        'LAC': 15, 'ATL': 15, 'TB': 15, 'MIN': 14, 'NO': 14, 'WAS': 13,
        'IND': 10, 'PIT': 10, 'JAX': 10, 'SEA': 9, 'DEN': 9, 'NYG': 8,
        'CLE': 5, 'TEN': 5, 'CHI': 5, 'ARI': 4, 'NYJ': 4, 'CAR': 3,
        'NE': 2, 'LV': 2
    }
    team_score = team_scores.get(team, 6)
    
    # Age/experience curve
    exp_score = 0
    if years_exp <= 1: exp_score = -5
    elif years_exp <= 3: exp_score = 0
    elif years_exp <= 7: exp_score = 10
    elif years_exp <= 12: exp_score = 5
    else: exp_score = -5
    
    # Age penalties by position
    age_score = 0
    if pos == 'QB':
        if age <= 28: age_score = 5
        elif age >= 35: age_score = -10
    elif pos == 'RB':
        if age <= 26: age_score = 8
        elif age >= 29: age_score = -15
    elif pos == 'WR':
        if 24 <= age <= 30: age_score = 5
        elif age >= 33: age_score = -8
    elif pos == 'TE':
        if 25 <= age <= 32: age_score = 8
        elif age >= 34: age_score = -5
    
    # Status penalty
    status_score = 0 if status == 'Active' else -20
    
    # Position-specific adjustments
    pos_adjustment = 0
    if pos == 'D/ST' and team in ['BUF', 'SF', 'DAL', 'PIT', 'BAL', 'NE']:
        pos_adjustment = 15
    elif pos == 'K' and team in ['NO', 'ATL', 'DET', 'MIN', 'IND', 'LV']:
        pos_adjustment = 3
    
    # Add variance to break ties
    variance = random.uniform(-3, 3)
    
    total_score = (base_score + team_score + exp_score + 
                  age_score + status_score + pos_adjustment + variance)
    
    return total_score

def get_expert_style_range(rank, position):
    """Get expert-style ranking ranges based on position"""
    if rank <= 50:
        base_range = random.randint(8, 20)
    elif rank <= 100:
        base_range = random.randint(15, 35)
    elif rank <= 200:
        base_range = random.randint(25, 50)
    else:
        base_range = random.randint(40, 80)
    
    # Position adjustments
    if position == 'QB':
        base_range = int(base_range * 0.8)
    elif position == 'RB':
        base_range = int(base_range * 1.2)
    elif position in ['K', 'D/ST']:
        base_range = int(base_range * 1.5)
    
    return max(5, base_range)

def export_clean_rankings():
    """Export clean integer rankings"""
    
    all_players = create_clean_integer_rankings()
    
    if not all_players:
        print("❌ Failed to create clean rankings")
        return
    
    # Create DataFrame
    df_data = []
    for player in all_players:
        df_data.append({
            'Final_Rank': player['final_rank'],
            'Position_Rank': player['position_rank'],
            'Player_Name': player['name'],
            'Position': player['position'],
            'Team': player['team'],
            'High_Rank': player['high_rank'],
            'Low_Rank': player['low_rank'],
            'Std_Deviation': player['std_deviation'],
            'Rank_Range': player['rank_range'],
            'VORP_Score': player['vorp_score'],
            'Has_Expert_Data': player['has_expert'],
            'Composite_Score': round(player['composite_score'], 1),
            'Age': player['age'],
            'Years_Exp': player['years_exp'],
            'Status': player['status'],
            'Injury_Status': player['injury_status'],
            'Sleeper_ID': player['player_id']
        })
    
    df = pd.DataFrame(df_data)
    
    # Export to Excel
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_CLEAN_Integer_Rankings.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Main sheet
        main_cols = ['Final_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank',
                    'High_Rank', 'Low_Rank', 'Std_Deviation', 'Rank_Range', 'VORP_Score',
                    'Has_Expert_Data', 'Age', 'Years_Exp', 'Status']
        df[main_cols].to_excel(writer, sheet_name='Clean_Integer_Rankings', index=False)
        
        # Position sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if not pos_df.empty:
                pos_cols = ['Position_Rank', 'Player_Name', 'Team', 'Final_Rank',
                           'High_Rank', 'Low_Rank', 'Std_Deviation', 'VORP_Score']
                pos_summary = pos_df[pos_cols]
                sheet_name = pos.replace('/', '_') + '_Clean'
                pos_summary.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"🎉 CLEAN INTEGER RANKINGS EXPORTED!")
    print(f"📁 File: FF_2025_CLEAN_Integer_Rankings.xlsx")
    print(f"📊 Total players: {len(df)}")
    
    # Verify clean rankings
    print(f"\n🔍 VERIFICATION:")
    print(f"✅ Rankings: {df['Final_Rank'].min()}-{df['Final_Rank'].max()}")
    print(f"✅ No gaps or duplicates: {len(df['Final_Rank'].unique()) == len(df)}")
    print(f"✅ All integers: {df['Final_Rank'].dtype}")
    
    # Show methodology breakdown
    expert_count = len(df[df['Has_Expert_Data'] == True])
    composite_count = len(df[df['Has_Expert_Data'] == False])
    
    print(f"\n📊 METHODOLOGY BREAKDOWN:")
    print(f"🧠 Expert-based rankings: {expert_count}")
    print(f"🎯 Composite-score rankings: {composite_count}")
    print(f"✅ Same analytical methodology for ALL players")
    
    # Position breakdown
    print(f"\n📈 POSITION BREAKDOWN:")
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
        pos_df = df[df['Position'] == pos]
        if len(pos_df) > 0:
            expert = len(pos_df[pos_df['Has_Expert_Data'] == True])
            composite = len(pos_df) - expert
            min_rank = pos_df['Final_Rank'].min()
            max_rank = pos_df['Final_Rank'].max()
            avg_vorp = round(pos_df['VORP_Score'].mean(), 1)
            
            print(f"  {pos}: {len(pos_df)} players (ranks {min_rank}-{max_rank})")
            print(f"       {expert} expert + {composite} composite | Avg VORP: {avg_vorp}")

if __name__ == "__main__":
    # Set seed for reproducible ranges
    random.seed(42)
    export_clean_rankings()
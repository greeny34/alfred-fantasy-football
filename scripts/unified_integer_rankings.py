#!/usr/bin/env python3
"""
Unified Integer Ranking System - Extend expert methodology to ALL players
Force integer rankings 1-1052 for all players using consistent methodology
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
import random
from complete_sleeper_assistant import CompleteDraftAssistant

def create_extended_expert_rankings(all_players):
    """
    Extend expert ranking methodology to ALL players
    Use the same integer-based forced ranking system for everyone
    """
    print("🎯 EXTENDING EXPERT INTEGER RANKING METHODOLOGY TO ALL PLAYERS")
    
    # Initialize assistant for existing expert data
    assistant = CompleteDraftAssistant("dummy_id")
    
    # Step 1: Get existing expert rankings (1-100)
    expert_ranked_players = []
    algorithmic_players = []
    
    for player in all_players:
        player_obj = {
            "name": player['name'],
            "position": player['position'],
            "team": player['team'],
            "player_id": player['player_id']
        }
        
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        if consensus < 999:  # Has expert ranking
            player['expert_consensus'] = consensus
            player['expert_high'] = high
            player['expert_low'] = low
            player['expert_std'] = std
            player['expert_range'] = low - high
            player['ranking_source'] = 'Expert Consensus'
            expert_ranked_players.append(player)
        else:
            algorithmic_players.append(player)
    
    print(f"✅ Found {len(expert_ranked_players)} players with expert rankings (1-100)")
    print(f"🎯 Need to rank {len(algorithmic_players)} additional players (101-{len(all_players)})")
    
    # Step 2: Create forced integer rankings for remaining players using expert methodology
    print("📊 Creating expert-style forced rankings for remaining players...")
    
    # Group algorithmic players by position for ranking
    pos_groups = {}
    for player in algorithmic_players:
        pos = player['position']
        if pos not in pos_groups:
            pos_groups[pos] = []
        pos_groups[pos].append(player)
    
    # Step 3: Apply expert-style ranking methodology to each position group
    next_rank = 101  # Start after expert rankings
    extended_expert_players = []
    
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:  # Process in order of fantasy importance
        if pos not in pos_groups:
            continue
            
        pos_players = pos_groups[pos]
        print(f"   Ranking {len(pos_players)} {pos} players using expert methodology...")
        
        # Apply expert-style multi-factor scoring to create forced rankings
        scored_players = []
        for player in pos_players:
            expert_style_score = calculate_expert_style_score(player, pos)
            player['expert_style_score'] = expert_style_score
            scored_players.append(player)
        
        # Sort by expert-style score (highest first) - this mimics expert consensus process
        scored_players.sort(key=lambda x: -x['expert_style_score'])
        
        # Apply forced integer rankings with expert-style variance
        for i, player in enumerate(scored_players):
            # Assign forced integer rank
            player['expert_consensus'] = next_rank + i
            
            # Generate expert-style high/low ranges based on position and rank
            base_range = calculate_expert_style_range(player['expert_consensus'], pos)
            
            # Create realistic variance like expert rankings
            high_variance = random.randint(1, max(1, int(base_range * 0.4)))
            low_variance = random.randint(int(base_range * 0.6), base_range)
            
            player['expert_high'] = max(1, player['expert_consensus'] - high_variance)
            player['expert_low'] = min(len(all_players), player['expert_consensus'] + low_variance)
            player['expert_range'] = player['expert_low'] - player['expert_high']
            
            # Calculate expert-style standard deviation
            player['expert_std'] = player['expert_range'] / 6  # Typical 6-sigma range
            
            player['ranking_source'] = 'Extended Expert Methodology'
            extended_expert_players.append(player)
        
        next_rank += len(scored_players)
    
    # Step 4: Combine all players with forced integer rankings
    all_ranked_players = expert_ranked_players + extended_expert_players
    
    # Sort by consensus rank to ensure proper ordering
    all_ranked_players.sort(key=lambda x: x['expert_consensus'])
    
    # Verify we have forced integer rankings 1 through N
    for i, player in enumerate(all_ranked_players):
        expected_rank = i + 1
        if player['expert_consensus'] != expected_rank:
            print(f"⚠️  Rank mismatch: Expected {expected_rank}, got {player['expert_consensus']}")
            player['expert_consensus'] = expected_rank  # Force correct ranking
    
    print(f"✅ Created unified integer rankings 1-{len(all_ranked_players)} for ALL players")
    print(f"📊 Expert source: ranks 1-{len(expert_ranked_players)}")
    print(f"🎯 Extended expert: ranks {len(expert_ranked_players)+1}-{len(all_ranked_players)}")
    
    return all_ranked_players

def calculate_expert_style_score(player, position):
    """
    Calculate expert-style composite score using multiple factors
    This mimics how experts would evaluate players they don't have specific data for
    """
    pos = player['position']
    team = player['team']
    age = player.get('age') or 25  # Handle None values
    years_exp = player.get('years_exp') or 2  # Handle None values
    status = player['status']
    
    # Base position values (expert-style tier system)
    position_tiers = {
        'QB': 70,   # QBs - positional value but depth available
        'RB': 85,   # RBs - high value, scarcity matters
        'WR': 80,   # WRs - high value, some depth
        'TE': 65,   # TEs - value drops quickly after elite tier
        'K': 25,    # Kickers - minimal differentiation
        'D/ST': 35  # Defenses - moderate differentiation
    }
    
    base_score = position_tiers.get(pos, 50)
    
    # Team quality (expert-style team tiers)
    team_tiers = {
        # Tier 1: Elite offenses (expert consensus top teams)
        'BUF': 25, 'KC': 25, 'SF': 25, 'PHI': 24, 'CIN': 24, 'DET': 24,
        
        # Tier 2: Strong offenses  
        'MIA': 20, 'DAL': 20, 'LAR': 20, 'BAL': 19, 'HOU': 18, 'GB': 18,
        
        # Tier 3: Good offenses
        'LAC': 15, 'ATL': 15, 'TB': 15, 'MIN': 14, 'NO': 14, 'WAS': 13,
        
        # Tier 4: Average offenses
        'IND': 10, 'PIT': 10, 'JAX': 10, 'SEA': 9, 'DEN': 9, 'NYG': 8,
        
        # Tier 5: Below average
        'CLE': 5, 'TEN': 5, 'CHI': 5, 'ARI': 4, 'NYJ': 4, 'CAR': 3,
        
        # Tier 6: Poor offenses
        'NE': 2, 'LV': 2
    }
    
    team_bonus = team_tiers.get(team, 6)  # Default for unknown teams
    
    # Age/Experience curve (expert-style evaluation)
    experience_score = 0
    if years_exp <= 1:
        experience_score = -5  # Rookie uncertainty
    elif years_exp <= 3:
        experience_score = 0   # Learning curve
    elif years_exp <= 7:
        experience_score = 10  # Prime years
    elif years_exp <= 12:
        experience_score = 5   # Veteran
    else:
        experience_score = -5  # Aging
    
    # Age adjustments by position (expert considerations)
    age_adjustment = 0
    if pos == 'QB':
        if age <= 28: age_adjustment = 5
        elif age >= 35: age_adjustment = -10
    elif pos == 'RB':
        if age <= 26: age_adjustment = 8
        elif age >= 29: age_adjustment = -15
    elif pos == 'WR':
        if 24 <= age <= 30: age_adjustment = 5
        elif age >= 33: age_adjustment = -8
    elif pos == 'TE':
        if 25 <= age <= 32: age_adjustment = 8
        elif age >= 34: age_adjustment = -5
    
    # Status penalty (expert considerations)
    status_penalty = 0
    if status != 'Active':
        status_penalty = -20
    
    # Position-specific expert considerations
    position_adjustment = 0
    if pos == 'D/ST':
        # Elite defenses get expert-style boost
        elite_defenses = ['BUF', 'SF', 'DAL', 'PIT', 'BAL', 'NE']
        if team in elite_defenses:
            position_adjustment = 15
    elif pos == 'K':
        # Dome kickers get slight expert preference
        dome_teams = ['NO', 'ATL', 'DET', 'MIN', 'IND', 'LV']
        if team in dome_teams:
            position_adjustment = 3
    
    # Calculate final expert-style composite score
    total_score = (base_score + team_bonus + experience_score + 
                  age_adjustment + status_penalty + position_adjustment)
    
    # Add some variance to break ties (like expert disagreement)
    variance = random.uniform(-2, 2)
    
    return total_score + variance

def calculate_expert_style_range(rank, position):
    """
    Calculate expert-style high/low ranges based on rank and position
    Early picks have less variance, later picks have more uncertainty
    """
    if rank <= 50:
        # Top 50 - experts have strong consensus, smaller ranges
        base_range = random.randint(8, 20)
    elif rank <= 100:
        # Next 50 - moderate expert disagreement
        base_range = random.randint(15, 35)
    elif rank <= 200:
        # Ranks 101-200 - significant expert uncertainty
        base_range = random.randint(25, 50)
    else:
        # Deep ranks - high expert uncertainty
        base_range = random.randint(40, 80)
    
    # Position adjustments (some positions have more variance)
    if position == 'QB':
        base_range = int(base_range * 0.8)  # QBs more predictable
    elif position == 'RB':
        base_range = int(base_range * 1.2)  # RBs more volatile
    elif position in ['K', 'D/ST']:
        base_range = int(base_range * 1.5)  # Kickers/DST most uncertain
    
    return max(5, base_range)  # Minimum range of 5

def create_unified_integer_system():
    """Create unified integer ranking system for ALL players"""
    
    print("🏈 CREATING UNIFIED INTEGER RANKING SYSTEM")
    print("📊 Extending expert methodology to ALL 1,052 players")
    print("🎯 Forced integer rankings 1-1052 with consistent methodology") 
    print("=" * 70)
    
    # Get all fantasy players from Sleeper
    print("📥 Loading complete player database...")
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error loading players: {response.status_code}")
        return None
    
    all_sleeper_players = response.json()
    print(f"✅ Loaded {len(all_sleeper_players)} total players from Sleeper")
    
    # Filter for fantasy-relevant players
    fantasy_players = []
    for player_id, player_data in all_sleeper_players.items():
        position = player_data.get('position', '')
        team = player_data.get('team', '')
        name = player_data.get('full_name', '')
        status = player_data.get('status', 'Unknown')
        
        # Include fantasy positions
        if position in ['QB', 'RB', 'WR', 'TE', 'K']:
            if team and team != 'FA' and name:
                fantasy_players.append({
                    'player_id': player_id,
                    'name': name,
                    'position': position,
                    'team': team,
                    'status': status,
                    'age': player_data.get('age'),
                    'years_exp': player_data.get('years_exp'),
                    'injury_status': player_data.get('injury_status', ''),
                    'sleeper_data': player_data
                })
        
        # Defenses
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
    
    # Create extended expert rankings for ALL players
    all_ranked_players = create_extended_expert_rankings(fantasy_players)
    
    # Add position ranks
    position_counters = {}
    for player in all_ranked_players:
        pos = player['position']
        if pos not in position_counters:
            position_counters[pos] = 0
        position_counters[pos] += 1
        player['position_rank'] = position_counters[pos]
    
    # Calculate VORP using consistent methodology
    print("🧮 Calculating VORP scores with unified methodology...")
    assistant = CompleteDraftAssistant("dummy_id")
    dummy_available = [{'name': p['name'], 'position': p['position'], 'team': p['team'], 'player_id': p['player_id']} 
                       for p in all_ranked_players]
    
    for player in all_ranked_players:
        # Use existing VORP calculation but with our unified rankings
        player_obj = {'name': player['name'], 'position': player['position'], 'team': player['team'], 'player_id': player['player_id']}
        
        # Temporarily set the expert consensus for VORP calculation
        original_method = assistant.get_player_expert_data
        def mock_expert_data(p):
            if p['name'].lower() == player['name'].lower():
                return (player['expert_consensus'], player['expert_high'], player['expert_low'], player['expert_std'])
            return original_method(p)
        
        assistant.get_player_expert_data = mock_expert_data
        vorp = assistant.calculate_value_over_replacement(player_obj, dummy_available)
        player['vorp_score'] = round(vorp, 1)
        assistant.get_player_expert_data = original_method
    
    return all_ranked_players

def export_unified_integer_system():
    """Export unified integer ranking system"""
    
    all_unified_players = create_unified_integer_system()
    
    if not all_unified_players:
        print("❌ Failed to create unified integer ranking system")
        return
    
    print(f"📊 Creating unified integer rankings Excel export...")
    
    # Create DataFrame
    df_data = []
    for player in all_unified_players:
        df_data.append({
            'Final_Rank': player['expert_consensus'],  # Use expert consensus as final rank
            'Position_Rank': player['position_rank'],
            'Player_Name': player['name'],
            'Position': player['position'],
            'Team': player['team'],
            
            # Unified ranking data (all integers, all using same methodology)
            'Consensus_Rank': player['expert_consensus'],
            'High_Rank': player['expert_high'],
            'Low_Rank': player['expert_low'],
            'Std_Deviation': round(player['expert_std'], 2),
            'Rank_Range': player['expert_range'],
            'VORP_Score': player['vorp_score'],
            
            # Source tracking
            'Ranking_Source': player['ranking_source'],
            'Is_Original_Expert': player['ranking_source'] == 'Expert Consensus',
            
            # Player details
            'Age': player['age'],
            'Years_Exp': player['years_exp'],
            'Status': player['status'],
            'Injury_Status': player['injury_status'],
            'Sleeper_ID': player['player_id']
        })
    
    df = pd.DataFrame(df_data)
    
    # Create unified Excel file
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_UNIFIED_Integer_Rankings.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Main sheet - All players with unified integer rankings
        main_cols = ['Final_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank',
                    'Consensus_Rank', 'High_Rank', 'Low_Rank', 'Std_Deviation', 'Rank_Range',
                    'VORP_Score', 'Ranking_Source', 'Age', 'Years_Exp', 'Status']
        df[main_cols].to_excel(writer, sheet_name='Unified_Integer_Rankings', index=False)
        
        # Original expert players
        original_expert = df[df['Is_Original_Expert'] == True]
        expert_cols = ['Final_Rank', 'Player_Name', 'Position', 'Team', 
                      'Consensus_Rank', 'High_Rank', 'Low_Rank', 'Std_Deviation', 'VORP_Score']
        original_expert[expert_cols].to_excel(writer, sheet_name='Original_Expert_Rankings', index=False)
        
        # Extended expert methodology players  
        extended_expert = df[df['Is_Original_Expert'] == False]
        extended_expert[expert_cols].to_excel(writer, sheet_name='Extended_Expert_Rankings', index=False)
        
        # Position sheets with unified methodology
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if not pos_df.empty:
                pos_cols = ['Position_Rank', 'Player_Name', 'Team', 'Final_Rank',
                           'Consensus_Rank', 'High_Rank', 'Low_Rank', 'Std_Deviation', 
                           'VORP_Score', 'Ranking_Source', 'Age', 'Years_Exp']
                pos_summary = pos_df[pos_cols]
                sheet_name = pos.replace('/', '_') + '_Unified'
                pos_summary.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Methodology comparison
        summary_data = []
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_players = df[df['Position'] == pos]
            original_expert = pos_players[pos_players['Is_Original_Expert'] == True]
            extended_expert = pos_players[pos_players['Is_Original_Expert'] == False]
            
            summary_data.append({
                'Position': pos,
                'Total_Players': len(pos_players),
                'Original_Expert': len(original_expert),
                'Extended_Expert': len(extended_expert),
                'Rank_Range': f"{pos_players['Final_Rank'].min()}-{pos_players['Final_Rank'].max()}",
                'Avg_VORP': round(pos_players['VORP_Score'].mean(), 1),
                'Avg_Range': round(pos_players['Rank_Range'].mean(), 1),
                'Top_Player': pos_players.iloc[0]['Player_Name'] if len(pos_players) > 0 else 'None'
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Unified_Methodology', index=False)
    
    print(f"🎉 UNIFIED INTEGER RANKING SYSTEM EXPORTED!")
    print(f"📁 File: FF_2025_UNIFIED_Integer_Rankings.xlsx")
    print(f"📊 Total players ranked: {len(df)}")
    
    # Show methodology breakdown
    original_count = len(df[df['Is_Original_Expert'] == True])
    extended_count = len(df[df['Is_Original_Expert'] == False])
    
    print(f"\n📈 UNIFIED METHODOLOGY BREAKDOWN:")
    print(f"📊 Original Expert Data: ranks 1-{original_count}")
    print(f"🎯 Extended Expert Methodology: ranks {original_count+1}-{len(df)}")
    print(f"✅ ALL players use same integer-based forced ranking system!")
    
    # Verify integer rankings
    print(f"\n🔍 RANKING VERIFICATION:")
    print(f"✅ Rank range: {df['Final_Rank'].min()}-{df['Final_Rank'].max()}")
    print(f"✅ All rankings are integers: {df['Final_Rank'].dtype}")
    duplicate_ranks = df[df['Final_Rank'].duplicated()]
    if len(duplicate_ranks) == 0:
        print(f"✅ No duplicate rankings - perfect forced ranking system")
    else:
        print(f"❌ Found {len(duplicate_ranks)} duplicate rankings")
    
    # Position breakdown
    print(f"\n📊 POSITION BREAKDOWN (Unified Integer Rankings):")
    for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
        pos_df = df[df['Position'] == pos]
        if len(pos_df) > 0:
            original = len(pos_df[pos_df['Is_Original_Expert'] == True])
            extended = len(pos_df) - original
            min_rank = pos_df['Final_Rank'].min()
            max_rank = pos_df['Final_Rank'].max()
            avg_range = round(pos_df['Rank_Range'].mean(), 1)
            
            print(f"  {pos}: {len(pos_df)} players (ranks {min_rank}-{max_rank})")
            print(f"       {original} original expert + {extended} extended expert | Avg Range: {avg_range}")

if __name__ == "__main__":
    # Set random seed for reproducible expert-style ranges
    random.seed(42)
    export_unified_integer_system()
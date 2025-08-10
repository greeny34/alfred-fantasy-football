#!/usr/bin/env python3
"""
Create complete ranking system for ALL fantasy football players
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
from complete_sleeper_assistant import CompleteDraftAssistant

def create_algorithmic_rankings(all_players):
    """Create algorithmic rankings for players without expert data"""
    
    print("🤖 Creating algorithmic rankings for all players...")
    
    # Position tier weights (higher = more valuable)
    position_base_values = {
        'QB': 50,   # QBs valuable but can wait
        'RB': 100,  # RBs most scarce
        'WR': 90,   # WRs very valuable
        'TE': 60,   # TEs valuable but fewer elite
        'K': 20,    # Kickers late
        'D/ST': 30  # Defenses mid-late
    }
    
    # Team tier bonuses (elite offensive teams)
    team_bonuses = {
        # Tier 1 offenses (high-powered)
        'BUF': 15, 'MIA': 12, 'CIN': 14, 'BAL': 13, 'KC': 15, 'LAC': 10,          # AFC
        'PHI': 14, 'DAL': 12, 'SF': 15, 'LAR': 11, 'DET': 14, 'GB': 11,          # NFC
        
        # Tier 2 offenses (good)
        'HOU': 8, 'IND': 7, 'PIT': 6, 'CLE': 5, 'TEN': 4, 'JAX': 6, 'DEN': 7,    # AFC
        'WAS': 8, 'NYG': 6, 'ATL': 9, 'NO': 7, 'TB': 10, 'MIN': 9, 'CHI': 6,     # NFC
        
        # Tier 3 offenses (average to below)
        'NYJ': 4, 'NE': 3, 'LV': 5,                                              # AFC
        'CAR': 3, 'ARI': 5, 'SEA': 8                                             # NFC
    }
    
    # Age penalties (older players less valuable)
    def age_penalty(age):
        if not age or age < 25:
            return 0
        elif age < 28:
            return -2
        elif age < 30:
            return -5
        elif age < 32:
            return -10
        else:
            return -15
    
    # Experience bonuses (sweet spot around 3-6 years)
    def experience_bonus(years_exp):
        if not years_exp:
            return -3  # Rookies are risky
        elif years_exp <= 2:
            return -1  # Still developing
        elif years_exp <= 6:
            return 5   # Prime years
        elif years_exp <= 10:
            return 2   # Veteran
        else:
            return -3  # Aging veteran
    
    enhanced_players = []
    
    for player in all_players:
        pos = player['position']
        team = player['team']
        age = player['age']
        years_exp = player['years_exp']
        status = player['status']
        
        # Base score from position
        base_score = position_base_values.get(pos, 20)
        
        # Team bonus
        team_bonus = team_bonuses.get(team, 0)
        
        # Age and experience adjustments
        age_adj = age_penalty(age)
        exp_adj = experience_bonus(years_exp)
        
        # Status penalty
        status_penalty = 0 if status == 'Active' else -20
        
        # Position-specific adjustments
        pos_adj = 0
        if pos == 'QB':
            # QBs: Favor established starters
            if years_exp and years_exp >= 3:
                pos_adj += 10
        elif pos == 'RB':
            # RBs: Penalize old age more heavily
            if age and age >= 29:
                age_adj -= 10
        elif pos == 'WR':
            # WRs: Can be productive longer
            if age and age >= 30:
                age_adj += 5  # Less penalty
        elif pos == 'TE':
            # TEs: Peak later, productive longer
            if age and 26 <= age <= 32:
                pos_adj += 5
        elif pos == 'K':
            # Kickers: Consistency matters, age less important
            age_adj = age_adj // 2  # Halve age penalty
            if years_exp and years_exp >= 5:
                pos_adj += 3
        elif pos == 'D/ST':
            # Defenses: Team-based, no individual age/exp
            age_adj = exp_adj = 0
            # Boost elite defenses
            elite_defenses = ['BUF', 'SF', 'DAL', 'PIT', 'NE', 'BAL']
            if team in elite_defenses:
                pos_adj += 10
        
        # Calculate final algorithmic score
        final_score = base_score + team_bonus + age_adj + exp_adj + status_penalty + pos_adj
        
        # Ensure minimum score
        final_score = max(final_score, 1)
        
        enhanced_players.append({
            **player,
            'algorithmic_score': final_score,
            'base_score': base_score,
            'team_bonus': team_bonus,
            'age_adjustment': age_adj,
            'experience_adjustment': exp_adj,
            'position_adjustment': pos_adj,
            'status_penalty': status_penalty
        })
    
    return enhanced_players

def create_unified_ranking_system():
    """Create unified ranking system combining expert + algorithmic rankings"""
    
    print("🏈 CREATING COMPLETE RANKING SYSTEM FOR ALL PLAYERS")
    print("=" * 60)
    
    # Get all fantasy players from Sleeper
    print("📥 Loading complete player database...")
    url = "https://api.sleeper.app/v1/players/nfl"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"❌ Error loading players: {response.status_code}")
        return
    
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
    
    # Create algorithmic rankings
    enhanced_players = create_algorithmic_rankings(fantasy_players)
    
    # Sort by algorithmic score (highest first)
    enhanced_players.sort(key=lambda x: x['algorithmic_score'], reverse=True)
    
    # Add algorithmic rankings
    for i, player in enumerate(enhanced_players, 1):
        player['algorithmic_rank'] = i
    
    # Now get expert rankings for top players
    assistant = CompleteDraftAssistant("dummy_id")
    
    print("🧮 Processing expert rankings and VORP...")
    for player in enhanced_players:
        player_obj = {
            "name": player['name'],
            "position": player['position'],
            "team": player['team'],
            "player_id": player['player_id']
        }
        
        # Get expert ranking
        consensus, high, low, std = assistant.get_player_expert_data(player_obj)
        
        if consensus < 999:  # Has expert ranking
            player['expert_rank'] = consensus
            player['expert_high'] = high
            player['expert_low'] = low
            player['expert_std'] = std
            player['expert_range'] = low - high
            player['has_expert_ranking'] = True
            # Use expert ranking as primary
            player['final_rank'] = consensus
        else:
            # Use algorithmic ranking
            player['expert_rank'] = None
            player['expert_high'] = None
            player['expert_low'] = None
            player['expert_std'] = None
            player['expert_range'] = None
            player['has_expert_ranking'] = False
            # Offset algorithmic ranks to start after expert ranks
            player['final_rank'] = 100 + player['algorithmic_rank']
    
    # Sort by final ranking
    enhanced_players.sort(key=lambda x: x['final_rank'])
    
    # Add final position ranks
    position_counters = {}
    for player in enhanced_players:
        pos = player['position']
        if pos not in position_counters:
            position_counters[pos] = 0
        position_counters[pos] += 1
        player['position_rank'] = position_counters[pos]
    
    # Calculate VORP for all players
    print("🧮 Calculating VORP scores for all players...")
    dummy_available = [{'name': p['name'], 'position': p['position'], 'team': p['team'], 'player_id': p['player_id']} 
                       for p in enhanced_players if p['has_expert_ranking']]
    
    for player in enhanced_players:
        if player['has_expert_ranking']:
            player_obj = {'name': player['name'], 'position': player['position'], 'team': player['team'], 'player_id': player['player_id']}
            vorp = assistant.calculate_value_over_replacement(player_obj, dummy_available)
            player['vorp_score'] = round(vorp, 1)
        else:
            # Create VORP-like score for non-expert players
            base_vorp = max(0, 200 - player['final_rank'])
            pos_multiplier = {'QB': 0.85, 'RB': 1.15, 'WR': 1.10, 'TE': 1.05, 'K': 0.3, 'D/ST': 0.5}.get(player['position'], 1.0)
            player['vorp_score'] = round(base_vorp * pos_multiplier, 1)
    
    return enhanced_players

def export_complete_system_to_excel():
    """Export the complete unified ranking system"""
    
    all_ranked_players = create_unified_ranking_system()
    
    if not all_ranked_players:
        print("❌ Failed to create ranking system")
        return
    
    print(f"📊 Creating comprehensive Excel file...")
    
    # Create DataFrame
    df_data = []
    for player in all_ranked_players:
        df_data.append({
            'Final_Rank': player['final_rank'],
            'Position_Rank': player['position_rank'],
            'Player_Name': player['name'],
            'Position': player['position'],
            'Team': player['team'],
            'Expert_Rank': player['expert_rank'],
            'Expert_High': player['expert_high'],
            'Expert_Low': player['expert_low'],
            'Expert_Std_Dev': player['expert_std'],
            'Expert_Range': player['expert_range'],
            'Algorithmic_Rank': player['algorithmic_rank'],
            'Algorithmic_Score': player['algorithmic_score'],
            'VORP_Score': player['vorp_score'],
            'Has_Expert_Ranking': player['has_expert_ranking'],
            'Age': player['age'],
            'Years_Exp': player['years_exp'],
            'Status': player['status'],
            'Injury_Status': player['injury_status'],
            'Base_Score': player.get('base_score', ''),
            'Team_Bonus': player.get('team_bonus', ''),
            'Age_Adjustment': player.get('age_adjustment', ''),
            'Experience_Adjustment': player.get('experience_adjustment', ''),
            'Position_Adjustment': player.get('position_adjustment', ''),
            'Status_Penalty': player.get('status_penalty', ''),
            'Sleeper_ID': player['player_id']
        })
    
    df = pd.DataFrame(df_data)
    
    # Create Excel file
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_COMPLETE_All_Player_Rankings.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Overall rankings (all players)
        overall_df = df[['Final_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank', 
                        'Expert_Rank', 'Algorithmic_Rank', 'VORP_Score', 'Has_Expert_Ranking',
                        'Age', 'Years_Exp', 'Status']].copy()
        overall_df.to_excel(writer, sheet_name='All_Player_Rankings', index=False)
        
        # Expert ranked players only
        expert_df = df[df['Has_Expert_Ranking'] == True][['Expert_Rank', 'Player_Name', 'Position', 'Team', 
                                                         'Position_Rank', 'Expert_High', 'Expert_Low', 'Expert_Range', 
                                                         'Expert_Std_Dev', 'VORP_Score']].copy()
        expert_df.to_excel(writer, sheet_name='Expert_Rankings', index=False)
        
        # Position sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos].copy()
            if not pos_df.empty:
                pos_cols = ['Position_Rank', 'Player_Name', 'Team', 'Final_Rank', 'Expert_Rank', 
                           'Algorithmic_Rank', 'VORP_Score', 'Age', 'Years_Exp', 'Status', 'Has_Expert_Ranking']
                pos_df = pos_df[pos_cols]
                sheet_name = pos.replace('/', '_') + '_Complete'
                pos_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Algorithmic breakdown
        algo_df = df[['Final_Rank', 'Player_Name', 'Position', 'Team', 'Algorithmic_Score', 
                     'Base_Score', 'Team_Bonus', 'Age_Adjustment', 'Experience_Adjustment', 
                     'Position_Adjustment', 'Status_Penalty']].copy()
        algo_df.to_excel(writer, sheet_name='Algorithmic_Breakdown', index=False)
        
        # Summary stats
        summary_data = []
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_players = df[df['Position'] == pos]
            expert_players = pos_players[pos_players['Has_Expert_Ranking'] == True]
            
            summary_data.append({
                'Position': pos,
                'Total_Players': len(pos_players),
                'Expert_Ranked': len(expert_players),
                'Algorithmic_Only': len(pos_players) - len(expert_players),
                'Top_Player': pos_players.iloc[0]['Player_Name'],
                'Top_Rank': pos_players.iloc[0]['Final_Rank'],
                'Avg_VORP': round(pos_players['VORP_Score'].mean(), 1),
                'Max_VORP': round(pos_players['VORP_Score'].max(), 1),
                'Min_VORP': round(pos_players['VORP_Score'].min(), 1)
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Complete_Summary', index=False)
    
    print(f"🎉 COMPLETE RANKING SYSTEM EXPORTED!")
    print(f"📁 File: FF_2025_COMPLETE_All_Player_Rankings.xlsx")
    print(f"📊 Total players ranked: {len(df)}")
    print(f"🏆 Expert rankings: {len(df[df['Has_Expert_Ranking'] == True])}")
    print(f"🤖 Algorithmic rankings: {len(df[df['Has_Expert_Ranking'] == False])}")
    
    # Position summary
    print(f"\n📈 COMPLETE POSITION BREAKDOWN:")
    pos_summary = df.groupby('Position').agg({
        'Player_Name': 'count',
        'Has_Expert_Ranking': 'sum',
        'VORP_Score': ['mean', 'max', 'min']
    })
    
    for pos, row in pos_summary.iterrows():
        total = int(row[('Player_Name', 'count')])
        expert = int(row[('Has_Expert_Ranking', 'sum')])
        algo = total - expert
        avg_vorp = round(row[('VORP_Score', 'mean')], 1)
        print(f"  {pos}: {total} total ({expert} expert + {algo} algorithmic) | Avg VORP: {avg_vorp}")

if __name__ == "__main__":
    export_complete_system_to_excel()
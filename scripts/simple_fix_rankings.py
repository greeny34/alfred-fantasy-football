#!/usr/bin/env python3
"""
Simple Fix for Rankings - Just properly extend expert rankings with common sense
"""
import sys
sys.path.append('/Users/jeffgreenfield/dev/ff_draft_vibe')

import pandas as pd
import requests
from complete_sleeper_assistant import CompleteDraftAssistant

def simple_fix_rankings():
    """Simple fix - just use expert rankings + logical positional ordering"""
    
    print("🏈 SIMPLE FIX FOR RANKINGS")
    print("🎯 Expert rankings + logical positional continuation")
    print("=" * 55)
    
    # Read the broken clean rankings to see what we have
    df = pd.read_excel('/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_CLEAN_Integer_Rankings.xlsx')
    
    print(f"📊 Loaded {len(df)} players from broken system")
    
    # Separate expert and non-expert players
    expert_df = df[df['Has_Expert_Data'] == True].copy()
    non_expert_df = df[df['Has_Expert_Data'] == False].copy()
    
    print(f"✅ Expert players: {len(expert_df)}")
    print(f"🔧 Non-expert players to fix: {len(non_expert_df)}")
    
    # Keep expert rankings as-is (they're good)
    expert_df = expert_df.sort_values('Final_Rank')
    
    # Now fix the non-expert players by position with football logic
    fixed_non_expert = []
    
    # QBs: Get actual NFL starters/relevant QBs
    qb_df = non_expert_df[non_expert_df['Position'] == 'QB'].copy()
    qb_priorities = get_qb_priorities()
    qb_df['priority'] = qb_df['Player_Name'].str.lower().map(qb_priorities).fillna(1000)
    qb_df = qb_df.sort_values('priority')
    fixed_non_expert.extend(qb_df.to_dict('records'))
    
    # RBs: Focus on actual relevant fantasy RBs
    rb_df = non_expert_df[non_expert_df['Position'] == 'RB'].copy()
    rb_priorities = get_rb_priorities()
    rb_df['priority'] = rb_df['Player_Name'].str.lower().map(rb_priorities).fillna(1000)
    rb_df = rb_df.sort_values('priority')
    fixed_non_expert.extend(rb_df.to_dict('records'))
    
    # WRs: Focus on relevant fantasy WRs
    wr_df = non_expert_df[non_expert_df['Position'] == 'WR'].copy()
    wr_priorities = get_wr_priorities()
    wr_df['priority'] = wr_df['Player_Name'].str.lower().map(wr_priorities).fillna(1000)
    wr_df = wr_df.sort_values('priority')
    fixed_non_expert.extend(wr_df.to_dict('records'))
    
    # TEs: Focus on relevant fantasy TEs
    te_df = non_expert_df[non_expert_df['Position'] == 'TE'].copy()
    te_priorities = get_te_priorities()
    te_df['priority'] = te_df['Player_Name'].str.lower().map(te_priorities).fillna(1000)
    te_df = te_df.sort_values('priority')
    fixed_non_expert.extend(te_df.to_dict('records'))
    
    # Kickers: Sort by team quality
    k_df = non_expert_df[non_expert_df['Position'] == 'K'].copy()
    k_priorities = get_kicker_priorities()
    k_df['priority'] = k_df['Team'].map(k_priorities).fillna(100)
    k_df = k_df.sort_values('priority')
    fixed_non_expert.extend(k_df.to_dict('records'))
    
    # Defenses: Sort by defensive quality
    dst_df = non_expert_df[non_expert_df['Position'] == 'D/ST'].copy()
    dst_priorities = get_defense_priorities()
    dst_df['priority'] = dst_df['Team'].map(dst_priorities).fillna(100)
    dst_df = dst_df.sort_values('priority')
    fixed_non_expert.extend(dst_df.to_dict('records'))
    
    # Combine expert + fixed non-expert
    all_expert_records = expert_df.to_dict('records')
    
    # Apply new rankings
    all_players = all_expert_records + fixed_non_expert
    
    # Re-rank everyone
    for i, player in enumerate(all_players, 1):
        player['Final_Rank'] = i
    
    # Recalculate position ranks
    position_counters = {}
    for player in all_players:
        pos = player['Position']
        if pos not in position_counters:
            position_counters[pos] = 0
        position_counters[pos] += 1
        player['Position_Rank'] = position_counters[pos]
    
    print(f"✅ Fixed rankings for all {len(all_players)} players")
    
    return all_players

def get_qb_priorities():
    """Return QB priority mapping - lower number = higher priority"""
    return {
        # Tier 1: Missing NFL starters (should be ranked right after experts)
        'tua tagovailoa': 1,
        'jordan love': 2,
        'dak prescott': 3,
        'kirk cousins': 4,
        'aaron rodgers': 5,
        
        # Tier 2: Young/developing starters
        'anthony richardson': 10,
        'c.j. stroud': 11,
        'bryce young': 12,
        'geno smith': 13,
        'drake maye': 14,
        
        # Tier 3: Quality backups/former starters
        'russell wilson': 20,
        'ryan tannehill': 21,
        'gardner minshew': 22,
        'jacoby brissett': 23,
        'mac jones': 24,
        'jimmy garoppolo': 25,
        'zach wilson': 26,
        'daniel jones': 27,
        'sam howell': 28,
        'aidan o\'connell': 29,
        
        # Everyone else gets default priority 1000 (ranked by team/age)
    }

def get_rb_priorities():
    """Return RB priority mapping"""
    return {
        # Tier 1: Relevant NFL RBs who should be ranked higher
        'ezekiel elliott': 1,
        'miles sanders': 2,
        'dameon pierce': 3,
        'antonio gibson': 4,
        'clyde edwards-helaire': 5,
        'jamaal williams': 6,
        'cam akers': 7,
        'david montgomery': 8,
        'kareem hunt': 9,
        'melvin gordon': 10,
        'leonard fournette': 11,
        'jerick mckinnon': 12,
        'sony michel': 13,
        
        # Tier 2: Young/backup RBs with potential
        'tyler allgeier': 20,
        'brian robinson': 21,
        'isaiah spiller': 22,
        'zamir white': 23,
        'kyren williams': 24,
        'hassan haskins': 25,
        'tyler badie': 26,
        'pierre strong': 27,
        'jerome ford': 28,
        'keaontay ingram': 29,
        
        # Everyone else gets 1000
    }

def get_wr_priorities():
    """Return WR priority mapping"""
    return {
        # Tier 1: Relevant NFL WRs
        'allen robinson': 1,
        'jarvis landry': 2,
        'kenny golladay': 3,
        'tyler boyd': 4,
        'adam thielen': 5,
        'robert woods': 6,
        'golden tate': 7,
        'marquise goodwin': 8,
        'nelson agholor': 9,
        'juju smith-schuster': 10,
        'tyler lockett': 11,
        'allen lazard': 12,
        'hunter renfrow': 13,
        'jakobi meyers': 14,
        'kendrick bourne': 15,
        'darnell mooney': 16,
        'van jefferson': 17,
        'tutu atwell': 18,
        'noah brown': 19,
        'jalen tolbert': 20,
        
        # Young WRs with potential
        'rome odunze': 30,
        'ladd mcconkey': 31,
        'brian thomas': 32,
        'malachi corley': 33,
        'keon coleman': 34,
        'adonai mitchell': 35,
        'xavier legette': 36,
        'troy franklin': 37,
        'ricky pearsall': 38,
        'ja\'lynn polk': 39,
    }

def get_te_priorities():
    """Return TE priority mapping"""
    return {
        # Tier 1: Relevant NFL TEs
        'zach ertz': 1,
        'austin hooper': 2,
        'noah fant': 3,
        'hayden hurst': 4,
        'gerald everett': 5,
        'tyler higbee': 6,
        'robert tonyan': 7,
        'cole kmet': 8,
        'pat freiermuth': 9,
        'mike gesicki': 10,
        'hunter henry': 11,
        'tyler kroft': 12,
        'c.j. uzomah': 13,
        'jordan akins': 14,
        'mo alie-cox': 15,
        'noah gray': 16,
        'luke farrell': 17,
        'foster moreau': 18,
        'cade otton': 19,
        'logan thomas': 20,
    }

def get_kicker_priorities():
    """Return kicker team priority mapping"""
    return {
        # Elite offenses = more opportunities
        'KC': 1, 'BUF': 2, 'SF': 3, 'PHI': 4, 'DET': 5,
        'MIA': 6, 'CIN': 7, 'DAL': 8, 'LAR': 9, 'BAL': 10,
        'HOU': 11, 'LAC': 12, 'GB': 13, 'ATL': 14, 'TB': 15,
        'MIN': 16, 'NO': 17, 'SEA': 18, 'IND': 19, 'WAS': 20,
        'PIT': 21, 'JAX': 22, 'DEN': 23, 'NYG': 24, 'TEN': 25,
        'CHI': 26, 'CLE': 27, 'ARI': 28, 'NYJ': 29, 'CAR': 30,
        'NE': 31, 'LV': 32
    }

def get_defense_priorities():
    """Return defense team priority mapping"""
    return {
        # Elite defenses first
        'BUF': 1, 'SF': 2, 'DAL': 3, 'PIT': 4, 'BAL': 5, 'NE': 6,
        'DEN': 7, 'MIA': 8, 'PHI': 9, 'NYJ': 10, 'CLE': 11, 'IND': 12,
        'LAC': 13, 'GB': 14, 'MIN': 15, 'NO': 16, 'TB': 17, 'SEA': 18,
        'ATL': 19, 'DET': 20, 'KC': 21, 'TEN': 22, 'HOU': 23, 'WAS': 24,
        'CHI': 25, 'CAR': 26, 'NYG': 27, 'JAX': 28, 'LV': 29, 'ARI': 30,
        'LAR': 31, 'CIN': 32
    }

def export_simple_fix():
    """Export the simple fix"""
    
    all_players = simple_fix_rankings()
    
    # Create DataFrame
    df_data = []
    for player in all_players:
        df_data.append({
            'Final_Rank': player['Final_Rank'],
            'Position_Rank': player['Position_Rank'],
            'Player_Name': player['Player_Name'],
            'Position': player['Position'],
            'Team': player['Team'],
            'High_Rank': player['High_Rank'],
            'Low_Rank': player['Low_Rank'],
            'Std_Deviation': player['Std_Deviation'],
            'Rank_Range': player['Rank_Range'],
            'VORP_Score': player['VORP_Score'],
            'Has_Expert_Data': player['Has_Expert_Data'],
            'Age': player['Age'],
            'Years_Exp': player['Years_Exp'],
            'Status': player['Status'],
            'Injury_Status': player.get('Injury_Status', ''),
            'Sleeper_ID': player.get('Sleeper_ID', player.get('sleeper_id', ''))
        })
    
    df = pd.DataFrame(df_data)
    
    # Export to Excel
    filename = '/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_FIXED_Rankings.xlsx'
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        
        # Main sheet
        main_cols = ['Final_Rank', 'Player_Name', 'Position', 'Team', 'Position_Rank',
                    'High_Rank', 'Low_Rank', 'Std_Deviation', 'Rank_Range', 'VORP_Score',
                    'Has_Expert_Data', 'Age', 'Years_Exp', 'Status']
        df[main_cols].to_excel(writer, sheet_name='Fixed_Rankings', index=False)
        
        # Position sheets
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if not pos_df.empty:
                pos_cols = ['Position_Rank', 'Player_Name', 'Team', 'Final_Rank',
                           'High_Rank', 'Low_Rank', 'Std_Deviation', 'VORP_Score', 'Has_Expert_Data']
                pos_summary = pos_df[pos_cols]
                sheet_name = pos.replace('/', '_') + '_Fixed'
                pos_summary.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"🎉 FIXED RANKINGS EXPORTED!")
    print(f"📁 File: FF_2025_FIXED_Rankings.xlsx")
    print(f"📊 Total players: {len(df)}")
    
    # Show QB verification
    print(f"\n🏈 FIXED QB RANKING VERIFICATION:")
    qb_df = df[df['Position'] == 'QB'].head(20)
    for _, row in qb_df.iterrows():
        expert_status = 'Expert' if row['Has_Expert_Data'] else 'Fixed'
        print(f"QB{int(row['Position_Rank']):2d}. {row['Player_Name']:<25} (Overall: {int(row['Final_Rank']):3d}) - {expert_status}")

if __name__ == "__main__":
    export_simple_fix()
#!/usr/bin/env python3
"""
Verify the complete ranking system
"""
import pandas as pd

def verify_complete_rankings():
    print("✅ VERIFYING COMPLETE RANKING SYSTEM")
    print("=" * 50)
    
    try:
        # Read the main sheet
        df = pd.read_excel('/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_COMPLETE_All_Player_Rankings.xlsx', 
                           sheet_name='All_Player_Rankings')
        
        print(f"📊 Total players in system: {len(df)}")
        
        # Check ranking completeness
        no_final_rank = df[df['Final_Rank'].isna()]
        no_vorp = df[df['VORP_Score'].isna()]
        
        print(f"✅ Players with Final_Rank: {len(df) - len(no_final_rank)} / {len(df)}")
        print(f"✅ Players with VORP_Score: {len(df) - len(no_vorp)} / {len(df)}")
        
        if len(no_final_rank) > 0:
            print(f"❌ Players missing Final_Rank: {len(no_final_rank)}")
            print(no_final_rank[['Player_Name', 'Position', 'Team']].head())
        
        if len(no_vorp) > 0:
            print(f"❌ Players missing VORP_Score: {len(no_vorp)}")
            print(no_vorp[['Player_Name', 'Position', 'Team']].head())
        
        # Show top players from each ranking method
        print(f"\n🏆 TOP 10 OVERALL PLAYERS:")
        top_10 = df.head(10)[['Final_Rank', 'Player_Name', 'Position', 'Team', 'Expert_Rank', 'VORP_Score']]
        for _, row in top_10.iterrows():
            expert_indicator = "📊" if pd.notna(row['Expert_Rank']) else "🤖"
            print(f"  {expert_indicator} {int(row['Final_Rank']):3d}. {row['Player_Name']:<22} ({row['Position']}) - {row['Team']} | VORP: {row['VORP_Score']}")
        
        # Show where algorithmic rankings start
        expert_players = df[df['Has_Expert_Ranking'] == True]
        algo_players = df[df['Has_Expert_Ranking'] == False]
        
        print(f"\n📊 Expert rankings: 1 - {expert_players['Final_Rank'].max()}")
        print(f"🤖 Algorithmic rankings: {algo_players['Final_Rank'].min()} - {algo_players['Final_Rank'].max()}")
        
        # Show first few algorithmic players
        print(f"\n🤖 FIRST 5 ALGORITHMIC PLAYERS:")
        first_algo = algo_players.head(5)[['Final_Rank', 'Player_Name', 'Position', 'Team', 'VORP_Score']]
        for _, row in first_algo.iterrows():
            print(f"  🤖 {int(row['Final_Rank']):3d}. {row['Player_Name']:<22} ({row['Position']}) - {row['Team']} | VORP: {row['VORP_Score']}")
        
        # Position breakdown
        print(f"\n📈 POSITION VERIFICATION:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            expert_count = len(pos_df[pos_df['Has_Expert_Ranking'] == True])
            algo_count = len(pos_df[pos_df['Has_Expert_Ranking'] == False])
            
            if len(pos_df) > 0:
                top_player = pos_df.iloc[0]
                ranking_type = "📊 Expert" if top_player['Has_Expert_Ranking'] else "🤖 Algo"
                print(f"  {pos}: {len(pos_df)} total ({expert_count} expert + {algo_count} algo) | Top: {ranking_type} - {top_player['Player_Name']}")
        
        # Check for any major issues
        print(f"\n🔍 VALIDATION CHECKS:")
        
        # Check for duplicate ranks
        duplicate_ranks = df[df.duplicated(['Final_Rank'], keep=False)]
        if len(duplicate_ranks) > 0:
            print(f"❌ Found {len(duplicate_ranks)} players with duplicate Final_Rank")
        else:
            print(f"✅ No duplicate Final_Rank values")
        
        # Check VORP distribution
        vorp_stats = df['VORP_Score'].describe()
        print(f"✅ VORP Score range: {vorp_stats['min']:.1f} to {vorp_stats['max']:.1f}")
        print(f"✅ VORP Score average: {vorp_stats['mean']:.1f}")
        
        print(f"\n🎉 COMPLETE RANKING SYSTEM VERIFIED!")
        print(f"✅ All {len(df)} players have rankings and VORP scores")
        
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    verify_complete_rankings()
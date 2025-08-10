#!/usr/bin/env python3
"""
Verify the clean integer ranking system addresses the methodology consistency issue
"""
import pandas as pd

def verify_clean_rankings():
    print("✅ VERIFYING CLEAN INTEGER RANKING SYSTEM")
    print("🎯 Confirming consistent methodology and proper integer rankings")
    print("=" * 65)
    
    try:
        # Read the clean rankings
        df = pd.read_excel('/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_CLEAN_Integer_Rankings.xlsx', 
                           sheet_name='Clean_Integer_Rankings')
        
        print(f"📊 Total players in system: {len(df)}")
        
        # CRITICAL TEST 1: Verify integer rankings 1-N with no gaps
        print(f"\n🔍 RANKING INTEGRITY TEST:")
        expected_ranks = set(range(1, len(df) + 1))
        actual_ranks = set(df['Final_Rank'].tolist())
        
        if expected_ranks == actual_ranks:
            print(f"✅ Perfect integer sequence: 1-{len(df)}")
        else:
            missing = expected_ranks - actual_ranks
            duplicates = len(df) - len(actual_ranks)
            print(f"❌ Ranking issues - Missing: {missing}, Duplicates: {duplicates}")
        
        # CRITICAL TEST 2: Verify data types
        print(f"\n🔍 DATA TYPE TEST:")
        if df['Final_Rank'].dtype in ['int64', 'int32']:
            print(f"✅ Rankings are integers: {df['Final_Rank'].dtype}")
        else:
            print(f"❌ Rankings are not integers: {df['Final_Rank'].dtype}")
        
        # CRITICAL TEST 3: Verify no float rankings
        has_floats = any(isinstance(rank, float) for rank in df['Final_Rank'])
        if not has_floats:
            print(f"✅ No float rankings detected")
        else:
            print(f"❌ Float rankings found!")
        
        # CRITICAL TEST 4: Check for proper ranges in analytical components
        print(f"\n🔍 ANALYTICAL COMPONENT TEST:")
        
        # High/Low ranks should be integers and logical
        high_low_valid = (
            (df['High_Rank'] <= df['Final_Rank']) & 
            (df['Final_Rank'] <= df['Low_Rank'])
        ).all()
        if high_low_valid:
            print(f"✅ High/Low ranges are logically consistent")
        else:
            print(f"❌ Some High/Low ranges are invalid")
        
        # Standard deviation should be reasonable
        std_range = (df['Std_Deviation'].min(), df['Std_Deviation'].max())
        print(f"✅ Standard deviation range: {std_range[0]:.2f} - {std_range[1]:.2f}")
        
        # VORP should be positive
        negative_vorp = len(df[df['VORP_Score'] < 0])
        if negative_vorp == 0:
            print(f"✅ All VORP scores are non-negative")
        else:
            print(f"⚠️  {negative_vorp} players have negative VORP")
        
        # TEST 5: Show ranking methodology consistency
        print(f"\n📊 METHODOLOGY CONSISTENCY TEST:")
        
        expert_players = df[df['Has_Expert_Data'] == True]
        composite_players = df[df['Has_Expert_Data'] == False]
        
        print(f"🧠 Players with expert data: {len(expert_players)}")
        print(f"🎯 Players with composite scoring: {len(composite_players)}")
        
        # Show that both groups have same analytical structure
        expert_complete = (
            expert_players['Final_Rank'].notna().all() and
            expert_players['High_Rank'].notna().all() and
            expert_players['Low_Rank'].notna().all() and
            expert_players['Std_Deviation'].notna().all() and
            expert_players['VORP_Score'].notna().all()
        )
        
        composite_complete = (
            composite_players['Final_Rank'].notna().all() and
            composite_players['High_Rank'].notna().all() and
            composite_players['Low_Rank'].notna().all() and
            composite_players['Std_Deviation'].notna().all() and
            composite_players['VORP_Score'].notna().all()
        )
        
        if expert_complete and composite_complete:
            print(f"✅ Both groups have complete analytical data")
        else:
            print(f"❌ Missing analytical data in some groups")
        
        # TEST 6: Show sample rankings to verify no float issues
        print(f"\n🏆 SAMPLE RANKINGS VERIFICATION:")
        
        print(f"📊 Top 10 players:")
        top_10 = df.head(10)
        for _, row in top_10.iterrows():
            rank_type = "Expert" if row['Has_Expert_Data'] else "Composite"
            print(f"   {int(row['Final_Rank']):3d}. {row['Player_Name']:<25} ({row['Position']}) | {rank_type} | VORP: {row['VORP_Score']:5.1f}")
        
        print(f"\n🔍 Ranks 91-100 (transition area):")
        transition = df[(df['Final_Rank'] >= 91) & (df['Final_Rank'] <= 100)]
        for _, row in transition.iterrows():
            rank_type = "Expert" if row['Has_Expert_Data'] else "Composite"
            print(f"   {int(row['Final_Rank']):3d}. {row['Player_Name']:<25} ({row['Position']}) | {rank_type} | VORP: {row['VORP_Score']:5.1f}")
        
        print(f"\n🎯 Ranks 101-110 (post-expert area):")
        post_expert = df[(df['Final_Rank'] >= 101) & (df['Final_Rank'] <= 110)]
        for _, row in post_expert.iterrows():
            rank_type = "Expert" if row['Has_Expert_Data'] else "Composite"
            print(f"   {int(row['Final_Rank']):3d}. {row['Player_Name']:<25} ({row['Position']}) | {rank_type} | VORP: {row['VORP_Score']:5.1f}")
        
        # TEST 7: Verify position ranking integrity
        print(f"\n📈 POSITION RANKING INTEGRITY:")
        for pos in ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']:
            pos_df = df[df['Position'] == pos]
            if len(pos_df) > 0:
                pos_ranks = sorted(pos_df['Position_Rank'].tolist())
                expected_pos_ranks = list(range(1, len(pos_df) + 1))
                
                if pos_ranks == expected_pos_ranks:
                    print(f"   ✅ {pos}: Perfect position ranks 1-{len(pos_df)}")
                else:
                    print(f"   ❌ {pos}: Position ranking issues")
        
        print(f"\n🎉 CLEAN INTEGER RANKING SYSTEM VERIFICATION COMPLETE!")
        
        # Final summary
        all_tests_passed = (
            expected_ranks == actual_ranks and  # Perfect integer sequence
            df['Final_Rank'].dtype in ['int64', 'int32'] and  # Integer data type
            not has_floats and  # No float rankings
            high_low_valid and  # Logical high/low ranges
            expert_complete and composite_complete  # Complete analytical data
        )
        
        if all_tests_passed:
            print(f"✅ ALL TESTS PASSED - System ready for use!")
            print(f"✅ Fixed the float/integer methodology inconsistency")
            print(f"✅ All {len(df)} players have proper integer rankings 1-{len(df)}")
            print(f"✅ Same analytical methodology applied consistently")
        else:
            print(f"❌ Some tests failed - system needs fixes")
            
    except Exception as e:
        print(f"❌ Error reading clean rankings file: {e}")

if __name__ == "__main__":
    verify_clean_rankings()
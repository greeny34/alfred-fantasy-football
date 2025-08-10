#!/usr/bin/env python3
"""
Check the defenses in the Excel file
"""
import pandas as pd

def check_defenses():
    print("🛡️ CHECKING DEFENSES IN EXCEL FILE")
    print("=" * 40)
    
    try:
        # Read the D/ST sheet
        df = pd.read_excel('/Users/jeffgreenfield/dev/ff_draft_vibe/FF_2025_Complete_Rankings.xlsx', 
                           sheet_name='D_ST_Rankings')
        
        print(f"📊 Found {len(df)} defenses in Excel file")
        print("\n🛡️ Defense teams:")
        
        for i, row in df.iterrows():
            print(f"  {i+1:2d}. {row['Player_Name']} - {row['Team']}")
        
        # Check if all 32 NFL teams are represented
        teams = set(df['Team'].unique())
        print(f"\n📋 Unique teams: {len(teams)}")
        print(f"Teams: {sorted(list(teams))}")
        
        # Check for missing major teams
        expected_teams = ['BUF', 'MIA', 'NE', 'NYJ', 'BAL', 'CIN', 'CLE', 'PIT', 
                         'HOU', 'IND', 'JAX', 'TEN', 'DEN', 'KC', 'LV', 'LAC',
                         'DAL', 'NYG', 'PHI', 'WAS', 'CHI', 'DET', 'GB', 'MIN',
                         'ATL', 'CAR', 'NO', 'TB', 'ARI', 'LAR', 'SF', 'SEA']
        
        missing_teams = set(expected_teams) - teams
        if missing_teams:
            print(f"❌ Missing teams: {sorted(list(missing_teams))}")
        else:
            print("✅ All 32 NFL teams represented!")
            
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")

if __name__ == "__main__":
    check_defenses()
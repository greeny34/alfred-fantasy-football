#!/usr/bin/env python3
"""
Add team defenses (DST) to the database
"""
import psycopg2
import os

def add_team_defenses():
    """Add DST entry for each NFL team"""
    
    # NFL teams
    nfl_teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LV', 'LAC', 'LAR', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'
    ]
    
    # Team name mappings for display
    team_names = {
        'ARI': 'Arizona Cardinals',
        'ATL': 'Atlanta Falcons',
        'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills',
        'CAR': 'Carolina Panthers',
        'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals',
        'CLE': 'Cleveland Browns',
        'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos',
        'DET': 'Detroit Lions',
        'GB': 'Green Bay Packers',
        'HOU': 'Houston Texans',
        'IND': 'Indianapolis Colts',
        'JAX': 'Jacksonville Jaguars',
        'KC': 'Kansas City Chiefs',
        'LV': 'Las Vegas Raiders',
        'LAC': 'Los Angeles Chargers',
        'LAR': 'Los Angeles Rams',
        'MIA': 'Miami Dolphins',
        'MIN': 'Minnesota Vikings',
        'NE': 'New England Patriots',
        'NO': 'New Orleans Saints',
        'NYG': 'New York Giants',
        'NYJ': 'New York Jets',
        'PHI': 'Philadelphia Eagles',
        'PIT': 'Pittsburgh Steelers',
        'SF': 'San Francisco 49ers',
        'SEA': 'Seattle Seahawks',
        'TB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans',
        'WAS': 'Washington Commanders'
    }
    
    print("🛡️ ADDING TEAM DEFENSES TO DATABASE")
    print("=" * 40)
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
        
        cur = conn.cursor()
        
        # Add DST for each team
        inserted_count = 0
        
        for team_code in nfl_teams:
            team_name = team_names.get(team_code, f"{team_code} Defense")
            defense_name = f"{team_name} DST"
            
            try:
                cur.execute("""
                    INSERT INTO players (name, position, team, year, is_active)
                    VALUES (%s, %s, %s, %s, %s);
                """, (defense_name, 'DST', team_code, 2025, True))
                
                print(f"  ✅ Added: {defense_name}")
                inserted_count += 1
                
            except Exception as e:
                print(f"  ❌ Error adding {defense_name}: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"\n✅ Successfully added {inserted_count} team defenses!")
        
        # Show updated counts
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
        
        cur = conn.cursor()
        cur.execute("""
            SELECT position, COUNT(*) as count
            FROM players 
            GROUP BY position 
            ORDER BY position;
        """)
        
        print(f"\n📊 UPDATED PLAYER COUNTS:")
        for pos, count in cur.fetchall():
            print(f"  {pos}: {count}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

if __name__ == "__main__":
    add_team_defenses()
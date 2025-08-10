#!/usr/bin/env python3
"""
Simple Database Data Checker
Check and fix player team assignments
"""
import psycopg2
import pandas as pd
import os

def connect_to_db():
    """Connect to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port='5432',
            user=os.environ.get('USER', 'jeffgreenfield'),
            password='',
            database='fantasy_draft_db'
        )
        return conn
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        return None

def check_player_teams():
    """Check player team assignments"""
    conn = connect_to_db()
    if not conn:
        return
    
    print("🔍 CHECKING PLAYER TEAM ASSIGNMENTS")
    print("=" * 50)
    
    # Known 2025 team changes
    correct_teams = {
        "DK Metcalf": "PIT",
        "Russell Wilson": "PIT", 
        "Calvin Ridley": "TEN",
        "Saquon Barkley": "PHI",
        "Tony Pollard": "TEN",
        "Josh Jacobs": "GB",
        "Aaron Jones": "MIN",
        "Joe Mixon": "HOU",
        "Stefon Diggs": "HOU",
        "DeAndre Hopkins": "KC",
        "Amari Cooper": "BUF",
        "Jerry Jeudy": "CLE",
        "Geno Smith": "LV",
        "Kirk Cousins": "ATL",
        "Aaron Rodgers": "NYJ"  # Fixed from PIT
    }
    
    cur = conn.cursor()
    
    issues_found = []
    
    # Check each player
    for player_name, correct_team in correct_teams.items():
        cur.execute("""
            SELECT player_id, name, team FROM players 
            WHERE name ILIKE %s;
        """, (f"%{player_name}%",))
        
        result = cur.fetchone()
        if result:
            player_id, name, current_team = result
            if current_team != correct_team:
                print(f"❌ {name}: Currently {current_team}, should be {correct_team}")
                issues_found.append((player_id, name, current_team, correct_team))
            else:
                print(f"✅ {name}: Correctly shows {current_team}")
        else:
            print(f"⚠️ {player_name}: Not found in database")
    
    if issues_found:
        print(f"\n🔧 Found {len(issues_found)} team assignment issues")
        
        fix_prompt = input("Fix these issues? (y/n): ").lower().strip()
        
        if fix_prompt == 'y':
            for player_id, name, old_team, new_team in issues_found:
                cur.execute("""
                    UPDATE players 
                    SET team = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE player_id = %s;
                """, (new_team, player_id))
                print(f"✅ Updated {name}: {old_team} → {new_team}")
            
            conn.commit()
            print("✅ All fixes applied!")
        else:
            print("❌ No changes made")
    else:
        print("✅ No team assignment issues found!")
    
    cur.close()
    conn.close()

def show_all_players():
    """Show all players by position"""
    conn = connect_to_db()
    if not conn:
        return
    
    print("\n👥 ALL PLAYERS IN DATABASE")
    print("=" * 50)
    
    cur = conn.cursor()
    
    positions = ['QB', 'RB', 'WR', 'TE']
    
    for pos in positions:
        cur.execute("""
            SELECT name, team FROM players 
            WHERE position = %s 
            ORDER BY name;
        """, (pos,))
        
        players = cur.fetchall()
        print(f"\n{pos} ({len(players)} players):")
        
        for name, team in players[:10]:  # Show first 10
            print(f"  {name} ({team})")
        
        if len(players) > 10:
            print(f"  ... and {len(players) - 10} more")
    
    cur.close()
    conn.close()

def show_rankings_summary():
    """Show rankings summary"""
    conn = connect_to_db()
    if not conn:
        return
    
    print("\n📊 RANKINGS SUMMARY")
    print("=" * 30)
    
    cur = conn.cursor()
    
    # Count rankings by source
    cur.execute("""
        SELECT rs.source_name, COUNT(*) as ranking_count
        FROM player_rankings pr
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        GROUP BY rs.source_name
        ORDER BY ranking_count DESC;
    """)
    
    for source, count in cur.fetchall():
        print(f"  {source}: {count} rankings")
    
    # Show total players and rankings
    cur.execute("SELECT COUNT(*) FROM players;")
    player_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM player_rankings;")
    ranking_count = cur.fetchone()[0]
    
    print(f"\nTotal: {player_count} players, {ranking_count} rankings")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🏈 DATABASE DATA CHECKER")
    print("=" * 30)
    
    check_player_teams()
    show_all_players()
    show_rankings_summary()
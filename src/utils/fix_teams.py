#!/usr/bin/env python3
"""
Fix team assignments automatically
"""
import psycopg2
import os

def fix_team_assignments():
    """Fix known team assignment issues"""
    
    # Connect to database
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )
    
    cur = conn.cursor()
    
    # Fixes needed
    fixes = [
        ("DK Metcalf", "PIT"),
        ("Aaron Rodgers", "NYJ")
    ]
    
    print("🔧 FIXING TEAM ASSIGNMENTS")
    print("=" * 30)
    
    for player_name, correct_team in fixes:
        # Find player
        cur.execute("""
            SELECT player_id, name, team FROM players 
            WHERE name ILIKE %s;
        """, (f"%{player_name}%",))
        
        result = cur.fetchone()
        if result:
            player_id, name, old_team = result
            
            # Update team
            cur.execute("""
                UPDATE players 
                SET team = %s, updated_at = CURRENT_TIMESTAMP
                WHERE player_id = %s;
            """, (correct_team, player_id))
            
            print(f"✅ Fixed {name}: {old_team} → {correct_team}")
        else:
            print(f"⚠️ Player '{player_name}' not found")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("\n✅ Team fixes completed!")

if __name__ == "__main__":
    fix_team_assignments()
#!/usr/bin/env python3
"""
Remove ALL Rotowire position rankings completely
"""

import psycopg2
import os

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

def remove_all_rotowire_rankings():
    """Remove ALL Rotowire position ranking sources and data"""
    print("🧹 Removing ALL Rotowire position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Find all Rotowire sources
        cur.execute("""
            SELECT source_id, source_name 
            FROM ranking_sources 
            WHERE source_name LIKE '%Rotowire%'
        """)
        rotowire_sources = cur.fetchall()
        
        print(f"Found {len(rotowire_sources)} Rotowire sources to remove:")
        for source_id, name in rotowire_sources:
            print(f"  - {name} (ID: {source_id})")
        
        # Remove rankings for all Rotowire sources
        total_deleted = 0
        for source_id, name in rotowire_sources:
            cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
            deleted_rankings = cur.rowcount
            print(f"  ✅ Deleted {deleted_rankings} rankings for {name}")
            total_deleted += deleted_rankings
        
        # Remove all Rotowire sources
        for source_id, name in rotowire_sources:
            cur.execute("DELETE FROM ranking_sources WHERE source_id = %s", (source_id,))
            print(f"  ✅ Removed source: {name}")
        
        conn.commit()
        print(f"\n✅ Total removed: {total_deleted} Rotowire rankings and {len(rotowire_sources)} sources")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_rotowire_removal():
    """Verify all Rotowire sources are gone"""
    print("🔍 Verifying Rotowire removal...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check for any remaining Rotowire sources
        cur.execute("SELECT source_name FROM ranking_sources WHERE source_name LIKE '%Rotowire%'")
        remaining_sources = cur.fetchall()
        
        if remaining_sources:
            print(f"❌ Still found {len(remaining_sources)} Rotowire sources:")
            for source in remaining_sources:
                print(f"  - {source[0]}")
        else:
            print("✅ All Rotowire sources removed")
        
        # Show remaining clean sources
        cur.execute("SELECT source_name FROM ranking_sources ORDER BY source_name")
        clean_sources = [row[0] for row in cur.fetchall()]
        print(f"\nRemaining position ranking sources: {clean_sources}")
        
        # Check for any Rotowire rankings
        cur.execute("""
            SELECT COUNT(*) 
            FROM player_rankings pr
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE rs.source_name LIKE '%Rotowire%'
        """)
        remaining_rankings = cur.fetchone()[0]
        
        if remaining_rankings > 0:
            print(f"❌ Still found {remaining_rankings} Rotowire rankings")
        else:
            print("✅ All Rotowire rankings removed")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Removing ALL Rotowire position rankings...\n")
    
    remove_all_rotowire_rankings()
    print()
    verify_rotowire_removal()
    
    print("\n✅ Rotowire cleanup complete!")
    print("Position rankings are now clean - we can add proper Rotowire data later.")
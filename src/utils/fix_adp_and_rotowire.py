#!/usr/bin/env python3
"""
Fix ADP and Rotowire position rankings issues
1. Remove Consensus ADP source
2. Delete and rebuild Rotowire position rankings
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

def remove_consensus_adp():
    """Remove the Consensus ADP source that's polluting data"""
    print("🧹 Removing Consensus ADP source...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Find Consensus ADP source
        cur.execute("SELECT adp_source_id FROM adp_sources WHERE source_name = 'Consensus'")
        consensus_source = cur.fetchone()
        
        if consensus_source:
            source_id = consensus_source[0]
            print(f"Found Consensus ADP source (ID: {source_id})")
            
            # Delete rankings for this source
            cur.execute("DELETE FROM adp_rankings WHERE adp_source_id = %s", (source_id,))
            deleted_rankings = cur.rowcount
            print(f"✅ Deleted {deleted_rankings} Consensus ADP rankings")
            
            # Delete the source itself
            cur.execute("DELETE FROM adp_sources WHERE adp_source_id = %s", (source_id,))
            print("✅ Deleted Consensus ADP source")
            
        else:
            print("No Consensus ADP source found")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def remove_rotowire_position_rankings():
    """Remove corrupted Rotowire position rankings"""
    print("🧹 Removing corrupted Rotowire position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Find Rotowire position source
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Rotowire_Position_Rankings'")
        rotowire_source = cur.fetchone()
        
        if rotowire_source:
            source_id = rotowire_source[0]
            print(f"Found Rotowire Position Rankings source (ID: {source_id})")
            
            # Delete rankings for this source
            cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
            deleted_rankings = cur.rowcount
            print(f"✅ Deleted {deleted_rankings} corrupted Rotowire position rankings")
            
            # Delete the source itself
            cur.execute("DELETE FROM ranking_sources WHERE source_id = %s", (source_id,))
            print("✅ Deleted Rotowire Position Rankings source")
            
        else:
            print("No Rotowire Position Rankings source found")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_cleanup():
    """Verify the cleanup worked"""
    print("🔍 Verifying cleanup...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check ADP sources
        cur.execute("SELECT source_name FROM adp_sources ORDER BY source_name")
        adp_sources = [row[0] for row in cur.fetchall()]
        print(f"Remaining ADP sources: {adp_sources}")
        
        # Check ranking sources
        cur.execute("SELECT source_name FROM ranking_sources ORDER BY source_name")
        ranking_sources = [row[0] for row in cur.fetchall()]
        print(f"Remaining ranking sources: {ranking_sources}")
        
        # Check for any Brian Thomas rankings to see if corruption is gone
        cur.execute("""
            SELECT p.name, p.position, rs.source_name, pr.position_rank
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id  
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE p.name ILIKE '%Brian Thomas%'
            ORDER BY rs.source_name, pr.position_rank
        """)
        
        brian_rankings = cur.fetchall()
        if brian_rankings:
            print("Brian Thomas rankings (should be clean now):")
            for name, pos, source, rank in brian_rankings:
                print(f"  {name} {pos} - {source}: #{rank}")
        else:
            print("No Brian Thomas rankings found (normal after cleanup)")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Fixing ADP and Rotowire issues...\n")
    
    remove_consensus_adp()
    print()
    remove_rotowire_position_rankings()
    print()
    verify_cleanup()
    
    print("\n✅ Cleanup complete!")
    print("\nNext steps:")
    print("1. Check that ADP values are now clean (no 350 defaults)")
    print("2. Manually reload Rotowire position rankings if needed")
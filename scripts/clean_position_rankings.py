#!/usr/bin/env python3
"""
Clean up position rankings - remove ALL ADP data
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

def show_current_sources():
    """Show current ranking sources"""
    print("📊 Current ranking sources:")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT source_id, source_name, base_url 
            FROM ranking_sources 
            ORDER BY source_name
        """)
        
        for source_id, name, url in cur.fetchall():
            print(f"  {source_id}: {name}")
        
    finally:
        cur.close()
        conn.close()

def remove_adp_sources_from_position_rankings():
    """Remove ADP sources from position rankings system"""
    print("🧹 Cleaning up position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Get ADP-related source IDs
        cur.execute("""
            SELECT source_id, source_name 
            FROM ranking_sources 
            WHERE source_name LIKE '%ADP%' OR source_name LIKE '%Rotowire_ADP%'
        """)
        adp_sources = cur.fetchall()
        
        print(f"Found {len(adp_sources)} ADP sources to remove from position rankings:")
        for source_id, name in adp_sources:
            print(f"  - {name} (ID: {source_id})")
        
        # Remove ADP rankings from player_rankings table
        for source_id, name in adp_sources:
            cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
            deleted = cur.rowcount
            print(f"  ✅ Removed {deleted} rankings for {name}")
        
        # Remove ADP sources from ranking_sources table
        for source_id, name in adp_sources:
            cur.execute("DELETE FROM ranking_sources WHERE source_id = %s", (source_id,))
            print(f"  ✅ Removed source: {name}")
        
        conn.commit()
        print("✅ Position rankings cleaned!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_clean_rankings():
    """Verify position rankings are clean"""
    print("🔍 Verifying clean position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Show remaining sources
        cur.execute("SELECT source_name FROM ranking_sources ORDER BY source_name")
        sources = [row[0] for row in cur.fetchall()]
        print(f"Remaining sources: {sources}")
        
        # Show sample QB rankings
        cur.execute("""
            SELECT p.name, rs.source_name, pr.position_rank
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE p.position = 'QB'
            ORDER BY rs.source_name, pr.position_rank
            LIMIT 15
        """)
        
        print("\nSample QB rankings:")
        for name, source, rank in cur.fetchall():
            print(f"  {rank:2d}. {name:20s} ({source})")
        
        # Count rankings by source
        cur.execute("""
            SELECT rs.source_name, COUNT(*) as count
            FROM player_rankings pr
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            GROUP BY rs.source_name
            ORDER BY count DESC
        """)
        
        print("\nRankings count by source:")
        for source, count in cur.fetchall():
            print(f"  {source}: {count}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Cleaning position rankings from ADP contamination...\n")
    
    show_current_sources()
    print()
    remove_adp_sources_from_position_rankings()
    print()
    verify_clean_rankings()
    
    print("\n✅ Position rankings cleanup complete!")
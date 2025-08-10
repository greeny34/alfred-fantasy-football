#!/usr/bin/env python3
"""
Simple database query tool
"""
import psycopg2
import os

def query_database():
    """Run simple queries to check database"""
    
    conn = psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )
    
    cur = conn.cursor()
    
    print("🏈 DATABASE STATUS")
    print("=" * 25)
    
    # Count players by position
    cur.execute("""
        SELECT position, COUNT(*) as count
        FROM players 
        GROUP BY position 
        ORDER BY position;
    """)
    
    print("Players by position:")
    for pos, count in cur.fetchall():
        print(f"  {pos}: {count}")
    
    # Check DK Metcalf specifically
    cur.execute("""
        SELECT p.name, p.position, p.team, rs.source_name, pr.position_rank
        FROM players p
        JOIN player_rankings pr ON p.player_id = pr.player_id
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        WHERE p.name ILIKE '%metcalf%'
        ORDER BY rs.source_name;
    """)
    
    print(f"\nDK Metcalf verification:")
    for name, pos, team, source, rank in cur.fetchall():
        print(f"  {source}: {name} {pos}{rank} ({team})")
    
    # Show a few top WRs
    cur.execute("""
        SELECT p.name, p.team, pr.position_rank
        FROM players p
        JOIN player_rankings pr ON p.player_id = pr.player_id
        JOIN ranking_sources rs ON pr.source_id = rs.source_id
        WHERE p.position = 'WR' AND rs.source_name = 'ESPN'
        ORDER BY pr.position_rank
        LIMIT 10;
    """)
    
    print(f"\nTop 10 WRs (ESPN):")
    for name, team, rank in cur.fetchall():
        print(f"  WR{rank}: {name} ({team})")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    query_database()
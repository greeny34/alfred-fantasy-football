#!/usr/bin/env python3
"""
Check ADP Data Availability
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

def check_adp_data():
    """Check if we have ADP data"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check players table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'players' 
            ORDER BY ordinal_position;
        """)
        
        print("Players table columns:")
        for col_name, data_type in cur.fetchall():
            print(f"  {col_name}: {data_type}")
        
        # Check if we have any ADP-related data in ranking sources
        cur.execute("""
            SELECT DISTINCT source_name 
            FROM ranking_sources 
            WHERE source_name ILIKE '%adp%' OR source_name ILIKE '%underdog%'
            ORDER BY source_name;
        """)
        
        adp_sources = cur.fetchall()
        print(f"\nPotential ADP sources: {len(adp_sources)}")
        for source in adp_sources:
            print(f"  {source[0]}")
        
        # Check a sample of data
        cur.execute("""
            SELECT p.name, p.position, rs.source_name, pr.position_rank
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE rs.source_name ILIKE '%underdog%'
            AND p.position = 'QB'
            ORDER BY pr.position_rank
            LIMIT 10;
        """)
        
        print(f"\nSample Underdog data (potential ADP):")
        for name, pos, source, rank in cur.fetchall():
            print(f"  {rank:2d}. {name} ({pos}) - {source}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_adp_data()
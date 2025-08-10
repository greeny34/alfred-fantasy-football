#!/usr/bin/env python3
"""
Load Rotowire TE rankings correctly (TE only)
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

def load_rotowire_te_rankings():
    """Load Rotowire TE rankings properly"""
    print("📊 Loading Rotowire TE rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create/get the ranking source
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url, has_ppr_rankings, has_position_ranks, quality_score)
            VALUES ('Rotowire_TE_Rankings', 'https://www.rotowire.com/', TRUE, TRUE, 8.0)
            ON CONFLICT (source_name) DO NOTHING
        """)
        
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Rotowire_TE_Rankings'")
        source_id = cur.fetchone()[0]
        print(f"✅ Using source ID: {source_id}")
        
        # Clear existing rankings for this source
        cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
        
        # Read the TE rankings
        df = pd.read_excel('rotowire rankings.xlsx', sheet_name='CheatSheetTE')
        print(f"✅ Loaded {len(df)} TE rankings from Rotowire")
        
        inserted = 0
        not_found = []
        
        for idx, row in df.iterrows():
            player_name = str(row['Player Name']).strip()
            position = str(row['Pos']).strip().upper()
            rank = int(row['Pos Rank'])
            team = str(row['Team']).strip().upper()
            
            if position != 'TE':
                continue
            
            # Find player in database - try multiple variations
            player_found = False
            
            # Try exact match first
            cur.execute("""
                SELECT player_id FROM players 
                WHERE LOWER(name) = LOWER(%s) AND position = %s
                LIMIT 1
            """, (player_name, position))
            
            player_result = cur.fetchone()
            
            if not player_result:
                # Try fuzzy match without Jr./Sr. suffixes
                clean_name = player_name.replace(' Jr.', '').replace(' Sr.', '').replace(' III', '').replace(' II', '')
                cur.execute("""
                    SELECT player_id FROM players 
                    WHERE LOWER(name) LIKE LOWER(%s) AND position = %s
                    LIMIT 1
                """, (f"%{clean_name}%", position))
                player_result = cur.fetchone()
            
            if player_result:
                player_id = player_result[0]
                
                # Insert position ranking
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, position_rank)
                    VALUES (%s, %s, %s)
                """, (player_id, source_id, rank))
                
                inserted += 1
                player_found = True
            
            if not player_found:
                not_found.append((player_name, position, rank))
        
        conn.commit()
        print(f"✅ Inserted {inserted} Rotowire TE rankings")
        
        if not_found:
            print(f"\n⚠️ Players not found in database ({len(not_found)}):")
            for name, pos, rank in not_found[:10]:  # Show first 10
                print(f"   - {name} {pos} (Rank: {rank})")
        
        # Verify with a sample player
        cur.execute("""
            SELECT p.name, p.position, pr.position_rank
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE rs.source_name = 'Rotowire_TE_Rankings'
            AND p.name ILIKE '%brock bowers%'
        """)
        
        brock_result = cur.fetchone()
        if brock_result:
            name, pos, rank = brock_result
            print(f"\n✅ Verification: {name} {pos} - Rotowire TE Rank: #{rank}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading Rotowire TE rankings: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    load_rotowire_te_rankings()
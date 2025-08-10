#!/usr/bin/env python3
"""
Load Rotowire ADP and position rankings into the database
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

def load_rotowire_adp():
    """Load Rotowire ADP overall rankings"""
    print("📊 Loading Rotowire ADP overall rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Read the ADP data
        df = pd.read_excel('ADP Values roto.xlsx')
        print(f"✅ Loaded {len(df)} rows from ADP Values roto.xlsx")
        print(f"Columns: {df.columns.tolist()}")
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Create source if it doesn't exist
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url, has_ppr_rankings, has_position_ranks, quality_score)
            VALUES ('Rotowire_ADP', 'https://www.rotowire.com/football/draft-guide.php', TRUE, FALSE, 8.0)
            ON CONFLICT (source_name) DO NOTHING
        """)
        
        # Get the source_id
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Rotowire_ADP'")
        source_id = cur.fetchone()[0]
        print(f"\n✅ Created/Updated source: Rotowire_ADP (ID: {source_id})")
        
        # Clear existing rankings for this source
        cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
        
        # Process and insert ADP data
        inserted = 0
        not_found = []
        
        for idx, row in df.iterrows():
            player_name = row.get('Player Name') or row.get('Player') or row.get('Name') or row.get('PLAYER')
            adp_rank = row.get('ADP') or row.get('Rank') or row.get('RANK') or row.get('Overall')
            
            if pd.isna(player_name) or pd.isna(adp_rank):
                continue
            
            # Clean player name
            player_name = str(player_name).strip()
            
            # Try to find player in database
            cur.execute("""
                SELECT player_id, position FROM players 
                WHERE LOWER(name) = LOWER(%s) 
                OR LOWER(name) LIKE LOWER(%s)
                LIMIT 1
            """, (player_name, f"%{player_name}%"))
            
            player_result = cur.fetchone()
            
            if player_result:
                player_id, position = player_result
                
                # Insert ranking - use overall_rank for ADP
                cur.execute("""
                    INSERT INTO player_rankings (player_id, source_id, overall_rank, position_rank)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (player_id, source_id, ranking_date) 
                    DO UPDATE SET overall_rank = EXCLUDED.overall_rank, position_rank = EXCLUDED.position_rank
                """, (player_id, source_id, int(adp_rank), int(adp_rank)))
                
                inserted += 1
            else:
                not_found.append((player_name, adp_rank))
        
        conn.commit()
        print(f"\n✅ Inserted {inserted} ADP rankings")
        
        if not_found:
            print(f"\n⚠️ Players not found in database ({len(not_found)}):")
            for name, rank in not_found[:10]:  # Show first 10
                print(f"   - {name} (ADP: {rank})")
            if len(not_found) > 10:
                print(f"   ... and {len(not_found) - 10} more")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading ADP data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def load_rotowire_position_rankings():
    """Load Rotowire position rankings"""
    print("\n📊 Loading Rotowire position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Read the position rankings data
        xl_file = pd.ExcelFile('rotowire rankings.xlsx')
        print(f"✅ Found sheets: {xl_file.sheet_names}")
        
        # Create source if it doesn't exist
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url, has_ppr_rankings, has_position_ranks, quality_score)
            VALUES ('Rotowire_Position_Rankings', 'https://www.rotowire.com/football/draft-guide.php', TRUE, TRUE, 8.0)
            ON CONFLICT (source_name) DO NOTHING
        """)
        
        # Get the source_id
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Rotowire_Position_Rankings'")
        source_id = cur.fetchone()[0]
        print(f"\n✅ Created/Updated source: Rotowire_Position_Rankings (ID: {source_id})")
        
        # Clear existing rankings for this source
        cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
        
        total_inserted = 0
        
        # Process each sheet (assuming each sheet is a position)
        for sheet_name in xl_file.sheet_names:
            print(f"\n📋 Processing sheet: {sheet_name}")
            df = pd.read_excel('rotowire rankings.xlsx', sheet_name=sheet_name)
            
            # Try to determine position from sheet name
            position = sheet_name.upper()
            if position not in ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'DEF']:
                print(f"   ⚠️ Skipping sheet {sheet_name} - unknown position")
                continue
            
            if position == 'DEF':
                position = 'DST'
            
            print(f"   Columns: {df.columns.tolist()}")
            
            inserted = 0
            
            for idx, row in df.iterrows():
                player_name = row.get('Player') or row.get('Name') or row.get('PLAYER')
                rank = row.get('Rank') or row.get('RANK') or row.get('Pos Rank') or (idx + 1)
                
                if pd.isna(player_name):
                    continue
                
                player_name = str(player_name).strip()
                
                # Try to find player
                cur.execute("""
                    SELECT player_id FROM players 
                    WHERE LOWER(name) = LOWER(%s) AND position = %s
                    LIMIT 1
                """, (player_name, position))
                
                player_result = cur.fetchone()
                
                if player_result:
                    player_id = player_result[0]
                    
                    # Insert position ranking
                    cur.execute("""
                        INSERT INTO player_rankings (player_id, source_id, position_rank)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (player_id, source_id, ranking_date) 
                        DO UPDATE SET position_rank = EXCLUDED.position_rank
                    """, (player_id, source_id, int(rank)))
                    
                    inserted += 1
            
            print(f"   ✅ Inserted {inserted} {position} rankings")
            total_inserted += inserted
        
        conn.commit()
        print(f"\n✅ Total inserted: {total_inserted} position rankings")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading position rankings: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_adp_data():
    """Verify the loaded ADP data"""
    print("\n🔍 Verifying ADP data...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Check top 20 players by ADP
        cur.execute("""
            SELECT p.name, p.position, p.team, pr.overall_rank as adp
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE rs.source_name = 'Rotowire_ADP'
            AND pr.overall_rank IS NOT NULL
            ORDER BY pr.overall_rank
            LIMIT 20
        """)
        
        print("\n📊 Top 20 players by ADP:")
        for i, (name, position, team, adp) in enumerate(cur.fetchall(), 1):
            print(f"{i:2d}. {name:25s} {position:3s} - {team:3s} (ADP: {adp})")
        
        # Count by position
        cur.execute("""
            SELECT p.position, COUNT(*) as count
            FROM players p
            JOIN player_rankings pr ON p.player_id = pr.player_id
            JOIN ranking_sources rs ON pr.source_id = rs.source_id
            WHERE rs.source_name = 'Rotowire_ADP'
            AND pr.overall_rank IS NOT NULL
            GROUP BY p.position
            ORDER BY p.position
        """)
        
        print("\n📊 Players with ADP by position:")
        for position, count in cur.fetchall():
            print(f"   {position}: {count}")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Loading Rotowire data into database...\n")
    
    # Load ADP overall rankings
    load_rotowire_adp()
    
    # Load position rankings
    load_rotowire_position_rankings()
    
    # Verify the data
    verify_adp_data()
    
    print("\n✅ Done!")
#!/usr/bin/env python3
"""
Load Rotowire position rankings correctly 
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

def inspect_rotowire_file():
    """Inspect the Rotowire rankings file structure"""
    print("📊 Inspecting Rotowire rankings file...")
    
    try:
        xl_file = pd.ExcelFile('rotowire rankings.xlsx')
        print(f"✅ Found sheets: {xl_file.sheet_names}")
        
        for sheet_name in xl_file.sheet_names:
            print(f"\n📋 Sheet: {sheet_name}")
            df = pd.read_excel('rotowire rankings.xlsx', sheet_name=sheet_name, nrows=10)
            print(f"   Columns: {df.columns.tolist()}")
            print("   Sample data:")
            print(df.head(3))
        
    except Exception as e:
        print(f"❌ Error inspecting file: {e}")

def load_rotowire_position_rankings():
    """Load Rotowire position rankings as a ranking source"""
    print("📊 Loading Rotowire position rankings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create/get the ranking source
        cur.execute("""
            INSERT INTO ranking_sources (source_name, base_url, has_ppr_rankings, has_position_ranks, quality_score)
            VALUES ('Rotowire_Position_Rankings', 'https://www.rotowire.com/', TRUE, TRUE, 8.0)
            ON CONFLICT (source_name) DO NOTHING
        """)
        
        cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Rotowire_Position_Rankings'")
        source_id = cur.fetchone()[0]
        print(f"✅ Using source ID: {source_id}")
        
        # Clear existing rankings for this source
        cur.execute("DELETE FROM player_rankings WHERE source_id = %s", (source_id,))
        
        # Read the file to see its actual structure
        xl_file = pd.ExcelFile('rotowire rankings.xlsx')
        
        # If there's only one sheet, try to parse it differently
        if len(xl_file.sheet_names) == 1:
            sheet_name = xl_file.sheet_names[0]
            df = pd.read_excel('rotowire rankings.xlsx', sheet_name=sheet_name)
            
            print(f"Working with sheet: {sheet_name}")
            print(f"Columns: {df.columns.tolist()}")
            print(f"Sample data:")
            print(df.head())
            
            # Try to identify position and ranking columns
            # Look for common column patterns
            position_col = None
            rank_col = None
            name_col = None
            
            for col in df.columns:
                col_lower = str(col).lower()
                if 'pos rank' in col_lower:
                    rank_col = col
                elif col_lower == 'pos':
                    position_col = col
                elif 'name' in col_lower or 'player' in col_lower:
                    name_col = col
            
            print(f"Detected columns - Name: {name_col}, Position: {position_col}, Rank: {rank_col}")
            
            if name_col and position_col:
                inserted = 0
                for idx, row in df.iterrows():
                    player_name = row.get(name_col)
                    position = row.get(position_col)
                    rank = row.get(rank_col) if rank_col else (idx + 1)
                    
                    if pd.isna(player_name) or pd.isna(position):
                        continue
                    
                    player_name = str(player_name).strip()
                    position = str(position).strip().upper()
                    
                    # Skip invalid positions
                    if position not in ['QB', 'RB', 'WR', 'TE', 'K', 'DST', 'DEF']:
                        continue
                    
                    if position == 'DEF':
                        position = 'DST'
                    
                    # Find player in database
                    cur.execute("""
                        SELECT player_id FROM players 
                        WHERE LOWER(name) = LOWER(%s) AND position = %s
                        LIMIT 1
                    """, (player_name, position))
                    
                    player_result = cur.fetchone()
                    if player_result:
                        player_id = player_result[0]
                        
                        try:
                            rank_int = int(rank)
                            cur.execute("""
                                INSERT INTO player_rankings (player_id, source_id, position_rank)
                                VALUES (%s, %s, %s)
                            """, (player_id, source_id, rank_int))
                            inserted += 1
                        except (ValueError, TypeError):
                            continue
                
                print(f"✅ Inserted {inserted} Rotowire position rankings")
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading Rotowire position rankings: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    inspect_rotowire_file()
    print("\n" + "="*50 + "\n")
    load_rotowire_position_rankings()
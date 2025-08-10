#!/usr/bin/env python3
"""
Create ADP rankings schema and load data
"""

import pandas as pd
import psycopg2
import os
import statistics
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

def create_adp_tables():
    """Create ADP-specific tables"""
    print("📊 Creating ADP tables...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create ADP sources table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adp_sources (
                adp_source_id SERIAL PRIMARY KEY,
                source_name VARCHAR(50) NOT NULL UNIQUE,
                source_url TEXT,
                quality_score DECIMAL(3,2) DEFAULT 5.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create ADP rankings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS adp_rankings (
                adp_ranking_id SERIAL PRIMARY KEY,
                player_id INTEGER NOT NULL,
                adp_source_id INTEGER NOT NULL,
                adp_value DECIMAL(6,2) NOT NULL,
                consensus_rank INTEGER,
                ranking_date DATE NOT NULL DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE,
                FOREIGN KEY (adp_source_id) REFERENCES adp_sources (adp_source_id) ON DELETE CASCADE,
                UNIQUE(player_id, adp_source_id, ranking_date)
            );
        """)
        
        # Create consensus ADP table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS consensus_adp (
                consensus_id SERIAL PRIMARY KEY,
                player_id INTEGER NOT NULL,
                mean_adp DECIMAL(6,2) NOT NULL,
                median_adp DECIMAL(6,2) NOT NULL,
                min_adp DECIMAL(6,2) NOT NULL,
                max_adp DECIMAL(6,2) NOT NULL,
                stdev_adp DECIMAL(6,2),
                source_count INTEGER NOT NULL,
                consensus_rank INTEGER NOT NULL,
                ranking_date DATE NOT NULL DEFAULT CURRENT_DATE,
                
                FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE,
                UNIQUE(player_id, ranking_date)
            );
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_adp_rankings_player ON adp_rankings(player_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_adp_rankings_source ON adp_rankings(adp_source_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_consensus_adp_rank ON consensus_adp(consensus_rank);")
        
        conn.commit()
        print("✅ ADP tables created successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error creating ADP tables: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def load_adp_sources():
    """Load ADP sources"""
    print("📝 Loading ADP sources...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    sources = [
        ('Fantrax', 'https://www.fantrax.com/', 8.0),
        ('Sleeper', 'https://sleeper.app/', 8.5),
        ('ESPN', 'https://www.espn.com/fantasy/', 8.0),
        ('MFL', 'https://www.myfantasyleague.com/', 7.5),
        ('NFFC', 'https://nffc.com/', 8.0),
        ('Consensus', 'Multiple Sources Average', 9.0)
    ]
    
    try:
        for name, url, quality in sources:
            cur.execute("""
                INSERT INTO adp_sources (source_name, source_url, quality_score)
                VALUES (%s, %s, %s)
                ON CONFLICT (source_name) DO NOTHING
            """, (name, url, quality))
        
        conn.commit()
        print("✅ ADP sources loaded!")
        
    finally:
        cur.close()
        conn.close()

def load_adp_data():
    """Load ADP data from multiple sources file"""
    print("📊 Loading ADP data from multiple sources...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Read the data
        df = pd.read_excel('ADP values multiple sources.xlsx')
        print(f"✅ Loaded {len(df)} rows")
        
        # Get source IDs
        cur.execute("SELECT adp_source_id, source_name FROM adp_sources")
        source_map = {name: id for id, name in cur.fetchall()}
        
        # Clear existing data
        cur.execute("DELETE FROM adp_rankings")
        cur.execute("DELETE FROM consensus_adp")
        
        # Process each row
        adp_sources = ['Fantrax', 'Sleeper', 'ESPN', 'MFL', 'NFFC']
        inserted_count = 0
        consensus_data = []
        
        for idx, row in df.iterrows():
            player_name = str(row['Name']).strip()
            consensus_rank = row['Rank']
            
            # Skip rows with non-numeric ranks (like 'T34' for ties)
            try:
                consensus_rank = int(consensus_rank)
            except (ValueError, TypeError):
                continue
            
            # Find player in database
            cur.execute("""
                SELECT player_id FROM players 
                WHERE LOWER(name) = LOWER(%s)
                LIMIT 1
            """, (player_name,))
            
            player_result = cur.fetchone()
            if not player_result:
                continue
            
            player_id = player_result[0]
            adp_values = []
            
            # Insert individual source ADPs
            for source in adp_sources:
                adp_value = row.get(source)
                if pd.notna(adp_value):
                    try:
                        adp_float = float(adp_value)
                        if adp_float > 0:
                            source_id = source_map.get(source)
                            if source_id:
                                cur.execute("""
                                    INSERT INTO adp_rankings (player_id, adp_source_id, adp_value, consensus_rank)
                                    VALUES (%s, %s, %s, %s)
                                """, (player_id, source_id, adp_float, consensus_rank))
                                adp_values.append(adp_float)
                                inserted_count += 1
                    except (ValueError, TypeError):
                        continue
            
            # Calculate consensus for this player
            if adp_values:
                mean_adp = statistics.mean(adp_values)
                median_adp = statistics.median(adp_values)
                min_adp = min(adp_values)
                max_adp = max(adp_values)
                stdev_adp = statistics.stdev(adp_values) if len(adp_values) > 1 else 0.0
                
                consensus_data.append({
                    'player_id': player_id,
                    'mean_adp': mean_adp,
                    'median_adp': median_adp,
                    'min_adp': min_adp,
                    'max_adp': max_adp,
                    'stdev_adp': stdev_adp,
                    'source_count': len(adp_values),
                    'consensus_rank': consensus_rank
                })
        
        # Insert consensus data
        consensus_inserted = 0
        for data in consensus_data:
            cur.execute("""
                INSERT INTO consensus_adp (player_id, mean_adp, median_adp, min_adp, max_adp, stdev_adp, source_count, consensus_rank)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                data['player_id'], data['mean_adp'], data['median_adp'], 
                data['min_adp'], data['max_adp'], data['stdev_adp'],
                data['source_count'], data['consensus_rank']
            ))
            consensus_inserted += 1
        
        conn.commit()
        print(f"✅ Inserted {inserted_count} individual ADP rankings")
        print(f"✅ Inserted {consensus_inserted} consensus ADP records")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error loading ADP data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

def verify_adp_data():
    """Verify loaded ADP data"""
    print("🔍 Verifying ADP data...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Show top 15 consensus ADP
        cur.execute("""
            SELECT p.name, p.position, p.team, c.consensus_rank, c.mean_adp, c.source_count
            FROM consensus_adp c
            JOIN players p ON c.player_id = p.player_id
            ORDER BY c.consensus_rank
            LIMIT 15
        """)
        
        print("\n📊 Top 15 Consensus ADP:")
        for name, pos, team, rank, mean_adp, sources in cur.fetchall():
            print(f"{rank:3d}. {name:25s} {pos:3s} - {team:3s} (Avg: {mean_adp:.1f}, {sources} sources)")
        
        # Show source coverage
        cur.execute("""
            SELECT s.source_name, COUNT(*) as player_count
            FROM adp_rankings ar
            JOIN adp_sources s ON ar.adp_source_id = s.adp_source_id
            GROUP BY s.source_name
            ORDER BY player_count DESC
        """)
        
        print("\n📊 ADP Source Coverage:")
        for source, count in cur.fetchall():
            print(f"   {source}: {count} players")
        
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("🚀 Setting up ADP ranking system...\n")
    
    create_adp_tables()
    load_adp_sources()
    load_adp_data()
    verify_adp_data()
    
    print("\n✅ ADP system setup complete!")
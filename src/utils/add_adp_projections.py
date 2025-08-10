#!/usr/bin/env python3
"""
Add ADP and Projections Schema
Extends database to store ADP and projected points data
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

def add_adp_projections_tables():
    """Add tables for ADP and projections data"""
    print("🔧 Adding ADP and projections tables...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create ADP data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_adp (
            adp_id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES players(player_id),
            source_id INTEGER REFERENCES ranking_sources(source_id),
            adp_value DECIMAL(5,2),
            data_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, source_id, data_date)
        );
    """)
    
    # Create projections data table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_projections (
            projection_id SERIAL PRIMARY KEY,
            player_id INTEGER REFERENCES players(player_id),
            source_id INTEGER REFERENCES ranking_sources(source_id),
            projected_points DECIMAL(6,2),
            projection_type VARCHAR(50) DEFAULT 'season_total',
            data_date DATE DEFAULT CURRENT_DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(player_id, source_id, projection_type, data_date)
        );
    """)
    
    # Create indexes for better performance
    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_adp_player_id ON player_adp(player_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_adp_source_id ON player_adp(source_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_projections_player_id ON player_projections(player_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_projections_source_id ON player_projections(source_id);")
    except Exception as e:
        print(f"⚠️  Note: Some indexes may already exist: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    
    print("✅ ADP and projections tables created successfully")

def populate_underdog_adp_projections():
    """Populate ADP and projections data from recent Underdog parsing"""
    print("📊 Populating ADP and projections data...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get Underdog source ID
    cur.execute("SELECT source_id FROM ranking_sources WHERE source_name = 'Underdog'")
    result = cur.fetchone()
    if not result:
        print("❌ Underdog source not found in database")
        return
    
    underdog_source_id = result[0]
    
    # Note: Since we didn't store ADP/projections in the original parse,
    # we'd need to re-run the parser with database storage for these fields
    # For now, just create the schema
    
    print("ℹ️  Schema created. Re-run new_rankings_parser.py with updated database storage to populate ADP/projections data")
    
    cur.close()
    conn.close()

def main():
    print("🚀 Adding ADP and projections support...")
    
    # Add the new tables
    add_adp_projections_tables()
    
    # Note about populating data
    populate_underdog_adp_projections()
    
    print("🎉 Database schema updated for ADP and projections!")

if __name__ == "__main__":
    main()
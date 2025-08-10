#!/usr/bin/env python3
"""
Database Setup for Fantasy Football Draft Assistant
Simple schema to get started with PostgreSQL
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost', 
    'port': '5432',
    'user': os.environ.get('USER', 'jeffgreenfield'),  # Use current user
    'password': '',  # No password for local setup
    'database': 'fantasy_draft_db'
}

def create_database_schema():
    """Create the basic database schema"""
    
    # SQL to create our core tables
    create_tables_sql = """
    -- Players table
    CREATE TABLE IF NOT EXISTS players (
        player_id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        position VARCHAR(10) NOT NULL CHECK (position IN ('QB','RB','WR','TE','K','D/ST')),
        team VARCHAR(3) NOT NULL,
        year INTEGER NOT NULL DEFAULT 2025,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        UNIQUE(name, team, year)
    );

    -- Ranking sources table
    CREATE TABLE IF NOT EXISTS ranking_sources (
        source_id SERIAL PRIMARY KEY,
        source_name VARCHAR(50) NOT NULL UNIQUE,
        base_url TEXT NOT NULL,
        has_ppr_rankings BOOLEAN DEFAULT FALSE,
        has_position_ranks BOOLEAN DEFAULT FALSE,
        quality_score DECIMAL(3,2) DEFAULT 5.0 CHECK (quality_score >= 1.0 AND quality_score <= 10.0),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );

    -- Player rankings table
    CREATE TABLE IF NOT EXISTS player_rankings (
        ranking_id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL,
        source_id INTEGER NOT NULL,
        position_rank INTEGER NOT NULL,
        overall_rank INTEGER,
        ranking_date DATE NOT NULL DEFAULT CURRENT_DATE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        
        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE,
        FOREIGN KEY (source_id) REFERENCES ranking_sources (source_id) ON DELETE CASCADE,
        UNIQUE(player_id, source_id, ranking_date)
    );

    -- ADP data table
    CREATE TABLE IF NOT EXISTS player_adp (
        adp_id SERIAL PRIMARY KEY,
        player_id INTEGER NOT NULL,
        source VARCHAR(50) NOT NULL,
        adp_value DECIMAL(5,2) NOT NULL,
        sample_size INTEGER,
        league_format VARCHAR(20) DEFAULT '12team_ppr',
        collection_date DATE NOT NULL DEFAULT CURRENT_DATE,
        
        FOREIGN KEY (player_id) REFERENCES players (player_id) ON DELETE CASCADE,
        UNIQUE(player_id, source, league_format, collection_date)
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_players_position ON players(position);
    CREATE INDEX IF NOT EXISTS idx_players_team ON players(team);
    CREATE INDEX IF NOT EXISTS idx_rankings_player_date ON player_rankings(player_id, ranking_date);
    CREATE INDEX IF NOT EXISTS idx_rankings_source ON player_rankings(source_id);
    CREATE INDEX IF NOT EXISTS idx_adp_player ON player_adp(player_id);
    """
    
    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("🔗 Connected to PostgreSQL database")
        
        # Execute table creation
        cur.execute(create_tables_sql)
        conn.commit()
        
        print("✅ Database schema created successfully!")
        
        # Show what we created
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cur.fetchall()
        
        print("\n📊 Created tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating database schema: {e}")
        return False

def populate_ranking_sources():
    """Add initial ranking sources to the database"""
    
    sources = [
        {
            'name': 'ESPN',
            'url': 'https://www.espn.com/fantasy/football/',
            'ppr': True,
            'position': True,
            'quality': 8.5
        },
        {
            'name': 'FantasyPros',
            'url': 'https://www.fantasypros.com/nfl/',
            'ppr': True,
            'position': True,
            'quality': 9.0
        },
        {
            'name': 'Yahoo',
            'url': 'https://football.fantasysports.yahoo.com/',
            'ppr': True,
            'position': True,
            'quality': 7.5
        },
        {
            'name': 'CBS',
            'url': 'https://www.cbssports.com/fantasy/football/',
            'ppr': True,
            'position': True,
            'quality': 7.0
        },
        {
            'name': 'NFL',
            'url': 'https://www.nfl.com/fantasy/',
            'ppr': True,
            'position': True,
            'quality': 6.5
        }
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n📝 Adding ranking sources...")
        
        for source in sources:
            cur.execute("""
                INSERT INTO ranking_sources (source_name, base_url, has_ppr_rankings, has_position_ranks, quality_score)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_name) DO NOTHING;
            """, (source['name'], source['url'], source['ppr'], source['position'], source['quality']))
        
        conn.commit()
        
        # Show what we added
        cur.execute("SELECT source_name, quality_score FROM ranking_sources ORDER BY quality_score DESC;")
        sources_added = cur.fetchall()
        
        print("✅ Ranking sources added:")
        for source_name, quality in sources_added:
            print(f"   - {source_name} (Quality: {quality})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error adding ranking sources: {e}")
        return False

def test_database_connection():
    """Test that we can connect to the database and run basic queries"""
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n🧪 Testing database connection...")
        
        # Test basic query
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print(f"✅ PostgreSQL version: {version[0]}")
        
        # Test our tables exist
        cur.execute("""
            SELECT COUNT(*) as table_count 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        table_count = cur.fetchone()[0]
        print(f"✅ Tables created: {table_count}")
        
        # Test sources table
        cur.execute("SELECT COUNT(*) FROM ranking_sources;")
        source_count = cur.fetchone()[0]
        print(f"✅ Ranking sources: {source_count}")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

if __name__ == "__main__":
    print("🏈 Fantasy Football Database Setup")
    print("=" * 40)
    
    # Create schema
    if create_database_schema():
        # Add initial data
        if populate_ranking_sources():
            # Test everything
            test_database_connection()
            print("\n🎉 Database setup complete!")
            print("\nNext steps:")
            print("  1. Run the data scraping pipeline")
            print("  2. Populate player data")
            print("  3. Start collecting rankings")
        else:
            print("❌ Failed to populate ranking sources")
    else:
        print("❌ Failed to create database schema")
#!/usr/bin/env python3
"""
Create Draft Recommendation Schema
Database schema for tracking draft state and recommendations
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

def create_draft_tables():
    """Create draft tracking tables"""
    print("🚀 Creating draft recommendation schema...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Draft sessions table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS draft_sessions (
                session_id SERIAL PRIMARY KEY,
                session_name VARCHAR(100) NOT NULL,
                draft_format VARCHAR(20) DEFAULT 'standard', -- 'standard', 'ppr', 'superflex'
                team_count INTEGER DEFAULT 12,
                rounds INTEGER DEFAULT 16,
                current_pick INTEGER DEFAULT 1,
                user_draft_position INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Draft picks table (tracks all picks made)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS draft_picks (
                pick_id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES draft_sessions(session_id),
                player_id INTEGER REFERENCES players(player_id),
                pick_number INTEGER NOT NULL,
                round_number INTEGER NOT NULL,
                pick_in_round INTEGER NOT NULL,
                team_number INTEGER NOT NULL,
                is_user_pick BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # User roster construction preferences
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roster_strategy (
                strategy_id SERIAL PRIMARY KEY,
                strategy_name VARCHAR(50) UNIQUE NOT NULL,
                qb_early_rounds INTEGER DEFAULT 0, -- 0=late, 1-3=early rounds to target QB
                rb_priority INTEGER DEFAULT 2, -- 1=low, 2=medium, 3=high priority
                wr_priority INTEGER DEFAULT 2,
                te_priority INTEGER DEFAULT 1,
                flex_strategy VARCHAR(20) DEFAULT 'best_available', -- 'rb_heavy', 'wr_heavy', 'best_available'
                value_threshold DECIMAL(5,2) DEFAULT 5.0, -- Minimum ADP value gap to consider
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Position targets for roster construction
        cur.execute("""
            CREATE TABLE IF NOT EXISTS position_targets (
                target_id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES draft_sessions(session_id),
                position VARCHAR(10) NOT NULL,
                min_count INTEGER DEFAULT 1,
                max_count INTEGER DEFAULT 3,
                priority_rounds TEXT, -- JSON array of preferred round ranges
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Create indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_draft_picks_session ON draft_picks(session_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_draft_picks_player ON draft_picks(player_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_position_targets_session ON position_targets(session_id);")
        
        conn.commit()
        print("✅ Draft schema created successfully")
        
    except Exception as e:
        print(f"❌ Error creating draft schema: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insert_default_strategies():
    """Insert default roster strategies"""
    print("📊 Inserting default roster strategies...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    default_strategies = [
        ('Zero RB', 0, 1, 3, 2, 'wr_heavy', 3.0),
        ('RB Heavy', 0, 3, 2, 1, 'rb_heavy', 4.0),
        ('Balanced', 0, 2, 2, 2, 'best_available', 5.0),
        ('Late Round QB', 0, 2, 2, 1, 'best_available', 4.0),
        ('Early QB', 2, 2, 2, 1, 'best_available', 6.0),
    ]
    
    try:
        for name, qb_early, rb_pri, wr_pri, te_pri, flex_strat, value_thresh in default_strategies:
            cur.execute("""
                INSERT INTO roster_strategy 
                (strategy_name, qb_early_rounds, rb_priority, wr_priority, te_priority, flex_strategy, value_threshold)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (strategy_name) DO NOTHING
            """, (name, qb_early, rb_pri, wr_pri, te_pri, flex_strat, value_thresh))
        
        conn.commit()
        print("✅ Default strategies inserted")
        
        # Show inserted strategies
        cur.execute("SELECT strategy_name, qb_early_rounds, rb_priority, wr_priority, te_priority FROM roster_strategy ORDER BY strategy_name")
        strategies = cur.fetchall()
        
        print("\n📋 Available strategies:")
        for name, qb_early, rb_pri, wr_pri, te_pri in strategies:
            print(f"  {name}: QB={qb_early}, RB={rb_pri}, WR={wr_pri}, TE={te_pri}")
        
    except Exception as e:
        print(f"❌ Error inserting default strategies: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def main():
    print("🚀 Setting up draft recommendation system...")
    
    # Create schema
    create_draft_tables()
    
    # Insert defaults
    insert_default_strategies()
    
    print("\n🎉 Draft recommendation system ready!")
    print("Next steps:")
    print("  1. Create draft recommendation API endpoints")
    print("  2. Build recommendation algorithm")
    print("  3. Add draft UI components")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Create Settings Schema
Database schema for storing user configuration settings
"""

import psycopg2
import os
import json

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        port='5432',
        user=os.environ.get('USER', 'jeffgreenfield'),
        password='',
        database='fantasy_draft_db'
    )

def create_settings_tables():
    """Create settings tables"""
    print("🔧 Creating settings database schema...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Main settings table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                setting_id SERIAL PRIMARY KEY,
                setting_name VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type VARCHAR(50) DEFAULT 'string',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Team preferences table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS team_preferences (
                pref_id SERIAL PRIMARY KEY,
                team_name VARCHAR(10) NOT NULL,
                preference_type VARCHAR(20) NOT NULL, -- 'favorite', 'hated'
                bias_percentage DECIMAL(5,2) DEFAULT 10.0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(team_name, preference_type)
            );
        """)
        
        # Player adjustments table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS player_adjustments (
                adjustment_id SERIAL PRIMARY KEY,
                player_id INTEGER REFERENCES players(player_id),
                adjustment_type VARCHAR(20) NOT NULL, -- 'undervalued', 'overvalued'
                adjustment_percentage DECIMAL(5,2) NOT NULL,
                notes TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(player_id, adjustment_type)
            );
        """)
        
        # Indexes for performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_name ON user_settings(setting_name);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_team_preferences_team ON team_preferences(team_name);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_player_adjustments_player ON player_adjustments(player_id);")
        
        conn.commit()
        print("✅ Settings schema created successfully")
        
    except Exception as e:
        print(f"❌ Error creating settings schema: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insert_default_settings():
    """Insert default settings values"""
    print("📊 Inserting default settings...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    default_settings = [
        # Position limits
        ('position_limit_qb', '30', 'integer', 'Maximum QB players to include in rankings'),
        ('position_limit_rb', '60', 'integer', 'Maximum RB players to include in rankings'),
        ('position_limit_wr', '75', 'integer', 'Maximum WR players to include in rankings'),
        ('position_limit_te', '30', 'integer', 'Maximum TE players to include in rankings'),
        ('position_limit_k', '20', 'integer', 'Maximum K players to include in rankings'),
        ('position_limit_dst', '15', 'integer', 'Maximum DST players to include in rankings'),
        
        # CV multiplier settings
        ('cv_multiplier_standard', '1.0', 'decimal', 'CV multiplier for standard aggressive/conservative'),
        ('cv_multiplier_high', '2.0', 'decimal', 'CV multiplier for high aggressive/conservative'),
        
        # Team bias settings
        ('team_bias_enabled', 'true', 'boolean', 'Enable team bias adjustments'),
        ('default_favorite_bias', '10.0', 'decimal', 'Default percentage bias for favorite teams (decrease mean)'),
        ('default_hated_bias', '10.0', 'decimal', 'Default percentage bias for hated teams (increase mean)'),
        
        # Player adjustment settings
        ('player_adjustments_enabled', 'true', 'boolean', 'Enable individual player value adjustments'),
        ('default_undervalued_adjustment', '10.0', 'decimal', 'Default percentage for undervalued players (decrease mean)'),
        ('default_overvalued_adjustment', '10.0', 'decimal', 'Default percentage for overvalued players (increase mean)'),
        
        # Strategy settings
        ('default_strategy', 'standard', 'string', 'Default ranking strategy (standard, aggressive, conservative, aggressive_high, conservative_high)'),
        ('show_all_strategies', 'true', 'boolean', 'Show all strategy columns in spreadsheet'),
        
        # Algorithm settings
        ('enable_hard_cuts', 'true', 'boolean', 'Enable automatic hard cuts based on position limits'),
        ('recalculate_on_settings_change', 'true', 'boolean', 'Automatically recalculate rankings when settings change'),
    ]
    
    try:
        for setting_name, value, type_name, description in default_settings:
            cur.execute("""
                INSERT INTO user_settings (setting_name, setting_value, setting_type, description)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (setting_name) DO NOTHING
            """, (setting_name, value, type_name, description))
        
        conn.commit()
        print("✅ Default settings inserted")
        
        # Show inserted settings
        cur.execute("SELECT setting_name, setting_value, setting_type FROM user_settings ORDER BY setting_name")
        settings = cur.fetchall()
        
        print("\n📋 Current settings:")
        for name, value, type_name in settings:
            print(f"  {name}: {value} ({type_name})")
        
    except Exception as e:
        print(f"❌ Error inserting default settings: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def main():
    print("🚀 Setting up configurable settings system...")
    
    # Create schema
    create_settings_tables()
    
    # Insert defaults
    insert_default_settings()
    
    print("\n🎉 Settings system ready!")
    print("Next steps:")
    print("  1. Create settings UI")
    print("  2. Update data_viewer.py to use settings")
    print("  3. Add settings route and template")

if __name__ == "__main__":
    main()
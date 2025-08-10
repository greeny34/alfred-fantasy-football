#!/usr/bin/env python3
"""
Create Strategy Optimization Schema
Database schema for dynamic roster construction optimization
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

def create_optimization_tables():
    """Create strategy optimization tables"""
    print("🚀 Creating strategy optimization schema...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Draft strategy states - tracks optimal strategy at each pick
        cur.execute("""
            CREATE TABLE IF NOT EXISTS draft_strategy_states (
                state_id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES draft_sessions(session_id),
                pick_number INTEGER NOT NULL,
                roster_state JSONB NOT NULL, -- Current roster composition
                optimal_path JSONB NOT NULL, -- Next 3-5 positions to target
                confidence_score DECIMAL(5,2) NOT NULL, -- 0-100 probability of success
                backup_paths JSONB, -- Alternative strategies
                expected_points DECIMAL(8,2), -- Projected final roster points
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, pick_number)
            );
        """)
        
        # Roster completion paths cache - precomputed optimal sequences 
        cur.execute("""
            CREATE TABLE IF NOT EXISTS roster_completion_paths (
                path_id SERIAL PRIMARY KEY,
                roster_signature TEXT NOT NULL, -- Hash of roster state
                remaining_picks INTEGER NOT NULL,
                draft_position INTEGER, -- 1-10 for position-specific strategies
                optimal_sequence JSONB NOT NULL, -- Array of positions to draft
                player_targets JSONB, -- Specific player targets by tier
                expected_points DECIMAL(8,2) NOT NULL,
                success_probability DECIMAL(5,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(roster_signature, remaining_picks, draft_position)
            );
        """)
        
        # Position tier values - dynamic values for optimization
        cur.execute("""
            CREATE TABLE IF NOT EXISTS position_tier_values (
                tier_id SERIAL PRIMARY KEY,
                position VARCHAR(10) NOT NULL,
                tier_number INTEGER NOT NULL, -- 1=elite, 2=tier1, etc
                tier_name VARCHAR(50), -- 'Elite', 'Tier 1', etc
                min_rank INTEGER NOT NULL,
                max_rank INTEGER NOT NULL,
                base_value DECIMAL(6,2) NOT NULL, -- Base points value
                scarcity_multiplier DECIMAL(4,2) DEFAULT 1.0,
                draft_position_adjustments JSONB, -- Position-specific bonuses
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(position, tier_number)
            );
        """)
        
        # Strategy optimization parameters
        cur.execute("""
            CREATE TABLE IF NOT EXISTS strategy_parameters (
                param_id SERIAL PRIMARY KEY,
                draft_position INTEGER NOT NULL, -- 1-10
                round_number INTEGER, -- NULL = applies to all rounds
                parameter_name VARCHAR(100) NOT NULL,
                parameter_value DECIMAL(8,4) NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(draft_position, round_number, parameter_name)
            );
        """)
        
        # Draft pick probabilities - likelihood of getting target players
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pick_probabilities (
                prob_id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES draft_sessions(session_id),
                pick_number INTEGER NOT NULL,
                player_id INTEGER REFERENCES players(player_id),
                probability DECIMAL(5,2) NOT NULL, -- 0-100% chance available
                tier_rank INTEGER, -- Rank within position tier
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(session_id, pick_number, player_id)
            );
        """)
        
        # Create indexes for performance
        cur.execute("CREATE INDEX IF NOT EXISTS idx_strategy_states_session ON draft_strategy_states(session_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_strategy_states_pick ON draft_strategy_states(session_id, pick_number);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_completion_paths_signature ON roster_completion_paths(roster_signature);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_completion_paths_picks ON roster_completion_paths(remaining_picks, draft_position);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tier_values_position ON position_tier_values(position, tier_number);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_strategy_params_position ON strategy_parameters(draft_position, round_number);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_pick_probs_session ON pick_probabilities(session_id, pick_number);")
        
        conn.commit()
        print("✅ Strategy optimization schema created successfully")
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insert_position_tiers():
    """Insert default position tier definitions"""
    print("📊 Inserting position tier values...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Define position tiers based on typical fantasy values
    position_tiers = [
        # QB tiers - lower base values, QB is less critical in 10-team
        ('QB', 1, 'Elite', 1, 3, 85.0, 1.2),  # Top 3 QBs
        ('QB', 2, 'Tier 1', 4, 8, 75.0, 1.0),  # Next 5 QBs
        ('QB', 3, 'Tier 2', 9, 15, 65.0, 0.9),  # Streaming options
        
        # RB tiers - highest base values due to scarcity
        ('RB', 1, 'Elite', 1, 4, 120.0, 1.5),  # True bellcows
        ('RB', 2, 'Tier 1', 5, 12, 100.0, 1.3),  # Solid RB1s
        ('RB', 3, 'Tier 2', 13, 24, 80.0, 1.2),  # Flex worthy RBs
        ('RB', 4, 'Tier 3', 25, 36, 65.0, 1.0),  # Depth pieces
        ('RB', 5, 'Dart Throws', 37, 60, 45.0, 0.8),  # Upside plays
        
        # WR tiers - high volume, good depth
        ('WR', 1, 'Elite', 1, 5, 110.0, 1.4),  # True alpha WRs
        ('WR', 2, 'Tier 1', 6, 15, 95.0, 1.2),  # Solid WR1s
        ('WR', 3, 'Tier 2', 16, 30, 80.0, 1.1),  # Good WR2s
        ('WR', 4, 'Tier 3', 31, 45, 65.0, 1.0),  # Flex options
        ('WR', 5, 'Depth', 46, 75, 50.0, 0.9),  # Bench/upside
        
        # TE tiers - big gap between elite and rest
        ('TE', 1, 'Elite', 1, 3, 95.0, 1.8),  # Game changers
        ('TE', 2, 'Tier 1', 4, 8, 70.0, 1.2),  # Solid starters
        ('TE', 3, 'Streaming', 9, 20, 55.0, 1.0),  # Matchup plays
        ('TE', 4, 'Deep', 21, 30, 40.0, 0.8),  # Desperation
        
        # K/DST tiers - lowest priority
        ('K', 1, 'Top', 1, 5, 25.0, 1.0),
        ('K', 2, 'Streaming', 6, 20, 20.0, 1.0),
        ('DST', 1, 'Top', 1, 5, 30.0, 1.0),
        ('DST', 2, 'Streaming', 6, 15, 25.0, 1.0),
    ]
    
    try:
        for pos, tier, name, min_rank, max_rank, base_val, scarcity in position_tiers:
            cur.execute("""
                INSERT INTO position_tier_values 
                (position, tier_number, tier_name, min_rank, max_rank, base_value, scarcity_multiplier)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (position, tier_number) DO UPDATE SET
                base_value = EXCLUDED.base_value,
                scarcity_multiplier = EXCLUDED.scarcity_multiplier
            """, (pos, tier, name, min_rank, max_rank, base_val, scarcity))
        
        conn.commit()
        print("✅ Position tier values inserted")
        
        # Show inserted tiers
        cur.execute("""
            SELECT position, tier_name, min_rank, max_rank, base_value, scarcity_multiplier 
            FROM position_tier_values 
            ORDER BY position, tier_number
        """)
        
        print("\n📋 Position Tier Structure:")
        current_pos = None
        for pos, tier_name, min_rank, max_rank, base_val, scarcity in cur.fetchall():
            if pos != current_pos:
                print(f"\n{pos}:")
                current_pos = pos
            print(f"  {tier_name}: Ranks {min_rank}-{max_rank}, Value: {base_val}, Scarcity: {scarcity}x")
        
    except Exception as e:
        print(f"❌ Error inserting tier values: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def insert_strategy_parameters():
    """Insert draft position-specific strategy parameters"""
    print("⚙️  Inserting strategy optimization parameters...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Strategy parameters by draft position
    strategy_params = [
        # Pick 1 parameters
        (1, None, 'rb_bonus_early', 1.2, 'RB bonus in early rounds for Pick 1'),
        (1, None, 'wr_bonus_late', 1.1, 'WR bonus in late rounds for Pick 1'),
        (1, 1, 'must_take_elite', 1.5, 'Must take elite player in round 1'),
        
        # Picks 2-5 parameters  
        (2, None, 'balanced_approach', 1.0, 'Balanced strategy for picks 2-5'),
        (3, None, 'balanced_approach', 1.0, 'Balanced strategy for picks 2-5'),
        (4, None, 'balanced_approach', 1.0, 'Balanced strategy for picks 2-5'),
        (5, None, 'balanced_approach', 1.0, 'Balanced strategy for picks 2-5'),
        
        # Picks 6-9 parameters
        (6, None, 'upside_bonus', 1.3, 'Upside player bonus for picks 6-9'),
        (7, None, 'upside_bonus', 1.3, 'Upside player bonus for picks 6-9'),
        (8, None, 'upside_bonus', 1.3, 'Upside player bonus for picks 6-9'),
        (9, None, 'upside_bonus', 1.3, 'Upside player bonus for picks 6-9'),
        
        # Pick 10 parameters
        (10, None, 'turn_advantage', 1.4, 'Double pick advantage for Pick 10'),
        (10, None, 'position_run_starter', 1.2, 'Can start position runs'),
        
        # Round-specific parameters (all positions - use 0 for draft_position)
        (0, 1, 'no_qb_penalty', 0.7, 'QB penalty in round 1 for all positions'),
        (0, 2, 'no_qb_penalty', 0.8, 'QB penalty in round 2 for all positions'),
        (0, 3, 'no_te_penalty', 0.9, 'TE penalty in round 3 for all positions'),
        (0, 14, 'dst_bonus', 1.1, 'DST bonus in round 14 for all positions'),
        (0, 15, 'k_bonus', 1.1, 'K bonus in round 15 for all positions'),
    ]
    
    try:
        for draft_pos, round_num, param_name, param_val, description in strategy_params:
            cur.execute("""
                INSERT INTO strategy_parameters 
                (draft_position, round_number, parameter_name, parameter_value, description)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (draft_position, round_number, parameter_name) 
                DO UPDATE SET parameter_value = EXCLUDED.parameter_value
            """, (draft_pos, round_num, param_name, param_val, description))
        
        conn.commit()
        print("✅ Strategy parameters inserted")
        
        # Show parameters by draft position
        cur.execute("""
            SELECT draft_position, round_number, parameter_name, parameter_value
            FROM strategy_parameters 
            ORDER BY draft_position NULLS LAST, round_number NULLS LAST, parameter_name
        """)
        
        print("\n📋 Strategy Parameters:")
        for draft_pos, round_num, param_name, param_val in cur.fetchall():
            pos_str = f"Pick {draft_pos}" if draft_pos and draft_pos > 0 else "All Positions"
            round_str = f"Round {round_num}" if round_num else "All Rounds"
            print(f"  {pos_str}, {round_str}: {param_name} = {param_val}")
        
    except Exception as e:
        print(f"❌ Error inserting strategy parameters: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def main():
    print("🚀 Setting up dynamic strategy optimization system...\n")
    
    # Create schema
    create_optimization_tables()
    print()
    
    # Insert tier definitions
    insert_position_tiers()
    print()
    
    # Insert strategy parameters
    insert_strategy_parameters()
    
    print("\n🎉 Strategy optimization system ready!")
    print("Next steps:")
    print("  1. Build dynamic programming optimization engine")
    print("  2. Create position path generator")
    print("  3. Implement player assignment optimizer")
    print("  4. Add live strategy adaptation")

if __name__ == "__main__":
    main()
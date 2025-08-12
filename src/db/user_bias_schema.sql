-- User Bias System Database Schema Extensions
-- Extends existing fantasy_draft_db with user preference and bias tracking

-- User preferences for team and strategy biases
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) DEFAULT 'default',  -- Support multiple users/sessions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Team biases
    favorite_teams TEXT[],  -- Array of team abbreviations ['KC', 'SF', 'DAL']
    favorite_team_multiplier DECIMAL(3,2) DEFAULT 1.2,  -- 1.2x boost for favorite teams
    hated_teams TEXT[],     -- Array of team abbreviations to avoid
    hated_team_multiplier DECIMAL(3,2) DEFAULT 0.8,     -- 0.8x penalty for hated teams
    
    -- Risk strategy preferences (affects CV weighting)
    strategy_type VARCHAR(20) DEFAULT 'balanced' CHECK (strategy_type IN ('conservative', 'balanced', 'aggressive')),
    cv_weight DECIMAL(3,2) DEFAULT 1.0,  -- How much to weight coefficient of variation
    
    -- Advanced preferences
    positional_scarcity_weight DECIMAL(3,2) DEFAULT 1.0,  -- Weight position scarcity in rankings
    news_sensitivity DECIMAL(3,2) DEFAULT 1.0,           -- Future: how much to react to news
    
    UNIQUE(user_session)
);

-- Individual player adjustments and biases
CREATE TABLE IF NOT EXISTS player_adjustments (
    adjustment_id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) DEFAULT 'default',
    player_id INTEGER REFERENCES players(player_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Player-specific bias
    bias_multiplier DECIMAL(3,2) DEFAULT 1.0,  -- Custom multiplier for this player
    bias_reason VARCHAR(500),                   -- User notes explaining the bias
    
    -- Special flags
    must_draft BOOLEAN DEFAULT FALSE,           -- Force high ranking
    avoid_player BOOLEAN DEFAULT FALSE,         -- Force low ranking
    
    -- Future news integration
    news_impact_score DECIMAL(3,2) DEFAULT 0.0, -- -1.0 to 1.0 based on news sentiment
    last_news_update TIMESTAMP,
    
    UNIQUE(user_session, player_id)
);

-- Calculated adjusted rankings (materialized for performance)
CREATE TABLE IF NOT EXISTS adjusted_rankings (
    ranking_id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) DEFAULT 'default',
    player_id INTEGER REFERENCES players(player_id),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Original values
    original_adp DECIMAL(5,1),
    original_ordinal_rank INTEGER,
    coefficient_of_variation DECIMAL(4,3),
    
    -- Bias components
    team_multiplier DECIMAL(3,2) DEFAULT 1.0,
    player_multiplier DECIMAL(3,2) DEFAULT 1.0,
    cv_strategy_multiplier DECIMAL(3,2) DEFAULT 1.0,
    news_multiplier DECIMAL(3,2) DEFAULT 1.0,
    
    -- Final adjusted values
    adjusted_adp DECIMAL(5,1),
    adjusted_ordinal_rank INTEGER,
    bias_impact DECIMAL(3,2),  -- How much bias changed the ranking (-1.0 to 1.0)
    
    UNIQUE(user_session, player_id)
);

-- Strategy analysis and recommendations
CREATE TABLE IF NOT EXISTS strategy_analysis (
    analysis_id SERIAL PRIMARY KEY,
    user_session VARCHAR(100) DEFAULT 'default',
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Roster construction predictions based on biases
    predicted_qb_picks INTEGER[],
    predicted_rb_picks INTEGER[],
    predicted_wr_picks INTEGER[],
    predicted_te_picks INTEGER[],
    predicted_k_picks INTEGER[],
    predicted_dst_picks INTEGER[],
    
    -- Risk analysis
    portfolio_risk_score DECIMAL(3,2),     -- Overall risk of draft strategy
    expected_value_boost DECIMAL(3,2),     -- Expected benefit from biases
    strategy_alignment_score DECIMAL(3,2)  -- How well biases match stated strategy
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_adjustments_session ON player_adjustments(user_session);
CREATE INDEX IF NOT EXISTS idx_adjusted_rankings_session ON adjusted_rankings(user_session);
CREATE INDEX IF NOT EXISTS idx_adjusted_rankings_adp ON adjusted_rankings(adjusted_adp);

-- Function to recalculate adjusted rankings
CREATE OR REPLACE FUNCTION recalculate_adjusted_rankings(session_name VARCHAR DEFAULT 'default')
RETURNS INTEGER AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Delete old calculations
    DELETE FROM adjusted_rankings WHERE user_session = session_name;
    
    -- Recalculate with current biases
    INSERT INTO adjusted_rankings (
        user_session, player_id, original_adp, original_ordinal_rank,
        coefficient_of_variation, team_multiplier, player_multiplier,
        cv_strategy_multiplier, adjusted_adp, adjusted_ordinal_rank, bias_impact
    )
    SELECT 
        session_name,
        p.player_id,
        COALESCE(adp.avg_adp, 999.0) as original_adp,
        ROW_NUMBER() OVER (ORDER BY COALESCE(adp.avg_adp, 999.0)) as original_ordinal_rank,
        COALESCE(pr.stdev_rank / NULLIF(pr.mean_rank, 0), 0) as coefficient_of_variation,
        
        -- Team multiplier
        CASE 
            WHEN p.team = ANY(up.favorite_teams) THEN up.favorite_team_multiplier
            WHEN p.team = ANY(up.hated_teams) THEN up.hated_team_multiplier
            ELSE 1.0
        END as team_multiplier,
        
        -- Player multiplier
        COALESCE(pa.bias_multiplier, 1.0) as player_multiplier,
        
        -- CV strategy multiplier (affects ranking based on risk preference)
        CASE up.strategy_type
            WHEN 'conservative' THEN 1.0 - (COALESCE(pr.stdev_rank / NULLIF(pr.mean_rank, 0), 0) * 0.3)
            WHEN 'aggressive' THEN 1.0 + (COALESCE(pr.stdev_rank / NULLIF(pr.mean_rank, 0), 0) * 0.2)
            ELSE 1.0
        END as cv_strategy_multiplier,
        
        -- Calculate adjusted ADP
        COALESCE(adp.avg_adp, 999.0) * 
        CASE 
            WHEN p.team = ANY(up.favorite_teams) THEN up.favorite_team_multiplier
            WHEN p.team = ANY(up.hated_teams) THEN up.hated_team_multiplier
            ELSE 1.0
        END * 
        COALESCE(pa.bias_multiplier, 1.0) *
        CASE up.strategy_type
            WHEN 'conservative' THEN 1.0 - (COALESCE(pr.stdev_rank / NULLIF(pr.mean_rank, 0), 0) * 0.3)
            WHEN 'aggressive' THEN 1.0 + (COALESCE(pr.stdev_rank / NULLIF(pr.mean_rank, 0), 0) * 0.2)
            ELSE 1.0
        END as adjusted_adp,
        
        -- Will be updated with ranking after insert
        0 as adjusted_ordinal_rank,
        0 as bias_impact
        
    FROM players p
    LEFT JOIN player_adp adp ON p.player_id = adp.player_id
    LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
    LEFT JOIN user_preferences up ON up.user_session = session_name
    LEFT JOIN player_adjustments pa ON p.player_id = pa.player_id AND pa.user_session = session_name;
    
    -- Update ordinal rankings based on adjusted ADP
    WITH ranked_players AS (
        SELECT ranking_id, 
               ROW_NUMBER() OVER (ORDER BY adjusted_adp) as new_ordinal_rank
        FROM adjusted_rankings 
        WHERE user_session = session_name
    )
    UPDATE adjusted_rankings ar
    SET adjusted_ordinal_rank = rp.new_ordinal_rank,
        bias_impact = (ar.original_ordinal_rank - rp.new_ordinal_rank) / NULLIF(ar.original_ordinal_rank::DECIMAL, 0)
    FROM ranked_players rp
    WHERE ar.ranking_id = rp.ranking_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    RETURN rows_affected;
END;
$$ LANGUAGE plpgsql;

-- Initialize default user preferences
INSERT INTO user_preferences (user_session) 
VALUES ('default')
ON CONFLICT (user_session) DO NOTHING;
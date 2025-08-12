-- ALFRED Draft Management Schema
-- Creates tables for managing live fantasy football drafts

-- Draft configuration table
CREATE TABLE IF NOT EXISTS draft_config (
    draft_id SERIAL PRIMARY KEY,
    draft_name VARCHAR(100) DEFAULT 'ALFRED Draft',
    num_teams INTEGER DEFAULT 10,
    roster_positions JSONB DEFAULT '{"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DST": 1, "BENCH": 6}',
    rounds INTEGER DEFAULT 15,
    seconds_per_pick INTEGER DEFAULT 90,
    snake_draft BOOLEAN DEFAULT TRUE,
    current_pick INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Team information for drafts
CREATE TABLE IF NOT EXISTS draft_teams (
    team_id SERIAL PRIMARY KEY,
    draft_id INTEGER REFERENCES draft_config(draft_id) ON DELETE CASCADE,
    team_number INTEGER NOT NULL,
    team_name VARCHAR(100),
    owner_name VARCHAR(100),
    draft_position INTEGER,
    is_auto_draft BOOLEAN DEFAULT FALSE,
    UNIQUE(draft_id, team_number)
);

-- Extend draft_picks table if needed
ALTER TABLE draft_picks ADD COLUMN IF NOT EXISTS roster_position VARCHAR(10);
ALTER TABLE draft_picks ADD COLUMN IF NOT EXISTS pick_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE draft_picks ADD COLUMN IF NOT EXISTS is_keeper BOOLEAN DEFAULT FALSE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_draft_picks_draft_id ON draft_picks(draft_id);
CREATE INDEX IF NOT EXISTS idx_draft_picks_player_id ON draft_picks(player_id);
CREATE INDEX IF NOT EXISTS idx_draft_teams_draft_id ON draft_teams(draft_id);

-- View for getting current draft state
CREATE OR REPLACE VIEW draft_state AS
SELECT 
    dc.draft_id,
    dc.draft_name,
    dc.num_teams,
    dc.current_pick,
    dc.rounds,
    dc.is_active,
    COUNT(DISTINCT dp.pick_id) as total_picks,
    CEIL(dc.current_pick::FLOAT / dc.num_teams) as current_round,
    CASE 
        WHEN dc.snake_draft AND CEIL(dc.current_pick::FLOAT / dc.num_teams)::INT % 2 = 0 
        THEN dc.num_teams - ((dc.current_pick - 1) % dc.num_teams)
        ELSE ((dc.current_pick - 1) % dc.num_teams) + 1
    END as current_team_picking
FROM draft_config dc
LEFT JOIN draft_picks dp ON dc.draft_id = dp.draft_id
GROUP BY dc.draft_id;

-- View for team rosters
CREATE OR REPLACE VIEW team_rosters AS
SELECT 
    dt.draft_id,
    dt.team_number,
    dt.team_name,
    dt.owner_name,
    p.player_id,
    p.name as player_name,
    p.position,
    p.team,
    dp.pick_number,
    dp.round,
    dp.roster_position
FROM draft_teams dt
LEFT JOIN draft_picks dp ON dt.draft_id = dp.draft_id AND dt.team_number = dp.team_number
LEFT JOIN players p ON dp.player_id = p.player_id
ORDER BY dt.team_number, dp.pick_number;

-- Function to get undrafted players with ADP
CREATE OR REPLACE FUNCTION get_undrafted_players(draft_id_param INTEGER)
RETURNS TABLE (
    player_id INTEGER,
    name VARCHAR,
    position VARCHAR,
    team VARCHAR,
    avg_adp NUMERIC,
    consensus_rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.player_id,
        p.name,
        p.position,
        p.team,
        ROUND(AVG(ar.adp_value), 1) as avg_adp,
        MIN(pr.overall_rank) as consensus_rank
    FROM players p
    LEFT JOIN adp_rankings ar ON p.player_id = ar.player_id
    LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
    WHERE p.player_id NOT IN (
        SELECT player_id FROM draft_picks WHERE draft_id = draft_id_param
    )
    AND p.is_active = TRUE
    GROUP BY p.player_id, p.name, p.position, p.team
    ORDER BY COALESCE(AVG(ar.adp_value), 999), COALESCE(MIN(pr.overall_rank), 999);
END;
$$ LANGUAGE plpgsql;

-- Insert a default draft configuration for testing
INSERT INTO draft_config (draft_name, num_teams, is_active) 
VALUES ('Test Draft', 10, TRUE)
ON CONFLICT DO NOTHING;

-- Insert default teams for the test draft
INSERT INTO draft_teams (draft_id, team_number, team_name, owner_name, draft_position)
SELECT 
    (SELECT draft_id FROM draft_config WHERE draft_name = 'Test Draft' LIMIT 1),
    team_num,
    'Team ' || team_num,
    'Owner ' || team_num,
    team_num
FROM generate_series(1, 10) as team_num
ON CONFLICT DO NOTHING;
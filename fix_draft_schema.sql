-- Fix draft schema to work with existing tables

-- Add draft_id column to link with our new draft_config
ALTER TABLE draft_picks ADD COLUMN IF NOT EXISTS draft_id INTEGER REFERENCES draft_config(draft_id);

-- Create indexes for the new column
CREATE INDEX IF NOT EXISTS idx_draft_picks_draft_id ON draft_picks(draft_id);

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
    dp.round_number as round,
    dp.roster_position
FROM draft_teams dt
LEFT JOIN draft_picks dp ON dt.draft_id = dp.draft_id AND dt.team_number = dp.team_number
LEFT JOIN players p ON dp.player_id = p.player_id
ORDER BY dt.team_number, dp.pick_number;

-- Function to get undrafted players with ADP (fixed)
CREATE OR REPLACE FUNCTION get_undrafted_players(draft_id_param INTEGER)
RETURNS TABLE (
    player_id INTEGER,
    player_name VARCHAR,
    player_position VARCHAR,
    player_team VARCHAR,
    avg_adp NUMERIC,
    consensus_rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.player_id,
        p.name::VARCHAR as player_name,
        p.position::VARCHAR as player_position,
        p.team::VARCHAR as player_team,
        ROUND(AVG(ar.adp_value), 1) as avg_adp,
        MIN(pr.overall_rank) as consensus_rank
    FROM players p
    LEFT JOIN adp_rankings ar ON p.player_id = ar.player_id
    LEFT JOIN player_rankings pr ON p.player_id = pr.player_id
    WHERE p.player_id NOT IN (
        SELECT dp2.player_id FROM draft_picks dp2 WHERE dp2.draft_id = draft_id_param AND dp2.player_id IS NOT NULL
    )
    AND p.is_active = TRUE
    GROUP BY p.player_id, p.name, p.position, p.team
    ORDER BY COALESCE(AVG(ar.adp_value), 999), COALESCE(MIN(pr.overall_rank), 999);
END;
$$ LANGUAGE plpgsql;
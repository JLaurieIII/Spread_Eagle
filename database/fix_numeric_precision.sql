-- Fix NUMERIC precision for fields that can exceed 99.999
-- Run this after cbb_schema.sql

SET search_path TO cbb;

-- team_season_stats fixes
ALTER TABLE team_season_stats 
    ALTER COLUMN pace TYPE NUMERIC(6,2),
    ALTER COLUMN ts_true_shooting TYPE NUMERIC(6,3),
    ALTER COLUMN ts_rating TYPE NUMERIC(7,2),
    ALTER COLUMN ts_fg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_2pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_3pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_ft_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_tov_ratio TYPE NUMERIC(6,3),
    ALTER COLUMN ts_oreb_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_ft_rate TYPE NUMERIC(6,3),
    ALTER COLUMN os_true_shooting TYPE NUMERIC(6,3),
    ALTER COLUMN os_rating TYPE NUMERIC(7,2),
    ALTER COLUMN os_fg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_2pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_3pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_ft_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_tov_ratio TYPE NUMERIC(6,3),
    ALTER COLUMN os_oreb_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_ft_rate TYPE NUMERIC(6,3);

-- player_season_stats fixes  
ALTER TABLE player_season_stats
    ALTER COLUMN offensive_rating TYPE NUMERIC(7,2),
    ALTER COLUMN defensive_rating TYPE NUMERIC(7,2),
    ALTER COLUMN net_rating TYPE NUMERIC(7,2),
    ALTER COLUMN porpag TYPE NUMERIC(7,2),
    ALTER COLUMN usage TYPE NUMERIC(6,3),
    ALTER COLUMN ast_tov_ratio TYPE NUMERIC(6,2),
    ALTER COLUMN oreb_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ft_rate TYPE NUMERIC(6,3),
    ALTER COLUMN efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_pct TYPE NUMERIC(6,3),
    ALTER COLUMN fg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN two_pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN three_pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ft_pct TYPE NUMERIC(6,3);

-- game_team_stats fixes
ALTER TABLE game_team_stats
    ALTER COLUMN pace TYPE NUMERIC(7,2),
    ALTER COLUMN ts_possessions TYPE NUMERIC(7,2),
    ALTER COLUMN ts_true_shooting TYPE NUMERIC(7,3),
    ALTER COLUMN ts_rating TYPE NUMERIC(7,2),
    ALTER COLUMN ts_game_score TYPE NUMERIC(7,2),
    ALTER COLUMN ts_fg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_2pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_3pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_ft_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_ft_rate TYPE NUMERIC(6,3),
    ALTER COLUMN ts_tov_ratio TYPE NUMERIC(6,3),
    ALTER COLUMN ts_oreb_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_possessions TYPE NUMERIC(7,2),
    ALTER COLUMN os_true_shooting TYPE NUMERIC(7,3),
    ALTER COLUMN os_rating TYPE NUMERIC(7,2),
    ALTER COLUMN os_game_score TYPE NUMERIC(7,2),
    ALTER COLUMN os_fg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_2pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_3pt_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_ft_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN os_ft_rate TYPE NUMERIC(6,3),
    ALTER COLUMN os_tov_ratio TYPE NUMERIC(6,3),
    ALTER COLUMN os_oreb_pct TYPE NUMERIC(6,3);

-- game_player_stats fixes
ALTER TABLE game_player_stats
    ALTER COLUMN game_pace TYPE NUMERIC(7,2),
    ALTER COLUMN offensive_rating TYPE NUMERIC(7,2),
    ALTER COLUMN defensive_rating TYPE NUMERIC(7,2),
    ALTER COLUMN net_rating TYPE NUMERIC(7,2),
    ALTER COLUMN usage TYPE NUMERIC(6,3),
    ALTER COLUMN efg_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ts_pct TYPE NUMERIC(6,3),
    ALTER COLUMN ft_rate TYPE NUMERIC(6,3),
    ALTER COLUMN oreb_pct TYPE NUMERIC(6,3);

SELECT 'Numeric precision fixes applied successfully' as status;

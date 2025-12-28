--------------------------------------------------------------------------------
-- SPREAD EAGLE - College Basketball Schema
-- Database: PostgreSQL 14+
-- Schema: cbb
--
-- CHANGELOG:
-- 2024-12-24: Initial production schema
--   - Removed years from table names (data starts 2022, expandable)
--   - Fixed SMALLINT -> INTEGER for IDs exceeding 32,767
--   - Added proper primary/composite keys
--   - Added audit columns (created_at)
--   - Added security roles
--   - Comprehensive comments
--------------------------------------------------------------------------------

--------------------------------------------------------------------------------
-- SECURITY SETUP
-- Create roles for application access control
--------------------------------------------------------------------------------

-- Read-only role for dashboards/reporting
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cbb_readonly') THEN
        CREATE ROLE cbb_readonly NOLOGIN;
    END IF;
END
$$;

-- Read-write role for ETL/ingestion
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'cbb_readwrite') THEN
        CREATE ROLE cbb_readwrite NOLOGIN;
    END IF;
END
$$;

--------------------------------------------------------------------------------
-- SCHEMA SETUP
--------------------------------------------------------------------------------

CREATE SCHEMA IF NOT EXISTS cbb;
SET search_path TO cbb;

-- Grant schema access
GRANT USAGE ON SCHEMA cbb TO cbb_readonly;
GRANT USAGE ON SCHEMA cbb TO cbb_readwrite;

-- Default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA cbb GRANT SELECT ON TABLES TO cbb_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA cbb GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cbb_readwrite;

--------------------------------------------------------------------------------
-- REFERENCE TABLES
-- Static/slowly-changing dimension tables
--------------------------------------------------------------------------------

-- Conferences (Power 5, mid-majors, etc.)
DROP TABLE IF EXISTS conferences CASCADE;
CREATE TABLE conferences (
    id              INTEGER PRIMARY KEY,          -- API-provided ID
    source_id       INTEGER,                      -- External source ID (ESPN, etc.)
    name            VARCHAR(100),                 -- Full name: "Southeastern Conference"
    abbreviation    VARCHAR(20),                  -- Short: "SEC"
    short_name      VARCHAR(50),                  -- Display: "SEC"
    created_at      TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE conferences IS 'NCAA basketball conferences (D1, D2, D3, NAIA, etc.)';

-- Venues/Arenas
DROP TABLE IF EXISTS venues CASCADE;
CREATE TABLE venues (
    id              INTEGER PRIMARY KEY,
    source_id       INTEGER,
    name            VARCHAR(150),                 -- "Cameron Indoor Stadium"
    city            VARCHAR(100),
    state           VARCHAR(50),
    country         VARCHAR(50) DEFAULT 'USA',
    created_at      TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE venues IS 'Basketball arenas and venues';

-- Teams
DROP TABLE IF EXISTS teams CASCADE;
CREATE TABLE teams (
    id                  INTEGER PRIMARY KEY,
    source_id           VARCHAR(50),              -- External ID (string for flexibility)
    school              VARCHAR(100),             -- "Duke"
    mascot              VARCHAR(100),             -- "Blue Devils"
    abbreviation        VARCHAR(20),              -- "DUKE"
    display_name        VARCHAR(150),             -- "Duke Blue Devils"
    short_display_name  VARCHAR(100),             -- "Duke"
    primary_color       VARCHAR(20),              -- Hex: "#003087"
    secondary_color     VARCHAR(20),              -- Hex: "#FFFFFF"

    -- Current venue (can change)
    current_venue_id    INTEGER REFERENCES venues(id),
    current_venue       VARCHAR(150),             -- Denormalized for convenience
    current_city        VARCHAR(100),
    current_state       VARCHAR(50),

    -- Conference (can change yearly)
    conference_id       INTEGER REFERENCES conferences(id),
    conference          VARCHAR(100),             -- Denormalized for convenience

    created_at          TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE teams IS 'All basketball teams (D1, D2, etc.)';

CREATE INDEX idx_teams_conference ON teams(conference_id);

--------------------------------------------------------------------------------
-- GAME TABLES
-- Core fact tables for games and betting
--------------------------------------------------------------------------------

-- Games (one row per game)
DROP TABLE IF EXISTS games CASCADE;
CREATE TABLE games (
    id                  INTEGER PRIMARY KEY,      -- API game ID
    source_id           INTEGER,                  -- External source ID

    -- Season info
    season              SMALLINT NOT NULL,        -- Academic year: 2024 = 2023-24 season
    season_label        INTEGER,                  -- Alternative label format
    season_type         VARCHAR(20),              -- "regular", "postseason"
    tournament          VARCHAR(50),              -- "NCAA Tournament", "NIT", etc.

    -- Game metadata
    start_date          TIMESTAMP WITH TIME ZONE,
    start_time_tbd      BOOLEAN DEFAULT FALSE,
    neutral_site        BOOLEAN DEFAULT FALSE,
    conference_game     BOOLEAN DEFAULT FALSE,
    game_type           VARCHAR(50),              -- Exhibition, regular, etc.
    status              VARCHAR(20),              -- "final", "scheduled", etc.
    game_notes          TEXT,                     -- Any special notes
    attendance          INTEGER,

    -- Home team
    home_team_id        INTEGER REFERENCES teams(id),
    home_team           VARCHAR(100),             -- Denormalized
    home_conference_id  INTEGER,
    home_conference     VARCHAR(100),
    home_seed           SMALLINT,                 -- Tournament seed (1-16)
    home_points         SMALLINT,
    home_period_points  JSONB,                    -- [35, 42] for halves
    home_winner         BOOLEAN,

    -- Away team
    away_team_id        INTEGER REFERENCES teams(id),
    away_team           VARCHAR(100),
    away_conference_id  INTEGER,
    away_conference     VARCHAR(100),
    away_seed           SMALLINT,
    away_points         SMALLINT,
    away_period_points  JSONB,
    away_winner         BOOLEAN,

    -- Venue
    venue_id            INTEGER REFERENCES venues(id),
    venue               VARCHAR(150),
    city                VARCHAR(100),
    state               VARCHAR(50),

    -- Analytics
    excitement          NUMERIC(6,3),             -- Game excitement index

    created_at          TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE games IS 'All basketball games with final scores';

CREATE INDEX idx_games_season ON games(season);
CREATE INDEX idx_games_start_date ON games(start_date);
CREATE INDEX idx_games_home_team ON games(home_team_id);
CREATE INDEX idx_games_away_team ON games(away_team_id);
CREATE INDEX idx_games_season_type ON games(season, season_type);

-- Betting Lines (one row per game per sportsbook)
DROP TABLE IF EXISTS betting_lines CASCADE;
CREATE TABLE betting_lines (
    id                  SERIAL PRIMARY KEY,       -- Auto-generated
    game_id             INTEGER NOT NULL REFERENCES games(id),

    -- Game context (denormalized for query convenience)
    season              SMALLINT NOT NULL,
    season_type         VARCHAR(20),
    start_date          TIMESTAMP WITH TIME ZONE,

    -- Teams (denormalized)
    home_team_id        INTEGER,
    home_team           VARCHAR(100),
    home_conference     VARCHAR(100),
    home_score          NUMERIC(5,1),             -- Actual final score
    away_team_id        INTEGER,
    away_team           VARCHAR(100),
    away_conference     VARCHAR(100),
    away_score          NUMERIC(5,1),

    -- Betting lines
    provider            VARCHAR(50),              -- "ESPN BET", "DraftKings", etc.
    spread              NUMERIC(5,1),             -- Home team spread (-6.5 = home favored)
    spread_open         NUMERIC(5,1),             -- Opening spread
    over_under          NUMERIC(5,1),             -- Total points line
    over_under_open     NUMERIC(5,1),             -- Opening total
    home_moneyline      INTEGER,                  -- -260, +150, etc.
    away_moneyline      INTEGER,

    created_at          TIMESTAMP DEFAULT NOW()
);
COMMENT ON TABLE betting_lines IS 'Betting lines from sportsbooks - core table for ATS analysis';

CREATE INDEX idx_lines_game ON betting_lines(game_id);
CREATE INDEX idx_lines_season ON betting_lines(season);
CREATE INDEX idx_lines_provider ON betting_lines(provider);
CREATE INDEX idx_lines_home_team ON betting_lines(home_team_id);
CREATE INDEX idx_lines_away_team ON betting_lines(away_team_id);

--------------------------------------------------------------------------------
-- GAME STATS TABLES
-- Per-game performance statistics
--------------------------------------------------------------------------------

-- Team Game Stats (two rows per game - one per team)
DROP TABLE IF EXISTS game_team_stats CASCADE;
CREATE TABLE game_team_stats (
    id                  SERIAL PRIMARY KEY,
    game_id             INTEGER NOT NULL REFERENCES games(id),
    team_id             INTEGER NOT NULL,

    -- Game context
    season              SMALLINT NOT NULL,
    season_label        INTEGER,
    season_type         VARCHAR(20),
    tournament          VARCHAR(50),
    start_date          TIMESTAMP WITH TIME ZONE,
    start_time_tbd      BOOLEAN,

    -- Team info
    team                VARCHAR(100),
    conference          VARCHAR(100),
    team_seed           SMALLINT,

    -- Opponent info
    opponent_id         INTEGER,
    opponent            VARCHAR(100),
    opponent_conference VARCHAR(100),
    opponent_seed       SMALLINT,

    -- Game situation
    neutral_site        BOOLEAN,
    is_home             BOOLEAN,
    conference_game     BOOLEAN,
    game_type           VARCHAR(50),
    notes               TEXT,

    -- Game totals
    game_minutes        NUMERIC(5,1),
    pace                NUMERIC(6,2),             -- Possessions per 40 min

    -- Team stats (ts_ prefix)
    ts_possessions      NUMERIC(6,2),
    ts_assists          NUMERIC(5,1),
    ts_steals           NUMERIC(5,1),
    ts_blocks           NUMERIC(5,1),
    ts_true_shooting    NUMERIC(6,3),
    ts_rating           NUMERIC(6,2),
    ts_game_score       NUMERIC(6,2),
    ts_points_total     NUMERIC(5,1),
    ts_points_by_period JSONB,
    ts_points_largest_lead NUMERIC(5,1),
    ts_points_fastbreak NUMERIC(5,1),
    ts_points_in_paint  NUMERIC(5,1),
    ts_points_off_turnovers NUMERIC(5,1),
    ts_fg_made          NUMERIC(5,1),
    ts_fg_attempted     NUMERIC(5,1),
    ts_fg_pct           NUMERIC(5,3),
    ts_2pt_made         NUMERIC(5,1),
    ts_2pt_attempted    NUMERIC(5,1),
    ts_2pt_pct          NUMERIC(5,3),
    ts_3pt_made         NUMERIC(5,1),
    ts_3pt_attempted    NUMERIC(5,1),
    ts_3pt_pct          NUMERIC(5,3),
    ts_ft_made          NUMERIC(5,1),
    ts_ft_attempted     NUMERIC(5,1),
    ts_ft_pct           NUMERIC(5,3),
    ts_turnovers_total  NUMERIC(5,1),
    ts_turnovers_team   NUMERIC(5,1),
    ts_reb_offensive    NUMERIC(5,1),
    ts_reb_defensive    NUMERIC(5,1),
    ts_reb_total        NUMERIC(5,1),
    ts_fouls_total      NUMERIC(5,1),
    ts_fouls_technical  NUMERIC(5,1),
    ts_fouls_flagrant   NUMERIC(5,1),
    ts_efg_pct          NUMERIC(5,3),
    ts_ft_rate          NUMERIC(5,3),
    ts_tov_ratio        NUMERIC(5,3),
    ts_oreb_pct         NUMERIC(5,3),

    -- Opponent stats (os_ prefix)
    os_possessions      NUMERIC(6,2),
    os_assists          NUMERIC(5,1),
    os_steals           NUMERIC(5,1),
    os_blocks           NUMERIC(5,1),
    os_true_shooting    NUMERIC(6,3),
    os_rating           NUMERIC(6,2),
    os_game_score       NUMERIC(6,2),
    os_points_total     NUMERIC(5,1),
    os_points_by_period JSONB,
    os_points_largest_lead NUMERIC(5,1),
    os_points_fastbreak NUMERIC(5,1),
    os_points_in_paint  NUMERIC(5,1),
    os_points_off_turnovers NUMERIC(5,1),
    os_fg_made          NUMERIC(5,1),
    os_fg_attempted     NUMERIC(5,1),
    os_fg_pct           NUMERIC(5,3),
    os_2pt_made         NUMERIC(5,1),
    os_2pt_attempted    NUMERIC(5,1),
    os_2pt_pct          NUMERIC(5,3),
    os_3pt_made         NUMERIC(5,1),
    os_3pt_attempted    NUMERIC(5,1),
    os_3pt_pct          NUMERIC(5,3),
    os_ft_made          NUMERIC(5,1),
    os_ft_attempted     NUMERIC(5,1),
    os_ft_pct           NUMERIC(5,3),
    os_turnovers_total  NUMERIC(5,1),
    os_turnovers_team   NUMERIC(5,1),
    os_reb_offensive    NUMERIC(5,1),
    os_reb_defensive    NUMERIC(5,1),
    os_reb_total        NUMERIC(5,1),
    os_fouls_total      NUMERIC(5,1),
    os_fouls_technical  NUMERIC(5,1),
    os_fouls_flagrant   NUMERIC(5,1),
    os_efg_pct          NUMERIC(5,3),
    os_ft_rate          NUMERIC(5,3),
    os_tov_ratio        NUMERIC(5,3),
    os_oreb_pct         NUMERIC(5,3),

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(game_id, team_id)
);
COMMENT ON TABLE game_team_stats IS 'Per-game team statistics (two rows per game) - variance analysis';

CREATE INDEX idx_gts_game ON game_team_stats(game_id);
CREATE INDEX idx_gts_team ON game_team_stats(team_id);
CREATE INDEX idx_gts_season ON game_team_stats(season);
CREATE INDEX idx_gts_opponent ON game_team_stats(opponent_id);

-- Player Game Stats (per player per game)
DROP TABLE IF EXISTS game_player_stats CASCADE;
CREATE TABLE game_player_stats (
    id                  SERIAL PRIMARY KEY,
    game_id             INTEGER NOT NULL REFERENCES games(id),
    team_id             INTEGER NOT NULL,
    athlete_id          INTEGER NOT NULL,

    -- Game context
    season              SMALLINT NOT NULL,
    season_label        INTEGER,
    season_type         VARCHAR(20),
    tournament          VARCHAR(50),
    start_date          TIMESTAMP WITH TIME ZONE,
    start_time_tbd      BOOLEAN,
    conference_game     BOOLEAN,
    neutral_site        BOOLEAN,
    is_home             BOOLEAN,
    game_type           VARCHAR(50),
    notes               TEXT,

    -- Team info
    team                VARCHAR(100),
    conference          VARCHAR(100),
    team_seed           SMALLINT,
    opponent_id         INTEGER,
    opponent            VARCHAR(100),
    opponent_conference VARCHAR(100),
    opponent_seed       SMALLINT,

    -- Game-level
    game_minutes        SMALLINT,
    game_pace           NUMERIC(6,2),

    -- Player info
    athlete_source_id   INTEGER,
    name                VARCHAR(100),
    position            VARCHAR(20),
    starter             BOOLEAN,
    ejected             BOOLEAN,

    -- Player stats
    minutes             NUMERIC(5,1),
    points              NUMERIC(5,1),
    turnovers           NUMERIC(5,1),
    fouls               NUMERIC(5,1),
    assists             NUMERIC(5,1),
    steals              NUMERIC(5,1),
    blocks              NUMERIC(5,1),
    game_score          NUMERIC(6,2),

    -- Advanced stats
    offensive_rating    NUMERIC(6,2),
    defensive_rating    NUMERIC(6,2),
    net_rating          NUMERIC(6,2),
    usage               NUMERIC(5,3),
    efg_pct             NUMERIC(5,3),
    ts_pct              NUMERIC(5,3),
    ast_tov_ratio       NUMERIC(5,2),
    ft_rate             NUMERIC(5,3),
    oreb_pct            NUMERIC(5,3),

    -- Shooting (JSONB for flexibility)
    field_goals         JSONB,
    two_point_fg        JSONB,
    three_point_fg      JSONB,
    free_throws         JSONB,
    rebounds            JSONB,

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(game_id, team_id, athlete_id)
);
COMMENT ON TABLE game_player_stats IS 'Per-game player box scores';

CREATE INDEX idx_gps_game ON game_player_stats(game_id);
CREATE INDEX idx_gps_team ON game_player_stats(team_id);
CREATE INDEX idx_gps_athlete ON game_player_stats(athlete_id);
CREATE INDEX idx_gps_season ON game_player_stats(season);

--------------------------------------------------------------------------------
-- SEASON AGGREGATE TABLES
-- Aggregated season-level statistics
--------------------------------------------------------------------------------

-- Team Season Stats (one row per team per season)
DROP TABLE IF EXISTS team_season_stats CASCADE;
CREATE TABLE team_season_stats (
    id                  SERIAL PRIMARY KEY,
    season              SMALLINT NOT NULL,
    season_label        INTEGER,
    team_id             INTEGER NOT NULL,
    team                VARCHAR(100),
    conference          VARCHAR(100),

    -- Record
    games               SMALLINT,
    wins                SMALLINT,
    losses              SMALLINT,
    total_minutes       SMALLINT,
    pace                NUMERIC(6,2),

    -- Team offensive stats (ts_ prefix)
    ts_assists          SMALLINT,
    ts_blocks           SMALLINT,
    ts_steals           SMALLINT,
    ts_possessions      SMALLINT,
    ts_true_shooting    NUMERIC(5,3),
    ts_rating           NUMERIC(6,2),
    ts_fg_made          SMALLINT,
    ts_fg_attempted     SMALLINT,
    ts_fg_pct           NUMERIC(5,3),
    ts_2pt_made         SMALLINT,
    ts_2pt_attempted    SMALLINT,
    ts_2pt_pct          NUMERIC(5,3),
    ts_3pt_made         SMALLINT,
    ts_3pt_attempted    SMALLINT,
    ts_3pt_pct          NUMERIC(5,3),
    ts_ft_made          SMALLINT,
    ts_ft_attempted     SMALLINT,
    ts_ft_pct           NUMERIC(5,3),
    ts_reb_offensive    SMALLINT,
    ts_reb_defensive    SMALLINT,
    ts_reb_total        SMALLINT,
    ts_turnovers_total  SMALLINT,
    ts_turnovers_team   SMALLINT,
    ts_fouls_total      SMALLINT,
    ts_fouls_technical  SMALLINT,
    ts_fouls_flagrant   SMALLINT,
    ts_points_total     SMALLINT,
    ts_points_in_paint  SMALLINT,
    ts_points_off_tov   SMALLINT,
    ts_points_fastbreak SMALLINT,
    ts_efg_pct          NUMERIC(5,3),
    ts_tov_ratio        NUMERIC(5,3),
    ts_oreb_pct         NUMERIC(5,3),
    ts_ft_rate          NUMERIC(5,3),

    -- Opponent/defensive stats (os_ prefix)
    os_assists          SMALLINT,
    os_blocks           SMALLINT,
    os_steals           SMALLINT,
    os_possessions      SMALLINT,
    os_true_shooting    NUMERIC(5,3),
    os_rating           NUMERIC(6,2),
    os_fg_made          SMALLINT,
    os_fg_attempted     SMALLINT,
    os_fg_pct           NUMERIC(5,3),
    os_2pt_made         SMALLINT,
    os_2pt_attempted    SMALLINT,
    os_2pt_pct          NUMERIC(5,3),
    os_3pt_made         SMALLINT,
    os_3pt_attempted    SMALLINT,
    os_3pt_pct          NUMERIC(5,3),
    os_ft_made          SMALLINT,
    os_ft_attempted     SMALLINT,
    os_ft_pct           NUMERIC(5,3),
    os_reb_offensive    SMALLINT,
    os_reb_defensive    SMALLINT,
    os_reb_total        SMALLINT,
    os_turnovers_total  SMALLINT,
    os_turnovers_team   SMALLINT,
    os_fouls_total      SMALLINT,
    os_fouls_technical  SMALLINT,
    os_fouls_flagrant   SMALLINT,
    os_points_total     SMALLINT,
    os_points_in_paint  SMALLINT,
    os_points_off_tov   SMALLINT,
    os_points_fastbreak SMALLINT,
    os_efg_pct          NUMERIC(5,3),
    os_tov_ratio        NUMERIC(5,3),
    os_oreb_pct         NUMERIC(5,3),
    os_ft_rate          NUMERIC(5,3),

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(season, team_id)
);
COMMENT ON TABLE team_season_stats IS 'Aggregated team statistics per season - baseline for variance';

CREATE INDEX idx_tss_season ON team_season_stats(season);
CREATE INDEX idx_tss_team ON team_season_stats(team_id);

-- Player Season Stats (one row per player per season)
DROP TABLE IF EXISTS player_season_stats CASCADE;
CREATE TABLE player_season_stats (
    id                  SERIAL PRIMARY KEY,
    season              SMALLINT NOT NULL,
    season_label        INTEGER,
    team_id             INTEGER NOT NULL,
    team                VARCHAR(100),
    conference          VARCHAR(100),

    -- Player info
    athlete_id          INTEGER NOT NULL,
    athlete_source_id   INTEGER,
    name                VARCHAR(100),
    position            VARCHAR(20),

    -- Playing time
    games               SMALLINT,
    starts              SMALLINT,
    minutes             SMALLINT,

    -- Basic stats
    points              SMALLINT,
    turnovers           SMALLINT,
    fouls               SMALLINT,
    assists             SMALLINT,
    steals              SMALLINT,
    blocks              SMALLINT,

    -- Advanced stats
    offensive_rating    NUMERIC(6,2),
    defensive_rating    NUMERIC(6,2),
    net_rating          NUMERIC(6,2),
    porpag              NUMERIC(6,2),
    usage               NUMERIC(5,3),
    ast_tov_ratio       NUMERIC(5,2),
    oreb_pct            NUMERIC(5,3),
    ft_rate             NUMERIC(5,3),
    efg_pct             NUMERIC(5,3),
    ts_pct              NUMERIC(5,3),

    -- Shooting
    fg_made             SMALLINT,
    fg_attempted        SMALLINT,
    fg_pct              NUMERIC(5,3),
    two_pt_made         SMALLINT,
    two_pt_attempted    SMALLINT,
    two_pt_pct          NUMERIC(5,3),
    three_pt_made       SMALLINT,
    three_pt_attempted  SMALLINT,
    three_pt_pct        NUMERIC(5,3),
    ft_made             SMALLINT,
    ft_attempted        SMALLINT,
    ft_pct              NUMERIC(5,3),

    -- Rebounds
    reb_offensive       SMALLINT,
    reb_defensive       SMALLINT,
    reb_total           SMALLINT,

    -- Win shares
    ws_offensive        NUMERIC(5,2),
    ws_defensive        NUMERIC(5,2),
    ws_total            NUMERIC(5,2),
    ws_per_40           NUMERIC(5,3),

    created_at          TIMESTAMP DEFAULT NOW(),

    UNIQUE(season, athlete_id)
);
COMMENT ON TABLE player_season_stats IS 'Aggregated player statistics per season';

CREATE INDEX idx_pss_season ON player_season_stats(season);
CREATE INDEX idx_pss_team ON player_season_stats(team_id);
CREATE INDEX idx_pss_athlete ON player_season_stats(athlete_id);

--------------------------------------------------------------------------------
-- GRANT PERMISSIONS
--------------------------------------------------------------------------------

GRANT SELECT ON ALL TABLES IN SCHEMA cbb TO cbb_readonly;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA cbb TO cbb_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA cbb TO cbb_readwrite;

--------------------------------------------------------------------------------
-- SUMMARY
--------------------------------------------------------------------------------
-- Tables (9 total):
--   Reference:     conferences, venues, teams
--   Games:         games, betting_lines
--   Game Stats:    game_team_stats, game_player_stats
--   Season Stats:  team_season_stats, player_season_stats
--
-- Key improvements:
--   1. Generic table names (no years - expandable)
--   2. INTEGER for all IDs (handles values > 32,767)
--   3. Clean snake_case naming with ts_/os_ prefixes
--   4. Proper PKs, unique constraints, foreign keys
--   5. Security roles: cbb_readonly, cbb_readwrite
--   6. Audit column: created_at on all tables
--   7. Strategic indexes for common query patterns
--   8. JSONB for flexible nested data (period points, shooting stats)
--------------------------------------------------------------------------------

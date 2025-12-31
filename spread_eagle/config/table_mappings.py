"""
CSV to PostgreSQL table mappings for CBB data.
Order matters due to foreign key constraints.

Column mappings transform CSV columns (camelCase__nested) to DB columns (snake_case).
"""

# Common column renames: CSV normalized name -> DB column name
# NOTE: Order matters! Longer strings are replaced first (sorted by -len)
COLUMN_RENAMES = {
    # Team stats prefix
    "teamstats_": "ts_",
    "opponentstats_": "os_",
    # Field renames (for nested stats with ts_/os_ prefix)
    "fieldgoals_": "fg_",
    "twopointfieldgoals_": "2pt_",      # ts_2pt_made, os_2pt_made
    "threepointfieldgoals_": "3pt_",    # ts_3pt_made, os_3pt_made
    "freethrows_": "ft_",
    "rebounds_": "reb_",
    # NOTE: Player stats (2pt_ → two_pt_) handled in normalize function
    # to avoid conflicting with ts_2pt_ / os_2pt_ columns
    # JSONB column renames for game_player_stats
    "fieldgoals": "field_goals",
    "freethrows": "free_throws",
    "twopointfieldgoals": "two_point_fg",
    "threepointfieldgoals": "three_point_fg",
    # Opponent conference (missing underscore)
    "opponentconference": "opponent_conference",
    # Four factors
    "fourfactors_effectivefieldgoalpct": "efg_pct",
    "fourfactors_freethrowrate": "ft_rate",
    "fourfactors_turnoverratio": "tov_ratio",
    "fourfactors_offensivereboundpct": "oreb_pct",
    # Specific renames
    "trueshooting": "true_shooting",
    "gamescore": "game_score",
    "largestlead": "largest_lead",
    "inpaint": "in_paint",
    "offturnovers": "off_turnovers",    # ts_points_off_turnovers
    "teamtotal": "team",
    "byperiod": "by_period",
    # ID fields
    "gameid": "game_id",
    "teamid": "team_id",
    "athleteid": "athlete_id",
    "opponentid": "opponent_id",
    "hometeamid": "home_team_id",
    "awayteamid": "away_team_id",
    "venueid": "venue_id",
    "conferenceid": "conference_id",
    "sourceid": "source_id",
    "athletesourceid": "athlete_source_id",
    "seasonlabel": "season_label",
    "seasontype": "season_type",
    "startdate": "start_date",
    "starttimetbd": "start_time_tbd",
    "neutralsite": "neutral_site",
    "conferencegame": "conference_game",
    "gametype": "game_type",
    "gamenotes": "game_notes",
    "homeconferenceid": "home_conference_id",
    "homeconference": "home_conference",
    "homeseed": "home_seed",
    "homepoints": "home_points",
    "homeperiodpoints": "home_period_points",
    "homewinner": "home_winner",
    "hometeam": "home_team",
    "awayconferenceid": "away_conference_id",
    "awayconference": "away_conference",
    "awayseed": "away_seed",
    "awaypoints": "away_points",
    "awayperiodpoints": "away_period_points",
    "awaywinner": "away_winner",
    "awayteam": "away_team",
    "homescore": "home_score",
    "awayscore": "away_score",
    "overunder": "over_under",
    "overunderopen": "over_under_open",
    "spreadopen": "spread_open",
    "homemoneyline": "home_moneyline",
    "awaymoneyline": "away_moneyline",
    "ishome": "is_home",
    "gameminutes": "game_minutes",
    "gamepace": "game_pace",
    "displayname": "display_name",
    "shortdisplayname": "short_display_name",
    "primarycolor": "primary_color",
    "secondarycolor": "secondary_color",
    "currentvenueid": "current_venue_id",
    "currentvenue": "current_venue",
    "currentcity": "current_city",
    "currentstate": "current_state",
    "shortname": "short_name",
    "totalminutes": "total_minutes",
    "offensiverating": "offensive_rating",
    "defensiverating": "defensive_rating",
    "netrating": "net_rating",
    "assiststurnoverratio": "ast_tov_ratio",
    "offensivereboundpct": "oreb_pct",
    "freethrowrate": "ft_rate",
    "effectivefieldgoalpct": "efg_pct",
    "trueshootingpct": "ts_pct",
    "winshares_": "ws_",
    "totalper40": "per_40",
    "teamseed": "team_seed",
    "opponentseed": "opponent_seed",
}

# Load order respects FK dependencies
# NOTE: Year range should include current CBB season (2026 = 2025-26 season)
CBB_TABLE_MAPPINGS = [
    # Reference tables first
    {"csv": "conferences.csv", "schema": "cbb", "table": "conferences", "truncate": True},
    {"csv": "venues.csv", "schema": "cbb", "table": "venues", "truncate": True},
    {"csv": "teams.csv", "schema": "cbb", "table": "teams", "truncate": True},
    # Games table (FK to teams, venues)
    {"csv": "games_2022_2026_all_full_flat.csv", "schema": "cbb", "table": "games", "truncate": True},
    # Child tables (FK to games)
    {"csv": "team_stats_2022_2026_all_full_flat.csv", "schema": "cbb", "table": "game_team_stats", "truncate": True},
    {"csv": "lines_2022_2026_all_full_flat.csv", "schema": "cbb", "table": "betting_lines", "truncate": True},
    {"csv": "game_players_2022_2026_all_full_flat.csv", "schema": "cbb", "table": "game_player_stats", "truncate": True},
    # Season stats
    {"csv": "team_season_stats_2022_2026_flat.csv", "schema": "cbb", "table": "team_season_stats", "truncate": True},
    {"csv": "player_season_stats_2022_2026_flat.csv", "schema": "cbb", "table": "player_season_stats", "truncate": True},
]

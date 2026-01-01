"""
Score upcoming games with trained teaser model.
"""

import requests
import pandas as pd
import numpy as np
import psycopg2
import xgboost as xgb
from datetime import datetime, timedelta


def get_upcoming_games():
    """Fetch upcoming games from ESPN API."""
    print("Fetching upcoming games from ESPN...")

    today = datetime.now()
    dates_to_check = [(today + timedelta(days=i)).strftime('%Y%m%d') for i in range(5)]

    all_games = []
    for date_str in dates_to_check:
        url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates={date_str}'
        resp = requests.get(url)
        data = resp.json()

        events = data.get('events', [])
        print(f"  {date_str}: {len(events)} games")

        for event in events:
            competition = event['competitions'][0]

            # Home is always index 0 in ESPN API
            teams = competition['competitors']
            home = next((t for t in teams if t['homeAway'] == 'home'), teams[0])
            away = next((t for t in teams if t['homeAway'] == 'away'), teams[1])

            odds = competition.get('odds', [{}])
            odds = odds[0] if odds else {}
            spread = odds.get('spread')
            total = odds.get('overUnder')

            status = event['status']['type']['name']

            if status not in ['STATUS_FINAL', 'STATUS_POSTPONED']:
                all_games.append({
                    'game_date': event['date'],
                    'home_team': home['team']['displayName'].upper(),
                    'home_id': int(home['team'].get('id', 0)),
                    'away_team': away['team']['displayName'].upper(),
                    'away_id': int(away['team'].get('id', 0)),
                    'closing_spread_home': float(spread) if spread else None,
                    'closing_total': float(total) if total else None,
                    'status': status
                })

    return pd.DataFrame(all_games)


def get_team_features(team_ids):
    """Get latest features for teams from database."""

    conn = psycopg2.connect(
        host='localhost', port=5432, database='spread_eagle',
        user='dbeaver_user', password='Sport4788!'
    )

    # Get most recent features for each team
    query = """
    WITH latest_games AS (
        SELECT DISTINCT ON (team_id)
            team_id,
            team,
            stddev_cover_margin_last5,
            stddev_cover_margin_last10,
            stddev_cover_margin_last20,
            within_7_rate_last10,
            within_10_rate_last10,
            downside_tail_rate_last10,
            mean_cover_margin_last10,
            ats_win_rate_last5,
            ats_win_rate_last10,
            teaser_8_survival_last10,
            teaser_8_survival_last20,
            blowout_rate_last10,
            worst_cover_margin_last10,
            downside_tail_8_rate_last10,
            downside_tail_10_rate_last10,
            downside_tail_15_rate_last10,
            spread_games_in_window as games_played
        FROM dbt_dev.fct_cbb_teaser_spread_dataset
        ORDER BY team_id, game_date DESC
    )
    SELECT * FROM latest_games
    """

    df = pd.read_sql(query, conn)
    conn.close()

    return df


def train_model():
    """Train a fresh model on all available data."""
    print("\nTraining prediction model...")

    conn = psycopg2.connect(
        host='localhost', port=5432, database='spread_eagle',
        user='dbeaver_user', password='Sport4788!'
    )

    query = """
    SELECT
        win_teased_8,
        stddev_cover_margin_last10,
        within_10_rate_last10,
        downside_tail_rate_last10,
        ats_win_rate_last5,
        ats_win_rate_last10,
        teaser_8_survival_last10,
        teaser_8_survival_last20,
        blowout_rate_last10,
        worst_cover_margin_last10,
        downside_tail_8_rate_last10,
        downside_tail_10_rate_last10,
        closing_spread_team,
        closing_total,
        is_home
    FROM dbt_dev.fct_cbb_teaser_spread_dataset
    WHERE win_teased_8 IS NOT NULL
      AND has_sufficient_history = true
    """

    df = pd.read_sql(query, conn)
    conn.close()

    # Prepare features
    feature_cols = [c for c in df.columns if c != 'win_teased_8']
    X = df[feature_cols].fillna(-999)
    y = df['win_teased_8'].astype(int)

    # Train model
    model = xgb.XGBClassifier(
        max_depth=4, learning_rate=0.03, n_estimators=200,
        subsample=0.7, colsample_bytree=0.7, min_child_weight=15,
        random_state=42, n_jobs=-1
    )
    model.fit(X, y)

    print(f"  Trained on {len(df):,} games")
    print(f"  Historical win rate: {y.mean():.1%}")

    return model, feature_cols


def score_games(upcoming_df, team_features, model, feature_cols):
    """Score upcoming games."""

    results = []

    for _, game in upcoming_df.iterrows():
        # Match teams by name (uppercase comparison)
        home_feat = team_features[team_features['team'].str.upper() == game['home_team']]
        away_feat = team_features[team_features['team'].str.upper() == game['away_team']]

        if len(home_feat) == 0 or len(away_feat) == 0:
            # Try partial match
            home_feat = team_features[team_features['team'].str.upper().str.contains(game['home_team'].split()[0])]
            away_feat = team_features[team_features['team'].str.upper().str.contains(game['away_team'].split()[0])]

        if len(home_feat) == 0 or len(away_feat) == 0:
            continue

        home_feat = home_feat.iloc[0]
        away_feat = away_feat.iloc[0]

        # Build feature vectors for home and away perspectives
        for is_home, team_feat, team_name, spread_sign in [
            (True, home_feat, game['home_team'], 1),
            (False, away_feat, game['away_team'], -1)
        ]:
            spread = game['closing_spread_home']
            if spread is None:
                continue

            team_spread = spread * spread_sign if not is_home else spread

            features = {
                'stddev_cover_margin_last10': team_feat['stddev_cover_margin_last10'],
                'within_10_rate_last10': team_feat['within_10_rate_last10'],
                'downside_tail_rate_last10': team_feat['downside_tail_rate_last10'],
                'ats_win_rate_last5': team_feat['ats_win_rate_last5'],
                'ats_win_rate_last10': team_feat['ats_win_rate_last10'],
                'teaser_8_survival_last10': team_feat['teaser_8_survival_last10'],
                'teaser_8_survival_last20': team_feat['teaser_8_survival_last20'],
                'blowout_rate_last10': team_feat['blowout_rate_last10'],
                'worst_cover_margin_last10': team_feat['worst_cover_margin_last10'],
                'downside_tail_8_rate_last10': team_feat['downside_tail_8_rate_last10'],
                'downside_tail_10_rate_last10': team_feat['downside_tail_10_rate_last10'],
                'closing_spread_team': team_spread,
                'closing_total': game['closing_total'],
                'is_home': 1 if is_home else 0
            }

            X = pd.DataFrame([features])[feature_cols].fillna(-999)
            prob = model.predict_proba(X)[0, 1]

            results.append({
                'game_date': game['game_date'],
                'team': team_name,
                'opponent': game['away_team'] if is_home else game['home_team'],
                'is_home': is_home,
                'spread': team_spread,
                'total': game['closing_total'],
                'teaser_spread': team_spread + 8,
                'win_prob': prob,
                'survival_hist': team_feat['teaser_8_survival_last10'],
                'blowout_rate': team_feat['blowout_rate_last10'],
                'games_played': team_feat['games_played']
            })

    return pd.DataFrame(results)


def main():
    print("=" * 70)
    print("TEASER +8 GAME SCORER")
    print("=" * 70)

    # Get upcoming games
    upcoming = get_upcoming_games()

    if len(upcoming) == 0:
        print("\nNo upcoming games found. It may be off-season or a holiday.")
        print("Showing scoring on most recent historical games instead...")

        # Fall back to recent games from database
        conn = psycopg2.connect(
            host='localhost', port=5432, database='spread_eagle',
            user='dbeaver_user', password='Sport4788!'
        )
        query = """
        SELECT DISTINCT ON (game_id)
            game_id, game_date, team as home_team, opponent as away_team,
            closing_spread_team as closing_spread_home, closing_total
        FROM dbt_dev.fct_cbb_teaser_spread_dataset
        WHERE is_home = true
        ORDER BY game_id, game_date DESC
        LIMIT 30
        """
        upcoming = pd.read_sql(query, conn)
        conn.close()
        upcoming = upcoming.sort_values('game_date', ascending=False).head(20)

    games_with_lines = upcoming[upcoming['closing_spread_home'].notna()]
    print(f"\nFound {len(games_with_lines)} games with betting lines")

    if len(games_with_lines) == 0:
        print("No games with lines to score.")
        return

    # Get team features
    team_features = get_team_features([])
    print(f"Loaded features for {len(team_features)} teams")

    # Train model
    model, feature_cols = train_model()

    # Score games
    print("\nScoring games...")
    scores = score_games(games_with_lines, team_features, model, feature_cols)

    if len(scores) == 0:
        print("Could not match any teams to historical data.")
        return

    # Display results
    print("\n" + "=" * 70)
    print("TEASER +8 PREDICTIONS")
    print("=" * 70)
    print(f"\n{'Team':<25} {'Spread':>7} {'Teased':>7} {'P(Win)':>8} {'Hist%':>7} {'Risk':>8}")
    print("-" * 70)

    # Sort by win probability descending
    scores = scores.sort_values('win_prob', ascending=False)

    for _, row in scores.iterrows():
        risk = "LOW" if row['blowout_rate'] < 0.15 else "MED" if row['blowout_rate'] < 0.25 else "HIGH"
        loc = "@" if not row['is_home'] else "vs"

        print(f"{row['team']:<25} {row['spread']:>+6.1f} {row['teaser_spread']:>+6.1f} {row['win_prob']:>7.1%} {row['survival_hist']:>6.1%}  {risk:>6}")

    # Summary
    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)

    best_bets = scores[scores['win_prob'] >= 0.80]
    if len(best_bets) > 0:
        print(f"\nBEST BETS (P >= 80%): {len(best_bets)} games")
        for _, row in best_bets.iterrows():
            print(f"  {row['team']} {row['teaser_spread']:+.1f}")
    else:
        print("\nNo high-confidence picks (P >= 80%) today")

    avoid = scores[scores['win_prob'] < 0.70]
    if len(avoid) > 0:
        print(f"\nAVOID (P < 70%): {len(avoid)} games")
        for _, row in avoid.head(5).iterrows():
            print(f"  {row['team']} {row['teaser_spread']:+.1f} (P={row['win_prob']:.1%})")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()

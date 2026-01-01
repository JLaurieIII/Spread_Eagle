"""Pull all CFB player game stats (box scores) for multiple seasons."""
from pathlib import Path
from _common import fetch_by_weeks, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]


def flatten_player_stats(records):
    """Flatten nested games/players structure into one row per game-player-category."""
    flat = []

    for game in records:
        game_id = game.get("id")
        teams = game.get("teams", [])

        for team in teams:
            team_name = team.get("team")
            conference = team.get("conference")
            home_away = team.get("homeAway")
            points = team.get("points")

            categories = team.get("categories", [])
            for cat in categories:
                cat_name = cat.get("name", "")

                for player_type in cat.get("types", []):
                    type_name = player_type.get("name", "")

                    for athlete in player_type.get("athletes", []):
                        row = {
                            "game_id": game_id,
                            "team": team_name,
                            "conference": conference,
                            "home_away": home_away,
                            "team_points": points,
                            "athlete_id": athlete.get("id"),
                            "athlete_name": athlete.get("name"),
                            "category": cat_name,
                            "stat_type": type_name,
                            "stat_value": athlete.get("stat"),
                        }
                        flat.append(row)

    return flat


def main():
    print("Pulling CFB player game stats...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}:")

        # Regular season
        print(f"    Regular season:")
        regular = fetch_by_weeks("/games/players", year, "regular")
        all_records.extend(regular)

        # Postseason
        print(f"    Postseason:")
        postseason = fetch_by_weeks("/games/players", year, "postseason")
        all_records.extend(postseason)

    # Flatten
    flat_records = flatten_player_stats(all_records)

    # Deduplicate by game_id + athlete_id + category + stat_type
    seen = set()
    unique = []
    for r in flat_records:
        key = (r.get("game_id"), r.get("athlete_id"), r.get("category"), r.get("stat_type"))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "game_players"
    save_to_files(unique, output_dir, f"game_players_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/game_players")

    print(f"Done! {len(unique)} total player-game stats")


if __name__ == "__main__":
    main()

"""Pull all CFB team game stats (box scores) for multiple seasons."""
from pathlib import Path
from _common import fetch_by_weeks, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]


def flatten_team_stats(records):
    """Flatten nested games/teams structure into one row per game-team."""
    flat = []

    for game in records:
        game_id = game.get("id")
        teams = game.get("teams", [])

        for team in teams:
            row = {
                "game_id": game_id,
                "team": team.get("team"),
                "conference": team.get("conference"),
                "home_away": team.get("homeAway"),
                "points": team.get("points"),
            }

            # Flatten categories (stats)
            categories = team.get("categories", [])
            for cat in categories:
                cat_name = cat.get("name", "").lower().replace(" ", "_")
                for stat in cat.get("types", []):
                    stat_name = stat.get("name", "").lower().replace(" ", "_")
                    col_name = f"{cat_name}_{stat_name}"
                    row[col_name] = stat.get("stat")

            flat.append(row)

    return flat


def main():
    print("Pulling CFB team game stats...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}:")

        # Regular season
        print(f"    Regular season:")
        regular = fetch_by_weeks("/games/teams", year, "regular")
        all_records.extend(regular)

        # Postseason
        print(f"    Postseason:")
        postseason = fetch_by_weeks("/games/teams", year, "postseason")
        all_records.extend(postseason)

    # Flatten
    flat_records = flatten_team_stats(all_records)

    # Deduplicate by game_id + team
    seen = set()
    unique = []
    for r in flat_records:
        key = (r.get("game_id"), r.get("team"))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "team_stats"
    save_to_files(unique, output_dir, f"team_stats_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/team_stats")

    print(f"Done! {len(unique)} total team-game stats")


if __name__ == "__main__":
    main()

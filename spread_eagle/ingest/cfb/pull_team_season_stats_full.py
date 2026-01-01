"""Pull all CFB team season stats for multiple seasons."""
from pathlib import Path
from _common import fetch_by_year_only, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]


def pivot_team_stats(records):
    """
    Pivot from long format (team, statName, statValue) to wide format.
    Each team gets one row with all stats as columns.
    """
    # Group by team+season
    team_stats = {}

    for r in records:
        key = (r.get("season"), r.get("team"))
        if key not in team_stats:
            team_stats[key] = {
                "season": r.get("season"),
                "team": r.get("team"),
                "conference": r.get("conference"),
            }
        stat_name = r.get("statName", "").lower().replace(" ", "_")
        team_stats[key][stat_name] = r.get("statValue")

    return list(team_stats.values())


def main():
    print("Pulling CFB team season stats...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}...", end=" ")
        try:
            data = fetch_by_year_only("/stats/season", year)
            all_records.extend(data)
            print(f"{len(data)} records")
        except Exception as e:
            print(f"Error: {e}")

    # Pivot to wide format
    pivoted = pivot_team_stats(all_records)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "team_season_stats"
    save_to_files(pivoted, output_dir, f"team_season_stats_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/team_season_stats")

    print(f"Done! {len(pivoted)} team-season records")


if __name__ == "__main__":
    main()

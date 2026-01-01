"""Pull all CFB player season stats for multiple seasons."""
import time
from pathlib import Path
from _common import fetch_endpoint, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]

# FBS conferences to iterate through
FBS_CONFERENCES = [
    "ACC", "Big Ten", "Big 12", "Pac-12", "SEC",
    "American Athletic", "Conference USA", "Mid-American",
    "Mountain West", "Sun Belt", "FBS Independents",
]


def pivot_player_stats(records):
    """
    Pivot from long format (playerId, category, statType, stat) to wide format.
    Each player-season gets one row with stats as columns.
    """
    player_stats = {}

    for r in records:
        key = (r.get("season"), r.get("playerId"), r.get("team"))
        if key not in player_stats:
            player_stats[key] = {
                "season": r.get("season"),
                "player_id": r.get("playerId"),
                "player": r.get("player"),
                "team": r.get("team"),
                "conference": r.get("conference"),
                "position": r.get("position"),
            }
        cat = r.get("category", "").lower().replace(" ", "_")
        stat_type = r.get("statType", "").lower().replace(" ", "_")
        col_name = f"{cat}_{stat_type}" if cat else stat_type
        player_stats[key][col_name] = r.get("stat")

    return list(player_stats.values())


def main():
    print("Pulling CFB player season stats...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}:")

        # Pull by conference to avoid timeout
        for conf in FBS_CONFERENCES:
            try:
                data = fetch_endpoint(
                    "/stats/player/season",
                    {"year": year, "conference": conf},
                    timeout=60,
                )
                all_records.extend(data)
                print(f"    {conf}: {len(data)} records")
                time.sleep(0.2)
            except Exception as e:
                print(f"    {conf}: Error - {e}")

    # Pivot to wide format
    pivoted = pivot_player_stats(all_records)

    # Deduplicate by player_id + team + season
    seen = set()
    unique = []
    for r in pivoted:
        key = (r.get("season"), r.get("player_id"), r.get("team"))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "player_season_stats"
    save_to_files(unique, output_dir, f"player_season_stats_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/player_season_stats")

    print(f"Done! {len(unique)} player-season records")


if __name__ == "__main__":
    main()

"""Pull all CFB betting lines for multiple seasons."""
from pathlib import Path
from _common import fetch_by_weeks, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]


def flatten_lines(records):
    """Flatten the nested lines array into one row per provider."""
    flat = []
    for game in records:
        game_base = {
            "game_id": game.get("id"),
            "season": game.get("season"),
            "season_type": game.get("seasonType"),
            "week": game.get("week"),
            "start_date": game.get("startDate"),
            "home_team_id": game.get("homeTeamId"),
            "home_team": game.get("homeTeam"),
            "home_conference": game.get("homeConference"),
            "home_classification": game.get("homeClassification"),
            "home_score": game.get("homeScore"),
            "away_team_id": game.get("awayTeamId"),
            "away_team": game.get("awayTeam"),
            "away_conference": game.get("awayConference"),
            "away_classification": game.get("awayClassification"),
            "away_score": game.get("awayScore"),
        }

        lines = game.get("lines", [])
        if lines:
            for line in lines:
                row = {**game_base}
                row["provider"] = line.get("provider")
                row["spread"] = line.get("spread")
                row["formatted_spread"] = line.get("formattedSpread")
                row["spread_open"] = line.get("spreadOpen")
                row["over_under"] = line.get("overUnder")
                row["over_under_open"] = line.get("overUnderOpen")
                row["home_moneyline"] = line.get("homeMoneyline")
                row["away_moneyline"] = line.get("awayMoneyline")
                flat.append(row)
        else:
            # Keep game even without lines
            flat.append(game_base)

    return flat


def main():
    print("Pulling CFB betting lines...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}:")

        # Regular season
        print(f"    Regular season:")
        regular = fetch_by_weeks("/lines", year, "regular")
        all_records.extend(regular)

        # Postseason
        print(f"    Postseason:")
        postseason = fetch_by_weeks("/lines", year, "postseason")
        all_records.extend(postseason)

    # Flatten the nested lines
    flat_records = flatten_lines(all_records)

    # Deduplicate by game_id + provider
    seen = set()
    unique = []
    for r in flat_records:
        key = (r.get("game_id"), r.get("provider"))
        if key not in seen:
            seen.add(key)
            unique.append(r)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "lines"
    save_to_files(unique, output_dir, f"lines_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/lines")

    print(f"Done! {len(unique)} total lines")


if __name__ == "__main__":
    main()

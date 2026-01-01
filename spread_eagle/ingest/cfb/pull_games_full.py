"""Pull all CFB games for multiple seasons."""
from pathlib import Path
from _common import fetch_by_weeks, save_to_files, upload_to_s3


SEASONS = [2022, 2023, 2024, 2025]


def main():
    print("Pulling CFB games...")
    all_records = []

    for year in SEASONS:
        print(f"  Season {year}:")

        # Regular season (weeks 0-15)
        print(f"    Regular season:")
        regular = fetch_by_weeks("/games", year, "regular")
        all_records.extend(regular)

        # Postseason
        print(f"    Postseason:")
        postseason = fetch_by_weeks("/games", year, "postseason")
        all_records.extend(postseason)

        print(f"    Total: {len(regular) + len(postseason)} games")

    # Deduplicate by game id
    seen = set()
    unique = []
    for r in all_records:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "games"
    save_to_files(unique, output_dir, f"games_{SEASONS[0]}_{SEASONS[-1]}")
    upload_to_s3(output_dir, "cfb/raw/games")

    print(f"Done! {len(unique)} total games")


if __name__ == "__main__":
    main()

"""Pull all CFB teams."""
from pathlib import Path
from _common import fetch_endpoint, save_to_files, upload_to_s3


def main():
    print("Pulling CFB teams...")
    data = fetch_endpoint("/teams")

    # Flatten location data
    flat_data = []
    for team in data:
        record = {**team}
        # Flatten location
        if "location" in record and record["location"]:
            loc = record.pop("location")
            record["venue_id"] = loc.get("venueId")
            record["city"] = loc.get("city")
            record["state"] = loc.get("state")
            record["latitude"] = loc.get("latitude")
            record["longitude"] = loc.get("longitude")
        else:
            record.pop("location", None)

        # Handle logos (keep first logo URL)
        if "logos" in record and record["logos"]:
            record["logo_url"] = record["logos"][0] if record["logos"] else None
        record.pop("logos", None)

        # Handle alternate names
        if "alternateNames" in record:
            record["alternate_names"] = ", ".join(record["alternateNames"]) if record["alternateNames"] else None
            record.pop("alternateNames", None)

        flat_data.append(record)

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "teams"
    save_to_files(flat_data, output_dir, "teams")
    upload_to_s3(output_dir, "cfb/raw/teams")

    print(f"Done! {len(flat_data)} teams")


if __name__ == "__main__":
    main()

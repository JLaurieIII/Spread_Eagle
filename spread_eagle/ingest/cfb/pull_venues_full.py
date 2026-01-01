"""Pull all CFB venues."""
from pathlib import Path
from _common import fetch_endpoint, save_to_files, upload_to_s3


def main():
    print("Pulling CFB venues...")
    data = fetch_endpoint("/venues")

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "venues"
    save_to_files(data, output_dir, "venues")
    upload_to_s3(output_dir, "cfb/raw/venues")

    print(f"Done! {len(data)} venues")


if __name__ == "__main__":
    main()

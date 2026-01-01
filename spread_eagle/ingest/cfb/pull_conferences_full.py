"""Pull all CFB conferences."""
from pathlib import Path
from _common import fetch_endpoint, save_to_files, upload_to_s3


def main():
    print("Pulling CFB conferences...")
    data = fetch_endpoint("/conferences")

    output_dir = Path(__file__).parent.parent.parent.parent / "data" / "cfb" / "raw" / "conferences"
    save_to_files(data, output_dir, "conferences")
    upload_to_s3(output_dir, "cfb/raw/conferences")

    print(f"Done! {len(data)} conferences")


if __name__ == "__main__":
    main()

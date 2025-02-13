import hashlib
import re
import requests
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Configuration
LISTING_URL = "https://ods.railway.gov.tw/tra-ods-web/ods/download/dataResource/railway_schedule/JSON/list"
BASE_URL = "https://ods.railway.gov.tw"
HASH_LOG_FILE = Path("hash_log.txt")  # Path for the hash log file


def fetch_file_list():
    """
    Fetch the list of file paths and dates from the HTML listing page.
    """
    try:
        response = requests.get(LISTING_URL, timeout=10)
        response.raise_for_status()
        html_content = response.text

        # Regex to find all JSON file paths with a 32-character hex string
        pattern = r'<a href="(/tra-ods-web/ods/download/dataResource/exceptionDataResource/[0-9a-f]{32})">(\d{8})\.json</a>'
        matches = re.findall(pattern, html_content)

        if not matches:
            raise Exception("No valid JSON file links found on the page.")

        # Return a list of (file_url, file_date)
        return [(f"{BASE_URL}{match[0]}", match[1]) for match in matches]

    except Exception as e:
        print(f"Error fetching file list: {e}")
        return []


def download_json(file_url: str) -> bytes:
    """
    Download the JSON file from the provided URL.
    """
    try:
        response = requests.get(file_url, timeout=10, stream=True)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error downloading file {file_url}: {e}")
        return b""


def compute_md5(content: bytes) -> str:
    """
    Compute the MD5 hash of the given content.
    """
    return hashlib.md5(content).hexdigest()


def load_hash_log() -> dict:
    """
    Load the hash log from the file and return as a dictionary.
    """
    if not HASH_LOG_FILE.exists():
        return {}
    with open(HASH_LOG_FILE, "r") as f:
        lines = f.readlines()
    return {line.split()[0]: line.split()[1] for line in lines if len(line.split()) == 2}


def update_hash_log(date: str, hash_value: str):
    """
    Update the hash log with a new entry.
    """
    with open(HASH_LOG_FILE, "a") as f:
        f.write(f"{date} {hash_value}\n")


def save_file(content: bytes, date: str, db_folder: Path):
    """
    Save the JSON file to the specified folder.
    """
    file_path = db_folder / f"{date}.json"
    with open(file_path, "wb") as f:
        f.write(content)


def run_for_all(db_folder: Path, force: bool = False):
    """
    Download all files listed on the HTML page, skipping identical ones unless forced.
    """
    file_list = fetch_file_list()
    if not file_list:
        print("No files found to download.")
        return

    hash_log = load_hash_log()
    downloaded_files = []

    for file_url, file_date in file_list:
        print(f"Processing file: {file_date}.json from {file_url}")
        json_content = download_json(file_url)

        if not json_content:
            print(f"Failed to download content for {file_date}.json. Skipping.")
            continue

        new_hash = compute_md5(json_content)

        # Skip if the hash is already logged and matches
        if not force and hash_log.get(file_date) == new_hash:
            print(f"{file_date}.json is identical to the logged hash. Skipping.")
            continue
        else:
            print(f"{file_date}.json is new or mismatch to a logged hash. Downloading.")

        # Save the file and update the hash log
        save_file(json_content, file_date, db_folder)
        update_hash_log(file_date, new_hash)
        downloaded_files.append(file_date)

    print(f"Downloaded files: {downloaded_files}")


def run_for_date(file_date: str, db_folder: Path, force: bool = False):
    """
    Download a specific file for the given date, skipping if identical unless forced.
    """
    file_list = fetch_file_list()
    if not file_list:
        print("No files found to download.")
        return

    hash_log = load_hash_log()

    for file_url, file_date_from_list in file_list:
        if file_date_from_list == file_date:
            print(f"Processing file: {file_date}.json from {file_url}")
            json_content = download_json(file_url)

            if not json_content:
                print(f"Failed to download content for {file_date}.json. Skipping.")
                return

            new_hash = compute_md5(json_content)

            # Skip if the hash is already logged and matches
            if not force and hash_log.get(file_date) == new_hash:
                print(f"{file_date}.json is identical to the logged hash. Skipping.")
                return

            # Save the file and update the hash log
            save_file(json_content, file_date, db_folder)
            update_hash_log(file_date, new_hash)
            print(f"Downloaded and saved: {file_date}.json")
            return

    print(f"File for date {file_date} not found on the page.")


def schedule_jobs(db_folder: Path):
    """
    Schedule the crawler to run at specific times using BackgroundScheduler.
    """
    scheduler = BackgroundScheduler()

    # Schedule to download all files at 06:00 and 18:00 daily
    scheduler.add_job(run_for_all, CronTrigger(hour=6, minute=0), kwargs={"db_folder": db_folder, "force": False})
    scheduler.add_job(run_for_all, CronTrigger(hour=18, minute=0), kwargs={"db_folder": db_folder, "force": False})

    # Start the scheduler
    scheduler.start()
    print("Scheduler started in the background.")


if __name__ == "__main__":
    import argparse

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Crawler for JSON files")
    parser.add_argument("--date", help="Specific date to download (YYYYMMDD)")
    parser.add_argument("--force", action="store_true", help="Force download even if the file exists and is identical")
    parser.add_argument("--all", action="store_true", help="Download all files listed on the page")
    parser.add_argument("--schedule", action="store_true", help="Run the crawler on a schedule")
    parser.add_argument("--db-folder", default="db", help="Directory to save JSON files (default: db)")
    args = parser.parse_args()

    # Set up the database folder
    db_folder = Path(args.db_folder)
    db_folder.mkdir(exist_ok=True)

    if args.schedule:
        # Run the scheduler
        schedule_jobs(db_folder)
    elif args.all:
        # Download all files
        run_for_all(db_folder, force=args.force)
    elif args.date:
        # Download a specific file
        run_for_date(args.date, db_folder, force=args.force)
    else:
        print("Please specify --date, --all, or --schedule.")

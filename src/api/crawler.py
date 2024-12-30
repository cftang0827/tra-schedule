import hashlib
import re
import requests
from pathlib import Path
import schedule
import threading
import time

# Configuration
LISTING_URL = "https://ods.railway.gov.tw/tra-ods-web/ods/download/dataResource/railway_schedule/JSON/list"
BASE_URL = "https://ods.railway.gov.tw"
DB_FOLDER = Path("db")

# Ensure the db folder exists
DB_FOLDER.mkdir(exist_ok=True)

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

def save_file(content: bytes, date: str):
    """
    Save the JSON file to the local `db/` folder.
    """
    file_path = DB_FOLDER / f"{date}.json"
    with open(file_path, "wb") as f:
        f.write(content)

def run_for_all(force: bool = False):
    """
    Download all files listed on the HTML page, skipping identical ones unless forced.
    """
    file_list = fetch_file_list()
    if not file_list:
        print("No files found to download.")
        return

    downloaded_files = []
    for file_url, file_date in file_list:
        print(f"Processing file: {file_date}.json from {file_url}")
        json_content = download_json(file_url)

        if not json_content:
            print(f"Failed to download content for {file_date}.json. Skipping.")
            continue

        new_hash = compute_md5(json_content)
        file_path = DB_FOLDER / f"{file_date}.json"

        # Check if the file exists and skip if not forcing
        if file_path.exists() and not force:
            with open(file_path, "rb") as f:
                existing_hash = compute_md5(f.read())
            if new_hash == existing_hash:
                print(f"{file_date}.json is identical. Skipping download.")
                continue

        # Save the file if new or forcing
        save_file(json_content, file_date)
        downloaded_files.append(file_date)

    print(f"Downloaded files: {downloaded_files}")

def run_for_date(file_date: str, force: bool = False):
    """
    Download a specific file for the given date, skipping if identical unless forced.
    """
    file_list = fetch_file_list()
    if not file_list:
        print("No files found to download.")
        return

    for file_url, file_date_from_list in file_list:
        if file_date_from_list == file_date:
            print(f"Processing file: {file_date}.json from {file_url}")
            json_content = download_json(file_url)

            if not json_content:
                print(f"Failed to download content for {file_date}.json. Skipping.")
                return

            new_hash = compute_md5(json_content)
            file_path = DB_FOLDER / f"{file_date}.json"

            # Check if the file exists and skip if not forcing
            if file_path.exists() and not force:
                with open(file_path, "rb") as f:
                    existing_hash = compute_md5(f.read())
                if new_hash == existing_hash:
                    print(f"{file_date}.json is identical. Skipping download.")
                    return

            # Save the file if new or forcing
            save_file(json_content, file_date)
            print(f"Downloaded and saved: {file_date}.json")
            return

    print(f"File for date {file_date} not found on the page.")

def schedule_jobs():
    """
    Schedule the crawler to run at specific times.
    """
    # Schedule to download all files at 06:00 and 18:00 daily
    schedule.every().day.at("06:00").do(run_for_all, force=False)
    schedule.every().day.at("18:00").do(run_for_all, force=False)

    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(1)

    # Run the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Crawler for JSON files")
    parser.add_argument("--date", help="Specific date to download (YYYYMMDD)")
    parser.add_argument("--force", action="store_true", help="Force download even if the file exists and is identical")
    parser.add_argument("--all", action="store_true", help="Download all files listed on the page")
    parser.add_argument("--schedule", action="store_true", help="Run the crawler on a schedule")
    args = parser.parse_args()

    if args.schedule:
        # Run the scheduler
        schedule_jobs()
        print("Scheduler is running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    elif args.all:
        # Force download all files
        run_for_all(force=args.force)
    elif args.date:
        # Force download for a specific date
        run_for_date(args.date, force=args.force)
    else:
        print("Please specify --date, --all, or --schedule.")

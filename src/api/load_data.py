import json
import mysql.connector
from pathlib import Path
from datetime import datetime
from api.crawler import run_for_all, schedule_jobs, run_for_date

# Database configuration
db_config = {
    "user": "user",
    "password": "userpassword",
    "host": "db",
    "database": "train_schedule"
}

def load_json_to_db(json_file, db_config):
    """
    Load a single JSON file into the MySQL unified train_schedule table.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    insert_query = """
    INSERT INTO train_schedule (
        train_type, train_code, breast_feed, route, package, overnight_stn, line_dir, line,
        dinning, food_srv, cripple, car_class, bike, extra_train, everyday, note, note_eng,
        station, order_in_trip, dep_time, arr_time, route_station, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """

    # Extract the date from the file name
    date_str = json_file.stem  # e.g., "20250318"
    file_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"  # YYYY-MM-DD

    # Read and process the JSON file
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for train_info in data["TrainInfos"]:
        for time_info in train_info["TimeInfos"]:
            dep_time = f"{file_date} {time_info['DEPTime']}"
            arr_time = f"{file_date} {time_info['ARRTime']}"
            
            values = (
                train_info["Type"], train_info["Train"], train_info["BreastFeed"], train_info["Route"],
                train_info["Package"], train_info["OverNightStn"], train_info["LineDir"], train_info["Line"],
                train_info["Dinning"], train_info["FoodSrv"], train_info["Cripple"], train_info["CarClass"],
                train_info["Bike"], train_info["ExtraTrain"], train_info["Everyday"], train_info["Note"],
                train_info["NoteEng"], time_info["Station"], int(time_info["Order"]), dep_time, arr_time,
                time_info["Route"]
            )
            cursor.execute(insert_query, values)

    conn.commit()
    cursor.close()
    conn.close()


def ensure_json_files(db_folder):
    """
    Ensure JSON files are present in the specified folder. If none exist, download all using run_for_all.
    """
    db_folder_path = Path(db_folder)
    db_folder_path.mkdir(parents=True, exist_ok=True)

    # Check if any JSON files exist in the folder
    if not any(db_folder_path.glob("*.json")):
        print(f"No JSON files found in {db_folder}. Downloading all possible JSON files...")
        run_for_all(db_folder_path)  # Trigger run_for_all to download all JSON files
    else:
        print(f"JSON files found in {db_folder}. Skipping download.")

def process_all_jsons(db_folder, db_config):
    """
    Process all JSON files in the db_folder to load data into the database.
    """
    ensure_json_files(db_folder)  # Ensure JSON files are available

    db_folder_path = Path(db_folder)

    print("Processing JSON files in the db folder...")
    for json_file in db_folder_path.glob("*.json"):
        print(f"Processing {json_file.name}...")
        load_json_to_db(json_file, db_config)

if __name__ == "__main__":
    db_folder = "/app/src/api/db"  # Adjust the path as necessary
    process_all_jsons(db_folder, db_config)

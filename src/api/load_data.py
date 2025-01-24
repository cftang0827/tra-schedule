import json
import mysql.connector
from pathlib import Path
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


# Database configuration
db_config = {
    "user": "user",
    "password": "userpassword",
    "host": "db",
    "database": "train_schedule"
}

def batch_insert_to_db(data, db_config):
    """
    Perform batch insertion with REPLACE INTO for train_schedule table.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Prepare the REPLACE INTO query
    query = """
    REPLACE INTO train_schedule (
        train_type, train_code, breast_feed, route, package, overnight_stn, line_dir, line,
        dinning, food_srv, cripple, car_class, bike, extra_train, everyday, note, note_eng,
        station, order_in_trip, dep_time, arr_time, route_station, created_at
    ) VALUES 
    """ + ", ".join(["(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"] * len(data))

    # Flatten the data list for the query
    flat_data = [item for sublist in data for item in sublist]

    # Execute the query
    try:
        cursor.execute(query, flat_data)
        conn.commit()
        print(f"Inserted {len(data)} rows into the database.")
    except Exception as e:
        print(f"Error during batch insertion: {e}")
    finally:
        cursor.close()
        conn.close()


def load_json_to_db(json_file: Path, db_config):
    """
    Load a single JSON file into the MySQL database using batch insertion.
    """
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        date = json_file.stem  # Extract the date from the filename
        file_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"  # YYYY-MM-DD format
        batch_data = []

        for train_info in data["TrainInfos"]:
            for time_info in train_info["TimeInfos"]:
                dep_time = f"{file_date} {time_info['DEPTime']}"
                arr_time = f"{file_date} {time_info['ARRTime']}"
                batch_data.append((
                    train_info["Type"], train_info["Train"], train_info["BreastFeed"], train_info["Route"],
                    train_info["Package"], train_info["OverNightStn"], train_info["LineDir"], train_info["Line"],
                    train_info["Dinning"], train_info["FoodSrv"], train_info["Cripple"], train_info["CarClass"],
                    train_info["Bike"], train_info["ExtraTrain"], train_info["Everyday"], train_info["Note"],
                    train_info["NoteEng"], time_info["Station"], int(time_info["Order"]), dep_time, arr_time,
                    time_info["Route"]
                ))

        # Perform batch insertion
        batch_insert_to_db(batch_data, db_config)

        # Remove the JSON file after successful insertion
        json_file.unlink()
        print(f"Processed and deleted JSON file: {json_file.name}")
    except Exception as e:
        print(f"Error processing {json_file.name}: {e}")

def remove_duplicates(db_config):
    """
    Remove duplicate entries from the database while keeping one of each.
    """
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    delete_duplicates_query = """
    DELETE t1
    FROM train_schedule t1
    INNER JOIN train_schedule t2
    ON t1.train_code = t2.train_code
       AND t1.station = t2.station
       AND t1.arr_time = t2.arr_time
       AND t1.created_at > t2.created_at;
    """

    try:
        cursor.execute(delete_duplicates_query)
        conn.commit()
        print("Duplicates removed successfully.")
    except Exception as e:
        print(f"Error removing duplicates: {e}")
    finally:
        cursor.close()
        conn.close()


def process_all_jsons(db_folder, db_config):
    """
    Process all JSON files in the db folder (only new or hash-mismatched files).
    """
    db_folder_path = Path(db_folder)

    print("Processing JSON files in the db folder...")
    for json_file in db_folder_path.glob("*.json"):
        print(f"Processing new or updated file: {json_file.name}")
        load_json_to_db(json_file, db_config)

    # Remove duplicates after processing
    #print("Removing duplicates...")
    #remove_duplicates(db_config)



def schedule_load_jobs(db_folder: Path, db_config):
    """
    Schedule the loading process to run at specific times using BackgroundScheduler.
    """
    scheduler = BackgroundScheduler()

    # Schedule to load JSONs into the database at 07:30 and 19:30 daily
    scheduler.add_job(
        process_all_jsons, 
        CronTrigger(hour=6, minute=30), 
        kwargs={"db_folder": db_folder, "db_config": db_config}
    )
    scheduler.add_job(
        process_all_jsons, 
        CronTrigger(hour=18, minute=30), 
        kwargs={"db_folder": db_folder, "db_config": db_config}
    )

    # Start the scheduler
    scheduler.start()
    print("Load scheduler started in the background.")


if __name__ == "__main__":
    db_folder = "/app/src/api/db"  # Adjust the path as necessary
    process_all_jsons(db_folder, db_config)

# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from api.crawler import run_for_all, schedule_jobs, run_for_date
from api.load_data import process_all_jsons, schedule_load_jobs
from fastapi import Query
from typing import List
from datetime import datetime, timedelta
import mysql.connector
import time
import os

app = FastAPI()
DB_FOLDER = Path(__file__).parent / "db"

# MySQL connection configuration
db_config = {
    "user": os.getenv("DB_USER"),  # Replace with your MySQL username
    "password": os.getenv("DB_PASSWORD"),  # Replace with your MySQL password
    "host": os.getenv("DB_HOST", "localhost"),  # The service name in docker-compose.yml
    "database": os.getenv("DB_DATABASE", "train_schedule")
}


@app.on_event("startup")
def startup_event():
    """
    Initialize the application and start both the crawler and load schedulers.
    """
    DB_FOLDER.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
    print(f"DB_FOLDER set to: {DB_FOLDER}")

    print("Starting the crawler scheduler...")
    schedule_jobs(DB_FOLDER)  # Scheduler for crawling

    print("Starting the load scheduler...")
    schedule_load_jobs(DB_FOLDER, db_config)  # Scheduler for loading JSONs into the database

    print("Starting init download of all possible jsons")
    run_for_all(db_folder=DB_FOLDER, force=False)

    print("Starting init SQL DB loading of all jsons inside db/")
    process_all_jsons(db_folder=DB_FOLDER, db_config=db_config)


@app.get("/json/{date}")
async def get_json(date: str):
    """
    Fetch a JSON file by date from the local storage. If the file doesn't exist, download it.
    """
    try:
        # Construct the file path
        file_path = DB_FOLDER / f"{date}.json"

        # Check if the file exists
        if not file_path.exists():
            # Call the function to download the file
            run_for_date(date, db_folder=DB_FOLDER, force=True)

        # Check again if the file now exists
        if file_path.exists():
            # Return the file as a response
            return FileResponse(file_path, media_type="application/json")
        else:
            return {"error": f"File for date {date} could not be downloaded."}
    except Exception as e:
        # Handle unexpected errors gracefully
        return {"error": f"An unexpected error occurred: {str(e)}"}




@app.get("/force-download")
async def force_download(file_date: str = None):
    """
    Trigger a manual force-download for all files or a specific file.
    """
    if file_date:
        # Download for a specific date
        run_for_date(file_date, db_folder=DB_FOLDER, force=True)
        return {"message": f"Force download completed for date {file_date}"}
    else:
        # Download for all files
        run_for_all(db_folder=DB_FOLDER, force=True)
        return {"message": "Force download completed for all files"}



@app.get("/timetable/")
async def get_timetable(
    departure_station: str,
    arrival_station: str,
    travel_day: str,  # Expecting ISO format: "YYYY-MM-DD"
    travel_time: str # "HH:MM:SS"
):
    """
    Fetch all trains departing from a given station after a specified time.
    """
    try:
        # Parse the departure_time
        #departure_datetime = datetime.strptime(departure_time, "%Y-%m-%d %H:%M:%S")

        # Connect to the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # SQL query to fetch trains departing after the specified time
        query = """
        WITH locate_code_by_dept_station_and_travel_time AS (
            SELECT train_code, dep_time
            FROM train_schedule
            WHERE station = %s
            AND DATE(arr_time) = %s
            AND TIME(arr_time) >= %s
            AND DATE(created_at) = CURDATE()
        ),
        locate_rows_by_code_and_arr_station AS (
            SELECT ts.*
            FROM train_schedule ts
            JOIN locate_code_by_dept_station_and_travel_time lc
            ON ts.train_code = lc.train_code
            WHERE ts.station = %s
            AND DATE(ts.arr_time) = %s
            AND ts.arr_time > lc.dep_time
        )
        SELECT *
        FROM locate_rows_by_code_and_arr_station
        ORDER BY arr_time;
        """

        # Execute query
        params = (
            departure_station,
            travel_day,
            travel_time,
            arrival_station,
            travel_day
        )
        cursor.execute(query, params)

        # Fetch results
        results = cursor.fetchall()

        cursor.close()
        conn.close()

        return results

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database query error")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

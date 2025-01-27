# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from api.crawler import run_for_all, schedule_jobs, run_for_date
from fastapi import Query
from typing import List
from datetime import datetime, timedelta
import mysql.connector
import time
import logging

app = FastAPI()
DB_FOLDER = Path(__file__).parent / "db"

# MySQL connection configuration
db_config = {
    "user": "user",  # Replace with your MySQL username
    "password": "userpassword",  # Replace with your MySQL password
    "host": "db",  # The service name in docker-compose.yml
    "database": "train_schedule"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.on_event("startup")
def startup_event():
    """
    Initialize the application and start the scheduler.
    """
    DB_FOLDER.mkdir(parents=True, exist_ok=True)  # Ensure the folder exists
    print(f"DB_FOLDER set to: {DB_FOLDER}")
    print("Starting the scheduler...")
    schedule_jobs(DB_FOLDER)

@app.on_event("startup")
async def startup_event():
    start_time = time.time()
    logger.info("Starting FastAPI application...")
    
    # If you have initialization tasks, log each step
    logger.info("Step 1: Loading configurations...")
    # Simulate a delay
    time.sleep(1)  

    logger.info("Step 2: Initializing background jobs...")
    # Simulate another delay
    time.sleep(1)  

    end_time = time.time()
    logger.info(f"FastAPI started successfully in {end_time - start_time:.2f} seconds.")


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

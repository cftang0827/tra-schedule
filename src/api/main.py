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
import os
from contextlib import asynccontextmanager
import json
from bidict import bidict
from fastapi.middleware.cors import CORSMiddleware

origins = ["*"]

DB_FOLDER = Path("db")

with open("api/files/stations.json", "r") as f:
    stations_objs = json.load(f)

stations = bidict()
for s in stations_objs:
    stations[s["stationName"]] = s["stationCode"]

with open("api/files/cars.json", "r") as f:
    cars = json.load(f)

# MySQL connection configuration
db_config = {
    "user": os.getenv("DB_USER"),  # Replace with your MySQL username
    "password": os.getenv("DB_PASSWORD"),  # Replace with your MySQL password
    "host": os.getenv("DB_HOST", "localhost"),  # The service name in docker-compose.yml
    "database": os.getenv("DB_DATABASE", "train_schedule")
}

# Connect to the database
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
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

    yield

    print("Release mysql connection handler")
    cursor.close()
    conn.close()

# app = FastAPI(lifespan=lifespan)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,            # 可以設定 ["*"] 允許全部，但不建議上線用
    allow_credentials=True,
    allow_methods=["*"],              # 允許所有 method：GET, POST, PUT, DELETE...
    allow_headers=["*"],              # 允許所有 headers
)

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




# @app.get("/force-download")
# async def force_download(file_date: str = None):
#     """
#     Trigger a manual force-download for all files or a specific file.
#     """
#     if file_date:
#         # Download for a specific date
#         run_for_date(file_date, db_folder=DB_FOLDER, force=True)
#         return {"message": f"Force download completed for date {file_date}"}
#     else:
#         # Download for all files
#         run_for_all(db_folder=DB_FOLDER, force=True)
#         return {"message": "Force download completed for all files"}
@app.get("/stations")
async def get_stations():

    response = []

    for k, v in stations.items():
        response.append({
            "station_name": k,
            "station_id": v
        })

    return response


@app.get("/timetable")
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

        # SQL query to fetch trains departing after the specified time
        query = """
        WITH locate_code_by_arrival_station AS (
            SELECT train_code, arr_time, dep_time
            FROM train_schedule
            WHERE station = %s
            AND DATE(arr_time) = %s
            AND created_at = CURDATE()
        ),
        locate_rows_by_code_and_arr_station AS (
            SELECT lc.arr_time as lc_arr_time, lc.dep_time as lc_dep_time, ts.*
            FROM train_schedule ts
            JOIN locate_code_by_arrival_station lc
            ON ts.train_code = lc.train_code
            WHERE ts.station = %s
            AND DATE(ts.dep_time) = %s
            AND TIME(ts.dep_time) >= %s
            AND ts.dep_time <= lc.arr_time
            AND TIMESTAMPDIFF(HOUR, ts.dep_time, lc.arr_time) <= 12
        )
        SELECT *
        FROM locate_rows_by_code_and_arr_station
        ORDER BY dep_time;

        """

        # Execute query
        params = (
            arrival_station,
            travel_day,
            departure_station,
            travel_day,
            travel_time
        )
        cursor.execute(query, params)

        # Fetch results
        results = cursor.fetchall()

        # add car name
        for r in results:
            car = cars.get(r["car_class"])
            r["car_name"] = car["name"] if car else None
            r["car_alias"] = car["alias"] if car else None

        return results

    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database query error")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")

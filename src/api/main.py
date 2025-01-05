# app/main.py
from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from crawler import run_for_all, schedule_jobs

app = FastAPI()
DB_FOLDER = Path("db")

@app.on_event("startup")
def startup_event():
    """
    Initialize the application and start the scheduler.
    """
    db_folder = Path("db")
    db_folder.mkdir(exist_ok=True)  # Ensure the folder exists
    print("Starting the scheduler...")
    schedule_jobs(db_folder)

@app.get("/json/{date}")
async def get_json(date: str):
    """
    Fetch a JSON file by date from the local storage.
    """
    try:
        # Construct the file path
        file_path = DB_FOLDER / f"{date}.json"

        # Check if the file exists
        if not file_path.exists():
            return {"error": f"File for date {date} not found"}

        # Return the file as a response
        return FileResponse(file_path, media_type="application/json")
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


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
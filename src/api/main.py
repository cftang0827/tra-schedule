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
    Run the scheduler when the FastAPI app starts.
    """
    print("Starting the scheduler...")
    schedule_jobs()

@app.get("/json/{date}")
async def get_json(date: str):
    """
    Fetch a JSON file by date from the local storage.
    """
    file_path = DB_FOLDER / f"{date}.json"
    if not file_path.exists():
        return {"error": "File not found"}
    return FileResponse(file_path)

@app.post("/force-download")
async def force_download():
    """
    Trigger a manual force-download for all files.
    """
    run_for_all(force=True)
    return {"message": "Force download completed"}



'''
@app.get("/get-file/{file_date}")
def get_file(file_date: str):
    try:
        # Fetch the file URL as before
        response = requests.get(LISTING_URL, timeout=10)
        response.raise_for_status()
        html_content = response.text

        pattern = rf'<a href="(/tra-ods-web/ods/download/dataResource/exceptionDataResource/[^"]+)">{file_date}\.json</a>'
        match = re.search(pattern, html_content)

        if not match:
            raise HTTPException(status_code=404, detail="File not found")

        file_url = f"https://ods.railway.gov.tw{match.group(1)}"
        file_response = requests.get(file_url, timeout=10, stream=True)
        file_response.raise_for_status()

        return StreamingResponse(file_response.iter_content(chunk_size=1024),
                                 media_type="application/json")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "FastAPI JSON Fetcher for Railway Schedule"}
'''

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
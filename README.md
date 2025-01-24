# tra-schedule



## System Design
<img width="496" alt="截圖 2024-12-29 16 07 10" src="https://github.com/user-attachments/assets/5ad6c270-b8de-4ed8-94eb-c6ade16e5187" />


## Tech Stack
- API layer: Python + FastAPI
- Cron job: Python
- Database: MongoDB
- Web Front: Vue JS + Nginx

## Resource
- https://ods.railway.gov.tw/tra-ods-web/ods/download/dataResource/railway_schedule/JSON/list
- https://superiorapis.cteam.com.tw/premium?q=%E9%90%B5%E8%B7%AF


## TODO
- API development (done!)
- Infra docker compose development (Functionality done. Awaiting efficiency and clarity update.)
- Web frontend development
- Crawler script developement

## DB data schema
```json
{
    "Route": "",
    "Station": "0990",
    "Order": "6",
    "DEPTime": "16:50:00",
    "ARRTime": "16:49:00",
    "Train": "2551",
    "Date": "20250225",
    "LineDir": "1"
}
```

- Input start & end station id
- Intersect all the train id from start station and end station
- Use `Order` to check the LineDir


## Docker Compose Setup
```sh
# Start docker
docker-compose up --build

# Terminate docker cont.
docker-compose down

# Clean DB
docker volume rm tra-schedule_db_data
```

## Use of API (Example command)
```sh
curl "http://localhost:8000/timetable/?departure_station=1000&arrival_station=1020&travel_day=2025-01-30&travel_time=04:06:00" | jq .
```
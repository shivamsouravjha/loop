from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime, time
from pydantic import BaseModel
from dataSync import load_csv_to_db  # Import the function from data_loader.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy.sql import column
from uuid import uuid4
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import asyncio
from sqlalchemy import text,create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy import cast, TIMESTAMP
from datetime import datetime, timedelta
from createDB import store_timezone, store_hours, store_status, store_reports
from sqlalchemy.orm import joinedload
from sqlalchemy import select, func, Time
import pytz
app = FastAPI()
DATABASE_URL = "postgresql+asyncpg://storageData:storageData@localhost:5432/storageData"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)
class Downtime(BaseModel):
    start: datetime
    end: datetime
def job_listener(event):
    if event.exception:
        logging.error('The job crashed :(')
    else:
        logging.info('The job worked :)')

@app.on_event("startup")
def startup_event():
    print("heretodothings")
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        seconds=10,
        args=["/home/shivamsouravjha.linux/loop/data/bq-results-20230125-202210-1674678181880.csv", 'store_timezone',""],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        seconds=10,
        args=["/home/shivamsouravjha.linux/loop/data/Menu_hours.csv", 'store_hours',""],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        seconds=10,
        args=["/home/shivamsouravjha.linux/loop/data/store_status.csv", 'store_status',"a.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.start()
    print("sheretodothings")

async def create_report(session, report_id):
    async with session.begin():
        await session.execute(text("INSERT INTO store_reports (report_id, status, data) VALUES (:report_id, 'pending', NULL)"), {'report_id': report_id})
    await session.commit()


async def generate_report(session, report_id):
    # Step 1: Fetch necessary data
    # We'll join the tables on store_id and filter by date if necessary
    # For demo, let's assume we're calculating for a specific day
    # start_of_day = datetime.combine(today, datetime.min.time())
    # end_of_day = datetime.combine(today, datetime.max.time())
    current_time = datetime.utcnow()

    # Define time intervals
    one_hour_ago = current_time - timedelta(hours=1)
    one_day_ago = current_time - timedelta(days=1)
    one_week_ago = current_time - timedelta(weeks=1)

    print(one_week_ago)
    stmt = select(
        store_status.c.store_id,
        store_status.c.timestamp_utc,
        store_status.c.status,
        store_hours.c.day,
        func.extract('dow', func.timezone(func.coalesce(store_timezone.c.timezone_str, 'UTC'), store_status.c.timestamp_utc)).label('dow_utc_local'),
        cast(store_hours.c.start_time_local, Time).label('start_time_local'),
        cast(store_hours.c.end_time_local, Time).label('end_time_local'),
        func.coalesce(store_timezone.c.timezone_str, 'UTC').label('timezone_str')
    ).select_from(
        store_status
        .join(store_hours, store_status.c.store_id == store_hours.c.store_id)
        .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
    ).where(
        store_status.c.status == 'inactive'
    )



    result = await session.execute(stmt)
    records = result.fetchall()
    print(records)
    # Step 2: Process records to calculate uptime/downtime
    report_data = {}
    for record in records:
        try:
            # Access fields using correct attribute names, assume records are correctly labeled from the SQL query
            store_id = record.store_id
            timezone_str = record.timezone_str if record.timezone_str else 'UTC'  # Use UTC if None
            timezone = pytz.timezone(timezone_str)

            # Since timestamp_utc is already a datetime object, no need to parse it
            timestamp_utc = pytz.utc.localize(record.timestamp_utc)

            # Handling time parsing directly
            start_time_local = record.start_time_local
            end_time_local = record.end_time_local

            # Calculating local times
            timestamp_local = timestamp_utc.astimezone(timezone)
            business_start = datetime.combine(timestamp_local.date(), start_time_local)
            business_end = datetime.combine(timestamp_local.date(), end_time_local)

            # Localize these times to the same timezone as timestamp_local
            business_start = timezone.localize(business_start)
            business_end = timezone.localize(business_end)

            print(f"Business hours for store {store_id}: start at {business_start}, end at {business_end}")

            # Check if the timestamp is within business hours
            if business_start <= timestamp_local <= business_end:
                print('This time is within business hours.')
                # Initialize report data for the store if not already done
                if store_id not in report_data:
                    report_data[store_id] = {'uptime': 0, 'downtime': 0}

                # Count this record in uptime/downtime calculation
                status_key = 'uptime' if record.status == 'active' else 'downtime'
                report_data[store_id][status_key] += 1

            else:
                print('This time is outside business hours.')

        except Exception as e:
            print(f"Error processing record for store {store_id}: {e}")

    print(report_data,"report_data")

    # Format report_data as needed for final output
    # final_report = format_report_data(report_data)

    # Step 3: Update the database with the generated report data
    async with session.begin():
        stmt = text(
            "UPDATE store_reports SET data = :data, status = 'complete' WHERE report_id = :report_id"
        )
        await session.execute(stmt, {'data': str(records), 'report_id': report_id})
    await session.commit()

@app.post("/trigger_report/")
async def trigger_report():
    report_id = str(uuid4())
    async with SessionLocal() as session:
        await create_report(session, report_id)
        asyncio.create_task(generate_report(session, report_id))  # Start background task
    return {"report_id": report_id}

@app.get("/report_status/{report_id}")
async def report_status(report_id: str):
    async with SessionLocal() as session:
        result = await session.execute(select(text("status, data FROM store_reports WHERE report_id = :report_id")), {'report_id': report_id})
        report = result.fetchone()
        if report:
            return {"report_id": report_id, "status": report.status, "data": report.data}
        else:
            raise HTTPException(status_code=404, detail="Report not found")
@app.get("/ping")
async def ping():
    return {"message": "pong"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

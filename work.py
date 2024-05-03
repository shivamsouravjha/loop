from fastapi import FastAPI, HTTPException
from typing import List, Optional
from datetime import datetime, time
from pydantic import BaseModel
from sqlalchemy import select, func, and_, exists
from sqlalchemy.sql import extract
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, or_, cast, Time,case
from dataSync import load_csv_to_db  # Import the function from data_loader.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import asyncio
from sqlalchemy.sql import extract
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import column
from uuid import uuid4
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import asyncio
from datetime import timezone
from sqlalchemy import text,create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy import cast, TIMESTAMP
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
def ensure_timezone(dt, timezone):
    """Ensure datetime is timezone-aware using the provided timezone."""
    if dt.tzinfo is None:
        return timezone.localize(dt)
    return dt.astimezone(timezone)

def calculate_time_difference(start, end):
    """Calculate the difference in hours between two datetime objects."""
    return (end - start).total_seconds() / 3600
@app.on_event("startup")
def startup_event():
    print("heretodothings")
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/bq-results-20230125-202210-1674678181880.csv", 'store_timezone',"c.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/Menu_hours.csv", 'store_hours',"b.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/store_status.csv", 'store_status',"a.txt"],
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
    current_utc_str = "2023-01-19 15:28:46.983397"

    current_utc = datetime.strptime(current_utc_str, "%Y-%m-%d %H:%M:%S.%f")
    report_data = {}
    print(current_utc,"current_utc")
    try:
        start_time_hour = current_utc - timedelta(hours=1)
        start_time_day = current_utc - timedelta(days=1)
        start_time_week = current_utc - timedelta(weeks=1)
        subquery = (
            select(1)  # We select a constant value because we only care if rows exist, not their content
            .where(and_(
                store_hours.c.store_id == store_status.c.store_id,
                extract('hour', func.cast(store_status.c.timestamp_utc, Time)) >= extract('hour', store_hours.c.start_time_local),
                extract('hour', func.cast(store_status.c.timestamp_utc, Time)) <= extract('hour', store_hours.c.end_time_local)
            ))
            .correlate(store_status)  # Ensure the subquery is correlated with the outer query
        )
        stmt_hours  = select(
            store_status.c.store_id,
            store_status.c.status,
            store_status.c.timestamp_utc,
        ).select_from(
            store_status
            .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
        ).where(and_(
            store_status.c.timestamp_utc >= start_time_hour,
            store_status.c.timestamp_utc < current_utc,
            exists(subquery)  # Use the EXISTS clause here
        )).order_by(
            store_status.c.store_id.asc()
        )
        stmt_days  = select(
            store_status.c.store_id,
            store_status.c.status,
            store_status.c.timestamp_utc,
        ).select_from(
            store_status
            .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
        ).where(and_(
            store_status.c.timestamp_utc >= start_time_day,
            store_status.c.timestamp_utc < current_utc,
            exists(subquery)  # Use the EXISTS clause here
        )).order_by(
            store_status.c.store_id.asc()
        )
        stmt_weeks = select(
            store_status.c.store_id,
            store_status.c.status,
            store_status.c.timestamp_utc,
        ).select_from(
            store_status
            .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
        ).where(and_(
            store_status.c.timestamp_utc >= start_time_week,
            store_status.c.timestamp_utc < current_utc,
            exists(subquery)  # Use the EXISTS clause here
        )).order_by(
            store_status.c.store_id.asc()
        )


        print("records")
        prev_timestamp = {}
        prev_status = {}
        async with SessionLocal() as session:
            hour_result = await session.stream(stmt_hours) 
            async for batch in hour_result.yield_per(100):  # Controls how many records are fetched per batch
                try:
                    store_id, status, timestamp_utc = batch[0], batch[1], batch[2]
                    print(store_id,status,timestamp_utc)
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                    if store_id not in report_data:
                        report_data[store_id] = {
                            'uptime_last_hour': timedelta(0),
                            'downtime_last_hour': timedelta(0)
                        }
                    
                    if store_id in prev_timestamp:
                        # Calculate the duration from the last timestamp to the current one
                        duration = timestamp_utc - prev_timestamp[store_id]

                        # Check previous status and add the duration to the correct total
                        if prev_status[store_id] == 'active':
                            report_data[store_id]['uptime_last_hour'] += duration
                        elif prev_status[store_id] == 'inactive':
                            report_data[store_id]['downtime_last_hour'] += duration

                    # Update the previous timestamp and status for this store_id
                    prev_timestamp[store_id] = timestamp_utc
                    prev_status[store_id] = status
                    
                    # Handle the final interval for each store_id
                    # for store_id in prev_timestamp:
                    #     current_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
                    #     final_duration = current_utc - prev_timestamp[store_id]
                    #     if prev_status[store_id] == 'active':
                    #         report_data[store_id]['uptime_last_hour'] += final_duration
                    #     elif prev_status[store_id] == 'inactive':
                    #         report_data[store_id]['downtime_last_hour'] += final_duration

                except Exception as e:
                    print(f"Error processing record for store {store_id}: {e}")
            day_result = await session.stream(stmt_hours) 
            async for batch in day_result.yield_per(100):  # Controls how many records are fetched per batch
                try:
                    store_id, status, timestamp_utc = batch[0], batch[1], batch[2]
                    print(store_id,status,timestamp_utc)
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                    if store_id not in report_data:
                        report_data[store_id] = {
                            'uptime_last_day': timedelta(0),
                            'downtime_last_day': timedelta(0)
                        }
                    
                    if store_id in prev_timestamp:
                        # Calculate the duration from the last timestamp to the current one
                        duration = timestamp_utc - prev_timestamp[store_id]

                        # Check previous status and add the duration to the correct total
                        if prev_status[store_id] == 'active':
                            report_data[store_id]['uptime_last_day'] += duration
                        elif prev_status[store_id] == 'inactive':
                            report_data[store_id]['downtime_last_day'] += duration

                    # Update the previous timestamp and status for this store_id
                    prev_timestamp[store_id] = timestamp_utc
                    prev_status[store_id] = status
                    
                    # Handle the final interval for each store_id
                    # for store_id in prev_timestamp:
                    #     current_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
                    #     final_duration = current_utc - prev_timestamp[store_id]
                    #     if prev_status[store_id] == 'active':
                    #         report_data[store_id]['uptime_last_hour'] += final_duration
                    #     elif prev_status[store_id] == 'inactive':
                    #         report_data[store_id]['downtime_last_hour'] += final_duration

                except Exception as e:
                    print(f"Error processing record for store {store_id}: {e}")
            week_result = await session.stream(stmt_hours) 
            async for batch in week_result.yield_per(100):  # Controls how many records are fetched per batch
                try:
                    store_id, status, timestamp_utc = batch[0], batch[1], batch[2]
                    print(store_id,status,timestamp_utc)
                    timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

                    if store_id not in report_data:
                        report_data[store_id] = {
                            'uptime_last_week': timedelta(0),
                            'downtime_last_week': timedelta(0)
                        }
                    
                    if store_id in prev_timestamp:
                        # Calculate the duration from the last timestamp to the current one
                        duration = timestamp_utc - prev_timestamp[store_id]

                        # Check previous status and add the duration to the correct total
                        if prev_status[store_id] == 'active':
                            report_data[store_id]['uptime_last_week'] += duration
                        elif prev_status[store_id] == 'inactive':
                            report_data[store_id]['downtime_last_week'] += duration

                    # Update the previous timestamp and status for this store_id
                    prev_timestamp[store_id] = timestamp_utc
                    prev_status[store_id] = status
                    
                    # Handle the final interval for each store_id
                    # for store_id in prev_timestamp:
                    #     current_utc = datetime.utcnow().replace(tzinfo=timezone.utc)
                    #     final_duration = current_utc - prev_timestamp[store_id]
                    #     if prev_status[store_id] == 'active':
                    #         report_data[store_id]['uptime_last_hour'] += final_duration
                    #     elif prev_status[store_id] == 'inactive':
                    #         report_data[store_id]['downtime_last_hour'] += final_duration

                except Exception as e:
                    print(f"Error processing record for store {store_id}: {e}")

    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        await session.rollback()
    else:
        await session.commit()
    # result = await session.execute(stmt_hours)
    # records = result.fetchall()
    # print(records)
    # Step 2: Process records to calculate uptime/downtime
    for store_id in prev_timestamp:
        current_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        final_duration = current_utc - prev_timestamp[store_id]
        if prev_status[store_id] == 'active':
            report_data[store_id]['uptime_last_hour'] += final_duration
        elif prev_status[store_id] == 'inactive':
            report_data[store_id]['downtime_last_hour'] += final_duration


    print(report_data,"report_data")
    async with session.begin():
        stmt_hours = text(
            "UPDATE store_reports SET data = :data, status = 'complete' WHERE report_id = :report_id"
        )
        await session.execute(stmt_hours, {'data': str(report_data), 'report_id': report_id})
    await session.commit()

@app.post("/trigger_report/")
async def trigger_report():
    report_id = str(uuid4())
    asyncio.create_task(create_and_generate_report(report_id))
    return {"report_id": report_id}

async def create_and_generate_report(report_id):
    async with SessionLocal() as session:
        await create_report(session, report_id)
        await generate_report(session, report_id)

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

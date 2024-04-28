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
from uuid import uuid4
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import asyncio
from sqlalchemy import text,create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

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
    # Simulate data processing
    await asyncio.sleep(10)  # Simulate time-consuming processing
    report_data = "Simulated report data"  # Placeholder for real report generation logic
    async with session.begin():
        stmt = text("UPDATE store_reports SET data = :data, status = 'complete' WHERE report_id = :report_id")
        await session.execute(stmt, {'data': report_data, 'report_id': report_id})
    await session.commit()

@app.post("/trigger_report/")
async def trigger_report():
    report_id = str(uuid4())
    async with SessionLocal() as session:
        await create_report(session, report_id)
        asyncio.create_task(generate_report(session, report_id))  # Start background task
    return {"report_id": report_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

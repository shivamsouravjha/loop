from sqlalchemy import select, func, and_, Time, exists, text
from datetime import datetime, timedelta
from app.database.createSchema import store_hours, store_status,store_timezone
from sqlalchemy.sql import extract
from sqlalchemy.exc import SQLAlchemyError
from app.dependencies import SessionLocal
from app.helpers.processBatch import process_batch
import asyncio
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
        # start_time_hour = current_utc - timedelta(hours=1)
        # start_time_day = current_utc - timedelta(days=1)
        # start_time_week = current_utc - timedelta(weeks=1)
        # subquery = (
        #     select(1)  # We select a constant value because we only care if rows exist, not their content
        #     .where(and_(
        #         store_hours.c.store_id == store_status.c.store_id,
        #         extract('hour', func.cast(store_status.c.timestamp_utc, Time)) >= extract('hour', store_hours.c.start_time_local),
        #         extract('hour', func.cast(store_status.c.timestamp_utc, Time)) <= extract('hour', store_hours.c.end_time_local)
        #     ))
        #     .correlate(store_status)  # Ensure the subquery is correlated with the outer query
        # )

        # stmt_hours  = select(
        #     store_status.c.store_id,
        #     store_status.c.status,
        #     store_status.c.timestamp_utc,
        # ).select_from(
        #     store_status
        #     .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
        # ).where(and_(
        #     store_status.c.timestamp_utc >= start_time_hour,
        #     store_status.c.timestamp_utc < current_utc,
        #     exists(subquery)  # Use the EXISTS clause here
        # )).order_by(
        #     store_status.c.store_id.asc()
        # ).limit(100)

        
        
        report_data= {}


        
        # async with SessionLocal() as session:
        #     hour_result = await session.stream(stmt_hours) 
        #     async for batch in hour_result.yield_per(100):  # Controls how many records are fetched per batch
        #         try:
        #             store_id= batch[0]
        #             await process_batch(batch,report_data,prev_timestamp_hour,prev_status_hour,'uptime_last_hour','downtime_last_hour')
        #         except Exception as e:
        #             print(f"Error processing record for store {store_id}: {e}")
        #     day_result = await session.stream(stmt_days) 
        #     async for batch in day_result.yield_per(100):  # Controls how many records are fetched per batch
        #         try:
        #             store_id= batch[0]
        #             await process_batch(batch,report_data,prev_timestamp_day,prev_status_day,'uptime_last_day','downtime_last_day')
        #         except Exception as e:
        #             print(f"Error processing record for store {store_id}: {e}")
        #     week_result = await session.stream(stmt_weeks) 
        #     async for batch in week_result.yield_per(100):  # Controls how many records are fetched per batch
        #         try:
        #             store_id= batch[0]
        #             await process_batch(batch,report_data,prev_timestamp_week,prev_status_week,'uptime_last_week','downtime_last_week')
        #         except Exception as e:
        #             print(f"Error processing record for store {store_id}: {e}")
        await asyncio.gather(
            process_hours(current_utc, report_data),
            process_day(current_utc, report_data),
            process_weeks(current_utc, report_data)
        )
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        await session.rollback()
    else:
        await session.commit()
    print(report_data)

    print(report_data,"report_data")
    async with session.begin():
        stmt_hours = text(
            "UPDATE store_reports SET data = :data, status = 'complete' WHERE report_id = :report_id"
        )
        await session.execute(stmt_hours, {'data': str(report_data), 'report_id': report_id})
    await session.commit()

async def process_hours(current_utc, report_data):
    start_time_hour = current_utc - timedelta(hours=1)
    prev_timestamp_hour = {}
    prev_status_hour = {}
    subquery = (
        select(1)
        .where(and_(
            store_hours.c.store_id == store_status.c.store_id,
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) >= extract('hour', store_hours.c.start_time_local),
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) <= extract('hour', store_hours.c.end_time_local)
        ))
        .correlate(store_status)
    )
    stmt_hours = select(
        store_status.c.store_id,
        store_status.c.status,
        store_status.c.timestamp_utc,
    ).select_from(
        store_status
        .outerjoin(store_timezone, store_status.c.store_id == store_timezone.c.store_id)
    ).where(and_(
        store_status.c.timestamp_utc >= start_time_hour,
        store_status.c.timestamp_utc < current_utc,
        exists(subquery)
    )).order_by(
        store_status.c.store_id.asc(),
        store_status.c.timestamp_utc.asc()
    ).limit(100)
    
    async with SessionLocal() as session:
        hour_result = await session.stream(stmt_hours)
        async for batch in hour_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_hour,prev_status_hour,'uptime_last_hour','downtime_last_hour')



async def process_day(current_utc,report_data):
    start_time_day = current_utc - timedelta(days=1)
    prev_timestamp_day = {}
    prev_status_day = {}
    subquery = (
        select(1)
        .where(and_(
            store_hours.c.store_id == store_status.c.store_id,
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) >= extract('hour', store_hours.c.start_time_local),
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) <= extract('hour', store_hours.c.end_time_local)
        ))
        .correlate(store_status)
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
        store_status.c.store_id.asc(),
        store_status.c.timestamp_utc.asc()
    ).limit(100)

    async with SessionLocal() as session:
        days_result = await session.stream(stmt_days)
        async for batch in days_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_day,prev_status_day,'uptime_last_day','downtime_last_day')



async def process_weeks(current_utc,report_data):
    start_time_week = current_utc - timedelta(days=1)
    prev_timestamp_week = {}
    prev_status_week = {}
    subquery = (
        select(1)
        .where(and_(
            store_hours.c.store_id == store_status.c.store_id,
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) >= extract('hour', store_hours.c.start_time_local),
            extract('hour', func.cast(store_status.c.timestamp_utc, Time)) <= extract('hour', store_hours.c.end_time_local)
        ))
        .correlate(store_status)
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
        store_status.c.store_id.asc(),
        store_status.c.timestamp_utc.asc()
    ).limit(100)
    async with SessionLocal() as session:
        weeks_result = await session.stream(stmt_weeks)
        async for batch in weeks_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_week,prev_status_week,'uptime_last_day','downtime_last_day')

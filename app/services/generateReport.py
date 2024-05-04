from sqlalchemy import select, func, and_, Time, exists, text
from datetime import datetime, timedelta
from app.database.createSchema import store_hours, store_status,store_timezone
from sqlalchemy.sql import extract
from sqlalchemy.exc import SQLAlchemyError
from app.dependencies import SessionLocal
from app.helpers.processBatch import process_batch
import asyncio
from pytz import utc

async def generate_report(session, report_id):
    current_utc_str = "2023-01-19 15:28:46.983397"
    current_utc = datetime.strptime(current_utc_str, "%Y-%m-%d %H:%M:%S.%f")
    report_data = {}
    try:
        report_data_hour= {}
        report_data_day= {}
        report_data_week= {}
        await asyncio.gather(
            process_hours(current_utc, report_data_hour),
            process_day(current_utc, report_data_day),
            process_weeks(current_utc, report_data_week)
        )
        report_data = merge_reports(report_data_hour,report_data_day,report_data_week)
    except SQLAlchemyError as e:
        print(f"An error occurred: {e}")
        await session.rollback()
    else:
        await session.commit()

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
    )
    
    async with SessionLocal() as session:
        hour_result = await session.stream(stmt_hours)
        async for batch in hour_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_hour,prev_status_hour,'uptime_last_hour','downtime_last_hour',start_time_hour,60)
        await finalize_durations(report_data, prev_timestamp_hour, prev_status_hour, 'uptime_last_hour', 'downtime_last_hour', current_utc,60)



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
    )

    async with SessionLocal() as session:
        days_result = await session.stream(stmt_days)
        async for batch in days_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_day,prev_status_day,'uptime_last_day','downtime_last_day',start_time_day,3600)
        await finalize_durations(report_data, prev_timestamp_day, prev_status_day, 'uptime_last_day', 'downtime_last_day', current_utc,3600)



async def process_weeks(current_utc,report_data):
    start_time_week = current_utc - timedelta(weeks=1)
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
    )
    async with SessionLocal() as session:
        weeks_result = await session.stream(stmt_weeks)
        async for batch in weeks_result.yield_per(100):
            await process_batch(batch,report_data,prev_timestamp_week,prev_status_week,'uptime_last_week','downtime_last_week',start_time_week,3600)
        await finalize_durations(report_data, prev_timestamp_week, prev_status_week, 'uptime_last_week', 'downtime_last_week', current_utc,3600)

def merge_reports(hourly_data, daily_data, weekly_data):
    # Initialize the final report dictionary
    final_report = {}

    # All unique store_ids across all reports
    all_store_ids = set(hourly_data.keys()) | set(daily_data.keys()) | set(weekly_data.keys())

    # Iterate over each store_id to combine data
    for store_id in all_store_ids:
        final_report[store_id] = {
            'uptime_last_hour': 0,
            'downtime_last_hour': 0,
            'uptime_last_day': 0,
            'downtime_last_day': 0,
            'uptime_last_week': 0,
            'downtime_last_week': 0,
        }

        # Merge hourly data if available
        if store_id in hourly_data:
            final_report[store_id]['uptime_last_hour'] = hourly_data[store_id].get('uptime_last_hour', 0)
            final_report[store_id]['downtime_last_hour'] = hourly_data[store_id].get('downtime_last_hour', 0)
        
        # Merge daily data if available
        if store_id in daily_data:
            final_report[store_id]['uptime_last_day'] = daily_data[store_id].get('uptime_last_day', 0)
            final_report[store_id]['downtime_last_day'] = daily_data[store_id].get('downtime_last_day', 0)

        # Merge weekly data if available
        if store_id in weekly_data:
            final_report[store_id]['uptime_last_week'] = weekly_data[store_id].get('uptime_last_week', 0)
            final_report[store_id]['downtime_last_week'] = weekly_data[store_id].get('downtime_last_week', 0)

    return final_report

async def finalize_durations(report_data, prev_timestamps, prev_statuses, uptime_key, downtime_key, current_utc, unit_time):
    for store_id in prev_timestamps:
        # Ensure both datetimes are offset-aware
        if prev_timestamps[store_id].tzinfo is None:
            prev_timestamps[store_id] = utc.localize(prev_timestamps[store_id])
        if current_utc.tzinfo is None:
            current_utc = utc.localize(current_utc)

        # Now perform the subtraction
        final_duration = abs((current_utc - prev_timestamps[store_id]).total_seconds() / unit_time)
        if prev_statuses[store_id] == 'active':
            report_data[store_id][uptime_key] += final_duration
        elif prev_statuses[store_id] == 'inactive':
            report_data[store_id][downtime_key] += final_duration

from datetime import timezone
from asyncio import Lock

lock = Lock()

async def process_batch(batch, report_data,prev_timestamps,prev_statuses,uptime_key,downtime_key, start_time_period, result_unit):
    async with lock:
            store_id, status, timestamp_utc = batch[0], batch[1], batch[2]
            if store_id not in report_data:
                report_data[store_id] = {
                    'uptime_last_hour': 0,
                    'downtime_last_hour': 0,
                    'uptime_last_day':0,
                    'downtime_last_day': 0,
                    'uptime_last_week': 0,
                    'downtime_last_week':0 
                }
            if store_id not in prev_timestamps:
                # Initialize with the start of the period
                prev_timestamps[store_id] = start_time_period.replace(tzinfo=timezone.utc)
                prev_statuses[store_id] = status  # No previous status at the start

            duration = abs((timestamp_utc - prev_timestamps[store_id]).total_seconds()) / result_unit  # Convert to hours
            if prev_statuses[store_id] == 'active':
                    report_data[store_id][uptime_key] += duration
            elif prev_statuses[store_id] == 'inactive':
                    report_data[store_id][downtime_key] += duration

            # Update the last known status and timestamp
            prev_timestamps[store_id] = timestamp_utc
            prev_statuses[store_id] = status
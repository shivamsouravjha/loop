from datetime import timezone
from asyncio import Lock

lock = Lock()

async def process_batch(batch, report_data,prev_timestamp_week,prev_status_week,uptime,downtime):
    async with lock:
            store_id, status, timestamp_utc = batch[0], batch[1], batch[2]
            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)

            if store_id not in report_data:
                report_data[store_id] = {
                    'uptime_last_hour': 0,
                    'downtime_last_hour': 0,
                    'uptime_last_day':0,
                    'downtime_last_day': 0,
                    'uptime_last_week': 0,
                    'downtime_last_week':0 
                }
            
            if store_id in prev_timestamp_week:
                # Calculate the duration from the last timestamp to the current one
                duration = timestamp_utc - prev_timestamp_week[store_id]
                duration = abs((prev_timestamp_week[store_id] - timestamp_utc).total_seconds() / 3600)

                # Check previous status and add the duration to the correct total
                if prev_status_week[store_id] == 'active':
                    report_data[store_id][uptime] += duration
                elif prev_status_week[store_id] == 'inactive':
                    report_data[store_id][downtime] += duration
            prev_timestamp_week[store_id] = timestamp_utc
            prev_status_week[store_id] = status

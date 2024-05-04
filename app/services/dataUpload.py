from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.core.scheduler import setup_scheduler
from app.database.dataSync import load_csv_to_db
def startup_event():
    scheduler = setup_scheduler()
    index_file_path = "data_upload_check.txt"  # Central file for tracking
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        hours=1,
        args=["data/store_timezone.csv", 'store_timezone',index_file_path],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        hours=1,
        args=["data/Menu_hours.csv", 'store_hours',index_file_path],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        hours=1,
        args=["data/store_status.csv", 'store_status',index_file_path],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.start()


from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.core.scheduler import setup_scheduler
from app.database.dataSync import load_csv_to_db
def startup_event():
    scheduler = setup_scheduler()
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/bq-results-20230125-202210-1674678181880.csv", 'store_timezone',"/Users/shivamsouravjha/loop/c.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/Menu_hours.csv", 'store_hours',"/Users/shivamsouravjha/loop/b.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.add_job(
        load_csv_to_db,
        'interval', 
        minutes=1,
        args=["/Users/shivamsouravjha/loop/data/store_status.csv", 'store_status',"/Users/shivamsouravjha/loop/a.txt"],
        next_run_time=datetime.now()  # Start immediately
    )
    scheduler.start()


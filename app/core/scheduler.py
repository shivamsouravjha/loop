from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
import logging

def job_listener(event):
    if event.exception:
        logging.error('The job crashed :(')
    else:
        logging.info('The job worked :)')

def setup_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    return scheduler
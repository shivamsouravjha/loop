
from fastapi import APIRouter, HTTPException
from app.services.reportService import create_and_generate_report
from app.services.reportStatusLogic import report_status
import asyncio
from uuid import uuid4

reporting_router = APIRouter()

@reporting_router.post("/trigger_report/")
async def trigger_report():
    report_id = str(uuid4())
    asyncio.create_task(create_and_generate_report(report_id))
    return {"report_id": report_id}

@reporting_router.get("/report_status/{report_id}")
async def fetch_report_status(report_id: str):
    result = await report_status(report_id)
    if result:
        return result
    else:
        raise HTTPException(status_code=404, detail="Report not found")
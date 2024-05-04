from app.dependencies import SessionLocal
from sqlalchemy import select,text

async def report_status(report_id: str):
    async with SessionLocal() as session:
        result = await session.execute(select(text("status, data FROM store_reports WHERE report_id = :report_id")), {'report_id': report_id})
        report = result.fetchone()
        if report:
            return {"report_id": report_id, "status": report.status, "data": report.data}
        else:
            return None
from app.dependencies import SessionLocal
from app.services.generateReport import generate_report
from app.services.createReport import create_report

async def create_and_generate_report(report_id):
    async with SessionLocal() as session:
        await create_report(session, report_id)
        await generate_report(session, report_id)

# plus other functions that handle report creation and fetching

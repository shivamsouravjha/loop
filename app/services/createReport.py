from sqlalchemy import text
async def create_report(session, report_id):
    async with session.begin():
        await session.execute(text("INSERT INTO store_reports (report_id, status, data) VALUES (:report_id, 'pending', NULL)"), {'report_id': report_id})
    await session.commit()

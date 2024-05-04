from fastapi import FastAPI
from app.api.routers import api_router
from app.services.dataUpload import startup_event
app = FastAPI(title="Availability Manager")

async def start_app() -> None:
    print("Starting up...")
    startup_event()

app.add_event_handler("startup", start_app)
app.include_router(api_router)

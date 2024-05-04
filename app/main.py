from fastapi import FastAPI
from app.api.routers import api_router
from app.services.dataUpload import startup_event
app = FastAPI(title="Availability Manager")

@app.on_event("startup")
async def eventHandler():
    print("Starting up...")
    startup_event()

app.include_router(api_router)

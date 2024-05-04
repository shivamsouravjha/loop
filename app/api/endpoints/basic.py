from fastapi import APIRouter

basic_router = APIRouter()

@basic_router.get("/ping")
async def ping():
    return {"message": "pong"}

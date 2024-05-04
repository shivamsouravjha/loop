from fastapi import APIRouter
from .endpoints.reporting import reporting_router
from .endpoints.basic import basic_router

api_router = APIRouter()
api_router.include_router(reporting_router, prefix="/reporting", tags=["reporting"])
api_router.include_router(basic_router, prefix="/basic", tags=["basic"])

from fastapi import APIRouter
from .endpoints import auth, dashboard

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

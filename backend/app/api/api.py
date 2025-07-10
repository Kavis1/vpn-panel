from fastapi import APIRouter
from .endpoints import auth, dashboard, users, nodes, subscriptions
from .v1.api import api_router as api_v1_router

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["subscriptions"])
api_router.include_router(api_v1_router, prefix="/v1")

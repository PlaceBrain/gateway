from fastapi import APIRouter

from src.api import auth, places

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.controllers.router)
api_router.include_router(places.controllers.router)

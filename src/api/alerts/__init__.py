from fastapi import APIRouter

from .global_alerts import router as global_router
from .place_alerts import router as place_router

router = APIRouter()

router.include_router(place_router)
router.include_router(global_router)

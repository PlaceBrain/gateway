from fastapi import APIRouter

from .actuators import router as actuators_router
from .commands import router as commands_router
from .devices import router as devices_router
from .sensors import router as sensors_router
from .thresholds import router as thresholds_router

router = APIRouter()

router.include_router(devices_router)
router.include_router(sensors_router)
router.include_router(actuators_router)
router.include_router(thresholds_router)
router.include_router(commands_router)

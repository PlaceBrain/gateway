from fastapi import APIRouter

from src.api import alerts, auth, devices, mqtt, places, telemetry

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.controllers.router)
api_router.include_router(places.controllers.router)
api_router.include_router(devices.router)
api_router.include_router(mqtt.router)
api_router.include_router(mqtt.internal_router)
api_router.include_router(telemetry.controllers.router)
api_router.include_router(alerts.router)

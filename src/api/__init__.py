from fastapi import APIRouter

from src.api import auth, devices, mqtt, places, telemetry

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.controllers.router)
api_router.include_router(places.controllers.router)
api_router.include_router(devices.controllers.router)
api_router.include_router(devices.controllers.mqtt_router)
api_router.include_router(mqtt.controllers.router)
api_router.include_router(telemetry.controllers.router)

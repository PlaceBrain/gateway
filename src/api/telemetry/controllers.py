from datetime import UTC

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts.collector_pb2 import GetLatestReadingsRequest
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2 import GetDeviceRequest as GrpcGetDeviceRequest
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser

from .schemas import LatestReadingsResponse, SensorReadingResponse

router = APIRouter(
    prefix="/places/{place_id}/devices/{device_id}/telemetry",
    tags=["telemetry"],
    route_class=DishkaRoute,
)


@router.get("/latest", response_model=LatestReadingsResponse)
async def get_latest_readings(
    place_id: str,
    device_id: str,
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
):
    # Access check: verifies user has role in place and device belongs to place
    await devices_stub.GetDevice(
        GrpcGetDeviceRequest(user_id=current_user.user_id, place_id=place_id, device_id=device_id)
    )

    response = await collector_stub.GetLatestReadings(GetLatestReadingsRequest(device_id=device_id))

    return LatestReadingsResponse(
        readings=[
            SensorReadingResponse(
                key=r.key,
                value=r.value,
                time=r.time.ToDatetime(tzinfo=UTC).isoformat(),
            )
            for r in response.readings
        ]
    )

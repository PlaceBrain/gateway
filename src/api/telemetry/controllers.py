from datetime import UTC, datetime

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from google.protobuf.timestamp_pb2 import Timestamp
from placebrain_contracts.collector_pb2 import (
    GetLatestReadingsRequest,
    GetReadingsRequest,
)
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2 import GetDeviceRequest as GrpcGetDeviceRequest
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser

from .schemas import (
    AggregatedPoint,
    LatestReadingsResponse,
    RawPoint,
    ReadingsHistoryResponse,
    SensorReadingResponse,
    SeriesResponse,
)

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


def _iso_to_proto_ts(iso: str) -> Timestamp:
    dt = datetime.fromisoformat(iso)
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


@router.get("/history", response_model=ReadingsHistoryResponse)
async def get_readings_history(
    place_id: str,
    device_id: str,
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
    time_from: str = Query(alias="from"),
    time_to: str = Query(alias="to"),
    interval: int = Query(default=0),
    keys: str | None = Query(default=None),
):
    await devices_stub.GetDevice(
        GrpcGetDeviceRequest(
            user_id=current_user.user_id,
            place_id=place_id,
            device_id=device_id,
        )
    )

    key_list = [k.strip() for k in keys.split(",") if k.strip()] if keys else []

    response = await collector_stub.GetReadings(
        GetReadingsRequest(
            device_id=device_id,
            keys=key_list,
            interval_seconds=interval,
            **{"from": _iso_to_proto_ts(time_from)},
            to=_iso_to_proto_ts(time_to),
        )
    )

    series_list: list[SeriesResponse] = []
    for s in response.series:
        points = [
            AggregatedPoint(
                time=p.time.ToDatetime(tzinfo=UTC).isoformat(),
                avg=p.avg if p.HasField("avg") else None,
                min=p.min if p.HasField("min") else None,
                max=p.max if p.HasField("max") else None,
            )
            for p in s.points
        ]
        raw_points = [
            RawPoint(
                time=r.time.ToDatetime(tzinfo=UTC).isoformat(),
                value=r.value,
            )
            for r in s.raw_points
        ]
        series_list.append(SeriesResponse(key=s.key, points=points, raw_points=raw_points))

    return ReadingsHistoryResponse(series=series_list)

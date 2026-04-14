from datetime import UTC, datetime
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from google.protobuf.timestamp_pb2 import Timestamp
from placebrain_contracts import collector_pb2 as collector_pb
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import AUTH_ERRORS, FORBIDDEN_ERRORS, NOT_FOUND_ERRORS

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


@router.get(
    "/latest",
    response_model=LatestReadingsResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def get_latest_readings(
    place_id: UUID,
    device_id: UUID,
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
):
    await devices_stub.GetDevice(
        devices_pb.GetDeviceRequest(
            user_id=current_user.user_id, place_id=str(place_id), device_id=str(device_id)
        )
    )

    response = await collector_stub.GetLatestReadings(
        collector_pb.GetLatestReadingsRequest(device_id=str(device_id))
    )

    return LatestReadingsResponse(
        readings=[
            SensorReadingResponse(
                key=r.key,
                value=r.value,
                time=r.time.ToDatetime(tzinfo=UTC),
            )
            for r in response.readings
        ]
    )


def _iso_to_proto_ts(iso: str) -> Timestamp:
    dt = datetime.fromisoformat(iso)
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


@router.get(
    "/history",
    response_model=ReadingsHistoryResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def get_readings_history(
    place_id: UUID,
    device_id: UUID,
    devices_stub: FromDishka[DevicesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
    time_from: str = Query(
        alias="from",
        description="Start time in ISO 8601 format (e.g. 2024-01-01T00:00:00Z)",
    ),
    time_to: str = Query(
        alias="to",
        description="End time in ISO 8601 format (e.g. 2024-01-02T00:00:00Z)",
    ),
    interval: int = Query(
        default=0,
        description="Aggregation interval in seconds. 0 = raw data without aggregation",
    ),
    keys: str | None = Query(
        default=None,
        description="Comma-separated sensor keys to filter (e.g. 'temperature,humidity')",
    ),
):
    await devices_stub.GetDevice(
        devices_pb.GetDeviceRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
        )
    )

    key_list = [k.strip() for k in keys.split(",") if k.strip()] if keys else []

    response = await collector_stub.GetReadings(
        collector_pb.GetReadingsRequest(
            device_id=str(device_id),
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
                time=p.time.ToDatetime(tzinfo=UTC),
                avg=p.avg if p.HasField("avg") else None,
                min=p.min if p.HasField("min") else None,
                max=p.max if p.HasField("max") else None,
            )
            for p in s.points
        ]
        raw_points = [
            RawPoint(
                time=r.time.ToDatetime(tzinfo=UTC),
                value=r.value,
            )
            for r in s.raw_points
        ]
        series_list.append(SeriesResponse(key=s.key, points=points, raw_points=raw_points))

    return ReadingsHistoryResponse(series=series_list)

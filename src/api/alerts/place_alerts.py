from datetime import datetime
from math import ceil
from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query
from google.protobuf.timestamp_pb2 import Timestamp
from placebrain_contracts import collector_pb2 as collector_pb
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.core.enums import (
    ALERT_SEVERITY_TO_PROTO,
    ALERT_STATUS_TO_PROTO,
    AlertSeverity,
    AlertStatus,
)
from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import (
    AUTH_ERRORS,
    FORBIDDEN_ERRORS,
    NOT_FOUND_ERRORS,
    PaginatedResponse,
)

from .schemas import AlertResponse, PlaceAlertCountResponse

router = APIRouter(
    prefix="/places/{place_id}/alerts",
    tags=["alerts"],
    route_class=DishkaRoute,
)


def _dt_to_proto_ts(dt: datetime) -> Timestamp:
    ts = Timestamp()
    ts.FromDatetime(dt)
    return ts


@router.get(
    "",
    response_model=PaginatedResponse[AlertResponse],
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def list_alerts(
    place_id: UUID,
    places_stub: FromDishka[PlacesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
    status: Annotated[AlertStatus | None, Query()] = None,
    severity: Annotated[AlertSeverity | None, Query()] = None,
    sensor_id: Annotated[UUID | None, Query()] = None,
    device_id: Annotated[UUID | None, Query()] = None,
    time_from: Annotated[datetime | None, Query(alias="from")] = None,
    time_to: Annotated[datetime | None, Query(alias="to")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedResponse[AlertResponse]:
    await places_stub.GetPlace(
        places_pb.GetPlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )

    request = collector_pb.GetAlertsRequest(
        place_id=str(place_id),
        page=page,
        per_page=per_page,
    )
    if status is not None:
        request.status = ALERT_STATUS_TO_PROTO[status]  # type: ignore[assignment]
    if severity is not None:
        request.severity = ALERT_SEVERITY_TO_PROTO[severity]  # type: ignore[assignment]
    if sensor_id is not None:
        request.sensor_id = str(sensor_id)
    if device_id is not None:
        request.device_id = str(device_id)
    if time_from is not None:
        getattr(request, "from").CopyFrom(_dt_to_proto_ts(time_from))
    if time_to is not None:
        request.to.CopyFrom(_dt_to_proto_ts(time_to))

    response = await collector_stub.GetAlerts(request)

    total_pages = ceil(response.total / per_page) if per_page else 0
    return PaginatedResponse[AlertResponse](
        items=[AlertResponse.from_proto(a) for a in response.items],
        total=response.total,
        page=page,
        per_page=per_page,
        has_next=page < total_pages,
        has_prev=page > 1,
    )


@router.get(
    "/count",
    response_model=PlaceAlertCountResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def get_place_alert_count(
    place_id: UUID,
    places_stub: FromDishka[PlacesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
) -> PlaceAlertCountResponse:
    await places_stub.GetPlace(
        places_pb.GetPlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    response = await collector_stub.GetAlertCounts(
        collector_pb.GetAlertCountsRequest(place_id=[str(place_id)])
    )
    return PlaceAlertCountResponse(unresolved=response.total_unresolved)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def resolve_alert(
    place_id: UUID,
    alert_id: UUID,
    places_stub: FromDishka[PlacesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
) -> AlertResponse:
    await places_stub.GetPlace(
        places_pb.GetPlaceRequest(user_id=current_user.user_id, place_id=str(place_id))
    )
    response = await collector_stub.ResolveAlert(
        collector_pb.ResolveAlertRequest(alert_id=str(alert_id))
    )
    return AlertResponse.from_proto(response.alert)

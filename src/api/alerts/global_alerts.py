from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import collector_pb2 as collector_pb
from placebrain_contracts import places_pb2 as places_pb
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import AUTH_ERRORS

from .schemas import GlobalAlertCountResponse

router = APIRouter(prefix="/alerts", tags=["alerts"], route_class=DishkaRoute)


@router.get(
    "/count",
    response_model=GlobalAlertCountResponse,
    responses={**AUTH_ERRORS},
)
async def get_global_alert_count(
    places_stub: FromDishka[PlacesServiceStub],
    collector_stub: FromDishka[CollectorServiceStub],
    current_user: AuthenticatedUser,
) -> GlobalAlertCountResponse:
    places_response = await places_stub.ListPlaces(
        places_pb.ListPlacesRequest(user_id=current_user.user_id)
    )
    place_ids = [p.place_id for p in places_response.places]
    if not place_ids:
        return GlobalAlertCountResponse(total_unresolved=0, by_place={})

    counts = await collector_stub.GetAlertCounts(
        collector_pb.GetAlertCountsRequest(place_id=place_ids)
    )
    return GlobalAlertCountResponse(
        total_unresolved=counts.total_unresolved,
        by_place={UUID(pid): n for pid, n in counts.unresolved_by_place.items()},
    )

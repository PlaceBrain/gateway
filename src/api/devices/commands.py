from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter
from placebrain_contracts import devices_pb2 as devices_pb
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub

from src.dependencies.auth import AuthenticatedUser
from src.schemas.base import AUTH_ERRORS, FORBIDDEN_ERRORS, NOT_FOUND_ERRORS, SuccessResponse

from .schemas import SendCommandRequest

router = APIRouter(
    prefix="/places/{place_id}/devices/{device_id}", tags=["commands"], route_class=DishkaRoute
)


@router.post(
    "/command",
    response_model=SuccessResponse,
    responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, **NOT_FOUND_ERRORS},
)
async def send_command(
    place_id: UUID,
    device_id: UUID,
    body: SendCommandRequest,
    stub: FromDishka[DevicesServiceStub],
    current_user: AuthenticatedUser,
) -> SuccessResponse:
    response = await stub.SendCommand(
        devices_pb.SendCommandRequest(
            user_id=current_user.user_id,
            place_id=str(place_id),
            device_id=str(device_id),
            actuator_key=body.actuator_key,
            value=body.value,
        )
    )
    return SuccessResponse(success=response.success)

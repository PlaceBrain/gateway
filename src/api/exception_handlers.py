import logging

import grpc
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse

logger = logging.getLogger(__name__)

_GRPC_TO_HTTP_STATUS: dict[grpc.StatusCode, int] = {
    grpc.StatusCode.NOT_FOUND: 404,
    grpc.StatusCode.ALREADY_EXISTS: 409,
    grpc.StatusCode.UNAUTHENTICATED: 401,
    grpc.StatusCode.PERMISSION_DENIED: 403,
    grpc.StatusCode.INVALID_ARGUMENT: 422,
    grpc.StatusCode.UNAVAILABLE: 503,
    grpc.StatusCode.RESOURCE_EXHAUSTED: 429,
    grpc.StatusCode.DEADLINE_EXCEEDED: 504,
    grpc.StatusCode.FAILED_PRECONDITION: 400,
}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(grpc.aio.AioRpcError)
    async def grpc_error_handler(request: Request, exc: grpc.aio.AioRpcError) -> ORJSONResponse:
        status_code = _GRPC_TO_HTTP_STATUS.get(exc.code(), 500)
        detail = exc.details() or "Unknown error"

        if status_code == 500:
            logger.error("Unhandled gRPC error: %s", exc, exc_info=True)

        return ORJSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception) -> ORJSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return ORJSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

import logging
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api.auth import router as auth_router
from src.api.exception_handlers import register_exception_handlers
from src.core.config import settings
from src.dependencies.config import ConfigProvider
from src.dependencies.grpc import GrpcProvider

container = make_async_container(
    ConfigProvider(),
    GrpcProvider(),
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(
        level=settings.logging.level_value,
        format=settings.logging.format,
        datefmt=settings.logging.date_format,
    )
    try:
        yield
    finally:
        await container.close()


app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)
register_exception_handlers(app)
app.include_router(auth_router)
setup_dishka(container, app)

import logging
from contextlib import asynccontextmanager

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from src.api import api_router
from src.api.exception_handlers import register_exception_handlers
from src.api.utils import generate_openapi_file
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
    generate_openapi_file(app)
    try:
        yield
    finally:
        await container.close()


app = FastAPI(
    title="PlaceBrain API",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)
register_exception_handlers(app)
app.include_router(api_router)
setup_dishka(container, app)

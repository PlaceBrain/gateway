from collections.abc import AsyncIterable

import grpc
from dishka import Provider, Scope, provide
from placebrain_contracts.auth_pb2_grpc import AuthServiceStub
from placebrain_contracts.collector_pb2_grpc import CollectorServiceStub
from placebrain_contracts.devices_pb2_grpc import DevicesServiceStub
from placebrain_contracts.places_pb2_grpc import PlacesServiceStub

from src.core.config import Settings


class GrpcProvider(Provider):
    @provide(scope=Scope.APP)
    async def provide_auth_channel(self, settings: Settings) -> AsyncIterable[grpc.aio.Channel]:
        channel = grpc.aio.insecure_channel(settings.auth_service_url)
        yield channel
        await channel.close()

    @provide(scope=Scope.APP)
    def provide_auth_stub(self, channel: grpc.aio.Channel) -> AuthServiceStub:
        return AuthServiceStub(channel)

    @provide(scope=Scope.APP)
    async def provide_places_stub(self, settings: Settings) -> AsyncIterable[PlacesServiceStub]:
        channel = grpc.aio.insecure_channel(settings.places_service_url)
        try:
            yield PlacesServiceStub(channel)
        finally:
            await channel.close()

    @provide(scope=Scope.APP)
    async def provide_devices_stub(self, settings: Settings) -> AsyncIterable[DevicesServiceStub]:
        channel = grpc.aio.insecure_channel(settings.devices_service_url)
        try:
            yield DevicesServiceStub(channel)
        finally:
            await channel.close()

    @provide(scope=Scope.APP)
    async def provide_collector_stub(
        self, settings: Settings
    ) -> AsyncIterable[CollectorServiceStub]:
        channel = grpc.aio.insecure_channel(settings.collector_service_url)
        try:
            yield CollectorServiceStub(channel)
        finally:
            await channel.close()

# Gateway Service

- **Port:** 8000, **no own DB** — stateless proxy
- FastAPI + Hypercorn, DI via Dishka with FastAPI integration
- OpenAPI: `title="PlaceBrain API"`, `version="1.0.0"`

## Structure

```
src/core/
├── config.py                # Pydantic Settings
└── enums.py                 # StrEnum + proto mappings (single file)

src/api/
├── __init__.py              # Assembly of all routers into api_router
├── exception_handlers.py    # gRPC → HTTP error mapping
├── utils.py                 # OpenAPI JSON generation
├── auth/                    # /api/auth — registration, login, JWT, OTP
├── places/                  # /api/places — CRUD locations and members
├── devices/                 # /api/places/{place_id}/devices/...
│   ├── __init__.py          # Assembly of child routers
│   ├── devices.py           # CRUD devices + regenerate-token
│   ├── sensors.py           # CRUD sensors
│   ├── actuators.py         # CRUD actuators
│   ├── thresholds.py        # Sensor thresholds
│   ├── commands.py          # Sending commands to devices
│   └── schemas.py           # All Pydantic schemas for the package (shared file)
├── mqtt/                    # MQTT endpoints
│   ├── controllers.py       # router (user-facing /api/mqtt) + internal_router (EMQX webhooks)
│   └── schemas.py
└── telemetry/               # /api/places/{place_id}/devices/{device_id}/telemetry
```

**Route organization rules:**
- Each module in `devices/` defines its own `router` with full prefix and `route_class=DishkaRoute` — route_class is **not inherited** from the parent router
- `devices/__init__.py` assembles child routers via `include_router()`, itself has an empty prefix
- MQTT: `router` — user-facing (`/api/mqtt/credentials`), `internal_router` — EMQX webhooks (`/api/internal/mqtt/`, hidden from OpenAPI)
- `/api/internal/` is blocked by Traefik externally, accessible only from the Docker network

## Protobuf Imports

**Import proto modules, not individual classes:**
```python
# Correct:
from placebrain_contracts import devices_pb2 as devices_pb
response = await stub.CreateDevice(devices_pb.CreateDeviceRequest(...))

# Incorrect:
from placebrain_contracts.devices_pb2 import CreateDeviceRequest as GrpcCreateDeviceRequest
```

Stub classes (`DevicesServiceStub`, etc.) — the only exception, imported individually from `*_pb2_grpc` for Dishka type hints.

## Proto → Pydantic Mapping

Response schemas with non-trivial or repetitive mapping **must** have a `from_proto()` classmethod:
```python
class SensorResponse(BaseModel):
    ...
    @classmethod
    def from_proto(cls, s) -> Self:
        return cls(sensor_id=s.sensor_id, value_type=VALUE_TYPE_FROM_PROTO.get(...), ...)
```

Schemas with `from_proto()`: `SensorResponse`, `ActuatorResponse`, `ThresholdResponse`, `DeviceSummaryResponse`, `PlaceResponse`.

**Rule:** if the mapping contains enum conversion or is used more than once — extract into `from_proto()`.

## Enum Mappings

- All enum types are `StrEnum` in `src/core/enums.py`
- Proto int ↔ StrEnum mappings use **named proto constants** (`ROLE_OWNER`, `DEVICE_STATUS_ONLINE`), not magic numbers
- **Do not use** plain `str` for fields with a limited set of values — always StrEnum

## Error Handling

- Centralized exception handlers in `src/api/exception_handlers.py` — **do not duplicate try/except in controllers** for gRPC errors
- When adding a new gRPC StatusCode — **must add mapping** in `exception_handlers.py`
- **Cascade delete:** cleanup operations that can fail should be wrapped in try/except and return `DeleteResponse(warnings=[...])`, do not silently swallow errors
- OpenAPI error responses: document via `responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, ...}` from `src/schemas/base.py`

## Typing

- **ID:** `uuid.UUID` (not `str`). When passing to gRPC: `str(place_id)`
- **Datetime:** `datetime` (not `str`). `last_seen_at` from gRPC may be an empty string → `d.last_seen_at or None`
- **None vs falsy:** for optional numeric fields — `x if x is not None else default`, not `x or default`

## Shared Schemas (`src/schemas/base.py`)

- `PaginatedResponse[T]`, `SuccessResponse`, `DeleteResponse`, `ErrorResponse`, `PaginationParams`
- Pagination is implemented only for `ListDevices`. Other list endpoints return plain lists. **Do not add** gateway-side slicing

## HTTP Status Codes

- **201 Created:** POST endpoints for resource creation (register, create_place, create_device, create_sensor, create_actuator, set_threshold)
- **200 OK:** POST endpoints for actions (login, refresh, logout, send-otp, verify-otp, regenerate-token, send-command, mqtt/credentials)

## Cascade Operations (Event-Driven)

Cascade operations (MQTT credential invalidation, device cleanup, readings deletion) are **no longer orchestrated by gateway**. They are handled via Kafka events:
- **places service** publishes `PlaceDeleted`, `MemberAdded`, `MemberRemoved`, `MemberRoleChanged` events
- **devices service** consumes these events and handles credential invalidation + device cleanup
- **collector service** consumes `DevicesBulkDeleted`/`DeviceDeleted` events for readings cleanup

Gateway simply calls the gRPC method (e.g., `DeletePlace`) and returns the result.

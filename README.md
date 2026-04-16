# gateway

> HTTP API gateway for PlaceBrain — the single REST facade in front of all gRPC backend services.

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](./LICENSE)
![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg)

The gateway is a stateless proxy that speaks HTTP to the outside world and gRPC to the platform. It owns no data of its own. The Vue frontend (and any third-party integration) talks exclusively to this service; EMQX calls a hidden internal router on this service for MQTT authentication.

## Role in PlaceBrain

PlaceBrain is an open-source IoT platform for smart buildings. See the [organization profile](https://github.com/PlaceBrain) for the full architecture.

- Accepts HTTP requests on port 8000, routed in front by Traefik on `/api/*`, `/docs`, and `/openapi.json`.
- Talks over gRPC to [auth](https://github.com/PlaceBrain/auth), [places](https://github.com/PlaceBrain/places), [devices](https://github.com/PlaceBrain/devices), [collector](https://github.com/PlaceBrain/collector).
- Hosts `/api/internal/mqtt/*` for EMQX webhooks — blocked at Traefik, reachable only from the Docker network.
- Never orchestrates cascading deletes — those have moved to Kafka events. The gateway simply calls the relevant gRPC method and returns the result.

## Tech stack

- Python 3.14, uv
- [FastAPI](https://fastapi.tiangolo.com/) 0.128 on [Hypercorn](https://hypercorn.readthedocs.io/)
- Dishka with FastAPI integration (`DishkaRoute`)
- `grpcio` client stubs generated from [placebrain-contracts](https://github.com/PlaceBrain/contracts)
- Pydantic v2, orjson responses

## API surface

Modular by domain (each module has its own `router` with `route_class=DishkaRoute`):

| Prefix | Description |
|---|---|
| `/api/auth/*` | Register, login, refresh, logout, profile, OTP flow |
| `/api/places/*` | CRUD places + members |
| `/api/places/{place_id}/devices/*` | Devices, sensors, actuators, thresholds, commands |
| `/api/places/{place_id}/devices/{device_id}/telemetry` | Readings (raw or time-bucketed) |
| `/api/mqtt/credentials` | Short-lived MQTT credentials for the browser MQTT.js client |
| `/api/internal/mqtt/auth` `/api/internal/mqtt/acl` | EMQX webhooks — hidden from OpenAPI, blocked by Traefik |

Full schema: `http://<host>/docs` when the stack is running.

## Local development

**Full stack (recommended):** clone [infra](https://github.com/PlaceBrain/infra) and run `make dev`. Open `http://localhost` for the SPA and `http://localhost/docs` for the Swagger UI.

**Service-only mode:**

```bash
uv sync
cp .env.example .env
uv run python -m src
```

Requires all backend gRPC services reachable at the URLs configured in `.env`.

## Environment variables

See [`.env.example`](./.env.example). Key points:

| Variable | Purpose |
|---|---|
| `AUTH_SERVICE_URL` etc. | In-cluster `host:port` for each gRPC service |
| `JWT_SECRET` | HS256 key used to validate access tokens — **must match** the auth service's `JWT__SECRET` |

## Project layout

```
src/
├── main.py                      FastAPI app, Dishka container, exception handlers
├── core/
│   ├── config.py                Pydantic Settings
│   └── enums.py                 StrEnum + proto int mappings (single source of truth)
├── api/
│   ├── __init__.py              Assembles the top-level api_router
│   ├── exception_handlers.py    gRPC StatusCode → HTTP status mapping
│   ├── utils.py                 OpenAPI JSON generation
│   ├── auth/                    /api/auth/*
│   ├── places/                  /api/places/*
│   ├── devices/                 /api/places/{place_id}/devices/*
│   ├── mqtt/                    Public + internal MQTT routers
│   └── telemetry/               Readings endpoints
├── schemas/base.py              Shared: PaginatedResponse[T], DeleteResponse, ErrorResponse
└── dependencies/                Dishka providers (grpc stubs, current user)
```

## Conventions

- Every proto→Pydantic mapping that is non-trivial or repeated has a `from_proto()` classmethod on the schema.
- Enum fields are always `StrEnum`; mappings to proto ints use named constants (e.g. `ROLE_OWNER`), never magic numbers.
- `POST` returns **201** for resource creation and **200** for actions (login, refresh, send-command).
- Exception mapping is centralized — controllers do not wrap gRPC calls in try/except.

## License

Apache License 2.0 — see [LICENSE](./LICENSE).

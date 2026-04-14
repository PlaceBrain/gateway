# Gateway Service

- **Порт:** 8000, **без собственной БД** — stateless proxy
- FastAPI + Hypercorn, DI через Dishka с FastAPI-интеграцией
- OpenAPI: `title="PlaceBrain API"`, `version="1.0.0"`

## Структура роутов

```
src/api/
├── __init__.py              # Сборка всех роутеров в api_router
├── enums.py                 # StrEnum + proto-маппинги (единый файл)
├── exception_handlers.py    # gRPC → HTTP маппинг ошибок
├── utils.py                 # Генерация openapi.json
├── auth/                    # /api/auth — регистрация, логин, JWT, OTP
├── places/                  # /api/places — CRUD локаций и участников
├── devices/                 # /api/places/{place_id}/devices/...
│   ├── __init__.py          # Сборка дочерних роутеров
│   ├── devices.py           # CRUD устройств + regenerate-token
│   ├── sensors.py           # CRUD сенсоров
│   ├── actuators.py         # CRUD актуаторов
│   ├── thresholds.py        # Пороги сенсоров
│   ├── commands.py          # Отправка команд на устройства
│   └── schemas.py           # Все Pydantic-схемы пакета (общий файл)
├── mqtt/                    # MQTT endpoints
│   ├── controllers.py       # router (user-facing /api/mqtt) + internal_router (EMQX webhooks)
│   └── schemas.py
└── telemetry/               # /api/places/{place_id}/devices/{device_id}/telemetry
```

**Правила организации роутов:**
- Каждый модуль в `devices/` определяет свой `router` с полным prefix и `route_class=DishkaRoute` — route_class **не наследуется** от parent router
- `devices/__init__.py` собирает дочерние роутеры через `include_router()`, сам имеет пустой prefix
- MQTT: `router` — пользовательский (`/api/mqtt/credentials`), `internal_router` — EMQX-вебхуки (`/api/internal/mqtt/`, скрыт из OpenAPI)
- `/api/internal/` закрыт Traefik'ом снаружи, доступен только из Docker-сети

## Protobuf-импорты

**Импортировать proto-модули, не отдельные классы:**
```python
# Правильно:
from placebrain_contracts import devices_pb2 as devices_pb
response = await stub.CreateDevice(devices_pb.CreateDeviceRequest(...))

# Неправильно:
from placebrain_contracts.devices_pb2 import CreateDeviceRequest as GrpcCreateDeviceRequest
```

Stub-классы (`DevicesServiceStub`, etc.) — единственное исключение, импортируются поштучно из `*_pb2_grpc` для Dishka type hints.

## Proto → Pydantic маппинг

Response-схемы с нетривиальным или повторяющимся маппингом **обязаны** иметь `from_proto()` classmethod:
```python
class SensorResponse(BaseModel):
    ...
    @classmethod
    def from_proto(cls, s) -> Self:
        return cls(sensor_id=s.sensor_id, value_type=VALUE_TYPE_FROM_PROTO.get(...), ...)
```

Схемы с `from_proto()`: `SensorResponse`, `ActuatorResponse`, `ThresholdResponse`, `DeviceSummaryResponse`, `PlaceResponse`.

**Правило:** если маппинг содержит enum-преобразование или используется более одного раза — выносить в `from_proto()`.

## Enum-маппинги

- Все enum-типы — `StrEnum` в `src/api/enums.py`
- Маппинги proto int ↔ StrEnum используют **именованные proto-константы** (`ROLE_OWNER`, `DEVICE_STATUS_ONLINE`), не магические числа
- **Не использовать** plain `str` для полей с ограниченным набором значений — всегда StrEnum

## Обработка ошибок

- Централизованные exception handlers в `src/api/exception_handlers.py` — **не дублировать try/except в контроллерах** для gRPC-ошибок
- При добавлении нового gRPC StatusCode — **обязательно добавить маппинг** в `exception_handlers.py`
- **Cascade delete:** cleanup-операции, которые могут упасть, оборачивать в try/except и возвращать `DeleteResponse(warnings=[...])`, не глотать ошибки молча
- OpenAPI error responses: документировать через `responses={**AUTH_ERRORS, **FORBIDDEN_ERRORS, ...}` из `src/schemas/base.py`

## Типизация

- **ID:** `uuid.UUID` (не `str`). При передаче в gRPC: `str(place_id)`
- **Datetime:** `datetime` (не `str`). `last_seen_at` из gRPC может быть пустой строкой → `d.last_seen_at or None`
- **None vs falsy:** для optional числовых полей — `x if x is not None else default`, не `x or default`

## Shared schemas (`src/schemas/base.py`)

- `PaginatedResponse[T]`, `SuccessResponse`, `DeleteResponse`, `ErrorResponse`, `PaginationParams`
- Пагинация реализована только для `ListDevices`. Остальные list-эндпоинты возвращают простые списки. **Не добавлять** gateway-side slicing

## HTTP status codes

- **201 Created:** POST-эндпоинты создания ресурсов (register, create_place, create_device, create_sensor, create_actuator, set_threshold)
- **200 OK:** POST-эндпоинты действий (login, refresh, logout, send-otp, verify-otp, regenerate-token, send-command, mqtt/credentials)

## MQTT credentials инвалидация

Gateway вызывает `devices.InvalidateMqttCredentials(user_ids)` при мутациях, меняющих состав локаций:
- **create_place** → `current_user`
- **delete_place** → все участники (получить `ListMembers` **до** удаления)
- **add_member** → `target_user`
- **remove_member** → `target_user`
- **update_member_role** — инвалидация **не нужна** (роль не влияет на `allowed_place_ids`)

Инвалидация — fire-and-forget: ошибка логируется, но не ломает ответ.

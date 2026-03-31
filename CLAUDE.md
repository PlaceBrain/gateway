# Gateway Service

- **Порт:** 8000, **без собственной БД** — stateless proxy
- **Единственная точка входа** в сеть микросервисов извне (через nginx)
- FastAPI + Hypercorn, DI через Dishka с FastAPI-интеграцией
- OpenAPI метаданные: `title="PlaceBrain API"`, `version="1.0.0"`

## Роуты

- Все под `/api/`: auth, places, devices (вложенные: sensors, actuators, thresholds, command), mqtt, telemetry
- `/api/internal/` — закрыт nginx'ом (404), используется только EMQX-вебхуками внутри Docker-сети, **скрыт из OpenAPI** (`include_in_schema=False`)

## Auth

- OAuth2PasswordBearer → JWT → AuthenticatedUser dependency
- tokenUrl: `/api/auth/login`

## Обработка ошибок

- Централизованные exception handlers для gRPC-ошибок — **не дублировать try/except в контроллерах**
- При добавлении нового gRPC StatusCode в сервисах — **обязательно добавить маппинг** в `src/api/exception_handlers.py`
- **Cascade delete:** если cleanup-операция может упасть, возвращать `warnings: list[str]` вместо молчаливого `success: True`
- **Error responses в OpenAPI:** эндпоинты документируют возможные ошибки (401/403/404/409) через `responses=` с использованием shared dicts из `src/schemas/base.py` (`AUTH_ERRORS`, `FORBIDDEN_ERRORS`, `NOT_FOUND_ERRORS`, `CONFLICT_ERRORS`)

## Enum-маппинги

- Все enum-типы определены как `StrEnum` в **`src/api/enums.py`**: `PlaceRole`, `DeviceStatus`, `ValueType`, `ThresholdType`, `ThresholdSeverity`
- Маппинги proto int ↔ StrEnum: `ROLE_FROM_PROTO`/`ROLE_TO_PROTO`, `STATUS_FROM_PROTO`, `VALUE_TYPE_FROM_PROTO`/`VALUE_TYPE_TO_PROTO`, и т.д.
- В Pydantic-схемах используются StrEnum-типы напрямую — автоматически появляются как `enum` в OpenAPI
- **Не использовать** plain `str` для полей с ограниченным набором значений — всегда StrEnum

## Типизация схем

- **ID:** `uuid.UUID` (не `str`) — Pydantic автоматически парсит строки из gRPC
- **Datetime:** `datetime` (не `str`) — для `created_at`, `updated_at`, `last_seen_at`, telemetry `time`
- **Path-параметры:** типизированы как `UUID` — FastAPI валидирует формат на входе
- При передаче в gRPC: `str(place_id)`, `str(device_id)` и т.д.
- `last_seen_at` может быть пустой строкой из gRPC → тип `datetime | None`, в контроллере `d.last_seen_at or None`

## Shared schemas

- **`src/schemas/base.py`** — общие модели и утилиты:
  - `PaginatedResponse[T]` — для пагинированных эндпоинтов (items, total, page, per_page, has_next, has_prev)
  - `SuccessResponse` — `{ success: bool }` (используется везде вместо дубликатов)
  - `DeleteResponse` — `{ success: bool, warnings: list[str] }` (cascade delete с предупреждениями)
  - `ErrorResponse` — `{ detail: str }` (для OpenAPI documentation)
  - `PaginationParams` — Annotated dependency для query-параметров page/per_page

## Пагинация

- **Сквозная пагинация** реализована только для `ListDevices` (proto → devices service → gateway → frontend)
- Gateway передаёт `page`/`per_page` в gRPC, получает `total` из ответа, собирает `PaginatedResponse`
- Остальные list-эндпоинты (places, members, sensors, actuators, thresholds) возвращают **простые списки** — коллекции естественно ограничены (5-50 элементов)
- **Не добавлять** gateway-side slicing (фейковую пагинацию) — это не уменьшает нагрузку на БД

## HTTP status codes

- POST-эндпоинты создания ресурсов возвращают **201 Created** (register, create_place, create_device, create_sensor, create_actuator, set_threshold)
- POST-эндпоинты действий возвращают **200 OK** (login, refresh, logout, send-otp, verify-otp, regenerate-token, send-command, mqtt/credentials)

## MQTT credentials инвалидация

- При мутациях, меняющих состав локаций, gateway вызывает `devices.InvalidateMqttCredentials(user_ids)` для сброса кэша Redis
- **create_place** → инвалидировать `current_user`
- **delete_place** → получить `ListMembers` **до** удаления, инвалидировать всех участников
- **add_member** → инвалидировать `target_user`
- **remove_member** → инвалидировать `target_user`
- **update_member_role** — инвалидация **не нужна** (роль не влияет на `allowed_place_ids`)
- Инвалидация — fire-and-forget: ошибка логируется, но не ломает ответ

## Прочее

- Ответы: ORJSON для сериализации
- openapi.json генерируется при старте, маунтится в var/gateway/
- gRPC-стабы: auth, places, devices, collector (APP-scope через Dishka)

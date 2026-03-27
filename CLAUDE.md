# Gateway Service

- **Порт:** 8000, **без собственной БД** — stateless proxy
- **Единственная точка входа** в сеть микросервисов извне (через nginx)
- FastAPI + Hypercorn, DI через Dishka с FastAPI-интеграцией

## Роуты

- Все под `/api/`: auth, places, devices (вложенные: sensors, actuators, thresholds, command), mqtt, telemetry
- `/api/internal/` — закрыт nginx'ом (404), используется только EMQX-вебхуками внутри Docker-сети

## Auth

- OAuth2PasswordBearer → JWT → AuthenticatedUser dependency

## Обработка ошибок

- Централизованные exception handlers для gRPC-ошибок — **не дублировать try/except в контроллерах**
- При добавлении нового gRPC StatusCode в сервисах — **обязательно добавить маппинг** в `src/api/exception_handlers.py`
- **Cascade delete:** если cleanup-операция может упасть, возвращать `warnings: list[str]` вместо молчаливого `success: True`

## Enum-маппинги

- Все маппинги proto enum ↔ HTTP string хранятся в **`src/api/enums.py`** — не дублировать в контроллерах
- Для преобразования string → proto enum использовать `resolve_enum()` из `src/api/enums.py` — **никогда** не использовать `.get(value, default)` с тихим fallback на дефолт

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

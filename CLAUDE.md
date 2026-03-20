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

## Прочее

- Ответы: ORJSON для сериализации
- openapi.json генерируется при старте, маунтится в var/gateway/
- gRPC-стабы: auth, places, devices, collector (APP-scope через Dishka)

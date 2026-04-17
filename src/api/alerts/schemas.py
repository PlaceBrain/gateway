from datetime import UTC, datetime
from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel

from src.core.enums import (
    ALERT_SEVERITY_FROM_PROTO,
    ALERT_STATUS_FROM_PROTO,
    ALERT_THRESHOLD_TYPE_FROM_PROTO,
    AlertSeverity,
    AlertStatus,
    AlertThresholdType,
)


class AlertResponse(BaseModel):
    id: UUID
    sensor_id: UUID
    threshold_id: UUID
    device_id: UUID
    place_id: UUID
    key: str
    value: float
    threshold_value: float
    threshold_type: AlertThresholdType
    severity: AlertSeverity
    status: AlertStatus
    created_at: datetime
    resolved_at: datetime | None

    @classmethod
    def from_proto(cls, a: Any) -> Self:
        return cls(
            id=a.id,
            sensor_id=a.sensor_id,
            threshold_id=a.threshold_id,
            device_id=a.device_id,
            place_id=a.place_id,
            key=a.key,
            value=a.value,
            threshold_value=a.threshold_value,
            threshold_type=ALERT_THRESHOLD_TYPE_FROM_PROTO[a.threshold_type],
            severity=ALERT_SEVERITY_FROM_PROTO[a.severity],
            status=ALERT_STATUS_FROM_PROTO[a.status],
            created_at=a.created_at.ToDatetime(tzinfo=UTC),
            resolved_at=(
                a.resolved_at.ToDatetime(tzinfo=UTC) if a.HasField("resolved_at") else None
            ),
        )


class PlaceAlertCountResponse(BaseModel):
    unresolved: int


class GlobalAlertCountResponse(BaseModel):
    total_unresolved: int
    by_place: dict[UUID, int]

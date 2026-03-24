from pydantic import BaseModel


class SensorReadingResponse(BaseModel):
    key: str
    value: float
    time: str


class LatestReadingsResponse(BaseModel):
    readings: list[SensorReadingResponse]


# --- Historical readings ---


class AggregatedPoint(BaseModel):
    time: str
    avg: float | None = None
    min: float | None = None
    max: float | None = None


class RawPoint(BaseModel):
    time: str
    value: float


class SeriesResponse(BaseModel):
    key: str
    points: list[AggregatedPoint] = []
    raw_points: list[RawPoint] = []


class ReadingsHistoryResponse(BaseModel):
    series: list[SeriesResponse]

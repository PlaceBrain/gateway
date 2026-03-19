from pydantic import BaseModel


class SensorReadingResponse(BaseModel):
    key: str
    value: float
    time: str


class LatestReadingsResponse(BaseModel):
    readings: list[SensorReadingResponse]

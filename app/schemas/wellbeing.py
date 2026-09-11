from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class WellbeingCreate(BaseModel):
    soldier_id: int

    stress_level: float = Field(
        default=0.0,
        ge=0,
        le=100
    )

    sleep_hours: float = Field(
        default=0.0,
        ge=0,
        le=24
    )

    fatigue_level: float = Field(
        default=0.0,
        ge=0,
        le=100
    )

    mood_score: float = Field(
        default=0.0,
        ge=0,
        le=100
    )

    heart_rate: float | None = Field(
        default=None,
        ge=0
    )

    risk_level: float = Field(
        default=0.0,
        ge=0,
        le=100
    )

    notes: str | None = None


class WellbeingResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    soldier_id: int

    stress_level: float
    sleep_hours: float
    fatigue_level: float
    mood_score: float

    heart_rate: float | None
    risk_level: float

    notes: str | None

    created_at: datetime
    recorded_at: datetime
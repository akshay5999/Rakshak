from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class WellbeingRecord(Base):
    __tablename__ = "wellbeing_records"

    # Primary Key
    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Soldier
    soldier_id = Column(
        Integer,
        ForeignKey(
            "soldiers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # Well-being metrics
    stress_level = Column(
        Float,
        nullable=False,
        default=0.0
    )

    sleep_hours = Column(
        Float,
        nullable=False,
        default=0.0
    )

    fatigue_level = Column(
        Float,
        nullable=False,
        default=0.0
    )

    mood_score = Column(
        Float,
        nullable=False,
        default=0.0
    )

    heart_rate = Column(
        Float,
        nullable=True
    )

    # AI-generated risk
    risk_level = Column(
        Float,
        nullable=False,
        default=0.0
    )

    # Notes
    notes = Column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    recorded_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # Relationship
    soldier = relationship(
        "Soldier",
        back_populates="wellbeing_records"
    )
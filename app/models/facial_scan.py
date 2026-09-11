from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
)

from app.database import Base


class FacialScan(Base):
    __tablename__ = "facial_scans"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    soldier_id = Column(
        Integer,
        ForeignKey(
            "soldiers.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ---------------------------------------------------------
    # FACIAL BEHAVIOURAL SIGNALS
    # ---------------------------------------------------------

    forehead_tension = Column(
        Float,
        nullable=False,
        default=0
    )

    eye_closure = Column(
        Float,
        nullable=False,
        default=0
    )

    left_eye_open = Column(
        Float,
        nullable=False,
        default=0
    )

    right_eye_open = Column(
        Float,
        nullable=False,
        default=0
    )

    blink_count = Column(
        Integer,
        nullable=False,
        default=0
    )

    brow_activity = Column(
        Float,
        nullable=False,
        default=0
    )

    mouth_activity = Column(
        Float,
        nullable=False,
        default=0
    )

    expression_intensity = Column(
        Float,
        nullable=False,
        default=0
    )

    facial_signal = Column(
        Float,
        nullable=False,
        default=0
    )

    # ---------------------------------------------------------
    # TIMESTAMP
    # ---------------------------------------------------------

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
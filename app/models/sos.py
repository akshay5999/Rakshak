from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class SOSAlert(Base):
    __tablename__ = "sos_alerts"

    id = Column(Integer, primary_key=True, index=True)

    soldier_id = Column(
        Integer,
        ForeignKey("soldiers.id"),
        nullable=False
    )

    alert_type = Column(
        String,
        nullable=False,
        default="EMERGENCY"
    )

    message = Column(
        String,
        nullable=True
    )

    location = Column(
        String,
        nullable=True
    )

    latitude = Column(
        String,
        nullable=True
    )

    longitude = Column(
        String,
        nullable=True
    )

    status = Column(
        String,
        nullable=False,
        default="ACTIVE"
    )

    is_resolved = Column(
        Boolean,
        default=False
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )
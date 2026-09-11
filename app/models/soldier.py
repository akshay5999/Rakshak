from sqlalchemy import Column, Integer, String, Float, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class Soldier(Base):
    __tablename__ = "soldiers"

    id = Column(Integer, primary_key=True, index=True)

    service_number = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    rank = Column(
        String,
        nullable=False
    )

    unit = Column(
        String,
        nullable=False
    )

    location = Column(
        String,
        nullable=True
    )

    phone = Column(
        String,
        nullable=True
    )

    latitude = Column(
        Float,
        nullable=True
    )

    longitude = Column(
        Float,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    stress_level = Column(
        Float,
        default=0.0
    )

    wellbeing_records = relationship(
        "WellbeingRecord",
        back_populates="soldier",
        cascade="all, delete-orphan"
    )
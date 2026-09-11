from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord
from app.schemas.wellbeing import (
    WellbeingCreate,
    WellbeingResponse,
)


router = APIRouter(
    prefix="/wellbeing",
    tags=["Well-being"]
)


# ============================================================
# GET ALL WELL-BEING RECORDS
# ============================================================

@router.get(
    "/",
    response_model=list[WellbeingResponse]
)
def get_wellbeing_records(
    db: Session = Depends(get_db)
):
    records = (
        db.query(WellbeingRecord)
        .order_by(
            WellbeingRecord.recorded_at.desc()
        )
        .all()
    )

    return records


# ============================================================
# GET WELL-BEING RECORDS FOR ONE SOLDIER
# ============================================================

@router.get(
    "/soldier/{soldier_id}",
    response_model=list[WellbeingResponse]
)
def get_soldier_wellbeing(
    soldier_id: int,
    db: Session = Depends(get_db)
):
    # Check soldier
    soldier = (
        db.query(Soldier)
        .filter(Soldier.id == soldier_id)
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    # Get records
    records = (
        db.query(WellbeingRecord)
        .filter(
            WellbeingRecord.soldier_id == soldier_id
        )
        .order_by(
            WellbeingRecord.recorded_at.desc()
        )
        .all()
    )

    return records


# ============================================================
# GET SINGLE WELL-BEING RECORD
# ============================================================

@router.get(
    "/{record_id}",
    response_model=WellbeingResponse
)
def get_wellbeing_record(
    record_id: int,
    db: Session = Depends(get_db)
):
    record = (
        db.query(WellbeingRecord)
        .filter(
            WellbeingRecord.id == record_id
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="Well-being record not found"
        )

    return record


# ============================================================
# CREATE WELL-BEING RECORD
# ============================================================

@router.post(
    "/",
    response_model=WellbeingResponse,
    status_code=201
)
def create_wellbeing_record(
    data: WellbeingCreate,
    db: Session = Depends(get_db)
):
    # --------------------------------------------------------
    # CHECK SOLDIER
    # --------------------------------------------------------

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id == data.soldier_id
        )
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    # --------------------------------------------------------
    # CURRENT TIME
    # --------------------------------------------------------

    now = datetime.utcnow()

    # --------------------------------------------------------
    # CREATE RECORD
    # --------------------------------------------------------

    record = WellbeingRecord(
        soldier_id=data.soldier_id,

        stress_level=data.stress_level,

        sleep_hours=data.sleep_hours,

        fatigue_level=data.fatigue_level,

        mood_score=data.mood_score,

        heart_rate=data.heart_rate,

        risk_level=data.risk_level,

        notes=data.notes,

        created_at=now,

        recorded_at=now
    )

    # --------------------------------------------------------
    # DATABASE SAVE
    # --------------------------------------------------------

    db.add(record)

    db.commit()

    db.refresh(record)

    return record
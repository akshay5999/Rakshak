from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord


router = APIRouter(
    prefix="/soldiers",
    tags=["Soldiers"]
)


# ============================================================
# SCHEMAS
# ============================================================

class SoldierCreate(BaseModel):
    service_number: str
    name: str
    rank: str
    unit: str
    location: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool = True


class SoldierResponse(BaseModel):
    id: int
    service_number: str
    name: str
    rank: str
    unit: str
    location: str | None = None
    phone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_active: bool
    stress_level: float | None = None

    class Config:
        from_attributes = True


# ============================================================
# GET ALL SOLDIERS
# ============================================================

@router.get("/", response_model=list[SoldierResponse])
def get_soldiers(
    db: Session = Depends(get_db)
):
    soldiers = db.query(Soldier).all()

    result = []

    for soldier in soldiers:

        # Latest wellbeing record
        wellbeing = (
            db.query(WellbeingRecord)
            .filter(
                WellbeingRecord.soldier_id == soldier.id
            )
            .order_by(
                WellbeingRecord.id.desc()
            )
            .first()
        )

        result.append({
            "id": soldier.id,
            "service_number": soldier.service_number,
            "name": soldier.name,
            "rank": soldier.rank,
            "unit": soldier.unit,
            "location": soldier.location,
            "phone": soldier.phone,
            "latitude": soldier.latitude,
            "longitude": soldier.longitude,
            "is_active": soldier.is_active,
            "stress_level": (
                wellbeing.stress_level
                if wellbeing
                else 0
            )
        })

    return result


# ============================================================
# GET SINGLE SOLDIER
# ============================================================

@router.get("/{soldier_id}", response_model=SoldierResponse)
def get_soldier(
    soldier_id: int,
    db: Session = Depends(get_db)
):

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id == soldier_id
        )
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    wellbeing = (
        db.query(WellbeingRecord)
        .filter(
            WellbeingRecord.soldier_id == soldier.id
        )
        .order_by(
            WellbeingRecord.id.desc()
        )
        .first()
    )

    return {
        "id": soldier.id,
        "service_number": soldier.service_number,
        "name": soldier.name,
        "rank": soldier.rank,
        "unit": soldier.unit,
        "location": soldier.location,
        "phone": soldier.phone,
        "latitude": soldier.latitude,
        "longitude": soldier.longitude,
        "is_active": soldier.is_active,
        "stress_level": (
            wellbeing.stress_level
            if wellbeing
            else 0
        )
    }


# ============================================================
# CREATE SOLDIER
# ============================================================

@router.post(
    "/",
    response_model=SoldierResponse
)
def create_soldier(
    soldier_data: SoldierCreate,
    db: Session = Depends(get_db)
):

    # Check duplicate service number
    existing = (
        db.query(Soldier)
        .filter(
            Soldier.service_number
            == soldier_data.service_number
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Service number already exists"
        )

    new_soldier = Soldier(
        service_number=soldier_data.service_number,
        name=soldier_data.name,
        rank=soldier_data.rank,
        unit=soldier_data.unit,
        location=soldier_data.location,
        phone=soldier_data.phone,
        latitude=soldier_data.latitude,
        longitude=soldier_data.longitude,
        is_active=soldier_data.is_active
    )

    db.add(new_soldier)
    db.commit()
    db.refresh(new_soldier)

    return {
        "id": new_soldier.id,
        "service_number": new_soldier.service_number,
        "name": new_soldier.name,
        "rank": new_soldier.rank,
        "unit": new_soldier.unit,
        "location": new_soldier.location,
        "phone": new_soldier.phone,
        "latitude": new_soldier.latitude,
        "longitude": new_soldier.longitude,
        "is_active": new_soldier.is_active,
        "stress_level": 0
    }


# ============================================================
# DELETE SOLDIER
# ============================================================

@router.delete("/{soldier_id}")
def delete_soldier(
    soldier_id: int,
    db: Session = Depends(get_db)
):

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id == soldier_id
        )
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    db.delete(soldier)
    db.commit()

    return {
        "message": "Soldier deleted successfully",
        "soldier_id": soldier_id
    }


# ============================================================
# AI / ML RISK ANALYSIS
# ============================================================

@router.get("/{soldier_id}/risk")
def get_soldier_risk(
    soldier_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Find soldier
    # --------------------------------------------------------

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id == soldier_id
        )
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    # --------------------------------------------------------
    # Get latest wellbeing record
    # --------------------------------------------------------

    wellbeing = (
        db.query(WellbeingRecord)
        .filter(
            WellbeingRecord.soldier_id
            == soldier.id
        )
        .order_by(
            WellbeingRecord.id.desc()
        )
        .first()
    )

    if not wellbeing:
        raise HTTPException(
            status_code=404,
            detail="No wellbeing record found for this soldier"
        )

    # --------------------------------------------------------
    # Prepare ML request
    # --------------------------------------------------------

    payload = {
        "stress": wellbeing.stress_level,
        "fatigue": wellbeing.fatigue_level,
        "sleep": wellbeing.sleep_hours,
        "mood": wellbeing.mood_score,
        "heart_rate": wellbeing.heart_rate
    }

    # --------------------------------------------------------
    # Call ML Service
    # --------------------------------------------------------

    try:

        response = httpx.post(
            "http://127.0.0.1:8001/predict-risk",
            json=payload,
            timeout=10.0
        )

        response.raise_for_status()

        ml_result = response.json()

    except httpx.RequestError as exc:

        raise HTTPException(
            status_code=503,
            detail=f"ML service unavailable: {exc}"
        )

    except httpx.HTTPStatusError as exc:

        raise HTTPException(
            status_code=502,
            detail=f"ML service returned an error: {exc}"
        )

    # --------------------------------------------------------
    # Return combined intelligence
    # --------------------------------------------------------

    return {
        "soldier": {
            "id": soldier.id,
            "name": soldier.name,
            "service_number": soldier.service_number,
            "rank": soldier.rank,
            "unit": soldier.unit,
            "location": soldier.location
        },

        "wellbeing": {
            "stress": wellbeing.stress_level,
            "fatigue": wellbeing.fatigue_level,
            "sleep": wellbeing.sleep_hours,
            "mood": wellbeing.mood_score,
            "heart_rate": wellbeing.heart_rate
        },

        "risk": ml_result
    }
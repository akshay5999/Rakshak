from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.facial_scan import FacialScan


router = APIRouter(
    prefix="/facial-scans",
    tags=["Facial Analysis"]
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class FacialScanCreate(BaseModel):

    soldier_id: int

    forehead_tension: float = Field(
        ge=0,
        le=100
    )

    eye_closure: float = Field(
        ge=0,
        le=100
    )

    left_eye_open: float = Field(
        ge=0,
        le=100
    )

    right_eye_open: float = Field(
        ge=0,
        le=100
    )

    blink_count: int = Field(
        ge=0
    )

    brow_activity: float = Field(
        ge=0,
        le=100
    )

    mouth_activity: float = Field(
        ge=0,
        le=100
    )

    expression_intensity: float = Field(
        ge=0,
        le=100
    )

    facial_signal: float = Field(
        ge=0,
        le=100
    )


# ============================================================
# RESPONSE
# ============================================================

def serialize_scan(scan):

    return {
        "id": scan.id,
        "soldier_id": scan.soldier_id,

        "forehead_tension":
            round(
                scan.forehead_tension,
                2
            ),

        "eye_closure":
            round(
                scan.eye_closure,
                2
            ),

        "left_eye_open":
            round(
                scan.left_eye_open,
                2
            ),

        "right_eye_open":
            round(
                scan.right_eye_open,
                2
            ),

        "blink_count":
            scan.blink_count,

        "brow_activity":
            round(
                scan.brow_activity,
                2
            ),

        "mouth_activity":
            round(
                scan.mouth_activity,
                2
            ),

        "expression_intensity":
            round(
                scan.expression_intensity,
                2
            ),

        "facial_signal":
            round(
                scan.facial_signal,
                2
            ),

        "created_at":
            scan.created_at,
    }


# ============================================================
# SAVE FACIAL SCAN
# ============================================================

@router.post("/")
def create_facial_scan(
    payload: FacialScanCreate,
    db: Session = Depends(get_db)
):

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id ==
            payload.soldier_id
        )
        .first()
    )

    if not soldier:
        raise HTTPException(
            status_code=404,
            detail="Soldier not found"
        )

    scan = FacialScan(
        soldier_id=
            payload.soldier_id,

        forehead_tension=
            payload.forehead_tension,

        eye_closure=
            payload.eye_closure,

        left_eye_open=
            payload.left_eye_open,

        right_eye_open=
            payload.right_eye_open,

        blink_count=
            payload.blink_count,

        brow_activity=
            payload.brow_activity,

        mouth_activity=
            payload.mouth_activity,

        expression_intensity=
            payload.expression_intensity,

        facial_signal=
            payload.facial_signal,
    )

    db.add(scan)
    db.commit()
    db.refresh(scan)

    return {
        "message":
            "Facial scan stored successfully",

        "scan":
            serialize_scan(scan)
    }


# ============================================================
# GET LATEST SCAN
# ============================================================

@router.get(
    "/soldier/{soldier_id}/latest"
)
def get_latest_scan(
    soldier_id: int,
    db: Session = Depends(get_db)
):

    scan = (
        db.query(FacialScan)
        .filter(
            FacialScan.soldier_id ==
            soldier_id
        )
        .order_by(
            FacialScan.created_at.desc()
        )
        .first()
    )

    if not scan:
        return {
            "found": False,
            "scan": None
        }

    return {
        "found": True,
        "scan":
            serialize_scan(scan)
    }


# ============================================================
# GET ALL SCANS FOR SOLDIER
# ============================================================

@router.get(
    "/soldier/{soldier_id}"
)
def get_soldier_scans(
    soldier_id: int,
    db: Session = Depends(get_db)
):

    scans = (
        db.query(FacialScan)
        .filter(
            FacialScan.soldier_id ==
            soldier_id
        )
        .order_by(
            FacialScan.created_at.desc()
        )
        .all()
    )

    return [
        serialize_scan(scan)
        for scan in scans
    ]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models.sos import SOSAlert
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord


router = APIRouter(
    prefix="/sos",
    tags=["SOS Alerts"]
)


ML_SERVICE_URL = "http://127.0.0.1:8001/predict-risk"


# ============================================================
# AI / ML PRIORITY ANALYSIS
# ============================================================

def calculate_sos_priority(risk_score):
    """
    Convert ML risk score into emergency priority.
    """

    if risk_score >= 70:
        return "CRITICAL"

    if risk_score >= 40:
        return "HIGH"

    if risk_score >= 20:
        return "MEDIUM"

    return "LOW"


def get_ml_risk(wellbeing):
    """
    Send latest wellbeing signals to ML service.
    """

    payload = {
        "stress": wellbeing.stress_level,
        "fatigue": wellbeing.fatigue_level,
        "sleep": wellbeing.sleep_hours,
        "mood": wellbeing.mood_score,
        "heart_rate": wellbeing.heart_rate
    }

    try:
        response = httpx.post(
            ML_SERVICE_URL,
            json=payload,
            timeout=5.0
        )

        response.raise_for_status()

        return response.json()

    except Exception as error:
        print(f"ML service error: {error}")
        return None


# ============================================================
# GET ALL SOS ALERTS
# ============================================================

@router.get("/")
def get_sos_alerts(
    db: Session = Depends(get_db)
):

    alerts = (
        db.query(SOSAlert)
        .order_by(SOSAlert.created_at.desc())
        .all()
    )

    result = []

    for alert in alerts:

        # ----------------------------------------------------
        # Find soldier
        # ----------------------------------------------------

        soldier = (
            db.query(Soldier)
            .filter(Soldier.id == alert.soldier_id)
            .first()
        )

        # ----------------------------------------------------
        # Find latest wellbeing record
        # ----------------------------------------------------

        wellbeing = (
            db.query(WellbeingRecord)
            .filter(
                WellbeingRecord.soldier_id == alert.soldier_id
            )
            .order_by(
                WellbeingRecord.id.desc()
            )
            .first()
        )

        ml_result = None
        priority = "UNKNOWN"

        if wellbeing:

            ml_result = get_ml_risk(wellbeing)

            if ml_result:

                risk_score = float(
                    ml_result.get("risk_score", 0)
                )

                priority = calculate_sos_priority(
                    risk_score
                )

        # ----------------------------------------------------
        # Return enriched SOS alert
        # ----------------------------------------------------

        result.append({

            "id": alert.id,

            "soldier_id": alert.soldier_id,

            "soldier": {
                "name": soldier.name if soldier else "Unknown",
                "service_number": (
                    soldier.service_number
                    if soldier
                    else None
                ),
                "rank": (
                    soldier.rank
                    if soldier
                    else None
                ),
                "unit": (
                    soldier.unit
                    if soldier
                    else None
                )
            },

            "alert_type": alert.alert_type,

            "message": alert.message,

            "location": alert.location,

            "latitude": alert.latitude,

            "longitude": alert.longitude,

            "status": alert.status,

            "is_resolved": alert.is_resolved,

            "created_at": alert.created_at,

            # AI / ML intelligence
            "priority": priority,

            "risk": ml_result

        })

    return result


# ============================================================
# CREATE SOS ALERT
# ============================================================

@router.post("/")
def create_sos_alert(
    alert_data: dict,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Check required soldier_id
    # --------------------------------------------------------

    soldier_id = alert_data.get("soldier_id")

    if not soldier_id:

        raise HTTPException(
            status_code=400,
            detail="soldier_id is required"
        )

    # --------------------------------------------------------
    # Verify soldier exists
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Prevent duplicate ACTIVE SOS
    # --------------------------------------------------------

    existing_alert = (
        db.query(SOSAlert)
        .filter(
            SOSAlert.soldier_id == soldier_id,
            SOSAlert.is_resolved == False
        )
        .first()
    )

    if existing_alert:

        return {
            "message": (
                "An active SOS alert already exists "
                "for this soldier."
            ),
            "duplicate": True,
            "alert": existing_alert
        }

    # --------------------------------------------------------
    # Get latest wellbeing
    # --------------------------------------------------------

    wellbeing = (
        db.query(WellbeingRecord)
        .filter(
            WellbeingRecord.soldier_id == soldier_id
        )
        .order_by(
            WellbeingRecord.id.desc()
        )
        .first()
    )

    # --------------------------------------------------------
    # AI / ML risk analysis
    # --------------------------------------------------------

    ml_result = None
    priority = "UNKNOWN"

    if wellbeing:

        ml_result = get_ml_risk(wellbeing)

        if ml_result:

            risk_score = float(
                ml_result.get("risk_score", 0)
            )

            priority = calculate_sos_priority(
                risk_score
            )

    # --------------------------------------------------------
    # Create SOS alert
    # --------------------------------------------------------

    alert = SOSAlert(

        soldier_id=soldier_id,

        message=alert_data.get(
            "message",
            "Emergency assistance required"
        ),

        latitude=alert_data.get("latitude"),

        longitude=alert_data.get("longitude"),

        location=alert_data.get("location"),

        alert_type=alert_data.get(
            "alert_type",
            "EMERGENCY"
        ),

        status="ACTIVE",

        is_resolved=False
    )

    # --------------------------------------------------------
    # Save to PostgreSQL
    # --------------------------------------------------------

    db.add(alert)

    db.commit()

    db.refresh(alert)

    # --------------------------------------------------------
    # AI recommendation
    # --------------------------------------------------------

    if priority == "CRITICAL":

        response_action = (
            "Immediate command intervention required."
        )

    elif priority == "HIGH":

        response_action = (
            "Urgent personnel review recommended."
        )

    elif priority == "MEDIUM":

        response_action = (
            "Monitor soldier and initiate response protocol."
        )

    elif priority == "LOW":

        response_action = (
            "Continue monitoring while processing SOS."
        )

    else:

        response_action = (
            "ML analysis unavailable. Manual assessment required."
        )

    # --------------------------------------------------------
    # Final response
    # --------------------------------------------------------

    return {

        "message": "SOS alert activated successfully.",

        "duplicate": False,

        "alert": {

            "id": alert.id,

            "soldier_id": alert.soldier_id,

            "soldier_name": soldier.name,

            "service_number": soldier.service_number,

            "rank": soldier.rank,

            "unit": soldier.unit,

            "alert_type": alert.alert_type,

            "message": alert.message,

            "location": alert.location,

            "latitude": alert.latitude,

            "longitude": alert.longitude,

            "status": alert.status,

            "is_resolved": alert.is_resolved,

            "created_at": alert.created_at,

            "priority": priority,

            "risk": ml_result,

            "recommended_action": response_action
        }
    }


# ============================================================
# RESOLVE SOS ALERT
# ============================================================

@router.patch("/{alert_id}/resolve")
def resolve_sos_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):

    alert = (
        db.query(SOSAlert)
        .filter(
            SOSAlert.id == alert_id
        )
        .first()
    )

    if not alert:

        raise HTTPException(
            status_code=404,
            detail="SOS alert not found"
        )

    # --------------------------------------------------------
    # Already resolved
    # --------------------------------------------------------

    if alert.is_resolved:

        return {

            "message": "SOS alert is already resolved.",

            "alert": alert
        }

    # --------------------------------------------------------
    # Resolve
    # --------------------------------------------------------

    alert.is_resolved = True

    alert.status = "RESOLVED"

    db.commit()

    db.refresh(alert)

    return {

        "message": "SOS alert resolved successfully.",

        "alert": alert
    }
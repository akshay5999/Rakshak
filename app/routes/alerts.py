from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord
from app.models.sos import SOSAlert

router = APIRouter(
    prefix="/alerts",
    tags=["Intelligent Alerts"]
)


def get_latest_wellbeing(db: Session, soldier_id: int):
    return (
        db.query(WellbeingRecord)
        .filter(WellbeingRecord.soldier_id == soldier_id)
        .order_by(WellbeingRecord.recorded_at.desc())
        .first()
    )


@router.get("/")
def get_intelligent_alerts(
    db: Session = Depends(get_db)
):
    soldiers = db.query(Soldier).all()

    alerts = []

    for soldier in soldiers:

        wellbeing = get_latest_wellbeing(
            db,
            soldier.id
        )

        active_sos = (
            db.query(SOSAlert)
            .filter(
                SOSAlert.soldier_id == soldier.id,
                SOSAlert.is_resolved == False
            )
            .first()
        )

        stress = float(
            wellbeing.stress_level
            if wellbeing
            else soldier.stress_level or 0
        )

        fatigue = float(
            wellbeing.fatigue_level
            if wellbeing
            else 0
        )

        sleep = float(
            wellbeing.sleep_hours
            if wellbeing
            else 0
        )

        mood = float(
            wellbeing.mood_score
            if wellbeing
            else 0
        )

        # --------------------------------------------------
        # CRITICAL — ACTIVE SOS
        # --------------------------------------------------

        if active_sos:

            alerts.append({
                "id": f"SOS-{active_sos.id}",
                "type": "SOS",
                "severity": "CRITICAL",
                "title": "Active SOS Alert",
                "message": (
                    f"{soldier.name} has activated "
                    "an emergency SOS."
                ),
                "soldier_id": soldier.id,
                "soldier_name": soldier.name,
                "service_number": soldier.service_number,
                "location": (
                    active_sos.location
                    or soldier.location
                    or "Unknown"
                ),
                "action": "Immediate response required",
            })

        # --------------------------------------------------
        # HIGH STRESS
        # --------------------------------------------------

        if stress >= 70:

            alerts.append({
                "id": f"STRESS-{soldier.id}",
                "type": "WELLBEING",
                "severity": "HIGH",
                "title": "High Stress Detected",
                "message": (
                    f"{soldier.name} is showing "
                    f"high stress ({stress:.0f}%)."
                ),
                "soldier_id": soldier.id,
                "soldier_name": soldier.name,
                "service_number": soldier.service_number,
                "location": soldier.location,
                "action": "Welfare follow-up recommended",
            })

        # --------------------------------------------------
        # HIGH FATIGUE
        # --------------------------------------------------

        if fatigue >= 70:

            alerts.append({
                "id": f"FATIGUE-{soldier.id}",
                "type": "WELLBEING",
                "severity": "HIGH",
                "title": "High Fatigue Detected",
                "message": (
                    f"{soldier.name} is showing "
                    f"high fatigue ({fatigue:.0f}%)."
                ),
                "soldier_id": soldier.id,
                "soldier_name": soldier.name,
                "service_number": soldier.service_number,
                "location": soldier.location,
                "action": "Rest and welfare assessment recommended",
            })

        # --------------------------------------------------
        # LOW SLEEP
        # --------------------------------------------------

        if sleep > 0 and sleep < 5:

            alerts.append({
                "id": f"SLEEP-{soldier.id}",
                "type": "WELLBEING",
                "severity": "MODERATE",
                "title": "Low Sleep Detected",
                "message": (
                    f"{soldier.name} recorded only "
                    f"{sleep:.1f} hours of sleep."
                ),
                "soldier_id": soldier.id,
                "soldier_name": soldier.name,
                "service_number": soldier.service_number,
                "location": soldier.location,
                "action": "Continue sleep and fatigue monitoring",
            })

        # --------------------------------------------------
        # LOW MOOD
        # --------------------------------------------------

        if mood > 0 and mood < 40:

            alerts.append({
                "id": f"MOOD-{soldier.id}",
                "type": "WELLBEING",
                "severity": "MODERATE",
                "title": "Low Mood Indicator",
                "message": (
                    f"{soldier.name} has a low "
                    f"mood score ({mood:.0f}/100)."
                ),
                "soldier_id": soldier.id,
                "soldier_name": soldier.name,
                "service_number": soldier.service_number,
                "location": soldier.location,
                "action": "Well-being check recommended",
            })

    # ------------------------------------------------------
    # SORT BY SEVERITY
    # ------------------------------------------------------

    severity_order = {
        "CRITICAL": 1,
        "HIGH": 2,
        "MODERATE": 3,
        "INFO": 4,
    }

    alerts.sort(
        key=lambda alert: severity_order.get(
            alert["severity"],
            5
        )
    )

    return {
        "total": len(alerts),
        "critical": sum(
            1 for a in alerts
            if a["severity"] == "CRITICAL"
        ),
        "high": sum(
            1 for a in alerts
            if a["severity"] == "HIGH"
        ),
        "moderate": sum(
            1 for a in alerts
            if a["severity"] == "MODERATE"
        ),
        "alerts": alerts,
    }
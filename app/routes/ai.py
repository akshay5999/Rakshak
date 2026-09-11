from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord
from app.models.sos import SOSAlert

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"]
)


def latest_wellbeing(db: Session, soldier_id: int):
    return (
        db.query(WellbeingRecord)
        .filter(WellbeingRecord.soldier_id == soldier_id)
        .order_by(WellbeingRecord.recorded_at.desc())
        .first()
    )


def soldier_snapshot(db: Session):
    soldiers = db.query(Soldier).all()

    result = []

    for soldier in soldiers:

        wb = latest_wellbeing(db, soldier.id)

        stress = float(
            wb.stress_level
            if wb
            else getattr(soldier, "stress_level", 0) or 0
        )

        fatigue = float(
            wb.fatigue_level
            if wb
            else 0
        )

        sleep = float(
            wb.sleep_hours
            if wb
            else 0
        )

        mood = float(
            wb.mood_score
            if wb
            else 0
        )

        heart_rate = (
            float(wb.heart_rate)
            if wb and wb.heart_rate is not None
            else None
        )

        # Simple explainable risk model
        risk_score = (
            stress * 0.45
            + fatigue * 0.25
            + max(0, 8 - sleep) * 5
            + max(0, 60 - mood) * 0.25
        )

        risk_score = round(
            min(max(risk_score, 0), 100),
            1
        )

        safety_score = round(
            100 - risk_score,
            1
        )

        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        active_sos = (
            db.query(SOSAlert)
            .filter(
                SOSAlert.soldier_id == soldier.id,
                SOSAlert.is_resolved == False
            )
            .first()
        )

        result.append({
            "id": soldier.id,
            "name": soldier.name,
            "service_number": soldier.service_number,
            "rank": soldier.rank,
            "unit": soldier.unit,
            "location": soldier.location,
            "is_active": soldier.is_active,

            "stress": round(stress, 1),
            "fatigue": round(fatigue, 1),
            "sleep": round(sleep, 1),
            "mood": round(mood, 1),
            "heart_rate": heart_rate,

            "risk_score": risk_score,
            "safety_score": safety_score,
            "risk_level": risk_level,

            "active_sos": bool(active_sos),
        })

    return result


@router.get("/overview")
def ai_overview(
    db: Session = Depends(get_db)
):
    personnel = soldier_snapshot(db)

    total = len(personnel)

    high = [
        s for s in personnel
        if s["risk_level"] == "HIGH"
    ]

    moderate = [
        s for s in personnel
        if s["risk_level"] == "MODERATE"
    ]

    low = [
        s for s in personnel
        if s["risk_level"] == "LOW"
    ]

    active_sos = [
        s for s in personnel
        if s["active_sos"]
    ]

    highest = (
        max(
            personnel,
            key=lambda s: s["risk_score"]
        )
        if personnel
        else None
    )

    return {
        "total_personnel": total,
        "high_risk": len(high),
        "moderate_risk": len(moderate),
        "low_risk": len(low),
        "active_sos": len(active_sos),
        "highest_risk_soldier": highest,
        "personnel": personnel,
    }


@router.post("/ask")
def ask_ai(
    payload: dict,
    db: Session = Depends(get_db)
):
    question = str(
        payload.get("question", "")
    ).strip()

    if not question:
        return {
            "answer": "Please enter a question.",
            "type": "INFO",
            "data": []
        }

    q = question.lower()

    personnel = soldier_snapshot(db)

    total = len(personnel)

    high = [
        s for s in personnel
        if s["risk_level"] == "HIGH"
    ]

    moderate = [
        s for s in personnel
        if s["risk_level"] == "MODERATE"
    ]

    low = [
        s for s in personnel
        if s["risk_level"] == "LOW"
    ]

    sos = [
        s for s in personnel
        if s["active_sos"]
    ]

    # --------------------------------------------------------
    # HIGHEST RISK
    # --------------------------------------------------------

    if (
        "highest risk" in q
        or "highest-risk" in q
        or "most risk" in q
        or "maximum risk" in q
        or "most dangerous" in q
    ):

        if not personnel:
            return {
                "answer": "No personnel data is currently available.",
                "type": "INFO",
                "data": []
            }

        soldier = max(
            personnel,
            key=lambda s: s["risk_score"]
        )

        return {
            "answer": (
                f"{soldier['name']} ({soldier['service_number']}) "
                f"is currently the highest-risk personnel record "
                f"with a risk score of {soldier['risk_score']}/100 "
                f"and a safety score of "
                f"{soldier['safety_score']}/100."
            ),
            "type": "HIGH_RISK",
            "data": [soldier]
        }

    # --------------------------------------------------------
    # ACTIVE SOS
    # --------------------------------------------------------

    if (
        "sos" in q
        or "emergency" in q
        or "emergencies" in q
        or "active alert" in q
    ):

        if not sos:
            return {
                "answer": "There are currently no active SOS emergencies.",
                "type": "SAFE",
                "data": []
            }

        names = ", ".join(
            f"{s['name']} ({s['location'] or 'Unknown location'})"
            for s in sos
        )

        return {
            "answer": (
                f"There are {len(sos)} active SOS emergency alert(s). "
                f"Personnel requiring immediate response: {names}."
            ),
            "type": "CRITICAL",
            "data": sos
        }

    # --------------------------------------------------------
    # HIGH RISK
    # --------------------------------------------------------

    if (
        "high risk" in q
        or "high-risk" in q
        or "immediate attention" in q
        or "need attention" in q
        or "critical personnel" in q
    ):

        if not high:
            return {
                "answer": "No personnel are currently classified as high risk.",
                "type": "SAFE",
                "data": []
            }

        names = ", ".join(
            f"{s['name']} ({s['risk_score']}/100)"
            for s in high
        )

        return {
            "answer": (
                f"{len(high)} personnel are currently at high risk: "
                f"{names}. Command-level welfare review is recommended."
            ),
            "type": "HIGH_RISK",
            "data": high
        }

    # --------------------------------------------------------
    # MODERATE
    # --------------------------------------------------------

    if (
        "moderate" in q
        or "medium risk" in q
    ):

        names = ", ".join(
            s["name"]
            for s in moderate
        )

        return {
            "answer": (
                f"There are {len(moderate)} personnel in the moderate-risk "
                f"category: {names or 'none'}."
            ),
            "type": "MODERATE",
            "data": moderate
        }

    # --------------------------------------------------------
    # WELLBEING
    # --------------------------------------------------------

    if (
        "wellbeing" in q
        or "well-being" in q
        or "well being" in q
        or "health" in q
        or "stress" in q
        or "fatigue" in q
        or "sleep" in q
        or "mood" in q
    ):

        if not personnel:
            return {
                "answer": "No well-being data is currently available.",
                "type": "INFO",
                "data": []
            }

        avg_stress = round(
            sum(s["stress"] for s in personnel) / total,
            1
        )

        avg_fatigue = round(
            sum(s["fatigue"] for s in personnel) / total,
            1
        )

        sleep_values = [
            s["sleep"]
            for s in personnel
            if s["sleep"] > 0
        ]

        avg_sleep = round(
            sum(sleep_values) / len(sleep_values),
            1
        ) if sleep_values else 0

        avg_mood = round(
            sum(s["mood"] for s in personnel) / total,
            1
        )

        return {
            "answer": (
                f"Current unit well-being indicators: "
                f"average stress {avg_stress}%, "
                f"average fatigue {avg_fatigue}%, "
                f"average sleep {avg_sleep} hours, "
                f"and average mood {avg_mood}/100."
            ),
            "type": "WELLBEING",
            "data": personnel
        }

    # --------------------------------------------------------
    # SPECIFIC SOLDIER
    # --------------------------------------------------------

    matched = None

    for soldier in personnel:

        name = soldier["name"].lower()
        service = soldier["service_number"].lower()

        if name in q or service in q:
            matched = soldier
            break

    if matched:

        return {
            "answer": (
                f"{matched['name']} ({matched['service_number']}) "
                f"is currently classified as {matched['risk_level']} risk. "
                f"Risk score: {matched['risk_score']}/100. "
                f"Safety score: {matched['safety_score']}/100. "
                f"Stress: {matched['stress']}%, "
                f"Fatigue: {matched['fatigue']}%, "
                f"Sleep: {matched['sleep']} hours, "
                f"Mood: {matched['mood']}/100. "
                f"Location: {matched['location'] or 'Unknown'}."
            ),
            "type": matched["risk_level"],
            "data": [matched]
        }

    # --------------------------------------------------------
    # TOTAL PERSONNEL
    # --------------------------------------------------------

    if (
        "how many" in q
        or "total soldiers" in q
        or "total personnel" in q
        or "personnel count" in q
        or "soldiers" == q
    ):

        return {
            "answer": (
                f"RakshakCare is currently monitoring "
                f"{total} personnel: "
                f"{len(high)} high risk, "
                f"{len(moderate)} moderate risk, "
                f"and {len(low)} low risk."
            ),
            "type": "OVERVIEW",
            "data": personnel
        }

    # --------------------------------------------------------
    # LOCATION
    # --------------------------------------------------------

    if (
        "location" in q
        or "where" in q
    ):

        location_data = [
            {
                "name": s["name"],
                "location": s["location"],
                "risk_level": s["risk_level"],
                "risk_score": s["risk_score"]
            }
            for s in personnel
        ]

        return {
            "answer": (
                "Current monitored personnel locations are "
                + ", ".join(
                    f"{s['name']} — {s['location'] or 'Unknown'}"
                    for s in personnel
                )
                + "."
            ),
            "type": "LOCATION",
            "data": location_data
        }

    # --------------------------------------------------------
    # DEFAULT INTELLIGENCE RESPONSE
    # --------------------------------------------------------

    highest = (
        max(
            personnel,
            key=lambda s: s["risk_score"]
        )
        if personnel
        else None
    )

    if highest:

        return {
            "answer": (
                f"I can analyze RakshakCare personnel data. "
                f"Currently {total} personnel are monitored, "
                f"{len(high)} are high risk, "
                f"{len(moderate)} are moderate risk, "
                f"{len(sos)} have active SOS alerts. "
                f"The highest current risk is "
                f"{highest['name']} with "
                f"{highest['risk_score']}/100."
            ),
            "type": "OVERVIEW",
            "data": personnel
        }

    return {
        "answer": (
            "RakshakCare currently has no personnel records "
            "available for analysis."
        ),
        "type": "INFO",
        "data": []
    }
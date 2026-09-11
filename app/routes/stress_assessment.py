from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.facial_scan import FacialScan
from app.models.wellbeing import WellbeingRecord


router = APIRouter(
    prefix="/stress-assessment",
    tags=["Stress Assessment"]
)


# ============================================================
# REQUEST
# ============================================================

class StressAssessmentRequest(BaseModel):

    soldier_id: int

    facial_scan_id: int

    answers: list[int] = Field(
        min_length=12,
        max_length=12
    )

    sleep_hours: float = Field(
        ge=0,
        le=24
    )

    fatigue_level: float = Field(
        ge=0,
        le=100
    )

    mood_score: float = Field(
        ge=0,
        le=100
    )

    heart_rate: float | None = Field(
        default=None,
        ge=30,
        le=250
    )


# ============================================================
# RISK
# ============================================================

def get_risk_level(score):

    if score >= 70:
        return "HIGH"

    if score >= 40:
        return "MODERATE"

    return "LOW"


def get_recommendation(
    score,
    sleep_hours,
    fatigue,
    mood
):

    if score >= 70:

        return (
            "Elevated welfare indicators detected. "
            "A confidential welfare review and "
            "appropriate rest/support are recommended."
        )

    if score >= 40:

        if sleep_hours < 5:

            return (
                "Sleep duration is low. "
                "Prioritize recovery and continue "
                "well-being monitoring."
            )

        if fatigue >= 70:

            return (
                "Fatigue indicators are elevated. "
                "Consider workload review and recovery time."
            )

        return (
            "Moderate stress indicators detected. "
            "Continue monitoring and repeat the "
            "well-being check after recovery."
        )

    return (
        "Current indicators are within the monitored "
        "range. Continue routine well-being checks."
    )


# ============================================================
# COMPLETE ASSESSMENT
# ============================================================

@router.post("/complete")
def complete_assessment(
    payload: StressAssessmentRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # SOLDIER
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # FACIAL SCAN
    # --------------------------------------------------------

    facial_scan = (
        db.query(FacialScan)
        .filter(
            FacialScan.id ==
            payload.facial_scan_id,

            FacialScan.soldier_id ==
            payload.soldier_id
        )
        .first()
    )

    if not facial_scan:

        raise HTTPException(
            status_code=404,
            detail="Facial scan not found for this soldier"
        )

    # --------------------------------------------------------
    # QUESTIONNAIRE
    # --------------------------------------------------------

    answers = [
        max(
            0,
            min(
                4,
                int(answer)
            )
        )
        for answer in payload.answers
    ]

    questionnaire_raw = sum(
        answers
    )

    questionnaire_score = (
        questionnaire_raw /
        48
    ) * 100

    # --------------------------------------------------------
    # SLEEP RISK
    # --------------------------------------------------------

    sleep_risk = max(
        0,
        min(
            100,
            ((8 - payload.sleep_hours) / 8)
            * 100
        )
    )

    # --------------------------------------------------------
    # MOOD RISK
    # --------------------------------------------------------

    mood_risk = (
        100 -
        payload.mood_score
    )

    # --------------------------------------------------------
    # FACIAL SIGNAL
    # --------------------------------------------------------

    facial_score = float(
        facial_scan.facial_signal
    )

    # --------------------------------------------------------
    # FINAL FUSION
    #
    # Questionnaire: 50%
    # Facial signal: 20%
    # Sleep risk:     10%
    # Fatigue:        10%
    # Mood risk:      10%
    # --------------------------------------------------------

    final_score = (
        questionnaire_score * 0.50
        +
        facial_score * 0.20
        +
        sleep_risk * 0.10
        +
        payload.fatigue_level * 0.10
        +
        mood_risk * 0.10
    )

    final_score = round(
        max(
            0,
            min(
                100,
                final_score
            )
        ),
        1
    )

    risk_level = get_risk_level(
        final_score
    )

    # --------------------------------------------------------
    # RECOMMENDATION
    # --------------------------------------------------------

    recommendation = get_recommendation(
        final_score,
        payload.sleep_hours,
        payload.fatigue_level,
        payload.mood_score
    )

    # --------------------------------------------------------
    # SAVE WELLBEING RECORD
    # --------------------------------------------------------

    record = WellbeingRecord(

        soldier_id=
            payload.soldier_id,

        stress_level=
            final_score,

        sleep_hours=
            payload.sleep_hours,

        fatigue_level=
            payload.fatigue_level,

        mood_score=
            payload.mood_score,

        heart_rate=
            payload.heart_rate,

        notes=(
            "AI-assisted multi-signal stress "
            "assessment. "
            f"Facial signal: {facial_score:.1f}. "
            f"Questionnaire score: "
            f"{questionnaire_score:.1f}. "
            f"Final risk: {risk_level}. "
            f"Recommendation: {recommendation}"
        )
    )

    db.add(record)

    db.commit()

    db.refresh(record)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "message":
            "Stress assessment completed successfully",

        "soldier": {
            "id":
                soldier.id,

            "name":
                soldier.name,

            "service_number":
                soldier.service_number,
        },

        "facial_analysis": {

            "scan_id":
                facial_scan.id,

            "facial_signal":
                round(
                    facial_score,
                    1
                ),

            "forehead_tension":
                round(
                    facial_scan.forehead_tension,
                    1
                ),

            "eye_closure":
                round(
                    facial_scan.eye_closure,
                    1
                ),

            "blink_count":
                facial_scan.blink_count,
        },

        "assessment": {

            "questionnaire_score":
                round(
                    questionnaire_score,
                    1
                ),

            "sleep_hours":
                payload.sleep_hours,

            "fatigue_level":
                payload.fatigue_level,

            "mood_score":
                payload.mood_score,

            "heart_rate":
                payload.heart_rate,
        },

        "final_result": {

            "stress_score":
                final_score,

            "risk_level":
                risk_level,

            "recommendation":
                recommendation,
        },

        "wellbeing_record_id":
            record.id,
    }
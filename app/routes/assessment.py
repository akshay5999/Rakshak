from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord


router = APIRouter(
    prefix="/assessment",
    tags=["Stress Assessment"]
)


# ============================================================
# REQUEST SCHEMA
# ============================================================

class AssessmentRequest(BaseModel):

    soldier_id: int

    answers: List[int] = Field(
        ...,
        min_length=12,
        max_length=12
    )


# ============================================================
# QUESTIONS
# ============================================================

QUESTIONS = [
    {
        "id": 1,
        "category": "MENTAL STRESS",
        "question": "How would you rate your overall stress during the recent duty period?"
    },
    {
        "id": 2,
        "category": "SLEEP",
        "question": "How many hours do you usually sleep in a 24-hour period?"
    },
    {
        "id": 3,
        "category": "FATIGUE",
        "question": "How physically tired have you felt during recent duty?"
    },
    {
        "id": 4,
        "category": "WORKLOAD",
        "question": "How difficult has your current workload felt?"
    },
    {
        "id": 5,
        "category": "EMOTIONAL STATE",
        "question": "How often have you felt irritated, restless or emotionally tense?"
    },
    {
        "id": 6,
        "category": "FOCUS",
        "question": "How difficult has it been to concentrate on your duties?"
    },
    {
        "id": 7,
        "category": "RECOVERY",
        "question": "How well do you feel you recover after duty or rest?"
    },
    {
        "id": 8,
        "category": "SLEEP QUALITY",
        "question": "How would you rate the quality of your recent sleep?"
    },
    {
        "id": 9,
        "category": "ANXIETY",
        "question": "How frequently have you felt worried or under pressure?"
    },
    {
        "id": 10,
        "category": "SUPPORT",
        "question": "How supported and connected do you currently feel?"
    },
    {
        "id": 11,
        "category": "PHYSICAL FATIGUE",
        "question": "How exhausted do you feel after completing your duties?"
    },
    {
        "id": 12,
        "category": "OVERLOAD",
        "question": "How often have you felt that your responsibilities are becoming overwhelming?"
    }
]


# ============================================================
# GET QUESTIONS
# ============================================================

@router.get("/questions")
def get_questions():

    return {
        "total_questions": len(QUESTIONS),
        "questions": QUESTIONS,
        "answer_scale": {
            "0": "Very Low / Excellent",
            "1": "Low / Good",
            "2": "Moderate",
            "3": "High / Poor",
            "4": "Very High / Very Poor"
        }
    }


# ============================================================
# SCORING ENGINE
# ============================================================

def calculate_assessment(answers):

    # --------------------------------------------------------
    # Safety validation
    # --------------------------------------------------------

    if len(answers) != 12:
        raise ValueError(
            "Exactly 12 answers are required."
        )

    if any(
        answer < 0 or answer > 4
        for answer in answers
    ):
        raise ValueError(
            "Every answer must be between 0 and 4."
        )

    # --------------------------------------------------------
    # Convert sleep answer into hours
    #
    # 0 = 7-9 hours
    # 1 = 6-7 hours
    # 2 = 5-6 hours
    # 3 = 4-5 hours
    # 4 = less than 4 hours
    # --------------------------------------------------------

    sleep_map = {
        0: 8.0,
        1: 6.5,
        2: 5.5,
        3: 4.5,
        4: 3.5
    }

    sleep_hours = sleep_map[answers[1]]

    # --------------------------------------------------------
    # STRESS
    #
    # q1 overall stress
    # q4 workload
    # q5 emotional tension
    # q9 pressure
    # q12 overload
    # --------------------------------------------------------

    stress_average = (
        answers[0]
        + answers[3]
        + answers[4]
        + answers[8]
        + answers[11]
    ) / 5

    stress = round(
        stress_average * 25,
        1
    )

    # --------------------------------------------------------
    # FATIGUE
    #
    # q3 physical tiredness
    # q7 poor recovery
    # q11 physical exhaustion
    # --------------------------------------------------------

    recovery_problem = answers[6]

    fatigue_average = (
        answers[2]
        + recovery_problem
        + answers[10]
    ) / 3

    fatigue = round(
        fatigue_average * 25,
        1
    )

    # --------------------------------------------------------
    # MOOD
    #
    # Higher stress/focus/support problems = lower mood
    # --------------------------------------------------------

    emotional_load = (
        answers[4]
        + answers[5]
        + answers[8]
        + answers[11]
    ) / 4

    support_problem = answers[9]

    mood = 100 - (
        emotional_load * 17
        + support_problem * 8
    )

    mood = round(
        max(0, min(100, mood)),
        1
    )

    # --------------------------------------------------------
    # SLEEP QUALITY
    # --------------------------------------------------------

    sleep_duration_score = (
        min(sleep_hours / 8, 1) * 100
    )

    sleep_quality_score = (
        100 - answers[7] * 20
    )

    sleep_score = (
        sleep_duration_score * 0.6
        + sleep_quality_score * 0.4
    )

    sleep_stress = 100 - sleep_score

    # --------------------------------------------------------
    # RISK SCORE
    # --------------------------------------------------------

    risk_score = (
        stress * 0.45
        + fatigue * 0.25
        + sleep_stress * 0.15
        + (100 - mood) * 0.15
    )

    risk_score = round(
        max(0, min(100, risk_score)),
        1
    )

    # --------------------------------------------------------
    # SAFETY SCORE
    # --------------------------------------------------------

    safety_score = round(
        max(0, min(100, 100 - risk_score)),
        1
    )

    # --------------------------------------------------------
    # RISK LEVEL
    # --------------------------------------------------------

    if risk_score >= 75:

        risk_level = "CRITICAL"

        recommendation = (
            "Immediate command and welfare intervention "
            "recommended. Conduct a direct personnel check "
            "and review current duty load."
        )

    elif risk_score >= 55:

        risk_level = "HIGH"

        recommendation = (
            "Enhanced monitoring recommended. "
            "Welfare follow-up and workload review should "
            "be considered."
        )

    elif risk_score >= 30:

        risk_level = "MODERATE"

        recommendation = (
            "Continue enhanced monitoring. Encourage "
            "adequate rest, recovery and welfare support."
        )

    else:

        risk_level = "LOW"

        recommendation = (
            "Current indicators appear stable. "
            "Continue routine monitoring and preventive "
            "well-being support."
        )

    # --------------------------------------------------------
    # ADDITIONAL INSIGHTS
    # --------------------------------------------------------

    insights = []

    if stress >= 70:
        insights.append(
            "High psychological stress indicator detected."
        )

    if fatigue >= 70:
        insights.append(
            "High fatigue indicator detected."
        )

    if sleep_hours < 5:
        insights.append(
            "Insufficient sleep duration detected."
        )

    if mood < 40:
        insights.append(
            "Low mood indicator detected."
        )

    if answers[3] >= 3:
        insights.append(
            "High workload pressure reported."
        )

    if answers[11] >= 3:
        insights.append(
            "High responsibility overload reported."
        )

    if not insights:
        insights.append(
            "No major high-severity indicators detected."
        )

    return {
        "stress": stress,
        "fatigue": fatigue,
        "sleep_hours": sleep_hours,
        "mood": mood,
        "risk_score": risk_score,
        "safety_score": safety_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "insights": insights
    }


# ============================================================
# SUBMIT ASSESSMENT
# ============================================================

@router.post("/submit")
def submit_assessment(
    payload: AssessmentRequest,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # FIND SOLDIER
    # --------------------------------------------------------

    soldier = (
        db.query(Soldier)
        .filter(
            Soldier.id == payload.soldier_id
        )
        .first()
    )

    if not soldier:

        raise HTTPException(
            status_code=404,
            detail="Soldier not found."
        )

    # --------------------------------------------------------
    # CALCULATE
    # --------------------------------------------------------

    try:

        result = calculate_assessment(
            payload.answers
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    # --------------------------------------------------------
    # SAVE TO POSTGRESQL
    # --------------------------------------------------------

    record = WellbeingRecord(

        soldier_id=soldier.id,

        stress_level=result["stress"],

        sleep_hours=result["sleep_hours"],

        fatigue_level=result["fatigue"],

        mood_score=result["mood"],

        heart_rate=None,

        notes=(
            "Stress assessment submitted. "
            f"Risk: {result['risk_level']}. "
            f"Risk Score: {result['risk_score']}/100. "
            f"Safety Score: {result['safety_score']}/100. "
            + " ".join(result["insights"])
        )
    )

    db.add(record)

    db.commit()

    db.refresh(record)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {

        "success": True,

        "message": (
            "Assessment completed and stored successfully."
        ),

        "assessment_id": record.id,

        "soldier": {
            "id": soldier.id,
            "name": soldier.name,
            "service_number": soldier.service_number,
            "rank": soldier.rank,
            "unit": soldier.unit,
            "location": soldier.location
        },

        "result": result,

        "database": {
            "record_id": record.id,
            "recorded_at": record.recorded_at
        }
    }
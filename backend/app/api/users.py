"""
Users API
Profile management, BMI/RFM recalculation on update,
condition management, and user statistics summary.
"""
import math
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exercise import WorkoutLog, Reward, SafetyAuditLog
from app.schemas.schemas import UserOut, UserUpdate

router = APIRouter()


class UserStatsOut(BaseModel):
    total_sessions:    int
    completed:         int
    completion_rate:   float
    total_calories:    int
    total_duration:    int
    avg_effort:        float
    total_points:      int
    streak:            int
    badges_earned:     int
    active_conditions: List[str]
    bmi:               float
    rfm:               float
    bmi_category:      str


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5: return "Underweight"
    if bmi < 25.0: return "Normal"
    if bmi < 30.0: return "Overweight"
    if bmi < 35.0: return "Obese Class I"
    return "Obese Class II+"


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's full profile."""
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update user profile.
    Automatically recalculates BMI and RFM if weight or height changes.
    Automatically adds 'obesity' condition if new BMI > 30.
    """
    if payload.weight_kg is not None:
        current_user.weight_kg = payload.weight_kg
    if payload.height_cm is not None:
        current_user.height_cm = payload.height_cm
    if payload.goal is not None:
        current_user.goal = payload.goal

    # Recalculate BMI and RFM if body measurements changed
    if payload.weight_kg is not None or payload.height_cm is not None:
        w = current_user.weight_kg
        h = current_user.height_cm
        current_user.bmi = round(w / ((h / 100) ** 2), 1)
        g = 12 if current_user.gender == "female" else 0
        rfm = 64 - (20 * (h / 100) / math.sqrt(w / h)) + g
        current_user.rfm = round(max(5.0, min(60.0, rfm)), 1)

        # Auto-manage obesity condition
        conditions = list(current_user.conditions or [])
        if current_user.bmi > 30 and "obesity" not in conditions:
            conditions.append("obesity")
        elif current_user.bmi <= 30 and "obesity" in conditions:
            conditions.remove("obesity")
        current_user.conditions = conditions

    db.commit()
    db.refresh(current_user)
    return current_user


@router.patch("/me/conditions")
def update_conditions(
    conditions: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user's health conditions list. Auto-adds obesity if BMI > 30."""
    valid = {"obesity","hypertension","diabetes","joint-pain","elderly","back-pain"}
    filtered = [c for c in conditions if c in valid]

    # Always enforce obesity flag based on BMI
    if current_user.bmi > 30 and "obesity" not in filtered:
        filtered.append("obesity")

    current_user.conditions = filtered
    db.commit()
    return {"conditions": current_user.conditions, "message": "Conditions updated. Safety rules recalculated."}


@router.get("/me/stats", response_model=UserStatsOut)
def get_my_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return comprehensive workout and health statistics for the current user."""
    logs   = db.query(WorkoutLog).filter(WorkoutLog.user_id == current_user.id).all()
    badges = db.query(Reward).filter(Reward.user_id == current_user.id).count()

    completed       = [l for l in logs if l.completed]
    total_calories  = sum(l.calories_burned or 0 for l in logs)
    total_duration  = sum(l.duration_mins or 0 for l in logs)
    avg_effort      = round(sum(l.perceived_effort or 0 for l in logs) / max(len(logs), 1), 1)
    completion_rate = round(len(completed) / max(len(logs), 1) * 100, 1)

    return UserStatsOut(
        total_sessions=len(logs),
        completed=len(completed),
        completion_rate=completion_rate,
        total_calories=total_calories,
        total_duration=total_duration,
        avg_effort=avg_effort,
        total_points=current_user.points or 0,
        streak=current_user.streak or 0,
        badges_earned=badges,
        active_conditions=current_user.conditions or [],
        bmi=current_user.bmi,
        rfm=current_user.rfm,
        bmi_category=_bmi_category(current_user.bmi),
    )


@router.get("/me/safety-audit")
def get_safety_audit(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the user's safety audit log — all rule firings and HR alerts."""
    audits = (
        db.query(SafetyAuditLog)
        .filter(SafetyAuditLog.user_id == current_user.id)
        .order_by(SafetyAuditLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"rule": a.rule_fired, "reason": a.reason, "logged_at": a.logged_at}
        for a in audits
    ]

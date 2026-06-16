"""
Workout Logs API
Handles session logging, streak tracking, calorie calculation,
heart rate safety alerts, and automatic reward evaluation.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exercise import WorkoutLog, Exercise, SafetyAuditLog
from app.schemas.schemas import LogCreate, LogOut

router = APIRouter()


class LogResponse(BaseModel):
    id: int
    exercise_id: int
    logged_at: datetime
    duration_mins: int
    completed: bool
    perceived_effort: int
    heart_rate_avg: Optional[int]
    calories_burned: Optional[int]
    hr_warning: Optional[str] = None
    points_earned: int = 0
    new_streak: int = 0

    class Config:
        from_attributes = True


def _check_heart_rate(user: User, hr: int, exercise_id: int, db: Session) -> Optional[str]:
    """
    Age-based maximum heart rate check (220 - age formula).
    Logs to safety_audit_logs and returns warning string if dangerous.
    """
    max_hr       = 220 - user.age
    danger_zone  = int(max_hr * 0.95)   # 95% of max
    warning_zone = int(max_hr * 0.85)   # 85% of max

    if hr >= max_hr:
        reason = f"Heart rate {hr} bpm EXCEEDED age-based maximum of {max_hr} bpm. STOP exercise immediately."
        audit  = SafetyAuditLog(user_id=user.id, exercise_id=exercise_id, rule_fired="HR-DANGER", reason=reason)
        db.add(audit)
        return f"🚨 DANGER: Your heart rate ({hr} bpm) exceeded your safe maximum ({max_hr} bpm). Stop exercising and rest immediately. Seek medical attention if symptoms persist."

    if hr >= danger_zone:
        reason = f"Heart rate {hr} bpm in danger zone (≥{danger_zone} bpm, 95% of max {max_hr})."
        audit  = SafetyAuditLog(user_id=user.id, exercise_id=exercise_id, rule_fired="HR-ALERT", reason=reason)
        db.add(audit)
        return f"⚠️ WARNING: Heart rate ({hr} bpm) is near your maximum limit ({max_hr} bpm). Reduce intensity immediately."

    if hr >= warning_zone and "hypertension" in (user.conditions or []):
        reason = f"Hypertensive user heart rate {hr} bpm at 85% max during exercise."
        audit  = SafetyAuditLog(user_id=user.id, exercise_id=exercise_id, rule_fired="HR-HYPERTENSION", reason=reason)
        db.add(audit)
        return f"⚠️ CAUTION: Heart rate ({hr} bpm) is elevated. As a hypertensive user, consider reducing intensity."

    return None


def _calculate_streak(user: User, completed: bool) -> int:
    """Update and return new streak value."""
    if not completed:
        return user.streak  # incomplete session doesn't break streak

    today = datetime.utcnow().date()
    if user.last_workout_date:
        last_date = user.last_workout_date.date()
        days_gap  = (today - last_date).days
        if days_gap == 0:
            return user.streak          # already logged today
        elif days_gap == 1:
            return user.streak + 1      # consecutive day
        else:
            return 1                    # streak broken, restart
    return 1                            # first ever workout


def _calculate_points(completed: bool, effort: int, streak: int) -> int:
    """Award points based on completion, effort, and streak bonuses."""
    if not completed:
        return 5   # participation points

    pts = 10                            # base completion
    if effort >= 7:
        pts += 10                       # high effort bonus
    if effort >= 9:
        pts += 5                        # maximum effort bonus
    if streak >= 7:
        pts += 50                       # week streak bonus
    elif streak >= 3:
        pts += 20                       # 3-day streak bonus
    return pts


def _auto_evaluate_badges(user: User, logs: list, db: Session):
    """Automatically evaluate and award new badges after each log."""
    from app.models.exercise import Reward

    ALL_BADGES = [
        {"id": "first",    "name": "First Step",        "pts": 50,
         "check": lambda l, s: sum(1 for x in l if x.completed) >= 1},
        {"id": "streak3",  "name": "On Fire",            "pts": 75,
         "check": lambda l, s: s >= 3},
        {"id": "streak7",  "name": "Week Warrior",       "pts": 150,
         "check": lambda l, s: s >= 7},
        {"id": "w5",       "name": "Consistent",         "pts": 100,
         "check": lambda l, s: sum(1 for x in l if x.completed) >= 5},
        {"id": "w10",      "name": "Dedicated",          "pts": 200,
         "check": lambda l, s: sum(1 for x in l if x.completed) >= 10},
        {"id": "effort",   "name": "Intensity Climber",  "pts": 100,
         "check": lambda l, s: sum(1 for x in l if (x.perceived_effort or 0) >= 8) >= 3},
        {"id": "safe",     "name": "Safety First",       "pts": 25,
         "check": lambda l, s: True},
        {"id": "calorie",  "name": "Calorie Crusher",    "pts": 150,
         "check": lambda l, s: sum(x.calories_burned or 0 for x in l) >= 2000},
    ]

    existing_ids = {
        r.badge_id for r in db.query(Reward).filter(Reward.user_id == user.id).all()
    }

    for badge in ALL_BADGES:
        if badge["id"] not in existing_ids:
            try:
                if badge["check"](logs, user.streak):
                    reward = Reward(
                        user_id=user.id, badge_id=badge["id"],
                        badge_name=badge["name"], points=badge["pts"],
                        earned_at=datetime.utcnow()
                    )
                    db.add(reward)
            except Exception:
                pass


@router.post("/", response_model=LogResponse, status_code=201)
def create_log(
    payload: LogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a workout session log.
    Handles: calorie calculation, streak tracking, heart rate safety check,
    points award, automatic badge evaluation.
    """
    # Validate exercise exists
    ex = db.query(Exercise).filter(Exercise.id == payload.exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    # Calculate calories: MET × weight × (duration / 60)
    calories = round(ex.met_value * current_user.weight_kg * (payload.duration_mins / 60))

    # Heart rate safety check
    hr_warning = None
    if payload.heart_rate_avg:
        hr_warning = _check_heart_rate(current_user, payload.heart_rate_avg, ex.id, db)

    # Update streak
    new_streak = _calculate_streak(current_user, payload.completed)
    current_user.streak = new_streak
    if payload.completed:
        current_user.last_workout_date = datetime.utcnow()

    # Calculate and award points
    points_earned = _calculate_points(payload.completed, payload.perceived_effort, new_streak)
    current_user.points = (current_user.points or 0) + points_earned

    # Create log entry
    log = WorkoutLog(
        user_id=current_user.id,
        exercise_id=payload.exercise_id,
        duration_mins=payload.duration_mins,
        completed=payload.completed,
        perceived_effort=payload.perceived_effort,
        heart_rate_avg=payload.heart_rate_avg,
        calories_burned=calories,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    # Auto-evaluate badges
    all_logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == current_user.id).all()
    _auto_evaluate_badges(current_user, all_logs, db)
    db.commit()

    return LogResponse(
        id=log.id, exercise_id=log.exercise_id, logged_at=log.logged_at,
        duration_mins=log.duration_mins, completed=log.completed,
        perceived_effort=log.perceived_effort, heart_rate_avg=log.heart_rate_avg,
        calories_burned=log.calories_burned, hr_warning=hr_warning,
        points_earned=points_earned, new_streak=new_streak,
    )


@router.get("/{user_id}", response_model=List[LogOut])
def get_logs(
    user_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workout history for a user, most recent first."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return (
        db.query(WorkoutLog)
        .filter(WorkoutLog.user_id == user_id)
        .order_by(WorkoutLog.logged_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{user_id}/stats")
def get_log_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aggregate statistics for the user's workout history."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    logs = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all()
    if not logs:
        return {"total_sessions": 0, "completed": 0, "completion_rate": 0,
                "total_calories": 0, "avg_effort": 0, "total_duration_mins": 0}

    completed  = [l for l in logs if l.completed]
    avg_effort = round(sum(l.perceived_effort or 0 for l in logs) / len(logs), 1)

    return {
        "total_sessions":    len(logs),
        "completed":         len(completed),
        "completion_rate":   round(len(completed) / len(logs) * 100, 1),
        "total_calories":    sum(l.calories_burned or 0 for l in logs),
        "avg_effort":        avg_effort,
        "total_duration_mins": sum(l.duration_mins or 0 for l in logs),
        "current_streak":    current_user.streak,
        "total_points":      current_user.points,
    }

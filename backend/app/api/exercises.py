"""
Exercises API
Exercise catalogue with filtering, search, and safety-aware listing.
Returns exercises filtered through the user's safety profile when requested.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exercise import Exercise
from app.schemas.schemas import ExerciseOut
from app.ontology.safety_engine import check_exercise_safety

router = APIRouter()


def _ex_to_dict(e: Exercise) -> dict:
    return {
        "id": e.id, "name": e.name, "category": e.category, "icon": e.icon,
        "met_value": e.met_value, "intensity_level": e.intensity_level,
        "muscle_groups": e.muscle_groups, "equipment": e.equipment,
        "safe_for": e.safe_for or [],
    }


@router.get("/", response_model=List[ExerciseOut])
def list_exercises(
    category:       Optional[str] = Query(None, description="Filter by category: Cardio, Strength, Flexibility"),
    intensity:      Optional[str] = Query(None, description="Filter by intensity: Low, Moderate, High"),
    safe_only:      bool          = Query(False, description="Return only exercises safe for your profile"),
    db:             Session       = Depends(get_db),
    current_user:   User          = Depends(get_current_user),
):
    """
    List all exercises with optional filters.
    When safe_only=true, runs every exercise through the user's SWRL safety profile.
    """
    q = db.query(Exercise)
    if category:  q = q.filter(Exercise.category == category)
    if intensity: q = q.filter(Exercise.intensity_level == intensity)
    exercises = q.order_by(Exercise.name).all()

    if safe_only:
        user_profile = {
            "bmi": current_user.bmi, "conditions": current_user.conditions or [],
            "age": current_user.age,
        }
        safe = []
        for ex in exercises:
            is_safe, _, _ = check_exercise_safety(user_profile, _ex_to_dict(ex))
            if is_safe:
                safe.append(ex)
        return safe

    return exercises


@router.get("/search")
def search_exercises(
    q:            str     = Query(..., min_length=2, description="Search term"),
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Search exercises by name, category, or muscle group."""
    term = f"%{q.lower()}%"
    results = (
        db.query(Exercise)
        .filter(
            (Exercise.name.ilike(term)) |
            (Exercise.category.ilike(term)) |
            (Exercise.muscle_groups.ilike(term)) |
            (Exercise.equipment.ilike(term))
        )
        .limit(10)
        .all()
    )
    return [ExerciseOut.model_validate(e) for e in results]


@router.get("/categories")
def get_categories(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return distinct exercise categories available."""
    cats = db.query(Exercise.category).distinct().all()
    return {"categories": [c[0] for c in cats]}


@router.get("/{exercise_id}", response_model=ExerciseOut)
def get_exercise(
    exercise_id:  int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
):
    """Return a single exercise with safety status for the current user."""
    ex = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    user_profile = {
        "bmi": current_user.bmi, "conditions": current_user.conditions or [],
        "age": current_user.age,
    }
    is_safe, rule_id, reason = check_exercise_safety(user_profile, _ex_to_dict(ex))

    result = ExerciseOut.model_validate(ex)
    # Attach safety info as extra fields
    return {
        **result.model_dump(),
        "safe_for_user": is_safe,
        "block_rule":    rule_id,
        "block_reason":  reason,
    }

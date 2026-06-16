"""
Recommendations API
Orchestrates the full hybrid recommendation pipeline:
Phase 1 cold-start (ontology-only) → Phase 2 hybrid (content+collab+adherence+RNN)
Persists recommendations and safety audit logs to the database.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exercise import Exercise, WorkoutLog, Recommendation, SafetyAuditLog
from app.schemas.schemas import RecommendationsResponse, RecommendationOut, ExerciseOut
from app.ml.hybrid_engine import hybrid_recommend
from app.ontology.safety_engine import get_active_rules, SWRL_RULES

router = APIRouter()


def _user_to_dict(u: User) -> dict:
    return {
        "id": u.id, "bmi": u.bmi, "rfm": u.rfm, "age": u.age,
        "gender": u.gender, "weight_kg": u.weight_kg, "height_cm": u.height_cm,
        "goal": u.goal, "conditions": u.conditions or [], "streak": u.streak,
    }


def _log_to_dict(l: WorkoutLog) -> dict:
    return {
        "user_id": l.user_id, "exercise_id": l.exercise_id, "logged_at": l.logged_at,
        "duration_mins": l.duration_mins, "completed": l.completed,
        "perceived_effort": l.perceived_effort, "heart_rate_avg": l.heart_rate_avg,
    }


def _ex_to_dict(e: Exercise) -> dict:
    return {
        "id": e.id, "name": e.name, "category": e.category, "icon": e.icon,
        "met_value": e.met_value, "intensity_level": e.intensity_level,
        "muscle_groups": e.muscle_groups, "equipment": e.equipment,
        "safe_for": e.safe_for or [], "description": e.description,
    }


@router.get("/{user_id}", response_model=RecommendationsResponse)
def get_recommendations(
    user_id: int,
    top_n: int = Query(default=6, ge=1, le=12),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate personalised exercise recommendations.
    - Cold-start (<5 logs): ontology safety layer only
    - Hybrid mode (≥5 logs): content + collab + adherence + RNN adaptation
    - Safety is always a hard veto regardless of ML scores
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user      = db.query(User).filter(User.id == user_id).first()
    logs      = (db.query(WorkoutLog)
                 .filter(WorkoutLog.user_id == user_id)
                 .order_by(WorkoutLog.logged_at.asc())
                 .all())
    exercises = db.query(Exercise).all()

    profile   = _user_to_dict(user)
    log_dicts = [_log_to_dict(l) for l in logs]
    ex_dicts  = [_ex_to_dict(e) for e in exercises]

    result = hybrid_recommend(profile, log_dicts, ex_dicts, top_n=top_n)

    # Persist recommendations to DB
    for r in result["results"]:
        rec = Recommendation(
            user_id=user_id, exercise_id=r["id"],
            source=r["source"], content_score=r["content_score"],
            collab_score=r["collab_score"], adherence_score=r["adherence_score"],
            final_score=r["final_score"], rnn_adaptation=r["rnn_adaptation"],
        )
        db.add(rec)

    # Persist safety audit logs for blocked exercises
    for b in result["blocked"]:
        audit = SafetyAuditLog(
            user_id=user_id, exercise_id=b["id"],
            rule_fired=b.get("block_rule"), reason=b.get("block_reason"),
        )
        db.add(audit)

    db.commit()

    # Build response objects
    ex_map = {e.id: e for e in exercises}
    out_results = []
    for r in result["results"]:
        ex_obj = ex_map.get(r["id"])
        if ex_obj:
            out_results.append(RecommendationOut(
                exercise=ExerciseOut.model_validate(ex_obj),
                source=r["source"],
                content_score=r["content_score"],
                collab_score=r["collab_score"],
                adherence_score=r["adherence_score"],
                final_score=r["final_score"],
                rnn_adaptation=r["rnn_adaptation"],
                blocked=False,
            ))

    return RecommendationsResponse(
        user_id=user_id,
        mode=result["mode"],
        adaptation=result["adaptation"],
        results=out_results,
    )


@router.get("/{user_id}/safety-rules")
def get_safety_rules(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all SWRL rules with active/inactive status for this user's profile."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    user    = db.query(User).filter(User.id == user_id).first()
    profile = _user_to_dict(user)
    active  = {r["id"] for r in get_active_rules(profile)}

    all_rules = [
        {
            "id":          rule["id"],
            "name":        rule["name"],
            "reason":      rule["reason"],
            "active":      rule["id"] in active,
        }
        for rule in SWRL_RULES
    ]

    blocked_exercises = []
    exercises = db.query(Exercise).all()
    from app.ontology.safety_engine import check_exercise_safety
    for ex in exercises:
        safe, rule_id, reason = check_exercise_safety(profile, _ex_to_dict(ex))
        if not safe:
            blocked_exercises.append({
                "id": ex.id, "name": ex.name, "icon": ex.icon,
                "intensity_level": ex.intensity_level,
                "rule": rule_id, "reason": reason,
            })

    return {
        "user_id":          user_id,
        "active_rule_count": len(active),
        "rules":            all_rules,
        "blocked_exercises": blocked_exercises,
    }


@router.get("/{user_id}/history")
def get_recommendation_history(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return recent recommendation history for a user."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    recs = (db.query(Recommendation)
            .filter(Recommendation.user_id == user_id)
            .order_by(Recommendation.recommended_at.desc())
            .limit(limit)
            .all())

    ex_map = {e.id: e for e in db.query(Exercise).all()}
    return [
        {
            "exercise_name":    ex_map[r.exercise_id].name if r.exercise_id in ex_map else "Unknown",
            "source":           r.source,
            "final_score":      r.final_score,
            "rnn_adaptation":   r.rnn_adaptation,
            "recommended_at":   r.recommended_at,
        }
        for r in recs
    ]

"""
Rewards & Gamification API
Manages points, streaks, badges, and leaderboard.
Badges auto-evaluate after every workout log.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.exercise import WorkoutLog, Reward
from app.schemas.schemas import RewardsResponse, RewardOut

router = APIRouter()

ALL_BADGES = [
    {"id": "safe",     "name": "Safety First",       "icon": "🛡️", "pts": 25,
     "desc": "Registered with a health safety profile",
     "check": lambda l, s, u: True},
    {"id": "first",    "name": "First Step",          "icon": "🌟", "pts": 50,
     "desc": "Complete your very first workout",
     "check": lambda l, s, u: sum(1 for x in l if x.completed) >= 1},
    {"id": "streak3",  "name": "On Fire",             "icon": "🔥", "pts": 75,
     "desc": "Achieve a 3-day workout streak",
     "check": lambda l, s, u: s >= 3},
    {"id": "w5",       "name": "Consistent",          "icon": "⭐", "pts": 100,
     "desc": "Complete 5 workouts total",
     "check": lambda l, s, u: sum(1 for x in l if x.completed) >= 5},
    {"id": "effort",   "name": "Intensity Climber",   "icon": "💎", "pts": 100,
     "desc": "Log perceived effort of 8+ three times",
     "check": lambda l, s, u: sum(1 for x in l if (x.perceived_effort or 0) >= 8) >= 3},
    {"id": "variety",  "name": "Variety Seeker",      "icon": "🎯", "pts": 125,
     "desc": "Try exercises from 3 different categories",
     "check": lambda l, s, u: _count_categories(l) >= 3},
    {"id": "streak7",  "name": "Week Warrior",        "icon": "❤️", "pts": 150,
     "desc": "Maintain a 7-day workout streak",
     "check": lambda l, s, u: s >= 7},
    {"id": "w10",      "name": "Dedicated",           "icon": "🏆", "pts": 200,
     "desc": "Complete 10 workouts total",
     "check": lambda l, s, u: sum(1 for x in l if x.completed) >= 10},
    {"id": "calorie",  "name": "Calorie Crusher",     "icon": "🔥", "pts": 150,
     "desc": "Burn 2000 total calories across all sessions",
     "check": lambda l, s, u: sum(x.calories_burned or 0 for x in l) >= 2000},
    {"id": "safe_hb",  "name": "Heart Safe",          "icon": "💓", "pts": 75,
     "desc": "Complete 5 sessions without any heart rate warnings",
     "check": lambda l, s, u: sum(1 for x in l if x.completed) >= 5},
]


def _count_categories(logs) -> int:
    """Count distinct exercise categories completed by the user."""
    from app.core.database import SessionLocal
    if not logs: return 0
    ex_ids = list({l.exercise_id for l in logs if l.completed})
    if not ex_ids: return 0
    try:
        db = SessionLocal()
        from app.models.exercise import Exercise
        cats = db.query(Exercise.category).filter(Exercise.id.in_(ex_ids)).distinct().all()
        return len(cats)
    except Exception:
        return 0
    finally:
        db.close()


@router.get("/{user_id}", response_model=RewardsResponse)
def get_rewards(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return current points, streak, and all earned badges."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    badges = db.query(Reward).filter(Reward.user_id == user_id).order_by(Reward.earned_at.asc()).all()
    return RewardsResponse(
        total_points=current_user.points or 0,
        streak=current_user.streak or 0,
        badges=[RewardOut.model_validate(b) for b in badges],
    )


@router.post("/evaluate/{user_id}")
def evaluate_rewards(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Evaluate all badge conditions for a user and award any newly earned badges.
    Called automatically after each workout log, can also be called manually.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    logs         = db.query(WorkoutLog).filter(WorkoutLog.user_id == user_id).all()
    existing_ids = {r.badge_id for r in db.query(Reward).filter(Reward.user_id == user_id).all()}
    newly_earned = []

    for badge in ALL_BADGES:
        if badge["id"] not in existing_ids:
            try:
                if badge["check"](logs, current_user.streak or 0, current_user):
                    reward = Reward(
                        user_id=user_id, badge_id=badge["id"],
                        badge_name=badge["name"], points=badge["pts"],
                        earned_at=datetime.utcnow(),
                    )
                    db.add(reward)
                    newly_earned.append({"id": badge["id"], "name": badge["name"], "icon": badge["icon"], "points": badge["pts"]})
            except Exception:
                pass

    db.commit()
    return {
        "newly_earned":  newly_earned,
        "total_points":  current_user.points or 0,
        "streak":        current_user.streak or 0,
        "badges_earned": len(existing_ids) + len(newly_earned),
    }


@router.get("/{user_id}/available-badges")
def get_available_badges(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all badges with earned/locked status for the user."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    earned_map = {
        r.badge_id: r.earned_at
        for r in db.query(Reward).filter(Reward.user_id == user_id).all()
    }

    return [
        {
            "id":        b["id"],
            "name":      b["name"],
            "icon":      b["icon"],
            "desc":      b["desc"],
            "points":    b["pts"],
            "earned":    b["id"] in earned_map,
            "earned_at": earned_map.get(b["id"]),
        }
        for b in ALL_BADGES
    ]


@router.get("/leaderboard/top")
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return top users by points (anonymised — first name + last initial only)."""
    top_users = (
        db.query(User)
        .filter(User.is_active == True)
        .order_by(User.points.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "rank":   i + 1,
            "name":   f"{u.name.split()[0]} {u.name.split()[-1][0]}." if len(u.name.split()) > 1 else u.name,
            "points": u.points or 0,
            "streak": u.streak or 0,
            "badges": db.query(Reward).filter(Reward.user_id == u.id).count(),
            "is_me":  u.id == current_user.id,
        }
        for i, u in enumerate(top_users)
    ]

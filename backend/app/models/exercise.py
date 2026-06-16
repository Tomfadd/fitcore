from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON, ForeignKey, Text
from app.core.database import Base

class Exercise(Base):
    __tablename__ = "exercises"
    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(120), unique=True, nullable=False)
    category        = Column(String(60), nullable=False)
    icon            = Column(String(10), default="🏋️")
    met_value       = Column(Float, nullable=False)
    intensity_level = Column(String(20), nullable=False)
    muscle_groups   = Column(String(255))
    equipment       = Column(String(120))
    safe_for        = Column(JSON, default=list)
    description     = Column(Text)
    created_at      = Column(DateTime, default=datetime.utcnow)

class WorkoutLog(Base):
    __tablename__ = "workout_logs"
    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id      = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    logged_at        = Column(DateTime, default=datetime.utcnow)
    duration_mins    = Column(Integer, default=30)
    completed        = Column(Boolean, nullable=False)
    perceived_effort = Column(Integer)
    heart_rate_avg   = Column(Integer)
    calories_burned  = Column(Integer)
    notes            = Column(Text)

class Recommendation(Base):
    __tablename__ = "recommendations"
    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id     = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    recommended_at  = Column(DateTime, default=datetime.utcnow)
    source          = Column(String(30), default="hybrid")
    content_score   = Column(Float)
    collab_score    = Column(Float)
    adherence_score = Column(Float)
    final_score     = Column(Float)
    rnn_adaptation  = Column(String(20))

class Reward(Base):
    __tablename__ = "rewards"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    badge_id   = Column(String(50), nullable=False)
    badge_name = Column(String(120))
    points     = Column(Integer, default=0)
    earned_at  = Column(DateTime, default=datetime.utcnow)

class SafetyAuditLog(Base):
    __tablename__ = "safety_audit_logs"
    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    rule_fired  = Column(String(120))
    reason      = Column(Text)
    logged_at   = Column(DateTime, default=datetime.utcnow)

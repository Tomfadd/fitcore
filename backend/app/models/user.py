from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, JSON
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(120), nullable=False)
    email             = Column(String(255), unique=True, index=True, nullable=False)
    password_hash     = Column(String(255), nullable=False)
    age               = Column(Integer, nullable=False)
    gender            = Column(String(10), nullable=False)
    weight_kg         = Column(Float, nullable=False)
    height_cm         = Column(Float, nullable=False)
    bmi               = Column(Float, nullable=False)
    rfm               = Column(Float, nullable=False)
    goal              = Column(String(50), nullable=False)
    conditions        = Column(JSON, default=list)
    points            = Column(Integer, default=0)
    streak            = Column(Integer, default=0)
    last_workout_date = Column(DateTime, nullable=True)
    is_active         = Column(Boolean, default=True)
    created_at        = Column(DateTime, default=datetime.utcnow)
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

"""
Pydantic Schemas — Request and Response Validation
All API input validation and response serialisation is handled here.
BMI and RFM are computed server-side on registration.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, computed_field
import math


# ── Auth ──────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:       str         = Field(..., min_length=2, max_length=120, examples=["Alex Johnson"])
    email:      EmailStr
    password:   str         = Field(..., min_length=8)
    age:        int         = Field(..., ge=13, le=110)
    gender:     str         = Field(..., pattern="^(male|female)$")
    weight_kg:  float       = Field(..., gt=20, lt=400, description="Weight in kilograms")
    height_cm:  float       = Field(..., gt=100, lt=250, description="Height in centimetres")
    goal:       str         = Field(..., pattern="^(weight-loss|strength|endurance|flexibility)$")
    conditions: List[str]   = Field(default=[], description="Health conditions: obesity, hypertension, diabetes, joint-pain, elderly, back-pain")

    @computed_field
    @property
    def bmi(self) -> float:
        """Body Mass Index = weight / height²"""
        return round(self.weight_kg / ((self.height_cm / 100) ** 2), 1)

    @computed_field
    @property
    def rfm(self) -> float:
        """Relative Fat Mass (Thomas et al. 2018 formula)"""
        g   = 12 if self.gender == "female" else 0
        val = 64 - (20 * (self.height_cm / 100) / math.sqrt(self.weight_kg / self.height_cm)) + g
        return round(max(5.0, min(60.0, val)), 1)


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"


# ── User ──────────────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id:         int
    name:       str
    email:      str
    age:        int
    gender:     str
    weight_kg:  float
    height_cm:  float
    bmi:        float
    rfm:        float
    goal:       str
    conditions: List[str]
    points:     int
    streak:     int
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    weight_kg: Optional[float] = Field(None, gt=20, lt=400)
    height_cm: Optional[float] = Field(None, gt=100, lt=250)
    goal:      Optional[str]   = Field(None, pattern="^(weight-loss|strength|endurance|flexibility)$")


# ── Exercise ──────────────────────────────────────────────────────────────────
class ExerciseOut(BaseModel):
    id:              int
    name:            str
    category:        str
    icon:            str
    met_value:       float
    intensity_level: str
    muscle_groups:   Optional[str]
    equipment:       Optional[str]
    description:     Optional[str]

    class Config:
        from_attributes = True


# ── Recommendation ────────────────────────────────────────────────────────────
class RecommendationOut(BaseModel):
    exercise:        ExerciseOut
    source:          str            # ontology | content | hybrid | rnn
    content_score:   float          # 0–1: content-based similarity
    collab_score:    float          # 0–1: collaborative filter score
    adherence_score: float          # 0–1: predicted completion probability
    final_score:     float          # 0–1: weighted hybrid score
    rnn_adaptation:  str            # increase | maintain | decrease
    blocked:         bool = False
    block_reason:    Optional[str] = None


class RecommendationsResponse(BaseModel):
    user_id:    int
    mode:       str   # cold-start | hybrid | rnn-adapted
    adaptation: str   # increase | maintain | decrease
    results:    List[RecommendationOut]


# ── Workout Log ───────────────────────────────────────────────────────────────
class LogCreate(BaseModel):
    exercise_id:      int
    duration_mins:    int           = Field(default=30, ge=1, le=300)
    completed:        bool
    perceived_effort: int           = Field(default=5, ge=1, le=10, description="Rate session difficulty 1 (easy) to 10 (maximum)")
    heart_rate_avg:   Optional[int] = Field(default=None, ge=40, le=220, description="Average heart rate in bpm")
    notes:            Optional[str] = Field(default=None, max_length=500)


class LogOut(BaseModel):
    id:               int
    exercise_id:      int
    logged_at:        datetime
    duration_mins:    int
    completed:        bool
    perceived_effort: int
    heart_rate_avg:   Optional[int]
    calories_burned:  Optional[int]

    class Config:
        from_attributes = True


# ── Rewards ───────────────────────────────────────────────────────────────────
class RewardOut(BaseModel):
    badge_id:   str
    badge_name: str
    points:     int
    earned_at:  datetime

    class Config:
        from_attributes = True


class RewardsResponse(BaseModel):
    total_points: int
    streak:       int
    badges:       List[RewardOut]

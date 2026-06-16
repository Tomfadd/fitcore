"""
XGBoost Adherence Predictor
Predicts the probability that a user will COMPLETE a given exercise session.

This is the key differentiator from traditional recommenders — we optimise
for adherence probability, not just physical optimality.

Feature vector (11 features):
  0  hour_of_day          — time context (0-23, normalised)
  1  day_of_week          — day context (0-6 Mon-Sun, normalised)
  2  exercise_intensity   — Low=0 / Moderate=0.5 / High=1.0
  3  exercise_category    — Cardio=0 / Strength=0.5 / Flexibility=1.0
  4  met_value            — metabolic equivalent (normalised to 12)
  5  user_streak          — current streak (capped at 14, normalised)
  6  days_since_last_log  — recency (capped at 30, normalised)
  7  avg_effort_last_3    — recent effort average (normalised to 10)
  8  completion_rate      — last 10 sessions completion rate
  9  bmi_norm             — BMI (capped at 50, normalised)
  10 num_conditions       — count of health conditions (normalised to 6)

Target: completed (0 = incomplete, 1 = completed)
"""
import os
import pickle
import numpy as np
from datetime import datetime
from typing import List, Optional

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score

from app.core.config import settings

INTENSITY_MAP = {"Low": 0.0, "Moderate": 0.5, "High": 1.0}
CATEGORY_MAP  = {"Cardio": 0.0, "Strength": 0.5, "Flexibility": 1.0}


def extract_features(
    user_profile: dict,
    exercise:     dict,
    user_logs:    List[dict],
    streak:       int,
) -> np.ndarray:
    """Build the 11-feature vector for one user-exercise pair."""
    now     = datetime.utcnow()
    recent  = user_logs[-10:] if len(user_logs) >= 10 else user_logs
    last_3  = user_logs[-3:]  if len(user_logs) >= 3  else user_logs

    # Days since last workout
    days_since = 0
    if user_logs:
        last_ts = user_logs[-1].get("logged_at")
        if isinstance(last_ts, datetime):
            days_since = max(0, (now - last_ts).days)

    avg_effort = (
        np.mean([l.get("perceived_effort", 5) for l in last_3]) / 10.0
        if last_3 else 0.5
    )
    completion_rate = (
        sum(1 for l in recent if l.get("completed")) / len(recent)
        if recent else 0.5
    )

    return np.array([
        now.hour / 23.0,
        now.weekday() / 6.0,
        INTENSITY_MAP.get(exercise.get("intensity_level", "Moderate"), 0.5),
        CATEGORY_MAP.get(exercise.get("category", "Cardio"), 0.0),
        min(float(exercise.get("met_value", 5.0)), 12.0) / 12.0,
        min(streak, 14) / 14.0,
        min(days_since, 30) / 30.0,
        avg_effort,
        completion_rate,
        min(float(user_profile.get("bmi", 25.0)), 50.0) / 50.0,
        len(user_profile.get("conditions", [])) / 6.0,
    ], dtype=np.float32)


class AdherencePredictor:
    def __init__(self):
        self.model:  Optional[xgb.XGBClassifier] = None
        self.fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray):
        """Train XGBoost on historical workout completion data."""
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            eval_metric="logloss",
            random_state=42,
            use_label_encoder=False,
        )
        X_tr, X_v, y_tr, y_v = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        self.model.fit(X_tr, y_tr, eval_set=[(X_v, y_v)], verbose=False)
        self.fitted = True

        acc = accuracy_score(y_v, self.model.predict(X_v))
        f1  = f1_score(y_v, self.model.predict(X_v), zero_division=0)
        print(f"[XGBoost] Validation — Accuracy: {acc:.3f} | F1: {f1:.3f} | Samples: {len(X)}")

    def predict_proba(self, features: np.ndarray) -> float:
        """
        Return probability of session completion (0.0 – 1.0).
        Falls back to heuristic if model not yet trained.
        """
        if not self.fitted or self.model is None:
            return self._heuristic(features)
        prob = self.model.predict_proba(features.reshape(1, -1))[0][1]
        return float(round(prob, 4))

    def _heuristic(self, f: np.ndarray) -> float:
        """
        Rule-based heuristic fallback used before training data is available.
        f[5]=streak, f[6]=days_since, f[7]=avg_effort, f[2]=intensity, f[8]=completion_rate
        """
        base  = 0.60
        base += f[5]  * 0.12    # streak bonus
        base -= f[6]  * 0.08    # penalty for inactivity
        base += f[7]  * 0.08    # recent effort bonus
        base -= (f[2] - 0.5) * 0.20  # intensity penalty
        base += f[8]  * 0.10    # historical completion rate
        return float(round(max(0.10, min(0.95, base)), 4))

    def save(self, path: str = settings.XGBOOST_MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    @classmethod
    def load(cls, path: str = settings.XGBOOST_MODEL_PATH) -> "AdherencePredictor":
        if not os.path.exists(path):
            return cls()
        with open(path, "rb") as fh:
            return pickle.load(fh)


# ── Singleton ─────────────────────────────────────────────────────────────────
_adherence_model: Optional[AdherencePredictor] = None

def get_adherence_model() -> AdherencePredictor:
    global _adherence_model
    if _adherence_model is None:
        _adherence_model = AdherencePredictor.load()
    return _adherence_model

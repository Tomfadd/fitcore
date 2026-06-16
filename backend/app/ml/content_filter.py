"""
Content-Based Filtering Engine
Recommends exercises similar to what the user has previously enjoyed.

Method: Cosine similarity between the user's preference vector
        and each exercise's feature vector.

Feature vector (3D):
  [category_normalised, intensity_normalised, met_normalised]

User preference vector:
  Weighted average of completed exercise vectors,
  weighted by perceived_effort score.
"""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict

CATEGORY_MAP  = {"Cardio": 0, "Strength": 1, "Flexibility": 2}
INTENSITY_MAP = {"Low": 0,    "Moderate": 1, "High": 2}


def encode_exercise(ex: dict) -> np.ndarray:
    """Encode a single exercise into a normalised 3D feature vector."""
    cat       = CATEGORY_MAP.get(ex.get("category", "Cardio"), 0)      / 2.0
    intensity = INTENSITY_MAP.get(ex.get("intensity_level", "Moderate"), 1) / 2.0
    met       = min(float(ex.get("met_value", 5.0)), 12.0)             / 12.0
    return np.array([cat, intensity, met], dtype=np.float32)


def build_user_preference_vector(logs: List[dict], exercises: List[dict]) -> np.ndarray:
    """
    Build user preference vector as effort-weighted average of
    completed exercise feature vectors.

    Falls back to a neutral [0.5, 0.5, 0.5] prior for new users.
    """
    if not logs:
        return np.array([0.5, 0.5, 0.5], dtype=np.float32)

    ex_map    = {e["id"]: e for e in exercises}
    completed = [l for l in logs if l.get("completed")] or logs

    vectors, weights = [], []
    for log in completed:
        ex = ex_map.get(log.get("exercise_id"))
        if ex:
            vectors.append(encode_exercise(ex))
            weights.append(max(1.0, float(log.get("perceived_effort", 5))))

    if not vectors:
        return np.array([0.5, 0.5, 0.5], dtype=np.float32)

    w = np.array(weights)
    w = w / w.sum()
    return np.average(vectors, axis=0, weights=w).astype(np.float32)


def content_based_scores(
    user_logs: List[dict],
    all_exercises: List[dict],
) -> Dict[int, float]:
    """
    Compute cosine similarity between the user preference vector
    and each exercise feature vector.

    Returns dict: {exercise_id: score [0.0 – 1.0]}
    """
    if not user_logs:
        # Equal scores for cold-start (no preference signal yet)
        return {ex["id"]: 0.5 for ex in all_exercises}

    user_vec = build_user_preference_vector(user_logs, all_exercises)
    ex_matrix = np.array([encode_exercise(ex) for ex in all_exercises])

    sims = cosine_similarity([user_vec], ex_matrix)[0]

    # Normalise to [0, 1]
    if sims.max() > sims.min():
        sims = (sims - sims.min()) / (sims.max() - sims.min())

    return {ex["id"]: float(round(sims[i], 4)) for i, ex in enumerate(all_exercises)}

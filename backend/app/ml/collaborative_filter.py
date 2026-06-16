"""
Collaborative Filtering Engine — SVD Matrix Factorisation
Finds users similar to the target user and surfaces exercises
they enjoyed that the target hasn't tried yet.

Method: Truncated SVD (TruncatedSVD from scikit-learn)
        applied to the user × exercise interaction matrix.

Interaction value cell formula:
  completion_rate × (avg_effort / 10)
  → higher for exercises the user consistently finishes with high effort
  → lower for exercises they abandon or find easy (low engagement)

This encodes both preference AND engagement quality.
"""
import os
import pickle
import numpy as np
from sklearn.decomposition import TruncatedSVD
from collections import defaultdict
from typing import List, Dict, Optional

from app.core.config import settings


def _build_interaction_matrix(
    all_logs:     List[dict],
    user_ids:     List[int],
    exercise_ids: List[int],
) -> np.ndarray:
    """
    Build the user × exercise interaction matrix.
    Rows = users, Columns = exercises.
    Cell = completion_rate × avg_effort_normalised.
    """
    uid_idx = {uid: i for i, uid in enumerate(user_ids)}
    eid_idx = {eid: j for j, eid in enumerate(exercise_ids)}
    matrix  = np.zeros((len(user_ids), len(exercise_ids)), dtype=np.float32)

    # Group logs by (user_id, exercise_id)
    user_ex_logs = defaultdict(list)
    for log in all_logs:
        key = (log["user_id"], log["exercise_id"])
        user_ex_logs[key].append(log)

    for (uid, eid), logs in user_ex_logs.items():
        if uid in uid_idx and eid in eid_idx:
            completion_rate = sum(1 for l in logs if l.get("completed")) / max(len(logs), 1)
            avg_effort_norm = np.mean([l.get("perceived_effort", 5) for l in logs]) / 10.0
            matrix[uid_idx[uid]][eid_idx[eid]] = completion_rate * avg_effort_norm

    return matrix


class CollaborativeFilter:
    def __init__(self, n_components: int = 20):
        self.svd            = TruncatedSVD(n_components=n_components, random_state=42)
        self.user_ids:      List[int]             = []
        self.exercise_ids:  List[int]             = []
        self.latent_matrix: Optional[np.ndarray] = None   # (n_users, n_components)
        self.ex_latent:     Optional[np.ndarray] = None   # (n_exercises, n_components)
        self.fitted:        bool                  = False

    def fit(self, all_logs: List[dict], user_ids: List[int], exercise_ids: List[int]):
        """Fit SVD on the interaction matrix."""
        self.user_ids    = user_ids
        self.exercise_ids = exercise_ids

        matrix = _build_interaction_matrix(all_logs, user_ids, exercise_ids)

        # Cap n_components to valid range for this matrix size
        max_components = min(self.svd.n_components, min(matrix.shape) - 1)
        if max_components < 1:
            return
        self.svd.n_components = max_components

        self.latent_matrix = self.svd.fit_transform(matrix)   # (n_users, k)
        self.ex_latent     = self.svd.components_.T            # (n_exercises, k)
        self.fitted        = True

        explained = self.svd.explained_variance_ratio_.sum()
        print(f"[SVD] Fitted. Components: {max_components} | Variance explained: {explained:.2%}")

    def predict_scores(self, user_id: int) -> Dict[int, float]:
        """
        Predict interaction score for each exercise for a given user.
        Returns dict: {exercise_id: score [0.0 – 1.0]}
        Returns equal scores (0.5) if user not in training data.
        """
        if not self.fitted or user_id not in self.user_ids:
            return {eid: 0.5 for eid in self.exercise_ids}

        uid_idx = self.user_ids.index(user_id)
        user_vec = self.latent_matrix[uid_idx]          # (k,)
        scores   = self.ex_latent.dot(user_vec)         # (n_exercises,)

        # Normalise to [0, 1]
        if scores.max() > scores.min():
            scores = (scores - scores.min()) / (scores.max() - scores.min())

        return {
            eid: float(round(scores[i], 4))
            for i, eid in enumerate(self.exercise_ids)
        }

    def save(self, path: str = settings.SVD_MODEL_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            pickle.dump(self, fh)

    @classmethod
    def load(cls, path: str = settings.SVD_MODEL_PATH) -> "CollaborativeFilter":
        if not os.path.exists(path):
            return cls()
        with open(path, "rb") as fh:
            return pickle.load(fh)


# ── Singleton ─────────────────────────────────────────────────────────────────
_collab_model: Optional[CollaborativeFilter] = None

def get_collab_model() -> CollaborativeFilter:
    global _collab_model
    if _collab_model is None:
        _collab_model = CollaborativeFilter.load()
    return _collab_model

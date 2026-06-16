"""
LSTM RNN Session Adapter — Phase 4 Model Adaptation
Analyses the last N workout sessions as a time-series sequence
and outputs an intensity adjustment signal for the next session.

Output classes:
  0 → "decrease"  — user is struggling, reduce intensity
  1 → "maintain"  — user is in optimal zone, keep intensity
  2 → "increase"  — user is coping well, ready to progress

Input sequence shape: (SEQUENCE_LEN, N_FEATURES) = (5, 5)

Features per session:
  0  intensity_norm   — exercise intensity (Low/Moderate/High normalised)
  1  duration_norm    — session duration normalised to 120 mins
  2  effort_norm      — perceived effort normalised to 10
  3  completed        — 1.0 if completed, 0.0 if not
  4  hr_norm          — average heart rate normalised to 200 bpm
"""
import os
import numpy as np
from typing import List, Optional

from app.core.config import settings

SEQUENCE_LEN  = 5
N_FEATURES    = 5
LABEL_MAP     = {0: "decrease", 1: "maintain", 2: "increase"}
INTENSITY_MAP = {"Low": 0.2, "Moderate": 0.5, "High": 0.9}

_tf = None
def _get_tf():
    global _tf
    if _tf is None:
        import tensorflow as tf
        _tf = tf
    return _tf


def logs_to_sequence(logs: List[dict], exercises: List[dict]) -> np.ndarray:
    """
    Convert the last SEQUENCE_LEN workout logs into a padded feature matrix.
    Older sessions are zero-padded at the start if fewer than SEQUENCE_LEN exist.
    """
    ex_map  = {e["id"]: e for e in exercises}
    recent  = logs[-SEQUENCE_LEN:]
    rows    = []

    for log in recent:
        ex = ex_map.get(log.get("exercise_id"), {})
        rows.append([
            INTENSITY_MAP.get(ex.get("intensity_level", "Moderate"), 0.5),
            min(log.get("duration_mins",  30),  120) / 120.0,
            (log.get("perceived_effort",   5))        / 10.0,
            1.0 if log.get("completed") else 0.0,
            min(log.get("heart_rate_avg", 120), 200) / 200.0,
        ])

    # Zero-pad if fewer than SEQUENCE_LEN sessions
    while len(rows) < SEQUENCE_LEN:
        rows.insert(0, [0.5, 0.25, 0.5, 0.5, 0.6])

    return np.array(rows, dtype=np.float32)


def rule_based_adaptation(logs: List[dict]) -> str:
    """
    Heuristic fallback adaptation signal.
    Used when the LSTM model is not yet trained (insufficient data).

    Logic:
      - Low effort (≤4) + all completed → ready to increase
      - High effort (≥8) OR last session incomplete → decrease
      - Otherwise → maintain
    """
    if len(logs) < 3:
        return "maintain"

    recent        = logs[-3:]
    avg_effort    = np.mean([l.get("perceived_effort", 5) for l in recent])
    all_completed = all(l.get("completed") for l in recent)
    last_done     = recent[-1].get("completed", False)

    if avg_effort <= 4 and all_completed:
        return "increase"
    if avg_effort >= 8 or not last_done:
        return "decrease"
    return "maintain"


class RNNAdapter:
    def __init__(self):
        self.model:  object       = None
        self.fitted: bool         = False

    def _build_model(self):
        tf = _get_tf()
        model = tf.keras.Sequential([
            tf.keras.layers.LSTM(
                64,
                input_shape=(SEQUENCE_LEN, N_FEATURES),
                return_sequences=True,
                dropout=0.2,
                recurrent_dropout=0.1,
            ),
            tf.keras.layers.LSTM(32, dropout=0.2),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(3, activation="softmax"),
        ])
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        return model

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 40):
        """
        Train the LSTM on session sequences.
        X shape: (n_samples, SEQUENCE_LEN, N_FEATURES)
        y shape: (n_samples,) with labels 0/1/2
        """
        tf = _get_tf()
        self.model = self._build_model()
        self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=16,
            validation_split=0.2,
            verbose=0,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(
                    patience=8,
                    restore_best_weights=True,
                    monitor="val_accuracy",
                )
            ],
        )
        self.fitted = True
        print(f"[LSTM] Training complete. Samples: {len(X)}")

    def predict(self, sequence: np.ndarray) -> str:
        """
        Predict intensity adjustment from a session sequence.
        sequence shape: (SEQUENCE_LEN, N_FEATURES)
        Returns: "increase" | "maintain" | "decrease"
        """
        if not self.fitted or self.model is None:
            return "maintain"
        probs     = self.model.predict(sequence.reshape(1, SEQUENCE_LEN, N_FEATURES), verbose=0)[0]
        label_idx = int(np.argmax(probs))
        return LABEL_MAP[label_idx]

    def save(self, path: str = settings.RNN_MODEL_PATH):
        if self.model:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            self.model.save(path)

    @classmethod
    def load(cls, path: str = settings.RNN_MODEL_PATH) -> "RNNAdapter":
        inst = cls()
        if os.path.exists(path):
            tf = _get_tf()
            inst.model  = tf.keras.models.load_model(path)
            inst.fitted = True
            print("[LSTM] Model loaded from disk.")
        return inst


# ── Singleton ─────────────────────────────────────────────────────────────────
_rnn_model: Optional[RNNAdapter] = None

def get_rnn_model() -> RNNAdapter:
    global _rnn_model
    if _rnn_model is None:
        _rnn_model = RNNAdapter.load()
    return _rnn_model


def get_adaptation_signal(logs: List[dict], exercises: List[dict]) -> str:
    """
    Main entry point for the RNN adapter.
    Returns the adaptation signal for the user's next session.
    Falls back to rule-based logic if the LSTM is not yet trained.
    """
    if len(logs) < 3:
        return "maintain"
    rnn = get_rnn_model()
    if rnn.fitted:
        seq = logs_to_sequence(logs, exercises)
        return rnn.predict(seq)
    return rule_based_adaptation(logs)

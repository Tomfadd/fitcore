"""
Hybrid Recommendation Engine — Core Orchestrator
Combines all ML components with the ontology safety layer.

Scoring formula:
  final_score = 0.50 × content_score
              + 0.40 × collab_score
              + 0.10 × adherence_score
              ± rnn_intensity_bonus

Safety is a HARD VETO: any exercise blocked by SWRL rules scores 0
regardless of ML output. This is non-negotiable and cannot be bypassed.
"""
from typing import List, Dict, Any

from app.core.config import settings
from app.ontology.safety_engine import check_exercise_safety
from app.ml.content_filter import content_based_scores
from app.ml.collaborative_filter import get_collab_model
from app.ml.adherence_predictor import get_adherence_model, extract_features
from app.ml.rnn_adapter import get_adaptation_signal, rule_based_adaptation


# RNN intensity adjustment bonuses
_RNN_BONUS = {
    "increase": {"Low": -0.05, "Moderate": 0.02, "High": 0.10},
    "decrease": {"Low": 0.10,  "Moderate": 0.02, "High": -0.10},
    "maintain": {"Low": 0.0,   "Moderate": 0.0,  "High": 0.0},
}

# Goal-based category preferences (soft boost, not hard filter)
_GOAL_CATEGORY_BOOST = {
    "weight-loss": {"Cardio": 0.06,      "Strength": 0.02,  "Flexibility": -0.01},
    "strength":    {"Cardio": 0.01,      "Strength": 0.08,  "Flexibility": 0.01},
    "endurance":   {"Cardio": 0.08,      "Strength": -0.01, "Flexibility": 0.01},
    "flexibility": {"Cardio": 0.0,       "Strength": 0.0,   "Flexibility": 0.08},
}


def hybrid_recommend(
    user_profile: dict,
    user_logs:    List[dict],
    all_exercises: List[dict],
    top_n:        int = 6,
) -> Dict[str, Any]:
    """
    Main recommendation entry point.

    Args:
        user_profile:  Dict with keys: id, bmi, conditions, age, weight_kg,
                       height_cm, goal, streak
        user_logs:     Chronological list of workout log dicts
        all_exercises: Full exercise catalogue dicts
        top_n:         Number of recommendations to return

    Returns:
        {
            mode:       "cold-start" | "hybrid" | "rnn-adapted"
            adaptation: "increase" | "maintain" | "decrease"
            results:    [scored + ranked exercise dicts]
            blocked:    [exercises blocked by safety layer]
        }
    """
    n_logs     = len(user_logs)
    cold_start = n_logs < settings.COLD_START_THRESHOLD

    # ── Step 1: RNN adaptation signal ─────────────────────────────────────────
    if cold_start:
        adaptation = "maintain"
    else:
        adaptation = get_adaptation_signal(user_logs, all_exercises)

    # ── Step 2: Safety veto — hard pass, no exceptions ────────────────────────
    safe_exercises, blocked_exercises = [], []
    for ex in all_exercises:
        is_safe, rule_id, reason = check_exercise_safety(user_profile, ex)
        if is_safe:
            safe_exercises.append(ex)
        else:
            blocked_exercises.append({
                **ex,
                "blocked":      True,
                "block_rule":   rule_id,
                "block_reason": reason,
            })

    if not safe_exercises:
        return {
            "mode":       "cold-start",
            "adaptation": adaptation,
            "results":    [],
            "blocked":    blocked_exercises,
        }

    # ── Step 3: Content-based scores ──────────────────────────────────────────
    cb_scores = content_based_scores(user_logs, safe_exercises)

    # ── Step 4: Collaborative filter scores ───────────────────────────────────
    collab_model = get_collab_model()
    cf_scores    = {} if cold_start else collab_model.predict_scores(user_profile["id"])

    # ── Step 5: Adherence predictor ───────────────────────────────────────────
    adh_model = get_adherence_model()
    streak    = user_profile.get("streak", 0)
    goal      = user_profile.get("goal", "weight-loss")

    # ── Step 6: Score, rank, annotate ─────────────────────────────────────────
    scored = []
    for ex in safe_exercises:
        eid = ex["id"]

        content_score   = cb_scores.get(eid, 0.5)
        collab_score    = cf_scores.get(eid, 0.5)
        features        = extract_features(user_profile, ex, user_logs, streak)
        adherence_score = adh_model.predict_proba(features)

        # RNN intensity adjustment
        intensity_bonus = _RNN_BONUS[adaptation].get(ex.get("intensity_level", "Moderate"), 0.0)

        # Goal-based soft boost
        goal_bonus = _GOAL_CATEGORY_BOOST.get(goal, {}).get(ex.get("category", "Cardio"), 0.0)

        # Weighted hybrid merge
        if cold_start:
            # Cold-start: content + goal only (no collab history)
            final_score = content_score + goal_bonus
            source      = "ontology"
        else:
            final_score = (
                settings.CONTENT_WEIGHT   * content_score +
                settings.COLLAB_WEIGHT    * collab_score  +
                settings.ADHERENCE_WEIGHT * adherence_score +
                intensity_bonus +
                goal_bonus
            )
            source = "rnn" if adaptation != "maintain" else "hybrid"

        final_score = round(max(0.0, min(1.0, final_score)), 4)

        scored.append({
            **ex,
            "source":          source,
            "content_score":   round(content_score, 4),
            "collab_score":    round(collab_score, 4),
            "adherence_score": round(adherence_score, 4),
            "final_score":     final_score,
            "rnn_adaptation":  adaptation,
            "goal_boost":      round(goal_bonus, 4),
            "blocked":         False,
        })

    scored.sort(key=lambda x: x["final_score"], reverse=True)

    mode = (
        "cold-start"  if cold_start else
        "rnn-adapted" if adaptation != "maintain" else
        "hybrid"
    )

    return {
        "mode":       mode,
        "adaptation": adaptation,
        "results":    scored[:top_n],
        "blocked":    blocked_exercises,
    }

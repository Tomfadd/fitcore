import numpy as np
from collections import defaultdict
from app.core.database import SessionLocal
from app.models.exercise import WorkoutLog, Exercise
from app.models.user import User
from app.ml.collaborative_filter import CollaborativeFilter
from app.ml.adherence_predictor import AdherencePredictor, extract_features
from app.ml.rnn_adapter import RNNAdapter, logs_to_sequence, SEQUENCE_LEN

MIN_COLLAB, MIN_XGB, MIN_RNN = 20, 50, 30

def retrain_all_models():
    print("Retraining models...")
    db = SessionLocal()
    try:
        logs = db.query(WorkoutLog).all()
        users = db.query(User).all()
        exercises = db.query(Exercise).all()
        ld = [_ld(l) for l in logs]
        ud = {u.id: _ud(u) for u in users}
        ed = [_ed(e) for e in exercises]
        _retrain_collab(ld, [u.id for u in users], [e.id for e in exercises])
        _retrain_xgb(ld, ud, ed)
        _retrain_rnn(ld, ud, ed)
        print("Retraining complete.")
    finally:
        db.close()

def _retrain_collab(ld, uids, eids):
    if len(ld) < MIN_COLLAB: return
    m = CollaborativeFilter(n_components=min(20, len(uids)-1, len(eids)-1))
    m.fit(ld, uids, eids); m.save()
    import app.ml.collaborative_filter as c; c._collab_model = m
    print(f"[SVD] retrained on {len(ld)} logs")

def _retrain_xgb(ld, ud, ed):
    if len(ld) < MIN_XGB: return
    em = {e["id"]: e for e in ed}
    ul = defaultdict(list)
    for l in sorted(ld, key=lambda x: x.get("logged_at") or 0): ul[l["user_id"]].append(l)
    X, y = [], []
    for uid, logs in ul.items():
        p = ud.get(uid, {}); streak = 0
        for i, log in enumerate(logs):
            ex = em.get(log.get("exercise_id"), {})
            if ex:
                X.append(extract_features(p, ex, logs[:i], streak))
                y.append(1 if log.get("completed") else 0)
                streak = streak+1 if log.get("completed") else 0
    if len(X) >= MIN_XGB:
        m = AdherencePredictor(); m.fit(np.array(X), np.array(y)); m.save()
        import app.ml.adherence_predictor as a; a._adherence_model = m
        print(f"[XGBoost] retrained on {len(X)} samples")

def _retrain_rnn(ld, ud, ed):
    if len(ld) < MIN_RNN: return
    ul = defaultdict(list)
    for l in sorted(ld, key=lambda x: x.get("logged_at") or 0): ul[l["user_id"]].append(l)
    X, y = [], []
    for uid, logs in ul.items():
        for i in range(SEQUENCE_LEN, len(logs)):
            window = logs[i-SEQUENCE_LEN:i]; nxt = logs[i]
            ae = np.mean([l.get("perceived_effort", 5) for l in window])
            ne = nxt.get("perceived_effort", 5)
            label = 2 if ne > ae+1 else (0 if ne < ae-1 else 1)
            X.append(logs_to_sequence(window, ed)); y.append(label)
    if len(X) >= MIN_RNN:
        m = RNNAdapter(); m.fit(np.array(X), np.array(y)); m.save()
        import app.ml.rnn_adapter as r; r._rnn_model = m
        print(f"[RNN] retrained on {len(X)} sequences")

def _ld(l): return {"id":l.id,"user_id":l.user_id,"exercise_id":l.exercise_id,"logged_at":l.logged_at,"duration_mins":l.duration_mins,"completed":l.completed,"perceived_effort":l.perceived_effort,"heart_rate_avg":l.heart_rate_avg,"calories_burned":l.calories_burned}
def _ud(u): return {"id":u.id,"bmi":u.bmi,"rfm":u.rfm,"age":u.age,"gender":u.gender,"weight_kg":u.weight_kg,"height_cm":u.height_cm,"goal":u.goal,"conditions":u.conditions or [],"streak":u.streak}
def _ed(e): return {"id":e.id,"name":e.name,"category":e.category,"icon":e.icon,"met_value":e.met_value,"intensity_level":e.intensity_level,"muscle_groups":e.muscle_groups,"equipment":e.equipment,"safe_for":e.safe_for or []}

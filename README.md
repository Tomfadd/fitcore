# FitCore AI — Hybrid Exercise Recommender System
### Final Year Project | BSc Computing / Engineering

---

## Quick Start (3 commands)

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Build and start everything
docker-compose up --build

# 3. Open in browser
# Frontend:  http://localhost
# API Docs:  http://localhost:8000/docs
```

---

## What's Inside

```
fitcore/
├── backend/
│   ├── main.py                        # FastAPI entry point
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic/                       # DB migrations
│   │   └── versions/001_initial_schema.py
│   └── app/
│       ├── core/
│       │   ├── config.py              # Settings (.env)
│       │   ├── database.py            # SQLAlchemy engine
│       │   └── security.py            # JWT + bcrypt
│       ├── models/
│       │   ├── user.py                # User model
│       │   └── exercise.py            # Exercise, Log, Recommendation, Reward models
│       ├── schemas/
│       │   └── schemas.py             # Pydantic request/response schemas
│       ├── api/
│       │   ├── auth.py                # Register, Login, Refresh, Logout
│       │   ├── users.py               # Profile endpoints
│       │   ├── exercises.py           # Exercise catalogue
│       │   ├── recommendations.py     # Hybrid engine endpoint
│       │   ├── logs.py                # Workout logging
│       │   └── rewards.py             # Points, badges, streaks
│       ├── ml/
│       │   ├── content_filter.py      # Cosine similarity content filter
│       │   ├── collaborative_filter.py # SVD matrix factorisation
│       │   ├── adherence_predictor.py  # XGBoost completion predictor
│       │   ├── rnn_adapter.py          # LSTM intensity adapter
│       │   ├── hybrid_engine.py        # Main orchestrator
│       │   └── retrain.py              # Weekly retraining pipeline
│       └── ontology/
│           └── safety_engine.py        # SWRL safety rules R1-R6
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── App.jsx                    # Router + auth guard
│       ├── index.js
│       ├── api/
│       │   ├── client.js              # Axios + auto token refresh
│       │   └── endpoints.js           # All API calls
│       ├── hooks/
│       │   └── useAuth.js             # Auth context + hook
│       ├── utils/
│       │   └── helpers.js             # BMI, RFM, formatting
│       ├── components/
│       │   └── Layout.jsx             # Sidebar + nav shell
│       └── pages/
│           ├── Register.jsx           # Onboarding form
│           ├── Login.jsx              # Sign in
│           ├── Dashboard.jsx          # Recommendations + logging
│           ├── Progress.jsx           # Charts + analytics
│           ├── Rewards.jsx            # Points + badges
│           └── Safety.jsx             # SWRL rules display
│
├── scripts/
│   └── seed.sql                       # 20 exercises pre-loaded
├── tests/
│   ├── test_safety.py                 # Safety engine unit tests
│   └── test_hybrid_engine.py          # Recommendation engine tests
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Running Tests

```bash
cd tests
python test_safety.py
python test_hybrid_engine.py
```

---

## API Documentation

Auto-generated Swagger UI available at:
`http://localhost:8000/docs`

ReDoc available at:
`http://localhost:8000/redoc`

---

## ML Models

Models are saved to `backend/ml_models/` after first retraining.
Before enough data exists, all models fall back to rule-based heuristics automatically.

| Model | File | Min data to train |
|---|---|---|
| XGBoost Adherence | xgboost_adherence.pkl | 50 logs |
| SVD Collab Filter | svd_collab.pkl | 20 logs |
| LSTM RNN Adapter  | rnn_adapter.keras | 30 logs |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL 15 |
| Cache | Redis 7 |
| Auth | JWT (access + refresh) |
| ML | scikit-learn, XGBoost, TensorFlow/Keras |
| Ontology | Owlready2 + SWRL |
| Frontend | React 18, Recharts |
| Deployment | Docker, Docker Compose |

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.core.database import engine, Base
from app.api import auth, users, exercises, recommendations, logs, rewards
from app.ml.retrain import retrain_all_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = BackgroundScheduler()
    scheduler.add_job(retrain_all_models, trigger="interval", weeks=1, id="retrain_models", replace_existing=True)
    scheduler.start()
    print("FitCore AI started.")
    yield
    scheduler.shutdown()

app = FastAPI(title="FitCore AI", description="Hybrid Exercise Recommender System", version="1.0.0", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,            prefix="/api/auth",            tags=["Auth"])
app.include_router(users.router,           prefix="/api/users",           tags=["Users"])
app.include_router(exercises.router,       prefix="/api/exercises",       tags=["Exercises"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(logs.router,            prefix="/api/logs",            tags=["Logs"])
app.include_router(rewards.router,         prefix="/api/rewards",         tags=["Rewards"])

@app.get("/health")
def health(): return {"status": "ok"}

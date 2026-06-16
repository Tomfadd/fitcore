from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    DATABASE_URL: str = "postgresql://fitcore:fitcore_secret@localhost:5432/fitcore_db"
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str = "change_me_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ENVIRONMENT: str = "development"
    MODEL_DIR: str = "ml_models"
    XGBOOST_MODEL_PATH: str = "ml_models/xgboost_adherence.pkl"
    RNN_MODEL_PATH: str = "ml_models/rnn_adapter.keras"
    SVD_MODEL_PATH: str = "ml_models/svd_collab.pkl"
    ONTOLOGY_PATH: str = "app/ontology/exercise_safety.owl"
    CONTENT_WEIGHT: float = 0.50
    COLLAB_WEIGHT: float = 0.40
    ADHERENCE_WEIGHT: float = 0.10
    COLD_START_THRESHOLD: int = 5

settings = Settings()

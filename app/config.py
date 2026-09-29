from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "rtoguard"

    # Risk scoring defaults
    HIGH_RISK_THRESHOLD: float = 0.6
    MODEL_PATH: str = "models/rto_model.joblib"

    # App
    APP_NAME: str = "RTOGuard AI"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

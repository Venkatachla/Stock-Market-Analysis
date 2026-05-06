"""
Configuration management using Pydantic BaseSettings.
Loads all configuration from environment variables.
"""
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from .env"""
    
    # ==================== API CONFIGURATION ====================
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_title: str = "STCOK Trading System API"
    api_version: str = "2.0.0"
    api_description: str = "Production-grade stock prediction and trading system"
    
    # ==================== DATABASE CONFIGURATION ====================
    database_url: str = Field(default="sqlite:///./db.sqlite3", env="DATABASE_URL")
    
    @validator("database_url")
    def validate_database_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL must be set")
        return v
    
    # ==================== JWT AUTHENTICATION ====================
    secret_key: str = Field(default="your-secret-key-change-in-production-12345", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters for production")
        return v
    
    # ==================== RAZORPAY PAYMENT GATEWAY ====================
    razorpay_key_id: Optional[str] = Field(default="", env="RAZORPAY_KEY_ID")
    razorpay_key_secret: Optional[str] = Field(default="", env="RAZORPAY_KEY_SECRET")
    
    # ==================== ML MODELS CONFIGURATION ====================
    model_dir: Path = Field(default="models", env="MODEL_DIR")
    model_type: str = Field(default="ensemble", env="MODEL_TYPE")  # ensemble, xgb, lgbm, rf, lstm
    
    @validator("model_dir")
    def validate_model_dir(cls, v):
        model_path = Path(v)
        if not model_path.exists():
            print(f"⚠️  Model directory {model_path} does not exist. Creating it...")
            model_path.mkdir(parents=True, exist_ok=True)
        return model_path
    
    # ==================== ENVIRONMENT ====================
    environment: str = Field(default="development", env="PYTHON_ENV")
    debug: bool = Field(default=True, env="DEBUG")
    
    @validator("environment")
    def validate_environment(cls, v):
        valid_envs = ["development", "staging", "production"]
        if v not in valid_envs:
            raise ValueError(f"PYTHON_ENV must be one of: {valid_envs}")
        return v
    
    # ==================== LOGGING ====================
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # ==================== FEATURE FLAGS ====================
    enable_razorpay: bool = Field(default=False, env="ENABLE_RAZORPAY")
    enable_ml_predictions: bool = Field(default=True, env="ENABLE_ML_PREDICTIONS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __str__(self) -> str:
        """String representation (without secrets)"""
        return f"""
        === STCOK Configuration ===
        Environment: {self.environment}
        API: {self.api_host}:{self.api_port}
        Database: {self.database_url}
        Models: {self.model_dir} ({self.model_type})
        Razorpay: {'Enabled' if self.enable_razorpay else 'Disabled'}
        Debug: {self.debug}
        """


# Global settings instance
settings = Settings()

# Validate production requirements
if settings.environment == "production":
    if settings.debug:
        raise ValueError("DEBUG must be False in production")
    if settings.secret_key == "your-secret-key-change-in-production-12345":
        raise ValueError("SECRET_KEY must be changed in production")
    if settings.enable_razorpay and (not settings.razorpay_key_id or not settings.razorpay_key_secret):
        raise ValueError("Razorpay keys must be set if ENABLE_RAZORPAY=true in production")

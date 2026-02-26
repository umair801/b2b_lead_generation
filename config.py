# config.py
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    openai_api_key: str
    supabase_url: str
    supabase_key: str
    apollo_api_key: str
    hunter_api_key: str
    log_level: str = "INFO"
    environment: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
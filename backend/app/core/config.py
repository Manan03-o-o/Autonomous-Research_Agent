from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Autonomous Research Agent"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/research_agent"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # APIs
    GEMINI_API_KEY: str = ""
    SEARCH_API_KEY: str = "" # In case we switch to Tavily or similar, otherwise we use duckduckgo
    
    # Model config
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

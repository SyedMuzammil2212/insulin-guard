from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./dev.db'
    jwt_secret: str
    access_minutes: int = 15
    refresh_days: int = 30
    cors_origins: str = ''
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

settings = Settings()

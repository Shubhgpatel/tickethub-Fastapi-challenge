from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    env: str = "development"
    mongo_uri: str
    mongo_db: str = "tickethub"
    redis_url: str

settings = Settings()
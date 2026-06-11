from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ADZUNA_APP_ID: str = ""
    ADZUNA_APP_KEY: str = ""
    JSEARCH_API_KEY: str = ""
    ONET_USERNAME: str = ""
    ONET_PASSWORD: str = ""
    CLEARBIT_API_KEY: str = ""
    GLASSDOOR_PARTNER_ID: str = ""
    GLASSDOOR_KEY: str = ""


settings = Settings()

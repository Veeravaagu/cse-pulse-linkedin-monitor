from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "CSE Pulse LinkedIn Monitor"
    env: str = "development"
    mock_mode: bool = True
    log_level: str = "INFO"

    data_file: str = "data/activities.json"

    ai_provider: str = "mock"
    ai_model: str = "gpt-4o-mini"

    google_sheets_id: str = ""
    google_service_account_json: str = ""
    google_sheets_worksheet: str = "Sheet1"

    gmail_query: str = "from:linkedin.com"
    gmail_max_results: int = 25

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

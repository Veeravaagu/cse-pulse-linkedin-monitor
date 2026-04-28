from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "CSE Pulse LinkedIn Monitor"
    env: str = "development"
    mock_mode: bool = True
    # Ingestion adapter mode: "mock" (local JSON) or "gmail" (API scaffold).
    ingestion_mode: str = "mock"
    log_level: str = "INFO"

    data_file: str = "data/activities.json"
    ingestion_state_file: str = "data/ingestion_state.json"
    public_fetch_mode_file: str = "data/public_fetch_mode.json"

    # Enrichment mode: "mock" keeps rule-based logic, "llm" is a future scaffold.
    ai_provider: str = "mock"
    ai_model: str = "gpt-4o-mini"

    google_sheets_enabled: bool = False
    google_sheets_id: str = ""
    # Backward-compatible legacy field. If present, we treat it as a file path.
    google_service_account_json: str = ""
    google_service_account_path: str = ""
    google_sheets_worksheet: str = "Sheet1"

    mock_email_payload_path: str = "data/mock_emails/linkedin_notifications.json"

    gmail_query: str = "from:linkedin.com"
    gmail_max_results: int = 25
    gmail_credentials_path: str = ""
    gmail_oauth_client_secret_path: str = ""
    gmail_token_path: str = ""
    admin_username: str = ""
    admin_password: str = ""
    admin_session_secret: str = ""
    main_dashboard_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

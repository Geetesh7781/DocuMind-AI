from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "none"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    chunk_words: int = 180
    chunk_overlap: int = 40
    top_k: int = 5
    max_upload_mb: int = 25
    data_dir: str = "data"


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class _Config(BaseSettings):
    model_config = SettingsConfigDict(
        extra='ignore',
        case_sensitive=False,
        env_file='.env',
        env_file_encoding='utf-8',
    )

    TELEGRAM_BOT_TOKEN: str
    MAP_API_KEY: str
    WEATHER_API_KEY: str
    DATABASE_URL: str
    LLM_API_URL: str
    MODEL_NAME: str
    SERVER_URL: str


Config = _Config()

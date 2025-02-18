import os

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    MAPS_API_KEY = os.getenv("MAPS_API_KEY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    LLM_API_URL = os.getenv("LLM_API_URL")

if not Config.TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set")
if not Config.MAPS_API_KEY:
    raise ValueError("MAPS_API_KEY is not set")
if not Config.WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY is not set")
if not Config.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set")
if not Config.DATABASE_URL:
    raise ValueError("LLM_API_URL is not set")

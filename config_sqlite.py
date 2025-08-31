import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database - используем SQLite для тестирования
    @property
    def DATABASE_URL(self) -> str:
        return "sqlite:///./badminton_test.db"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "Badminton Rating"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()


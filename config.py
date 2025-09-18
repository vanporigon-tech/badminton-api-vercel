import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "badminton_rating")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Database URL
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "")
    # По умолчанию используем публичные URL, чтобы бот и Mini App были согласованы
    MINI_APP_URL: str = os.getenv("MINI_APP_URL", "https://vanporigon-tech.github.io/badminton-rating-app")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://badminton-api-vercel.onrender.com")
    
    # Admins
    @property
    def ADMIN_IDS(self):
        raw = os.getenv("ADMIN_IDS", "")
        ids = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                ids.append(int(part))
            except ValueError:
                continue
        return set(ids)
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App
    APP_NAME: str = "Badminton Rating"
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

settings = Settings()


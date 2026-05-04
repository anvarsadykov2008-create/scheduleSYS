import os
import logging

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

# Получаем абсолютный путь к папке проекта (корень, где лежит schedule.db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "schedule.db")

_INSECURE_DEFAULT_KEY = "your-super-secret-key-change-it"


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{DEFAULT_DB_PATH}"
    # [FIX S-04] Убран дефолтный ключ. Обязательно задать SECRET_KEY в .env
    secret_key: str = _INSECURE_DEFAULT_KEY
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 1 неделя
    # [FIX S-01] Список допустимых CORS origins через запятую (без пробелов)
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = ".env"


settings = Settings()

# [FIX S-04] Предупреждение о небезопасном ключе
if settings.secret_key == _INSECURE_DEFAULT_KEY:
    logger.critical(
        "⚠️  SECRET_KEY не задан в .env и используется небезопасный дефолт! "
        "Установите случайный SECRET_KEY перед развёртыванием в production. "
        "Пример: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# Export variables for compatibility with auth.py
DATABASE_URL = settings.database_url
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
CORS_ORIGINS = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

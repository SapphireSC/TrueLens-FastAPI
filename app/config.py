import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = APP_DIR / "static" / "uploads"
MODEL_PATH = BASE_DIR / "ai" / "saved_model" / "truelens_efficientnet.keras"
METRICS_JSON_PATH = BASE_DIR / "ai" / "saved_model" / "evaluation_metrics.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Default ke PostgreSQL jika diset di .env, fallback ke SQLite lokal agar langsung siap jalan di VS Code
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{BASE_DIR / 'truelens_local.db'}"
)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}

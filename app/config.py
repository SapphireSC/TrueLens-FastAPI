import os
from pathlib import Path
from sqlmodel import Session, SQLModel, create_engine

APP_NAME = "TrueLens AI"
APP_DESCRIPTION = "Sistem Klasifikasi Gambar Asli vs Buatan AI dengan Database PostgreSQL"
APP_VERSION = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Konfigurasi Database PostgreSQL sesuai yang diajarkan di kelas
# (Ubah password 'postgres' di bawah ini jika password PostgreSQL lokal Anda berbeda, atau set melalui environment variable)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:SuperNova00@localhost:5432/truelens_db"
)

engine = create_engine(DATABASE_URL, echo=True)


def get_session():
    with Session(engine) as session:
        yield session

from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlmodel import SQLModel

from config import APP_NAME, APP_DESCRIPTION, APP_VERSION, engine
from routes.truelens_route import router as truelens_router

app = FastAPI(
    title=APP_NAME,
    description=APP_DESCRIPTION,
    version=APP_VERSION
)

app.add_middleware(
    SessionMiddleware,
    secret_key="secret123",
)

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Otomatis memastikan tabel database siap saat aplikasi dijalankan
try:
    SQLModel.metadata.create_all(engine)
except Exception as e:
    print(f"[Info Database] Pastikan PostgreSQL aktif dan database 'truelens_db' sudah dibuat: {e}")

app.include_router(truelens_router)

from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import APP_DIR, MODEL_PATH
from app.database import Base, engine, SessionLocal
from app.models import ScanHistory
from app.services.scan_engine import TrueLensScanEngine
from app.routes import home, predict, history


def seed_initial_sample_records():
    """Mengisi 4 data contoh berlabel 'Contoh' apabila tabel scan_history masih kosong."""
    db = SessionLocal()
    try:
        if db.query(ScanHistory).count() == 0:
            samples = [
                ScanHistory(
                    filename="sample_stage_concert_photo.jpg",
                    image_path="",
                    file_size_kb=412.5,
                    resolution="1920x1080",
                    predicted_label="Real",
                    risk_tier="Citra asli (Authentic Real Image)",
                    confidence_score=88.7,
                    raw_prob=0.113,
                    notes="Contoh data awal: dokumentasi panggung konser kamera DSLR",
                    is_sample=True,
                    created_at=datetime(2026, 11, 9, 19, 15, 0),
                ),
                ScanHistory(
                    filename="sample_synth_cyberpunk_poster.png",
                    image_path="",
                    file_size_kb=684.2,
                    resolution="1024x1024",
                    predicted_label="AI-Generated",
                    risk_tier="Sintetis AI (Synthetic AI-Generated)",
                    confidence_score=91.2,
                    raw_prob=0.912,
                    notes="Contoh data awal: ilustrasi poster sintetis hasil generator difusi",
                    is_sample=True,
                    created_at=datetime(2026, 11, 9, 20, 5, 0),
                ),
                ScanHistory(
                    filename="sample_editorial_portrait_compressed.jpg",
                    image_path="",
                    file_size_kb=198.0,
                    resolution="1280x853",
                    predicted_label="Real",
                    risk_tier="Cenderung asli (Likely Real Image)",
                    confidence_score=64.2,
                    raw_prob=0.358,
                    notes="Contoh data awal: foto redaksi dengan kompresi JPEG tingkat lanjut",
                    is_sample=True,
                    created_at=datetime(2026, 11, 10, 8, 30, 0),
                ),
                ScanHistory(
                    filename="sample_concept_art_character.png",
                    image_path="",
                    file_size_kb=520.8,
                    resolution="768x768",
                    predicted_label="AI-Generated",
                    risk_tier="Cenderung AI (Likely AI-Generated)",
                    confidence_score=68.4,
                    raw_prob=0.684,
                    notes="Contoh data awal: konsep karakter digital dengan inpainting AI",
                    is_sample=True,
                    created_at=datetime(2026, 11, 10, 10, 45, 0),
                ),
            ]
            db.add_all(samples)
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Buat tabel otomatis dan isi data contoh jika kosong
    Base.metadata.create_all(bind=engine)
    seed_initial_sample_records()
    # Muat model AI satu kali ke memori aplikasi
    app.state.scan_engine = TrueLensScanEngine(MODEL_PATH)
    yield


app = FastAPI(
    title="TrueLens AI",
    description="Sistem Klasifikasi Gambar Asli vs Buatan AI Berbasis Deep Learning (EfficientNet-B0 & FastAPI)",
    version="1.0.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))
app.state.templates = templates

app.include_router(home.router)
app.include_router(predict.router)
app.include_router(history.router)


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    status_code = exc.status_code
    title = "Halaman tidak ditemukan" if status_code == 404 else "Permintaan tidak dapat diproses"
    message = (
        "Alamat halaman atau entri riwayat yang Anda tuju tidak tersedia di server."
        if status_code == 404
        else str(exc.detail)
    )
    return request.app.state.templates.TemplateResponse(
        request,
        "error.html",
        {
            "active_page": "",
            "status_code": status_code,
            "error_title": title,
            "error_message": message,
        },
        status_code=status_code,
    )


@app.exception_handler(Exception)
async def custom_internal_exception_handler(request: Request, exc: Exception):
    return request.app.state.templates.TemplateResponse(
        request,
        "error.html",
        {
            "active_page": "",
            "status_code": 500,
            "error_title": "Layanan tidak tersedia",
            "error_message": "Terjadi kendala teknis saat memproses permintaan Anda. Silakan coba beberapa saat lagi.",
        },
        status_code=500,
    )

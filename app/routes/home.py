import json
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.config import METRICS_JSON_PATH

router = APIRouter()


def load_evaluation_metrics() -> dict:
    if METRICS_JSON_PATH.exists():
        try:
            with open(METRICS_JSON_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"evaluated": False}


@router.get("/", response_class=HTMLResponse, name="home")
async def home_page(request: Request):
    metrics = load_evaluation_metrics()
    scan_engine = getattr(request.app.state, "scan_engine", None)
    is_live_model = bool(scan_engine and scan_engine.is_live_model)

    return request.app.state.templates.TemplateResponse(
        request,
        "home.html",
        {
            "active_page": "home",
            "metrics": metrics,
            "is_live_model": is_live_model,
        },
    )


@router.get("/contact", response_class=HTMLResponse, name="contact")
async def contact_page(request: Request):
    team_roles = [
        {
            "code": "A1",
            "role": "Anggota 1 · AI & Data Specialist",
            "focus": "Eksplorasi Dataset CIFAKE & Pelatihan EfficientNet-B0",
            "tasks": [
                "Mengunduh dan mempartisi 120.000 citra dataset CIFAKE (Train, Validation, Test).",
                "Menyusun pipeline prapemrosesan (224x224x3) dengan koreksi Rescaling internal Keras.",
                "Melatih Transfer Learning EfficientNet-B0 dua tahap dan mengekspor bobot .keras.",
                "Menghitung metrik evaluasi pada 20.000 data uji (Accuracy, Precision, Recall, F1, ROC-AUC).",
            ],
        },
        {
            "code": "A2",
            "role": "Anggota 2 · Backend Developer",
            "focus": "Arsitektur FastAPI, Lifespan AI, & Keamanan Upload",
            "tasks": [
                "Membangun struktur modular FastAPI dan pemuatan model AI satu kali saat startup (Lifespan).",
                "Mengimplementasikan TrueLensScanEngine untuk ekstraksi probabilitas Sigmoid dan skor keyakinan.",
                "Memvalidasi ukuran file (maks 10 MB), ekstensi, serta verifikasi magic bytes PNG/JPEG.",
                "Menyediakan endpoint prediksi, penyimpanan riwayat, dan penghapusan file fisik secara sinkron.",
            ],
        },
        {
            "code": "A3",
            "role": "Anggota 3 · Frontend Developer",
            "focus": "Antarmuka Jinja2, Desain Klinis-Forensik, & Aksesibilitas",
            "tasks": [
                "Merancang antarmuka Light Forensic-Clinical berbasis CSS custom properties dan Jinja2 macro.",
                "Membangun komponen dropzone interaktif dengan pratinjau gambar langsung dan state loading.",
                "Memvisualisasikan meter keyakinan, skala probabilitas 4 rentang, dan disclosure teknis.",
                "Memastikan tampilan responsif dari layar 375px hingga desktop tanpa horizontal scroll.",
            ],
        },
        {
            "code": "A4",
            "role": "Anggota 4 · Database & QA Lead",
            "focus": "Skema PostgreSQL, Operasi CRUD SQLAlchemy, & Pengujian",
            "tasks": [
                "Merancang tabel relasional scan_history pada PostgreSQL beserta indeks pencarian.",
                "Menyusun file dump database/truelens_db.sql dan model SQLAlchemy 2.0 ORM.",
                "Memverifikasi alur Create (Simpan), Read (Filter Riwayat), dan Delete (Konfirmasi & Hapus).",
                "Menjalankan pengujian fungsional Black-Box dan menyusun dokumentasi laporan PDF UAS.",
            ],
        },
    ]

    return request.app.state.templates.TemplateResponse(
        request,
        "contact.html",
        {
            "active_page": "contact",
            "team_roles": team_roles,
        },
    )

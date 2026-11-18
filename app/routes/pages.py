from fastapi import APIRouter, Request

from routes.common import get_current_user, templates
from services.truelens_service import get_metadata

router = APIRouter()


@router.get("/", name="home")
def home(request: Request):
    metadata = get_metadata()
    return templates.TemplateResponse(
        request,
        "home.html",
        context={
            "active_page": "home",
            "current_user": get_current_user(request),
            "metadata": metadata,
            "metrics": metadata.get("evaluation", {}),
        },
    )


@router.get("/contact", name="contact")
def contact_page(request: Request):
    team_roles = [
        {
            "code": "A1",
            "role": "Anggota 1 · AI & Data Specialist",
            "focus": "Eksplorasi Dataset CIFAKE & Pelatihan EfficientNet-B0",
            "tasks": [
                "Mengunduh dan mempartisi 120.000 citra dataset CIFAKE (Train, Validation, Test).",
                "Menyusun pipeline prapemrosesan (224x224x3) dan melatih model EfficientNet-B0.",
                "Mengekspor paket inferensi PyTorch (ai_package) beserta metrik evaluasi.",
            ],
        },
        {
            "code": "A2",
            "role": "Anggota 2 · Backend Developer",
            "focus": "Arsitektur FastAPI, SQLModel, & Layanan Prediksi",
            "tasks": [
                "Membangun struktur app/ (config.py, main.py, models, schemas, services, routes).",
                "Mengintegrasikan sistem autentikasi Session (Login, Register, Logout) & Predictor AI.",
                "Menyediakan operasi Create, Read, dan Delete ke PostgreSQL menggunakan SQLModel.",
            ],
        },
        {
            "code": "A3",
            "role": "Anggota 3 · Frontend Developer",
            "focus": "Antarmuka Jinja2, CSS Responsif, & Interaksi JavaScript",
            "tasks": [
                "Merancang halaman Beranda, Pindai, Hasil, Riwayat, Kontak, Login, dan Register berbasis Jinja2.",
                "Membangun komponen dropzone interaktif dengan pratinjau gambar langsung.",
                "Memvisualisasikan meter keyakinan dan skala probabilitas 4 rentang.",
            ],
        },
        {
            "code": "A4",
            "role": "Anggota 4 · Database & QA Lead",
            "focus": "Administrasi PostgreSQL & Pengujian Fungsional",
            "tasks": [
                "Merancang tabel users dan scan_history di PostgreSQL (db/query_truelens.txt).",
                "Menguji seluruh alur autentikasi, unggah gambar, simpan riwayat, filter, dan hapus data.",
                "Menyusun laporan PDF proyek dan dokumentasi pengujian.",
            ],
        },
    ]
    return templates.TemplateResponse(
        request,
        "contact.html",
        context={
            "active_page": "contact",
            "current_user": get_current_user(request),
            "team_roles": team_roles,
        },
    )

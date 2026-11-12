import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from config import get_session, UPLOAD_DIR
from schemas.truelens_schema import TrueLensData
from services.truelens_service import (
    get_metadata,
    get_history,
    analyze_uploaded_image,
    save_prediction,
    delete_prediction,
    verify_image_magic_bytes,
    format_id_number,
)
from models.truelens_model import Prediction_history

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


@router.get("/", name="home")
def home(request: Request):
    metadata = get_metadata()
    return templates.TemplateResponse(
        request,
        "home.html",
        context={
            "active_page": "home",
            "metadata": metadata,
            "metrics": metadata.get("evaluation", {}),
        },
    )


@router.get("/scan", name="scan")
@router.get("/predictions/create", name="predictions_create")
def new_predictions(request: Request):
    return templates.TemplateResponse(
        request,
        name="scan.html",
        context={
            "active_page": "scan",
            "error_message": None,
        },
    )


@router.post("/predict", name="predict")
@router.post("/predictions/create")
async def create_prediction(
    request: Request,
    file: UploadFile | None = File(default=None),
):
    if file is None or not file.filename:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "error_message": "Pilih satu file gambar."},
            status_code=400,
        )

    original_filename = Path(file.filename).name
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "error_message": "Format harus JPG, JPEG, atau PNG."},
            status_code=400,
        )

    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "error_message": "Ukuran file melebihi 10 MB."},
            status_code=400,
        )

    detected_ext = verify_image_magic_bytes(content)
    if detected_ext is None:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "error_message": "Isi file tidak cocok dengan format gambar yang didukung."},
            status_code=400,
        )

    safe_name = f"scan_{uuid.uuid4().hex[:16]}{detected_ext}"
    saved_path = UPLOAD_DIR / safe_name
    saved_path.write_bytes(content)
    relative_image_path = f"static/uploads/{safe_name}"

    analysis = analyze_uploaded_image(saved_path)
    scan_timestamp = datetime.now().strftime("%d %b %Y, %H:%M WIB")

    return templates.TemplateResponse(
        request,
        name="result.html",
        context={
            "active_page": "scan",
            "filename": original_filename,
            "image_path": relative_image_path,
            "scan_timestamp": scan_timestamp,
            "analysis": analysis,
            "is_preview_demo": False,
        },
    )


@router.post("/history/save", name="history_save")
def history_save(
    filename: str = Form(...),
    image_path: str = Form(""),
    file_size_kb: float = Form(0.0),
    resolution: str = Form("Unknown"),
    predicted_label: str = Form(...),
    risk_tier: str = Form(...),
    confidence_score: float = Form(...),
    raw_prob: float = Form(...),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    data = TrueLensData(
        filename=filename,
        image_path=image_path,
        file_size_kb=file_size_kb,
        resolution=resolution,
        predicted_label="AI-Generated" if predicted_label == "AI-Generated" else "Real",
        risk_tier=risk_tier,
        confidence_score=confidence_score,
        raw_prob=raw_prob,
        notes=notes.strip() if notes else None,
    )
    save_prediction(session, data)
    return RedirectResponse(url="/history?msg=saved", status_code=303)


@router.get("/history", name="history")
@router.get("/predictions", name="predictions")
def predictions(
    request: Request,
    status: str = "all",
    date: str = "",
    msg: str = "",
    session: Session = Depends(get_session),
):
    raw_records = get_history(session, status=status)
    formatted_items = []
    for item in raw_records:
        if date.strip():
            if item.created_at.strftime("%Y-%m-%d") != date.strip():
                continue
        formatted_items.append(
            {
                "id": item.id,
                "filename": item.filename,
                "image_path": item.image_path,
                "file_size_display": f"{format_id_number(item.file_size_kb, 1)} KB",
                "resolution": item.resolution,
                "predicted_label": item.predicted_label,
                "risk_tier": item.risk_tier,
                "confidence_score": item.confidence_score,
                "confidence_display": format_id_number(item.confidence_score, 1),
                "raw_prob_display": format_id_number(item.raw_prob, 3),
                "notes": item.notes or "",
                "is_sample": item.is_sample,
                "created_display": item.created_at.strftime("%d %b %Y · %H:%M"),
            }
        )

    flash_message = None
    if msg == "saved":
        flash_message = "Pemindaian disimpan ke riwayat."
    elif msg == "deleted":
        flash_message = "Entri riwayat dihapus."

    return templates.TemplateResponse(
        request,
        "history.html",
        context={
            "active_page": "history",
            "records": formatted_items,
            "total_all_count": len(raw_records),
            "current_status": status,
            "current_date": date,
            "filter_error": None,
            "flash_message": flash_message,
        },
    )


@router.get("/predictions/delete/{id}", name="prediction_delete_get")
def prediction_delete_get(id: int, session: Session = Depends(get_session)):
    delete_prediction(session, id)
    return RedirectResponse(url="/history?msg=deleted", status_code=303)


@router.get("/history/{record_id}/delete", name="confirm_delete")
def confirm_delete_page(request: Request, record_id: int, session: Session = Depends(get_session)):
    record = session.get(Prediction_history, record_id)
    if not record:
        return RedirectResponse(url="/history", status_code=303)
    return templates.TemplateResponse(
        request,
        "confirm_delete.html",
        context={
            "active_page": "history",
            "record": {
                "id": record.id,
                "filename": record.filename,
                "image_path": record.image_path,
                "predicted_label": record.predicted_label,
                "risk_tier": record.risk_tier,
                "confidence_display": format_id_number(record.confidence_score, 1),
                "raw_prob_display": format_id_number(record.raw_prob, 3),
                "is_sample": record.is_sample,
                "created_display": record.created_at.strftime("%d %b %Y · %H:%M"),
            },
        },
    )


@router.post("/history/{record_id}/delete", name="delete_history")
def prediction_delete_post(record_id: int, session: Session = Depends(get_session)):
    delete_prediction(session, record_id)
    return RedirectResponse(url="/history?msg=deleted", status_code=303)


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
                "Mengekspor bobot model terlatih dan json metrik evaluasi (Accuracy, Precision, Recall, F1).",
            ],
        },
        {
            "code": "A2",
            "role": "Anggota 2 · Backend Developer",
            "focus": "Arsitektur FastAPI, SQLModel, & Layanan Prediksi",
            "tasks": [
                "Membangun struktur app/ (config.py, main.py, models, schemas, services, routes).",
                "Mengintegrasikan layanan inferensi gambar dengan model EfficientNet-B0.",
                "Menyediakan operasi Create, Read, dan Delete ke PostgreSQL menggunakan SQLModel.",
            ],
        },
        {
            "code": "A3",
            "role": "Anggota 3 · Frontend Developer",
            "focus": "Antarmuka Jinja2, CSS Responsif, & Interaksi JavaScript",
            "tasks": [
                "Merancang halaman Beranda, Pindai, Hasil, Riwayat, dan Kontak berbasis Jinja2.",
                "Membangun komponen dropzone interaktif dengan pratinjau gambar langsung.",
                "Memvisualisasikan meter keyakinan dan skala probabilitas 4 rentang.",
            ],
        },
        {
            "code": "A4",
            "role": "Anggota 4 · Database & QA Lead",
            "focus": "Administrasi PostgreSQL & Pengujian Fungsional",
            "tasks": [
                "Merancang tabel scan_history di PostgreSQL (db/query_truelens.txt).",
                "Menguji seluruh alur unggah gambar, simpan riwayat, filter, dan hapus data.",
                "Menyusun laporan PDF proyek dan dokumentasi pengujian.",
            ],
        },
    ]
    return templates.TemplateResponse(
        request,
        "contact.html",
        context={"active_page": "contact", "team_roles": team_roles},
    )

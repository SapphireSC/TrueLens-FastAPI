import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session

from config import get_session, UPLOAD_DIR
from schemas.truelens_schema import TrueLensData, UserRegister
from services.truelens_service import (
    get_metadata,
    get_history,
    analyze_uploaded_image,
    save_prediction,
    delete_prediction,
    verify_image_magic_bytes,
    format_id_number,
    register_user,
    authenticate_user,
)
from models.truelens_model import Prediction_history

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def get_current_user(request: Request) -> dict | None:
    return request.session.get("user")


# =====================================================================
# RUTE AUTENTIKASI (COCOK DENGAN TEMPLATE LOGIN.HTML, REGISTER.HTML, BASE.HTML)
# =====================================================================
@router.get("/login", name="login")
def login_page(request: Request, msg: str = ""):
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    success_msg = None
    if msg == "registered":
        success_msg = "Registrasi berhasil! Silakan masuk dengan akun Anda."
    elif msg == "logged_out":
        success_msg = "Anda telah berhasil keluar."
    elif msg == "login_required":
        success_msg = "Silakan masuk terlebih dahulu untuk mengakses fitur tersebut."
    return templates.TemplateResponse(
        request,
        "login.html",
        context={
            "active_page": "login",
            "current_user": None,
            "error": None,
            "success_message": success_msg,
        },
    )


@router.post("/login", name="login_post")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    user = authenticate_user(session, username, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "login.html",
            context={
                "active_page": "login",
                "current_user": None,
                "error": "Username atau password tidak sesuai.",
                "success_message": None,
                "username_val": username,
            },
            status_code=400,
        )

    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }
    return RedirectResponse(url="/scan", status_code=303)


@router.get("/register", name="register")
def register_page(request: Request):
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request,
        "register.html",
        context={
            "active_page": "register",
            "current_user": None,
            "error": None,
        },
    )


@router.post("/register", name="registers_post")
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    if len(password) < 4:
        return templates.TemplateResponse(
            request,
            "register.html",
            context={
                "active_page": "register",
                "current_user": None,
                "error": "Password minimal terdiri dari 4 karakter.",
                "username_val": username,
                "email_val": email,
            },
            status_code=400,
        )

    try:
        data = UserRegister(username=username, email=email, password=password)
        register_user(session, data)
        return RedirectResponse(url="/login?msg=registered", status_code=303)
    except ValueError as err:
        return templates.TemplateResponse(
            request,
            "register.html",
            context={
                "active_page": "register",
                "current_user": None,
                "error": str(err),
                "username_val": username,
                "email_val": email,
            },
            status_code=400,
        )


@router.post("/logout", name="logout")
@router.get("/logout")
def logout_user(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login?msg=logged_out", status_code=303)


# =====================================================================
# RUTE UTAMA, PEMINDAIAN, & RIWAYAT CRUD
# =====================================================================
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


@router.get("/scan", name="scan")
@router.get("/predictions/create", name="predictions_create")
def new_predictions(request: Request):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login?msg=login_required", status_code=303)
    return templates.TemplateResponse(
        request,
        name="scan.html",
        context={
            "active_page": "scan",
            "current_user": current_user,
            "error_message": None,
        },
    )


@router.post("/predict", name="predict")
@router.post("/predictions/create")
async def create_prediction(
    request: Request,
    file: UploadFile | None = File(default=None),
):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login?msg=login_required", status_code=303)

    if file is None or not file.filename:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "current_user": current_user, "error_message": "Pilih satu file gambar."},
            status_code=400,
        )

    original_filename = Path(file.filename).name
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "current_user": current_user, "error_message": "Format harus JPG, JPEG, atau PNG."},
            status_code=400,
        )

    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "current_user": current_user, "error_message": "Ukuran file melebihi 10 MB."},
            status_code=400,
        )

    detected_ext = verify_image_magic_bytes(content)
    if detected_ext is None:
        return templates.TemplateResponse(
            request,
            name="scan.html",
            context={"active_page": "scan", "current_user": current_user, "error_message": "Isi file tidak cocok dengan format gambar yang didukung."},
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
            "current_user": current_user,
            "filename": original_filename,
            "image_path": relative_image_path,
            "scan_timestamp": scan_timestamp,
            "analysis": analysis,
            "is_preview_demo": False,
        },
    )


@router.post("/history/save", name="history_save")
def history_save(
    request: Request,
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
    if not get_current_user(request):
        return RedirectResponse(url="/login?msg=login_required", status_code=303)

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
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login?msg=login_required", status_code=303)

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
            "current_user": current_user,
            "records": formatted_items,
            "total_all_count": len(raw_records),
            "current_status": status,
            "current_date": date,
            "filter_error": None,
            "flash_message": flash_message,
        },
    )


@router.get("/predictions/delete/{id}", name="prediction_delete_get")
def prediction_delete_get(request: Request, id: int, session: Session = Depends(get_session)):
    if not get_current_user(request):
        return RedirectResponse(url="/login?msg=login_required", status_code=303)
    delete_prediction(session, id)
    return RedirectResponse(url="/history?msg=deleted", status_code=303)


@router.get("/history/{record_id}/delete", name="confirm_delete")
def confirm_delete_page(request: Request, record_id: int, session: Session = Depends(get_session)):
    current_user = get_current_user(request)
    if not current_user:
        return RedirectResponse(url="/login?msg=login_required", status_code=303)
    record = session.get(Prediction_history, record_id)
    if not record:
        return RedirectResponse(url="/history", status_code=303)
    return templates.TemplateResponse(
        request,
        "confirm_delete.html",
        context={
            "active_page": "history",
            "current_user": current_user,
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
def prediction_delete_post(request: Request, record_id: int, session: Session = Depends(get_session)):
    if not get_current_user(request):
        return RedirectResponse(url="/login?msg=login_required", status_code=303)
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

import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import RedirectResponse

from config import UPLOAD_DIR
from routes.common import get_current_user, templates
from services.truelens_service import analyze_uploaded_image, verify_image_magic_bytes

router = APIRouter()

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}


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

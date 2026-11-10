import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from app.config import UPLOAD_DIR, MAX_UPLOAD_SIZE_BYTES, ALLOWED_EXTENSIONS
from app.services.scan_engine import verify_image_magic_bytes, TrueLensScanEngine

router = APIRouter()


@router.get("/scan", response_class=HTMLResponse, name="scan")
async def scan_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        request,
        "scan.html",
        {
            "active_page": "scan",
            "error_message": None,
        },
    )


@router.post("/predict", response_class=HTMLResponse, name="predict")
async def predict_image(request: Request, file: UploadFile | None = File(default=None)):
    # 1. Validasi keberadaan file
    if file is None or not file.filename:
        return request.app.state.templates.TemplateResponse(
            request,
            "scan.html",
            {
                "active_page": "scan",
                "error_message": "Pilih satu file gambar.",
            },
            status_code=400,
        )

    original_filename = Path(file.filename).name
    ext = Path(original_filename).suffix.lower()

    # 2. Validasi ekstensi
    if ext not in ALLOWED_EXTENSIONS:
        return request.app.state.templates.TemplateResponse(
            request,
            "scan.html",
            {
                "active_page": "scan",
                "error_message": "Format harus JPG, JPEG, atau PNG.",
            },
            status_code=400,
        )

    # 3. Validasi ukuran file (baca maks 10 MB + 1 byte)
    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        return request.app.state.templates.TemplateResponse(
            request,
            "scan.html",
            {
                "active_page": "scan",
                "error_message": "Ukuran file melebihi 10 MB.",
            },
            status_code=400,
        )

    # 4. Validasi magic bytes PNG / JPEG
    detected_ext = verify_image_magic_bytes(content)
    if detected_ext is None:
        return request.app.state.templates.TemplateResponse(
            request,
            "scan.html",
            {
                "active_page": "scan",
                "error_message": "Isi file tidak cocok dengan format gambar yang didukung.",
            },
            status_code=400,
        )

    # 5. Simpan file gambar dengan nama token UUID yang aman
    safe_token_name = f"scan_{uuid.uuid4().hex[:16]}{detected_ext}"
    saved_path = UPLOAD_DIR / safe_token_name
    saved_path.write_bytes(content)
    relative_image_path = f"static/uploads/{safe_token_name}"

    # 6. Jalankan inferensi melalui TrueLensScanEngine
    scan_engine: TrueLensScanEngine = request.app.state.scan_engine
    analysis = scan_engine.analyze_image(saved_path)

    scan_timestamp = datetime.now().strftime("%d %b %Y, %H:%M WIB")

    return request.app.state.templates.TemplateResponse(
        request,
        "result.html",
        {
            "active_page": "scan",
            "filename": original_filename,
            "image_path": relative_image_path,
            "scan_timestamp": scan_timestamp,
            "analysis": analysis,
            "is_preview_demo": False,
        },
    )


@router.get("/preview/result", response_class=HTMLResponse, name="preview_result")
async def preview_result_page(request: Request, p: float = 0.912):
    """Endpoint pratinjau hasil untuk kebutuhan pengujian UI & screenshot."""
    analysis = TrueLensScanEngine.map_probability_to_result(p)
    analysis.update(
        {
            "resolution": "1024x1024",
            "file_size_kb": 540.0,
            "file_size_display": "540,0 KB",
            "inference_mode": "Contoh Pratinjau UI",
            "is_live_model": False,
        }
    )
    return request.app.state.templates.TemplateResponse(
        request,
        "result.html",
        {
            "active_page": "scan",
            "filename": "contoh_visual_synthesizer.png",
            "image_path": "",
            "scan_timestamp": datetime.now().strftime("%d %b %Y, %H:%M WIB"),
            "analysis": analysis,
            "is_preview_demo": True,
        },
    )

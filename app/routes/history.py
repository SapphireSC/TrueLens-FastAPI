from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.config import APP_DIR, UPLOAD_DIR
from app.database import get_db
from app.models import ScanHistory
from app.services.scan_engine import format_id_number
from app.routes.auth import get_current_user

router = APIRouter()


@router.get("/history", response_class=HTMLResponse, name="history")
async def view_history(
    request: Request,
    status: str = "all",
    date: str = "",
    msg: str = "",
    db: Session = Depends(get_db),
):
    current_user = get_current_user(request, db)
    stmt = select(ScanHistory).order_by(ScanHistory.created_at.desc(), ScanHistory.id.desc())
    filter_error = None

    if current_user:
        stmt = stmt.where(ScanHistory.user_id == current_user.id)
    else:
        stmt = stmt.where(ScanHistory.is_sample == True)

    if status in ("Real", "AI-Generated"):
        stmt = stmt.where(ScanHistory.predicted_label == status)
    elif status not in ("all", ""):
        status = "all"

    if date.strip():
        try:
            parsed_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
            start_dt = datetime.combine(parsed_date, datetime.min.time())
            end_dt = datetime.combine(parsed_date, datetime.max.time())
            stmt = stmt.where(ScanHistory.created_at >= start_dt, ScanHistory.created_at <= end_dt)
        except ValueError:
            filter_error = "Format tanggal filter tidak valid. Gunakan format YYYY-MM-DD."

    records = db.scalars(stmt).all()
    total_all_count = db.query(ScanHistory).count()

    formatted_items = []
    for item in records:
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

    return request.app.state.templates.TemplateResponse(
        request,
        "history.html",
        {
            "active_page": "history",
            "records": formatted_items,
            "total_all_count": total_all_count,
            "current_status": status,
            "current_date": date,
            "filter_error": filter_error,
            "flash_message": flash_message,
            "current_user": get_current_user(request, db),
        },
    )


@router.post("/history/save", name="history_save")
async def save_scan_to_history(
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
    db: Session = Depends(get_db),
):
    """Operasi CREATE (Soal Nomor 4 UAS): Menyimpan data input & hasil AI ke database."""
    current_user = get_current_user(request, db)
    clean_label = "AI-Generated" if predicted_label == "AI-Generated" else "Real"
    new_entry = ScanHistory(
        filename=Path(filename).name[:255],
        image_path=image_path[:255],
        file_size_kb=float(file_size_kb),
        resolution=resolution[:50],
        predicted_label=clean_label,
        risk_tier=risk_tier[:80],
        confidence_score=round(float(confidence_score), 2),
        raw_prob=round(float(raw_prob), 4),
        notes=notes.strip()[:500] if notes else None,
        is_sample=False,
        user_id=current_user.id if current_user else None,
        created_at=datetime.now(),
    )
    db.add(new_entry)
    db.commit()
    return RedirectResponse(url="/history?msg=saved", status_code=303)


@router.get("/history/{record_id}/delete", response_class=HTMLResponse, name="confirm_delete")
async def confirm_delete_page(
    request: Request,
    record_id: int,
    db: Session = Depends(get_db),
):
    record = db.get(ScanHistory, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Data riwayat pemindaian tidak ditemukan.")

    return request.app.state.templates.TemplateResponse(
        request,
        "confirm_delete.html",
        {
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
            "current_user": get_current_user(request, db),
        },
    )


@router.post("/history/{record_id}/delete", name="delete_history")
async def delete_history_entry(
    record_id: int,
    db: Session = Depends(get_db),
):
    """Operasi DELETE (Soal Nomor 4 UAS): Menghapus record dari database beserta file fisik di server."""
    record = db.get(ScanHistory, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Data riwayat tidak ditemukan.")

    if record.image_path:
        try:
            candidate_path = (APP_DIR / record.image_path).resolve()
            upload_root = UPLOAD_DIR.resolve()
            if str(candidate_path).startswith(str(upload_root)) and candidate_path.is_file():
                candidate_path.unlink()
        except Exception as exc:
            print(f"[Delete Warning] Gagal menghapus file fisik: {exc}")

    db.delete(record)
    db.commit()
    return RedirectResponse(url="/history?msg=deleted", status_code=303)

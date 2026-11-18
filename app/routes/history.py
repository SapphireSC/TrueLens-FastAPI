from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from config import get_session
from models.truelens_model import Prediction_history
from routes.common import get_current_user, templates
from schemas.truelens_schema import TrueLensData
from services.truelens_service import (
    delete_prediction,
    format_id_number,
    get_history,
    save_prediction,
)

router = APIRouter()


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

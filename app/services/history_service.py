from sqlmodel import Session, select

from config import UPLOAD_DIR
from models.truelens_model import Prediction_history
from schemas.truelens_schema import TrueLensData


def get_history(session: Session, status: str = "all"):
    statement = select(Prediction_history).order_by(Prediction_history.created_at.desc())
    if status in ("Real", "AI-Generated"):
        statement = statement.where(Prediction_history.predicted_label == status)
    return session.exec(statement).all()


def save_prediction(session: Session, data: TrueLensData):
    record = Prediction_history(
        filename=data.filename,
        image_path=data.image_path,
        file_size_kb=data.file_size_kb,
        resolution=data.resolution,
        predicted_label=data.predicted_label,
        risk_tier=data.risk_tier,
        confidence_score=data.confidence_score,
        raw_prob=data.raw_prob,
        notes=data.notes,
        is_sample=False,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def delete_prediction(session: Session, id: int):
    prediction = session.get(Prediction_history, id)
    if not prediction:
        return None

    if prediction.image_path:
        try:
            candidate = (UPLOAD_DIR.parent / prediction.image_path).resolve()
            if str(candidate).startswith(str(UPLOAD_DIR.resolve())) and candidate.is_file():
                candidate.unlink()
        except Exception:
            pass

    session.delete(prediction)
    session.commit()
    return prediction

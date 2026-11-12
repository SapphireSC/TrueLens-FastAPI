from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class Prediction_history(SQLModel, table=True):
    __tablename__ = "scan_history"

    id: int | None = Field(default=None, primary_key=True)
    filename: str
    image_path: str = Field(default="")
    file_size_kb: float = Field(default=0.0)
    resolution: str = Field(default="Unknown")
    predicted_label: str
    risk_tier: str
    confidence_score: float
    raw_prob: float
    notes: str | None = Field(default=None)
    is_sample: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

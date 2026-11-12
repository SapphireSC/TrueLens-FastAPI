from sqlmodel import SQLModel, Field


class TrueLensData(SQLModel):
    filename: str
    image_path: str = ""
    file_size_kb: float = Field(ge=0)
    resolution: str = "Unknown"
    predicted_label: str
    risk_tier: str
    confidence_score: float = Field(ge=0)
    raw_prob: float = Field(ge=0)
    notes: str | None = None

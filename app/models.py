from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Text, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ScanHistory(Base):
    """
    Model ORM SQLAlchemy 2.0 untuk tabel `scan_history` (Pemenuhan Soal Nomor 3 & 4 UAS).
    """
    __tablename__ = "scan_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    image_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    file_size_kb: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    resolution: Mapped[str] = mapped_column(String(50), nullable=False, default="Unknown")
    predicted_label: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    risk_tier: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    raw_prob: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)


class User(Base):
    """
    Model ORM SQLAlchemy 2.0 untuk tabel `users` (akun sistem).
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)

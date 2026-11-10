"""
TrueLens AI - Scanning & Detection Engine
Menangani validasi magic bytes gambar, prapemrosesan (224x224x3),
inferensi model Keras EfficientNet-B0, serta fallback deterministik berbasis SHA-256
apabila bobot model (.keras) belum selesai dilatih di mesin lokal.
"""
import os
import hashlib
from pathlib import Path
from PIL import Image
import numpy as np


def verify_image_magic_bytes(data: bytes) -> str | None:
    """Memastikan isi biner file benar-benar gambar JPEG atau PNG (bukan sekadar ekstensi)."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    return None


def format_id_number(value: float, decimals: int = 2) -> str:
    """Format angka desimal dengan pemisah koma khas Indonesia (contoh: 88,70)."""
    return f"{value:.{decimals}f}".replace(".", ",")


class TrueLensScanEngine:
    def __init__(self, model_path: str | Path):
        self.model_path = Path(model_path)
        self.model = None
        self.tf_preprocess = None
        self.is_live_model = False
        self._load_model_if_available()

    def _load_model_if_available(self):
        if self.model_path.exists():
            try:
                import tensorflow as tf
                from tensorflow.keras.applications.efficientnet import preprocess_input

                self.model = tf.keras.models.load_model(str(self.model_path))
                self.tf_preprocess = preprocess_input
                self.is_live_model = True
                print(f"[TrueLensScanEngine] Model AI berhasil dimuat dari: {self.model_path}")
            except Exception as exc:
                print(f"[TrueLensScanEngine] Gagal memuat model Keras ({exc}). Beralih ke mode simulasi deterministik.")
        else:
            print(
                f"[TrueLensScanEngine] File model belum ditemukan di {self.model_path}. "
                "Menjalankan mode pratinjau deterministik berbasis SHA-256."
            )

    @staticmethod
    def map_probability_to_result(raw_prob: float) -> dict:
        """
        Memetakan skor probabilitas Sigmoid p ∈ [0.0, 1.0] ke label database,
        Confidence Score (%), dan 4 rentang interpretasi tampilan.
        """
        raw_prob = max(0.001, min(0.999, float(raw_prob)))

        if raw_prob >= 0.50:
            predicted_label = "AI-Generated"
            confidence_score = round(raw_prob * 100.0, 2)
        else:
            predicted_label = "Real"
            confidence_score = round((1.0 - raw_prob) * 100.0, 2)

        if raw_prob < 0.30:
            tier_code = "authentic"
            risk_tier = "Citra asli (Authentic Real Image)"
            tier_desc = "Indikasi sangat kuat foto asli dari sensor kamera optik; distribusi piksel alami."
        elif raw_prob < 0.50:
            tier_code = "likely_real"
            risk_tier = "Cenderung asli (Likely Real Image)"
            tier_desc = "Cenderung foto asli dengan sedikit noise atau jejak kompresi JPEG."
        elif raw_prob < 0.75:
            tier_code = "likely_ai"
            risk_tier = "Cenderung AI (Likely AI-Generated)"
            tier_desc = "Terdeteksi pola artefak sintetis tingkat sedang pada frekuensi spasial."
        else:
            tier_code = "synthetic"
            risk_tier = "Sintetis AI (Synthetic AI-Generated)"
            tier_desc = "Indikasi kuat gambar dibangkitkan oleh model kecerdasan buatan generatif."

        return {
            "predicted_label": predicted_label,
            "confidence_score": confidence_score,
            "confidence_display": format_id_number(confidence_score, 1),
            "raw_prob": round(raw_prob, 4),
            "raw_prob_display": format_id_number(raw_prob, 3),
            "marker_percent": round(raw_prob * 100.0, 1),
            "tier_code": tier_code,
            "risk_tier": risk_tier,
            "tier_desc": tier_desc,
        }

    def analyze_image(self, file_path: str | Path) -> dict:
        file_path = Path(file_path)
        file_size_kb = round(file_path.stat().st_size / 1024.0, 2)

        with Image.open(file_path) as img:
            width, height = img.size
            img_rgb = img.convert("RGB").resize((224, 224), Image.Resampling.BICUBIC)
            arr = np.asarray(img_rgb, dtype=np.float32)

        if self.is_live_model and self.model is not None and self.tf_preprocess is not None:
            tensor = np.expand_dims(arr, axis=0)  # Shape: (1, 224, 224, 3)
            tensor = self.tf_preprocess(tensor)   # Rentang [0, 255] float32 sesuai EfficientNetB0
            raw_prob = float(self.model.predict(tensor, verbose=0)[0][0])
            inference_mode = "Model EfficientNet-B0 Aktif"
        else:
            # Simulasi deterministik dari hash SHA-256 isi file gambar
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
            int_val = int(digest[:8], 16)
            raw_prob = (int_val % 920 + 40) / 1000.0  # Rentang 0.040 - 0.959
            inference_mode = "Pratinjau Deterministik (Menunggu File .keras)"

        result = self.map_probability_to_result(raw_prob)
        result.update(
            {
                "resolution": f"{width}x{height}",
                "file_size_kb": file_size_kb,
                "file_size_display": f"{format_id_number(file_size_kb, 1)} KB",
                "inference_mode": inference_mode,
                "is_live_model": self.is_live_model,
            }
        )
        return result

import sys
import json
from pathlib import Path

from PIL import Image

from config import BASE_DIR
from services.common import format_id_number

PROJECT_ROOT = BASE_DIR.parent
MODEL_DIR = BASE_DIR / "model_ai"
AI_PACKAGE_V2_DIR = PROJECT_ROOT / "ai_package_v2" / "truelens-image-detector"
APP_THRESHOLD = 0.65  

if AI_PACKAGE_V2_DIR.exists() and str(AI_PACKAGE_V2_DIR) not in sys.path:
    sys.path.insert(0, str(AI_PACKAGE_V2_DIR))

from truelens_image_detector import ImageDetector, ImageInputError, ModelError


detector: ImageDetector | None = None
try:
    detector = ImageDetector(device="cpu")
    print(
        f"[TrueLens Service] Berhasil memuat {detector.model_id} v{detector.model_version} "
        f"(model_threshold={detector.threshold}, app_threshold={APP_THRESHOLD}) dari ai_package_v2"
    )
except Exception as exc:
    print(f"[TrueLens Service] GAGAL memuat ai_package_v2: {exc}")


def get_metadata() -> dict:
    with open(MODEL_DIR / "model_truelens_metadata.json", "r", encoding="utf-8") as file:
        return json.load(file)


def map_probability_to_result(raw_prob: float, threshold: float = APP_THRESHOLD) -> dict:
    raw_prob = max(0.0, min(1.0, float(raw_prob)))
    threshold_str = str(threshold).replace(".", ",")

    if raw_prob >= threshold:
        predicted_label = "AI-Generated"
        confidence_score = round(raw_prob * 100.0, 2)
    else:
        predicted_label = "Real"
        confidence_score = round((1.0 - raw_prob) * 100.0, 2)

    if raw_prob < 0.35:
        tier_code = "authentic"
        risk_tier = "Citra asli (Authentic Real Image)"
        tier_desc = "Indikasi sangat kuat foto asli dari sensor kamera optik; distribusi piksel alami."
    elif raw_prob < threshold:
        tier_code = "likely_real"
        risk_tier = "Cenderung asli (Likely Real Image)"
        tier_desc = (
            f"Skor di bawah ambang {threshold_str}; foto asli yang kemungkinan mengalami "
            "penyuntingan warna, filter, atau kompresi."
        )
    elif raw_prob < 0.80:
        tier_code = "likely_ai"
        risk_tier = "Cenderung AI (Likely AI-Generated)"
        tier_desc = f"Melewati ambang {threshold_str}; terdeteksi pola artefak sintetis tingkat sedang."
    else:
        tier_code = "synthetic"
        risk_tier = "Sintetis AI (Synthetic AI-Generated)"
        tier_desc = "Indikasi sangat kuat gambar dibangkitkan oleh model kecerdasan buatan generatif."

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


def analyze_uploaded_image(file_path: Path) -> dict:
    if detector is None:
        raise ModelError("Model ai_package_v2 belum termuat. Periksa instalasi PyTorch dan bobot model.")

    file_bytes = file_path.read_bytes()
    file_size_kb = round(len(file_bytes) / 1024.0, 2)

    with Image.open(file_path) as img:
        width, height = img.size

    pred_out = detector.predict_bytes(file_bytes)
    raw_prob = float(pred_out["fake_score"])
    threshold = APP_THRESHOLD  
    model_id = pred_out.get("model_id", "truelens-image-detector")
    model_ver = pred_out.get("model_version", "1.0.0")

    result = map_probability_to_result(raw_prob, threshold=threshold)
    result.update(
        {
            "resolution": f"{width}x{height}",
            "file_size_kb": file_size_kb,
            "file_size_display": f"{format_id_number(file_size_kb, 1)} KB",
            "model_id": model_id,
            "model_version": model_ver,
            "inference_mode": f"PyTorch EfficientNet-B0 ({model_id} v{model_ver}, Ambang {threshold})",
            "is_live_model": True,
        }
    )
    return result
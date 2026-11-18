import sys
import json
import hashlib
from pathlib import Path

from PIL import Image

from config import BASE_DIR
from services.common import format_id_number

PROJECT_ROOT = BASE_DIR.parent
MODEL_DIR = BASE_DIR / "model_ai"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AI_PACKAGE_DIR = PROJECT_ROOT / "ai_package"
predictor = None

if AI_PACKAGE_DIR.exists():
    try:
        from ai_package.truelens_inference import Predictor
        predictor = Predictor.from_package(AI_PACKAGE_DIR, device="cpu")
        print(f"[TrueLens Service] Berhasil memuat PyTorch Predictor asli dari: {AI_PACKAGE_DIR}")
    except Exception as e:
        print(f"[TrueLens Service] Info pemuatan ai_package ({e}). Menggunakan fallback deterministik.")


def get_metadata() -> dict:
    with open(MODEL_DIR / "model_truelens_metadata.json", "r", encoding="utf-8") as file:
        return json.load(file)


def map_probability_to_result(raw_prob: float, threshold: float = 0.55) -> dict:
    raw_prob = max(0.0001, min(0.9999, float(raw_prob)))

    if raw_prob >= threshold:
        predicted_label = "AI-Generated"
        confidence_score = round(raw_prob * 100.0, 2)
    else:
        predicted_label = "Real"
        confidence_score = round((1.0 - raw_prob) * 100.0, 2)

    if raw_prob < 0.30:
        tier_code = "authentic"
        risk_tier = "Citra asli (Authentic Real Image)"
        tier_desc = "Indikasi sangat kuat foto asli dari sensor kamera optik; distribusi piksel alami."
    elif raw_prob < threshold:
        tier_code = "likely_real"
        risk_tier = "Cenderung asli (Likely Real Image)"
        tier_desc = "Skor di bawah ambang batas 0,55; cenderung foto asli dengan sedikit noise/kompresi."
    elif raw_prob < 0.75:
        tier_code = "likely_ai"
        risk_tier = "Cenderung AI (Likely AI-Generated)"
        tier_desc = "Melewati ambang 0,55; terdeteksi pola artefak sintetis tingkat sedang."
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
    file_bytes = file_path.read_bytes()
    file_size_kb = round(len(file_bytes) / 1024.0, 2)

    with Image.open(file_path) as img:
        width, height = img.size

    if predictor is not None:
        pred_out = predictor.predict_bytes(file_bytes)
        raw_prob = float(pred_out["fake_score"])
        threshold = float(pred_out.get("decision_threshold", 0.55))
        model_ver = pred_out.get("model_version", "truelens-r2-epoch9-v1.0.0")
        inference_mode = f"PyTorch EfficientNet-B0 Aktif ({model_ver}, Ambang {threshold})"
        is_live = True
    else:
        digest = hashlib.sha256(file_bytes).hexdigest()
        int_val = int(digest[:8], 16)
        raw_prob = (int_val % 920 + 40) / 1000.0
        threshold = 0.55
        inference_mode = "Simulasi Deterministik (Instal torch & torchvision untuk mengaktifkan ai_package)"
        is_live = False

    result = map_probability_to_result(raw_prob, threshold=threshold)
    result.update(
        {
            "resolution": f"{width}x{height}",
            "file_size_kb": file_size_kb,
            "file_size_display": f"{format_id_number(file_size_kb, 1)} KB",
            "inference_mode": inference_mode,
            "is_live_model": is_live,
        }
    )
    return result

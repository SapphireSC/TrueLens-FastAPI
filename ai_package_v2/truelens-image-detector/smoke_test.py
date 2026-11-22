"""Synthetic fixture smoke test. Pass --device cpu or --device cuda."""
import argparse
import io
import json

from PIL import Image, features
import torch

from truelens_image_detector import ImageDetector, ImageInputError
from truelens_image_detector.predictor import MAX_BYTES, MAX_SIDE


def fixtures():
    picture = Image.new("RGB", (37, 23))
    picture.putdata([((x * 19) % 256, (x * 7) % 256, (x * 3 + x // 37) % 256)
                     for x in range(37 * 23)])
    exif = picture.getexif()
    exif[274] = 6

    def encode(image, fmt, **kwargs):
        out = io.BytesIO()
        image.save(out, format=fmt, **kwargs)
        return out.getvalue()

    return {
        "oriented_jpeg": encode(picture, "JPEG", exif=exif),
        "alpha_png": encode(picture.convert("RGBA"), "PNG"),
        "webp": encode(picture, "WEBP", lossless=True),
        "tiny_png": encode(Image.new("L", (1, 1), 173), "PNG"),
    }


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def smoke(device):
    torch.set_num_threads(2)
    check(features.check("webp"), "WebP capability")
    detector = ImageDetector(device=device)
    outputs = {}
    for name, data in fixtures().items():
        result = detector.predict_bytes(data)
        score = result["fake_score"]
        check(result == {"model_id": "truelens-image-detector", "model_version": "1.0.0",
                         "label": "FAKE" if score >= .5 else "REAL",
                         "fake_score": score, "threshold": .5}
              and 0 <= score <= 1, f"Public contract: {name}")
        outputs[name] = result

    wide = io.BytesIO()
    Image.new("RGB", (MAX_SIDE + 1, 1)).save(wide, "PNG")
    bitmap = io.BytesIO()
    Image.new("RGB", (2, 2)).save(bitmap, "BMP")
    crowded = io.BytesIO()
    Image.new("1", (5000, 4001)).save(crowded, "PNG")
    cases = [(b"", "invalid_input"), (b"invalid", "invalid_image"),
             (b"x" * (MAX_BYTES + 1), "file_too_large"),
             (wide.getvalue(), "dimensions_exceeded"), (crowded.getvalue(), "dimensions_exceeded"),
             (bitmap.getvalue(), "unsupported_format")]
    for data, code in cases:
        try:
            detector.predict_bytes(data)
        except ImageInputError as exc:
            check(exc.code == code, f"Expected {code}, got {exc.code}")
        else:
            raise AssertionError(f"Input unexpectedly accepted: {code}")

    again = detector.predict_bytes(fixtures()["tiny_png"])
    check(again == outputs["tiny_png"], "Repeat prediction on the same instance")
    return {"passed": True, "device": device, "checks": 12, "fixtures": outputs}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    print(json.dumps(smoke(args.device), indent=2, allow_nan=False))


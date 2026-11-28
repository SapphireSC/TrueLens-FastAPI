"""Read one local image and print an inference result as JSON."""
import argparse
import json
from pathlib import Path
import sys

from . import ImageDetector, ImageInputError, ModelError
from .predictor import MAX_BYTES


def main():
    parser = argparse.ArgumentParser(description="TrueLens Image Detector v1")
    parser.add_argument("image", type=Path)
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()
    try:
        with args.image.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        result = ImageDetector(device=args.device).predict_bytes(data)
    except (OSError, ImageInputError, ModelError) as exc:
        print(json.dumps({"error": getattr(exc, "code", type(exc).__name__),
                          "message": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())


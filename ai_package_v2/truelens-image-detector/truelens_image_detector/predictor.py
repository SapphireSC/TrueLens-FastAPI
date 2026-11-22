"""Local inference with the exported EfficientNet-B0 weights."""
import hashlib
import io
import json
import math
from pathlib import Path
import warnings

from PIL import Image, ImageFile, ImageOps
import torch
from torchvision.models import efficientnet_b0
from torchvision.transforms import CenterCrop, Compose, InterpolationMode, Normalize, Resize, ToTensor

MODEL_ID = "truelens-image-detector"
VERSION = "1.0.0"
THRESHOLD = 0.5
MAX_BYTES = 10 * 1024**2
MAX_PIXELS = 20_000_000
MAX_SIDE = 8192
FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
WEIGHTS = "truelens-image-detector-v1.pt"


class ImageInputError(ValueError):
    """Invalid image input with a stable error code."""
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


class ModelError(RuntimeError):
    """Model initialization or inference failed."""


def _decode(data):
    if not isinstance(data, bytes) or not data:
        raise ImageInputError("invalid_input", "Masukkan byte gambar yang tidak kosong.")
    if len(data) > MAX_BYTES:
        raise ImageInputError("file_too_large", "Ukuran gambar melebihi 10 MiB.")
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        raise ModelError("Pillow harus dikonfigurasi untuk menolak gambar terpotong.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as probe:
                if probe.format not in FORMATS:
                    raise ImageInputError("unsupported_format", "Format yang didukung adalah JPEG, PNG, dan WebP.")
                if probe.width * probe.height > MAX_PIXELS or max(probe.size) > MAX_SIDE:
                    raise ImageInputError("dimensions_exceeded", "Gambar melebihi batas piksel atau dimensi.")
                if getattr(probe, "n_frames", 1) != 1:
                    raise ImageInputError("unsupported_animation", "Gunakan gambar satu frame.")
                probe.verify()
            with Image.open(io.BytesIO(data)) as source:
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except ImageInputError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ImageInputError("dimensions_exceeded", "Gambar melebihi batas piksel.") from exc
    except (OSError, ValueError, SyntaxError, EOFError) as exc:
        raise ImageInputError("invalid_image", "Gambar rusak atau tidak dapat didekode.") from exc


class ImageDetector:
    """Load and verify a single model for repeated calls to predict_bytes."""
    model_id = MODEL_ID
    model_version = VERSION
    threshold = THRESHOLD

    def __init__(self, device="cpu"):
        try:
            self.device = torch.device(device)
            if self.device.type not in {"cpu", "cuda"} or (
                self.device.type == "cpu" and self.device.index is not None
            ):
                raise ValueError("Pilih cpu, cuda, atau cuda:N.")
            if self.device.type == "cuda" and (
                not torch.cuda.is_available() or
                (self.device.index is not None and self.device.index >= torch.cuda.device_count())
            ):
                raise ValueError("Perangkat CUDA yang diminta tidak tersedia.")
            root = Path(__file__).resolve().parent
            info = json.loads((root / "model_info.json").read_text(encoding="utf-8"))
            if (info["model_id"], info["model_version"], info["threshold"], info["weights"]["filename"]) != (
                MODEL_ID, VERSION, THRESHOLD, WEIGHTS
            ):
                raise ValueError("Identitas metadata tidak cocok.")
            # Hash the same bytes passed into torch.load.
            data = (root / "weights" / WEIGHTS).read_bytes()
            if hashlib.sha256(data).hexdigest() != info["weights"]["sha256"]:
                raise ValueError("Checksum bobot tidak cocok.")
            state = torch.load(io.BytesIO(data), map_location="cpu", weights_only=True)
            self._model = efficientnet_b0(weights=None)
            self._model.classifier[1] = torch.nn.Linear(self._model.classifier[1].in_features, 1)
            self._model.load_state_dict(state, strict=True)
            self._model.to(device=self.device, dtype=torch.float32).eval()
            self._transform = Compose([
                Resize(256, interpolation=InterpolationMode.BICUBIC),
                CenterCrop(224), ToTensor(),
                Normalize([.485, .456, .406], [.229, .224, .225]),
            ])
        except Exception as exc:
            raise ModelError(f"Gagal memuat {MODEL_ID} v{VERSION}: {exc}") from exc

    def predict_bytes(self, image_bytes):
        image = _decode(image_bytes)
        try:
            with torch.inference_mode():
                tensor = self._transform(image).unsqueeze(0).to(self.device)
                if self.device.type == "cuda":
                    with torch.autocast("cuda", dtype=torch.float16):
                        logit = self._model(tensor).reshape(())
                else:
                    # Explicitly use FP32 even if the caller enables CPU autocast.
                    with torch.autocast("cpu", enabled=False):
                        logit = self._model(tensor).reshape(())
                need_finite = torch.isfinite(logit).item()
                if not need_finite:
                    raise ValueError("Logit tidak finite.")
                score = torch.sigmoid(logit.float()).item()
                if not math.isfinite(score):
                    raise ValueError("Skor FAKE tidak finite.")
        except Exception as exc:
            raise ModelError(f"Inferensi {MODEL_ID} gagal: {exc}") from exc
        return {
            "model_id": self.model_id, "model_version": self.model_version,
            "label": "FAKE" if score >= self.threshold else "REAL",
            "fake_score": score, "threshold": self.threshold,
        }


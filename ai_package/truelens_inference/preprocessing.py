"""Decoder tunggal untuk audit, loader, dan predictor; tidak pernah menulis input."""
from __future__ import annotations

import io
import struct
import warnings
from pathlib import Path

from PIL import Image, ImageFile, ImageOps

from .common import sha256_bytes

DECODER_VERSION = "exif-rgb-white-v1"
SUPPORTED = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".bmp": "BMP", ".webp": "WEBP", ".tif": "TIFF", ".tiff": "TIFF", ".gif": "GIF"}


def decode_image(source):
    data = source if isinstance(source, bytes) else Path(source).read_bytes()
    if ImageFile.LOAD_TRUNCATED_IMAGES:
        raise RuntimeError("LOAD_TRUNCATED_IMAGES harus False")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(data)) as image:
            metadata = {"width": image.width, "height": image.height, "format": image.format,
                        "mode": image.mode, "frame_count": getattr(image, "n_frames", 1)}
            if metadata["frame_count"] != 1:
                raise ValueError("animated_or_multiframe_not_supported")
            image.load()
            image = ImageOps.exif_transpose(image)
            if "A" in image.getbands() or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
                image = Image.alpha_composite(background, rgba).convert("RGB")
            else:
                image = image.convert("RGB")
            return image.copy(), metadata


def pixel_hash(image):
    return sha256_bytes(struct.pack(">II", *image.size) + image.tobytes())


def build_transform():
    from torchvision.models import EfficientNet_B0_Weights
    return EfficientNet_B0_Weights.IMAGENET1K_V1.transforms()


def preprocessing_config():
    transform = build_transform()
    return {"decoder_version": DECODER_VERSION, "exif_transpose": True, "mode": "RGB",
            "alpha_background": "white", "grayscale": "convert_RGB", "animation": "reject",
            "resize_short_edge": transform.resize_size[0], "center_crop": transform.crop_size[0],
            "interpolation": transform.interpolation.name, "antialias": transform.antialias,
            "input_scale": [0, 1], "mean": transform.mean, "std": transform.std,
            "augmentation": None, "normalization_count": 1}

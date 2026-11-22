"""Public API for TrueLens Image Detector v1."""
from .predictor import ImageDetector, ImageInputError, ModelError

__all__ = ["ImageDetector", "ImageInputError", "ModelError"]


"""Satu aturan keputusan untuk predictor dan seleksi threshold; FAKE positif."""
import math
from numbers import Real


def validate_decision(config):
    threshold = config.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, Real) or not math.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Threshold harus finite dan 0 < threshold < 1")
    if config.get("positive_class") != "FAKE" or config.get("rule") != "score >= threshold":
        raise ValueError("Keputusan wajib score >= threshold menjadi FAKE")
    return {"threshold": float(threshold), "positive_class": "FAKE", "rule": "score >= threshold"}


def decide_score(fake_score, config):
    decision = validate_decision(config)
    if isinstance(fake_score, bool) or not isinstance(fake_score, Real) or not math.isfinite(fake_score) or not 0 <= fake_score <= 1:
        raise ValueError("Score FAKE harus finite dalam 0–1")
    return int(fake_score >= decision["threshold"])


def labels_from_scores(fake_scores, config):
    import numpy as np
    decision = validate_decision(config)
    scores = np.asarray(fake_scores, dtype=np.float64)
    if scores.ndim != 1 or not np.isfinite(scores).all() or not ((scores >= 0) & (scores <= 1)).all():
        raise ValueError("Score FAKE harus vektor finite dalam 0–1")
    return (scores >= decision["threshold"]).astype(np.int64)

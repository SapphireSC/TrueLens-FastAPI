from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

LABEL_MAP = {"name_to_index": {"REAL": 0, "FAKE": 1}, "index_to_name": {"0": "REAL", "1": "FAKE"}}


def now():
    return datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")


def new_run_id():
    return datetime.now(timezone(timedelta(hours=7))).strftime("%Y%m%d_%H%M%S_%f")


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")


def atomic_bytes(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def write_json(path, value):
    atomic_bytes(path, json_bytes(value))


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_text(path, text):
    atomic_bytes(path, text.encode("utf-8"))


def csv_bytes(rows, fields=None):
    rows = list(rows)
    fields = fields or (list(rows[0]) if rows else [])
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n", extrasaction="raise")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def write_csv(path, rows, fields=None):
    atomic_bytes(path, csv_bytes(rows, fields))


def read_csv(path):
    with Path(path).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def truth(value):
    return value is True or str(value).lower() in ("true", "1")


def safe_sample_path(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"Path sampel di luar dataset: {relative}")
    return path


def load_config(root):
    config = read_json(Path(root) / "configs/stages_1_4.json")
    if config["labels"] != LABEL_MAP["name_to_index"]:
        raise ValueError("Mapping wajib REAL=0, FAKE=1")
    return config

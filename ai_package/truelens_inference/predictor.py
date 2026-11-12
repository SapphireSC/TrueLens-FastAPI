"""Adapter paket: pemeriksaan integritas/input di sekitar pipeline penelitian asli."""
from __future__ import annotations

import io
import math
import warnings
from importlib.metadata import version
from pathlib import Path

import torch
from PIL import Image, ImageFile, UnidentifiedImageError

from .common import LABEL_MAP, file_hash, read_json
from .decision import decide_score, validate_decision
from .model import build_model
from .preprocessing import build_transform, decode_image, preprocessing_config


class PackageIntegrityError(ValueError):
    """Paket tidak lengkap, checksum salah, atau konfigurasi tidak kompatibel."""


class DeviceError(ValueError):
    """Perangkat diminta tidak valid/tersedia; tidak ada fallback diam-diam."""


class ImageInputError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(f'{code}: {message}')


def verify_package(package_dir):
    root = Path(package_dir).resolve()
    try:
        manifest = read_json(root / 'package_manifest.json')
        if manifest['schema_version'] != 1:
            raise PackageIntegrityError('Schema manifest paket tidak didukung')
        required = {'model.pt', 'model_config.json', 'preprocessing.json', 'label_map.json',
                    'decision_config.json', 'input_policy.json'}
        if not required.issubset(manifest['files']):
            raise PackageIntegrityError('Manifest paket kehilangan komponen wajib')
        for relative, entry in manifest['files'].items():
            path = (root / relative).resolve()
            if Path(relative).is_absolute() or not path.is_relative_to(root) or not path.is_file():
                raise PackageIntegrityError(f'Path paket tidak valid: {relative}')
            if path.stat().st_size != entry['bytes'] or file_hash(path) != entry['sha256']:
                raise PackageIntegrityError(f'Checksum paket berbeda: {relative}')
        if manifest['files']['model.pt']['sha256'] != manifest['model_sha256']:
            raise PackageIntegrityError('Identitas model berbeda')
        for name, expected in manifest['runtime_versions'].items():
            # CPU wheels dan CUDA wheels boleh berbeda local suffix, bukan versi publik.
            if version(name).split('+')[0] != expected.split('+')[0]:
                raise PackageIntegrityError(f'Versi {name} berbeda; gunakan dependency yang didokumentasikan')
        return root, manifest
    except PackageIntegrityError:
        raise
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise PackageIntegrityError(f'Paket gagal diverifikasi: {error}') from error


def select_device(device):
    try:
        selected = torch.device(device)
    except (TypeError, RuntimeError, ValueError) as error:
        raise DeviceError(f'Perangkat tidak valid: {device}') from error
    if selected.type not in ('cpu', 'cuda'):
        raise DeviceError('Perangkat didukung: cpu atau cuda[:index]')
    if selected.type == 'cpu' and selected.index is not None:
        raise DeviceError('Gunakan device="cpu" tanpa index')
    if selected.type == 'cuda':
        if not torch.cuda.is_available():
            raise DeviceError('CUDA diminta tetapi tidak tersedia; pilih device="cpu" secara eksplisit')
        if selected.index is not None and selected.index >= torch.cuda.device_count():
            raise DeviceError('Index CUDA tidak tersedia')
    return selected


class Predictor:
    """Buat sekali saat startup; setiap predict tidak memuat bobot lagi."""
    @classmethod
    def from_package(cls, package_dir, device='cpu', *, max_pixels=None, max_dimension=None):
        root, manifest = verify_package(package_dir)
        selected = select_device(device)
        config = read_json(root / 'model_config.json')
        if (config['architecture'], config['output_logits'], config['dropout'], config['in_features']) != ('efficientnet_b0', 1, .2, 1280):
            raise PackageIntegrityError('Arsitektur/head paket berbeda')
        if read_json(root / 'label_map.json') != LABEL_MAP:
            raise PackageIntegrityError('Mapping label paket berbeda')
        if read_json(root / 'preprocessing.json') != preprocessing_config():
            raise PackageIntegrityError('Preprocessing paket berbeda dari implementasi')
        decision = validate_decision(read_json(root / 'decision_config.json'))
        if decision['threshold'] != .55 or manifest['decision_threshold'] != .55:
            raise PackageIntegrityError('Threshold kandidat wajib 0,55')
        policy = read_json(root / 'input_policy.json')
        if policy['max_file_bytes'] != 10 * 1024 * 1024 or policy['formats'] != ['JPEG', 'PNG']:
            raise PackageIntegrityError('Kontrak format/ukuran paket berbeda')
        for name, override in (('max_pixels', max_pixels), ('max_dimension', max_dimension)):
            value = policy[name] if override is None else override
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f'{name} harus integer positif')
            policy[name] = value
        if not Image.MAX_IMAGE_PIXELS or policy['max_pixels'] > Image.MAX_IMAGE_PIXELS:
            raise ValueError('max_pixels tidak boleh melebihi pengaman Pillow yang aktif')
        self = cls()
        self.package_dir, self.manifest, self.device = root, manifest, selected
        self.decision_config, self.threshold, self.input_policy = decision, decision['threshold'], policy
        self.model_version = manifest['model_version']
        self.preprocessing_version = manifest['preprocessing_version']
        self.model = build_model(pretrained=False)
        state = torch.load(root / 'model.pt', map_location=selected, weights_only=True)
        self.model.to(selected)
        self.model.load_state_dict(state, strict=True)
        self.model.eval()
        self.transform = build_transform()
        return self

    def _validate_input(self, data):
        if not isinstance(data, bytes):
            raise ImageInputError('invalid_type', 'Input harus bytes')
        if not data:
            raise ImageInputError('empty_file', 'Gambar kosong')
        if len(data) > self.input_policy['max_file_bytes']:
            raise ImageInputError('file_too_large', 'Maksimum file 10 MiB (10.485.760 byte)')
        if ImageFile.LOAD_TRUNCATED_IMAGES:
            raise RuntimeError('LOAD_TRUNCATED_IMAGES harus False')
        try:
            with warnings.catch_warnings():
                warnings.simplefilter('error', Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as image:
                    if getattr(image, 'n_frames', 1) != 1:
                        raise ImageInputError('animated_image', 'Gambar animasi/multiframe tidak didukung')
                    if image.format not in self.input_policy['formats']:
                        raise ImageInputError('unsupported_format', 'Isi file wajib JPEG atau PNG statis')
                    if image.width * image.height > self.input_policy['max_pixels'] or max(image.size) > self.input_policy['max_dimension']:
                        raise ImageInputError('dimensions_exceeded', 'Dimensi/piksel melebihi input_policy predictor')
        except ImageInputError:
            raise
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise ImageInputError('dimensions_exceeded', 'Batas piksel pengaman Pillow terlampaui') from error
        except (OSError, ValueError, SyntaxError, EOFError) as error:
            raise ImageInputError('invalid_image', 'Isi file tidak dapat dibaca sebagai gambar') from error

    def predict_bytes(self, image_bytes):
        self._validate_input(image_bytes)
        try:
            image, _ = decode_image(image_bytes)
        except (OSError, ValueError, SyntaxError, EOFError) as error:
            raise ImageInputError('invalid_image', 'Gambar rusak/tidak lengkap saat decode resmi') from error
        with torch.inference_mode():
            logit = self.model(self.transform(image).unsqueeze(0).to(self.device)).squeeze(-1)[0]
            score = torch.sigmoid(logit).item()
        if not math.isfinite(score):
            raise RuntimeError('Model menghasilkan score tidak finite')
        label = decide_score(score, self.decision_config)
        return {'predicted_label': LABEL_MAP['index_to_name'][str(label)], 'fake_score': score,
                'decision_threshold': self.threshold, 'model_version': self.model_version,
                'preprocessing_version': self.preprocessing_version, 'logit': logit.item()}

    def predict(self, path):
        # Baca terbatas; nama/ekstensi tidak digunakan sebagai fitur/keputusan.
        with Path(path).open('rb') as stream:
            return self.predict_bytes(stream.read(self.input_policy['max_file_bytes'] + 1))

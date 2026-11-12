"""Uji CPU mandiri: bobot nyata,20fixture validation dan kasus input perangkat lunak."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    network_attempts = []
    def offline(event, values):
        if event in ('socket.connect', 'socket.getaddrinfo', 'socket.bind'):
            network_attempts.append(event)
            raise RuntimeError('Smoke test melarang akses jaringan')
    sys.addaudithook(offline)
    import numpy as np
    import torch
    from PIL import Image
    from truelens_inference import Predictor, ImageInputError, PackageIntegrityError, DeviceError
    from truelens_inference.common import file_hash, read_json
    from truelens_inference.preprocessing import decode_image
    from truelens_inference.predictor import select_device
    torch.set_num_threads(4)
    root = args.package_dir.resolve()
    reference = read_json(root / 'fixtures/reference.json')
    predictor = Predictor.from_package(root, device='cpu')
    model_id = id(predictor.model)
    def state_hash():
        h = hashlib.sha256()
        for name, tensor in sorted(predictor.model.state_dict().items()):
            h.update(name.encode()); h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()
    before = state_hash()
    actual = []
    checks = []
    for sample in reference['samples']:
        path = root / sample['input_path']
        assert file_hash(path) == sample['file_sha256']
        result = predictor.predict_bytes(path.read_bytes())
        assert result['predicted_label'] == sample['result']['predicted_label']
        for key in ('decision_threshold', 'model_version', 'preprocessing_version'):
            assert result[key] == sample['result'][key] == reference[key]
        actual.append({'sample_id': sample['sample_id'], 'file_sha256': file_hash(path), 'result': result})
    assert len(actual) == 20 and len({r['sample_id'] for r in actual}) == 20
    scores = np.array([[r['result']['logit'], r['result']['fake_score']] for r in actual])
    expected = np.array([[r['result']['logit'], r['result']['fake_score']] for r in reference['samples']])
    assert np.allclose(scores, expected, atol=1e-6, rtol=1e-5)
    checks += ['20_actual_neural_CPU_fixtures', 'fixture_ID_and_bytes_identical', 'score_and_logit_allclose', 'labels_threshold_versions_identical']

    def image_bytes(fmt='PNG', mode='RGB'):
        image = Image.new(mode, (32, 24), 128 if mode in ('L', 'P') else (90, 120, 180, 90) if mode == 'RGBA' else (90, 120, 180))
        stream = io.BytesIO()
        options = {'transparency': 128} if mode == 'P' else {}
        image.save(stream, format=fmt, **options)
        return stream.getvalue()
    for name, fmt, mode in [('JPEG_RGB', 'JPEG', 'RGB'), ('PNG_RGB', 'PNG', 'RGB'), ('PNG_gray', 'PNG', 'L'), ('PNG_alpha', 'PNG', 'RGBA'), ('PNG_palette_transparency', 'PNG', 'P')]:
        result = predictor.predict_bytes(image_bytes(fmt, mode))
        assert result['predicted_label'] in ('REAL', 'FAKE') and 0 <= result['fake_score'] <= 1
        checks.append('valid_' + name)
    image = Image.new('RGB', (32, 24), 'green'); exif = image.getexif(); exif[274] = 6
    stream = io.BytesIO(); image.save(stream, 'JPEG', exif=exif)
    oriented, _ = decode_image(stream.getvalue()); assert oriented.size == (24, 32)
    predictor.predict_bytes(stream.getvalue()); checks.append('EXIF_orientation_preserved')
    alpha, _ = decode_image(image_bytes('PNG', 'RGBA'))
    expected_alpha = Image.alpha_composite(Image.new('RGBA', (32,24), 'white'), Image.new('RGBA', (32,24), (90,120,180,90))).convert('RGB')
    assert alpha.tobytes() == expected_alpha.tobytes(); checks.append('alpha_white_RGB_preserved')

    def rejects(data, code):
        try:
            predictor.predict_bytes(data)
        except ImageInputError as error:
            assert error.code == code, (error.code, code)
        else:
            raise AssertionError('Input salah diterima: ' + code)
    for name, data, code in [('empty', b'', 'empty_file'), ('corrupt', b'\x89PNG\r\n\x1a\ninvalid', 'invalid_image'),
                             ('text', b'not an image', 'invalid_image'), ('oversize', b'x' * (10*1024*1024+1), 'file_too_large'),
                             ('BMP', image_bytes('BMP'), 'unsupported_format'), ('truncated_JPEG', image_bytes('JPEG')[:-2], 'invalid_image'),
                             ('wrong_type', 'image.png', 'invalid_type')]:
        rejects(data, code); checks.append('reject_' + name)
    for fmt in ('GIF', 'PNG'):
        stream = io.BytesIO()
        Image.new('RGB', (16,16), 'red').save(stream, format=fmt, save_all=True, append_images=[Image.new('RGB',(16,16),'blue')], duration=100, loop=0)
        rejects(stream.getvalue(), 'animated_image'); checks.append('reject_animated_' + fmt)
    original_limit = predictor.input_policy['max_pixels']
    predictor.input_policy['max_pixels'] = 10
    rejects(image_bytes(), 'dimensions_exceeded')
    predictor.input_policy['max_pixels'] = original_limit
    checks.append('explicit_pixel_limit')
    original_dimension = predictor.input_policy['max_dimension']
    predictor.input_policy['max_dimension'] = 10
    rejects(image_bytes(), 'dimensions_exceeded')
    predictor.input_policy['max_dimension'] = original_dimension
    checks.append('explicit_dimension_limit')

    with tempfile.TemporaryDirectory(prefix='truelens_package_negative_') as temporary:
        temporary = Path(temporary)
        fixture = root / reference['samples'][0]['input_path']
        a, b = temporary/'same.jpg', temporary/'renamed.no_extension'
        shutil.copyfile(fixture, a); shutil.copyfile(fixture, b)
        assert predictor.predict(a) == predictor.predict(b) == actual[0]['result']
        assert file_hash(a) == file_hash(b) == file_hash(fixture)
        checks += ['same_image_different_filename_and_extension', 'input_bytes_unchanged']
        bad = temporary/'tampered_package'
        shutil.copytree(root, bad, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for relative in ('model.pt', 'decision_config.json', 'preprocessing.json'):
            path = bad/relative
            with path.open('ab') as stream: stream.write(b'changed')
            try:
                Predictor.from_package(bad)
            except PackageIntegrityError as error:
                assert 'Checksum' in str(error) and relative in str(error)
            else:
                raise AssertionError('Checksum salah diterima')
            shutil.copyfile(root/relative, path)
            checks.append('reject_checksum_' + relative)
    for name in ('invalid_device', 'cpu:1', 'mps'):
        try: select_device(name)
        except DeviceError: pass
        else: raise AssertionError('Perangkat salah diterima')
    checks.append('invalid_device_clear_error')
    if not torch.cuda.is_available():
        try: Predictor.from_package(root, device='cuda')
        except DeviceError as error: assert 'tidak tersedia' in str(error)
        else: raise AssertionError('CUDA unavailable tidak ditolak')
        checks.append('explicit_CUDA_unavailable_clear_error')
    assert id(predictor.model) == model_id and state_hash() == before
    assert not network_attempts
    checks += ['one_model_instance_repeated_predictions', 'all_parameters_and_buffers_unchanged', 'network_blocked_no_attempts']
    assert 'truelens_ai' not in sys.modules
    result = {'status': 'passed', 'device': str(predictor.device), 'fixture_samples': len(actual), 'atol': 1e-6, 'rtol': 1e-5,
              'max_abs_difference': float(np.abs(scores-expected).max()), 'label_differences': 0,
              'model_sha256': file_hash(root/'model.pt'), 'model_version': predictor.model_version,
              'preprocessing_version': predictor.preprocessing_version, 'decision_threshold': predictor.threshold,
              'checks': checks, 'checks_passed': len(checks), 'network_attempts': network_attempts,
              'parameter_buffer_hash_before': before, 'parameter_buffer_hash_after': state_hash(),
              'package_directory': str(root), 'working_directory': str(Path.cwd()), 'python': platform.python_version(),
              'python_executable': sys.executable, 'isolated_mode': bool(sys.flags.isolated),
              'runtime_versions': {name: __import__('importlib.metadata', fromlist=['version']).version(name) for name in ('torch', 'torchvision', 'Pillow', 'numpy')},
              'runtime_module': str(Path(sys.modules['truelens_inference']. __file__).resolve()), 'samples': actual}
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='samples'}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

# TrueLens AI — paket inferensi 1.0.0

Kandidat R2 epoch 9 yang sudah dievaluasi, EfficientNet-B0 satu logit, threshold **0,55**. Seluruh isi folder ini dapat dipindahkan bersama. Tidak memerlukan dataset, manifest penelitian, experiments, reports, notebook, jaringan atau folder proyek asal.

## Isi dan instalasi

`model.pt` hanya state dictionary, bukan optimizer. Konfigurasi model/preprocessing/label/keputusan identik dengan kandidat yang diuji. `package_manifest.json` memuat checksum dan provenance. `truelens_inference/` berisi runtime. `fixtures/` berisi20gambar validation tetap beserta referensi CPU; fixture bukan dataset untuk training. `provenance/` hanya rekaman, tidak dipakai untuk menyelesaikan path penelitian saat inferensi.

Dependency langsung runtime hanya torch, torchvision, Pillow dan numpy. Python yang diuji **3.13.5**, torch **2.10.0+cu128**, torchvision **0.25.0+cu128**, Pillow **13.0.0**, numpy **2.5.4**. CPU wajib bekerja; pengujian CPU memakai build CUDA yang sudah tersedia, bukan mengunduh wheel CPU atau membuat environment bersih baru. Versi publik dependency diperiksa saat startup; suffix +cpu/+cu128 boleh berbeda. Build CPU terpisah belum diuji di tahap9.

Untuk instalasi pada komputer backend baru, pilih salah satu sumber wheel resmi. CPU:

```powershell
python -m pip install torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install Pillow==13.0.0 numpy==2.5.4
```

CUDA12.8, jika perangkat/driver sesuai:

```powershell
python -m pip install torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cu128
python -m pip install Pillow==13.0.0 numpy==2.5.4
```

Sumber: [instruksi resmi versi PyTorch](https://pytorch.org/get-started/previous-versions/). `requirements-ai.txt` mengunci empat dependency langsung; dependency transitif ditangani pip. Tidak memerlukan pandas/sklearn/matplotlib/pytest/FastAPI untuk inferensi atau smoke test ini. Jangan mengubah environment penelitian hanya untuk instalasi contoh ini.

## Pemakaian backend

Salin seluruh folder `ai_package` ke backend, misalnya di samping `main.py`. Import sebagai namespace folder:

```python
from pathlib import Path
from ai_package.truelens_inference import Predictor

package_dir = Path(__file__).resolve().parent / 'ai_package'
predictor = Predictor.from_package(package_dir, device='cpu')  # sekali saat startup
result = predictor.predict_bytes(Path('example.png').read_bytes())
print(result)
```

Jika folder paket menjadi direktori kerja/import root, gunakan `from truelens_inference import Predictor`. Metode tambahan `predictor.predict(path)` membaca file secara terbatas. Nama/ekstensi file tidak memengaruhi label. Paket tidak menulis input atau riwayat. Backend menangani upload, batas request, error HTTP, konkurensi, autentikasi dan penyimpanan. Panggilan CUDA eksplisit yang tidak tersedia menghasilkan `DeviceError`, tanpa fallback diam-diam.

## Smoke test dari lokasi mana pun

```powershell
python path/to/ai_package/smoke_test.py
```

Script memilih CPU, memuat model nyata sekali, memeriksa20fixture (atol1e-6/rtol1e-5), format/input salah, nama berbeda, checksum salah, prediksi berulang dan parameter/buffer. Semua akses jaringan diblokir selama tes. `--output result.json` menulis laporan hanya bila diminta. Kode sukses0; kegagalan assertion/error memberi nonzero. Tidak melatih atau menjalankan ulang20.000test.

Error utama: `ImageInputError` dengan atribut `code` untuk input invalid, `PackageIntegrityError` untuk checksum/config/versi, `DeviceError` untuk perangkat. Error pemuatan runtime/perangkat juga dapat muncul dari torch. Detail batas: [inference_contract.md](inference_contract.md). Integritas manifest berguna untuk mendeteksi kerusakan; bukan tanda tangan kriptografis terhadap pihak yang mengubah manifest beserta semua berkas.

Serahkan **seluruh folder**, atau ZIP yang memuat folder tersebut. Jangan memilih model saja. Tidak menyertakan .venv, dataset lengkap, optimizer, kredensial atau cache. Hasil tahap8 dan batas penggunaan: [model_card.md](model_card.md). Tahap10 FastAPI belum dibuat.

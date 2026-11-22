# TrueLens Image Detector v1

**Versi 1.0.0 · Model ID `truelens-image-detector` · Kandidat integrasi backend.**

Paket ini memuat EfficientNet-B0 dengan satu logit untuk memberi skor kelas FAKE pada citra statis. Bobot lokal adalah state dict hasil ekspor checkpoint terminal Stage2BG setelah 225 update optimizer. Paket memuat model sekali per instance dan memakai kembali model untuk setiap permintaan.

## Struktur dan instalasi

- [Package Python dan metadata](truelens_image_detector/model_info.json) serta [bobot ekspor](truelens_image_detector/weights/truelens-image-detector-v1.pt)
- [Konfigurasi build](pyproject.toml) dan [smoke test](smoke_test.py)
- [Evaluasi historis agregat](docs/evaluation-summary.json) dan [bukti validasi rilis](docs/package-verification.json)
- [Checksum SHA-256](SHA256SUMS.txt)

Gunakan Python **3.13**. Instalasi dilakukan dari root folder paket.

```powershell
python -m pip install .
python smoke_test.py --device cpu
python -m truelens_image_detector path/to/image.jpg --device cpu
```

Untuk instalasi terkontrol, pasang dulu wheel Torch **2.11.0** dan Torchvision **0.26.0** yang cocok dengan perangkat. Pasang Pillow **12.3.0** dan NumPy **2.5.4**. Gunakan `python -m pip install --no-deps .` setelah dependensi tersedia. Untuk CUDA, gunakan build CUDA yang kompatibel dan driver yang sesuai. Konfigurasi yang diverifikasi memakai **Torch 2.11.0+cu128** dan **Torchvision 0.26.0+cu128**. Uji dengan `python smoke_test.py --device cuda`. CPU memakai FP32 dan dapat berjalan pada build CUDA yang sama. Detail build dan perangkat yang benar-benar diuji dicatat pada bukti validasi. Saat pemuatan dan inferensi, paket membaca bobot lokal dan tidak mengunduh bobot pretrained.

## Kontrak inferensi

```python
from truelens_image_detector import ImageDetector

detector = ImageDetector(device="cpu")  # Buat sekali untuk setiap proses backend.
result = detector.predict_bytes(image_bytes)
```

Contoh respons JSON:

```json
{
  "model_id": "truelens-image-detector",
  "model_version": "1.0.0",
  "label": "FAKE",
  "fake_score": 0.72,
  "threshold": 0.5
}
```

Input adalah `bytes` JPEG, PNG, atau WebP statis. Batasnya **10 MiB**, **20.000.000 piksel**, dan **8.192 piksel per sisi**. Validasi format membaca isi file. Pipeline menerapkan EXIF transpose, konversi RGB dengan perilaku Pillow, resize sisi pendek 256 BICUBIC dengan aspect ratio dipertahankan, CenterCrop 224, ToTensor, lalu normalisasi ImageNet dengan mean `[0.485, 0.456, 0.406]` dan std `[0.229, 0.224, 0.225]`. CUDA memakai FP16 autocast dan sigmoid pada logit FP32. Model memakai `eval()` dan `inference_mode()`.

`fake_score = sigmoid(logit)`. Skor **≥0,50** menghasilkan FAKE, termasuk nilai tepat 0,50. Skor di bawahnya menghasilkan REAL. Skor belum dikalibrasi sebagai probabilitas keaslian gambar. Saat pemuatan, paket memeriksa checksum bobot dan memuat state dict secara ketat.

`ImageInputError.code` membedakan input kosong atau bertipe salah, file terlalu besar, format tak didukung, animasi, dimensi berlebih, dan gambar rusak. `ModelError` menandai pemuatan atau inferensi gagal, termasuk checksum gagal, perangkat tidak tersedia, atau logit nonfinite. CLI mengembalikan JSON hasil ke stdout. Jika gagal, CLI mengirim JSON error ke stderr dan keluar dengan kode 1.

## Contoh FastAPI

Contoh ini memuat satu model per proses worker. Simpan `model_id`, `model_version`, dan `threshold` bersama `label` dan `fake_score` agar keputusan historis dapat ditelusuri.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from truelens_image_detector import ImageDetector, ImageInputError, ModelError


@asynccontextmanager
async def lifespan(app):
    app.state.detector = ImageDetector(device="cpu")
    yield


app = FastAPI(lifespan=lifespan)


@app.post("/predict")
async def predict(request: Request, file: UploadFile):
    data = await file.read(10 * 1024**2 + 1)
    try:
        return await run_in_threadpool(request.app.state.detector.predict_bytes, data)
    except ImageInputError as exc:
        status = 413 if exc.code in {"file_too_large", "dimensions_exceeded"} else 422
        raise HTTPException(status, detail={"code": exc.code}) from exc
    except ModelError as exc:
        raise HTTPException(503, detail={"code": "model_unavailable"}) from exc
```

## Riwayat dan konfigurasi riset

1. **Stage2AK** memulihkan training dengan BF16 dan mencapai accuracy 0,9885 pada Alessandra DEV2000.
2. **Pilot Defactify multi-generator** memperluas pengujian lintas generator. **AV900** kemudian menjadi checkpoint awal untuk continuation yang terkontrol.
3. **Stage2BD** membekukan kontrol BCE tanpa bobot. Perlakuan bobot REAL 1,25 gagal memenuhi hipotesis.
4. **Stage2BE** menggabungkan resize dan JPEG. Rata-rata macro-F1 Defactify pada dua degradasi naik 0,0244. Hipotesis dan absolute research gate gagal.
5. **Stage2BF** menemukan penurunan skor yang luas ke arah REAL serta kenaikan AUC khusus short128. Analisis tersebut belum memisahkan kontribusi masing-masing augmentasi.
6. **Stage2BG** mempertahankan slot dan parameter resize 2BE, lalu mengganti slot JPEG dengan original. Komposisi pada masing-masing kelas adalah 75% original dan 25% resize.

Stage2BG memakai satu training 225 update dari AV900 dengan state optimizer dan RNG yang dipulihkan. Konfigurasinya AdamW, effective batch 32, micro-batch 8, accumulation 4, LR backbone `1e-6`, LR head `1e-5`, weight decay 0,01, BCE tanpa bobot, BF16, dan running statistics BatchNorm beku.

Target utama short128 lulus dengan delta macro-F1 **+0,0606** terhadap 2BD. **Hypothesis screen gagal. Absolute research gate gagal.** Di clean DEV, FAKE FNR Defactify **26,44%** melampaui batas **25%**, dan REAL FPR Alessandra **5,40%** melampaui batas **4%**.

## Head-to-head historis terhadap R2

Angka berpasangan ditampilkan sebagai **R2 / Stage2BG**, pada threshold beku masing-masing **0,55 / 0,50**. Prediksi R2 berasal dari arsip terverifikasi. Confusion matrix memakai urutan **TN, FP, FN, TP**.

| Cohort original | N berlabel | Accuracy | Macro-F1 | ROC-AUC | REAL FPR | FAKE FNR | Confusion matrix R2 / Stage2BG |
|---|---:|---|---|---|---|---|---|
| Training AI | 20 | 0,5500 / 0,7000 | 0,4357 / 0,6970 | 0,7300 / 0,8300 | 90,00% / 20,00% | 0,00% / 40,00% | 1,9,0,10 / 8,2,4,6 |
| Defactify DEV900 | 900 | 0,5122 / 0,8322 | 0,3821 / 0,8306 | 0,6572 / 0,9141 | 94,67% / 7,11% | 2,89% / 26,44% | 24,426,13,437 / 418,32,119,331 |
| Alessandra DEV2000 | 2.000 | 0,5125 / 0,9640 | 0,3724 / 0,9640 | 0,7312 / 0,9954 | 96,00% / 5,40% | 1,50% / 1,80% | 40,960,15,985 / 946,54,18,982 |
| 2BC | 1.225 | 0,4743 / 0,5249 | 0,3257 / 0,4366 | 0,4241 / 0,5287 | 99,52% / 10,33% | 3,02% / 86,74% | 3,626,18,578 / 564,65,517,79 |

| Stress berlabel | Macro-F1 short128 | ROC-AUC short128 | Macro-F1 JPEG50 | ROC-AUC JPEG50 |
|---|---|---|---|---|
| Training AI | 0,4357 / 0,7494 | 0,7550 / 0,8100 | 0,5238 / 0,7442 | 0,7400 / 0,8500 |
| Defactify DEV900 | 0,3799 / 0,7720 | 0,6769 / 0,8560 | 0,4179 / 0,7811 | 0,6737 / 0,9167 |

Stage2BG memperoleh macro-F1 dan AUC lebih tinggi di seluruh cakupan perbandingan. Pada 2BC, Stage2BG masih melewatkan **517 dari 596 FAKE** dengan AUC sekitar **0,529**. Evaluasi memakai satu seed dan DEV yang telah dipakai berulang. 2BC adalah diagnosis eksternal yang sudah dilihat, dengan 13 gambar karantina. Training AI terdiri dari 20 label kiriman dengan asal belum diverifikasi dan 30 UNKNOWN. Generalisasi independen belum terbukti. Gunakan model sebagai sinyal bantu, terutama saat keputusan terhadap satu file punya konsekuensi.

## Validasi rilis dan GitHub

Validasi baru berfokus pada ekspor state dict, build dan instalasi wheel, smoke test input sintetis, CLI, dan parity dengan runner sumber. Evaluasi dataset historis tidak dijalankan ulang. Lihat [bukti validasi rilis](docs/package-verification.json) untuk hasil aktual dan batas pengujian.

Salin seluruh folder `truelens-image-detector/` ke root repo backend sebagai paket berdampingan. Dari root repo, periksa aturan LFS dan staging:

```powershell
git check-attr -a -- truelens-image-detector/truelens_image_detector/weights/truelens-image-detector-v1.pt
git add -- truelens-image-detector/
# Jika repo mengabaikan docs/, tambahkan hanya dua file agregat ini.
git add -f -- truelens-image-detector/docs/evaluation-summary.json truelens-image-detector/docs/package-verification.json
git diff --cached --name-status
git diff --cached --check
```

Sertakan kode, README, metadata, bobot ekspor, hasil agregat, smoke test, dan checksum. Simpan ZIP sebagai handoff terpisah. Gambar uji personal, dataset, checkpoint training lengkap, cache, secrets, dan output sementara berada di luar paket. Review perubahan sebelum commit dan push. Aktivasi pada aplikasi backend adalah keputusan terpisah.


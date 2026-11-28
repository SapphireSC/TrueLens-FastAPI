# TrueLens Image Detector v1

Paket inferensi Python untuk klasifikasi gambar REAL / FAKE. Rilis paket `1.0.0` memakai bobot EfficientNet-B0 dari checkpoint terminal Stage2BG. Nama rilis dipakai oleh backend, sementara nama stage dipertahankan dalam dokumentasi riset agar hasil dapat ditelusuri.

**Status: kandidat integrasi.** Dalam head-to-head, model ini mendapat macro-F1 dan ROC-AUC lebih tinggi daripada R2 pada seluruh cohort dan variasi yang dibandingkan. Pada diagnosis eksternal 2BC, model hanya mendeteksi 79 dari 596 FAKE, dengan AUC 0,529. Hasil tersebut membatasi penggunaan sebagai sinyal pemeriksaan gambar. Status kelulusan riset tetap tercatat di bagian Evaluasi pengembangan.

## Mulai cepat

Aktifkan virtual environment backend yang sesuai. Contoh instalasi untuk Linux atau Windows dengan CPU:

```bash
python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cpu
python -m pip install .
python smoke_test.py
python -m truelens_image_detector /path/to/image.jpg
```

Untuk NVIDIA, gunakan wheel CUDA yang sesuai dengan host. Runtime historis head-to-head memakai PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, CUDA 12.8, Pillow 12.3.0, dan NumPy 2.5.4. Referensi [instalasi PyTorch](https://pytorch.org/get-started/locally/).

```bash
python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
python -m pip install .
python smoke_test.py --device cuda
python -m truelens_image_detector /path/to/image.jpg --device cuda
```

Paket memuat bobot lokal saat `ImageDetector` dibuat. Gunakan satu instance per proses backend. CPU memakai FP32 dan CUDA memakai FP16 autocast pada forward, dilanjutkan sigmoid FP32. Periksa kesetaraan skor pada deployment yang akan dipakai, terutama untuk gambar di sekitar threshold. Skor head-to-head historis berasal dari runner evaluasi, sedangkan smoke test memeriksa jalur paket pada satu gambar sintetis.

## Kontrak integrasi

```python
from truelens_image_detector import ImageDetector

detector = ImageDetector(device="cpu")  # gunakan "cuda" pada host CUDA
with open("image.jpg", "rb") as image:
    prediction = detector.predict_bytes(image.read(16 * 1024 * 1024 + 1))
```

Contoh struktur respons:

```json
{
  "model_id": "truelens-image-detector",
  "model_version": "1.0.0",
  "label": "FAKE",
  "fake_score": 0.72,
  "threshold": 0.5
}
```

- Input adalah byte gambar statis JPEG, PNG, atau WebP. Adapter membatasi unggahan ke 16 MiB dan 25 juta piksel terdekode. Terapkan juga batas ukuran request pada backend.
- Pipeline model memakai EXIF transpose, RGB, bicubic resize ke sisi pendek 256 dengan rasio tetap, center crop 224 × 224, lalu konversi tensor dan normalisasi ImageNet. Mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`.
- EfficientNet-B0 menghasilkan satu logit. `fake_score` adalah sigmoid logit dan menggambarkan skor keluaran model. Skor ini belum dikalibrasi sebagai probabilitas keaslian. Kelas FAKE diberikan saat skor ≥ 0,50.
- Hubungkan label, skor, threshold, dan versi langsung dari hasil inferensi. Simpan model ID serta versi pada record prediksi baru agar hasil historis tetap bisa dibaca dengan konteksnya.
- Tangani `InvalidImageError` sebagai input bermasalah. Laporkan kegagalan load, checksum, runtime, atau skor nonfinite sebagai error layanan. Catat detail teknis di server dan tampilkan pesan umum ke pengguna.

Contoh pemanggilan dari handler FastAPI. Inisialisasikan `request.app.state.image_detector` di lifespan aplikasi. Sesuaikan nama route dan skema database dengan backend yang sudah ada.

```python
from fastapi import HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from truelens_image_detector import InvalidImageError

async def predict_image(request: Request, file: UploadFile):
    content = await file.read(16 * 1024 * 1024 + 1)
    if len(content) > 16 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ukuran gambar melebihi batas.")
    try:
        return await run_in_threadpool(
            request.app.state.image_detector.predict_bytes, content
        )
    except InvalidImageError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
```

## Riwayat pengembangan

| Tahap | Peran |
| --- | --- |
| R2 / CIFAKE | Baseline pembanding dengan threshold 0,55. Hasil historis test CIFAKE sekitar 96,49% untuk accuracy dan macro-F1. |
| Stage2AK / Alessandra | Baseline baru berbasis EfficientNet-B0. Training Alessandra menggunakan 20.000 gambar dan DEV tetap 2.000 gambar. Checkpoint terminal mencapai 98,85% pada DEV internal. |
| Stage2AT / Stage2AU | Memasukkan Defactify untuk memperluas distribusi training, dengan replay Alessandra. Defactify memakai lima kelompok generator: SD21, SDXL, SD3, DALL·E 3, dan Midjourney 6. Manifest memisahkan 3.600 gambar train dan 900 gambar DEV. Pilot menggabungkan 3.600 gambar Defactify dengan 3.600 replay Alessandra per epoch selama tiga epoch, menghasilkan 675 update. |
| Stage2AV | Melanjutkan pilot 225 update hingga AV900 dengan sampling Defactify yang lebih menekankan SDXL dan Midjourney 6 serta menjaga keseimbangan REAL / FAKE. AV900 menjadi titik awal untuk eksperimen berikutnya. |
| Stage2BD | Menetapkan kontrol tanpa augmentasi dan menguji pemberian bobot lebih pada kesalahan REAL. Perlakuan berbobot tidak melewati kriteria hipotesis, sehingga kontrol 2BD menjadi pembanding augmentasi. |
| Stage2BE / Stage2BF | Menguji gabungan resize dan JPEG. Macro-F1 Defactify short128 meningkat, disertai tambahan kesalahan FAKE. Analisis prediksi menunjukkan bahwa skor REAL dan FAKE sama-sama cenderung turun. |
| Stage2BG | Ablasi resize saja dari AV900. Slot dan parameter resize dipertahankan dari 2BE. Slot JPEG dikembalikan ke input original agar dampak penghentian augmentasi JPEG dapat dibandingkan. |

### Konfigurasi training checkpoint terminal

Stage2BG memulai dari bobot, optimizer, dan RNG AV900. Run memakai satu seed, 225 update AdamW, effective batch 32 (micro-batch 8 × 4 akumulasi), learning rate backbone `1e-6` dan head `1e-5`, serta weight decay 0,01. Training memakai BCE tanpa pembobotan kelas, BF16, dan running statistics BatchNorm yang dibekukan. Urutan data mengikuti rencana yang sama dengan kontrol 2BD dan perlakuan 2BE.

Untuk tiap kelas, 2.700 occurrence menggunakan input original dan 900 menggunakan resize. Ukuran sisi pendek resize berada di rentang 96–192 piksel, dengan bicubic dan rasio aspek tetap. Transform ini terjadi setelah EXIF/RGB dan sebelum transform EfficientNet. Evaluasi terminal menggunakan original, short128, dan JPEG50 pada DEV yang sudah dibekukan.

Paket berisi state dict untuk inferensi, termasuk buffer model. Ekspor membuang optimizer, RNG, dan state pelatihan. Seluruh 360 tensor dan buffer pada state dict hasil ekspor dibandingkan dengan checkpoint sumber dan identik. Identitas kedua artefak tercatat dalam [metadata bobot](truelens_image_detector/model_info.json).

### Evaluasi pengembangan

| Defactify DEV900 | Kontrol 2BD | Resize + JPEG 2BE | Resize saja 2BG |
| --- | ---: | ---: | ---: |
| Macro-F1 original | 84,27% | 83,23% | 83,06% |
| Macro-F1 short128 | 71,14% | 77,52% | 77,20% |
| Macro-F1 JPEG50 | 80,47% | 78,97% | 78,11% |

Target utama short128 lulus (+6,06 poin persentase terhadap kontrol), tetapi hasil penggabungan seluruh syarat hipotesis gagal. Gate absolut juga gagal karena FAKE FNR clean Defactify 26,44% melebihi batas 25% dan REAL FPR clean Alessandra 5,40% melebihi batas 4%. Hasil head-to-head dan gate pengembangan menjawab dua pertanyaan terpisah, yaitu performa relatif dan pencapaian batas minimum riset.

## Head-to-head terhadap R2

Perbandingan berpasangan mencakup 4.175 gambar original yang valid, termasuk 4.145 berlabel dan 30 UNKNOWN, serta 6.075 entri gambar dan varian. R2 memakai prediksi arsip yang cocok dengan identitas masukan, pipeline, dan varian. 2BG memakai prediksi DEV yang cocok dengan arsip dan menjalankan inferensi pada bagian yang belum tercakup. Threshold beku adalah 0,55 untuk R2 dan 0,50 untuk 2BG. Metrik AK ditambahkan sebagai referensi pada input yang sama dari pengujian R2–AK sebelumnya.

| Cohort original | N berlabel | Accuracy R2 / 2BG | Macro-F1 R2 / 2BG | ROC-AUC R2 / 2BG | Macro-F1 AK |
| --- | ---: | --- | --- | --- | ---: |
| Training AI | 20 | 55,00% / 70,00% | 43,57% / 69,70% | 0,730 / 0,830 | 33,33% |
| Defactify DEV | 900 | 51,22% / 83,22% | 38,21% / 83,06% | 0,657 / 0,914 | 38,49% |
| Alessandra DEV | 2.000 | 51,25% / 96,40% | 37,24% / 96,40% | 0,731 / 0,995 | 98,85% |
| 2BC, diagnosis eksternal | 1.225 | 47,43% / 52,49% | 32,57% / 43,66% | 0,424 / 0,529 | 34,34% |

| Stress test | Macro-F1 R2 / 2BG | ROC-AUC R2 / 2BG |
| --- | --- | --- |
| Training AI, short128 | 43,57% / 74,94% | 0,755 / 0,810 |
| Training AI, JPEG50 | 52,38% / 74,42% | 0,740 / 0,850 |
| Defactify, short128 | 37,99% / 77,20% | 0,677 / 0,856 |
| Defactify, JPEG50 | 41,79% / 78,11% | 0,674 / 0,917 |

Pada Training AI original, R2 mendeteksi 10/10 FAKE dan mengenali 1/10 REAL. 2BG mendeteksi 6/10 FAKE dan mengenali 8/10 REAL. Di Defactify original, R2 mengenali 24/450 REAL dan 437/450 FAKE. 2BG mengenali 418/450 REAL dan 331/450 FAKE. Kenaikan AUC di Defactify menunjukkan perbaikan pemeringkatan skor di samping perubahan keputusan pada threshold beku. Pada JPEG50, FAKE FNR 2BG di Defactify meningkat menjadi 38,67%.

2BG merupakan kandidat terkuat pada cakupan head-to-head. AK tetap memperoleh hasil tertinggi pada Alessandra DEV internal. Pada 2BC, 2BG melewatkan 517 dari 596 FAKE. Balanced accuracy 51,46% dan AUC 0,529 menunjukkan pemisahan kelas yang lemah pada cohort tersebut. Sumber dan proses pengambilan data berbeda antarcohort, jadi performa dilaporkan per cohort.

### Cakupan klaim

- Defactify dan Alessandra DEV dipakai dalam pengembangan. 2BC sudah ditinjau sebagai diagnosis eksternal dan mempertahankan 13 gambar dalam karantina. Ketiga cohort memiliki batas sebagai bukti generalisasi independen.
- Training AI terdiri dari 50 gambar valid. Hanya 20 memiliki label kiriman, dengan asal belum diverifikasi secara independen. Prediksi 30 UNKNOWN hanya memberi gambaran keputusan model. Varian original, short128, dan JPEG50 berbagi gambar induk.
- Perbandingan ini belum menguji 2BG pada test CIFAKE historis R2. Angka 96,49% R2 dan 98,85% AK berasal dari evaluasi yang berbeda.
- [Ringkasan evaluasi](docs/evaluation-summary.json) menyediakan confusion matrix, FPR, FNR, accuracy, AUC, coverage, hitungan pasangan R2–2BG, hasil gate, dan hash laporan sumber.

## Verifikasi paket

Wheel berhasil dibangun dan dipasang pada CPU Linux dengan torch 2.11.0, torchvision 0.26.0, Pillow 12.3.0, dan NumPy 2.5.4. Pada empat gambar sintetis, skor paket sama persis dengan referensi CPU yang memuat checkpoint sumber. Pemeriksaan mencakup JPEG berorientasi EXIF, PNG, WebP, dan gambar 32 × 48. Lima kasus input tidak valid ditolak. Smoke test dan CLI lulus. Uji CUDA dan integrasi repo FastAPI menjadi bagian validasi di host backend. [Hasil verifikasi](docs/package-verification.json).

## Handoff GitHub

Ekstrak arsip lalu masukkan folder sumber `truelens-image-detector` pada branch integrasi di repo yang dituju. Stage folder sumber beserta bobot, jalankan smoke test, dan review perubahan sebelum commit dan push. Arsip ZIP adalah media handoff. Bobot di dalam folder berukuran 15,6 MiB dan dapat disimpan dalam Git biasa berdasarkan batas ukuran GitHub. Ikuti konfigurasi Git LFS repo jika pola `*.pt` telah dikonfigurasi. [Batas ukuran GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github).

Paket memuat kode, bobot, metadata, hasil agregat, dan smoke test. Asal checkpoint serta dataset didokumentasikan untuk review tim sebelum mengubah visibilitas repo. Dalam protokol Stage2AT, izin penggunaan Defactify perlu dikonfirmasi kepada pemilik dataset. Hak publikasi ulang bobot hasil pelatihan belum diverifikasi dalam handoff ini.

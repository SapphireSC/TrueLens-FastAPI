# Kontrak inferensi TrueLens AI 1.0.0

## API

`Predictor.from_package(package_dir, device="cpu", *, max_pixels=None, max_dimension=None)` memeriksa checksum seluruh isi yang tercatat, memuat arsitektur `weights=None`, state dictionary melalui `torch.load(weights_only=True, map_location=device)`, `load_state_dict(strict=True)`, lalu `eval()`. Bobot dimuat sekali saat startup. Tidak mengunduh ImageNet. `predict_bytes(image_bytes: bytes) -> dict` menjalankan `inference_mode()`. `predict(path)` setara dan membaca maksimum10MiB+1byte untuk memeriksa ukuran.

Contoh respons:

```json
{
  "predicted_label": "FAKE",
  "fake_score": 0.7398839592933655,
  "decision_threshold": 0.55,
  "model_version": "truelens-r2-epoch9-v1.0.0",
  "preprocessing_version": "exif-rgb-white-v1+imagenet1k-v1",
  "logit": 1.045365333557129
}
```

FAKE jika `fake_score >= 0.55`, selainnya REAL. REAL=0, FAKE=1; tidak ada kelas ketiga/confidence band. Skor sigmoid dari satu logit FAKE, finite0–1; bukan jaminan persentase keaslian atau bukti forensik. `logit` adalah keluaran sebelum sigmoid. Tidak ada field latency; waktu pemrosesan batch tahap8 bukan waktu respons website.

## Input

Bytes gambar JPEG/JPG atau PNG statis. Konten diperiksa melalui Pillow, bukan ekstensi/MIME saja. Ukuran maksimum **10MiB =10.485.760byte**. File kosong/rusak/truncated, bukan gambar, animasi/APNG/multiframe, format lain ditolak. Ukuran dicek sebelum decoder/load. Tidak menyimpan atau mengubah file input otomatis.

`input_policy.json` menetapkan batas penerimaan eksplisit **20.000.000piksel** dan **8.192piksel per sisi**. Ini batas layanan paket baru, bukan perubahan resize/normalisasi penelitian. Backend dapat mengatur `max_pixels`/`max_dimension` integer positif saat startup; sepakati nilai sesuai memori server. `max_pixels` tidak boleh melebihi pengaman Pillow aktif. Pillow13.0.0 pada pengujian memakai `MAX_IMAGE_PIXELS=89.478.485`; peringatan decompression bomb diperlakukan sebagai error, `LOAD_TRUNCATED_IMAGES` harusFalse. Paket tidak mengubah global decoder. Perubahan global oleh aplikasi lain dapat menyebabkan error.

Setelah pemeriksaan penerimaan, decoder/preprocessing salinan persis penelitian: verify/load, EXIF transpose, konversi RGB, alpha/transparency dikomposit ke putih, grayscale→RGB, reject multiframe. Resize sisi pendek256 dengan bicubic/antialias, center crop224, skala0–1, normalisasi ImageNet mean/std sekali. Tidak augmentasi acak, kompres ulang, face detection atau manipulasi berdasarkan nama file.

## Error dan tanggung jawab

`ImageInputError.code`: `invalid_type`, `empty_file`, `file_too_large`, `invalid_image`, `animated_image`, `unsupported_format`, `dimensions_exceeded`. `PackageIntegrityError`: komponen hilang/checksum/konfigurasi/dependency tidak cocok. `DeviceError`: CPU/CUDA diminta tidak tersedia/valid; CUDA tidak fallback diam-diam. I/O file dapat melempar `OSError`. Error bukan label model. Backend memetakan error ke respons API, membatasi upload sebelum seluruh bytes berada di RAM, dan menentukan antrean/konkurensi serta penyimpanan riwayat. Predictor tidak membuat endpoint, database, autentikasi atau deployment. Backend sebaiknya memakai satu instance per worker; pengujian tahap9 berurutan, belum mengukur beban konkurensi web.

Path runtime relatif terhadap package_dir, tidak bergantung working directory. Dokumen sumber pada provenance hanya metadata; path penelitian tidak dibuka. CPU telah diperiksa pada proses baru dari salinan paket di luar proyek dengan working directory berbeda, dependency penelitian bersama; hasil rinci di laporan tahap9. CUDA adalah dukungan opsional, belum diklaim sama toleransi dengan CPU tanpa tes tersendiri.

# Laporan tahap 9 — paket inferensi mandiri

Run `PKG9_20261112_001940_802367`. Selesai 2026-11-12T00:21:29+07:00. **Passed**; berhenti setelah tahap9.

## Kandidat dan checksum

R2 best epoch9, FAKE jika score>=0,55, REAL=0/FAKE=1. Model sumber dan `ai_package/model.pt` identik: `c865f002bd1520fc115d005a71b901640dc14f89009b431c94d1941999d97913`. Tidak training/tuning, konversi, quantization atau mengganti hasil test. Dokumen kandidat asli, konfigurasi seleksi, manifest, hasil evaluasi dan seluruh sumber penelitian tetap identik: 865 berkas diverifikasi sebelum/sesudah (preservation_check.json).

Kandidat beku asli SHA-256 `1a68a10121cc751b6b3793031f3aaf392b5ac3bd601c90d87d7c709103a9d518`. Checksum model, konfigurasi, seluruh file paket dan sumber kandidat direkam di package_manifest.json; hash manifest `6c3a5288f3a54b7a8d38d888c5fdccda738cb8a8e05a55d5cb2d45bff5f69b90`. Sumber tahap7/tahap8 beserta seluruh checksums diperiksa sebelum membangun paket. frozen_candidate.json/evaluation_record.json dalam provenance adalah salinan identik, bukan kebutuhan path runtime.

## Implementasi dan input

`Predictor.from_package(package_dir, device="cpu")` memuat sekali saat startup. `predict_bytes(bytes)` mengembalikan predicted_label REAL/FAKE, fake_score, decision_threshold0,55, model_version, preprocessing_version dan logit. Adapter memakai fungsi build_model yang disalin persis (pretrained=False→weights=None), torch.load weights_only=True/map_location sesuai perangkat, strict=True, eval/inference_mode. Decoder, transform dan keputusan disalin byte-identik dari kode penelitian; hash reuse tercatat di manifest.

JPEG/PNG statis, maksimum10MiB, inspeksi konten, tanpa menyimpan/mengubah input otomatis. Batas penerimaan eksplisit default20juta piksel/8192 per sisi dapat diatur saat startup, dibatasi pengaman Pillow; ini batas layanan baru, bukan perubahan transform penelitian. EXIF/RGB/alpha putih/grayscale tetap sama. Detail input/error, tanggung jawab backend dan contoh startup ada di inference_contract.md dan README.md. Tidak membuat endpoint FastAPI, website atau database.

## Bukti neural dan portabilitas

Referensi20fixture validation tetap dibangun dari Predictor.from_frozen_candidate CPU nyata pada threshold0,55, cocok dengan referensi CPU R2 lama. Paket disalin ke direktori temp OS di luar root proyek, dijalankan dari working directory lain dalam proses Python baru `-I -B`, PYTHONPATH dihapus. Akses root penelitian ditolak oleh audit hook, kecuali .venv yang menyediakan dependency bersama. Tidak ada upaya akses sumber penelitian. Namespace import contoh backend (`ai_package.truelens_inference`) juga diperiksa.

CPU:20/20fixture cocok, max absolute difference logit/skor **0.0**, atol1e-6/rtol1e-5, label berbeda0. Threshold dan versi cocok; input ID/SHA identik. Seluruh parameter/buffer sebelum/sesudah identik. Jaringan diblokir, upaya jaringan0, TORCH_HOME kosong tetap kosong: tidak ada unduhan bobot. Isi paket asli dan hasil relokasi tidak berubah selama pengujian. Lokasi temp telah dibersihkan sesudah bukti disalin ke laporan.

32 pemeriksaan smoke lulus: fixture neural, JPEG/PNG RGB/gray/alpha/palette, EXIF dan alpha putih, nama/ekstensi berbeda, empty/corrupt/text/truncated/oversize/animasi GIF+APNG/BMP/wrong type, batas dimensi/piksel, checksum model/decision/preprocessing salah, perangkat invalid dan CUDA yang eksplisit tidak tersedia. Bobot sebenarnya tetap digunakan; tidak ada mock/fallback skor. Ini uji perangkat lunak dan konsistensi pengemasan; bukan evaluasi ulang20.000test. Bukti: portable_cpu_result.json, portable_cpu_smoke.log, portability_test.json, portability_guard.json, reference_build.json.

## Dependency dan hasil penelitian

Python 3.13.5; dependency langsung {"torch": "2.10.0+cu128", "torchvision": "0.25.0+cu128", "Pillow": "13.0.0", "numpy": "2.5.4"}. Memakai environment/dependency yang telah tersedia (build CUDA dipakai untuk inferensi CPU), **bukan** environment bersih baru atau wheel CPU terpisah. Tidak menginstal/upgrade/mengunduh wheel. Runtime hanya torch/torchvision/Pillow/numpy; library penelitian lain tidak dipakai oleh paket. README memuat instruksi CPU/CUDA dari [sumber resmi PyTorch](https://pytorch.org/get-started/previous-versions/). CUDA runtime opsional; konsistensi neural yang diklaim di tahap9 hanya CPU.

Hasil tahap8 tetap: test resmi20.000 accuracy0.9649, macro-F10.964899971568977; test unik19.962 accuracy0.964933373409478, macro-F10.9649333448972438. Test unik subset prediksi yang sama, bukan dataset independen kedua. Tidak menjalankan ulang seluruh test. Model card menjelaskan CIFAKE, duplikasi, pemilihan validation, sumber kelas, resolusi32x32 dan keterbatasan generator/provenance. Informasi lisensi mengikuti README penerbit; lisensi khusus distribusi kode/bobot TrueLens belum ditetapkan pemilik. Skor bukan bukti mutlak keaslian; waktu batch tahap8 bukan respons website.

## Penyerahan dan tahap berikutnya

Serahkan seluruh `ai_package/` atau ZIP `deliverables/TrueLens_AI_R2_epoch9_v1.0.0.zip` beserta `.zip.sha256`. ZIP 43 file terverifikasi byte-identik dengan folder, SHA-256 `696eb9745d2dda23213cbdf487ef3cc2d213d3d33b837bec919d9ccc6d8c700a`. Tidak berisi .venv, dataset lengkap, cache, kredensial atau optimizer. Isi paket: model/config, runtime, README, inference_contract, model_card, requirements-ai, package_manifest, smoke_test,20fixture+reference dan provenance.

Siap secara teknis untuk integrasi FastAPI tahap10, dengan antarmuka yang didokumentasikan. Tidak ada penghambat teknis tersisa pada pengujian CPU ini. Tahap10 belum dikerjakan; belum ada pengujian beban/konkurensi server atau deployment. Untuk memeriksa ulang checksum penyerahan tanpa inferensi: `python scripts/verify_stage9.py` setelah run passed. Untuk smoke manual paket pindahan: `python path/to/ai_package/smoke_test.py`.

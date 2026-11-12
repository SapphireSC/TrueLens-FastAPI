# Model card — TrueLens AI R2 epoch9

## Model dan penggunaan

EfficientNet-B0, head Dropout0,2 dan Linear1280→1. R1 menggunakan fitur ImageNet beku; R2 membuka grup MBConv terakhir, final convolution dan classifier, dengan BatchNorm dibekukan. Kandidat R2 best epoch9 tetap, threshold validation0,55, REAL=0/FAKE=1. Paket hanya salinan state dictionary, tanpa quantization/tracing/konversi. Model SHA-256: `c865f002bd1520fc115d005a71b901640dc14f89009b431c94d1941999d97913`.

Tujuan: eksperimen klasifikasi indikasi gambar sintetis pada protokol CIFAKE. Tidak layak diperlakukan sebagai bukti tunggal pemalsuan atau autentisitas. Skor sigmoid bukan jaminan probabilitas keaslian yang terkalibrasi.

## Data dan provenance

[Repositori penerbit CIFAKE](https://github.com/jordan-bird/CIFAKE-Real-and-AI-Generated-Synthetic-Images) menyebut REAL berasal dari CIFAR-10 dan FAKE dibuat memakai Stable Diffusion1.4;120.000gambar dengan100.000train resmi dan20.000test resmi. Dataset juga tersedia di [Kaggle](https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images). Audit lokal menemukan JPEG RGB32×32; model menerima crop224 setelah resize. Resolusi kecil dan satu keluarga generator membatasi generalisasi.

Audit lokal membuang1.298record train:920salinan duplikat internal dan378overlap identik dengan test; tidak ditemukan konflik label. Split eksperimen: train78.961 (40.000REAL/38.961FAKE), validation19.741 (10.000REAL/9.741FAKE). Train/validation/test disjoint menurut ID, path dan grup piksel identik. Ini bukan jaminan tidak ada near-duplicate atau kebocoran provenance yang tidak terdeteksi.

## Seleksi dan evaluasi

Validation dipakai memilih R2/checkpoint dan threshold; skor validation setelah seleksi bukan evaluasi independen. Evaluasi tahap8 memakai kandidat tetap tanpa perubahan berdasarkan test. Berikut hasil tersimpan, **tidak dievaluasi ulang pada tahap9**:

| Kelompok | N | Accuracy | Macro-F1 | ROC-AUC FAKE | Average precision FAKE | REAL→FAKE | FAKE→REAL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Test resmi |20.000|0.9649|0.964899971568977|0.9950328800000001|0.9951237417583031|360|342|
| Test unik |19.962|0.964933373409478|0.9649333448972438|0.9950322726360169|0.9951067136098394|360|340|

Test unik merupakan subset prediksi yang sama:10.000REAL/9.962FAKE, menghilangkan38salinan internal berlabel sama. Bukan dataset independen kedua. Validation terpilih accuracy0.9661617952484677, macro-F10.9661579290553344; hasil test resmi sedikit lebih rendah. Average precision dihitung dari skor kontinu dengan sklearn.average_precision_score, bukan semua definisi luas kurva PR. Waktu pemrosesan batch tahap8 bukan waktu respons website.

## Batas dan lisensi sumber

Belum diuji lintas seluruh generator, foto resolusi tinggi, kompresi/edit dunia nyata, domain baru atau lintas seed. REAL/FAKE mengikuti label asal dataset; tidak membuktikan semua gambar REAL bebas manipulasi. Kesalahan kedua arah tetap ada. File fixture hanya20gambar validation tetap untuk verifikasi pengemasan; tidak menambah data penelitian.

README penerbit menyatakan CIFAKE menggunakan MIT dan menautkan [teks lisensi yang dirujuk](https://github.com/wichtounet/cifar-10/blob/master/LICENSE). Pernyataan ini dicatat sebagai informasi penerbit, bukan audit hak setiap gambar/provenance. Lisensi distribusi khusus kode/bobot TrueLens belum ditetapkan oleh pemilik proyek; jangan menyimpulkan lisensi model otomatis sama dengan dataset. Library runtime mempertahankan lisensinya sendiri dan tidak dibundel sebagai wheel di sini.

Rujukan: Krizhevsky & Hinton (2009), [Learning Multiple Layers of Features from Tiny Images](https://www.cs.toronto.edu/~kriz/learning-features-2009-TR.pdf); Bird & Lotfi (2024), [CIFAKE: Image Classification and Explainable Identification of AI-Generated Synthetic Images](https://ieeexplore.ieee.org/abstract/document/10409290). Dokumen beku dan evaluation_record disalin ke provenance tanpa mengubah sumber; checksum sumber/paket dicatat di manifest dan laporan tahap9.

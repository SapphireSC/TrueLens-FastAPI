# TrueLens AI — Sistem Klasifikasi Gambar Asli vs Buatan AI

Proyek UAS Mata Kuliah **Pemrograman Web Framework** (Bidang: **Hiburan / Media Digital**).
Mengintegrasikan **FastAPI**, **Jinja2**, **CSS3/JavaScript**, **PostgreSQL (SQLAlchemy 2.0)**, dan model Deep Learning **EfficientNet-B0** yang dilatih pada dataset **CIFAKE**.

## 1. Fitur Utama (Pemenuhan Soal 1 s.d. 5 UAS)
- **Model AI EfficientNet-B0 (`ai/`)**: Prapemrosesan `(224, 224, 3)` dengan `preprocess_input` standar `[0..255]`, pelatihan Transfer Learning 2 tahap pada dataset [CIFAKE Kaggle](https://www.kaggle.com/datasets/birdy654/cifake-real-and-ai-generated-synthetic-images), dan evaluasi metrik lengkap (`evaluation_metrics.json`).
- **Beranda & Dokumentasi Detail (`GET /`)**: Menyajikan tujuan aplikasi, konteks deepfake, rincian dataset CIFAKE, dan detail arsitektur EfficientNet-B0.
- **Pindai & Inferensi Real-Time (`GET /scan`, `POST /predict`)**: Validasi ekstensi, batas ukuran 10 MB, dan pemeriksaan *magic bytes* gambar, dilengkapi meter keyakinan dan skala probabilitas 4 rentang.
- **Operasi Database CRUD (`POST /history/save`, `GET /history`, `POST /history/{id}/delete`)**: Menyimpan hasil pemindaian ke PostgreSQL (`scan_history`), memfilter riwayat berdasarkan status/tanggal, serta menghapus record sekaligus file gambar fisik di server.
- **Halaman Tim / Contact Us (`GET /contact`)**: Menampilkan pembagian peran teknis keempat anggota kelompok beserta spesifikasi fakta proyek.

## 2. Cara Menjalankan di Lokal (VS Code)

```bash
# 1. Buat dan aktifkan virtual environment
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate

# 2. Instal dependensi
pip install -r requirements.txt

# 3. (Opsional) Konfigurasi PostgreSQL
# Salin .env.example menjadi .env dan sesuaikan password PostgreSQL Anda,
# lalu impor database/truelens_db.sql ke pgAdmin / psql.
# Bila .env belum diatur, aplikasi otomatis menggunakan SQLite lokal (truelens_local.db) agar langsung siap diuji.

# 4. Jalankan server FastAPI
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Buka browser di `http://127.0.0.1:8000`.

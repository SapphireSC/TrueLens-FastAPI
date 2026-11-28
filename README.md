# TrueLens AI — Sistem Verifikasi Keaslian Citra Digital

Proyek UAS Mata Kuliah **Pemrograman Web Framework** (Bidang: **Hiburan / Media Digital** — Universitas Bunda Mulia).  
Mengintegrasikan **FastAPI**, **SQLModel**, **PostgreSQL**, **Jinja2 + Bootstrap 5.3**, **CSS3/JavaScript**, dan model Deep Learning **PyTorch EfficientNet-B0** melalui paket inferensi mandiri **`ai_package_v2` (`truelens-image-detector v1.0.0`)**.

---

## 1. Fitur Utama
- **Mesin Deteksi AI Terbaru (`ai_package_v2/truelens-image-detector`)**: Menggunakan bobot PyTorch **EfficientNet-B0** (checkpoint `Stage2BG`, `truelens-image-detector v1.0.0`) dengan prapemrosesan EXIF transpose, konversi RGB, *Bicubic Resize* sisi pendek 256 px, *Center Crop* `224x224`, dan normalisasi ImageNet-1K. Menghasilkan skor *sigmoid* (`fake_score`) dengan ambang batas keputusan **`0,50`** (`>= 0,50` → **AI-Generated**, `< 0,50` → **Real**) serta verifikasi *checksum* SHA-256 otomatis saat startup.
- **Autentikasi Akun & Sesi (`app/routes/auth.py`, `app/services/user_service.py`)**: Mendukung pendaftaran (`/register`), masuk (`/login`), profil akun (`/account`), dan keluar (`/logout`) menggunakan `SessionMiddleware` serta enkripsi kata sandi **PBKDF2-HMAC-SHA256** pada tabel `users`.
- **Beranda & Halaman Tim (`GET /`, `GET /contact`)**: Menyajikan alur kerja deteksi 3 langkah, ringkasan hasil yang didapatkan pengguna, profil anggota kelompok, serta spesifikasi teknis proyek.
- **Pindai & Inferensi Real-Time (`GET /scan`, `POST /predict`)**: Mendukung format **JPG, JPEG, PNG, dan WebP** (maksimal **10 MB**, 20 juta piksel, 8.192 px per sisi) dengan validasi berlapis (ekstensi, ukuran, *magic bytes*, dan `ImageInputError`/`ModelError`), pratinjau instan di browser, serta visualisasi skor keyakinan `0–100` dan 4 kategori risiko.
- **Manajemen Riwayat CRUD PostgreSQL (`POST /history/save`, `GET /history`, `POST /history/{id}/delete`)**: Menyimpan hasil pemindaian beserta catatan ke tabel `scan_history` di PostgreSQL (**Create**), menampilkan dan memfilter riwayat berdasarkan status atau tanggal (**Read**), serta menghapus data database beserta file gambar fisiknya di server (**Delete**).

---

## 2. Struktur Proyek Utama
```text
TrueLensAI/
├── ai_package_v2/
│   └── truelens-image-detector/   # Paket inferensi PyTorch v1.0.0 + bobot model + smoke_test.py
├── ai/                            # Skrip referensi pelatihan & evaluasi model
├── database/
│   └── truelens_db.sql            # Skema DDL PostgreSQL (tabel users & scan_history)
├── app/
│   ├── main.py                    # Entry point FastAPI, SessionMiddleware, & create_all()
│   ├── config.py                  # Koneksi PostgreSQL (SQLModel engine & get_session)
│   ├── models/truelens_model.py   # Model tabel ORM User & Prediction_history
│   ├── schemas/truelens_schema.py # Skema validasi input (TrueLensData, UserRegister, UserLogin)
│   ├── routes/                    # auth.py, pages.py, scan.py, history.py, common.py
│   ├── services/                  # prediction_service.py, history_service.py, user_service.py, common.py
│   ├── model_ai/                  # model_truelens_metadata.json
│   ├── templates/                 # Template Jinja2 (base, home, scan, result, history, contact, account, dll.)
│   └── static/                    # CSS modular, app.js, gambar tim, & folder uploads/
├── requirements.txt
└── .gitattributes                 # Melindungi integritas checksum file di ai_package_v2/

#1. Buat dan aktifkan virtual environment (dari folder root proyek)
python -m venv venv
# Windows (PowerShell):
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\venv\Scripts\Activate.ps1
# macOS / Linux:
# source venv/bin/activate

# 2. Instal dependensi web & PyTorch (versi CPU)
pip install "fastapi[standard]" sqlmodel itsdangerous "psycopg[binary]" jinja2 python-multipart pillow numpy
pip install torch torchvision --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# 3. Instal paket inferensi ai_package_v2 secara editable
python -m pip install --no-deps --ignore-requires-python -e .\ai_package_v2\truelens-image-detector

# 4. Uji mandiri paket AI (12 checks)
python .\ai_package_v2\truelens-image-detector\smoke_test.py --device cpu
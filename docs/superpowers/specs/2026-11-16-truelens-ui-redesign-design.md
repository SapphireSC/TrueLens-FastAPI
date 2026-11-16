# Desain Perombakan UI TrueLens AI

**Tanggal:** 2026-11-16
**Status:** Disetujui untuk diimplementasikan
**Scope:** Perombakan tampilan seluruh halaman publik. Logika, endpoint, skema database, dan alur fitur yang sudah ada **tidak diubah**.
**Stack:** FastAPI + Jinja2 + HTML/CSS/JS + PostgreSQL/SQLite
**Bahasa antarmuka:** Indonesia
**Mode warna:** Light forensic-clinical (dipertahankan)

---

## 1. Ringkasan

Perombakan tampilan TrueLens AI dengan teknik visual yang dipinjam dari tiga referensi Dribbble (`docs/reference-design/`), **tanpa** melanggar sistem desain yang sudah ditetapkan proyek di `DESIGN.md` dan `docs/plan/UI_DESIGN_TrueLensAI.md`.

Tiga teknik yang dipinjam:

1. **Bar input ringkas di hero** (dari referensi *Conceptzilla*) — diganti dari viewfinder dekoratif menjadi formulir unggah yang benar-benar bekerja.
2. **Cuplikan UI asli** (dari referensi *Stacker*) — digantikan window/browser chrome palsu dengan panel keluaran model yang dirender langsung dari macro yang sudah ada.
3. **Baris metrik model** (dari referensi *Walos*) — hanya dirender jika metrik evaluation benar-benar tersedia.

Tiga teknik yang **dibuang** beserta alasannya ada di §4.2.

---

## 2. Konteks dan batasan

### 2.1 Audiens

Prototipe UAS. Penilai adalah dosen dan juri yang menilai dua hal: apakah sistem benar-benar bekerja, dan apakah angka-angka yang ditampilkan kredibel. Setiap keputusan visual di bawah memakai satu tolok ukur: menampilkan sesuatu yang palsu akan lebih berbahaya daripada tampilannya biasa-biasa saja.

### 2.2 Aturan yang mengikat

`DESIGN.md` §2 dan `docs/plan/UI_DESIGN_TrueLensAI.md` §2/§11 menetapkan hal yang **sengaja tidak dipakai** proyek ini:

- Gradient dekoratif, neon, glow, glassmorphism.
- Background grid atau blueprint dekoratif.
- Bento grid, kartu fitur seragam, logo bar "trusted by", testimoni karangan.
- Fake terminal window.
- Eyebrow badge di atas H1 dan status dot dekoratif.
- Statistik atau delta persentase yang tidak berasal dari data nyata.
- Emoji sebagai ikon atau hiasan copy.

Disiplin aksen (`DESIGN.md` §2): **biru hanya untuk aksi utama, tautan, fokus, dan meter keyakinan.** Hijau dan merah hanya untuk status hasil. Amber hanya untuk peringatan. Shadow hanya pada dua permukaan fokus: kartu unggah dan panel hasil. Radius: 8px kontrol, 12px kartu, 10px alert, 999px hanya untuk badge status.

### 2.3 Model belum dilatih

`ai/saved_model/evaluation_metrics.json` saat ini berisi `"evaluated": false` dengan seluruh metrik `null`, dan file `ai/saved_model/truelens_efficientnet.keras` belum ada. `app/services/scan_engine.py` jatuh ke mode pratinjau deterministik berbasis SHA-256.

Konsekuensi: **angka performa model (accuracy, precision, recall, F1) tidak boleh tampil sebelum diukur.** Lihat §5.4 untuk mekanisme yang aman.

### 2.4 Batas perubahan

Tidak disentuh:

| Area | File |
|---|---|
| Route dan endpoint | `app/routes/*.py` (kecuali penambahan konteks template di `home.py`) |
| Skema database dan model ORM | `app/models.py`, `app/database.py`, `database/truelens_db.sql` |
| Logika deteksi | `app/services/scan_engine.py` |
| Autentikasi, sesi, bcrypt | `app/routes/auth.py` |
| Logika modal auth dan password toggle | `app/static/js/app.js` (bagian yang sudah berjalan) |
| Token warna yang sudah ada | `app/static/css/tokens.css` |

Tidak ada perintah lint atau typecheck yang dikarang — proyek memang tidak punya konfigurasi seperti itu.

---

## 3. Peta perubahan per file

| File | Tipe | Perubahan |
|---|---|---|
| `app/templates/partials/scan_form.html` | **Baru** | Satu partial berisi formulir unggah: dropzone, pratinjau berkas, kotak error klien, tombol submit. Dipakai di hero Beranda **dan** di halaman Pindai. |
| `app/templates/home.html` | Ubah | Hero baru; viewfinder dekoratif dihapus; panel contoh keluaran; disclosure metrik kondisional. |
| `app/templates/scan.html` | Ubah | Memakai partial yang sama; gaya dropzone penuh dipertahankan; panel panduan dipertahankan. |
| `app/templates/result.html` | Ubah | Tombol simpan untuk tamu diganti CTA masuk; panel hasil diselaraskan. |
| `app/templates/history.html` | Ubah | Penyelarasan visual tabel dan filter. |
| `app/templates/contact.html` | Ubah | Penyelarasan visual kartu peran. |
| `app/templates/account.html` | Ubah | Penyelarasan visual. |
| `app/templates/error.html` | Ubah | Penyelarasan visual. |
| `app/templates/confirm_delete.html` | Ubah | Penyelarasan visual. |
| `app/static/css/base.css` | Ubah | Tambah reset `[hidden]`. |
| `app/static/css/components.css` | Ubah | Tambah gaya `.scan-bar`, `.file-preview-name`, `.file-preview-size`, `.dropzone-title`. |
| `app/static/css/pages.css` | Ubah | `.hero-grid` disusun ulang; hapus `.viewfinder-frame`, `.vf-corners`, `.vf-scanline`. |
| `app/routes/home.py` | Ubah kecil | Kirim konteks `sample_analysis` dan `format_id_number` ke template. |
| `tests/test_ui_contract.py` | **Baru** | Pemeriksaan kontrak UI berbasis `assert` (tanpa pytest). |

---

## 4. Keputusan visual

### 4.1 Teknik yang dipinjam

**4.1.1 Bar input ringkas di hero (dari referensi Conceptzilla)**

Referensi memakai bar input bergaya prompt sebagai titik fokus utama hero. Di TrueLens, bar ini menjadi formulir unggah sungguhan: `<form action="/predict" method="post" enctype="multipart/form-data">` dengan input file asli, dukungan drag-and-drop, dan tombol submit yang disabled + spinner selama pemrosesan.

Adaptasi terhadap aturan proyek: latar putih `--color-surface`, border `--color-border`, satu `shadow-focus-card` (izin untuk "kartu unggah"), tanpa glassmorphism, tanpa chip format berwarna.

**4.1.2 Cuplikan UI asli (dari referensi Stacker)**

Referensi memakai window browser palsu sebagai elemen visual hero. Di TrueLens, digantikan **panel keluaran model yang dirender langsung** memakai macro `status_badge`, `confidence_meter`, dan `probability_scale` yang sudah ada — markup identik dengan halaman `/result`, bukan gambar.

Panel diberi badge **Contoh** sesuai prinsip no. 4 di `UI_DESIGN_TrueLensAI.md` §1 dan konvensi baris seed riwayat.

**4.1.3 Baris metrik model (dari referensi Walos)**

Referensi menampilkan empat metrik performa sebagai baris angka besar. Di TrueLens, metrik ini **hanya dirender jika benar-benar tersedia** — lihat §5.4. Versi ini jujur dan tersedia otomatis begitu model selesai dilatih.

### 4.2 Teknik yang dibuang

| Teknik | Alasan dibuang |
|---|---|
| Satu kata disorot di H1 | `DESIGN.md` §2: biru hanya untuk aksi utama, tautan, fokus, dan meter keyakinan. Menyorot kata di H1 melanggar disiplin aksen. Fokus visual diletakkan pada formulir unggah, bukan pada hiasan tipografi. |
| Baris metrik di hero | Model belum dilatih (§2.3). Angka di hero akan jadi karangan. Dipindah ke disclosure kondisional di §5.4. |
| Glow, gradient, chip melayang, dark mode | Langsung dilarang `DESIGN.md` §2 dan §11. |

### 4.3 Bentuk hero baru

```text
+----------------------------------------------------------------------+
| [ikon] TrueLens AI                    Beranda  Pindai  Riwayat  Kontak|
+----------------------------------------------------------------------+
| H1: Lihat lebih dekat sebelum mempercayai sebuah gambar.            |
| Lede: memindai JPG/PNG, label Real atau AI-Generated                 |
| +----------------------------------------------------------+        |
| | [ Unggah gambar atau tarik ke sini ] | [ Pindai gambar ]  |        |
| |   JPG, JPEG, atau PNG · maksimal 10 MB                    |        |
| +----------------------------------------------------------+        |
| [Lihat riwayat]  Catatan: alat bantu analisis visual, bukan ...    |
+-----------------------------------+------------------------------+
| Panel contoh keluaran model       |  (kolom kanan 5fr)           |
| badge Contoh + badge AI-Generated |                              |
| Sintetis AI (Synthetic AI-Generated)                              |
| Keyakinan model ......... 91,2%                                    |
| [meter track]                                                |
| Probabilitas AI (p) ....... p = 0,912                             |
| [4 segmen + penanda]                                            |
| legenda 4 rentang                                               |
| Contoh keluaran model, bukan bukti forensik.                      |
+------------------------------------------------------------------+
```

Kolom kiri `7fr`, kolom kanan `5fr`, sejajar ke atas. Di bawah 1024px menjadi satu kolom, panel contoh keluaran turun ke bawah hero.

Motif identitas **viewfinder / scan frame** tidak dihapus: bentuknya pindah menjadi sudut bracket pada dropzone hero dan markup `<span class="vf-corner">` di empat sudut zona unggah.

---

## 5. Detail komponen

### 5.1 Partial `app/templates/partials/scan_form.html`

Markup berikut adalah kontrak dengan `app/static/js/app.js`. **ID tidak boleh diubah** — `app.js` mencarinya dengan `getElementById`.

```html
{# Formulir unggah gambar.
   Dipakai di hero Beranda (/) dan halaman Pindai (/scan).
   ID di bawah WAJIB sama dengan yang dibaca app/static/js/app.js.
   app.js mencari satu form per halaman, jadi partial ini hanya boleh
   dipakai satu kali per halaman. #}
{% from "partials/macros.html" import icon %}

<form
  id="scan-form"
  class="scan-form{% if compact %} scan-form--compact{% endif %}"
  action="{{ url_for('predict') }}"
  method="post"
  enctype="multipart/form-data"
  novalidate
>
  <div id="upload-dropzone" class="dropzone">
    <span class="vf-corner vf-corner-tl" aria-hidden="true"></span>
    <span class="vf-corner vf-corner-tr" aria-hidden="true"></span>
    <span class="vf-corner vf-corner-bl" aria-hidden="true"></span>
    <span class="vf-corner vf-corner-br" aria-hidden="true"></span>

    <input
      type="file"
      id="image-file-input"
      name="file"
      accept=".jpg,.jpeg,.png,image/jpeg,image/png"
      class="dropzone-input"
      aria-describedby="dropzone-helper"
      required
    />

    <div class="dropzone-icon">{{ icon('upload', 28) }}</div>
    <div class="dropzone-title">Unggah gambar atau tarik berkas ke sini</div>
    <div id="dropzone-helper" class="text-muted">
      JPG, JPEG, atau PNG · maksimal 10 MB
    </div>
  </div>

  <div id="file-preview-container" class="file-preview-bar" hidden>
    <div class="file-preview-info">
      <img id="file-preview-thumb" class="file-preview-thumb" src="" alt="" />
      <div>
        <div id="file-preview-name" class="file-preview-name"></div>
        <div id="file-preview-size" class="file-preview-size mono"></div>
      </div>
    </div>
    <button
      type="button"
      id="clear-file-btn"
      class="btn-icon"
      aria-label="Hapus berkas yang dipilih"
    >
      {{ icon('x', 18) }}
    </button>
  </div>

  <div id="client-error-box" class="alert alert-danger" role="alert" hidden>
    {{ icon('triangle-alert', 20) }}
    <div id="client-error-text"></div>
  </div>

  <button type="submit" id="scan-submit-btn" class="btn btn-primary">
    Pindai gambar
  </button>
</form>
```

Catatan:
- `dropzone-input` sudah `position: absolute; inset: 0; opacity: 0` di `components.css`, sehingga input tetap fokusabel dan dapat dibuka dengan keyboard.
- `alt=""` pada thumbnail: dekoratif, nama berkas tercetak di sebelahnya (`UI_DESIGN_TrueLensAI.md` §7.2).
- `role="alert"` pada kotak error agar diumumkan pembaca layar.

### 5.2 Reset `[hidden]` — wajib

`components.css` tidak punya reset `[hidden]`, sedangkan `.file-preview-bar` memakai `display: flex` dan `.alert` juga `display: flex`. Tanpa reset, atribut `hidden` **tidak akan menyembunyikan** keduanya dan keduanya akan terlihat selalu.

Tambahkan di `app/static/css/base.css`:

```css
[hidden] {
  display: none !important;
}
```

### 5.3 Gaya bar input `.scan-bar`

Token yang dipakai (semua sudah ada, tidak ada token baru):

| Properti | Nilai |
|---|---|
| Latar | `--color-surface` |
| Border | `1px solid var(--color-border)` |
| Radius | `--radius-card` (12px) |
| Shadow | `--shadow-focus-card` (satu-satunya izin shadow untuk "kartu unggah") |
| Radius zona dalam | `--radius-control` (8px) |
| Padding | `--space-3` (12px) |

`.scan-form--compact` (hero): dropzone dan tombol submit dalam satu baris, `gap: var(--space-3)`, tombol `align-self: stretch`. Di bawah 640px membungkus ke dua baris, tombol full-width.

Tanpa modifier compact (halaman Pindai): dropzone vertikal seperti sekarang, tombol full-width di bawahnya.

CSS yang perlu ditambahkan di `app/static/css/components.css`:

```css
/* Bar input ringkas untuk hero Beranda */
.scan-form--compact .dropzone {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex: 1;
  min-width: 0;
  padding: var(--space-3) var(--space-4);
  text-align: left;
}

.scan-form--compact .dropzone-icon {
  margin: 0;
  flex-shrink: 0;
}

.scan-form--compact .dropzone-title {
  font-weight: 600;
  color: var(--color-text-strong);
}

.scan-form--compact #scan-submit-btn {
  align-self: stretch;
}

/* Sudut bracket viewfinder — motif identitas di dalam zona unggah */
.vf-corner {
  position: absolute;
  width: 14px;
  height: 14px;
  border-color: var(--color-border-strong);
  border-style: solid;
  border-width: 0;
  pointer-events: none;
}

.vf-corner-tl { top: 6px; left: 6px; border-top-width: 2px; border-left-width: 2px; }
.vf-corner-tr { top: 6px; right: 6px; border-top-width: 2px; border-right-width: 2px; }
.vf-corner-bl { bottom: 6px; left: 6px; border-bottom-width: 2px; border-left-width: 2px; }
.vf-corner-br { bottom: 6px; right: 6px; border-bottom-width: 2px; border-right-width: 2px; }
```

Penting: `.dropzone-input` memakai `position: absolute; inset: 0` sehingga input menutupi seluruh zona. Sudut bracket diberi `pointer-events: none` agar tidak mengganggu klik pada input, dan tidak boleh berada di atas input dalam urutan stacking — karena `input` sudah positioned, span sudut diletakkan **sebelum** input di dalam markup agar input tetap berada di atas.

### 5.4 Disclosure metrik model (kondisional)

`app/routes/home.py` sudah memanggil `load_evaluation_metrics()` dan mengirim `metrics` ke template, tetapi `home.html` tidak pernah merendernya. utilized sambungan ini.

Di section "Tentang Model & Data", tambahkan disclosure native `<details>` **hanya** bila metrik tersedia:

```jinja
{% if metrics and metrics.evaluated %}
<details class="tech-details">
  <summary class="tech-summary">Hasil evaluasi model</summary>
  <div class="tech-body">
    <div class="spec-list">
      <div class="spec-row"><span class="spec-term">Accuracy</span><span class="spec-val mono">{{ format_id_number(metrics.accuracy, 1) }}%</span></div>
      <div class="spec-row"><span class="spec-term">Precision</span><span class="spec-val mono">{{ format_id_number(metrics.precision, 1) }}%</span></div>
      <div class="spec-row"><span class="spec-term">Recall</span><span class="spec-val mono">{{ format_id_number(metrics.recall, 1) }}%</span></div>
      <div class="spec-row"><span class="spec-term">F1-Score</span><span class="spec-val mono">{{ format_id_number(metrics.f1_score, 1) }}%</span></div>
      <div class="spec-row"><span class="spec-term">ROC-AUC</span><span class="spec-val mono">{{ format_id_number(metrics.roc_auc, 4) }}</span></div>
      <div class="spec-row"><span class="spec-term">Data uji</span><span class="spec-val mono">{{ format_id_number(metrics.test_samples, 0) }} citra</span></div>
      <div class="spec-row"><span class="spec-term">Ambang keputusan</span><span class="spec-val mono">p &ge; {{ format_id_number(metrics.threshold, 2) }}</span></div>
    </div>
  </div>
</details>
{% endif %}
```

Skala angka mengikuti `ai/evaluate_model.py`: accuracy/precision/recall/F1 sudah dikali 100 (persen), ROC-AUC tetap 0–1.

`format_id_number` perlu dikirim ke konteks template. Di `app/routes/home.py`:

```python
from app.services.scan_engine import format_id_number
...
"format_id_number": format_id_number,
```

Sebelum model dilatih, `metrics.evaluated` bernilai `False` dan blok ini tidak dirender sama sekali — tidak ada angka yang tampil.

### 5.5 Panel contoh keluaran di hero

Nilai contoh diambil dari jalur kode yang sama dengan hasil nyata, agar tidak ada angka yang diketik manual:

```python
# app/routes/home.py
sample_analysis = TrueLensScanEngine.map_probability_to_result(0.912)
sample_analysis.update({
    "inference_mode": "Contoh keluaran model",
    "is_live_model": False,
})
```

`map_probability_to_result(0.912)` menghasilkan `predicted_label` = `AI-Generated`, `confidence_score` = `91.2`, `confidence_display` = `91,2`, `raw_prob` = `0.912`, `raw_prob_display` = `0,912`, `marker_percent` = `91.2`, `tier_code` = `synthetic`, `risk_tier` = `Sintetis AI (Synthetic AI-Generated)`.

Panel memakai `status_badge`, `confidence_meter`, dan `probability_scale` apa adanya:

```jinja
<div class="panel-elevated hero-sample">
  <div class="hero-sample-head">
    <span class="badge badge-sample">Contoh</span>
    {{ status_badge(analysis.predicted_label) }}
  </div>
  <h2 class="hero-sample-title">{{ analysis.risk_tier }}</h2>
  <p class="text-muted">{{ analysis.tier_desc }}</p>
  {{ confidence_meter(analysis.confidence_score, analysis.confidence_display) }}
  {{ probability_scale(analysis.marker_percent, analysis.tier_code, analysis.raw_prob_display) }}
  <p class="text-muted hero-sample-foot">
    Contoh keluaran model untuk satu gambar. Bukan bukti forensik atau putusan hukum.
  </p>
</div>
```

### 5.6 Tombol simpan untuk tamu

Tamu (`current_user` kosong) tidak dapat menyimpan hasil: `POST /history/save` membuat record dengan `user_id=None`, sedangkan `GET /history` untuk tamu hanya menampilkan record `is_sample == True`. Record semacam itu tidak pernah terlihat siapa pun.

Perbaikan dilakukan **sepenuhnya di layer template** — endpoint tidak disentuh. Di `result.html`, blok form simpan diganti CTA masuk bila tidak ada sesi:

```jinja
{% if current_user %}
  <form action="{{ url_for('history_save') }}" method="post">
    ... input tersembunyi seperti sekarang ...
  </form>
{% else %}
  <div class="save-gate">
    <p class="text-muted">
      Masuk untuk menyimpan hasil pemindaian ini ke riwayat Anda.
    </p>
    <a href="{{ url_for('login') }}" class="btn btn-primary">Masuk untuk menyimpan</a>
  </div>
{% endif %}
```

### 5.7 Halaman lain

Selain Beranda, Pindai, dan Hasil, perubahan pada halaman lain hanya **penyelarasan visual**: jarak (padding dan gap diseragamkan ke skala `--space-*`), tipografi, konsistensi border 1px `--color-border` dan radius 12px pada kartu, serta penyesuaian tinggi target sentuh ke minimal 44px. **Struktur section, isi teks, dan setiap perilaku interaktif tetap apa adanya** — tidak ada markup halaman lain yang dipindah atau dihapus.

| Halaman | Penyesuaian |
|---|---|
| Riwayat | Padding tabel, konsistensi `.spec-row`, baris filter diseragamkan |
| Kontak | `.role-grid` diseragamkan jaraknya, `.role-card` memakai radius 12px |
| Akun | Konsistensi `.panel` dan `.spec-list` |
| Error | Konsistensi `.panel` dan tombol |
| Konfirmasi hapus | Konsistensi `.panel-elevated` dan `.alert-danger` |

Catatan: setelah ekstraksi, `scan.html` tidak lagi memakai macro `icon` secara langsung, sehingga baris `{% from "partials/macros.html" import icon %}` di sana boleh dihapus. `home.html` tetap membutuhkannya untuk blok lain.

---

## 6. Alur data

Tidak berubah. Rantai yang sama untuk hero dan halaman Pindai:

```text
<form enctype="multipart/form-data" action="/predict">
  → validasi server: file ada, ekstensi .jpg/.jpeg/.png, ukuran ≤ 10 MB, magic bytes PNG/JPEG
  → simpan ke UPLOAD_DIR dengan nama token acak
  → scan_engine.analyze_image()
  → map_probability_to_result(p)
  → render result.html
```

Perbedaannya hanya letak form: di hero, atau di halaman `/scan`. `POST /predict` tidak memeriksa sesi, sehingga tamu dan user login memakai alur identik.

`GET /scan` tetap mengarahkan tamu ke `/login` (perilaku existing, tidak diubah).

---

## 7. Penanganan error

| Situasi | Sumber | Tampilan |
|---|---|---|
| Tidak ada file dipilih | Klien | "Pilih satu file gambar." di kotak `client-error-box` |
| Lebih dari satu file | Klien | "Pilih satu file gambar." |
| Format salah | Klien + server | "Format harus JPG, JPEG, atau PNG." |
| Ukuran > 10 MB | Klien + server | "Ukuran file melebihi 10 MB." |
| Isi bukan gambar | Server | "Isi file tidak cocok dengan format gambar yang didukung." |
| Model belum dilatih | Engine | Badge "Pratinjau" + mode inferensi di panel hasil |
| Tamu ingin menyimpan | Template | CTA "Masuk untuk menyimpan" |
| 404 / 500 | `app/main.py` | `error.html` |

Aturan yang berlaku: pesan selalu menyebut penyebab dan langkah berikutnya; input pengguna tidak dihapus atau diganti data contoh; validasi batas kepercayaan tetap di server (`UI_DESIGN_TrueLensAI.md` §7.1).

---

## 8. Aksesibilitas

Tidak ada penurunan dari `UI_DESIGN_TrueLensAI.md` §7.2:

- Fokus ring 3px `--color-focus` dengan `:focus-visible`; input file tetap fokusabel di dalam dropzone.
- Target sentuh minimal 44×44px, termasuk tombol hapus berkas dan tombol submit.
- Pesan error memakai `role="alert"`; spinner memakai `aria-busy="true"` pada tombol.
- Ikon dekoratif `aria-hidden="true"`; ikon pada badge status berpasangan dengan teks.
- Disclosure memakai `<details>` native sehingga tetap terbuka tanpa JavaScript.
- `prefers-reduced-motion: reduce` tetap mematikan transisi non-esensial.
- Tidak ada horizontal scroll pada 375px.

---

## 9. Verifikasi

### 9.1 Pemeriksaan kontrak UI

`tests/test_ui_contract.py` — berbasis `assert` biasa, **tanpa pytest** (pytest tidak terpasang di lingkungan ini; `httpx` sudah tersedia untuk `fastapi.testclient.TestClient`). Dijalankan dengan:

```bash
source .venv/bin/activate && python tests/test_ui_contract.py
```

Pemeriksaan:

1. `GET /` → 200, dan HTML memuat seluruh 11 ID yang dibaca `app/static/js/app.js`: `scan-form`, `image-file-input`, `upload-dropzone`, `file-preview-container`, `file-preview-thumb`, `file-preview-name`, `file-preview-size`, `clear-file-btn`, `client-error-box`, `client-error-text`, `scan-submit-btn`.
2. `GET /scan` → 200, dan memuat ID yang sama.
3. `GET /` dan `GET /scan` tidak lagi memuat kelas `.viewfinder-frame`.
4. `GET /preview/result` → 200 dan memuat `.meter-track` serta `.prob-segments`.
5. `GET /` → tidak memuat nilai metrik apa pun (misalnya "93,4%") saat `evaluation_metrics.json` belum terisi, sehingga tidak ada angka karangan yang bocor ke halaman publik.

Poin (1) adalah penjaga utama: ID yang hilang itu adalah bug yang membuat seluruh validasi klien mati.

### 9.2 Cek manual

- 375px, 768px, 1024px, 1440px — tanpa horizontal scroll.
- Hero: unggah file secara langsung dari Beranda → halaman Hasil terbuka.
- Dropzone: drag-drop, pilih file, hapus berkas, kirim → spinner "Menganalisis…" muncul.
- Tamu: memindai dari hero → hasil → tombol "Masuk untuk menyimpan" → `/login`.
- Login → hero → "Simpan ke riwayat" → record muncul di `/history`.
- Fokus keyboard pada seluruh form; `Enter`/`Space` membuka pemilih berkas.
- Kontras teks tetap memenuhi AA; `--color-accent` tidak dipakai sebagai warna teks.

---

## 10. Risiko dan batasan

| Risiko | Mitigasi |
|---|---|
| `app.js` mencari ID tunggal, jadi dua form dalam satu halaman tidak akan bekerja | Partial didokumentasikan "satu kali per halaman"; pemeriksa kontrak menyegel ini |
| Atribut `hidden` tidak menyembunyikan elemen ber-`display: flex` | Reset `[hidden]` di `base.css` (§5.2) |
| Hero yang memuat form membuat `/predict` lebih mudah dijangkau tamu, sehingga risiko record yatim naik | CTA masuk untuk tamu di `result.html` (§5.6) |
| Panel contoh keluar bisa disalahartikan sebagai keluaran nyata | Badge **Contoh** + disclaimer di kaki panel; label `Contoh` mengikuti konvensi yang sudah dipakai di baris seed riwayat |
| Metrik baru muncul setelah model dilatih dan mungkin terlihat "melompat" | Disclosure tersembunyi sampai `metrics.evaluated` bernilai `true`; format persen mengikuti `evaluate_model.py` |

---

## 11. Traceability

| Keputusan | Sumber |
|---|---|
| Aturan visual, disiplin aksen, larangan dekorasi | `DESIGN.md` §2, §11; `docs/plan/UI_DESIGN_TrueLensAI.md` §2, §11 |
| Struktur halaman dan komponen | `docs/plan/UI_DESIGN_TrueLensAI.md` §4, §5 |
| Validasi file dan aturan batas kepercayaan | `docs/plan/UI_DESIGN_TrueLensAI.md` §7.1 |
| Aturan aksesibilitas | `docs/plan/UI_DESIGN_TrueLensAI.md` §7.2 |
| Prinsip label `Contoh` untuk data pratinjau | `docs/plan/UI_DESIGN_TrueLensAI.md` §1 prinsip 4, §5.5 |
| Larangan menampilkan metrik sebelum diukur | `docs/plan/UI_DESIGN_TrueLensAI.md` §4.2, §10.4 |
| Skala angka metrik | `ai/evaluate_model.py` baris 56–59 |
| Pemformatan angka Indonesia | `app/services/scan_engine.py` `format_id_number` |
| Referensi visual | `docs/reference-design/` (3 berkas yang dianalisis) |
| Arah desain dan batasan redesign | `docs/superpowers/specs/2026-11-12-truelens-redux-design.md` |

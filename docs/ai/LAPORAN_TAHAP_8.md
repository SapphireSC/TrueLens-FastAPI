# Laporan tahap 8 — evaluasi test final

Run `TEST8_20261111_233913_703812`. Kandidat tetap R2 epoch9, threshold0,55 (FAKE jika score>=threshold). Model SHA-256 `c865f002bd1520fc115d005a71b901640dc14f89009b431c94d1941999d97913`.

Protokol evaluation_protocol.json disimpan sebelum model memprediksi test. Macro-F1 metrik utama; accuracy, metrik per kelas, confusion matrix, ROC-AUC dan average precision FAKE pendamping. Tidak memilih model/threshold melalui test. Test unik adalah subset prediksi test resmi, bukan dataset independen kedua.

Predictor.from_frozen_candidate benar-benar memuat bobot neural (tanpa mock/fallback), arsitektur weights=None, torch.load CPU/weights_only=True dan strict=True. Fixture validation tetap diverifikasi CPU dengan atol1e-6/rtol1e-5. Label referensi dihitung pada threshold0,55, bukan menuntut label threshold0,5. Lihat neural_load_check.json.

Seluruh gambar test dibaca per batch, SHA-256 byte dicocokkan manifest sebelum decoder resmi, tanpa mengubah/menulis gambar. Tidak ada optimizer/backward/augmentasi/update BatchNorm. Berkas JSON atomik per batch menyimpan hasil dan signature model/config/input. ID dipastikan unik dan lengkap.

| Kelompok | N | Accuracy | Macro-F1 | ROC-AUC FAKE | Average precision FAKE | REAL→FAKE | FAKE→REAL |
|---|---:|---:|---:|---:|---:|---:|---:|
| Test resmi (utama) | 20000 | 0.96490000 | 0.96489997 | 0.99503288 | 0.99512374 | 360 | 342 |
| Test unik (pendamping) | 19962 | 0.96493337 | 0.96493334 | 0.99503227 | 0.99510671 | 360 | 340 |

| Kelompok/kelas | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| Resmi/REAL | 0.96573833 | 0.96400000 | 0.96486838 | 10000 |
| Resmi/FAKE | 0.96406468 | 0.96580000 | 0.96493156 | 10000 |
| Unik/REAL | 0.96593186 | 0.96400000 | 0.96496496 | 10000 |
| Unik/FAKE | 0.96393508 | 0.96587031 | 0.96490172 | 9962 |

Confusion matrix urutan REAL/FAKE (baris benar, kolom prediksi): resmi `[[9640, 360], [342, 9658]]`, unik `[[9640, 360], [340, 9622]]`. Benar/salah resmi 19298/702; unik 19262/700.

Test resmi memiliki10.000 REAL/10.000 FAKE. Test unik memiliki10.000 REAL/9.962 FAKE karena38 salinan duplikat internal test berlabel sama memakai satu wakil per grup. Prediksi unik diturunkan berdasarkan sample ID dari inferensi resmi yang sama, tanpa inferensi neural kedua.

Validation terpilih: accuracy 0.96616180, macro-F1 0.96615793. Test resmi − validation: accuracy -0.00126180, macro-F1 -0.00125796. Ini perbandingan deskriptif; validation telah dipakai untuk seleksi sehingga bukan evaluasi independen. Test tidak dijanjikan harus menyamai atau melampaui validation.

REAL→FAKE adalah false positive untuk kelas positif FAKE: foto natural ditandai sebagai indikasi AI. FAKE→REAL adalah false negative: gambar AI terlewat. Kedua jenis kesalahan dilaporkan apa adanya tanpa mengganti threshold/model atau memberi label ulang data. Daftar semua kesalahan di misclassified_test.csv; tidak ada contoh yang dipilih untuk tuning.

ROC-AUC dan average precision memakai skor FAKE kontinu, bukan label prediksi. Average precision dihitung oleh sklearn.average_precision_score (non-interpolated weighted precision over recall increments); bukan menyamakan semua definisi area PR atau integral trapezoidal.

![Confusion matrix](confusion_matrix.png)

![ROC dan PR](roc_pr.png)

Perangkat cuda, batch 32, workers0. Pemuatan model 0.424s; pemeriksaan fixture 0.974s; pemrosesan batch test aktif 151.122s; seluruh invocation 158.285s sebelum render/laporan. Throughput batch 132.344 sampel/detik dan rerata pemrosesan batch per sampel 0.007556s. Bukan waktu respons website. Resume mengecualikan waktu proses berhenti dari waktu aktif.

Hash seluruh parameter dan buffer model sebelum/sesudah identik; kandidat beku asli, konfigurasi keputusan, manifest dan artefak lama tetap identik. frozen_candidate.json asli tetap test_evaluated=false sebagai rekaman saat pembekuan; evaluation_record.json terpisah mencatat test_evaluated=true dengan hash dokumen beku yang dipakai.

Artefak: `reports\stage_8\TEST8_20261111_233913_703812` berisi prediksi test/test_unique, berkas batch JSON, metrik JSON, protokol/config, timing, checksum, log/status dan evaluation_record.json. Perintah resume:

```powershell
Set-Location -LiteralPath 'C:\Users\hp victus\Downloads\TrueLens AI'
.\.venv\Scripts\python.exe -u -m truelens_ai.evaluate_test run --resume TEST8_20261111_233913_703812
```

Run passed hanya diperiksa integritasnya; tidak diprediksi ulang. Hasil parsial dipakai bila signature model/config/manifest cocok, urutan ID/metadata konsisten, dan bytes input yang sudah diproses masih cocok. Batch tak ter-commit boleh diulang; hasil final setiap ID tepat sekali. Error file dicatat dan menghentikan evaluasi lengkap, tanpa skip diam-diam.

**Siap secara teknis untuk tahap9: pengemasan model bagi backend.** Tahap9 belum dikerjakan. Hasil hanya berlaku pada protokol CIFAKE ini; belum membuktikan deteksi seluruh generator AI/foto dunia nyata. Skor sigmoid bukan jaminan persentase keaslian. Tidak ada training, tuning threshold, penggantian kandidat, website/database atau deployment.

Waktu invocation keseluruhan termasuk render/laporan: 162.009 detik (tidak termasuk pemeriksaan checksum keluaran paling akhir).

## Verifikasi akhir independen dari inferensi

16 uji perangkat lunak lulus (4 pengujian tahap8 pada fixture sintetis dan12 pemeriksaan tahap7). Ini berbeda dari20fixture validation neural CPU sebenarnya dan evaluasi final20.000test. Log keduanya disalin ke folder ini. Seluruh CSV diperiksa ulang: setiap ID tepat sekali, skor sigmoid/label threshold konsisten, test_unique subset persis, dan semua metrik dihitung ulang dari skor tersimpan. Protokol mendahului inferensi, checksum sumber/kandidat/artefak lama tetap cocok. Detail final_verification.json.

-- Jalankan perintah CREATE DATABASE ini di psql / pgAdmin bila database belum ada:
-- CREATE DATABASE truelens_db;

CREATE TABLE IF NOT EXISTS scan_history (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    file_size_kb DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    resolution VARCHAR(50) NOT NULL DEFAULT 'Unknown',
    predicted_label VARCHAR(50) NOT NULL CHECK (predicted_label IN ('Real', 'AI-Generated')),
    risk_tier VARCHAR(80) NOT NULL,
    confidence_score DOUBLE PRECISION NOT NULL,
    raw_prob DOUBLE PRECISION NOT NULL,
    notes TEXT DEFAULT NULL,
    is_sample BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scan_history_label ON scan_history (predicted_label);
CREATE INDEX IF NOT EXISTS idx_scan_history_created_at ON scan_history (created_at DESC);

-- ============================================================================
-- DATA SAMPEL AWAL (BERLABEL CONTOH / SEED DATA UNTUK DEMONSTRASI AWAL)
-- ============================================================================
INSERT INTO scan_history (
    filename, image_path, file_size_kb, resolution,
    predicted_label, risk_tier, confidence_score, raw_prob,
    notes, is_sample, created_at
) VALUES
(
    'sample_stage_concert_photo.jpg',
    '',
    412.5,
    '1920x1080',
    'Real',
    'Citra asli (Authentic Real Image)',
    88.70,
    0.1130,
    'Contoh data awal: dokumentasi panggung konser kamera DSLR',
    TRUE,
    '2026-11-09 19:15:00'
),
(
    'sample_synth_cyberpunk_poster.png',
    '',
    684.2,
    '1024x1024',
    'AI-Generated',
    'Sintetis AI (Synthetic AI-Generated)',
    91.20,
    0.9120,
    'Contoh data awal: ilustrasi poster sintetis hasil generator difusi',
    TRUE,
    '2026-11-09 20:05:00'
),
(
    'sample_editorial_portrait_compressed.jpg',
    '',
    198.0,
    '1280x853',
    'Real',
    'Cenderung asli (Likely Real Image)',
    64.20,
    0.3580,
    'Contoh data awal: foto redaksi dengan kompresi JPEG tingkat lanjut',
    TRUE,
    '2026-11-10 08:30:00'
),
(
    'sample_concept_art_character.png',
    '',
    520.8,
    '768x768',
    'AI-Generated',
    'Cenderung AI (Likely AI-Generated)',
    68.40,
    0.6840,
    'Contoh data awal: konsep karakter digital dengan inpainting AI',
    TRUE,
    '2026-11-10 10:45:00'
);

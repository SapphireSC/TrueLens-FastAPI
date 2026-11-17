-- Jalankan perintah CREATE DATABASE ini di psql / pgAdmin bila database belum ada:
-- CREATE DATABASE truelens_db;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

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

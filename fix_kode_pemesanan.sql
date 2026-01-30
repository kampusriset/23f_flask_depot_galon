-- Script untuk memperbaiki kolom kode_pemesanan
-- Jalankan script ini di MySQL jika masih ada error "Data too long for column"

USE depot_air;

-- 1. Hapus constraint UNIQUE jika ada (karena satu pesanan bisa punya multiple items)
SHOW INDEX FROM pemesanan WHERE Column_name = 'kode_pemesanan';

-- Hapus index unique jika ada
ALTER TABLE pemesanan DROP INDEX IF EXISTS kode_pemesanan;
ALTER TABLE pemesanan DROP INDEX IF EXISTS idx_kode_pemesanan;

-- 2. Perpanjang kolom kode_pemesanan dari 20 menjadi 30 karakter
-- Format kode: ORD + YYYYMMDDHHMMSS (14) + millisecond (3) + random (4) = 24 karakter
ALTER TABLE pemesanan MODIFY COLUMN kode_pemesanan VARCHAR(30) NOT NULL;

-- 3. Verifikasi perubahan
SHOW INDEX FROM pemesanan WHERE Column_name = 'kode_pemesanan';
DESCRIBE pemesanan;

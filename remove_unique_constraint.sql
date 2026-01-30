-- Script untuk memperbaiki kolom kode_pemesanan
-- Jalankan script ini di MySQL jika masih ada error

-- 1. Hapus constraint UNIQUE jika ada
SHOW INDEX FROM pemesanan WHERE Column_name = 'kode_pemesanan';

ALTER TABLE pemesanan DROP INDEX IF EXISTS kode_pemesanan;
ALTER TABLE pemesanan DROP INDEX IF EXISTS idx_kode_pemesanan;

-- 2. Perpanjang kolom kode_pemesanan dari 20 menjadi 30 karakter
ALTER TABLE pemesanan MODIFY COLUMN kode_pemesanan VARCHAR(30) NOT NULL;

-- 3. Verifikasi perubahan
SHOW INDEX FROM pemesanan WHERE Column_name = 'kode_pemesanan';
DESCRIBE pemesanan;
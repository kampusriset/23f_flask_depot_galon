# database/models.py
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# ============================================
# TABEL USER (Pengguna)
# ============================================
class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    telepon = db.Column(db.String(20), nullable=True)
    alamat = db.Column(db.Text, nullable=True)
    role = db.Column(db.String(20), default='customer')  # 'customer', 'admin'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi ke tabel lain
    pemesanan = db.relationship('Pemesanan', backref='user', lazy=True)
    pembelian_galon = db.relationship('PembelianGalon', backref='pembeli', lazy=True)
    
    # Fungsi untuk password
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Cek apakah admin
    def is_admin(self):
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username} - {self.role}>'


# ============================================
# TABEL GALON (Produk)
# ============================================
class Galon(db.Model):
    __tablename__ = 'galon'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jenis = db.Column(db.String(50), unique=True, nullable=False)
    harga = db.Column(db.Integer, nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    stok = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Galon {self.jenis} - Rp {self.harga}>'


# ============================================
# TABEL PEMESANAN (Order)
# ============================================
class Pemesanan(db.Model):
    __tablename__ = 'pemesanan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kode_pemesanan = db.Column(db.String(20), unique=True, nullable=False)
    nama_pelanggan = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    jenis_galon = db.Column(db.String(50), nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    total_harga = db.Column(db.Integer, nullable=False)
    catatan = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Menunggu Konfirmasi')
    metode_pembayaran = db.Column(db.String(50), default='Cash')
    tanggal_pesan = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_konfirmasi = db.Column(db.DateTime, nullable=True)
    tanggal_selesai = db.Column(db.DateTime, nullable=True)
    
    # Relasi ke pembayaran
    pembayaran = db.relationship('Pembayaran', backref='pemesanan', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<Pemesanan {self.kode_pemesanan} - {self.status}>'


# ============================================
# TABEL PEMBELIAN GALON (Tambah Stok)
# ============================================
class PembelianGalon(db.Model):
    __tablename__ = 'pembelian_galon'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    jenis_galon = db.Column(db.String(50), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    harga_satuan = db.Column(db.Integer, nullable=False)
    total_harga = db.Column(db.Integer, nullable=False)
    tanggal_beli = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')
    
    def __repr__(self):
        return f'<PembelianGalon {self.jenis_galon} x{self.jumlah}>'


# ============================================
# TABEL PEMBAYARAN (Payment)
# ============================================
class Pembayaran(db.Model):
    __tablename__ = 'pembayaran'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pemesanan_id = db.Column(db.Integer, db.ForeignKey('pemesanan.id'), nullable=False)
    jumlah_bayar = db.Column(db.Integer, nullable=False)
    metode = db.Column(db.String(50), default='Cash')
    status = db.Column(db.String(50), default='Belum Bayar')
    bukti_pembayaran = db.Column(db.String(200), nullable=True)
    tanggal_bayar = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Pembayaran {self.status} - Rp {self.jumlah_bayar}>'


# ============================================
# TABEL LAPORAN (Reports)
# ============================================
class Laporan(db.Model):
    __tablename__ = 'laporan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipe = db.Column(db.String(50), nullable=False)  # 'penjualan', 'pembelian', 'stok'
    periode = db.Column(db.String(20), nullable=False)  # 'harian', 'bulanan', 'tahunan'
    data = db.Column(db.Text, nullable=False)  # JSON data
    total = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Laporan {self.tipe} - {self.periode}>'


# ============================================
# TABEL PENGATURAN (Settings)
# ============================================
class Pengaturan(db.Model):
    __tablename__ = 'pengaturan'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_setting = db.Column(db.String(100), unique=True, nullable=False)
    nilai = db.Column(db.Text, nullable=False)
    keterangan = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Pengaturan {self.nama_setting}>'


# ============================================
# JIKA ADA ERROR, GUNAKAN INI:
# ============================================
"""
Jika ada error tentang MySQL, coba ganti dengan kode ini:

class User(db.Model):
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # ... (sisanya sama)

Lakukan hal yang sama untuk semua class di atas.
"""

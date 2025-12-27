from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
import os
import json
import pymysql

# Import dari database folder
from database.models import db, User, Pemesanan, Galon, PembelianGalon, Pembayaran, Laporan, Pengaturan

app = Flask(__name__)
app.secret_key = 'secretkey123'

# ⭐⭐⭐ UBAH INI ⭐⭐⭐
# DARI: 'sqlite:///depot_air.db'
# MENJADI:
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/depot_air'
# Penjelasan: root = username, kosong = password, localhost = server, depot_air = nama database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Data default untuk galon
DEFAULT_GALON = [
    {"jenis": "Air Galon Biasa", "harga": 6000, "stok": 100},
    {"jenis": "Air Galon RO", "harga": 8000, "stok": 100},
    {"jenis": "Air Galon Mineral", "harga": 7000, "stok": 100}
]

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        nama_lengkap = request.form.get('nama_lengkap', '')
        email = request.form.get('email', '')
        telepon = request.form.get('telepon', '')
        
        # Cek jika username sudah ada
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username sudah digunakan', 'error')
            return redirect(url_for('register'))
        
        # Buat user baru
        new_user = User(
            username=username, 
            nama_lengkap=nama_lengkap, 
            email=email,
            telepon=telepon
        )
        new_user.set_password(password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registrasi berhasil! Silakan login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan saat registrasi: {str(e)}', 'error')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['nama_lengkap'] = user.nama_lengkap or user.username
            session['role'] = user.role
            
            flash('Login berhasil!', 'success')
            
            # Redirect berdasarkan role
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Hitung statistik
    total_pesanan = Pemesanan.query.filter_by(user_id=user_id).count()
    pesanan_menunggu = Pemesanan.query.filter_by(
        user_id=user_id, 
        status='Menunggu Konfirmasi'
    ).count()
    pesanan_selesai = Pemesanan.query.filter_by(
        user_id=user_id, 
        status='Selesai'
    ).count()
    
    # Ambil pesanan terbaru
    pesanan_terbaru = Pemesanan.query.filter_by(user_id=user_id)\
        .order_by(Pemesanan.tanggal_pesan.desc())\
        .limit(5).all()
    
    return render_template('dashboard.html', 
                         username=session['nama_lengkap'],
                         total_pesanan=total_pesanan,
                         pesanan_menunggu=pesanan_menunggu,
                         pesanan_selesai=pesanan_selesai,
                         pesanan_terbaru=pesanan_terbaru)

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Akses ditolak. Hanya untuk admin.', 'error')
        return redirect(url_for('dashboard'))
    
    # Statistik admin
    total_users = User.query.count()
    total_pesanan = Pemesanan.query.count()
    total_pendapatan = db.session.query(db.func.sum(Pemesanan.total_harga)).scalar() or 0
    pesanan_hari_ini = Pemesanan.query.filter(
        db.func.date(Pemesanan.tanggal_pesan) == datetime.today().date()
    ).count()
    
    today = datetime.today().strftime('%d %B %Y')
    
    return render_template('dashboard.html',
                         total_users=total_users,
                         total_pesanan=total_pesanan,
                         total_pendapatan=total_pendapatan,
                         pesanan_hari_ini=pesanan_hari_ini,
                         today=today)

@app.route('/harga')
def harga():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ambil data galon dari database
    galon_list = Galon.query.filter_by(is_available=True).all()
    
    # Jika belum ada data, gunakan default
    if not galon_list:
        galon_list = DEFAULT_GALON
        # Simpan ke database
        for g in DEFAULT_GALON:
            galon = Galon(
                jenis=g['jenis'],
                harga=g['harga'],
                stok=g['stok']
            )
            db.session.add(galon)
        db.session.commit()
        galon_list = Galon.query.all()
    
    # Tentukan apakah user adalah admin untuk menampilkan form beli galon
    is_admin = session.get('role') == 'admin'
    
    return render_template("harga.html", harga=galon_list, is_admin=is_admin)

@app.route('/pesan', methods=['POST'])
def pesan_galon():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('login'))
    
    try:
        # Ambil data dari form
        nama = request.form['nama']
        alamat = request.form['alamat']
        jumlah = int(request.form['jumlah'])
        jenis_galon = request.form['jenis_galon']
        harga_input = int(request.form['harga'])
        catatan = request.form.get('catatan', '')
        metode_pembayaran = request.form.get('metode_pembayaran', 'Cash')
        
        # Generate kode pemesanan
        from datetime import datetime
        kode_pemesanan = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Hitung total harga
        total_harga = harga_input * jumlah
        
        # Cek stok galon
        galon = Galon.query.filter_by(jenis=jenis_galon).first()
        if galon and galon.stok < jumlah:
            flash(f'Stok {jenis_galon} tidak mencukupi. Stok tersedia: {galon.stok}', 'error')
            return redirect(url_for('harga'))
        
        # Kurangi stok jika ada
        if galon:
            galon.stok -= jumlah
            if galon.stok <= 0:
                galon.is_available = False
        
        # Simpan pemesanan ke database
        new_pesanan = Pemesanan(
            user_id=session['user_id'],
            kode_pemesanan=kode_pemesanan,
            nama_pelanggan=nama,
            alamat=alamat,
            jenis_galon=jenis_galon,
            harga_satuan=harga_input,
            jumlah=jumlah,
            total_harga=total_harga,
            catatan=catatan,
            metode_pembayaran=metode_pembayaran,
            status='Menunggu Konfirmasi'
        )
        
        # Buat record pembayaran
        pembayaran = Pembayaran(
            pemesanan=new_pesanan,
            jumlah_bayar=total_harga,
            metode=metode_pembayaran,
            status='Belum Bayar'
        )
        
        db.session.add(new_pesanan)
        db.session.add(pembayaran)
        db.session.commit()
        
        flash(f'Pesanan {jenis_galon} sebanyak {jumlah} galon berhasil! Kode: {kode_pemesanan}', 'success')
        return redirect(url_for('pemesanan'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan: {str(e)}', 'error')
        return redirect(url_for('harga'))

@app.route('/pemesanan')
def pemesanan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Jika admin, tampilkan semua pesanan
    if session.get('role') == 'admin':
        pesanan_list = Pemesanan.query.order_by(Pemesanan.tanggal_pesan.desc()).all()
    else:
        pesanan_list = Pemesanan.query.filter_by(user_id=user_id)\
            .order_by(Pemesanan.tanggal_pesan.desc()).all()
    
    return render_template("pemesanan.html", pemesanan=pesanan_list)

@app.route('/beli-galon', methods=['POST'])
def beli_galon():
    if 'user_id' not in session:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('login'))
    
    try:
        jenis_galon = request.form['jenis_galon']
        jumlah = int(request.form['jumlah'])
        
        # Cari harga galon
        galon = Galon.query.filter_by(jenis=jenis_galon).first()
        if not galon:
            flash('Jenis galon tidak ditemukan', 'error')
            return redirect(url_for('harga'))
        
        harga_satuan = galon.harga
        total_harga = harga_satuan * jumlah
        
        # Simpan pembelian galon
        pembelian = PembelianGalon(
            user_id=session['user_id'],
            jenis_galon=jenis_galon,
            jumlah=jumlah,
            harga_satuan=harga_satuan,
            total_harga=total_harga
        )
        
        # Tambah stok galon
        galon.stok += jumlah
        galon.is_available = True
        
        db.session.add(pembelian)
        db.session.commit()
        
        flash(f'Pembelian {jenis_galon} sebanyak {jumlah} galon berhasil ditambahkan ke stok!', 'success')
        return redirect(url_for('stok'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan: {str(e)}', 'error')
        return redirect(url_for('harga'))

@app.route('/stok')
def stok():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if session.get('role') != 'admin':
        flash('Hanya admin yang dapat mengakses halaman stok', 'error')
        return redirect(url_for('dashboard'))
    
    galon_list = Galon.query.all()
    pembelian_list = PembelianGalon.query.order_by(PembelianGalon.tanggal_beli.desc()).all()
    
    return render_template('stok.html', 
                         galon_list=galon_list, 
                         pembelian_list=pembelian_list)

@app.route('/update-status/<int:pesanan_id>', methods=['POST'])
def update_status(pesanan_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Akses ditolak. Hanya untuk admin.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        status = request.form['status']
        pesanan = Pemesanan.query.get_or_404(pesanan_id)
        
        pesanan.status = status
        
        if status == 'Selesai':
            pesanan.tanggal_selesai = datetime.utcnow()
        elif status == 'Dikonfirmasi':
            pesanan.tanggal_konfirmasi = datetime.utcnow()
        
        db.session.commit()
        flash(f'Status pesanan {pesanan.kode_pemesanan} berhasil diupdate menjadi {status}', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi kesalahan: {str(e)}', 'error')
    
    return redirect(url_for('pemesanan'))

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))

# ⭐⭐⭐ FUNGSI BARU UNTUK MIGRASI DATA ⭐⭐⭐
def backup_sqlite_to_json():
    """Backup data dari SQLite ke file JSON"""
    import sqlite3
    import json
    
    if not os.path.exists('depot_air.db'):
        print("File depot_air.db tidak ditemukan, skip backup")
        return
    
    conn = sqlite3.connect('depot_air.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Ambil semua tabel
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    data = {}
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        data[table_name] = [dict(row) for row in rows]
    
    # Simpan ke JSON
    with open('backup_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    conn.close()
    print("✅ Backup SQLite berhasil disimpan ke backup_data.json")

def migrate_to_mysql():
    """Pindahkan data dari SQLite ke MySQL"""
    backup_sqlite_to_json()
    
    if not os.path.exists('backup_data.json'):
        print("❌ File backup_data.json tidak ditemukan")
        return
    
    try:
        # Baca data backup
        with open('backup_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("📦 Mulai migrasi data ke MySQL...")
        
        # Urutan migrasi
        order = ['user', 'galon', 'pemesanan', 'pembelian_galon', 'pembayaran']
        
        for table_name in order:
            if table_name not in data or not data[table_name]:
                continue
            
            print(f"  Migrasi tabel: {table_name}")
            
            # Get model class
            model_class = None
            if table_name == 'user':
                model_class = User
            elif table_name == 'galon':
                model_class = Galon
            elif table_name == 'pemesanan':
                model_class = Pemesanan
            elif table_name == 'pembelian_galon':
                model_class = PembelianGalon
            elif table_name == 'pembayaran':
                model_class = Pembayaran
            
            if not model_class:
                continue
            
            # Insert data
            for row_data in data[table_name]:
                try:
                    # Hapus id untuk auto increment
                    if 'id' in row_data:
                        del row_data['id']
                    
                    # Buat objek
                    obj = model_class(**row_data)
                    db.session.add(obj)
                    
                except Exception as e:
                    print(f"    Error: {e}")
                    continue
            
            db.session.commit()
            print(f"  ✅ {len(data[table_name])} data berhasil dimigrasi")
        
        print("🎉 Migrasi data SELESAI!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error migrasi: {e}")

def init_database():
    """Inisialisasi database dengan data default"""
    with app.app_context():
        # Buat semua tabel di MySQL
        db.create_all()
        print("✅ Tabel berhasil dibuat di MySQL")
        
        # Cek apakah sudah ada data
        user_count = User.query.count()
        galon_count = Galon.query.count()
        
        if user_count == 0 and galon_count == 0:
            print("📦 Migrasi data dari SQLite (jika ada)...")
            migrate_to_mysql()
        
        # Cek apakah admin sudah ada
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                nama_lengkap='Administrator',
                email='admin@artatirta.com',
                role='admin'
            )
            admin_user.set_password('12345')
            db.session.add(admin_user)
            print("✅ Admin user dibuat")
        
        # Cek apakah galon sudah ada
        galon = Galon.query.first()
        if not galon:
            for g in DEFAULT_GALON:
                galon_item = Galon(
                    jenis=g['jenis'],
                    harga=g['harga'],
                    stok=g['stok']
                )
                db.session.add(galon_item)
            print("✅ Data galon default dibuat")
        
        try:
            db.session.commit()
            print('🎉 Database siap digunakan!')
        except Exception as e:
            db.session.rollback()
            print(f'❌ Error: {e}')

if __name__ == '__main__':
    # ⭐⭐⭐ INI YANG PENTING ⭐⭐⭐
    # Koneksi ke database
    db.init_app(app)
    
    # Inisialisasi database
    print("🔧 Memulai inisialisasi database...")
    init_database()
    
    # Jalankan aplikasi
    print("🚀 Aplikasi berjalan di http://localhost:5000")
    app.run(debug=True, port=5000)
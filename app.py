from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'secretkey123'  


USERNAME = 'admin'
PASSWORD = '12345'


@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USERNAME and password == PASSWORD:
            session['username'] = username
            flash('Login berhasil!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    else:
        flash('Silakan login terlebih dahulu', 'error')
        return redirect(url_for('login'))
    
    
@app.route('/pemesanan')
def pemesanan():
    if 'username' not in session:
        return redirect(url_for('login'))

    data_pemesanan = [
        {"nama": "Budi", "alamat": "Jl. Melati 12", "jumlah": 2, "status": "Selesai"},
        {"nama": "Sari", "alamat": "Jl. Kenanga 5", "jumlah": 1, "status": "Proses"},
        {"nama": "Agus", "alamat": "Jl. Mawar 11", "jumlah": 3, "status": "Dikirim"},
    ]
    return render_template("pemesanan.html", pemesanan=data_pemesanan)


@app.route('/harga')
def harga():
    if 'username' not in session:
        return redirect(url_for('login'))

    harga_list = [
        {"jenis": "Air Galon Biasa", "harga": "Rp 6.000"},
        {"jenis": "Air Galon RO", "harga": "Rp 8.000"},
        {"jenis": "Air Galon Mineral", "harga": "Rp 7.000"}
    ]
    return render_template("harga.html", harga=harga_list)


@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Anda telah logout', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)

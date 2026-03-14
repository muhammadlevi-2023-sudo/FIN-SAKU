import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro", layout="wide")

# --- DATABASE ---
conn = sqlite3.connect('finsaku_v15.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- HELPER ---
def format_rp(angka):
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# 2. UI STYLING (MODERN DARK NAVY)
st.markdown("""
<style>
    .stApp { background-color: #001220; color: #E0E0E0; }
    .main-card {
        background: #001f3f; padding: 25px; border-radius: 15px;
        border-left: 5px solid #FFD700; margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .stat-box {
        background: #ffffff; color: #001220; padding: 15px;
        border-radius: 10px; text-align: center;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FFD700, #FFA500) !important;
        color: black !important; font-weight: bold; border: none; width: 100%;
    }
    h1, h2, h3 { color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR (SETTING) ---
with st.sidebar:
    st.title("💰 FIN-Saku")
    st.markdown("---")
    nama_usaha = st.text_input("Nama Usaha", "UMKM Maju")
    modal_awal = st.number_input("Modal Awal Kas (Rp)", value=7000000, step=100000)
    st.markdown("---")
    st.subheader("Konfigurasi Profit")
    hpp = st.number_input("Harga Pokok (HPP)", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    prive_pct = st.slider("Jatah Jajan (Prive) %", 0, 100, 30)
    
    kas_terkini = modal_awal + (total_laba - total_prive)
    st.markdown(f"### Modal Terkini:\n## {format_rp(kas_terkini)}")

# --- ISI DASHBOARD ---
st.header(f"Pusat Analisis Keuangan: {nama_usaha}")

# 1. INPUT & REVISI (DIBUAT SEJAJAR & BERSIH)
col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("📝 Catat Penjualan")
    mode = st.radio("Metode:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    
    cx, cy = st.columns(2)
    with cx: tgl = st.date_input("Tanggal", datetime.now())
    with cy: omzet = st.number_input(f"Total Omzet {mode}", value=0, step=50000)
    
    laba_bersih = omzet - (omzet * (hpp/jual)) if jual > 0 else 0
    prive_ambil = laba_bersih * (prive_pct/100)
    
    st.markdown(f"**Prediksi Laba: {format_rp(laba_bersih)}** | **Jajan: {format_rp(prive_ambil)}**")
    
    if st.button("SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet, laba_bersih, prive_ambil, mode))
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="main-card">', unsafe_allow_html=True)
    st.subheader("🛠️ Revisi")
    if not df.empty:
        last_data = df.sort_values(by='id', ascending=False).head(3)
        for _, row in last_data.iterrows():
            c_a, c_b = st.columns([3, 1])
            c_a.write(f"{row['tanggal']} | {format_rp(row['omzet'])}")
            if c_b.button("🗑️", key=row['id']):
                c.execute(f"DELETE FROM transaksi WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    else:
        st.write("Belum ada data.")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. ANALISIS MENDALAM
st.markdown("---")
t1, t2 = st.tabs(["📈 LAPORAN MODAL", "🏦 ANALISIS LAYAK BANK"])

with t1:
    if not df.empty:
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        bln = st.selectbox("Pilih Bulan", df['bulan'].unique())
        data_bln = df[df['bulan'] == bln]
        
        l_bln = data_bln['laba'].sum()
        p_bln = data_bln['prive'].sum()
        tambah_modal = l_bln - p_bln
        
        st.write(f"### Laporan Perubahan Modal - {bln}")
        st.markdown(f"""
        - **Total Laba Bersih:** {format_rp(l_bln)}
        - **Total Prive (Diambil):** -{format_rp(p_bln)}
        ---
        ### ✅ PENAMBAHAN KAS MODAL: {format_rp(tambah_modal)}
        """)
        st.write(f"Bulan ini, kekayaan usaha Anda bertambah nyata sebesar **{format_rp(tambah_modal)}**.")
        st.markdown('</div>', unsafe_allow_html=True)

with t2:
    if not df.empty:
        # Menghitung kemampuan bayar (35% dari rata-rata laba)
        laba_rata = df['laba'].mean() * (30 if mode == "Harian" else 1)
        batas_aman = laba_rata * 0.35
        
        st.subheader("Analisis Strategis KUR BRI")
        st.write(f"Batas aman cicilan bulanan Anda: **{format_rp(batas_aman)}**")
        
        produk = [
            {"nama": "KUR Super Mikro (10 Juta)", "plafon": 10000000, "cicilan": 883000},
            {"nama": "KUR Mikro A (50 Juta)", "plafon": 50000000, "cicilan": 2250000},
            {"nama": "KUR Mikro B (100 Juta)", "plafon": 100000000, "cicilan": 4200000}
        ]
        
        cols = st.columns(3)
        for i, p in enumerate(produk):
            aman = p['cicilan'] <= batas_aman
            with cols[i]:
                st.markdown(f"""
                <div class="stat-box" style="border-top: 10px solid {'#28a745' if aman else '#dc3545'};">
                    <p style="margin:0; font-size:14px;">{p['nama']}</p>
                    <h3 style="margin:5px 0;">{format_rp(p['cicilan'])}/bln</h3>
                    <p style="font-size:12px;">{'✅ LAYAK PINJAM' if aman else '❌ BEBAN TERLALU BERAT'}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="main-card" style="margin-top:20px;">
            <h4>💡 Mengapa Angka Ini Penting?</h4>
            <p>Bank BRI menggunakan aturan <b>RPC (Repayment Capacity)</b>. Mereka hanya mau meminjamkan uang jika cicilannya tidak lebih dari 35% laba Anda.
            Jika statusnya <b style='color:red;'>BEBAN TERLALU BERAT</b>, jangan memaksakan pinjam sebesar itu karena risiko usaha Anda macet sangat tinggi.</p>
        </div>
        """, unsafe_allow_html=True)

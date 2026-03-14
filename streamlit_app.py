import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_final_v8.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD (ULTRA CONTRAST)
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }

    .white-card {
        background-color: #ffffff !important;
        padding: 25px; border-radius: 15px; border-left: 10px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .white-card *, .white-card p, .white-card b, .white-card td, .white-card h3 {
        color: #000000 !important; font-weight: 800 !important;
    }

    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 2px solid #FFD700; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
    
    .report-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .report-table td { padding: 10px; border-bottom: 1px solid #eee; }
    .highlight-row { background-color: #fff9c4; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: PARAMETER PRODUK & USAHA ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_raw = st.text_input("Uang Kas Awal (Modal)", "1000000")
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_raw = st.text_input("HPP / Modal per Produk", "5000")
    hrg_raw = st.text_input("Harga Jual per Produk", "15000")
    
    st.write("---")
    st.subheader("👨‍👩‍👦 Alokasi Pribadi")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)
    st.caption("Prive adalah uang yang Anda ambil untuk diri sendiri.")

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Laporan: {nama_u}")

st.markdown("""
<div class="white-card">
    <h3>📖 Panduan Mencatat Rekap:</h3>
    <p>Jika Anda mencatat <b>Mingguan/Bulanan</b>, sistem akan menghitung laba berdasarkan rata-rata margin produk Anda.</p>
</div>
""", unsafe_allow_html=True)

# --- INPUT TRANSAKSI MULTI-METODE ---
col_in, col_edu = st.columns([1.2, 1])

with col_in:
    st.subheader("📝 Form Pencatatan")
    
    # Pilih Jangka Waktu
    jangka_waktu = st.selectbox("Metode Catat:", ["Harian", "Rekap Mingguan", "Rekap Bulanan"])
    
    # Input Tanggal (Default hari ini)
    tgl = st.date_input("Tanggal Pencatatan / Akhir Periode", datetime.now())
    
    if jangka_waktu == "Harian":
        mode_input = st.radio("Cara Input:", ["Per Item Terjual", "Total Omzet Hari Ini"], horizontal=True)
        if mode_input == "Per Item Terjual":
            qty = st.number_input("Jumlah Produk Terjual", min_value=0, step=1)
            omzet = qty * clean_to_int(hrg_raw)
            laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
        else:
            omzet = st.number_input("Total Omzet Hari Ini", min_value=0, step=5000)
            ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
            laba = omzet * ratio
    
    elif jangka_waktu == "Rekap Mingguan":
        omzet = st.number_input("Total Omzet Selama 1 Minggu", min_value=0, step=10000)
        ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
        laba = omzet * ratio
        
    else: # Bulanan
        omzet = st.number_input("Total Omzet Selama 1 Bulan", min_value=0, step=50000)
        ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
        laba = omzet * ratio

    prive = laba * (prive_pct / 100)

    if st.button("🔔 SIMPAN KE DATABASE"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.success(f"Berhasil menyimpan rekap {jangka_waktu}!")
            st.rerun()

with col_edu:
    st.markdown(f"""
    <div class="white-card">
        <h3>🏦 Rumus KUR BRI (Kapasitas Bayar)</h3>
        <p>BRI melihat kemampuan bayar Anda dari:</p>
        <p><b>Cicilan Maksimal = 35% x Laba Bersih</b></p>
        <hr>
        <p>Contoh: Jika laba bulanan Anda Rp 3.000.000, maka BRI menganggap Anda mampu mencicil Rp 1.050.000 per bulan.</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN KEUANGAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR BRI"])

    def render_report(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        kas_bersih = l - p
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">{title}</h3>
            <table class="report-table">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi)</td><td style="text-align:right; color:red !important;">({format_rp(p)})</td></tr>
                <tr class="highlight-row">
                    <td><b>SALDO KAS MASUK</b></td><td style="text

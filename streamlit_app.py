import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_rekap_v9.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
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
    nama_u = st.text_input("Nama Usaha", "UMKM Baru", key="sidebar_nama")
    modal_raw = st.text_input("Kas Awal (Modal)", "0", key="sidebar_modal")
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_raw = st.text_input("HPP (Modal) /Produk", "5000")
    hrg_raw = st.text_input("Harga Jual /Produk", "15000")
    
    st.write("---")
    st.subheader("👨‍👩‍👦 Alokasi Pribadi")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)
    st.caption("Uang yang diambil untuk kebutuhan sendiri.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")

# PANDUAN CARA MENGISI
st.markdown("""
<div class="white-card">
    <h3>📖 Cara Mencatat:</h3>
    <ol>
        <li>Pilih periode pencatatan (Harian, Mingguan, atau Bulanan).</li>
        <li>Masukkan data omzet atau jumlah produk terjual.</li>
        <li>Sistem otomatis menghitung laba & kelayakan KUR BRI Anda.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# METODE CATAT MULTI-PERIODE
rekap_mode = st.selectbox("Pilih Periode Catat:", ["Harian", "Mingguan", "Bulanan"])

col_in, col_bri = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input Data {rekap_mode}")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    
    if rekap_mode == "Harian":
        input_type = st.radio("Metode:", ["Per Produk", "Total Omzet"], horizontal=True)
        if input_type == "Per Produk":
            qty = st.number_input("Unit Terjual", min_value=0, step=1)
            omzet = qty * clean_to_int(hrg_raw)
            laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
        else:
            omzet = st.number_input("Total Omzet Hari Ini", min_value=0, step=1000)
            ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
            laba = omzet * ratio
    else:
        omzet = st.number_input(f"Total Omzet 1 {rekap_mode}", min_value=0, step=5000)
        ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
        laba = omzet * ratio

    prive = laba * (prive_pct / 100)

    if st.button("🔔 SIMPAN DATA"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
            conn.commit()
            st.success("Tersimpan!")
            st.rerun()

with col_bri:
    st.markdown(f"""
    <div class="white-card">
        <h3>🏦 Standar KUR BRI</h3>
        <p>BRI menilai usaha Anda lewat 3 hal utama:</p>
        <ul>
            <li><b>Karakter:</b> Disiplin mencatat (Harian/Rekap).</li>
            <li><b>Kapasitas:</b> Mampu bayar cicilan (Max 35% Laba).</li>
            <li><b>Modal:</b> Pengaturan arus kas yang jelas.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN KEUANGAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR BRI"])

    def show_report(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        kas_bersih = l - p
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">{title}</h3>
            <table class="report-table">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi)</td><td style="text-align:right; color:red;">({format_rp(p)})</td></tr>
                <tr class="highlight-row">
                    <td><b>KAS BERSIH (TABUNGAN USAHA)</b></td><td style="text-align:right;"><b>{format_rp(kas_bersih)}</b></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Pilih Hari:", datetime.now(), key="rep_h")
        show_report(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan {sel_t.strftime('%d/%b/%Y')}")

    with t_min:
        sel_m = st.selectbox("Pilih Minggu:", df['minggu'].unique())
        show_report(df[df['minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        show_report(df[df['bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        # HITUNG KELAYAKAN KUR
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        rpc = avg_laba * 0.35
        plafon = rpc * 22
        
        st.subheader("🏦 Simulasi Pinjaman BRI")
        st.markdown(f"""
        <div class="white-card">
            <p>Rata-rata Laba Bulanan: <b>{format_rp(avg_laba)}</b></p>
            <p>Kemampuan Cicilan Aman (RPC): <b>{format_rp(rpc)}</b></p>
            <hr>
            <p>Estimasi Plafon Pinjaman:</p>
            <h1 style="color:#001f3f;">{format_rp(plafon)}</h1>
        </div>
        """, unsafe_allow_html=True)

        if plafon >= 5000000:
            st.success("✅ BANKABLE: Usaha Anda layak mendapatkan KUR BRI.")
        else:
            st.error("⚠️ BELUM LAYAK: Tingkatkan laba Anda agar plafon mencapai minimal Rp 5.000.000.")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_complete_v7.db', check_same_thread=False)
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

# 2. UI CUSTOM: NAVY & GOLD (SUPER CONTRAST)
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
    st.markdown(f"Tercatat: **{format_rp(clean_to_int(modal_raw))}**")
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_raw = st.text_input("HPP / Modal per Produk", "5000")
    hrg_raw = st.text_input("Harga Jual per Produk", "15000")
    st.markdown(f"Margin: **{format_rp(clean_to_int(hrg_raw) - clean_to_int(hpp_raw))}** /pcs")
    
    st.write("---")
    st.subheader("👨‍👩‍👦 Alokasi Pribadi")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)
    st.caption("BRI menyarankan Prive < 50% dari laba.")

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Laporan: {nama_u}")

# PANDUAN CARA MENGISI
st.markdown("""
<div class="white-card">
    <h3>📖 Cara Menggunakan Aplikasi:</h3>
    <ol>
        <li><b>Langkah 1:</b> Atur HPP dan Harga Jual di menu sidebar sebelah kiri.</li>
        <li><b>Langkah 2:</b> Pilih mode input di bawah ini (Satuan atau Totalan).</li>
        <li><b>Langkah 3:</b> Klik "Simpan Transaksi" setiap ada penjualan masuk.</li>
        <li><b>Langkah 4:</b> Pantau tab "ANALISIS KUR BRI" untuk melihat kelayakan pinjaman Anda.</li>
    </ol>
</div>
""", unsafe_allow_html=True)

# MODE INPUT
mode = st.radio("Pilih Mode Pencatatan:", ["Mode Satuan (Item Terjual)", "Mode Totalan (Omzet Harian)"], horizontal=True)

col_in, col_space = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 Catat Transaksi")
    tgl = st.date_input("Tanggal", datetime.now())
    
    if mode == "Mode Satuan (Item Terjual)":
        qty = st.number_input("Jumlah Produk Terjual", min_value=0, step=1)
        omzet = qty * clean_to_int(hrg_raw)
        laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
    else:
        omzet = st.number_input("Total Uang Masuk Hari Ini", min_value=0, step=5000)
        # Menghitung estimasi laba berdasarkan rasio HPP di sidebar
        ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
        laba = omzet * ratio
    
    prive = laba * (prive_pct / 100)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.success("Data berhasil masuk!")
            st.rerun()

# --- LAPORAN KEUANGAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR BRI"])

    def show_table(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        kas_masuk = l - p
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">{title}</h3>
            <table class="report-table">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih Kotor</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Diambil Sendiri)</td><td style="text-align:right; color:red !important;">({format_rp(p)})</td></tr>
                <tr class="highlight-row">
                    <td><b>KAS BERSIH USAHA</b></td><td style="text-align:right;"><b>{format_rp(kas_masuk)}</b></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Filter Hari", datetime.now(), key="harian")
        show_table(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan {sel_t.strftime('%d/%b/%Y')}")
    
    with t_min:
        sel_m = st.selectbox("Pilih Minggu", df['minggu'].unique())
        show_table(df[df['minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        show_table(df[df['bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        rpc = avg_laba * 0.35 # Standar BRI (Repayment Capacity)
        plafon_est = rpc * 22 # Estimasi plafon tenor 2 tahun
        
        st.subheader("🏦 Skor Kelayakan BRI")
        col1, col2 = st.columns(2)
        col1.metric("Kapasitas Bayar (RPC)", format_rp(rpc))
        col2.metric("Estimasi Plafon KUR", format_rp(plafon_est))

        if plafon_est >= 5000000:
            st.success("✅ STATUS: LAYAK (BANKABLE). Usaha Anda kuat untuk cicilan KUR.")
        else:
            st.error("⚠️ STATUS: BELUM LAYAK. Plafon di bawah Rp 5 Juta.")
            kurang = 5000000 - plafon_est
            st.info(f"💡 Tips: Tingkatkan laba sebesar {format_rp((kurang/22)/0.35)} lagi per bulan untuk lolos kriteria.")

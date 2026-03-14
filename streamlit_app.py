import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE (Menjamin Data Tidak Hilang Saat Refresh) ---
conn = sqlite3.connect('finsaku_unair_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS profil 
             (id INTEGER PRIMARY KEY, nama_usaha TEXT, modal_awal REAL)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except:
        return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: UNAIR NAVY & GOLD (High Contrast)
st.markdown("""
<style>
    .stApp { background-color: #003366 !important; }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] { background-color: #002244 !important; border-right: 3px solid #FFD700; }
    
    /* Box Edukasi: Teks Navy di atas Putih */
    .edu-box { 
        background-color: #ffffff !important; padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 25px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { color: #003366 !important; }

    /* Tab Navigasi */
    button[data-baseweb="tab"] p { color: #FFD700 !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #003366 !important; }

    /* Laporan & Card */
    .report-card { 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        padding: 25px; border-radius: 12px; border: 1px solid #FFD700; margin-bottom: 20px;
    }
    .kur-card { background-color: #FFD700 !important; padding: 30px; border-radius: 15px; }
    .kur-card h2, .kur-card p, .kur-card td, .kur-card b { color: #003366 !important; }

    /* Tombol Gold */
    .stButton>button { 
        background-color: #FFD700 !important; color: #003366 !important; 
        font-weight: bold; border-radius: 8px; height: 3.5em; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- PROSES DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
p_data = c.fetchone()
saved_nama = p_data[1] if p_data else "Usaha Baru"
saved_modal = p_data[2] if p_data else 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_usaha = st.text_input("Nama Usaha", saved_nama)
    m_raw = st.text_input("Modal Kas Awal (Rp)", value=str(int(saved_modal)))
    if st.button("💾 SIMPAN PROFIL"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", (nama_usaha, clean_to_int(m_raw)))
        conn.commit()
        st.success("Profil Berhasil Diperbarui!")
    
    st.write("---")
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Dashboard Keuangan: {nama_usaha}")
st.markdown("""<div class="edu-box"><h3>🔍 Mengapa FIN-Saku Membuat UMKM Bankable?</h3>
<p>Bank menilai kesehatan usaha Anda lewat 3 hal: <b>Karakter</b> (disiplin mencatat), <b>Kapasitas</b> (laba bersih bulanan), dan <b>Modal</b> (pengaturan arus kas).</p></div>""", unsafe_allow_html=True)

col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0)
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if qty > 0:
            v_omzet = qty * clean_to_int(harga_raw)
            v_laba = qty * (clean_to_int(harga_raw) - clean_to_int(hpp_raw))
            v_prive = v_laba * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", v_omzet, v_laba, v_prive))
            conn.commit()
            st.success("Data Berhasil Masuk Database!")
            st.rerun()

# --- BAGIAN ANALISIS & LAPORAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def render_laporan(data_df, judul):
        omz, lb, prv = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        # Perhitungan saldo kas total
        total_kas = clean_to_int(m_raw) + (df['laba'].sum() - df['prive'].sum())
        st.markdown(f"""<div class="report-card"><h3 style='text-align:center; color:#FFD700;'>{judul}</h3>
        <table style="width:100%; font-size:18px;">
        <tr><td>Total Pendapatan</td><td style="text-align:right;">{format_rp(omz)}</td></tr>
        <tr style="color:#FFD700;"><td><b>Laba Bersih</b></td><td style="text-align:right;"><b>{format_rp(lb)}</b></td></tr>
        <tr style="color:#ff4b4b;"><td>Prive (Konsumsi)</td><td style="text-align:right;">({format_rp(prv)})</td></tr>
        <tr style="background-color:#FFD700; color:#003366; font-weight:bold; font-size:20px;">
        <td style="padding:10px;">SALDO KAS SAAT INI</td><td style="text-align:right; padding:10px;">{format_rp(total_kas)}</td></tr></table></div>""", unsafe_allow_html=True)

    with t_har:
        sel_tgl = st.date_input("Filter Hari", datetime.now())
        df_h = df[df['tanggal'] == sel_tgl.strftime("%Y-%m-%d")]
        if not df_h.empty: render_laporan(df_h, f"Laporan Harian - {sel_tgl.strftime('%d/%m/%Y')}")
        else: st.info("Tidak ada transaksi pada tanggal ini.")

    with t_min:
        sel_m = st.selectbox("Pilih Minggu", df['minggu'].unique())
        render_laporan(df[df['minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        render_laporan(df[df['bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        # Logika KUR: Rata-rata laba per bulan
        avg_laba = df['laba'].sum() / max(1, len(df['bulan'].unique()))
        rpc = avg_laba * 0.35  # Batas cicilan aman 35% laba
        plafon = rpc * 22       # Estimasi plafon tenor 2 tahun
        
        if plafon >= 5000000:
            st.markdown(f"""<div class="kur-card"><h2>✅ STATUS: BANKABLE</h2>
            <p>Berdasarkan data Anda, estimasi plafon KUR: <b>{format_rp(plafon)}</b></p>
            <p>Rekomendasi cicilan maksimal: {format_rp(rpc)}/bulan</p></div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="kur-card" style="background-color:#ff4b4b !important;">
            <h2 style="color:white !important;">⚠️ BELUM LAYAK KUR</h2>
            <p style="color:white !important;">Kapasitas bayar Anda saat ini masih di bawah standar minimal plafon Bank ({format_rp(5000000)}).</p></div>
            <div style="background-color:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-top:15px;">
            <b>💡 Saran Inovatif:</b> Tingkatkan volume penjualan atau kurangi persentase Prive untuk memperkuat profil kapasitas bayar usaha Anda.</div>""", unsafe_allow_html=True)

if st.sidebar.button("🗑️ RESET SEMUA DATA"):
    c.execute("DELETE FROM transaksi")
    conn.commit()
    st.rerun()

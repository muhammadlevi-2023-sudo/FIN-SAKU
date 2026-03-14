import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Inovasi Keuangan Digital", layout="wide")

# --- DATABASE ENGINE (Auto-Save) ---
conn = sqlite3.connect('finsaku_unair_v2.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS profil 
             (id INTEGER PRIMARY KEY, nama_usaha TEXT, modal_awal REAL)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: UNAIR BLUE & GOLD (Hard-Locked Contrast)
st.markdown("""
<style>
    /* KUNCI BACKGROUND: Biru Tua UNAIR */
    .stApp { background-color: #003366 !important; }

    /* KUNCI WARNA TEKS UMUM: Putih */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }

    /* SIDEBAR: Navy Gelap + Border Kuning */
    [data-testid="stSidebar"] {
        background-color: #002244 !important;
        border-right: 3px solid #FFD700;
    }

    /* BOX EDUKASI: PERBAIKAN KONTRAS (Teks Navy Pekat di Background Putih) */
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; 
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 25px;
    }
    /* Memaksa teks di dalam box edukasi menjadi Biru UNAIR agar terbaca jelas */
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b, .edu-box span { 
        color: #003366 !important; 
        font-weight: 600 !important;
    }

    /* TAB: Kuning UNAIR */
    button[data-baseweb="tab"] p { color: #FFD700 !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #003366 !important; }

    /* CARD KUR & LAPORAN */
    .kur-card { 
        background-color: #FFD700 !important; 
        padding: 30px; border-radius: 15px; 
        color: #003366 !important;
    }
    .kur-card h2, .kur-card p, .kur-card td, .kur-card b { color: #003366 !important; }

    /* TOMBOL: Gold UNAIR */
    .stButton>button { 
        background-color: #FFD700 !important; 
        color: #003366 !important; 
        font-weight: bold; border-radius: 8px; height: 3.5em; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
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
    
    if st.button("💾 UPDATE PROFIL"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", 
                  (nama_usaha, clean_to_int(m_raw)))
        conn.commit()
        st.success("Profil Berhasil Disimpan!")

    st.write("---")
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Pusat Data Inovatif: {nama_usaha}")

# KOTAK EDUKASI (Teks sudah diperbaiki menjadi Navy di atas Putih)
st.markdown(f"""
<div class="edu-box">
    <h3>🔍 FIN-Saku: Mengapa Laporan Ini Membuat Anda Bankable?</h3>
    <p>Bank tidak hanya melihat saldo, tapi kedisiplinan Anda dalam mengelola 3 hal:</p>
    <ul>
        <li><b>Karakter:</b> Konsistensi Anda mencatat tiap transaksi harian secara jujur.</li>
        <li><b>Kapasitas:</b> Kemampuan laba bersih Anda untuk meng-cover cicilan bulanan.</li>
        <li><b>Modal:</b> Pemisahan uang pribadi (Prive) agar kas usaha tidak bocor.</li>
    </ul>
    <span><i>Sumber: Standar Kelayakan Kredit (RPC 35%) Manajemen Keuangan UMKM.</i></span>
</div>
""", unsafe_allow_html=True)

col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0)
    
    if st.button("🔔 SIMPAN KE DATABASE"):
        if qty > 0:
            omzet = qty * clean_to_int(harga_raw)
            laba = qty * (clean_to_int(harga_raw) - clean_to_int(hpp_raw))
            prive = laba * (prive_pct / 100)
            
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.success("Transaksi Berhasil Dicatat!")
            st.rerun()

# --- ANALISIS DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

if not df.empty:
    st.write("---")
    t_har, t_bul, t_kur = st.tabs(["📆 RIWAYAT", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    with t_bul:
        sel_b = st.selectbox("Filter Bulan", df['bulan'].unique())
        sub_df = df[df['bulan'] == sel_b]
        mod_berjalan = clean_to_int(m_raw) + (df['laba'].sum() - df['prive'].sum())

        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.1); padding:20px; border-radius:10px; border:1px solid #FFD700;">
            <h3 style='text-align:center; color:#FFD700;'>FIN-Saku Report: {sel_b}</h3>
            <table style="width:100%; font-size:18px;">
                <tr><td>Total Pendapatan</td><td style="text-align:right;">{format_rp(sub_df['omzet'].sum())}</td></tr>
                <tr style="color:#FFD700; font-weight:bold;"><td>Total Laba Bersih</td><td style="text-align:right;">{format_rp(sub_df['laba'].sum())}</td></tr>
                <tr><td>Total Prive</td><td style="text-align:right; color:#ff4b4b;">({format_rp(sub_df['prive'].sum())})</td></tr>
                <tr style="background-color:#FFD700; color:#003366; font-weight:bold; font-size:20px;">
                    <td style="padding:10px;">SALDO KAS SAAT INI</td><td style="text-align:right; padding:10px;">{format_rp(mod_berjalan)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        avg_laba = df['laba'].sum() / max(1, len(df['bulan'].unique()))
        rpc = avg_laba * 0.35
        plafon = rpc * 22
        
        if plafon >= 5000000:
            st.markdown(f"""
            <div class="kur-card">
                <h2>✅ STATUS: BANKABLE</h2>
                <p>Rekomendasi Pinjaman: <b>{format_rp(plafon)}</b></p>
                <p>Batas Cicilan Aman: {format_rp(rpc)}/bulan</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kur-card" style="background-color:#ff4b4b !important; color:white !important;">
                <h2 style="color:white !important;">⚠️ STATUS: BELUM LAYAK KUR</h2>
                <p style="color:white !important;">Plafon saat ini ({format_rp(plafon)}) masih di bawah syarat minimal Bank.</p>
            </div>
            """, unsafe_allow_html=True)

    if st.sidebar.button("🗑️ RESET DATABASE"):
        c.execute("DELETE FROM transaksi")
        conn.commit()
        st.rerun()

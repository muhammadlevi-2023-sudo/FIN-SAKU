import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_fix.db', check_same_thread=False)
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

# 2. UI CUSTOM: UNAIR NAVY & GOLD (High Contrast)
st.markdown("""
<style>
    .stApp { background-color: #003366 !important; }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] { background-color: #002244 !important; border-right: 3px solid #FFD700; }
    
    .edu-box { 
        background-color: #ffffff !important; padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; box-shadow: 0 4px 20px rgba(0,0,0,0.5);
        margin-bottom: 25px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { color: #003366 !important; }

    button[data-baseweb="tab"] p { color: #FFD700 !important; font-weight: bold !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #003366 !important; }

    .report-card { 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        padding: 25px; border-radius: 12px; border: 1px solid #FFD700; margin-bottom: 20px;
    }

    .kur-card { background-color: #FFD700 !important; padding: 30px; border-radius: 15px; }
    .kur-card h2, .kur-card p, .kur-card td, .kur-card b { color: #003366 !important; }

    .stButton>button { 
        background-color: #FFD700 !important; color: #003366 !important; 
        font-weight: bold; border-radius: 8px; height: 3.5em; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
p_data = c.fetchone()
saved_nama = p_data[1] if p_data else "Usaha Binaan"
saved_modal = p_data[2] if p_data else 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700 !important;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_usaha = st.text_input("Nama Usaha", saved_nama)
    m_raw = st.text_input("Modal Kas Awal (Rp)", value=str(int(saved_modal)))
    if st.button("💾 SIMPAN PROFIL"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", (nama_usaha, clean_to_int(m_raw)))
        conn.commit()
        st.rerun()
    st.write("---")
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Pusat Data Inovatif: {nama_usaha}")
st.markdown("""<div class="edu-box"><h3>🔍 Mengapa FIN-Saku Membuat UMKM Bankable?</h3>
<p>Bank melihat 3 kriteria: <b>Karakter</b> (kedisiplinan), <b>Kapasitas</b> (laba bersih), dan <b>Modal</b> (prive terkontrol).</p></div>""", unsafe_allow_html=True)

col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Unit Terjual", min_value=0)
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if qty > 0:
            omzet = qty * clean_to_int(harga_raw)
            laba = qty * (clean_to_int(harga_raw) - clean_to_int(hpp_raw))
            prive = laba * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.rerun()

# --- BAGIAN LAPORAN ---
df = pd.read_sql_query("

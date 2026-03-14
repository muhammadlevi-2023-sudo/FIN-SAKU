import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: UNAIR Financial Edition", layout="wide")

# --- DATABASE ENGINE (Auto-Save) ---
conn = sqlite3.connect('finsaku_unair.db', check_same_thread=False)
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

# 2. UI CUSTOM: UNAIR BLUE & GOLD (Hard-Locked)
st.markdown("""
<style>
    /* 1. KUNCI BACKGROUND: Biru Tua UNAIR */
    .stApp {
        background-color: #003366 !important; 
    }

    /* 2. KUNCI WARNA TEKS: Putih & Kuning Emas */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }

    /* 3. SIDEBAR: Lebih Gelap dengan Aksen Kuning */
    [data-testid="stSidebar"] {
        background-color: #002244 !important;
        border-right: 3px solid #FFD700;
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }

    /* 4. BOX EDUKASI: Putih Bersih (Agar berwibawa) dengan Teks Biru */
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 12px; 
        border-left: 10px solid #FFD700; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 25px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { 
        color: #003366 !important; 
    }

    /* 5. TAB: Kuning Emas saat Aktif */
    button[data-baseweb="tab"] p {
        color: #FFD700 !important;
        font-weight: bold !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FFD700 !important;
        border-radius: 5px 5px 0 0;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #003366 !important;
    }

    /* 6. CARD LAPORAN: Biru Muda Transparan dengan Border Kuning */
    .report-card { 
        background-color: rgba(255, 255, 255, 0.1) !important; 
        padding: 30px; border-radius: 10px; 
        border: 2px solid #FFD700; 
        margin-bottom: 20px;
    }

    /* 7. KARTU KUR: Kuning Emas Megah (Gaya UNAIR) */
    .kur-card { 
        background-color: #FFD700 !important; 
        padding: 30px; border-radius: 15px; 
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    .kur-card h2, .kur-card p, .kur-card td, .kur-card b {
        color: #003366 !important;
    }

    /* 8. INPUT FIELD: Border Kuning */
    .stTextInput input, .stNumberInput input {
        background-color: #002244 !important;
        color: #ffffff !important;
        border: 1px solid #FFD700 !important;
    }

    /* 9. TOMBOL: Kuning Emas Teks Biru */
    .stButton>button { 
        background-color: #FFD700 !important; 
        color: #003366 !important; 
        font-weight: bold;
        border-radius: 8px; border: none; height: 3.5em; width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #e6c200 !important;
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
profil_data = c.fetchone()
if profil_data:
    saved_nama, saved_modal = profil_data[1], profil_data[2]
else:
    saved_nama, saved_modal = "Usaha Binaan UNAIR", 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🏢 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_usaha = st.text_input("Nama Usaha", saved_nama)
    m_raw = st.text_input("Kas Awal (Rp)", value=str(int(saved_modal)))
    
    if st.button("💾 SIMPAN PROFIL"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", 
                  (nama_usaha, clean_to_int(m_raw)))
        conn.commit()
        st.success("Profil Tersimpan!")

    st.write("---")
    st.markdown("**Konfigurasi Produk**")
    hpp_raw = st.text_input("HPP (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Ambil Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Dashboard Keuangan: {nama_usaha}")

# EDU BOX
st.markdown(f"""
<div class="edu-box">
    <h3>🎓 Literasi Keuangan UMKM (Standar Perbankan)</h3>
    <p>Berdasarkan studi manajemen risiko, kesehatan usaha Anda diukur dari:</p>
    <ul>
        <li><b>Karakter:</b> Keajegan mencatat transaksi.</li>
        <li><b>Kapasitas:</b> Laba bersih bulanan wajib > 3x lipat cicilan (DSCR > 1.25).</li>
        <li><b>Modal:</b> Kas yang cukup untuk menanggung biaya operasional 3 bulan ke depan.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah Terjual", min_value=0)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if qty > 0:
            omzet = qty * clean_to_int(harga_raw)
            laba = qty * (clean_to_int(harga_raw) - clean_to_int(hpp_raw))
            prive = laba * (prive_pct / 100)
            
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.balloons()
            st.rerun()

# --- ANALISIS ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

if not df.empty:
    st.write("---")
    t_har, t_bul, t_kur = st.tabs(["📆 RIWAYAT", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        sub_df = df[df['bulan'] == sel_b]
        
        omz, lb, prv = sub_df['omzet'].sum(), sub_df['laba'].sum(), sub_df['prive'].sum()
        mod_berjalan = clean_to_int(m_raw) + (df['laba'].sum() - df['prive'].sum())

        st.markdown(f"""
        <div class="report-card">
            <h3 style='text-align:center; color:#FFD700;'>LAPORAN LABA RUGI - {sel_b}</h3>
            <table style="width:100%; font-size:18px;">
                <tr style="border-bottom: 1px solid #FFD700;"><td>Total Omzet</td><td style="text-align:right;">{format_rp(omz)}</td></tr>
                <tr style="font-weight:bold; color:#FFD700;"><td>LABA BERSIH</td><td style="text-align:right;">{format_rp(lb)}</td></tr>
                <tr style="color:#ff4b4b;"><td>Prive (Konsumsi)</td><td style="text-align:right;">({format_rp(prv)})</td></tr>
                <tr style="background-color:#FFD700; color:#003366; font-weight:bold; font-size:20px;">
                    <td style="padding:10px;">TOTAL MODAL KAS</td><td style="text-align:right; padding:10px;">{format_rp(mod_berjalan)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        avg_laba = df['laba'].sum() / max(1, len(df['bulan'].unique()))
        rpc = avg_laba * 0.35
        plafon = rpc * 22
        min_plafon = 5000000

        if plafon >= min_plafon:
            st.markdown(f"""
            <div class="kur-card">
                <h2>✅ STATUS: BANKABLE (LAYAK KUR)</h2>
                <p>Estimasi Plafon Pinjaman: {format_rp(plafon)}</p>
                <p style='font-size:14px;'>Rekomendasi Cicilan Aman: {format_rp(rpc)}/bulan</p>
            </div>
            <div style="background-color:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-top:15px;">
                <b>📌 Saran Analis:</b><br>
                Berdasarkan jurnal ekonomi mikro, kapasitas bayar Anda sudah memenuhi syarat KUR Mikro. 
                Disarankan mengambil tenor 24-36 bulan untuk menjaga arus kas tetap positif.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kur-card" style="background-color: #ff4b4b !important;">
                <h2 style="color: white !important;">⚠️ STATUS: BELUM LAYAK KUR</h2>
                <p style="color: white !important;">Plafon Berdasarkan Data: {format_rp(plafon)}</p>
            </div>
            <div style="background-color:rgba(255,255,255,0.1); padding:15px; border-radius:10px; margin-top:15px;">
                <b>🔍 Analisis Masalah:</b><br>
                Plafon Anda masih di bawah standar minimal perbankan ({format_rp(min_plafon)}).<br><br>
                <b>🚀 Solusi Strategis:</b><br>
                1. <b>Tingkatkan Omzet:</b> Fokus pada pemasaran digital untuk menaikkan volume penjualan.<br>
                2. <b>Disiplin Prive:</b> Kurangi pengambilan pribadi hingga laba bersih stabil.<br>
                3. <b>Kontinuitas:</b> Bank membutuhkan data transaksi minimal 6 bulan berturut-turut.
            </div>
            """, unsafe_allow_html=True)

    if st.sidebar.button("🗑️ RESET SEMUA DATA"):
        c.execute("DELETE FROM transaksi")
        conn.commit()
        st.rerun()

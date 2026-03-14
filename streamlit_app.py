import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE (Auto-Save) ---
conn = sqlite3.connect('finsaku_data.db', check_same_thread=False)
c = conn.cursor()

# Buat tabel jika belum ada
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

# 2. UI CUSTOM: BLACK & GOLD (Premium & Locked)
st.markdown("""
<style>
    .stApp { background-color: #000000 !important; }
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] { background-color: #0e0e0e !important; border-right: 2px solid #FFD700; }
    
    /* Box Edukasi */
    .edu-box { 
        background-color: #1a1a1a !important; padding: 20px; border-radius: 12px; 
        border: 1px solid #FFD700; border-left: 8px solid #FFD700; margin-bottom: 20px;
    }
    
    /* Card Laporan */
    .report-card { 
        background-color: #1a1a1a !important; padding: 25px; border-radius: 10px; 
        border: 1px solid #FFD700; margin-bottom: 20px;
    }
    
    /* Kartu KUR */
    .kur-card { 
        background-color: #FFD700 !important; padding: 25px; border-radius: 15px; 
    }
    .kur-card * { color: #000000 !important; font-weight: bold; }
    
    /* Saran Box */
    .saran-box {
        background-color: #332b00 !important; padding: 15px; border-radius: 8px;
        border: 1px solid #FFD700; margin-top: 10px;
    }

    .stButton>button { 
        background-color: #FFD700 !important; color: #000000 !important; 
        font-weight: bold; border-radius: 8px; width: 100%; height: 3em;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
profil_data = c.fetchone()
if profil_data:
    saved_nama, saved_modal = profil_data[1], profil_data[2]
else:
    saved_nama, saved_modal = "Usaha Baru", 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_usaha = st.text_input("Nama Usaha", saved_nama)
    m_raw = st.text_input("Uang Kas Awal (Rp)", value=str(int(saved_modal)))
    
    if st.button("💾 SIMPAN PROFIL"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", 
                  (nama_usaha, clean_to_int(m_raw)))
        conn.commit()
        st.success("Profil Diperbarui!")

    st.write("---")
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Dashboard Inklusi: {nama_usaha}")

col_input, col_edu = st.columns([1, 1.2])

with col_edu:
    st.markdown("""
    <div class="edu-box">
        <h3 style='margin-top:0;'>💡 Mengapa Data Ini Penting?</h3>
        <p style='font-size:14px;'>Berdasarkan <b>Prinsip 5C Perbankan</b> (Character, Capacity, Capital, Collateral, Condition), 
        catatan harian Anda membuktikan <b>Karakter</b> disiplin dan <b>Kapasitas</b> bayar yang nyata.</p>
    </div>
    """, unsafe_allow_html=True)

with col_input:
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
            st.balloons()

# --- TAMPILKAN DATA DARI DATABASE ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

if not df.empty:
    st.write("---")
    t_har, t_bul, t_kur = st.tabs(["📆 HARIAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    with t_har:
        render_df = df.tail(5) # Tampilkan 5 transaksi terakhir
        st.table(render_df[['tanggal', 'omzet', 'laba']])

    with t_kur:
        # LOGIKA KUR BANKABLE
        avg_laba = df['laba'].sum() / max(1, len(df['bulan'].unique()))
        rpc = avg_laba * 0.35 # Batas cicilan aman 35% dari laba
        plafon_estimasi = rpc * 22 
        
        # Standar Minimal KUR Mikro biasanya Rp 1.000.000 s/d Rp 10.000.000
        min_plafon_bank = 5000000 

        if plafon_estimasi >= min_plafon_bank:
            st.markdown(f"""
            <div class="kur-card">
                <h2>✅ STATUS: BANKABLE (LAYAK KUR)</h2>
                <p>Estimasi Plafon: {format_rp(plafon_estimasi)}</p>
                <p style='font-size:14px;'>Cicilan Aman: {format_rp(rpc)}/bulan</p>
            </div>
            <div class="saran-box">
                <b>📌 Saran Strategis:</b><br>
                Gunakan pinjaman ini untuk <i>Scaling Up</i> (menambah aset produktif), bukan untuk konsumsi. 
                Pertahankan DSCR (Debt Service Coverage Ratio) di atas 1.25x agar kesehatan keuangan terjaga.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="kur-card" style="background-color: #ff4b4b !important;">
                <h2 style="color: white !important;">⚠️ STATUS: BELUM BANKABLE</h2>
                <p style="color: white !important;">Rekomendasi Plafon: {format_rp(plafon_estimasi)}</p>
            </div>
            <div class="saran-box">
                <b>🔍 Mengapa Belum Layak?</b><br>
                Sesuai standar teknis perbankan, kapasitas bayar Anda saat ini masih di bawah batas minimal plafon KUR Mikro ({format_rp(min_plafon_bank)}).<br><br>
                <b>🚀 Apa yang Harus Dilakukan?</b><br>
                1. <b>Efisiensi Biaya:</b> Turunkan HPP atau tekan biaya operasional untuk menaikkan laba bersih.<br>
                2. <b>Reinvestasi:</b> Kurangi persentase Prive (ambil pribadi) untuk sementara waktu guna memperkuat modal kas.<br>
                3. <b>Catat Terus:</b> Bank menyukai tren data minimal 6 bulan yang stabil.
            </div>
            """, unsafe_allow_html=True)

    if st.button("❌ HAPUS SEMUA DATA"):
        c.execute("DELETE FROM transaksi")
        conn.commit()
        st.rerun()

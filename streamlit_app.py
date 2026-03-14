import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v12.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        abs_angka = abs(float(angka))
        formatted = "{:,.0f}".format(abs_angka).replace(",", ".")
        return f"Rp -{formatted}" if angka < 0 else f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI MODERN (GLASSMORPHISM STYLE)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .stApp { 
        background: radial-gradient(circle at top right, #001f3f, #000b18); 
    }
    
    /* Kartu Transparan Modern */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px; border-radius: 20px;
        margin-bottom: 20px;
        color: white !important;
    }
    
    .bank-card {
        background: #ffffff;
        color: #001f3f !important;
        padding: 25px; border-radius: 20px;
        border-left: 8px solid #FFD700;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* Button Glow */
    .stButton>button {
        background: linear-gradient(90deg, #FFD700, #FFA500) !important;
        color: #000 !important; font-weight: 800; border: none;
        border-radius: 12px; height: 3em; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 0 15px #FFD700; }

    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #000b18 !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PENGATURAN USAHA ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.markdown("---")
    nama_u = st.text_input("🏷️ Nama Toko/Usaha", "UMKM Maju")
    modal_awal = clean_to_int(st.text_input("🏦 Modal Awal Kas", "7000000"))
    
    modal_skrg = modal_awal + (total_laba - total_prive)
    
    st.markdown("### Posisi Kas Saat Ini")
    color = "#00ff88" if modal_skrg >= modal_awal else "#ff4b4b"
    st.markdown(f"<h2 style='color:{color};'>{format_rp(modal_skrg)}</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("📦 Setting Harga & HPP")
    hpp_val = clean_to_int(st.text_input("Harga Beli (Modal)", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Jajan / Prive (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard {nama_u}")

# AREA 1: RINGKASAN BANKABILITY (Paling Atas)
if not df.empty:
    laba_akhir = df.iloc[-1]['laba']
    rpc = laba_akhir * 0.35
    bulan_aktif = df['bulan'].nunique()

    st.markdown('<div class="bank-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='margin:0;'>🏦 Status Skor Bank (KUR BRI)</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write("Sanggup Cicil/Bulan:")
        st.markdown(f"**{format_rp(rpc)}**")
    with c2:
        st.write("Kedisiplinan Data:")
        st.markdown(f"**{bulan_aktif} Bulan Aktif**")
    with c3:
        status = "Layak" if laba_akhir > 0 and bulan_aktif >= 1 else "Pantau"
        st.markdown(f"Status: **{status}**")
    st.markdown('</div>', unsafe_allow_html=True)

# AREA 2: FORM INPUT (DIBUAT LEBIH MUDAH)
st.markdown("### 📝 Langkah 1: Catat Penjualan")
with st.container():
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    col_a, col_b = st.columns([1, 1])
    
    with col_a:
        tgl = st.date_input("Kapan Transaksi Ini?", datetime.now())
        mode = st.radio("Apa yang ingin dicatat?", ["Total Omzet Seharian", "Hanya Satu Transaksi"], horizontal=True)
    
    with col_b:
        omzet = st.number_input("Masukkan Total Uang Masuk (Rp)", value=0, step=50000)
        
        # Hitung Laba
        if hrg_val > 0:
            laba = omzet - (omzet * (hpp_val / hrg_val))
        else: laba = 0
        prive = laba * (prive_pct / 100) if laba > 0 else 0
        
        st.markdown(f"**Hasilnya:** Laba {format_rp(laba)} | Jatah Jajan {format_rp(prive)}")

    if st.button("🚀 SIMPAN DATA KE LAPORAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, "Input Cepat"))
        conn.commit()
        st.success("Data Tersimpan! Cek Laporan di bawah.")
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# AREA 3: LAPORAN & KUR
if not df.empty:
    st.markdown("### 📊 Langkah 2: Pantau Perkembangan")
    t1, t2 = st.tabs(["Laporan Bulanan", "Analisis Pinjaman KUR"])
    
    with t1:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        st.table(db[['tanggal', 'omzet', 'laba', 'prive']])
    
    with t2:
        plafon = (df.iloc[-1]['laba'] * 0.35) * 22
        st.info(f"Berdasarkan performa terakhir, Anda disarankan meminjam maksimal **{format_rp(plafon)}**")

# AREA 4: REVISI (PALING BAWAH)
with st.expander("⚙️ Koreksi / Hapus Data Salah"):
    if not df.empty:
        pilihan = st.selectbox("Pilih Data yang Salah", df['id'].tolist())
        if st.button("Hapus Data"):
            c.execute(f"DELETE FROM transaksi WHERE id = {pilihan}")
            conn.commit()
            st.rerun()

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. DATABASE SETUP
conn = sqlite3.connect('finsaku_final_v11.db', check_same_thread=False)
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

# 2. UI STYLING
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; color: white !important; }
    .white-card {
        background-color: #ffffff !important; padding: 20px; border-radius: 12px;
        border-left: 8px solid #FFD700; margin-bottom: 15px;
    }
    .white-card * { color: #000000 !important; font-weight: 700 !important; }
    .stMetric { background-color: #002b5c; padding: 10px; border-radius: 10px; border: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: MODAL AWAL ---
with st.sidebar:
    st.header("💰 Pengaturan Modal")
    modal_awal_input = st.text_input("Input Modal Awal (Rp)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    st.markdown(f"**Tercatat Awal: {format_rp(modal_awal)}**")
    
    st.write("---")
    st.header("📦 Produk")
    hpp = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- LOGIKA HITUNG SALDO BERJALAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0
# Modal Akhir = Modal Awal + Laba Bersih yang disimpan (Retained Earnings)
modal_akhir = modal_awal + (total_laba - total_prive)

# --- DASHBOARD ---
st.title("Update Modal & Kelayakan KUR")

# TAMPILAN SALDO MODAL TERKINI
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.metric("Modal Awal", format_rp(modal_awal))
with col_m2:
    delta_modal = total_laba - total_prive
    st.metric("Modal Saat Ini (Update)", format_rp(modal_akhir), delta=format_rp(delta_modal))

# INPUT TRANSAKSI (Sama seperti sebelumnya namun tetap update modal)
st.write("---")
with st.expander("➕ Tambah Transaksi Baru"):
    tgl = st.date_input("Tanggal", datetime.now())
    mode = st.radio("Metode:", ["Satuan", "Total Omzet"], horizontal=True)
    if mode == "Satuan":
        qty = st.number_input("Jumlah", min_value=0)
        omzet = qty * hrg
        laba = qty * (hrg - hpp)
    else:
        omzet = st.number_input("Omzet", min_value=0)
        ratio = (hrg - hpp) / hrg if hrg > 0 else 0
        laba = omzet * ratio
    
    prive = laba * (prive_pct / 100)
    if st.button("Simpan & Update Modal"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"M-{tgl.isocalendar()[1]}", omzet, laba, prive))
        conn.commit()
        st.success("Data masuk! Modal otomatis terupdate.")
        st.rerun()

# --- ANALISIS KUR DINAMIS ---
if not df.empty:
    st.write("---")
    st.header("🏦 Analisis KUR BRI (Berbasis Tren)")
    
    metode_analisis = st.selectbox("Gunakan Data Untuk Analisis:", ["Rata-rata Semua Bulan", "Hanya Bulan Terakhir"])
    
    if metode_analisis == "Hanya Bulan Terakhir":
        bulan_terakhir = df['bulan'].iloc[-1]
        data_analisis = df[df['bulan'] == bulan_terakhir]
        label_ket = f"Bulan {bulan_terakhir}"
    else:
        # Rata-rata laba bulanan
        data_analisis = df.groupby('bulan').sum().mean().to_frame().T
        label_ket = "Rata-rata Kumulatif"

    laba_ref = data_analisis['laba'].values[0]
    rpc = laba_ref * 0.35
    plafon = rpc * 22
    
    st.markdown(f"""
    <div class="white-card">
        <h3>Hasil Analisis ({label_ket}):</h3>
        <p>Laba yang dihitung: <b>{format_rp(laba_ref)}</b></p>
        <p>Cicilan Maksimal (RPC 35%): <b>{format_rp(rpc)}</b></p>
        <hr>
        <p>Dengan kondisi keuangan <b>{label_ket}</b>, Bank BRI kemungkinan besar menyetujui pinjaman sebesar:</p>
        <h1 style="font-size:40px;">{format_rp(plafon)}</h1>
    </div>
    """, unsafe_allow_html=True)

    # ANALISIS RISIKO BERDASARKAN MODAL TERSEDIA
    st.subheader("⚠️ Risiko & Beban Bunga")
    bunga_bln = plafon * (0.005) # 0.5% per bulan
    beban_modal = (bunga_bln / modal_akhir) * 100 if modal_akhir > 0 else 0
    
    st.info(f"""
    **Informasi Risiko:**
    1. Jika meminjam sesuai plafon, bunga bulanan Anda adalah **{format_rp(bunga_bln)}**.
    2. Beban bunga ini hanya sebesar **{beban_modal:.2f}%** dari total Modal Tersedia Anda saat ini ({format_rp(modal_akhir)}).
    3. Ini menunjukkan usaha Anda sangat sehat karena bunga bank tidak sampai merusak modal inti usaha.
    """)

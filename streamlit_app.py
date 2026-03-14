import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali Modal UMKM", layout="wide")

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
        if angka < 0: return f"Rp -{formatted}"
        return f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM (NAVY & GOLD) - LEBIH MODERN & BERSIH
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 25px; border-radius: 15px; border-top: 5px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 8px 16px rgba(0,0,0,0.4);
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3 { color: #000000 !important; }
    .stButton>button { 
        background-color: #FFD700 !important; color: #000 !important; 
        font-weight: bold; border-radius: 8px; height: 3em;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #002b59; border-radius: 10px 10px 0 0; padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PROFIL USAHA ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal (Modal)", "7000000"))
    modal_sekarang = modal_awal + (total_laba - total_prive)
    
    st.markdown(f"Modal Terkini: <h2 style='color:#FFD700;'>{format_rp(modal_sekarang)}</h2>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("⚙️ Aturan Harga Produk")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Jajan / Prive (%)", 0, 50, 30)

# --- BAGIAN ATAS: INPUT & REVISI (DIBUAT RAPI) ---
st.title(f"Pusat Kendali: {nama_u}")

col_main, col_sub = st.columns([1.5, 1])

with col_main:
    with st.container():
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.subheader("➕ Catat Uang Masuk")
        rekap_mode = st.selectbox("Pilih Cara Catat:", ["Harian", "Mingguan", "Bulanan"])
        
        c1, c2 = st.columns(2)
        with c1: tgl = st.date_input("Tanggal Transaksi", datetime.now())
        with c2: omzet = st.number_input(f"Total Omzet ({rekap_mode})", value=0, step=10000)
        
        laba_in = omzet - (omzet * (hpp_val / hrg_val)) if hrg_val > 0 else 0
        prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0
        
        st.info(f"Dari omzet ini, perkiraan untung bersih Anda: {format_rp(laba_in)}")
        
        if st.button("🚀 SIMPAN SEKARANG"):
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba_in, prive_in, rekap_mode))
            conn.commit()
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

with col_sub:
    with st.container():
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        st.subheader("🛠️ Perbaiki Data")
        if not df.empty:
            df_rev = df.sort_values(by='id', ascending=False).head(5)
            pilih = st.selectbox("Pilih data yang salah:", [f"ID {r['id']} - {r['tanggal']} - {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
            if st.button("🗑️ Hapus Data Ini"):
                c.execute(f"DELETE FROM transaksi WHERE id = {int(pilih.split(' ')[1])}")
                conn.commit()
                st.rerun()
        else: st.write("Belum ada data untuk diperbaiki.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- BAGIAN BAWAH: ANALISIS BESAR (TAB) ---
st.write("---")
tab_modal, tab_kur = st.tabs(["📊 CEK PERTUMBUHAN MODAL", "🏦 CEK KELAYAKAN PINJAM BANK"])

with tab_modal:
    if not df.empty:
        sel_b = st.selectbox("Lihat Laporan Bulan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        l_bln, p_bln = db['laba'].sum(), db['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Dompet Usaha - {sel_b}</h3>
            <hr>
            <table style="width:100%; font-size:20px; color:black;">
                <tr><td>Total Untung (Laba)</td><td style="text-align:right; color:green;">{format_rp(l_bln)}</td></tr>
                <tr><td>Diambil Sendiri (Prive)</td><td style="text-align:right; color:red;">({format_rp(p_bln)})</td></tr>
                <tr style="font-weight:bold; border-top:3px solid black; font-size:24px;">
                    <td>Sisa Uang Masuk ke Modal</td><td style="text-align:right;">{format_rp(l_bln - p_bln)}</td>
                </tr>
            </table>
            <br>
            <p>💡 <b>Artinya:</b> Uang kas Anda bertambah <b>{format_rp(l_bln - p_bln)}</b> bulan ini setelah dikurangi jajan pribadi.</p>
        </div>""", unsafe_allow_html=True)
    else: st.warning("Belum ada data untuk dianalisis.")

with tab_kur:
    if not df.empty:
        # Gunakan rata-rata laba harian sebagai patokan keamanan
        laba_patokan = df['laba'].mean() * (30 if rekap_mode == "Harian" else 1)
        jatah_cicilan = laba_patokan * 0.35 # Batas aman 35% laba

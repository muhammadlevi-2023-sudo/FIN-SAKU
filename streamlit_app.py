import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v12.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    # Logika untuk menangani angka negatif (Rugi)
    try:
        abs_angka = abs(float(angka))
        formatted = "Rp {:,.0f}".format(abs_angka).replace(",", ".")
        return f"- {formatted}" if angka < 0 else f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    # Tetap bisa baca angka meskipun user input manual
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 25px; border-radius: 15px; border-left: 10px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .white-card *, .white-card p, .white-card b, .white-card td, .white-card h3, .white-card h1 {
        color: #000000 !important; font-weight: 800 !important;
    }
    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 2px solid #FFD700; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA MODAL BERJALAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba_kumulatif = df['laba'].sum() if not df.empty else 0
total_prive_kumulatif = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    
    modal_awal = clean_to_int(st.text_input("Modal Kas Awal (Rp)", "7000000"))
    modal_sekarang = modal_awal + (total_laba_kumulatif - total_prive_kumulatif)
    
    st.markdown(f"**Modal Awal: {format_rp(modal_awal)}**")
    color_modal = "#FFD700" if modal_sekarang >= modal_awal else "#FF4B4B"
    st.markdown(f"**Modal Terkini: <span style='color:{color_modal};'>{format_rp(modal_sekarang)}</span>**", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_val = clean_to_int(st.text_input("HPP / Modal Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual Produk", "15000"))
    
    if hrg_val > 0:
        margin_rp = hrg_val - hpp_val
        margin_pct = (margin_rp / hrg_val) * 100
        st.markdown(f"Margin: **{margin_pct:.1f}%** ({format_rp(margin_rp)})")
        if margin_pct <= 0: st.error("⚠️ AWAS! Harga jual lebih rendah dari modal (RUGI).")

    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input {rekap_mode}")
    tgl = st.date_input("Tanggal", datetime.now())
    
    # Menghapus min_value agar bisa input angka kecil atau 0 jika rugi total
    omzet = st.number_input(f"Total Omzet {rekap_mode}", value=0, step=1000)
    
    # Hitung Laba/Rugi: Laba = Omzet - (Omzet / Harga Jual * HPP)
    # Ini memastikan kalau omzet dikit, labanya bisa minus (Rugi)
    if hrg_val > 0:
        beban_pokok = omzet * (hpp_val / hrg_val)
        laba = omzet - beban_pokok
    else:
        laba = 0

    # Jika laba negatif (Rugi), Prive otomatis 0 karena tidak ada yang bisa diambil
    prive = laba * (prive_pct / 100) if laba > 0 else 0

    if laba < 0:
        st.error(f"⚠️ Terdeteksi Rugi: {format_rp(laba)}")
    else:
        st.success(f"Estimasi Laba: {format_rp(laba)}")

    if st.button("🔔 SIMPAN KE LAPORAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
        conn.commit()
        st.rerun()

# --- ANALISIS KUR (BULAN TERAKHIR) ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI"])

    with t_rep:
        sel_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        data_b = df[df['bulan'] == sel_b]
        o, l, p = data_b['omzet'].sum(), data_b['laba'].sum(), data_b['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Bulanan: {sel_b}</h3>
            <table style="width:100%; font-size:1.1em;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Beban Usaha (HPP)</td><td style="text-align:right;">{format_rp(o-l)}</td></tr>
                <tr style="border-top: 2px solid black;">
                    <td><b>LABA/RUGI BERSIH</b></td>
                    <td style="text-align:right; color:{'red' if l < 0 else 'black'};"><b>{format_rp(l)}</b></td>
                </tr>
                <tr><td>Prive (Diambil)</td><td style="text-align:right;">({format_rp(p)})</td></tr>
                <tr style="background:#fff9c4;"><td><b>SISA KAS (UPDATE MODAL)</b></td><td style="text-align:right;"><b>{format_rp(l-p)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        # LOGIKA KUR BERBASIS BULAN TERAKHIR
        bulan_terakhir = df['bulan'].iloc[-1]
        data_akhir = df[df['bulan'] == bulan_terakhir]
        laba_akhir = data_akhir['laba'].sum()
        
        # Jika laba akhir rugi, maka KUR tidak bisa diproses
        if laba_akhir <= 0:
            st.error(f"🛑 BANKABILITY: TIDAK LAYAK. Bulan {bulan_terakhir} Anda mengalami rugi. Bank tidak bisa memproses KUR jika laba negatif.")
        else:
            rpc = laba_akhir * 0.35
            plafon = rpc * 22
            st.subheader(f"🏦 Analisis BRI (Bulan: {bulan_terakhir})")
            st.metric("Plafon Maksimal", format_rp(plafon))
            st.info(f"Karena Modal Terkini Anda {format_rp(modal_sekarang)}, pinjaman ini memiliki risiko bunga {( (plafon*0.005) / modal_sekarang * 100):.1f}% terhadap modal inti.")

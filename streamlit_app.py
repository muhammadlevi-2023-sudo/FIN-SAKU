import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v11.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

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

# --- SIDEBAR: INPUT MODAL & PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    
    modal_input = st.text_input("Modal Kas Awal (Rp)", "7000000")
    modal_awal = clean_to_int(modal_input)
    
    # HITUNG MODAL UPDATE (Modal Awal + Laba - Prive)
    modal_sekarang = modal_awal + (total_laba_kumulatif - total_prive_kumulatif)
    st.markdown(f"**Modal Awal: {format_rp(modal_awal)}**")
    st.markdown(f"**Modal Terkini: <span style='color:#FFD700;'>{format_rp(modal_sekarang)}</span>**", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_val = clean_to_int(st.text_input("HPP (Modal) /Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual /Produk", "15000"))
    
    # HITUNG MARGIN OTOMATIS
    if hrg_val > 0:
        margin_rp = hrg_val - hpp_val
        margin_pct = (margin_rp / hrg_val) * 100
        st.markdown(f"Margin: **{margin_pct:.1f}%** ({format_rp(margin_rp)})")
        
        # CAPTION SARAN MARGIN
        if margin_pct < 20:
            st.warning("⚠️ Margin rendah. Saran: 20-40% untuk keamanan operasional.")
        elif 20 <= margin_pct <= 50:
            st.success("✅ Margin sehat untuk UMKM.")
        else:
            st.info("💡 Margin tinggi. Pastikan harga tetap kompetitif.")

    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

# INPUT TRANSAKSI
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input {rekap_mode}")
    tgl = st.date_input("Tanggal", datetime.now())
    
    if rekap_mode == "Harian":
        input_type = st.radio("Metode:", ["Per Produk", "Total Omzet"], horizontal=True)
        if input_type == "Per Produk":
            qty = st.number_input("Unit Terjual", min_value=0, step=1)
            omzet = qty * hrg_val
            laba = qty * (hrg_val - hpp_val)
        else:
            omzet = st.number_input("Total Omzet Hari Ini", min_value=0, step=1000)
            ratio = (hrg_val - hpp_val) / hrg_val if hrg_val > 0 else 0
            laba = omzet * ratio
    else:
        omzet = st.number_input(f"Total Omzet 1 {rekap_mode}", min_value=0, step=10000)
        ratio = (hrg_val - hpp_val) / hrg_val if hrg_val > 0 else 0
        laba = omzet * ratio

    prive = laba * (prive_pct / 100)

    if st.button("🔔 SIMPAN KE LAPORAN"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
            conn.commit()
            st.success("Tersimpan & Modal Terupdate!")
            st.rerun()

with col_guidance:
    st.markdown(f"""
    <div class="white-card">
        <h3>💰 Laporan Laba Rugi Sederhana</h3>
        <p><b>Modal Berjalan:</b> Kas Anda bertambah jika laba disimpan, dan berkurang jika ada kerugian atau penarikan Prive berlebih.</p>
        <hr>
        <p><b>Status Kas Saat Ini:</b> {format_rp(modal_sekarang)}</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN & ANALISIS KUR ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN PERIODIK", "🏦 KELAYAKAN KUR BRI (BULAN TERAKHIR)"])

    with t_rep:
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        data_b = df[df['bulan'] == sel_b]
        o, l, p = data_b['omzet'].sum(), data_b['laba'].sum(), data_b['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Bulanan: {sel_b}</h3>
            <table style="width:100%; font-size:1.1em;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>HPP / Beban Pokok</td><td style="text-align:right;">{format_rp(o-l)}</td></tr>
                <tr style="border-top: 2px solid black;"><td><b>LABA BERSIH (Earning)</b></td><td style="text-align:right;"><b>{format_rp(l)}</b></td></tr>
                <tr><td>Prive (Konsumsi)</td><td style="text-align:right; color:red;">({format_rp(p)})</td></tr>
                <tr style="background:#fff9c4;"><td><b>SISA LABA UNTUK MODAL</b></td><td style="text-align:right;"><b>{format_rp(l-p)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        # LOGIKA: MENGGUNAKAN DATA BULAN TERAKHIR
        bulan_terakhir = df['bulan'].iloc[-1]
        data_akhir = df[df['bulan'] == bulan_terakhir]
        
        laba_akhir = data_akhir['laba'].sum()
        prive_akhir = data_akhir['prive'].sum()
        laba_bebas = laba_akhir - prive_akhir
        
        # Standar RPC BRI (35% dari Laba Bulan Terakhir)
        rpc_aman = laba_akhir * 0.35
        plafon_max = rpc_aman * 24
        
        st.subheader(f"🏦 Analisis Berdasarkan Performa: {bulan_terakhir}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Kapasitas Cicilan", format_rp(rpc_aman))
        col2.metric("Saran Plafon KUR", format_rp(plafon_max))
        col3.metric("Laba Tersedia", format_rp(laba_bebas))

        # Simulasi Bunga (0.5% per bulan)
        est_bunga_bulan = plafon_max * 0.005
        
        st.markdown(f"""
        <div class="white-card">
            <h4>Analisis Skor KUR BRI:</h4>
            <ul>
                <li><b>Dasar Plafon:</b> BRI melihat laba terakhir Anda (<b>{format_rp(laba_akhir)}</b>).</li>
                <li><b>Risiko Bunga:</b> Dengan plafon {format_rp(plafon_max)}, bunga per bulan adalah <b>{format_rp(est_bunga_bulan)}</b>.</li>
                <li><b>Ketahanan Modal:</b> Bunga tersebut hanya memakan sebagian kecil dari Modal Terupdate Anda ({format_rp(modal_sekarang)}).</li>
                <li><b>Status Kelayakan:</b> {"✅ SANGAT LAYAK (Bankable)" if plafon_max >= 5000000 else "⚠️ BELUM LAYAK (Tingkatkan Laba)"}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if plafon_max < 5000000:
            target_laba = (5000000 / 24) / 0.35
            st.warning(f"**Saran Strategi:** Laba bulan {bulan_terakhir} masih kurang {format_rp(target_laba - laba_akhir)} untuk pengajuan KUR minimal.")

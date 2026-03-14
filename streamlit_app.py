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
    try:
        abs_angka = abs(float(angka))
        formatted = "Rp {:,.0f}".format(abs_angka).replace(",", ".")
        return f"- {formatted}" if angka < 0 else f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM (NAVY & GOLD)
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

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    
    modal_awal = clean_to_int(st.text_input("Modal Kas Awal (Rp)", "7000000"))
    modal_sekarang = modal_awal + (total_laba - total_prive)
    
    st.markdown(f"**Modal Awal: {format_rp(modal_awal)}**")
    color_modal = "#FFD700" if modal_sekarang >= modal_awal else "#FF4B4B"
    st.markdown(f"**Modal Terkini: <span style='color:{color_modal};'>{format_rp(modal_sekarang)}</span>**", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_val = clean_to_int(st.text_input("HPP / Modal Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual Produk", "15000"))
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA (FOKUS INPUT) ---
st.title(f"Pusat Analisis: {nama_u}")

rekap_mode = st.selectbox("Pilih Cara Mencatat Hari Ini:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Form Input {rekap_mode}")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    omzet = st.number_input(f"Total Omzet ({rekap_mode})", value=0, step=1000)
    
    if hrg_val > 0:
        laba = omzet - (omzet * (hpp_val / hrg_val))
    else: laba = 0
    prive = laba * (prive_pct / 100) if laba > 0 else 0

    if laba < 0: st.error(f"⚠️ Terdeteksi Rugi: {format_rp(laba)}")
    else: st.success(f"Estimasi Laba Bersih: {format_rp(laba)}")

    if st.button("🔔 SIMPAN KE LAPORAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
        conn.commit()
        st.rerun()

with col_guidance:
    st.markdown(f"""
    <div class="white-card">
        <h3>💡 Tips Bankability</h3>
        <p>Agar layak KUR, Bank BRI sangat memperhatikan pemisahan uang:</p>
        <ul>
            <li><b>Uang Kas:</b> Simpan di wadah/rekening terpisah untuk operasional.</li>
            <li><b>Uang Prive:</b> Inilah "Gaji" Anda. Hanya ini yang boleh dipakai jajan.</li>
        </ul>
        <p>Status saat ini: <b>{prive_pct}% Laba</b> dialokasikan untuk pribadi.</p>
    </div>
    """, unsafe_allow_html=True)

# --- AREA HASIL & ANALISIS ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI"])
    
    with t_rep:
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        st.markdown(f"""<div class="white-card">
            <h3 style="text-align:center;">Ringkasan Bulanan: {sel_b}</h3>
            <table style="width:100%;">
                <tr><td>Total Penjualan (Omzet)</td><td style="text-align:right;">{format_rp(db['omzet'].sum())}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(db['laba'].sum())}</td></tr>
                <tr><td>Prive (Gaji Owner)</td><td style="text-align:right;">({format_rp(db['prive'].sum())})</td></tr>
            </table></div>""", unsafe_allow_html=True)

    with t_kur:
        # LOGIKA PINDAHAN DARI DASHBOARD KE SINI
        laba_akhir = df.iloc[-1]['laba']
        rpc_aman = laba_akhir * 0.35
        plafon = rpc_aman * 22
        bulan_aktif = df['bulan'].nunique()
        pertumbuhan = ((modal_sekarang - modal_awal) / modal_awal * 100) if modal_awal > 0 else 0

        st.markdown(f"### 🏦 Analisis Strategis KUR BRI")
        
        # Kartu Ringkasan (Pindahan dari Dashboard)
        st.markdown('<div class="white-card">', unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        with m1:
            st.write("**Cicilan Aman (RPC):**")
            st.subheader(format_rp(rpc_aman))
            st.caption("35% dari Laba terakhir")
        with m2:
            st.write("**Kontinuitas Usaha:**")
            st.subheader(f"{bulan_aktif} Bulan")
            st.progress(min(bulan_aktif / 6, 1.0))
            st.caption("Target Bank: Min. 6 Bulan")
        with m3:
            st.write("**Kesehatan Modal:**")
            st.subheader(f"{pertumbuhan:.1f}%")
            st.caption("Pertumbuhan Modal Awal")
        st.markdown("</div>", unsafe_allow_html=True)

        # Detail Perhitungan
        st.success(f"**STATUS: LAYAK AJUKAN**")
        st.markdown(f"""
        <div class="white-card">
            <p>Berdasarkan data {df.iloc[-1]['bulan']}, strategi pinjaman Anda:</p>
            <ul>
                <li><b>Saran Plafon:</b> Maksimal {format_rp(plafon)}</li>
                <li><b>Tenor Ideal:</b> 24 - 36 Bulan</li>
                <li><b>Analisis:</b> Laba Anda mampu mengcover angsuran {format_rp(rpc_aman)} secara stabil.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# --- FITUR REVISI (PALING BAWAH) ---
st.write("---")
with st.expander("KOREKSI DATA LAPORAN KEUANGAN"):
    df_rev = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id DESC", conn)
    if not df_rev.empty:
        list_rev = [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()]
        target = st.selectbox("Pilih data yang ingin dihapus:", list_rev)
        if st.button("🗑️ KONFIRMASI HAPUS"):
            c.execute(f"DELETE FROM transaksi WHERE id = {int(target.split(' | ')[0])}")
            conn.commit()
            st.rerun()

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
        formatted = "{:,.0f}".format(abs_angka).replace(",", ".")
        return f"Rp {formatted}"
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
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card h1 {
        color: #000000 !important;
    }
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
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    jenis_u = st.selectbox("Jenis Usaha", ["Dagang", "Jasa", "Produksi"])
    modal_awal = clean_to_int(st.text_input("Modal Kas Awal (Rp)", "7000000"))
    
    modal_sekarang = modal_awal + (total_laba - total_prive)
    st.markdown(f"**Modal Terkini: {format_rp(modal_sekarang)}**")
    
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP / Modal Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual Produk", "15000"))
    prive_pct = st.slider("Jatah Uang Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

rekap_mode = st.selectbox("Pilih Cara Mencatat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Form Input {rekap_mode}")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    omzet = st.number_input(f"Total Uang Masuk ({rekap_mode})", value=0)
    
    laba = omzet - (omzet * (hpp_val / hrg_val)) if hrg_val > 0 else 0
    prive = laba * (prive_pct / 100) if laba > 0 else 0

    if st.button("🔔 SIMPAN KE LAPORAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
        conn.commit()
        st.rerun()

with col_guidance:
    margin_p = ((hrg_val - hpp_val) / hrg_val * 100) if hrg_val > 0 else 0
    st.markdown(f"""
    <div class="white-card">
        <h3>📊 Analisis Margin</h3>
        <p>Margin Keuntungan: <b>{margin_p:.1f}%</b></p>
        <p><i>💡 Tips: Untuk usaha {jenis_u}, pastikan margin ini cukup untuk menutupi biaya operasional (listrik, plastik, dll).</i></p>
    </div>
    """, unsafe_allow_html=True)

# --- AREA HASIL & ANALISIS KUR ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 SIMULASI PINJAMAN KUR BRI"])
    
    with t_rep:
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        st.markdown(f"""<div class="white-card">
            <h3 style="text-align:center;">Laporan: {sel_b}</h3>
            <table style="width:100%;">
                <tr><td>Total Uang Masuk</td><td style="text-align:right;">{format_rp(db['omzet'].sum())}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(db['laba'].sum())}</td></tr>
                <tr><td>Uang Diambil (Prive)</td><td style="text-align:right;">({format_rp(db['prive'].sum())})</td></tr>
            </table></div>""", unsafe_allow_html=True)

    with t_kur:
        # DATA UNTUK ANALISIS
        laba_akhir = df.iloc[-1]['laba']
        rpc_aman = laba_akhir * 0.35 # Batas cicilan aman 35% dari laba
        
        # Simulasi Pinjaman (KUR Mikro BRI umumnya mulai dari 10jt - 50jt - 100jt)
        # Kita hitung plafon maksimal berdasarkan rpc (Plafon = RPC * 24 bulan)
        plafon_maks = (rpc_aman * 24)
        if plafon_maks < 10000000: plafon_maks = 10000000 # Minimal KUR Mikro 10 Juta
        
        st.markdown("### 🏦 Cek Kelayakan Pinjaman Anda")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="white-card">
                <h4>📈 Kondisi Terakhir</h4>
                <p>Laba Bersih Terakhir: <b>{format_rp(laba_akhir)}</b></p>
                <p>Kesehatan Modal: <b>{'✅ SANGAT BAIK' if modal_sekarang > modal_awal else '⚠️ PERLU HEMAT'}</b></p>
                <hr>
                <p>Sanggup Cicil per Bulan: <br><b style='font-size:24px; color:#28a745;'>{format_rp(rpc_aman)}</b></p>
                <p style='font-size:12px;'>*Ini adalah 35% dari laba Anda agar usaha tidak macet.</p>
            </div>""", unsafe_allow_html=True)
            
        with c2:
            # Hitung Bunga KUR BRI (6% per tahun atau 0.5% per bulan)
            bunga_bln = 0.005 
            tenor = 24
            angsuran_pokok = plafon_maks / tenor
            total_angsuran = angsuran_pokok + (plafon_maks * bunga_bln)
            
            st.markdown(f"""<div class="white-card">
                <h4>💰 Saran Pinjaman BRI</h4>
                <p>Plafon Pinjaman Aman:</p>
                <h2 style='color:#001f3f;'>{format_rp(plafon_maks)}</h2>
                <p>Bunga: <b>6% per tahun (KUR)</b></p>
                <p>Cicilan per bulan (2 Thn): <b>{format_rp(total_angsuran)}</b></p>
                <p style='color: {"green" if total_angsuran <= rpc_aman else "red"}; font-weight:bold;'>
                {'✅ CICILAN SEHAT' if total_angsuran <= rpc_aman else '⚠️ TERLALU BERAT'}
                </p>
            </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="white-card">
            <h4>📝 Cara Mengajukan KUR ke BRI</h4>
            <ol>
                <li><b>Siapkan Dokumen:</b> KTP, KK, NIB (Nomor Induk Berusaha), dan Laporan Keuangan dari aplikasi ini.</li>
                <li><b>Cetak Laporan:</b> Gunakan Tab "Laporan Keuangan" untuk bukti laba bersih ke Mantri BRI.</li>
                <li><b>Datangi Unit BRI:</b> Temui Mantri atau petugas KUR untuk menyerahkan berkas.</li>
                <li><b>Proses Survey:</b> Bank akan mengecek tempat usaha Anda. Pastikan catatan modal Anda sesuai.</li>
            </ol>
        </div>""", unsafe_allow_html=True)

# REVISI
with st.expander("🛠️ Perbaiki Data Salah"):
    df_rev = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id DESC", conn)
    if not df_rev.empty:
        target = st.selectbox("Pilih data:", [f"{r['id']} | {r['tanggal']}" for _, r in df_rev.iterrows()])
        if st.button("Hapus Data"):
            c.execute(f"DELETE FROM transaksi WHERE id = {int(target.split(' | ')[0])}")
            conn.commit()
            st.rerun()

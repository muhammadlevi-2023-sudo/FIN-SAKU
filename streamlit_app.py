import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR BRI", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_bri_final.db', check_same_thread=False)
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

# 2. UI CUSTOM: SUPER TAJAM & ANTI-NYARU
st.markdown("""
<style>
    /* Background Utama Navy UNAIR */
    .stApp { background-color: #003366 !important; }
    
    /* Paksa Sidebar Tetap Gelap */
    [data-testid="stSidebar"] { background-color: #002244 !important; border-right: 3px solid #FFD700; }

    /* CSS SAKTI: Kunci Font Dashboard Agar Sangat Terbaca */
    .dashboard-container {
        background-color: #ffffff !important;
        padding: 30px;
        border-radius: 20px;
        border-left: 15px solid #FFD700;
        margin-bottom: 30px;
        box-shadow: 0px 10px 20px rgba(0,0,0,0.3);
    }
    
    /* Paksa SEMUA teks di dalam kontainer putih menjadi Navy Gelap & Bold */
    .dashboard-container h3, .dashboard-container p, .dashboard-container li, 
    .dashboard-container b, .dashboard-container span, .dashboard-container div {
        color: #002244 !important;
        font-weight: 900 !important;
        opacity: 1 !important;
    }

    /* Styling Tabel Laporan agar Rapi */
    .report-table { width: 100%; border-collapse: collapse; }
    .report-table td { padding: 12px; border-bottom: 1px solid #ddd; color: #002244 !important; font-weight: bold; }
    .total-row { background-color: #FFD700; color: #002244 !important; font-size: 18px; }

    /* Style Tab agar Menyala */
    button[data-baseweb="tab"] p { color: #FFD700 !important; font-weight: 800 !important; font-size: 16px; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; border-radius: 10px 10px 0 0; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #003366 !important; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (LANGSUNG UPDATE) ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "Usaha Baru", key="f_nama")
    modal_raw = st.text_input("Modal Awal (Rp)", "0", key="f_modal")
    st.markdown(f"<small style='color:#FFD700;'>Tercatat: <b>{format_rp(clean_to_int(modal_raw))}</b></small>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Parameter Produk")
    hpp_raw = st.text_input("HPP/Produk", "5000")
    hrg_raw = st.text_input("Harga Jual/Produk", "15000")
    prive_pct = st.slider("Persentase Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Data KUR BRI: {nama_u}")

# Box Edukasi dengan Class CSS Baru
st.markdown(f"""
<div class="dashboard-container">
    <h3>🔍 Standar Kelayakan KUR BRI</h3>
    <p>Bank BRI menggunakan rumus <b>RPC (Repayment Capacity)</b> untuk menentukan apakah Anda bisa mencicil pinjaman:</p>
    <ul>
        <li><b>Batas Aman Cicilan:</b> Maksimal 35% dari Laba Bersih bulanan.</li>
        <li><b>Kedisiplinan Data:</b> Catatan harian membuktikan usaha Anda bukan 'usaha musiman'.</li>
        <li><b>Kesehatan Kas:</b> Modal awal {format_rp(clean_to_int(modal_raw))} harus terjaga agar operasional tidak terganggu.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# --- INPUT TRANSAKSI ---
col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Unit Terjual", min_value=0)
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if qty > 0:
            omzet = qty * clean_to_int(hrg_raw)
            laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
            prive = laba * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.rerun()

# --- LAPORAN & KUR ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_lap, t_kur = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS BANK BRI"])

    with t_lap:
        sel_b = st.selectbox("Pilih Bulan Laporan", df['bulan'].unique())
        sub_df = df[df['bulan'] == sel_b]
        
        o, l, p = sub_df['omzet'].sum(), sub_df['laba'].sum(), sub_df['prive'].sum()
        total_kas = clean_to_int(modal_raw) + (df['laba'].sum() - df['prive'].sum())
        
        st.markdown(f"""
        <div class="dashboard-container">
            <h3 style="text-align:center;">RINGKASAN BULAN: {sel_b}</h3>
            <table class="report-table">
                <tr><td>Total Penjualan (Omzet)</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih Usaha</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi Pribadi)</td><td style="text-align:right; color:#d9534f !important;">({format_rp(p)})</td></tr>
                <tr class="total-row">
                    <td><b>SALDO KAS AKHIR</b></td><td style="text-align:right;"><b>{format_rp(total_kas)}</b></td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        rpc = avg_laba * 0.35 
        plafon_est = rpc * 22  # Simulasi tenor 2 tahun (pembagi bunga & margin bank)
        
        st.markdown(f"""
        <div class="dashboard-container">
            <h3>🏦 Simulasi Kredit BRI</h3>
            <p>Rata-rata Laba Bersih: <b>{format_rp(avg_laba)} /bulan</b></p>
            <p>Kemampuan Bayar Cicilan (RPC 35%): <b style="color:#008000;">{format_rp(rpc)} /bulan</b></p>
            <hr>
            <p>Estimasi Plafon Pinjaman:</p>
            <h1 style="color:#002244;">{format_rp(plafon_est)}</h1>
        </div>
        """, unsafe_allow_html=True)

        if plafon_est >= 5000000:
            st.success("✅ STATUS: BANKABLE! Profil Anda layak mengajukan KUR BRI Mikro.")
        else:
            st.error("⚠️ STATUS: BELUM LAYAK KUR")
            kurang = 5000000 - plafon_est
            target_tambah = (kurang / 22) / 0.35
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px;">
                <p>Pinjaman minimal BRI adalah Rp 5.000.000.</p>
                <p>Anda butuh tambahan plafon sebesar <b>{format_rp(kurang)}</b>.</p>
                <p>💡 <b>Target:</b> Tingkatkan Laba Bersih Anda sebesar <b>{format_rp(target_tambah)}</b> per bulan agar lolos kriteria.</p>
            </div>
            """, unsafe_allow_html=True)

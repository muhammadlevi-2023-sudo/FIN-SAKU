import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_multi_mode.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, tipe_input TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: DARK NAVY & GOLD (ULTRA CONTRAST)
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }

    /* CONTAINER DASHBOARD PUTIH - KONTRAST TINGGI */
    .white-card {
        background-color: #ffffff !important;
        padding: 25px;
        border-radius: 15px;
        border-left: 10px solid #FFD700;
        margin-bottom: 20px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    /* PAKSA SEMUA TEKS DI DALAM CARD PUTIH MENJADI HITAM PEKAT */
    .white-card *, .white-card p, .white-card b, .white-card td, .white-card h3 {
        color: #000000 !important;
        font-weight: 800 !important;
    }

    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 2px solid #FFD700; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
    
    /* Tabel Styling */
    .report-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .report-table td { padding: 10px; border-bottom: 1px solid #eee; }
    .highlight-row { background-color: #fff9c4; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: MODAL & PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal = st.text_input("Uang Kas Awal (Modal Usaha)", "1000000")
    st.markdown(f"Tercatat: **{format_rp(clean_to_int(modal_awal))}**")
    
    st.write("---")
    st.subheader("⚙️ Aturan Keuangan")
    prive_pct = st.slider("Jatah Uang Pribadi (%)", 0, 100, 30, help="Persentase laba yang Anda ambil untuk keperluan pribadi/rumah tangga")
    st.info("BRI lebih suka jika Prive di bawah 50% agar usaha tetap punya napas modal.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")

# PILIHAN MODE CATAT
mode = st.radio("Pilih Cara Mencatat Hari Ini:", ["Satuan (Per Produk)", "Totalan (Langsung Sehari)"], horizontal=True)

col_input, col_edu = st.columns([1, 1.2])

with col_input:
    st.markdown('<div class="white-card">', unsafe_allow_html=True)
    st.subheader("📝 Form Input")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    
    if mode == "Satuan (Per Produk)":
        hrg = st.number_input("Harga Jual Satuan", min_value=0, step=1000)
        hpp = st.number_input("Modal (HPP) Satuan", min_value=0, step=1000)
        qty = st.number_input("Jumlah Terjual", min_value=1)
        omzet = hrg * qty
        laba = (hrg - hpp) * qty
    else:
        omzet = st.number_input("Total Omzet Sehari", min_value=0, step=1000)
        margin_pct = st.slider("Estimasi Margin Laba (%)", 5, 100, 30)
        laba = omzet * (margin_pct / 100)
    
    prive = laba * (prive_pct / 100)
    
    if st.button("🔔 SIMPAN KE LAPORAN"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, tipe_input) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, mode))
            conn.commit()
            st.success("Berhasil dicatat!")
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_edu:
    st.markdown(f"""
    <div class="white-card">
        <h3>💡 Pemisahan Uang (Bankability)</h3>
        <p>Agar layak KUR, Bank BRI melihat kedisiplinan Anda memisahkan uang:</p>
        <table class="report-table">
            <tr><td><b>Uang Kas Usaha</b></td><td>Simpan di rekening/wadah terpisah untuk operasional.</td></tr>
            <tr><td><b>Uang Prive</b></td><td>Inilah "Gaji" Anda. Hanya ini yang boleh dipakai jajan.</td></tr>
        </table>
        <p style="margin-top:10px;">Status saat ini: <b>{prive_pct}% Laba</b> dialokasikan untuk pribadi.</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN KEUANGAN LENGKAP ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR BRI"])

    def render_report(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        kas_bersih = l - p
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">{title}</h3>
            <table class="report-table">
                <tr><td>Total Penjualan (Omzet)</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih Kotor</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Diambil Pribadi (Prive)</td><td style="text-align:right; color:red !important;">({format_rp(p)})</td></tr>
                <tr class="highlight-row">
                    <td><b>Penambahan Kas Usaha</b></td><td style="text-align:right;"><b>{format_rp(kas_bersih)}</b></td>
                </tr>
            </table>
            <p style="font-size:0.8em; color:gray !important; margin-top:5px;">*Kas bersih adalah uang yang benar-benar tinggal di dalam usaha Anda.</p>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Pilih Hari", datetime.now())
        render_report(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan {sel_t.strftime('%d %B %Y')}")
    
    with t_min:
        sel_m = st.selectbox("Pilih Minggu", df['minggu'].unique())
        render_report(df[df['minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        render_report(df[df['bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        # LOGIKA KUR BRI
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        # RPC BRI standar: 35% dari laba bersih
        rpc = avg_laba * 0.35
        # Plafon tenor 24 bulan
        plafon_est = rpc * 22 
        
        st.subheader("🏦 Analisis Kelayakan KUR BRI")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Rata-rata Laba/Bulan", format_rp(avg_laba))
        with col2:
            st.metric("Batas Cicilan Aman (RPC)", format_rp(rpc))

        st.markdown(f"""
        <div class="white-card">
            <p>Berdasarkan performa keuangan, estimasi plafon KUR yang bisa Anda ajukan:</p>
            <h1 style="text-align:center; font-size:45px;">{format_rp(plafon_est)}</h1>
        </div>
        """, unsafe_allow_html=True)

        if plafon_est >= 5000000:
            st.success("✅ LAYAK KUR: Data Anda menunjukkan kapasitas bayar yang kuat untuk plafon minimal BRI.")
        else:
            st.error("⚠️ BELUM LAYAK: Plafon Anda masih di bawah Rp 5 Juta.")
            kekurangan = 5000000 - plafon_est
            st.markdown(f"""
            <div style="background:rgba(255,0,0,0.1); padding:15px; border-radius:10px;">
                <p><b>Analisis:</b> Anda butuh tambahan laba bersih sekitar <b>{format_rp((kekurangan/22)/0.35)} /bulan</b> agar layak mendapatkan pinjaman minimal BRI.</p>
                <p>💡 Tips: Kurangi jatah Prive atau tingkatkan omzet harian Anda.</p>
            </div>
            """, unsafe_allow_html=True)

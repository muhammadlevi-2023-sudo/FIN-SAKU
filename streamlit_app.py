import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_bri_v6.db', check_same_thread=False)
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

# 2. UI CUSTOM: UNAIR NAVY & GOLD
st.markdown("""
<style>
    .stApp { background-color: #003366 !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2 {
        color: #ffffff !important;
    }

    /* KUNCI TEKS DASHBOARD (BOX PUTIH) */
    .edu-box, .report-card { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; 
        margin-bottom: 25px;
    }
    .edu-box *, .report-card *, .report-card td, .report-card b, .report-card h3 { 
        color: #003366 !important; 
        font-weight: bold !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] { background-color: #002244 !important; border-right: 3px solid #FFD700; }
    button[data-baseweb="tab"] p { color: #FFD700 !important; font-weight: 800 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #FFD700 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #003366 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "Usaha Binaan BRI", key="f_nama")
    modal_raw = st.text_input("Modal Awal (Rp)", "0", key="f_modal")
    st.markdown(f"<small>Tercatat: <b>{format_rp(clean_to_int(modal_raw))}</b></small>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Parameter Produk")
    hpp_raw = st.text_input("HPP/Produk", "5000")
    hrg_raw = st.text_input("Harga Jual/Produk", "15000")
    prive_pct = st.slider("Persentase Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Data KUR BRI: {nama_u}")

st.markdown("""<div class="edu-box">
    <h3>🔍 Standar Bankable KUR BRI</h3>
    <p>Agar pengajuan KUR Anda disetujui oleh analis BRI, pastikan data Anda memenuhi syarat <b>RPC (Repayment Capacity)</b>:</p>
    <ul>
        <li><b>Cicilan Aman:</b> Maksimal 30% - 40% dari rata-rata Laba Bersih bulanan Anda.</li>
        <li><b>Kontinuitas:</b> Pencatatan transaksi harus dilakukan rutin setiap hari untuk membuktikan usaha berjalan.</li>
        <li><b>Kesehatan Modal:</b> Laba bersih tidak boleh habis seluruhnya untuk Prive (kepentingan pribadi).</li>
    </ul>
</div>""", unsafe_allow_html=True)

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

# --- LAPORAN KEUANGAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_bul, t_kur = st.tabs(["📆 HARIAN", "🗓️ BULANAN", "🏦 ANALISIS KUR BRI"])

    def show_report(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        total_kas = clean_to_int(modal_raw) + (df['laba'].sum() - df['prive'].sum())
        st.markdown(f"""<div class="report-card">
            <h3 style="text-align:center;">{title}</h3>
            <table style="width:100%;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi)</td><td style="text-align:right; color:#ff4b4b !important;">({format_rp(p)})</td></tr>
                <tr style="background:#FFD700;">
                    <td style="padding:10px;">SALDO KAS (POSISI KEUANGAN)</td><td style="text-align:right;">{format_rp(total_kas)}</td>
                </tr>
            </table>
        </div>""", unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Filter Hari", datetime.now(), key="filter_h")
        show_report(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan {sel_t.strftime('%d/%b/%Y')}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        show_report(df[df['bulan'] == sel_b], f"Laporan Bulanan: {sel_b}")

    with t_kur:
        # LOGIKA PERHITUNGAN KUR BRI
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        # RPC (Repayment Capacity) 35% adalah standar umum perbankan mikro
        rpc = avg_laba * 0.35 
        # Plafon estimasi tenor 24 bulan (2 tahun)
        plafon_est = rpc * 22  
        
        st.subheader("🏦 Kalkulator Layak KUR BRI")
        
        st.markdown(f"""<div class="report-card" style="border: 2px solid #FFD700;">
            <p>Berdasarkan rata-rata laba bulanan Anda ({format_rp(avg_laba)}), BRI mengestimasi:</p>
            <h3 style="margin:0;">Kemampuan Cicilan: <span style="color:#008000;">{format_rp(rpc)}/bulan</span></h3>
            <h2 style="margin:10px 0;">Estimasi Plafon: {format_rp(plafon_est)}</h2>
        </div>""", unsafe_allow_html=True)

        if plafon_est >= 5000000:
            st.success("✅ STATUS: BANKABLE (LAYAK KUR BRI)")
            st.write("Selamat! Profil keuangan Anda sudah memenuhi syarat plafon minimal BRI.")
        else:
            st.error("⚠️ STATUS: BELUM LAYAK (DI BAWAH PLAFON MINIMAL)")
            kekurangan_laba = ((5000000 / 22) / 0.35) - avg_laba
            st.markdown(f"""<div style="background:rgba(255,255,255,0.1); padding:15px; border-radius:10px;">
                <p>Pinjaman minimal KUR BRI adalah <b>Rp 5.000.000</b>.</p>
                <p><b>Analisis:</b> Laba bersih bulanan Anda saat ini belum cukup kuat untuk menjamin cicilan minimal.</p>
                <hr>
                <p>💡 <b>Cara agar Bankable:</b> Tingkatkan laba bersih rata-rata sebesar <b>{format_rp(kekurangan_laba)}</b> lagi per bulan dengan menambah volume penjualan atau menekan biaya operasional.</p>
            </div>""", unsafe_allow_html=True)

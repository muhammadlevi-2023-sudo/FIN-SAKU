import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali UMKM Pro", layout="wide")

# --- DATABASE ENGINE & AUTO-MIGRATION ---
conn = sqlite3.connect('finsaku_pro_v2.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, tahun TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')

# Migrasi: Tambah kolom tahun jika user pakai database lama
try:
    c.execute("SELECT tahun FROM transaksi LIMIT 1")
except:
    c.execute("ALTER TABLE transaksi ADD COLUMN tahun TEXT")
    conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        val = float(angka)
        formatted = "{:,.0f}".format(abs(val)).replace(",", ".")
        return f"Rp {'-' if val < 0 else ''}{formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# --- UI DESIGN (PREMIUM NAVY) ---
st.markdown("""
<style>
    .stApp { background-color: #0a192f !important; color: #e6f1ff !important; }
    [data-testid="stSidebar"] { background-color: #112240 !important; border-right: 2px solid #64ffda; }
    .report-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 25px; border-radius: 15px; border: 1px solid #64ffda;
        margin-bottom: 20px; box-shadow: 0 10px 30px -15px rgba(2,12,27,0.7);
    }
    .metric-val { color: #64ffda; font-size: 24px; font-weight: bold; }
    .stButton>button { 
        background-color: #64ffda !important; color: #0a192f !important; 
        font-weight: bold; border-radius: 5px; transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(100,255,218,0.4); }
    h1, h2, h3 { color: #ccd6f6 !important; }
    table { width: 100%; border-collapse: collapse; color: #ccd6f6; }
    td { padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#64ffda;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal = clean_to_int(st.text_input("Uang Kas Awal", "7000000"))
    
    # Hitung Modal Realtime
    total_laba = df['laba'].sum() if not df.empty else 0
    total_prive = df['prive'].sum() if not df.empty else 0
    kas_skrg = m_awal + total_laba - total_prive
    
    st.markdown(f"---")
    st.markdown(f"Kas Saat Ini:<br><span class='metric-val'>{format_rp(kas_skrg)}</span>", unsafe_allow_html=True)
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    p_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- INPUT SECTION ---
st.title(f"Dashboard: {nama_u}")
col_in, col_st = st.columns([1.5, 1])

with col_in:
    st.subheader("📝 Pencatatan Baru")
    c1, c2 = st.columns(2)
    with c1:
        tgl_pilih = st.date_input("Tanggal Transaksi", datetime.now())
        v_bln = tgl_pilih.strftime("%B")
        v_thn = tgl_pilih.strftime("%Y")
    with c2:
        omzet_in = st.number_input("Total Omzet (Pendapatan)", min_value=0, step=50000)
    
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    prive_in = laba_in * (p_pct / 100) if laba_in > 0 else 0

    if st.button("🚀 SIMPAN DATA KE SISTEM"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, tahun, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?,?)",
                  (tgl_pilih.strftime("%Y-%m-%d"), v_bln, v_thn, f"W-{(tgl_pilih.day-1)//7+1}", omzet_in, laba_in, prive_in, "Manual"))
        conn.commit()
        st.success("Transaksi Berhasil Dicatat!")
        st.rerun()

with col_st:
    st.markdown(f"""<div class="report-card">
        <h3 style='color:#64ffda; margin-top:0;'>Ringkasan Input</h3>
        <table>
            <tr><td>Bulan</td><td align="right">{v_bln} {v_thn}</td></tr>
            <tr><td>Estimasi Laba</td><td align="right">{format_rp(laba_in)}</td></tr>
            <tr><td>Potongan Prive</td><td align="right">{format_rp(prive_in)}</td></tr>
        </table>
    </div>""", unsafe_allow_html=True)

# --- LAPORAN KEUANGAN FORMAL ---
if not df.empty:
    st.markdown("---")
    tab1, tab2 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS BANKABILITY"])
    
    with tab1:
        # Filter Tahun & Bulan
        f1, f2 = st.columns(2)
        with f1: sel_thn = st.selectbox("Pilih Tahun:", sorted(df['tahun'].unique(), reverse=True))
        with f2: sel_bln = st.selectbox("Pilih Bulan:", df[df['tahun']==sel_thn]['bulan'].unique())
        
        curr_df = df[(df['tahun']==sel_thn) & (df['bulan']==sel_bln)]
        
        # Perhitungan Akuntansi
        o_sum = curr_df['omzet'].sum()
        l_sum = curr_df['laba'].sum()
        p_sum = curr_df['prive'].sum()
        
        # Cari Modal Awal Bulan Ini (akumulasi semua bulan sebelum bulan terpilih)
        # Sederhananya: Total Laba/Prive sebelum tanggal 1 bulan terpilih
        first_date = datetime.strptime(f"01 {sel_bln} {sel_thn}", "%d %B %Y").strftime("%Y-%m-%d")
        past_df = df[df['tanggal'] < first_date]
        m_awal_bulan = m_awal + past_df['laba'].sum() - past_df['prive'].sum()
        m_akhir_bulan = m_awal_bulan + l_sum - p_sum

        rep1, rep2 = st.columns(2)
        with rep1:
            st.markdown(f"""<div class="report-card">
                <h3 style='text-align:center;'>LABA RUGI<br><small>{sel_bln} {sel_thn}</small></h3>
                <table>
                    <tr><td>Total Pendapatan</td><td align="right">{format_rp(o_sum)}</td></tr>
                    <tr style="color:#ff4b4b;"><td>Harga Pokok Penjualan (HPP)</td><td align="right">({format_rp(o_sum - l_sum)})</td></tr>
                    <tr style="font-weight:bold; color:#64ffda; border-top:2px solid #64ffda;">
                        <td>LABA BERSIH</td><td align="right">{format_rp(l_sum)}</td>
                    </tr>
                </table>
            </div>""", unsafe_allow_html=True)
            
        with rep2:
            st.markdown(f"""<div class="report-card">
                <h3 style='text-align:center;'>PERUBAHAN MODAL<br><small>{sel_bln} {sel_thn}</small></h3>
                <table>
                    <tr><td>Modal Awal (1 {sel_bln})</td><td align="right">{format_rp(m_awal_bulan)}</td></tr>
                    <tr><td>Penambahan Laba Bersih</td><td align="right">{format_rp(l_sum)}</td></tr>
                    <tr style="color:#ff4b4b;"><td>Pengambilan Pribadi (Prive)</td><td align="right">({format_rp(p_sum)})</td></tr>
                    <tr style="font-weight:bold; color:#64ffda; border-top:2px solid #64ffda;">
                        <td>MODAL AKHIR</td><td align="right">{format_rp(m_akhir_bulan)}</td>
                    </tr>
                </table>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.subheader("🏦 Skor Kelayakan Bank (KUR)")
        # Hitung DSCR (Debt Service Coverage Ratio)
        # Bank biasanya mau angsuran maks 30-40% dari laba
        dscr_limit = l_sum * 0.4
        
        c_a, c_b = st.columns(2)
        with c_a:
            st.markdown(f"""<div class="report-card">
                <h4>Kapasitas Angsuran Aman</h4>
                <p class="metric-val">{format_rp(dscr_limit)} / bulan</p>
                <small>*Ini adalah nilai cicilan maksimal agar usaha tetap sehat.</small>
            </div>""", unsafe_allow_html=True)
        
        with c_b:
            status_kur = "SANGAT LAYAK" if l_sum > 2000000 and len(df['bulan'].unique()) >= 6 else "PERLU EVALUASI"
            st.markdown(f"""<div class="report-card">
                <h4>Prediksi Persetujuan Bank</h4>
                <p class="metric-val">{status_kur}</p>
                <small>Berdasarkan riwayat {len(df['bulan'].unique())} bulan data.</small>
            </div>""", unsafe_allow_html=True)

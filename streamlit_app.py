import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# Pastikan fpdf diimpor dengan aman
try:
    from fpdf import FPDF
except ImportError:
    st.error("Library 'fpdf' tidak ditemukan. Pastikan sudah ada di requirements.txt")

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali UMKM Pro", layout="wide")

# --- DATABASE ENGINE (Ganti nama file agar fresh) ---
conn = sqlite3.connect('finsaku_v3_core.db', check_same_thread=False)
c = conn.cursor()

# Buat tabel dengan struktur lengkap dari awal
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, tahun TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
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

# --- UI DESIGN (MODERN DARK MODE) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #161b22 !important; border-right: 1px solid #30363d; }
    .report-card {
        background: #1c2128; padding: 20px; border-radius: 12px;
        border: 1px solid #30363d; margin-bottom: 20px;
    }
    .metric-gold { color: #ffca28; font-size: 28px; font-weight: bold; }
    .stButton>button { 
        background-color: #ffca28 !important; color: #000000 !important; 
        font-weight: bold; width: 100%; border-radius: 8px; border: none;
    }
    table { width: 100%; border-collapse: collapse; }
    td { padding: 12px 8px; border-bottom: 1px solid #30363d; }
    .label-bank { color: #8b949e; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#ffca28; text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal = clean_to_int(st.text_input("Modal Awal (Cash)", "7000000"))
    
    total_laba = df['laba'].sum() if not df.empty else 0
    total_prive = df['prive'].sum() if not df.empty else 0
    kas_skrg = m_awal + total_laba - total_prive
    
    st.write("---")
    st.markdown(f"Saldo Kas Saat Ini:")
    st.markdown(f"<span class='metric-gold'>{format_rp(kas_skrg)}</span>", unsafe_allow_html=True)
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    p_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- INPUT SECTION ---
st.title(f"Dashboard Keuangan: {nama_u}")
col_in, col_st = st.columns([1.5, 1])

with col_in:
    st.subheader("📝 Catat Penjualan")
    c1, c2 = st.columns(2)
    with c1:
        tgl_pilih = st.date_input("Pilih Tanggal", datetime.now())
        v_bln, v_thn = tgl_pilih.strftime("%B"), tgl_pilih.strftime("%Y")
    with c2:
        omzet_in = st.number_input("Total Pendapatan (Omzet)", min_value=0, step=10000)
    
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    prive_in = laba_in * (p_pct / 100) if laba_in > 0 else 0

    if st.button("💾 SIMPAN TRANSAKSI"):
        if omzet_in > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, tahun, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?,?)",
                      (tgl_pilih.strftime("%Y-%m-%d"), v_bln, v_thn, f"W-{(tgl_pilih.day-1)//7+1}", omzet_in, laba_in, prive_in, "Manual"))
            conn.commit()
            st.success("Berhasil disimpan!")
            st.rerun()

with col_st:
    st.markdown(f"""<div class="report-card">
        <h4 style='margin-top:0;'>Analisis Transaksi</h4>
        <table>
            <tr><td class="label-bank">Periode</td><td align="right">{v_bln} {v_thn}</td></tr>
            <tr><td class="label-bank">Laba Bersih</td><td align="right" style="color:#4cd964;">{format_rp(laba_in)}</td></tr>
            <tr><td class="label-bank">Prive</td><td align="right" style="color:#ff3b30;">{format_rp(prive_in)}</td></tr>
        </table>
    </div>""", unsafe_allow_html=True)

# --- LAPORAN UNTUK BANK ---
if not df.empty:
    st.write("---")
    tab1, tab2 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KREDIT"])
    
    with tab1:
        # Filter Tahun & Bulan yang cerdas
        f1, f2 = st.columns(2)
        with f1: 
            years = sorted(df['tahun'].unique(), reverse=True)
            sel_thn = st.selectbox("Tahun", years)
        with f2: 
            months = df[df['tahun']==sel_thn]['bulan'].unique()
            sel_bln = st.selectbox("Bulan", months)
        
        curr_df = df[(df['tahun']==sel_thn) & (df['bulan']==sel_bln)]
        o_sum, l_sum, p_sum = curr_df['omzet'].sum(), curr_df['laba'].sum(), curr_df['prive'].sum()
        
        # Logika Modal Awal Dinamis
        first_date = datetime.strptime(f"01 {sel_bln} {sel_thn}", "%d %B %Y").strftime("%Y-%m-%d")
        past_df = df[df['tanggal'] < first_date]
        m_awal_bln = m_awal + past_df['laba'].sum() - past_df['prive'].sum()
        m_akhir_bln = m_awal_bln + l_sum - p_sum

        rep1, rep2 = st.columns(2)
        with rep1:
            st.markdown(f"""<div class="report-card">
                <h4 style='text-align:center;'>LABA RUGI</h4>
                <p style='text-align:center; font-size:12px; color:#8b949e;'>Periode: {sel_bln} {sel_thn}</p>
                <table>
                    <tr><td>Pendapatan Usaha</td><td align="right">{format_rp(o_sum)}</td></tr>
                    <tr><td>Beban HPP</td><td align="right">({format_rp(o_sum - l_sum)})</td></tr>
                    <tr style="font-weight:bold; color:#ffca28;"><td style="border:none;">LABA BERSIH</td><td align="right" style="border:none;">{format_rp(l_sum)}</td></tr>
                </table>
            </div>""", unsafe_allow_html=True)
            
        with rep2:
            st.markdown(f"""<div class="report-card">
                <h4 style='text-align:center;'>PERUBAHAN MODAL</h4>
                <p style='text-align:center; font-size:12px; color:#8b949e;'>Periode: {sel_bln} {sel_thn}</p>
                <table>
                    <tr><td>Modal Awal</td><td align="right">{format_rp(m_awal_bln)}</td></tr>
                    <tr><td>Laba Periode</td><td align="right">{format_rp(l_sum)}</td></tr>
                    <tr><td>Prive</td><td align="right">({format_rp(p_sum)})</td></tr>
                    <tr style="font-weight:bold; color:#ffca28;"><td style="border:none;">MODAL AKHIR</td><td align="right" style="border:none;">{format_rp(m_akhir_bln)}</td></tr>
                </table>
            </div>""", unsafe_allow_html=True)

    with tab2:
        st.subheader("🏦 Skor Kelayakan Kredit")
        # Analisis Kemampuan Bayar (DSCR Sederhana)
        cicilan_maks = l_sum * 0.35
        
        c_k1, c_k2 = st.columns(2)
        with c_k1:
            st.info(f"**Batas Aman Angsuran:**\n\n{format_rp(cicilan_maks)} / bulan")
            st.caption("Bank biasanya menyetujui pinjaman jika angsuran maksimal 35% dari laba bersih.")
        with c_k2:
            layak = "LAYAK" if l_sum > 1000000 else "EVALUASI"
            st.success(f"**Status Bankability:**\n\n{layak}")
            st.caption(f"Berdasarkan performa bulan {sel_bln}.")

else:
    st.info("Belum ada data transaksi. Silakan masukkan data pertama Anda di atas.")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- DATABASE SETUP ---
conn = sqlite3.connect('finsaku_v11_pro.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, 
              omzet REAL, laba REAL, prive REAL, tipe_catat TEXT)''')
conn.commit()

def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

# --- UI CSS CUSTOM ---
st.markdown("""
<style>
    .stApp { background-color: #001f3f; }
    
    /* Segmented Control / Modern Selector */
    .stSelectbox div[data-baseweb="select"] {
        border-radius: 10px; border: 2px solid #FFD700;
    }
    
    /* Container Laporan */
    .report-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        color: #333 !important; border-left: 10px solid #FFD700;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
        margin-top: 20px;
    }
    .report-card h3, .report-card b, .report-card p { color: #333 !important; }

    /* Modern Card Radio Replacement */
    div[data-testid="stHorizontalBlock"] > div:hover {
        transform: translateY(-5px);
        transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal = st.number_input("Kas Awal (Modal)", value=7000000)
    st.write("---")
    hpp = st.number_input("HPP Satuan", value=5000)
    hrg = st.number_input("Harga Jual", value=15000)
    margin_pct = ((hrg - hpp) / hrg) if hrg > 0 else 0
    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 30)

# --- DASHBOARD ---
st.title(f"Dashboard: {nama_u}")

# --- PENYUSUNAN METODE CATAT MODERN ---
st.subheader("📝 Pilih Metode Pencatatan")
col1, col2, col3 = st.columns(3)

# Simpan pilihan di session state
if 'metode' not in st.session_state:
    st.session_state.metode = "Harian"

with col1:
    if st.button("📅 HARIAN", use_container_width=True):
        st.session_state.metode = "Harian"
with col2:
    if st.button("📅 MINGGUAN", use_container_width=True):
        st.session_state.metode = "Mingguan"
with col3:
    if st.button("📅 BULANAN", use_container_width=True):
        st.session_state.metode = "Bulanan"

st.markdown(f"Metode Aktif: **{st.session_state.metode}**")

# Input Form
with st.container():
    c_a, c_b = st.columns(2)
    tgl = c_a.date_input("Tanggal Transaksi")
    omzet_in = c_b.number_input(f"Total Omzet ({st.session_state.metode})", min_value=0)
    
    if st.button("🚀 SIMPAN TRANSAKSI KE SISTEM", use_container_width=True):
        l_in = omzet_in * margin_pct
        p_in = l_in * (prive_pct / 100)
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, tipe_catat) VALUES (?,?,?,?,?,?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet_in, l_in, p_in, st.session_state.metode))
        conn.commit()
        st.toast("Data Berhasil Dicatat!", icon="✅")
        st.rerun()

# --- LOGIKA AKUNTANSI & KUR ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    tab_lap, tab_kur = st.tabs(["📊 LAPORAN MODERN", "🏦 ANALISIS KUR BRI"])

    with tab_lap:
        list_b = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Periode Laporan:", list_b, index=len(list_b)-1)
        
        # Perhitungan Akuntansi
        df_b = df[df['bulan'] == sel_b]
        o_tot = df_b['omzet'].sum()
        l_op = df_b['laba'].sum()
        p_tot = df_b['prive'].sum()
        laba_bersih = l_op - p_tot
        
        # Kas Flow
        idx = list_b.index(sel_b)
        l_lalu = df[df['bulan'].isin(list_b[:idx])]['laba'].sum()
        p_lalu = df[df['bulan'].isin(list_b[:idx])]['prive'].sum()
        kas_awal = m_awal + l_lalu - p_lalu
        kas_akhir = kas_awal + laba_bersih

        st.markdown(f"""
        <div class="report-card">
            <h2 style="text-align:center;">LAPORAN LABA RUGI & KAS</h2>
            <p style="text-align:center;">Periode: {sel_b}</p>
            <hr>
            <table style="width:100%; font-size: 1.1rem;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o_tot)}</td></tr>
                <tr><td>Laba Operasional</td><td style="text-align:right; color:green;">{format_rp(l_op)}</td></tr>
                <tr><td>Prive (Gaji Pemilik)</td><td style="text-align:right; color:red;">-{format_rp(p_tot)}</td></tr>
                <tr style="border-top: 2px solid #333; font-weight:bold;">
                    <td>LABA BERSIH (Sisa)</td><td style="text-align:right;">{format_rp(laba_bersih)}</td>
                </tr>
            </table>
            <br>
            <div style="background:#00152b; color:white; padding:15px; border-radius:10px;">
                <div style="display:flex; justify-content:space-between;">
                    <span>SALDO KAS AWAL</span><span>{format_rp(kas_awal)}</span>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:1.3rem; color:#FFD700; font-weight:bold; margin-top:10px;">
                    <span>SALDO KAS AKHIR</span><span>{format_rp(kas_akhir)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with tab_kur:
        st.subheader("🏦 Skor Kredit & Simulasi")
        
        # OTAK KUR FIX: Cicilan tidak boleh > 35% Laba Bersih
        limit_aman = laba_bersih * 0.35
        
        c1, c2 = st.columns(2)
        with c1:
            plafon = st.selectbox("Plafon KUR", [10000000, 25000000, 50000000])
            tenor = st.slider("Tenor (Bulan)", 12, 36, 12)
            cicilan = (plafon / tenor) + (plafon * 0.005) # Bunga 6% per tahun (0.5% per bulan)
            
        with c2:
            st.write(f"Estimasi Cicilan: **{format_rp(cicilan)}/bln**")
            st.write(f"Batas Aman Bank: **{format_rp(limit_aman)}/bln**")
            
            if cicilan > laba_bersih:
                st.error("### ❌ STATUS: TIDAK LAYAK")
                st.caption("Cicilan memakan seluruh laba bersih. Sangat berisiko.")
            elif cicilan > limit_aman:
                st.warning("### ⚠️ STATUS: RISIKO TINGGI")
                st.caption("Cicilan melebihi 35% laba. Bank mungkin akan ragu.")
            else:
                st.success("### ✅ STATUS: SANGAT LAYAK")
                st.caption("Arus kas sangat aman untuk plafon ini.")

        sisa_akhir = laba_bersih - cicilan
        persen_sisa = (sisa_akhir / laba_bersih * 100) if laba_bersih > 0 else 0
        
        st.metric("Sisa Laba Setelah Cicilan", format_rp(sisa_akhir), f"{persen_sisa:.1f}%")

else:
    st.info("Silakan masukkan transaksi pertama Anda.")

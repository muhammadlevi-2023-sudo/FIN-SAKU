import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF

# --- DATABASE FIX ---
conn = sqlite3.connect('finsaku_v10_fix.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
conn.commit()

def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

# --- UI PREMIUM REFINEMENT ---
st.markdown("""
<style>
    .report-container {
        background: #ffffff; padding: 30px; border-radius: 20px;
        color: #1e1e1e !important; border-top: 10px solid #FFD700;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .metric-card {
        background: #f1f3f5; padding: 15px; border-radius: 12px;
        text-align: center; border: 1px solid #dee2e6;
    }
    .stat-val { font-size: 1.4rem; font-weight: bold; color: #001f3f; }
    .stat-label { font-size: 0.8rem; color: #666; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR & LOGIKA MARGIN ---
with st.sidebar:
    st.title("💰 FIN-Saku Pro")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal = st.number_input("Modal Awal (Uang di Tangan)", value=7000000)
    
    st.write("---")
    hpp = st.number_input("HPP Satuan", value=5000)
    hrg = st.number_input("Harga Jual", value=15000)
    margin_pct = ((hrg - hpp) / hrg) if hrg > 0 else 0
    prive_pct = st.slider("Jatah Prive Pemilik (%)", 0, 100, 30)

# --- INPUT DATA ---
with st.expander("📝 CATAT TRANSAKSI", expanded=True):
    col_a, col_b, col_c = st.columns(3)
    tgl = col_a.date_input("Tanggal")
    omzet_in = col_b.number_input("Omzet Hari Ini", min_value=0)
    if col_c.button("SIMPAN KE SISTEM", use_container_width=True):
        laba_in = omzet_in * margin_pct
        prive_in = laba_in * (prive_pct / 100)
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive) VALUES (?,?,?,?,?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet_in, laba_in, prive_in))
        conn.commit()
        st.rerun()

# --- PROSES DATA & LAPORAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    list_bulan = df['bulan'].unique().tolist()
    sel_b = st.selectbox("Pilih Periode Laporan", list_bulan, index=len(list_bulan)-1)
    
    # Perhitungan Akuntansi yang Benar
    df_curr = df[df['bulan'] == sel_b]
    o_tot = df_curr['omzet'].sum()
    l_tot = df_curr['laba'].sum()
    p_tot = df_curr['prive'].sum()
    laba_bersih_akhir = l_tot - p_tot # Laba setelah gaji pemilik
    
    # Hitung Kas Berjalan
    idx = list_bulan.index(sel_b)
    laba_akum = df[df['bulan'].isin(list_bulan[:idx])]['laba'].sum()
    prive_akum = df[df['bulan'].isin(list_bulan[:idx])]['prive'].sum()
    kas_awal_bulan = m_awal + laba_akum - prive_akum
    kas_akhir_bulan = kas_awal_bulan + laba_bersih_akhir

    # UI LAPORAN WEB (GLOW UP)
    st.markdown(f"""
    <div class="report-container">
        <h2 style="text-align:center; color:#001f3f;">LAPORAN KEUANGAN: {sel_b.upper()}</h2>
        <p style="text-align:center; color:#666;">{nama_u}</p>
        <hr>
        <div style="display: flex; gap: 15px; margin-bottom:20px;">
            <div class="metric-card" style="flex:1;">
                <div class="stat-label">TOTAL OMZET</div>
                <div class="stat-val">{format_rp(o_tot)}</div>
            </div>
            <div class="metric-card" style="flex:1;">
                <div class="stat-label">LABA OPERASIONAL</div>
                <div class="stat-val" style="color:green;">{format_rp(l_tot)}</div>
            </div>
            <div class="metric-card" style="flex:1;">
                <div class="stat-label">GAJI PEMILIK (PRIVE)</div>
                <div class="stat-val" style="color:red;">-{format_rp(p_tot)}</div>
            </div>
        </div>
        <div style="background:#001f3f; color:white; padding:20px; border-radius:12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
                <small>SALDO KAS AKHIR</small><br>
                <b style="font-size:1.8rem; color:#FFD700;">{format_rp(kas_akhir_bulan)}</b>
            </div>
            <div style="text-align:right;">
                <small>KAS AWAL: {format_rp(kas_awal_bulan)}</small><br>
                <small>PERTUMBUHAN: {((kas_akhir_bulan-kas_awal_bulan)/kas_awal_bulan*100):.1f}%</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- OTAK KUR YANG DIPERBAIKI ---
    st.write("---")
    st.subheader("🏦 Analisis Kelayakan KUR (Bank Standard)")
    
    # Logika Bank: Cicilan aman maksimal 30% dari Laba setelah Prive
    kemampuan_bayar = laba_bersih_akhir * 0.30
    
    col1, col2 = st.columns(2)
    with col1:
        plafon_req = st.select_slider("Ajukan Plafon Pinjaman:", options=[10000000, 25000000, 50000000, 100000000])
        tenor = st.slider("Tenor (Bulan)", 12, 36, 12)
        cicilan_per_bulan = (plafon_req / tenor) + (plafon_req * 0.06 / 12) # Bunga KUR 6%
    
    with col2:
        sisa_setelah_cicilan = laba_bersih_akhir - cicilan_per_bulan
        
        if cicilan_per_bulan > laba_bersih_akhir:
            st.error("### ❌ TIDAK LAYAK")
            st.write("Alasan: Cicilan lebih besar dari sisa laba usaha. Bisnis akan bangkrut.")
        elif cicilan_per_bulan > kemampuan_bayar:
            st.warning("### ⚠️ RISIKO TINGGI")
            st.write(f"Cicilan ({format_rp(cicilan_per_bulan)}) melebihi batas aman bank ({format_rp(kemampuan_bayar)}).")
        else:
            st.success("### ✅ SANGAT LAYAK")
            st.write("Arus kas sangat sehat untuk meng-cover cicilan ini.")

    st.info(f"**Sisa Laba Akhir setelah Cicilan:** {format_rp(sisa_setelah_cicilan)}")

else:
    st.warning("Belum ada data transaksi untuk dianalisis.")

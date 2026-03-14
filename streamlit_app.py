import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro", layout="wide")

# --- DATABASE ---
conn = sqlite3.connect('finsaku_modern.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FORMATTING ---
def format_rp(angka):
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# 2. UI STYLING - MODERN DARK SLATE & MINT (Anti-UNAIR)
st.markdown("""
<style>
    /* Background & Font */
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Menghilangkan elemen kosong/dekorasi tidak perlu */
    .stMarkdown div[data-testid="stMarkdownContainer"] hr { border-top: 1px solid #1e293b; }
    
    /* Card Style */
    .card {
        background: #1e293b; padding: 24px; border-radius: 16px;
        border: 1px solid #334155; margin-bottom: 20px;
    }
    
    /* Metric Card */
    .metric-card {
        background: #0ea5e9; color: #ffffff; padding: 20px;
        border-radius: 12px; text-align: center; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    }
    
    /* Button Style */
    .stButton>button {
        background: #0ea5e9 !important; color: #ffffff !important;
        border-radius: 10px; border: none; font-weight: 600; width: 100%; height: 3em;
    }
    
    /* Headers */
    h1, h2, h3 { color: #38bdf8 !important; font-family: 'Inter', sans-serif; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
</style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏦 **Profil Bisnis**")
    nama_usaha = st.text_input("Nama Usaha", "UMKM Maju")
    modal_awal = st.number_input("Modal Awal Kas (Rp)", value=7000000)
    
    st.markdown("---")
    st.markdown("### ⚙️ **Parameter Profit**")
    hpp = st.number_input("HPP Produk", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    prive_pct = st.slider("Jatah Prive %", 0, 100, 30)
    
    kas_sekarang = modal_awal + (total_laba - total_prive)
    st.markdown(f"""
    <div style="background:#0ea5e9; padding:15px; border-radius:10px; margin-top:20px;">
        <p style="margin:0; font-size:14px; color:#e0f2fe;">Kas Saat Ini:</p>
        <h3 style="margin:0; color:white !important;">{format_rp(kas_sekarang)}</h3>
    </div>
    """, unsafe_allow_html=True)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_usaha}")

# 1. INPUT & REVISI (DIBERSIHKAN TOTAL)
col_left, col_right = st.columns([1.6, 1])

with col_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Pencatatan Baru")
    mode = st.radio("Metode:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1: tgl = st.date_input("Pilih Tanggal", datetime.now())
    with c2: omzet = st.number_input(f"Input Omzet ({mode})", value=0, step=10000)
    
    laba_calc = omzet - (omzet * (hpp/jual)) if jual > 0 else 0
    prive_calc = laba_calc * (prive_pct/100)
    
    if st.button("📥 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet, laba_calc, prive_calc, mode))
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🛠️ Koreksi Data")
    if not df.empty:
        # Menampilkan data terakhir dengan gaya list yang bersih
        last_data = df.sort_values(by='id', ascending=False).head(3)
        for _, row in last_data.iterrows():
            ca, cb = st.columns([4, 1])
            ca.markdown(f"**{row['tanggal']}**<br><small>{format_rp(row['omzet'])}</small>", unsafe_allow_html=True)
            if cb.button("🗑️", key=f"del_{row['id']}"):
                c.execute(f"DELETE FROM transaksi WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    else:
        st.info("Belum ada data untuk dikoreksi.")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. ANALISIS PERUBAHAN MODAL & KUR
st.markdown("---")
tab1, tab2 = st.tabs(["📊 PERUBAHAN MODAL", "🏦 KELAYAKAN PINJAMAN"])

with tab1:
    if not df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        sel_bln = st.selectbox("Pilih Periode:", df['bulan'].unique())
        f_df = df[df['bulan'] == sel_bln]
        
        t_laba, t_prive = f_df['laba'].sum(), f_df['prive'].sum()
        kenaikan = t_laba - t_prive
        
        st.markdown(f"### Laporan Modal: {sel_bln}")
        st.markdown(f"""
        - **Total Laba Bersih:** <span style="color:#38bdf8">{format_rp(t_laba)}</span>
        - **Prive (Konsumsi Pribadi):** <span style="color:#fb7185">-{format_rp(t_prive)}</span>
        <hr>
        <h2 style="margin:0;">📈 Kenaikan Kas Modal: {format_rp(kenaikan)}</h2>
        <p style="margin-top:10px; color:#94a3b8;">Uang ini adalah 'darah' baru yang memperkuat modal usaha Anda bulan ini.</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.warning("Masukkan data penjualan untuk melihat laporan modal.")

with tab2:
    if not df.empty:
        # Logika Kelayakan (Standar Perbankan 35% Laba)
        rata_laba = df['laba'].mean() * (30 if mode == "Harian" else 1)
        batas_cicilan = rata_laba * 0.35
        
        st.markdown(f"""
        <div class="card">
            <h3>Analisis Kredit BRI</h3>
            <p>Berdasarkan rata-rata untung, batas cicilan bulanan yang dianggap <b>aman</b> oleh bank adalah:</p>
            <h2 style="color:#38bdf8;">{format_rp(batas_cicilan)}</h2>
        </div>
        """, unsafe_allow_html=True)

        skema_kur = [
            {"nama": "Super Mikro (10jt)", "cicilan": 883000},
            {"nama": "Mikro A (50jt)", "cicilan": 2250000},
            {"nama": "Mikro B (100jt)", "cicilan": 4200000}
        ]
        
        cols = st.columns(3)
        for i, s in enumerate(skema_kur):
            status_aman = s['cicilan'] <= batas_cicilan
            with cols[i]:
                st.markdown(f"""
                <div style="background:{'#065f46' if status_aman else '#7f1d1d'}; padding:20px; border-radius:12px; text-align:center;">
                    <p style="margin:0; font-size:14px; color:#ecfdf5;">{s['nama']}</p>
                    <h3 style="margin:5px 0; color:white !important;">{format_rp(s['cicilan'])}/bln</h3>
                    <p style="margin:0; font-weight:bold;">{'✅ LAYAK' if status_aman else '⚠️ BERAT'}</p>
                </div>
                """, unsafe_allow_html=True)
    else: st.warning("Data transaksi belum cukup untuk simulasi pinjaman.")

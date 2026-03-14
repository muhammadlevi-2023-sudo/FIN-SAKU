import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro", layout="wide")

# --- DATABASE ---
conn = sqlite3.connect('finsaku_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FORMATTING ---
def format_rp(angka):
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# 2. UI STYLING - PREMIUM DARK MODE
st.markdown("""
<style>
    .stApp { background-color: #001220; color: #ffffff; }
    .card {
        background: #001f3f; padding: 20px; border-radius: 12px;
        border-top: 4px solid #FFD700; margin-bottom: 20px;
    }
    .metric-card {
        background: #ffffff; color: #001220; padding: 15px;
        border-radius: 10px; text-align: center; font-weight: bold;
    }
    .stButton>button {
        background: #FFD700 !important; color: #000 !important;
        font-weight: bold; border-radius: 8px; border: none;
    }
    h1, h2, h3 { color: #FFD700 !important; }
</style>
""", unsafe_allow_html=True)

# --- DATA PROCESSING ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("💰 FIN-Saku")
    st.markdown("---")
    nama_usaha = st.text_input("Nama Usaha", "UMKM Maju")
    modal_awal = st.number_input("Modal Awal Kas (Rp)", value=7000000)
    st.markdown("---")
    hpp = st.number_input("HPP Produk", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    prive_pct = st.slider("Jatah Prive %", 0, 100, 30)
    
    kas_sekarang = modal_awal + (total_laba - total_prive)
    st.metric("Modal Kas Terkini", format_rp(kas_sekarang))

# --- DASHBOARD UTAMA ---
st.header(f"Ringkasan Bisnis: {nama_usaha}")

# BAGIAN INPUT & REVISI
col_kiri, col_kanan = st.columns([1.5, 1])

with col_kiri:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Catat Transaksi")
    mode = st.radio("Metode Catat:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1: tgl = st.date_input("Tanggal", datetime.now())
    with c2: omzet = st.number_input(f"Omzet ({mode})", value=0, step=10000)
    
    laba_calc = omzet - (omzet * (hpp/jual)) if jual > 0 else 0
    prive_calc = laba_calc * (prive_pct/100)
    
    if st.button("🚀 SIMPAN DATA"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet, laba_calc, prive_calc, mode))
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_kanan:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🛠️ Revisi Terakhir")
    if not df.empty:
        last_data = df.sort_values(by='id', ascending=False).head(3)
        for _, row in last_data.iterrows():
            ca, cb = st.columns([3, 1])
            ca.write(f"{row['tanggal']} | {format_rp(row['omzet'])}")
            if cb.button("🗑️", key=f"del_{row['id']}"):
                c.execute(f"DELETE FROM transaksi WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    else: st.write("Data masih kosong.")
    st.markdown('</div>', unsafe_allow_html=True)

# BAGIAN LAPORAN & KUR
st.write("---")
tab1, tab2 = st.tabs(["📊 LAPORAN PERUBAHAN MODAL", "🏦 ANALISIS KELAYAKAN KUR"])

with tab1:
    if not df.empty:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        bln_pilih = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        data_filter = df[df['bulan'] == bln_pilih]
        
        untung = data_filter['laba'].sum()
        ambil = data_filter['prive'].sum()
        bersih = untung - ambil
        
        st.write(f"### Analisis Modal - {bln_pilih}")
        st.markdown(f"""
        * **Laba Bersih Usaha:** {format_rp(untung)}
        * **Prive (Diambil Pribadi):** -{format_rp(ambil)}
        ---
        ### ✅ PENAMBAHAN KAS MODAL: {format_rp(bersih)}
        """)
        st.success(f"Bulan ini, modal Anda bertambah sebesar {format_rp(bersih)}.")
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.info("Belum ada data bulanan.")

with tab2:
    if not df.empty:
        # Analisis Kemampuan Bayar (35% Laba)
        laba_avg = df['laba'].mean() * (30 if mode == "Harian" else 1)
        batas = laba_avg * 0.35
        
        st.subheader("Berapa Pinjaman Yang Aman Bagi Saya?")
        st.write(f"Berdasarkan performa, cicilan aman Anda adalah: **{format_rp(batas)}/bulan**")
        
        skema = [
            {"nama": "KUR Super Mikro (10jt)", "cicilan": 883000},
            {"nama": "KUR Mikro A (50jt)", "cicilan": 2250000},
            {"nama": "KUR Mikro B (100jt)", "cicilan": 4200000}
        ]
        
        cols = st.columns(3)
        for i, s in enumerate(skema):
            boleh = s['cicilan'] <= batas
            with cols[i]:
                st.markdown(f"""
                <div class="metric-card" style="border-bottom: 8px solid {'#28a745' if boleh else '#dc3545'};">
                    <p>{s['nama']}</p>
                    <h3 style="color:#001220;">{format_rp(s['cicilan'])}/bln</h3>
                    <p>{'✅ LAYAK' if boleh else '⚠️ BERAT'}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="card" style="margin-top:20px;">
            <h4>💡 Analisis Perbankan (BRI):</h4>
            <p>Agar KUR disetujui, bank melihat <b>RPC (Repayment Capacity)</b>. Idealnya cicilan tidak melebihi 35% laba. 
            Jika status Anda ⚠️ BERAT, disarankan memperkecil jumlah pinjaman atau memperpanjang jangka waktu.</p>
        </div>
        """, unsafe_allow_html=True)

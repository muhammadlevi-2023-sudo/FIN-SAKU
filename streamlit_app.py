import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro UNAIR", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_unair_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# 2. UI CUSTOM (NAVY & GOLD UNAIR) - ANTI KOTAK KOSONG
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; color: #ffffff !important; }
    
    /* Hilangkan elemen kosong yang mengganggu */
    [data-testid="stVerticalBlock"] > div:empty { display: none !important; }
    
    /* Card Putih Bersih untuk Konten */
    .unair-card {
        background-color: #ffffff !important;
        padding: 22px; border-radius: 15px; border-left: 10px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 6px 15px rgba(0,0,0,0.4);
        color: #000000 !important;
    }
    .unair-card h3, .unair-card p, .unair-card b, .unair-card td { color: #001f3f !important; }
    
    /* Tombol Gold */
    .stButton>button { 
        background-color: #FFD700 !important; color: #001f3f !important; 
        font-weight: bold; border-radius: 8px; width: 100%; height: 3.5em; border: none;
    }
    .stButton>button:hover { background-color: #e6c200 !important; }
    
    /* Header & Sidebar */
    h1, h2, h3 { color: #FFD700 !important; }
    [data-testid="stSidebar"] { background-color: #001226; border-right: 2px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PROFIL & MODAL ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal = st.number_input("Modal Awal Kas (Rp)", value=7000000)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga")
    hpp_val = st.number_input("HPP Produk", value=5000)
    hrg_val = st.number_input("Harga Jual", value=15000)
    prive_pct = st.slider("Jatah Jajan / Prive (%)", 0, 50, 30)
    
    kas_sekarang = m_awal + (total_laba - total_prive)
    st.markdown(f"""
    <div style="background:#FFD700; padding:15px; border-radius:10px; color:#001f3f; text-align:center; margin-top:20px;">
        <p style="margin:0; font-weight:bold;">Kas Modal Saat Ini:</p>
        <h2 style="margin:0; color:#001f3f !important;">{format_rp(kas_sekarang)}</h2>
    </div>
    """, unsafe_allow_html=True)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

# BAGIAN INPUT & REVISI (Dibuat Bersih)
col_in, col_rev = st.columns([1.5, 1])

with col_in:
    st.markdown('<div class="unair-card">', unsafe_allow_html=True)
    st.subheader("📝 Catat Penjualan")
    rekap_mode = st.radio("Metode:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1: tgl = st.date_input("Tanggal", datetime.now())
    with c2: omzet = st.number_input(f"Total Omzet", value=0, step=10000)
    
    # Hitung Laba Bersih Otomatis
    laba_in = omzet - (omzet * (hpp_val / hrg_val)) if hrg_val > 0 else 0
    prive_in = laba_in * (prive_pct / 100)
    
    st.write(f"Estimasi Untung Bersih: **{format_rp(laba_in)}**")
    
    if st.button("🚀 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_rev:
    st.markdown('<div class="unair-card">', unsafe_allow_html=True)
    st.subheader("🛠️ Koreksi")
    if not df.empty:
        df_rev = df.sort_values(by='id', ascending=False).head(4)
        for _, row in df_rev.iterrows():
            cx, cy = st.columns([4, 1])
            cx.write(f"**{row['tanggal']}** | {format_rp(row['omzet'])}")
            if cy.button("🗑️", key=f"del_{row['id']}"):
                c.execute(f"DELETE FROM transaksi WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    else:
        st.write("Data masih kosong.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ANALISIS MODAL & KUR ---
st.write("---")
tab_modal, tab_kur = st.tabs(["📊 LAPORAN PERUBAHAN MODAL", "🏦 ANALISIS LAYAK PINJAM (KUR)"])

with tab_modal:
    if not df.empty:
        st.markdown('<div class="unair-card">', unsafe_allow_html=True)
        pilih_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        db = df[df['bulan'] == pilih_b]
        l_bln, p_bln = db['laba'].sum(), db['prive'].sum()
        
        st.markdown(f"""
        <h3 style="text-align:center;">Laporan Modal - {pilih_b}</h3>
        <table style="width:100%; font-size:20px; margin-top:15px;">
            <tr><td>Total Untung Bersih</td><td style="text-align:right; color:green;">{format_rp(l_bln)}</td></tr>
            <tr><td>Total Diambil Jajan</td><td style="text-align:right; color:red;">({format_rp(p_bln)})</td></tr>
            <tr style="font-weight:bold; border-top:3px solid #001f3f;">
                <td>TAMBAHAN KAS MODAL</td><td style="text-align:right;">{format_rp(l_bln - p_bln)}</td>
            </tr>
        </table>
        <p style="margin-top:15px; font-style:italic;">*Artinya modal usaha Anda bertambah nyata sebesar <b>{format_rp(l_bln - p_bln)}</b> di bulan ini.</p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.warning("Masukkan data dulu untuk melihat laporan.")

with tab_kur:
    if not df.empty:
        # Logika Bank: Menggunakan rata-rata laba harian agar lebih adil
        rata_laba = df['laba'].mean() * (30 if rekap_mode == "Harian" else 1)
        batas_aman = rata_laba * 0.35 # Batas cicilan aman 35% dari untung
        
        st.subheader("Berapa Saya Bisa Pinjam di BRI?")
        st.write(f"Berdasarkan untung Anda, jatah cicilan aman adalah: **{format_rp(batas_aman)}** per bulan.")
        
        skema = [
            {"nama": "KUR Super Mikro (10jt)", "cicilan": 883000},
            {"nama": "KUR Mikro A (50jt)", "cicilan": 2250000},
            {"nama": "KUR Mikro B (100jt)", "cicilan": 4200000}
        ]
        
        cols = st.columns(3)
        for i, s in enumerate(skema):
            is_aman = s['cicilan'] <= batas_aman
            with cols[i]:
                st.markdown(f"""
                <div style="background:{'#006400' if is_aman else '#8B0000'}; padding:20px; border-radius:15px; text-align:center; color:white;">
                    <p style="margin:0; font-size:14px;">{s['nama']}</p>
                    <h3 style="margin:5px 0; color:white !important;">{format_rp(s['cicilan'])}/bln</h3>
                    <p style="font-weight:bold;">{'✅ LAYAK' if is_aman else '⚠️ TERLALU BERAT'}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="unair-card" style="margin-top:20px;">
            <h4>💡 Tips Lolos KUR:</h4>
            <p>Petugas Bank (Mantri) sangat suka jika <b>Uang Kas</b> dan <b>Uang Jajan</b> dipisah. 
            Gunakan laporan dari tab 'Laporan Modal' untuk membuktikan bahwa usaha Anda berkembang setiap bulan.</p>
        </div>
        """, unsafe_allow_html=True)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku UNAIR Edition", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_unair.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FORMATTING ---
def format_rp(angka):
    return f"Rp {int(angka):,.0f}".replace(",", ".")

# 2. UI STYLING - TEMA UNIVERSITAS AIRLANGGA (BIRU & KUNING)
st.markdown("""
<style>
    /* Background Navy UNAIR */
    .stApp { background-color: #001f3f; color: #ffffff; }
    
    /* Menghilangkan elemen dashboard kosong yang mengganggu */
    [data-testid="stVerticalBlock"] > div:empty { display: none !important; }
    hr { border-top: 2px solid #FFD700 !important; }

    /* Card Style - Putih Bersih agar Kontras */
    .unair-card {
        background: #ffffff; padding: 25px; border-radius: 15px;
        border-left: 8px solid #FFD700; margin-bottom: 20px;
        color: #001f3f !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .unair-card h3, .unair-card p, .unair-card b { color: #001f3f !important; }
    
    /* Button Style - Kuning Emas */
    .stButton>button {
        background: #FFD700 !important; color: #001f3f !important;
        font-weight: bold; border-radius: 8px; border: none; height: 3em;
    }
    
    /* Header Gold */
    h1, h2, h3 { color: #FFD700 !important; }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] { background-color: #001226; border-right: 2px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PROFIL & MODAL ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🏢 FIN-Saku</h2>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    m_awal = st.number_input("Modal Awal Kas (Rp)", value=7000000)
    
    st.write("---")
    hpp = st.number_input("HPP Produk", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    p_pct = st.slider("Jatah Prive %", 0, 100, 30)
    
    k_sekarang = m_awal + (total_laba - total_prive)
    st.markdown(f"""
    <div style="background:#FFD700; padding:15px; border-radius:10px; color:#001f3f; text-align:center;">
        <p style="margin:0; font-weight:bold;">Kas Modal Saat Ini:</p>
        <h3 style="margin:0; color:#001f3f !important;">{format_rp(k_sekarang)}</h3>
    </div>
    """, unsafe_allow_html=True)

# --- KONTEN UTAMA ---
st.title(f"Pusat Kendali Bisnis: {nama_u}")

# 1. FORM INPUT & REVISI (Tanpa Elemen Kosong)
col_a, col_b = st.columns([1.5, 1])

with col_a:
    st.markdown('<div class="unair-card">', unsafe_allow_html=True)
    st.subheader("📝 Catat Uang Masuk")
    mode = st.radio("Metode Pencatatan:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)
    
    c1, c2 = st.columns(2)
    with c1: tgl = st.date_input("Tanggal Transaksi", datetime.now())
    with c2: omz = st.number_input(f"Total Omzet ({mode})", value=0, step=10000)
    
    l_calc = omz - (omz * (hpp/jual)) if jual > 0 else 0
    p_calc = l_calc * (p_pct/100)
    
    if st.button("💾 SIMPAN DATA KE SISTEM"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omz, l_calc, p_calc, mode))
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_b:
    st.markdown('<div class="unair-card">', unsafe_allow_html=True)
    st.subheader("🛠️ Koreksi Data")
    if not df.empty:
        last = df.sort_values(by='id', ascending=False).head(3)
        for _, row in last.iterrows():
            ca, cb = st.columns([4, 1])
            ca.write(f"**{row['tanggal']}** | {format_rp(row['omzet'])}")
            if cb.button("🗑️", key=f"del_{row['id']}"):
                c.execute(f"DELETE FROM transaksi WHERE id={row['id']}")
                conn.commit()
                st.rerun()
    else: st.info("Belum ada data untuk diperbaiki.")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. ANALISIS KELAYAKAN & MODAL
st.write("---")
t_modal, t_bank = st.tabs(["📊 LAPORAN MODAL", "🏦 ANALISIS LAYAK PINJAM"])

with t_modal:
    if not df.empty:
        st.markdown('<div class="unair-card">', unsafe_allow_html=True)
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        f_df = df[df['bulan'] == sel_b]
        
        t_l, t_p = f_df['laba'].sum(), f_df['prive'].sum()
        bersih = t_l - t_p
        
        st.write(f"### Ringkasan Kas Bulan {sel_b}")
        st.markdown(f"""
        - Total Laba Bersih: **{format_rp(t_l)}**
        - Total Diambil Pribadi: **-{format_rp(t_p)}**
        <hr>
        <h2 style="color:#001f3f !important;">✅ TAMBAHAN MODAL: {format_rp(bersih)}</h2>
        <p><i>Uang ini secara otomatis memperkuat daya tahan bisnis Anda bulan ini.</i></p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.warning("Silakan isi data transaksi terlebih dahulu.")

with t_bank:
    if not df.empty:
        # Menghitung batas aman cicilan (35% laba terakhir)
        laba_ref = df['laba'].mean() * (30 if mode == "Harian" else 1)
        batas = laba_ref * 0.35
        
        st.markdown(f"""
        <div class="unair-card">
            <h3>Seberapa Layak Anda di Mata Bank?</h3>
            <p>Berdasarkan keuntungan usaha, cicilan bulanan yang <b>aman</b> bagi Anda adalah:</p>
            <h2 style="color:#001f3f !important;">{format_rp(batas)} / Bulan</h2>
        </div>
        """, unsafe_allow_html=True)

        # Skema KUR BRI Berdasarkan Kemampuan Bayar
        skema = [
            {"nama": "KUR Super Mikro (10jt)", "cicilan": 883000},
            {"nama": "KUR Mikro A (50jt)", "cicilan": 2250000},
            {"nama": "KUR Mikro B (100jt)", "cicilan": 4200000}
        ]
        
        cols = st.columns(3)
        for i, s in enumerate(skema):
            layak = s['cicilan'] <= batas
            with cols[i]:
                st.markdown(f"""
                <div style="background:{'#006400' if layak else '#8B0000'}; padding:20px; border-radius:12px; text-align:center; color:white;">
                    <p style="margin:0; font-size:14px;">{s['nama']}</p>
                    <h3 style="margin:5px 0; color:white !important;">{format_rp(s['cicilan'])}/bln</h3>
                    <p style="margin:0; font-weight:bold;">{'✅ LAYAK PINJAM' if layak else '⚠️ BEBAN BERAT'}</p>
                </div>
                """, unsafe_allow_html=True)
    else: st.warning("Data belum cukup untuk menganalisis kelayakan kredit.")

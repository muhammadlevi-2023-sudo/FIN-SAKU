import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi UMKM Bankable", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v13.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, 
              omzet REAL, laba REAL, prive REAL, tipe TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        val = int(angka)
        return f"Rp {val:,}".replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 2. UI CUSTOM (NAVY & GOLD STYLE)
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp { background-color: #002147; color: #FFFFFF; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #001a35 !important;
        border-right: 3px solid #FFD700;
    }
    
    /* Headers & Text */
    h1, h2, h3, p, label { color: #FFFFFF !important; }
    .gold-text { color: #FFD700 !important; font-weight: bold; }
    
    /* Card UI */
    .modern-card {
        background: #FFFFFF;
        padding: 25px;
        border-radius: 15px;
        border-top: 8px solid #FFD700;
        color: #002147 !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .modern-card h3, .modern-card p, .modern-card b, .modern-card span { color: #002147 !important; }
    
    /* Buttons */
    .stButton>button {
        background-color: #FFD700 !important;
        color: #002147 !important;
        font-weight: bold;
        border-radius: 10px;
        border: none;
        height: 50px;
    }
    .stButton>button:hover { background-color: #e6c200 !important; }

    /* Metric Styling */
    [data-testid="stMetricValue"] { color: #FFD700 !important; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA AWAL ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# 3. SIDEBAR (PROFIL BISNIS & REALTIME KAS)
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700; font-size: 40px;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; margin-top:-20px;'>Konsultan Keuangan Digital</p>", unsafe_allow_html=True)
    st.write("---")
    
    # Profil & Input Kas Awal
    nama_u = st.text_input("Nama Usaha", "Catering Maju Bersama")
    sektor = st.selectbox("Sektor", ["Kuliner", "Retail", "Jasa", "Manufaktur"])
    
    kas_awal_raw = st.text_input("Uang Kas Awal (Modal)", "10000000")
    kas_awal = clean_to_int(kas_awal_raw)
    
    # Update Kas Realtime
    total_laba = df['laba'].sum() if not df.empty else 0
    total_prive = df['prive'].sum() if not df.empty else 0
    kas_saat_ini = kas_awal + total_laba - total_prive
    
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border-left: 5px solid #FFD700;'>
        <p style='margin:0; font-size:14px;'>SALDO KAS REALTIME:</p>
        <h2 style='margin:0; color:#FFD700;'>{format_rp(kas_saat_ini)}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Prive")
    hpp_raw = st.text_input("HPP Produk", "5000")
    hpp = clean_to_int(hpp_raw)
    
    hrg_raw = st.text_input("Harga Jual", "15000")
    hrg = clean_to_int(hrg_raw)
    
    margin_pct = ((hrg - hpp) / hrg * 100) if hrg > 0 else 0
    st.markdown(f"Margin: <span class='gold-text'>{margin_pct:.1f}%</span>", unsafe_allow_html=True)
    
    # Warning Margin
    if margin_pct < 30: st.error("⚠️ Margin rendah! Bank menyukai margin > 30%.")
    
    prive_pct = st.slider("Alokasi Prive (%)", 0, 100, 30)

# 4. DASHBOARD UTAMA
st.title(f"🚀 Dashboard {nama_u}")

# Input Transaksi
with st.container():
    st.subheader("📝 Pencatatan Baru")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        tipe = st.selectbox("Metode Catat", ["Harian", "Mingguan", "Bulanan"])
        tgl = st.date_input("Tanggal", datetime.now())
    with c2:
        omzet_raw = st.text_input("Input Omzet (Angka Saja)")
        omzet = clean_to_int(omzet_raw)
        st.markdown(f"Tercatat: <span class='gold-text'>{format_rp(omzet)}</span>", unsafe_allow_html=True)
    with c3:
        st.write("##") # Spacer
        if st.button("🔔 SIMPAN TRANSAKSI"):
            laba_bersih = omzet * (margin_pct / 100)
            prive_val = laba_bersih * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, omzet, laba, prive, tipe) VALUES (?,?,?,?,?,?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), omzet, laba_bersih, prive_val, tipe))
            conn.commit()
            st.toast("Data Berhasil Diamankan!", icon="✅")
            st.rerun()

# 5. TAB LAPORAN & KUR
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN RESMI", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        sel_b = st.selectbox("Pilih Periode", df['bulan'].unique())
        df_m = df[df['bulan'] == sel_b]
        
        o_sum = df_m['omzet'].sum()
        l_sum = df_m['laba'].sum()
        p_sum = df_m['prive'].sum()
        
        # UI Laporan Modern
        st.markdown(f"""
        <div class="modern-card">
            <h3 style="text-align:center;">LAPORAN LABA RUGI - {sel_b.upper()}</h3>
            <hr>
            <div style="display:flex; justify-content:space-between;">
                <span>Total Omzet</span><b>{format_rp(o_sum)}</b>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Laba Operasional</span><b style="color:green;">{format_rp(l_sum)}</b>
            </div>
            <div style="display:flex; justify-content:space-between;">
                <span>Pengambilan Prive</span><b style="color:red;">-{format_rp(p_sum)}</b>
            </div>
            <hr>
            <div style="display:flex; justify-content:space-between; font-size:1.2rem;">
                <b>LABA DITAHAN (MODAL)</b><b style="color:#002147;">{format_rp(l_sum - p_sum)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # DOWNLOAD PDF
        if st.button("📥 UNDUH LAPORAN PDF (BANK READY)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"{nama_u.upper()}", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 7, f"Laporan Keuangan UMKM | Periode: {sel_b}", 0, 1, 'C')
            pdf.ln(10)
            pdf.cell(100, 10, "Keterangan", 1); pdf.cell(90, 10, "Nilai", 1, 1, 'C')
            pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(90, 10, format_rp(o_sum), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Bersih", 1); pdf.cell(90, 10, format_rp(l_sum), 1, 1, 'R')
            pdf.cell(100, 10, "Saldo Kas Saat Ini", 1); pdf.cell(90, 10, format_rp(kas_saat_ini), 1, 1, 'R')
            st.download_button("Klik untuk Simpan", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{sel_b}.pdf")

    with tab_kur:
        st.subheader("🏦 Konsultasi KUR BRI")
        histori = df['bulan'].nunique()
        
        # Penentuan Produk
        if kas_saat_ini < 10000000: p_nama, p_limit = "KUR Super Mikro", "Hingga Rp 10 Juta"
        elif kas_saat_ini < 50000000: p_nama, p_limit = "KUR Mikro", "Rp 10 - 50 Juta"
        else: p_nama, p_limit = "KUR Kecil", "Rp 50 - 500 Juta"
        
        st.markdown(f"""
        <div class="modern-card">
            <h4>Rekomendasi: {p_nama}</h4>
            <p>Plafon Ideal: <b>{p_limit}</b></p>
            <p>Status Histori: <b>{histori}/6 Bulan</b> {"✅ (Bankable)" if histori >=3 else "⚠️ (Lengkapi lagi)"}</p>
            <hr>
            <b>Dokumen Yang Perlu Dibawa:</b><br>
            1. KTP & KK (Asli & Fotokopi)<br>
            2. NIB atau Surat Keterangan Usaha (SKU)<br>
            3. Laporan Keuangan (Cetak dari FIN-Saku)<br>
            4. NPWP (Untuk plafon > Rp 50 Juta)
        </div>
        """, unsafe_allow_html=True)

    with tab_rev:
        target = st.selectbox("Pilih Data Hapus:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df.iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Silakan masukkan transaksi pertama Anda.")

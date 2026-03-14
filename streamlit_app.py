import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: CFO Dashboard", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_v9_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        abs_angka = abs(float(angka))
        formatted = "{:,.0f}".format(abs_angka).replace(",", ".")
        return f"Rp {formatted}" if angka >= 0 else f"Rp -{formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# --- FUNGSI PDF (Format Perusahaan) ---
def generate_pdf(nama_u, periode, omzet, laba, prive, kas_awal, kas_akhir):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, nama_u.upper(), 0, 1, 'C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, "Laporan Keuangan Resmi - UMKM Digital", 0, 1, 'C')
    pdf.ln(5)
    pdf.line(10, 32, 200, 32)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"LAPORAN LABA RUGI PERIODE {periode.upper()}", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    # Grid Laporan
    pdf.cell(100, 10, "Total Omzet", 1)
    pdf.cell(90, 10, format_rp(omzet), 1, 1, 'R')
    pdf.cell(100, 10, "Total Laba Bersih", 1)
    pdf.cell(90, 10, format_rp(laba), 1, 1, 'R')
    pdf.cell(100, 10, "Pengambilan Prive", 1)
    pdf.cell(90, 10, f"({format_rp(prive)})", 1, 1, 'R')
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "POSISI KAS", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 10, "Kas Awal Periode", 1)
    pdf.cell(90, 10, format_rp(kas_awal), 1, 1, 'R')
    pdf.cell(100, 10, "Kas Akhir Periode", 1)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(90, 10, format_rp(kas_akhir), 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM (DARK NAVY & GOLD)
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    
    /* Card Laporan */
    .report-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
        color: #333333 !important;
        border-top: 5px solid #FFD700;
    }
    .report-card h3, .report-card p, .report-card b { color: #333333 !important; }
    
    /* Stat Box */
    .stat-box {
        text-align: center;
        padding: 15px;
        background: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
    .stat-val { font-size: 1.5rem; font-weight: bold; color: #001f3f; }
    .stat-lbl { font-size: 0.8rem; color: #666; text-transform: uppercase; }

    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 2px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    
    m_awal_raw = st.text_input("Modal Awal", "7000000")
    modal_awal = clean_to_int(m_awal_raw)
    st.caption(f"Tercatat: {format_rp(modal_awal)}")
    
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    # PESAN PERINGATAN INTERAKTIF
    if hrg_val > 0:
        margin = ((hrg_val - hpp_val) / hrg_val) * 100
        if margin < 30: st.error(f"⚠️ Margin Kritis: {margin:.1f}%")
        else: st.success(f"✅ Margin Sehat: {margin:.1f}%")

    prive_pct = st.slider("Alokasi Prive (%)", 0, 100, 30)
    if prive_pct > 40: st.warning("⚠️ Prive tinggi menghambat ekspansi modal.")

# --- DASHBOARD UTAMA ---
st.title(f"🚀 Dashboard {nama_u}")

# Input Section
with st.expander("➕ CATAT TRANSAKSI BARU", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1: tgl = st.date_input("Tanggal", datetime.now())
    with c2: 
        omzet_raw = st.text_input("Omzet (Rp)", "0")
        omzet_in = clean_to_int(omzet_raw)
        st.caption(f"Tercatat: {format_rp(omzet_in)}")
    with c3:
        st.write(" ")
        if st.button("SIMPAN DATA"):
            laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
            p_in = laba_in * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, p_in, "Harian"))
            conn.commit()
            st.toast("Data Berhasil Disimpan!")
            st.rerun()

# --- BAGIAN LAPORAN ---
if not df.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR", "⚙️ KONTROL"])
    
    with tab1:
        list_bulan = sorted(df['bulan'].unique().tolist())
        sel_b = st.selectbox("Pilih Periode:", list_bulan, index=len(list_bulan)-1)
        
        # Logic Data
        db_b = df[df['bulan'] == sel_b]
        o_b, l_b, p_b = db_b['omzet'].sum(), db_b['laba'].sum(), db_b['prive'].sum()
        
        idx_b = list_bulan.index(sel_b)
        m_lalu = df[df['bulan'].isin(list_bulan[:idx_b])]['laba'].sum() - df[df['bulan'].isin(list_bulan[:idx_b])]['prive'].sum()
        kas_awal = modal_awal + m_lalu
        kas_akhir = kas_awal + l_b - p_b

        # UI LAPORAN MODERN
        st.markdown(f"""
        <div class="report-card">
            <h3 style="text-align:center;">LAPORAN KEUANGAN BULAN {sel_b.upper()}</h3>
            <hr>
            <div style="display: flex; justify-content: space-around; gap: 10px; margin-bottom: 20px;">
                <div class="stat-box" style="flex:1;">
                    <div class="stat-lbl">Total Omzet</div>
                    <div class="stat-val">{format_rp(o_b)}</div>
                </div>
                <div class="stat-box" style="flex:1;">
                    <div class="stat-lbl">Laba Bersih</div>
                    <div class="stat-val" style="color: green;">{format_rp(l_b)}</div>
                </div>
                <div class="stat-box" style="flex:1;">
                    <div class="stat-lbl">Prive</div>
                    <div class="stat-val" style="color: red;">{format_rp(p_b)}</div>
                </div>
            </div>
            <div style="background: #001f3f; color: white; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between;">
                <b>SALDO KAS AKHIR:</b>
                <b style="font-size: 1.2rem; color: #FFD700;">{format_rp(kas_akhir)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Download PDF
        pdf_file = generate_pdf(nama_u, sel_b, o_b, l_b, p_b, kas_awal, kas_akhir)
        st.download_button(f"📥 DOWNLOAD PDF {sel_b}", data=pdf_file, file_name=f"Laporan_{sel_b}.pdf", mime="application/pdf")

    with tab2:
        # LOGIKA KUR (Sesuai Permintaan)
        st.subheader("🏦 Kelayakan Kredit")
        konsistensi = df['bulan'].nunique()
        if konsistensi < 3:
            st.warning(f"Data baru {konsistensi} bulan. Bank butuh minimal 3 bulan.")
        else:
            st.success("Analisis: Bisnis Anda memenuhi kriteria tenor 3 bulan.")
            plafon = 50000000 if kas_akhir > 15000000 else 10000000
            st.markdown(f"""
            <div class="report-card">
                <h4>Simulasi KUR Mikro</h4>
                <p>Estimasi Plafon: <b>{format_rp(plafon)}</b></p>
                <p>Batas Cicilan Aman: <b>{format_rp(l_b * 0.35)}/bln</b></p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        st.subheader("Manajemen Data")
        target = st.selectbox("Hapus Data:", [f"ID:{r['id']} | {r['tanggal']}" for _, r in df.iterrows()])
        if st.button("HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()

else:
    st.info("Belum ada data. Silakan input penjualan di atas.")

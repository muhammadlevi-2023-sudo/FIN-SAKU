import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_final.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, tahun INTEGER,
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        abs_angka = abs(float(angka))
        formatted = "{:,.0f}".format(abs_angka).replace(",", ".")
        if angka < 0: return f"Rp -{formatted}"
        return f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# --- FUNGSI GENERATE PDF (STANDARD BANK) ---
def generate_pdf(nama_usaha, periode_bulan, data_ringkas):
    pdf = FPDF()
    pdf.add_page()
    
    # Header Laporan
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, nama_usaha.upper(), ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"LAPORAN KEUANGAN BULANAN", ln=True, align='C')
    pdf.cell(190, 10, f"Periode: {periode_bulan}", ln=True, align='C')
    pdf.line(10, 45, 200, 45)
    pdf.ln(15)

    # Section 1: Laba Rugi
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "I. LAPORAN LABA RUGI", ln=True)
    pdf.set_font("Arial", '', 11)
    
    pdf.cell(100, 10, "Total Pendapatan (Omzet)"); pdf.cell(90, 10, format_rp(data_ringkas['omzet']), ln=True, align='R')
    pdf.cell(100, 10, "Beban Pokok Penjualan (HPP)"); pdf.cell(90, 10, f"- {format_rp(data_ringkas['omzet'] - data_ringkas['laba'])}", ln=True, align='R')
    pdf.line(110, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "LABA BERSIH OPERASIONAL"); pdf.cell(90, 10, format_rp(data_ringkas['laba']), ln=True, align='R')
    pdf.ln(5)

    # Section 2: Perubahan Modal
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "II. LAPORAN PERUBAHAN MODAL", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 10, "Modal Awal Periode"); pdf.cell(90, 10, format_rp(data_ringkas['modal_awal']), ln=True, align='R')
    pdf.cell(100, 10, "Ditambah: Laba Bersih"); pdf.cell(90, 10, format_rp(data_ringkas['laba']), ln=True, align='R')
    pdf.cell(100, 10, "Dikurangi: Pengambilan Pribadi (Prive)"); pdf.cell(90, 10, f"- {format_rp(data_ringkas['prive'])}", ln=True, align='R')
    pdf.line(110, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "MODAL AKHIR PERIODE"); pdf.cell(90, 10, format_rp(data_ringkas['modal_akhir']), ln=True, align='R')
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, f"Dicetak otomatis melalui FIN-Saku pada {datetime.now().strftime('%d/%m/%Y %H:%M')}", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; color: #000000 !important;
    }
    .white-card * { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "Warung Maju Jaya")
    sektor = st.selectbox("Sektor:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    modal_awal = clean_to_int(st.text_input("Modal Awal (Kas)", "5000000"))
    
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "10000"))
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard: {nama_u}")

# --- INPUT TRANSAKSI DENGAN TAHUN ---
st.subheader("📝 Input Penjualan")
rekap_mode = st.radio("Pilih Periode:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col1, col2 = st.columns(2)
with col1:
    tgl_ref = st.date_input("Pilih Tanggal", datetime.now())
    thn_pilih = tgl_ref.year
    bln_pilih = tgl_ref.strftime("%B")
    
    if rekap_mode == "Harian":
        val_tgl = tgl_ref.strftime("%Y-%m-%d")
        dom = tgl_ref.day
        val_minggu = f"Minggu ke-{(dom-1)//7 + 1}"
    elif rekap_mode == "Mingguan":
        dom = tgl_ref.day
        val_minggu = f"Minggu ke-{(dom-1)//7 + 1}"
        val_tgl = f"Rekap {val_minggu}"
    else:
        val_minggu = "-"
        val_tgl = f"Rekap Bulanan"
    
    val_bulan_tahun = f"{bln_pilih} {thn_pilih}"

with col2:
    omzet_in = st.number_input("Omzet (Rp)", value=0, step=10000)
    if st.button("💾 SIMPAN DATA"):
        laba_in = omzet_in * ((hrg_val - hpp_val) / hrg_val) if hrg_val > 0 else 0
        prive_in = laba_in * (prive_pct / 100)
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, tahun, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (val_tgl, val_bulan_tahun, val_minggu, thn_pilih, omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

# --- TAB LAPORAN (OUTPUT BANK) ---
if not df.empty:
    st.write("---")
    tab_lap, tab_kur = st.tabs(["📊 LAPORAN SIAP CETAK", "🏦 ANALISIS KUR"])
    
    with tab_lap:
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Periode Laporan:", list_bulan)
        
        # Hitung Data Keuangan
        data_b = df[df['bulan'] == sel_b]
        omzet_b = data_b['omzet'].sum()
        laba_b = data_b['laba'].sum()
        prive_b = data_b['prive'].sum()
        
        # Hitung Modal Awal & Akhir
        idx_b = list_bulan.index(sel_b)
        laba_lalu = df[df['bulan'].isin(list_bulan[:idx_b])]['laba'].sum()
        prive_lalu = df[df['bulan'].isin(list_bulan[:idx_b])]['prive'].sum()
        m_awal_b = modal_awal + laba_lalu - prive_lalu
        m_akhir_b = m_awal_b + laba_b - prive_b
        
        # Preview UI
        st.markdown(f"""
        <div class="white-card">
            <h3 align="center">{nama_u.upper()}</h3>
            <p align="center">LAPORAN LABA RUGI & PERUBAHAN MODAL<br>Periode: {sel_b}</p>
            <hr>
            <table width="100%">
                <tr><td>Total Omzet</td><td align="right">{format_rp(omzet_b)}</td></tr>
                <tr><td>Total Laba Bersih</td><td align="right"><b>{format_rp(laba_b)}</b></td></tr>
                <tr><td colspan="2"><hr></td></tr>
                <tr><td>Modal Awal</td><td align="right">{format_rp(m_awal_b)}</td></tr>
                <tr><td>Prive (Ambil Modal)</td><td align="right">-{format_rp(prive_b)}</td></tr>
                <tr><td><b>Modal Akhir</b></td><td align="right"><b>{format_rp(m_akhir_b)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
        # TOMBOL CETAK PDF
        data_ringkas = {
            'omzet': omzet_b, 'laba': laba_b, 'prive': prive_b, 
            'modal_awal': m_awal_b, 'modal_akhir': m_akhir_b
        }
        pdf_bytes = generate_pdf(nama_u, sel_b, data_ringkas)
        st.download_button(
            label="📥 DOWNLOAD LAPORAN PDF (SIAP KE BANK)",
            data=pdf_bytes,
            file_name=f"Laporan_{nama_u}_{sel_b.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

    with tab_kur:
        st.info("Fitur Analisis KUR Tetap Berjalan di Sini...")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from fpdf import FPDF

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v5.db', check_same_thread=False)
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

# --- FUNGSI EXPORT PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LAPORAN KEUANGAN UMKM (FIN-SAKU)', 0, 1, 'C')
        self.ln(5)

def generate_pdf(nama, periode, omzet, laba, modal_awal, modal_akhir):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nama Usaha: {nama}", ln=True)
    pdf.cell(200, 10, txt=f"Periode: {periode}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "RINGKASAN KEUANGAN", 1, 1, 'C', 1)
    pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(0, 10, format_rp(omzet), 1, 1)
    pdf.cell(100, 10, "Laba Bersih", 1); pdf.cell(0, 10, format_rp(laba), 1, 1)
    pdf.cell(100, 10, "Kas Akhir", 1); pdf.cell(0, 10, format_rp(modal_akhir), 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: #000000 !important;
    }
    .white-card * { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    df['tgl_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal", "7000000"))
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    # --- INTERFACE MARGIN ---
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.markdown(f"Margin: **{margin_pct:.1f}%**")
        if "Kuliner" in sektor and margin_pct < 40:
            st.warning("💡 Tips: Kuliner butuh margin min 40% untuk cover risiko waste/basi.")
        elif "Jasa" in sektor and margin_pct < 60:
            st.warning("💡 Tips: Jasa butuh margin >60% karena aset utamanya adalah waktu Anda.")
        else:
            st.success("✅ Margin sudah sehat untuk sektor ini.")

    prive_pct = st.slider("Jatah Pribadi (%)", 0, 50, 30)
    # --- INTERFACE PRIVE ---
    if prive_pct > 35:
        st.error("🚩 Hati-hati: Prive >35% bisa menghambat pertumbuhan modal usaha.")
    else:
        st.info("✅ Alokasi prive sudah seimbang.")

# --- INPUT TRANSAKSI ---
st.title(f"Dashboard: {nama_u}")
with st.container():
    st.subheader("📝 Catat Penjualan")
    c1, c2, c3 = st.columns([1,1,1])
    with c1: tgl_in = st.date_input("Tanggal", datetime.now())
    with c2: omzet_in = st.number_input("Total Omzet", min_value=0, step=1000)
    with c3: 
        st.write("") # Spacer
        save = st.button("🚀 SIMPAN TRANSAKSI")

if save:
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    p_in = laba_in * (prive_pct / 100)
    c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?)",
              (tgl_in.strftime("%Y-%m-%d"), tgl_in.strftime("%B %Y"), f"W-{tgl_in.isocalendar()[1]}", omzet_in, laba_in, p_in, "Harian"))
    conn.commit()
    st.rerun()

# --- BAGIAN LAPORAN (PERBAIKAN UTAMA) ---
if not df.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR", "🛠️ REVISI"])

    with tab1:
        # Pastikan list bulan unik ada
        list_bulan = sorted(df['bulan'].unique().tolist())
        sel_b = st.selectbox("Pilih Bulan:", list_bulan, index=len(list_bulan)-1)
        
        # Filter Data
        mask = df['bulan'] == sel_b
        o_bln = df[mask]['omzet'].sum()
        l_bln = df[mask]['laba'].sum()
        p_bln = df[mask]['prive'].sum()
        
        # Hitung Modal
        m_akhir = modal_awal + df['laba'].sum() - df['prive'].sum()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""<div class="white-card">
                <h3>LABA RUGI - {sel_b}</h3><hr>
                Omzet: {format_rp(o_bln)}<br>
                Laba Bersih: <b>{format_rp(l_bln)}</b>
            </div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""<div class="white-card">
                <h3>POSISI KAS</h3><hr>
                Modal Awal: {format_rp(modal_awal)}<br>
                Kas Saat Ini: <b>{format_rp(m_akhir)}</b>
            </div>""", unsafe_allow_html=True)
        
        # Tombol PDF
        pdf_file = generate_pdf(nama_u, sel_b, o_bln, l_bln, modal_awal, m_akhir)
        st.download_button("📥 SIMPAN PDF", pdf_file, f"Laporan_{sel_b}.pdf", "application/pdf")

    with tab2:
        st.subheader("🏦 Analisis Kelayakan KUR")
        # Logika KUR sederhana
        cicilan_aman = l_bln * 0.35
        st.info(f"Berdasarkan laba bulan {sel_b}, cicilan maksimal yang disarankan Bank adalah {format_rp(cicilan_aman)}/bulan.")

    with tab3:
        st.subheader("🛠️ Revisi Data")
        df_rev = df.sort_values('id', ascending=False)
        pilihan = st.selectbox("Pilih Data untuk Dihapus/Ubah:", 
                                [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
        tid = int(pilihan.split("|")[0].replace("ID:","").strip())
        if st.button("🗑️ HAPUS DATA INI"):
            c.execute("DELETE FROM transaksi WHERE id=?", (tid,))
            conn.commit()
            st.rerun()
else:
    st.info("Belum ada data. Silakan isi form di atas.")

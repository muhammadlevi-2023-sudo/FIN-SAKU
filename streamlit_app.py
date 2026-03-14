import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from fpdf import FPDF

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
# Gunakan nama db baru jika ingin benar-benar bersih, atau tetap yang lama
conn = sqlite3.connect('finsaku_pro_final.db', check_same_thread=False)
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
    pdf.cell(200, 10, txt=f"Periode Laporan: {periode}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "RINGKASAN LABA RUGI", 1, 1, 'C', 1)
    pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(0, 10, format_rp(omzet), 1, 1)
    pdf.cell(100, 10, "Laba Bersih", 1); pdf.cell(0, 10, format_rp(laba), 1, 1)
    pdf.ln(5)
    pdf.cell(0, 10, "RINGKASAN PERUBAHAN MODAL", 1, 1, 'C', 1)
    pdf.cell(100, 10, "Modal Awal", 1); pdf.cell(0, 10, format_rp(modal_awal), 1, 1)
    pdf.cell(100, 10, "Modal Akhir (Kas)", 1); pdf.cell(0, 10, format_rp(modal_akhir), 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM (NAVY & GOLD)
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
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA (Fix ValueError) ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    # 'coerce' akan mengubah tanggal rusak jadi NaT (Not a Time) agar tidak crash
    df['tgl_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df = df.dropna(subset=['tgl_dt']) # Hapus data yang tanggalnya rusak

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner (Makanan/Minuman)", "Retail (Toko Kelontong/Baju)", "Jasa (Laundry/Service)", "Produksi/Manufaktur"])
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal", "7000000"))
    
    st.write("---")
    st.subheader("⚙️ Strategi Harga")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    # INTERFACE KATA-KATA MARGIN
    if hrg_val > 0:
        margin = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin Saat Ini: **{margin:.1f}%**")
        
        # Peringatan Sektoral
        if "Kuliner" in sektor and margin < 40:
            st.warning("⚠️ Untuk Kuliner, margin di bawah 40% berisiko karena ada faktor makanan basi/waste.")
        elif "Jasa" in sektor and margin < 60:
            st.warning("⚠️ Sektor Jasa idealnya memiliki margin >60% karena modal utamanya adalah keahlian/waktu.")
        else:
            st.success("✅ Margin Anda sudah sesuai dengan standar sektor ini.")

    st.write("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)
    # INTERFACE KATA-KATA PRIVE
    if prive_pct > 35:
        st.error("🚩 **Peringatan:** Prive di atas 35% dapat menguras kas usaha dan menghambat ekspansi.")
    else:
        st.info("💡 Angka prive ini ideal untuk menjaga keseimbangan kas pribadi dan usaha.")

# --- DASHBOARD ---
st.title("Pencatatan Baru")
col1, col2 = st.columns(2)
with col1:
    tgl_in = st.date_input("Tanggal Transaksi", datetime.now())
with col2:
    omzet_in = st.number_input("Total Omzet", min_value=0)

if st.button("🚀 SIMPAN DATA KE SISTEM"):
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    p_in = laba_in * (prive_pct / 100)
    c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?)",
              (tgl_in.strftime("%Y-%m-%d"), tgl_in.strftime("%B %Y"), f"W-{tgl_in.isocalendar()[1]}", omzet_in, laba_in, p_in, "Harian"))
    conn.commit()
    st.rerun()

# --- TAB REVISI ---
if not df.empty:
    st.write("---")
    t1, t2, t3 = st.tabs(["📊 LAPORAN", "🏦 KUR ANALISIS", "🛠️ REVISI"])
    
    with t3:
        st.subheader("🛠️ Revisi Transaksi")
        df_edit = df.sort_values('tgl_dt', ascending=False)
        pilih = st.selectbox("Pilih Data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_edit.iterrows()])
        tid = int(pilih.split("|")[0].replace("ID:","").strip())
        
        row = df[df['id'] == tid].iloc[0]
        with st.expander("Edit Detail"):
            new_omzet = st.number_input("Omzet Baru", value=float(row['omzet']))
            if st.button("Simpan Perubahan"):
                # Hitung ulang laba/prive otomatis
                n_laba = new_omzet - (new_omzet * (hpp_val / hrg_val) if hrg_val > 0 else 0)
                n_prive = n_laba * (prive_pct / 100)
                c.execute("UPDATE transaksi SET omzet=?, laba=?, prive=? WHERE id=?", (new_omzet, n_laba, n_prive, tid))
                conn.commit()
                st.rerun()
            if st.button("Hapus Data"):
                c.execute("DELETE FROM transaksi WHERE id=?", (tid,))
                conn.commit()
                st.rerun()

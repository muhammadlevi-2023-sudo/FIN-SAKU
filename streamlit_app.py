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
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')

# MIGRASI KOLOM TAHUN
try:
    c.execute("SELECT tahun FROM transaksi LIMIT 1")
except sqlite3.OperationalError:
    c.execute("ALTER TABLE transaksi ADD COLUMN tahun TEXT DEFAULT '2025'")
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

def generate_pdf(nama_usaha, periode, omzet, laba, prive, m_awal, m_akhir):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"LAPORAN KEUANGAN: {nama_usaha.upper()}", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 10, f"Periode: {periode}", ln=True, align='C')
    pdf.ln(10)
    pdf.line(10, 35, 200, 35)
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, "Keterangan", border=1); pdf.cell(90, 10, "Nilai", border=1, ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    rows = [("Total Omzet", format_rp(omzet)), ("Laba Bersih", format_rp(laba)), 
            ("Prive (Ambil Modal)", format_rp(prive)), ("Kas Awal", format_rp(m_awal)), ("Kas Akhir", format_rp(m_akhir))]
    for k, v in rows:
        pdf.cell(100, 10, k, border=1); pdf.cell(90, 10, v, border=1, ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# 2. UI & DATA
st.markdown("""<style>
    .stApp { background-color: #001f3f !important; color: white !important; }
    .white-card { background-color: #ffffff !important; padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700; color: black !important; margin-bottom:10px; }
    .white-card * { color: black !important; }
    .stButton>button { background-color: #FFD700 !important; color: black !important; font-weight: bold; width: 100%; }
</style>""", unsafe_allow_html=True)

df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.title("💰 FIN-Saku")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal", "7000000"))
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Prive (%)", 0, 100, 30)

# --- INPUT ---
st.subheader("📝 Catat Transaksi")
rekap_mode = st.radio("Mode:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col_in, col_status = st.columns([1, 1.2])
with col_in:
    now = datetime.now()
    if rekap_mode == "Harian":
        d = st.date_input("Tanggal", now)
        v_bln, v_thn, v_mng = d.strftime("%B"), d.strftime("%Y"), f"Minggu ke-{((d.day-1)//7+1)}"
        v_tgl = d.strftime("%Y-%m-%d")
    elif rekap_mode == "Mingguan":
        d = st.date_input("Pilih Tanggal di Minggu tsb", now)
        v_bln, v_thn = d.strftime("%B"), d.strftime("%Y")
        v_mng = f"Minggu ke-{((d.day-1)//7+1)}"
        v_tgl = f"Rekap {v_mng} - {v_bln} {v_thn}"
    else:
        list_m = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        v_bln = st.selectbox("Bulan", list_m, index=now.month-1)
        v_thn = st.selectbox("Tahun", [str(y) for y in range(2024, 2031)], index=now.year-2024)
        v_tgl, v_mng = f"Rekap Bulanan {v_bln} {v_thn}", "-"

    omzet_in = st.number_input("Omzet", value=0)
    laba_in = omzet_in - (omzet_in * (hpp_val/hrg_val) if hrg_val > 0 else 0)
    prive_in = laba_in * (prive_pct/100) if laba_in > 0 else 0

    if st.button("SIMPAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, tahun, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?,?)",
                  (v_tgl, v_bln, v_thn, v_mng, omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_status:
    st.markdown(f'<div class="white-card"><h3>Status</h3>{v_mng} | {v_bln} {v_thn}<hr>Laba: {format_rp(laba_in)}</div>', unsafe_allow_html=True)

# --- LAPORAN ---
if not df.empty:
    st.write("---")
    t1, t2, t3 = st.tabs(["📊 LAPORAN", "🏦 KUR", "🛠️ REVISI"])
    
    with t1:
        # Perbaikan filter agar tidak error index
        all_m = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        
        c1, c2 = st.columns(2)
        with c1: sel_t = st.selectbox("Pilih Tahun:", sorted(df['tahun'].unique()), key="yr")
        
        # Bersihkan data bulan (menghapus tahun jika ada di string bulan)
        df['bulan_clean'] = df['bulan'].apply(lambda x: x.split()[0] if x.split()[0] in all_m else x)
        
        with c2: 
            list_b_filtered = df[df['tahun'] == sel_t]['bulan_clean'].unique().tolist()
            sel_b = st.selectbox("Pilih Bulan:", list_b_filtered, key="mo")
        
        db_b = df[(df['bulan_clean'] == sel_b) & (df['tahun'] == sel_t)]
        o_b, l_b, p_b = db_b['omzet'].sum(), db_b['laba'].sum(), db_b['prive'].sum()
        
        # Hitung Kumulatif Modal
        cur_m_idx = all_m.index(sel_b)
        df['m_idx'] = df['bulan_clean'].apply(lambda x: all_m.index(x) if x in all_m else 0)
        
        prior = df[(df['tahun'].astype(int) < int(sel_t)) | ((df['tahun'] == sel_t) & (df['m_idx'] < cur_m_idx))]
        m_awal_b = modal_awal + prior['laba'].sum() - prior['prive'].sum()
        m_akhir_b = m_awal_b + l_b - p_b

        st.columns(2)[0].markdown(f'<div class="white-card"><h3>LABA</h3>{format_rp(l_b)}</div>', unsafe_allow_html=True)
        st.columns(2)[1].markdown(f'<div class="white-card"><h3>KAS AKHIR</h3>{format_rp(m_akhir_b)}</div>', unsafe_allow_html=True)
        
        pdf_bytes = generate_pdf(nama_u, f"{sel_b} {sel_t}", o_b, l_b, p_b, m_awal_b, m_akhir_b)
        st.download_button("📥 PDF", pdf_bytes, f"Laporan_{sel_b}.pdf")

    with t2:
        # LOGIKA KUR TETAP SAMA
        st.subheader("Analisis KUR")
        if df['bulan_clean'].nunique() < 3: st.warning("Data belum cukup 3 bulan.")
        else:
            st.success("LAYAK!")
            tenor = st.select_slider("Tenor", [12, 24, 36])
            cicilan = (50000000/tenor) + (50000000*0.005)
            st.info(f"Cicilan: {format_rp(cicilan)}/bln")

    with t3:
        target = st.selectbox("Hapus:", [f"ID:{r['id']} | {r['tanggal']}" for _, r in df.iterrows()])
        if st.button("Hapus Data"):
            c.execute("DELETE FROM transaksi WHERE id=?", (target.split(":")[1].split("|")[0].strip(),))
            conn.commit()
            st.rerun()

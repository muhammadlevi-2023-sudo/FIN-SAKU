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

# Buat tabel jika belum ada
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')

# --- LOGIKA MIGRASI: Tambah kolom 'tahun' jika belum ada ---
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
    data_pdf = [
        ("Total Omzet", format_rp(omzet)),
        ("Laba Bersih", format_rp(laba)),
        ("Prive (Ambil Modal)", format_rp(prive)),
        ("Kas Awal", format_rp(m_awal)),
        ("Kas Akhir", format_rp(m_akhir))
    ]
    for k, v in data_pdf:
        pdf.cell(100, 10, k, border=1); pdf.cell(90, 10, v, border=1, ln=True, align='R')
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important; padding: 20px; border-radius: 12px; 
        border-left: 8px solid #FFD700; margin-bottom: 15px; color: #000000 !important;
    }
    .white-card * { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

df = pd.read_sql_query("SELECT * FROM transaksi", conn)
jumlah_bulan_data = df['bulan'].nunique() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal (Modal)", "7000000"))
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- INPUT TRANSAKSI ---
st.title(f"Dashboard: {nama_u}")
rekap_mode = st.radio("Pilih Periode Catat:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col_in, col_info = st.columns([1, 1.2])

with col_in:
    if rekap_mode == "Harian":
        tgl_i = st.date_input("Pilih Tanggal", datetime.now())
        v_tgl, v_bln, v_thn = tgl_i.strftime("%Y-%m-%d"), tgl_i.strftime("%B"), tgl_i.strftime("%Y")
        v_mng = f"Minggu ke-{((tgl_i.day - 1) // 7 + 1)}"
    elif rekap_mode == "Mingguan":
        tgl_i = st.date_input("Pilih Tanggal di Minggu tsb:", datetime.now())
        v_bln, v_thn = tgl_i.strftime("%B"), tgl_i.strftime("%Y")
        v_mng = f"Minggu ke-{((tgl_i.day - 1) // 7 + 1)}"
        v_tgl = f"Rekap {v_mng} - {v_bln} {v_thn}"
    else:
        list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        v_bln = st.selectbox("Pilih Bulan", list_bln, index=datetime.now().month - 1)
        v_thn = st.selectbox("Pilih Tahun", [str(y) for y in range(2024, 2031)], index=datetime.now().year - 2024)
        v_tgl, v_mng = f"Rekap Bulanan {v_bln} {v_thn}", "-"

    omzet_in = st.number_input("Total Omzet Penjualan", value=0, step=10000)
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🔔 SIMPAN TRANSAKSI"):
        if omzet_in > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, tahun, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                      (v_tgl, v_bln, v_thn, v_mng, omzet_in, laba_in, prive_in, rekap_mode))
            conn.commit()
            st.success("Data Tersimpan!")
            st.rerun()

with col_info:
    st.markdown(f"""<div class="white-card">
        <h3>📢 Status</h3><p><b>{v_mng}</b> | <b>{v_bln} {v_thn}</b></p>
        <hr><p>Laba: <b>{format_rp(laba_in)}</b><br>Prive: <b>{format_rp(prive_in)}</b></p>
    </div>""", unsafe_allow_html=True)

# --- TABS ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        col1, col2 = st.columns(2)
        with col1: s_t = st.selectbox("Tahun:", sorted(df['tahun'].unique()), index=len(df['tahun'].unique())-1)
        with col2: 
            list_b = df[df['tahun'] == s_t]['bulan'].unique().tolist()
            s_b = st.selectbox("Bulan:", list_b, index=len(list_b)-1)
        
        db_b = df[(df['bulan'] == s_b) & (df['tahun'] == s_t)]
        o_b, l_b, p_b = db_b['omzet'].sum(), db_b['laba'].sum(), db_b['prive'].sum()
        
        # Hitung akumulasi untuk Modal Awal
        all_m = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        cur_idx = all_m.index(s_b)
        prior = df[(df['tahun'].astype(int) < int(s_t)) | ((df['tahun'] == s_t) & (df['bulan'].apply(lambda x: all_m.index(x)) < cur_idx))]
        
        m_awal_b = modal_awal + prior['laba'].sum() - prior['prive'].sum()
        m_akhir_b = m_awal_b + l_b - p_b

        st.columns(2)[0].markdown(f'<div class="white-card"><h3>LABA - {s_b}</h3>Omzet: {format_rp(o_b)}<br>Laba: <b>{format_rp(l_b)}</b></div>', unsafe_allow_html=True)
        st.columns(2)[1].markdown(f'<div class="white-card"><h3>MODAL - {s_b}</h3>Awal: {format_rp(m_awal_b)}<br>Akhir: <b>{format_rp(m_akhir_b)}</b></div>', unsafe_allow_html=True)
        
        pdf_file = generate_pdf(nama_u, f"{s_b} {s_t}", o_b, l_b, p_b, m_awal_b, m_akhir_b)
        st.download_button("📥 DOWNLOAD PDF", data=pdf_file, file_name=f"Laporan_{s_b}.pdf")

    with tab_kur:
        st.subheader("🏦 Konsultasi KUR")
        if jumlah_bulan_data < 3:
            st.error(f"Butuh {3-jumlah_bulan_data} bulan data lagi.")
        else:
            st.success("✅ STATUS: LAYAK")
            tenor = st.select_slider("Tenor (Bulan):", options=[12, 18, 24, 36])
            cicilan = (50000000 / tenor) + ((50000000 * 0.06) / 12)
            st.markdown(f'<div class="white-card">Estimasi Cicilan: {format_rp(cicilan)}/bln</div>', unsafe_allow_html=True)

    with tab_rev:
        target = st.selectbox("Hapus data:", [f"ID:{r['id']} | {r['tanggal']}" for _, r in df.sort_values(by='id', ascending=False).iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Mari mulai catat transaksi pertama Anda.")

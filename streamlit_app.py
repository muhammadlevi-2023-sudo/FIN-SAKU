import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI UTAMA
st.set_page_config(page_title="FIN-Saku Pro | Akuntansi Berkelanjutan", layout="wide")

def get_connection():
    conn = sqlite3.connect('finsaku_unair_v17.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi
                 (id INTEGER PRIMARY KEY, urutan INTEGER, tgl_input TEXT, bulan TEXT, tahun TEXT, 
                  tipe TEXT, omzet REAL, laba REAL, prive REAL)''')
    conn.commit()
    return conn

conn = get_connection()

# 2. UI STYLING (NAVY & GOLD)
st.markdown("""
<style>
    .stApp { background-color: #002147; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #001a35 !important; border-right: 3px solid #FFD700; }
    .report-card {
        background: #FFFFFF; padding: 30px; border-radius: 12px;
        border-left: 10px solid #FFD700; color: #333 !important;
        margin-bottom: 25px; box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
    .report-card h3, .report-card b, .report-card span { color: #002147 !important; }
    .stButton>button {
        background: #FFD700 !important; color: #002147 !important;
        font-weight: bold; border-radius: 8px; border: none; height: 45px;
    }
</style>
""", unsafe_allow_html=True)

# 3. FUNGSI PENDUKUNG
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_val(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 4. SIDEBAR: PROFIL & LOGIKA MODAL MENGALIR
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    m_awal_input = st.number_input("Modal Awal Investasi (Rp)", value=7000000)
    
    st.write("---")
    hpp = st.number_input("HPP Satuan", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    margin_pct = ((jual - hpp) / jual) if jual > 0 else 0
    prive_pct = st.slider("Alokasi Prive (%)", 0, 100, 30)

# 5. LOGIKA PERHITUNGAN MODAL BERKELANJUTAN (CORE ENGINE)
df_raw = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id ASC", conn)

def hitung_ekuitas_berjalan(df, modal_investasi):
    modal_saat_ini = modal_investasi
    history_modal = []
    
    for index, row in df.iterrows():
        laba_bersih_transaksi = row['laba'] - row['prive']
        modal_saat_ini += laba_bersih_transaksi
        history_modal.append(modal_saat_ini)
    
    df['modal_snapshot'] = history_modal
    return df, modal_saat_ini

df_final, kas_realtime = hitung_ekuitas_berjalan(df_raw, m_awal_input)

with st.sidebar:
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border:1px solid #FFD700;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>MODAL/KAS REALTIME:</p>
        <h2 style='margin:0; color:white;'>{format_rp(kas_realtime)}</h2>
    </div>
    """, unsafe_allow_html=True)

# 6. INPUT TRANSAKSI
st.title(f"Dashboard {nama_u}")
with st.expander("➕ CATAT TRANSAKSI BARU", expanded=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        tipe = st.selectbox("Jenis", ["Harian", "Mingguan", "Bulanan"])
        list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        sel_bln = st.selectbox("Bulan", list_bln, index=datetime.now().month-1)
    with c2:
        sel_thn = st.selectbox("Tahun", ["2025", "2026", "2027"], index=1)
        omzet_raw = st.text_input("Input Omzet")
        omzet_val = clean_val(omzet_raw)
        st.caption(f"Tercatat: {format_rp(omzet_val)}")
    with c3:
        st.write("##")
        if st.button("SIMPAN DATA"):
            laba_val = omzet_val * margin_pct
            prive_val = laba_val * (prive_pct/100)
            c = conn.cursor()
            c.execute("INSERT INTO transaksi (urutan, tgl_input, bulan, tahun, tipe, omzet, laba, prive) VALUES (?,?,?,?,?,?,?,?)",
                      (int(datetime.now().timestamp()), datetime.now().strftime("%Y-%m-%d"), sel_bln, sel_thn, tipe, omzet_val, laba_val, prive_val))
            conn.commit()
            st.rerun()

# 7. LAPORAN KEUANGAN BANKABLE
if not df_final.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR", "⚙️ REVISI"])
    
    with tab1:
        sel_lap = st.selectbox("Pilih Periode Laporan", df_final['bulan'].unique())
        
        # Filter data bulan ini
        df_curr = df_final[df_final['bulan'] == sel_lap]
        
        # Hitung angka-angka kunci
        omzet_bln = df_curr['omzet'].sum()
        laba_kotor = df_curr['laba'].sum()
        prive_bln = df_curr['prive'].sum()
        laba_bersih_bln = laba_kotor - prive_bln
        
        # Logika Modal: Ambil modal sebelum bulan ini dimulai
        idx_awal = df_curr.index[0]
        modal_awal_bln = df_final.iloc[idx_awal-1]['modal_snapshot'] if idx_awal > 0 else m_awal_input
        modal_akhir_bln = df_curr.iloc[-1]['modal_snapshot']

        # UI LAPORAN LABA RUGI
        st.markdown(f"""
        <div class="report-card">
            <h3 style="text-align:center;">LAPORAN LABA RUGI</h3>
            <p style="text-align:center; margin-top:-15px;">Periode: {sel_lap} {sel_thn}</p>
            <hr>
            <div style="display:flex; justify-content:space-between;"><span>Total Omzet</span><b>{format_rp(omzet_bln)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Laba Usaha (Margin)</span><b>{format_rp(laba_kotor)}</b></div>
            <div style="display:flex; justify-content:space-between; color:red;"><span>Prive (Gaji Pemilik)</span><b>-{format_rp(prive_bln)}</b></div>
            <hr>
            <div style="display:flex; justify-content:space-between; font-size:1.2rem;"><b>LABA BERSIH BULAN INI</b><b style="color:green;">{format_rp(laba_bersih_bln)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # UI LAPORAN PERUBAHAN MODAL
        st.markdown(f"""
        <div class="report-card" style="border-left-color: #002147;">
            <h3 style="text-align:center;">LAPORAN PERUBAHAN MODAL</h3>
            <hr>
            <div style="display:flex; justify-content:space-between;"><span>Modal Awal Periode</span><b>{format_rp(modal_awal_bln)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Penambahan (Laba Bersih)</span><b>{format_rp(laba_bersih_bln)}</b></div>
            <hr>
            <div style="display:flex; justify-content:space-between; font-size:1.4rem; background:#FFD700; padding:10px; border-radius:5px;">
                <b>MODAL AKHIR</b><b>{format_rp(modal_akhir_bln)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # DOWNLOAD PDF DI BAWAH MODAL
        if st.button("📥 DOWNLOAD LAPORAN (PDF)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"LAPORAN KEUANGAN {nama_u.upper()}", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 7, f"Dicetak pada: {datetime.now().strftime('%d %B %Y')}", 0, 1, 'C')
            pdf.ln(10)
            
            # Table Laba Rugi
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "1. LAPORAN LABA RUGI", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 10, "Omzet", 1); pdf.cell(90, 10, format_rp(omzet_bln), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Bersih", 1); pdf.cell(90, 10, format_rp(laba_bersih_bln), 1, 1, 'R')
            pdf.ln(5)
            
            # Table Modal
            pdf.set_font("Arial", 'B', 12); pdf.cell(190, 10, "2. LAPORAN PERUBAHAN MODAL", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 10, "Modal Awal Periode", 1); pdf.cell(90, 10, format_rp(modal_awal_bln), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Ditahan", 1); pdf.cell(90, 10, format_rp(laba_bersih_bln), 1, 1, 'R')
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "MODAL AKHIR", 1); pdf.cell(90, 10, format_rp(modal_akhir_bln), 1, 1, 'R')
            
            st.download_button("Klik untuk Simpan PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{sel_lap}.pdf")

    with tab2:
        st.subheader("🏦 Kelayakan KUR BRI")
        # Analisis Credit Scoring berdasarkan Modal Akhir
        st.write(f"Berdasarkan Modal Akhir Anda ({format_rp(modal_akhir_bln)}), Berikut analisis kami:")
        if modal_akhir_bln > m_awal_input:
            st.success("✅ Bisnis Anda bertumbuh secara organik. Skor Kredit: TINGGI.")
        else:
            st.warning("⚠️ Bisnis sedang mengalami penurunan modal. Perbaiki margin sebelum meminjam.")

    with tab3:
        st.subheader("🛠️ Revisi Data")
        st.dataframe(df_final[['id', 'bulan', 'omzet', 'laba', 'modal_snapshot']])
        target_id = st.number_input("Masukkan ID untuk hapus", step=1)
        if st.button("Hapus Permanen"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (target_id,))
            conn.commit()
            st.rerun()

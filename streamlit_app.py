import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. INITIAL SETUP
st.set_page_config(page_title="FIN-Saku | UMKM Bankable Dashboard", layout="wide")

# Database Management (Auto-Migration)
def get_connection():
    conn = sqlite3.connect('finsaku_master_v16.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi
                 (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, tahun TEXT, 
                  tipe_catat TEXT, omzet REAL, laba REAL, prive REAL, hpp REAL, harga_jual REAL)''')
    conn.commit()
    return conn

conn = get_connection()

# 2. UI STYLING (UNAIR NAVY & GOLD)
st.markdown("""
<style>
    .stApp { background-color: #002147; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #001a35 !important; border-right: 3px solid #FFD700; }
    h1, h2, h3, p, label { color: #FFFFFF !important; }
    .gold-label { color: #FFD700 !important; font-weight: bold; }
    
    .modern-card {
        background: #FFFFFF; padding: 25px; border-radius: 15px;
        border-top: 8px solid #FFD700; color: #002147 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4); margin-bottom: 20px;
    }
    .modern-card span, .modern-card b, .modern-card h3 { color: #002147 !important; }

    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%) !important;
        color: #002147 !important; font-weight: bold; border-radius: 8px;
        height: 50px; width: 100%; border: none;
    }
</style>
""", unsafe_allow_html=True)

# 3. HELPER FUNCTIONS
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_val(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 4. SIDEBAR: PROFIL & INTERAKTIF MARGIN/PRIVE
df_all = pd.read_sql_query("SELECT * FROM transaksi", conn)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    nama_usaha = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    kas_awal = st.number_input("Modal Kas Awal (Rp)", value=7000000)
    
    # Real-time Cash Logic
    untung_bersih = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_sekarang = kas_awal + untung_bersih
    
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border-left:5px solid #FFD700;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>KAS SAAT INI (REALTIME)</p>
        <h2 style='margin:0;'>{format_rp(kas_sekarang)}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    val_hpp = st.number_input("HPP Produk", value=5000)
    val_jual = st.number_input("Harga Jual", value=15000)
    
    margin = ((val_jual - val_hpp) / val_jual * 100) if val_jual > 0 else 0
    st.markdown(f"Margin: <span class='gold-label'>{margin:.1f}%</span>", unsafe_allow_html=True)
    
    # Peringatan Margin (Interaktif)
    if margin < 30:
        st.error("⚠️ Margin < 30%! Bank BRI biasanya menolak usaha dengan profitabilitas rendah.")
    elif margin >= 50:
        st.success("✅ Margin sangat sehat untuk ekspansi!")

    st.write("---")
    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 30)
    
    # Peringatan Prive (Interaktif)
    if prive_pct > 50:
        st.error("🚨 BAHAYA: Prive > 50% laba akan menguras modal kerja. Bank sangat tidak menyukai ini!")
    elif prive_pct <= 20:
        st.info("💡 Prive rendah mempercepat pertumbuhan modal usaha.")

# 5. DASHBOARD: PENCATATAN MODERN (HARIAN/MINGGUAN/BULANAN)
st.title(f"🚀 Kendali Bisnis: {nama_usaha}")

with st.container():
    st.subheader("📝 Pencatatan Transaksi")
    col_tgl, col_omz, col_btn = st.columns([2, 2, 1])
    
    with col_tgl:
        tipe_catat = st.selectbox("Jenis Pencatatan", ["Harian", "Mingguan", "Bulanan"])
        list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        
        c_bln, c_thn = st.columns(2)
        sel_bln = c_bln.selectbox("Bulan", list_bln, index=datetime.now().month - 1)
        sel_thn = c_thn.selectbox("Tahun", ["2024", "2025", "2026", "2027"], index=2)
        
    with col_omz:
        omzet_raw = st.text_input(f"Total Omzet ({tipe_catat})")
        omzet_in = clean_val(omzet_raw)
        st.markdown(f"Tercatat: <span class='gold-label'>{format_rp(omzet_in)}</span>", unsafe_allow_html=True)
        
    with col_btn:
        st.write("##")
        if st.button("SIMPAN"):
            l_in = omzet_in * (margin/100)
            p_in = l_in * (prive_pct/100)
            tgl_full = f"{datetime.now().day} {sel_bln} {sel_thn}" if tipe_catat == "Harian" else f"{sel_bln} {sel_thn}"
            
            cur = conn.cursor()
            cur.execute("INSERT INTO transaksi (tanggal, bulan, tahun, tipe_catat, omzet, laba, prive, hpp, harga_jual) VALUES (?,?,?,?,?,?,?,?,?)",
                      (tgl_full, sel_bln, sel_thn, tipe_catat, omzet_in, l_in, p_in, val_hpp, val_jual))
            conn.commit()
            st.toast("Data Berhasil Diamankan!", icon="✅")
            st.rerun()

# 6. LAPORAN, KUR, & PDF
if not df_all.empty:
    st.write("---")
    t1, t2, t3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "⚙️ REVISI DATA"])
    
    with t1:
        f_bln = st.selectbox("Pilih Periode Laporan:", df_all['bulan'].unique())
        df_v = df_all[df_all['bulan'] == f_bln]
        
        o_t = df_v['omzet'].sum(); l_t = df_v['laba'].sum(); p_t = df_v['prive'].sum()
        laba_bersih = l_t - p_t

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div class="modern-card">
                <h3 style="text-align:center;">LABA RUGI - {f_bln.upper()}</h3>
                <hr>
                <div style="display:flex; justify-content:space-between;"><span>Omzet</span><b>{format_rp(o_t)}</b></div>
                <div style="display:flex; justify-content:space-between;"><span>Laba Usaha</span><b>{format_rp(l_t)}</b></div>
                <div style="display:flex; justify-content:space-between; color:red;"><span>Prive Pemilik</span><b>-{format_rp(p_t)}</b></div>
                <hr>
                <div style="display:flex; justify-content:space-between;"><b>SISA LABA</b><b style="color:green;">{format_rp(laba_bersih)}</b></div>
            </div>
            """, unsafe_allow_html=True)
            
            # --- PDF GENERATOR ---
            if st.button("📥 DOWNLOAD PDF LAPORAN"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(190, 10, f"LAPORAN KEUANGAN: {nama_usaha.upper()}", 0, 1, 'C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(190, 7, f"Periode: {f_bln} {sel_thn}", 0, 1, 'C')
                pdf.ln(10)
                
                # Header Table
                pdf.set_fill_color(0, 33, 71) # Navy
                pdf.set_text_color(255, 255, 255) # White
                pdf.cell(100, 10, "KOMPONEN", 1, 0, 'C', True)
                pdf.cell(90, 10, "NILAI", 1, 1, 'C', True)
                
                # Content Table
                pdf.set_text_color(0, 0, 0)
                pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(90, 10, format_rp(o_t), 1, 1, 'R')
                pdf.cell(100, 10, "Laba Operasional", 1); pdf.cell(90, 10, format_rp(l_t), 1, 1, 'R')
                pdf.cell(100, 10, "Prive (Gaji Pemilik)", 1); pdf.cell(90, 10, f"-{format_rp(p_t)}", 1, 1, 'R')
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(100, 10, "TOTAL KAS AKHIR", 1); pdf.cell(90, 10, format_rp(kas_sekarang), 1, 1, 'R')
                
                st.download_button("Konfirmasi Download PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{nama_usaha}_{f_bln}.pdf")

        with col_b:
            st.markdown(f"""
            <div class="modern-card">
                <h3 style="text-align:center;">STRUKTUR MODAL</h3>
                <hr>
                <p>Kas Awal: <b>{format_rp(kas_awal)}</b></p>
                <p>Pertumbuhan Laba: <b>{format_rp(df_all['laba'].sum() - df_all['prive'].sum())}</b></p>
                <hr>
                <p>Total Modal Saat Ini:</p>
                <h2 style="color:#002147;">{format_rp(kas_sekarang)}</h2>
            </div>
            """, unsafe_allow_html=True)

    with t2:
        st.subheader("🏦 Analisis KUR Bank BRI")
        histori = df_all['bulan'].nunique()
        
        # Logika Plafon Berdasarkan Kas
        plafon_saran = 10000000 if kas_sekarang < 20000000 else 50000000
        status_k = "LAYAK" if histori >= 3 and laba_bersih > (plafon_saran*0.05) else "BUTUH PENYESUAIAN"
        
        st.markdown(f"""
        <div class="modern-card">
            <h4>Hasil Analisis Credit Scoring</h4>
            <p>Rekomendasi Produk: <b>KUR Mikro BRI</b></p>
            <p>Plafon Disarankan: <b>{format_rp(plafon_saran)}</b></p>
            <p>Status: <b style="color:{'green' if status_k == 'LAYAK' else 'red'};">{status_k}</b></p>
            <hr>
            <b>Saran Strategis:</b><br>
            {"Pertahankan omzet stabil selama 3 bulan ke depan agar skor kredit sempurna." if histori < 3 else "Arus kas Anda sudah memenuhi syarat administrasi Bank BRI."}
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.subheader("⚙️ Revisi Data")
        st.dataframe(df_all[['id', 'tanggal', 'tipe_catat', 'omzet', 'laba']], use_container_width=True)
        t_id = st.number_input("Masukkan ID untuk dihapus", step=1)
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (t_id,))
            conn.commit()
            st.rerun()
else:
    st.info("Input transaksi pertama Anda untuk melihat laporan interaktif.")

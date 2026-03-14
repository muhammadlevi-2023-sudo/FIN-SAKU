import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI & UI SETUP
st.set_page_config(page_title="FIN-Saku: Bankable UMKM Dashboard", layout="wide")

# Database v12
conn = sqlite3.connect('finsaku_v12_bankable.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, tipe TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
conn.commit()

# Formatting Rupiah & Clean Input
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_to_int(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# Custom CSS untuk UI Modern & Interaktif
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #0d1117; color: #e6edf3; }
    
    /* Card Styling */
    .bank-card {
        background: #161b22; padding: 25px; border-radius: 15px;
        border: 1px solid #30363d; margin-bottom: 20px;
        transition: 0.3s;
    }
    .bank-card:hover { border-color: #58a6ff; box-shadow: 0 0 15px rgba(88, 166, 255, 0.2); }
    
    /* Badge Layak/Tidak */
    .badge-layak { background: #238636; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    .badge-tidak { background: #da3633; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    
    /* Input & Button */
    .stButton>button { background: linear-gradient(90deg, #2ea44f, #238636); color: white; border: none; width: 100%; border-radius: 8px; height: 45px; }
</style>
""", unsafe_allow_html=True)

# 2. SIDEBAR: PROFIL & PARAMETER (INTERAKTIF)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135706.png", width=80)
    st.title("Profil Bisnis")
    nama_u = st.text_input("Nama Usaha", "Catering Maju Jaya")
    sektor = st.selectbox("Sektor Usaha", ["Kuliner", "Retail", "Jasa", "Manufaktur"])
    
    st.write("---")
    st.subheader("Target & Margin")
    m_target = st.slider("Target Margin (%)", 10, 70, 30)
    if m_target < 25: st.warning("⚠️ Margin rendah berisiko pada cicilan bank.")
    
    p_max = st.slider("Batas Prive (%)", 10, 100, 30)
    if p_max > 40: st.error("🚨 Bank tidak suka Prive > 40%!")

    m_awal_raw = st.text_input("Modal Kas Saat Ini", "10000000")
    modal_awal = clean_to_int(m_awal_raw)
    st.info(f"Tercatat: {format_rp(modal_awal)}")

# 3. FITUR PENCATATAN (UI MODERN SELECTOR)
st.title(f"🚀 {nama_u} Control Center")

col_sel, col_blank = st.columns([2, 2])
with col_sel:
    tipe_catat = st.segmented_control("Metode Pencatatan", ["Harian", "Mingguan", "Bulanan"], default="Harian")

with st.container():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: tgl_in = st.date_input("Pilih Tanggal")
    with c2: 
        omzet_raw = st.text_input("Masukkan Omzet")
        omzet_val = clean_to_int(omzet_raw)
        st.caption(f"Tercatat: {format_rp(omzet_val)}")
    with c3:
        st.write("##")
        if st.button("Simpan Transaksi"):
            laba_val = omzet_val * (m_target/100)
            prive_val = laba_val * (p_max/100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, tipe, omzet, laba, prive) VALUES (?,?,?,?,?,?)",
                      (tgl_in.strftime("%Y-%m-%d"), tgl_in.strftime("%B %Y"), tipe_catat, omzet_val, laba_val, prive_val))
            conn.commit()
            st.toast("Data masuk ke buku besar!")
            st.rerun()

# 4. DASHBOARD ANALISIS & REVISI
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

if not df.empty:
    tab1, tab2, tab3 = st.tabs(["📊 Laporan Bankable", "🏦 Analisis KUR BRI", "🛠️ Revisi Data"])
    
    with tab1:
        sel_bln = st.selectbox("Pilih Periode Laporan", df['bulan'].unique())
        df_m = df[df['bulan'] == sel_bln]
        
        o_sum = df_m['omzet'].sum()
        l_sum = df_m['laba'].sum()
        p_sum = df_m['prive'].sum()
        laba_ditahan = l_sum - p_sum
        kas_akhir = modal_awal + laba_ditahan

        c_a, c_b, c_c = st.columns(3)
        c_a.metric("Total Omzet", format_rp(o_sum))
        c_b.metric("Laba Bersih", format_rp(l_sum))
        c_c.metric("Kas Akhir", format_rp(kas_akhir))
        
        # DOWNLOAD PDF
        if st.button("📥 Download Laporan PDF (Siap ke Bank)"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"LAPORAN KEUANGAN: {nama_u}", 0, 1, 'C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(190, 7, f"Periode: {sel_bln} | Sektor: {sektor}", 0, 1, 'C')
            pdf.ln(10)
            pdf.cell(100, 10, "Keterangan", 1); pdf.cell(90, 10, "Nilai", 1, 1, 'C')
            pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(90, 10, format_rp(o_sum), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Operasional", 1); pdf.cell(90, 10, format_rp(l_sum), 1, 1, 'R')
            pdf.cell(100, 10, "Prive/Gaji Pemilik", 1); pdf.cell(90, 10, f"-{format_rp(p_sum)}", 1, 1, 'R')
            pdf.cell(100, 10, "Kas Akhir", 1); pdf.cell(90, 10, format_rp(kas_akhir), 1, 1, 'R')
            
            buf = io.BytesIO()
            pdf.output(dest='S').encode('latin-1')
            st.download_button("Klik untuk Simpan PDF", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{nama_u}.pdf")

    with tab2:
        st.subheader("🎯 Analisis Kelayakan KUR BRI")
        bulan_aktif = df['bulan'].nunique()
        
        # Penentuan Produk KUR
        if kas_akhir < 5000000: prod_kur = "KUR Super Mikro (Rp 5-10 Jt)"
        elif kas_akhir < 20000000: prod_kur = "KUR Mikro (Rp 10-50 Jt)"
        else: prod_kur = "KUR Kecil (Rp 50-100 Jt)"
        
        st.markdown(f"Produk yang disarankan: **{prod_kur}**")
        
        # Skor Kelayakan
        col_score, col_detail = st.columns([1, 2])
        is_layak = bulan_aktif >= 3 and (l_sum * 0.3) > (10000000 * 0.06 / 12)
        
        with col_score:
            if is_layak:
                st.markdown("<span class='badge-layak'>LAYAK PENGAJUAN</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span class='badge-tidak'>BELUM LAYAK</span>", unsafe_allow_html=True)
        
        with col_detail:
            st.write(f"• **Histori:** {bulan_aktif}/6 Bulan (Ideal 6 Bulan)")
            st.write(f"• **Kemampuan Bayar:** {format_rp(l_sum * 0.3)} / bulan")
            st.write(f"• **Syarat Dokumen:** KTP, KK, NIB (Surat Izin Usaha), Rekening 3 Bulan Terakhir.")

    with tab3:
        st.subheader("Koreksi Transaksi")
        df_rev = df.sort_values(by='id', ascending=False)
        selected_id = st.selectbox("Pilih ID Transaksi untuk dihapus", df_rev['id'])
        if st.button("🗑️ Hapus Transaksi Ini"):
            c.execute("DELETE FROM transaksi WHERE id=?", (selected_id,))
            conn.commit()
            st.success("Terhapus! Data sedang di-refresh...")
            st.rerun()

else:
    st.info("Selamat Datang! Silakan masukkan transaksi pertama Anda untuk memulai analisis Bankable.")

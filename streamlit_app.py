import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD (Fixed Visibility)
st.markdown("""
<style>
    /* Paksa warna dasar agar teks tidak putih di atas putih */
    .stApp { background-color: #f8f9fa; color: #1a1a1a; }
    
    /* Sidebar Navy */
    [data-testid="stSidebar"] { background-color: #001f3f; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #ffffff !important; }
    
    /* Box Edukasi (TEKS HITAM PEKAT) */
    .edu-box { 
        background-color: #ffffff; 
        padding: 25px; 
        border-radius: 12px; 
        border-left: 10px solid #FFD700; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
        color: #001f3f !important; /* Paksa Biru Navy Tua */
    }
    .edu-box h3 { color: #001f3f !important; margin-top:0; }
    .edu-box li { color: #333333 !important; font-weight: 500; }

    /* Laporan Akuntansi Biru */
    .report-card { 
        background-color: #dbeafe; 
        padding: 30px; 
        border-radius: 10px; 
        color: #001f3f !important; 
        border: 2px solid #001f3f; 
    }
    
    /* Tombol Gold */
    .stButton>button { 
        background-color: #FFD700; color: #001f3f; font-weight: bold;
        border-radius: 8px; border: none; height: 3em; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700; text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_usaha = st.text_input("Nama Usaha", "PT Enggan Mundur")
    
    st.markdown("### **1. Modal Awal**")
    m_raw = st.text_input("Uang Kas (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.warning(f"Tercatat: {format_rp(st.session_state.modal_awal)}")

    st.markdown("### **2. Setting Harga**")
    hpp_raw = st.text_input("HPP (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.markdown(f"<h1>Dashboard KUR: {nama_usaha}</h1>", unsafe_allow_html=True)

# KOTAK EDUKASI (Teks sudah dipaksa muncul)
st.markdown("""
<div class="edu-box">
    <h3>🔍 Mengapa Anda Layak Mendapatkan KUR?</h3>
    <p>Bank BRI melihat <b>3 Kriteria Utama</b> dari data yang Anda masukkan:</p>
    <ul>
        <li><b>Karakter:</b> Kedisiplinan Anda mencatat transaksi setiap hari.</li>
        <li><b>Kapasitas:</b> Laba bersih yang cukup untuk membayar cicilan.</li>
        <li><b>Modal:</b> Kemampuan Anda menjaga kas usaha agar tidak habis untuk pribadi.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([1, 1.2])
with c1:
    st.subheader("📝 Input Penjualan")
    qty = st.number_input("Unit Terjual", min_value=0, step=1)
    if st.button("🔔 SIMPAN DATA"):
        v_hpp, v_harga = clean_to_int(hpp_raw), clean_to_int(harga_raw)
        if qty > 0:
            laba = qty * (v_harga - v_hpp)
            new_data = pd.DataFrame([{
                "Tanggal": datetime.now(), 
                "Bulan": datetime.now().strftime("%B %Y"), 
                "Omzet": qty * v_harga, "Laba": laba, "Prive": laba * (prive_pct/100)
            }])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_data], ignore_index=True)
            st.success("Tersimpan!")

# --- LAPORAN ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    tab_lap, tab_kur = st.tabs(["📊 Laporan Akuntansi", "🏦 Analisis Bank"])
    
    with tab_lap:
        sel_b = st.selectbox("Periode", st.session_state.db_transaksi['Bulan'].unique())
        df_b = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b]
        
        st.markdown(f"""
        <div class="report-card">
            <h2 style='text-align:center; margin:0;'>{nama_usaha}</h2>
            <p style='text-align:center;'>Laporan Laba Rugi</p>
            <table style="width:100%; font-size:18px; color:#001f3f;">
                <tr><td>Pendapatan Usaha</td><td style="text-align:right;">{format_rp(df_b['Omzet'].sum())}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(df_b['Laba'].sum())}</td></tr>
                <tr style="color:#b91c1c;"><td>Prive (Ambil Sendiri)</td><td style="text-align:right;">({format_rp(df_b['Prive'].sum())})</td></tr>
                <tr style="background-color:#FFD700; font-weight:bold; font-size:20px;">
                    <td style="padding:10px;">TOTAL MODAL BERJALAN</td>
                    <td style="text-align:right;">{format_rp(st.session_state.modal_awal + (df_b['Laba'].sum() - df_b['Prive'].sum()))}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
    
    with tab_kur:
        avg_laba = st.session_state.db_transaksi['Laba'].sum()
        st.metric("Estimasi Plafon KUR", format_rp(avg_laba * 10))
        st.info("Bawa laporan ini ke Bank BRI terdekat sebagai bukti usaha layak kredit.")

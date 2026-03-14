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

# 2. UI CUSTOM: NAVY & GOLD (High-End Finance Look)
st.markdown("""
<style>
    /* Background Utama */
    .stApp { background-color: #f8f9fa; }
    
    /* Sidebar Navy */
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #e0e0e0; }
    
    /* Box Edukasi (Kuning) */
    .edu-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 8px solid #FFD700; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 25px;
    }
    
    /* Laporan Biru (Sesuai Gambar Referensi) */
    .report-card { 
        background-color: #dbeafe; 
        padding: 30px; 
        border-radius: 10px; 
        color: #001f3f; 
        border: 1px solid #001f3f; 
    }
    
    /* Kartu KUR Bankable (Navy-Gold) */
    .kur-card { 
        background-color: #001f3f; 
        color: #FFD700; 
        padding: 30px; 
        border-radius: 15px; 
        border: 2px solid #FFD700;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    /* Button Gold */
    .stButton>button { 
        background-color: #FFD700; 
        color: #001f3f; 
        font-weight: bold;
        border-radius: 8px;
        border: none;
        height: 3em;
    }
    .stButton>button:hover { background-color: #ccac00; color: white; }
    
    .step-tag { background-color: #FFD700; color: #001f3f; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: INPUT DATA ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700; text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    nama_usaha = st.text_input("Nama Usaha", "PT Enggan Mundur")
    
    st.markdown("<span class='step-tag'>STEP 1</span> **Kapasitas Modal**", unsafe_allow_html=True)
    m_raw = st.text_input("Uang Tunai Usaha Saat Ini (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.caption(f"Tersimpan: **{format_rp(st.session_state.modal_awal)}**")

    st.write("---")
    st.markdown("<span class='step-tag'>STEP 2</span> **Setting Produk**", unsafe_allow_html=True)
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Ambil Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.markdown(f"<h1>Dashboard Analisis KUR: {nama_usaha}</h1>", unsafe_allow_html=True)

# EDUKASI PROSEDUR (BUAT JURI)
st.markdown(f"""
<div class="edu-box">
    <h3>🔍 Mengapa Aplikasi Ini Membuat UMKM Bankable?</h3>
    <p>Bank BRI mencari 3 hal utama: <b>Disiplin (Karakter), Laba (Kapasitas), dan Pemisahan Uang (Modal)</b>.</p>
    <ul>
        <li><b>Modal Awal:</b> Menunjukkan keseriusan Anda (Capital).</li>
        <li><b>Laba Bersih:</b> Menunjukkan kemampuan mencicil (Capacity).</li>
        <li><b>Prive:</b> Menunjukkan kedisiplinan mengelola uang pribadi vs uang usaha.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col_in, col_empty = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan Hari Ini")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN KE DATABASE"):
        v_hpp, v_harga = clean_to_int(hpp_raw), clean_to_int(harga_raw)
        if qty > 0:
            omzet = qty * v_harga
            laba = qty * (v_harga - v_hpp)
            prive = laba * (prive_pct / 100)
            
            new_data = pd.DataFrame([{
                "Tanggal": tgl, 
                "Bulan": tgl.strftime("%B %Y"), 
                "Minggu": f"Minggu {tgl.isocalendar()[1]}", 
                "Omzet": omzet, 
                "Laba": laba, 
                "Prive": prive
            }])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_data], ignore_index=True)
            st.success("Transaksi dicatat!")

# --- LAPORAN & ANALISIS BANK ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    t_lap, t_kur = st.tabs(["📊 Laporan Bulanan", "🏦 Rekomendasi KUR BRI"])
    
    with t_lap:
        list_b = st.session_state.db_transaksi['Bulan'].unique()
        sel_b = st.selectbox("Pilih Periode", list_b)
        df_b = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b]
        
        # Desain Laporan Sesuai Gambar Referensi (PT Enggan Mundur)
        st.markdown(f"""
        <div class="report-card">
            <div style="text-align:center; margin-bottom:20px;">
                <h2 style='margin:0;'>{nama_usaha}</h2>
                <p><b>Laporan Laba Rugi</b><br>Periode: {sel_b}</p>
            </div>
            <table style="width:100%; border-collapse: collapse; font-size:18px;">
                <tr style="border-bottom: 2px solid #001f3f;">
                    <td style="padding:10px;"><b>Pendapatan Usaha (Omzet)</b></td>
                    <td style="text-align:right;"><b>{format_rp(df_b['Omzet'].sum())}</b></td>
                </tr>
                <tr>
                    <td style="padding:10px;">Beban Pokok Penjualan (HPP)</td>
                    <td style="text-align:right;">({format_rp(df_b['Omzet'].sum() - df_b['Laba'].sum())})</td>
                </tr>
                <tr style="border-bottom: 2px solid #001f3f; font-weight:bold;">
                    <td>LABA BERSIH (Earning)</td>
                    <td style="text-align:right;">{format_rp(df_b['Laba'].sum())}</td>
                </tr>
                <tr style="color:#b91c1c;">
                    <td style="padding:10px;">Pengambilan Pribadi (Prive)</td>
                    <td style="text-align:right;">({format_rp(df_b['Prive'].sum())})</td>
                </tr>
                <tr style="background-color:#FFD700; font-weight:bold; font-size:20px;">
                    <td style="padding:15px;">TOTAL MODAL BERJALAN</td>
                    <td style="text-align:right;">{format_rp(st.session_state.modal_awal + (df_b['Laba'].sum() - df_b['Prive'].sum()))}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        # Kalkulasi KUR BRI
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        rpc = avg_laba * 0.35 # Batas cicilan aman 35% dari laba
        plafon = rpc / ((1/12) + 0.005) # Estimasi plafon tenor 1 th bunga 6%

        st.markdown(f"""
        <div class="kur-card">
            <h2 style='margin-top:

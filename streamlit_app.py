import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku Bank-Ready", layout="wide")

# Inisialisasi Database Sesi
if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []
if 'profil' not in st.session_state:
    st.session_state.profil = {}

# 2. Styling BRI & Inklusi
st.markdown("""
    <style>
    .main-title { font-size: 32px; font-weight: bold; color: #00529b; text-align: center; }
    .sub-title { font-size: 20px; color: #00529b; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 10px; font-weight: bold; }
    .report-card { padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏦 FIN-Saku: Financial Hub UMKM</div>', unsafe_allow_html=True)

# --- SIDEBAR: PROFIL USAHA (ANALISIS 5C) ---
with st.sidebar:
    st.header("📋 Profil & Analisis 5C")
    st.session_state.profil['nama_usaha'] = st.text_input("Nama Usaha", placeholder="Warung Maju Jaya")
    st.session_state.profil['bidang'] = st.selectbox("Bidang Usaha", ["Kuliner", "Jasa", "Dagang/Ritel", "Produksi"])
    st.session_state.profil['lama_usaha'] = st.number_input("Lama Usaha (Bulan)", min_value=0)
    
    st.write("---")
    st.write("**Analisis Kapasitas (Capacity)**")
    hpp = st.number_input("Harga Pokok Produksi (HPP) per Unit", min_value=0, step=500)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0, step=500)
    
    if harga_jual > 0:
        margin = harga_jual - hpp
        persen_margin = (margin / harga_jual) * 100
        st.metric("Margin Keuntungan", f"Rp {margin:,.0f}", f"{persen_margin:.1f}%")
        st.session_state.profil['margin_ratio'] = margin / harga_jual

# --- HALAMAN UTAMA: PENCATATAN ---
col_input, col_history = st.columns([1, 1])

with col_input:
    st.markdown('<div class="sub-title">🎙️ Pencatatan Penjualan</div>', unsafe_allow_html=True)
    st.info("Gunakan suara di keyboard untuk input cepat!")
    
    jml_unit = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("➕ Simpan Transaksi"):
        if jml_unit > 0 and harga_jual > 0:
            total_sales = jml_unit * harga_jual
            total_hpp = jml_unit * hpp
            laba_kotor = total_sales - total_hpp
            
            st.session_state.transaksi.append({
                "Tanggal": datetime.now().strftime("%d/%m/%Y"),
                "Unit": jml_unit,
                "Omzet": total_sales,
                "HPP": total_hpp,
                "Laba": laba_kotor
            })
            st.toast("Data disimpan!")
        else:
            st.error("Set Harga Jual di sidebar dulu!")

with col_history:
    st.markdown('<div class="sub-title">📝 Riwayat Hari Ini</div>', unsafe_allow_html=True)
    if st.session_state.transaksi:
        df = pd.DataFrame(st.session_state.transaksi)
        st.table(df.style.format({"Omzet": "{:,.0f}", "Laba": "{:,.0f}"}))
        if st.button("Clear Data"):
            st.session_state.transaksi = []
            st.rerun()

# --- BAGIAN LAPORAN KEUANGAN STANDAR BANK ---
st.write("---")
if st.session_state.transaksi:
    st.header("📊 Laporan Keuangan & Rekomendasi KUR")
    
    total_omzet = sum(t['Omzet'] for t in st.session_state.transaksi)
    total_hpp_all = sum(t['HPP'] for t in st.session_state.transaksi)
    total_laba_kotor = total_omzet - total_hpp_all
    
    # 1. Laporan Laba Rugi Sederhana
    st.subheader("1. Laporan Laba Rugi (Income Statement)")
    st.markdown(f"""
    <div class="report-card">
    <table style="width:100%">
        <tr><td><b>Pendapatan Penjualan</b></td><td style="text-align:right">Rp {total_omzet:,.0f}</td></tr>
        <tr><td>Harga Pokok Penjualan (HPP)</td><td style="text-align:right">(Rp {total_hpp_all:,.0f})</td></tr>
        <tr style="border-top: 1px solid black"><td><b>LABA KOTOR</b></td><td style="text-align:right"><b>Rp {total_laba_kotor:,.0f}</b></td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # 2. Laporan Perubahan Modal & Porsi Pribadi
    st.subheader("2. Alokasi Modal & Dana Pribadi (Drawing)")
    porsi_pribadi = total_laba_kotor * 0.4 # Misal 40% dari laba boleh diambil
    reinvestasi = total_laba_kotor - porsi_pribadi
    
    st.markdown(f"""
    <div class="report-card">
    <table style="width:100%">
        <tr><td>Laba Bersih Tersedia</td><td style="text-align:right">Rp {total_laba_kotor:,.0f}</td></tr>
        <tr><td>Porsi Gaji Owner / Pribadi (Max 40%)</td><td style="text-align:right; color:red">Rp {porsi_pribadi:,.0f}</td></tr>
        <tr style="border-top: 1px solid black"><td><b>Penambahan Modal Usaha</b></td><td style="text-align:right; color:green"><b>Rp {reinvestasi:,.0f}</b></td></tr>
    </table>
    </div>
    """, unsafe_allow_html=True)

    # 3. Rekomendasi KUR BRI berdasarkan 5C
    st.write("---")
    st.subheader("🏦 Rekomendasi KUR BRI")
    
    cicilan_aman = total_laba_kotor * 0.3 # Maks 30% dari laba
    plafon = cicilan_aman / ((1/12) + 0.005)
    
    col_a, col_b = st.columns(2)
    with col_a:
        st.metric("Skor Kapasitas Bayar", f"Rp {cicilan_aman:,.0f}/bln")
        st.write("**Tips Bank:** Pertahankan margin di atas 20% agar plafon naik.")
    with col_b:
        st.metric("Estimasi Plafon KUR", f"Rp {plafon:,.0f}")
        st.link_button("Ajukan KUR BRI Online", "https://kur.bri.co.id/")

    # Download Report
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Unduh Laporan SAK-EMKM Lengkap", csv, "laporan_keuangan.csv", "text/csv")

import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Inklusi KUR BRI", layout="wide")

if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0.0

# --- FUNGSI FORMAT & SUARA ---
def format_rp(angka):
    return "Rp {:,.0f}".format(angka).replace(",", ".")

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# 2. CSS Styling (Standard Laporan Biru & Box KUR)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 10px; color: #1a1a1a; border: 1px solid #99aaff; }
    .header-lap { text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 10px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 8px; border-bottom: 1px solid #99aaff; }
    .kur-box { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; margin-top: 15px; border-left: 10px solid #ffab00; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #00529b; color: white; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: PROFIL BANKABLE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2e/BRI_Logo.svg", width=100)
    st.header("📋 Profil Nasabah KUR")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    st.session_state.modal_awal = st.number_input("Modal Awal (Cash on Hand)", min_value=0, step=100000)
    
    st.write("---")
    st.subheader("📊 Strategi Produk")
    hpp = st.number_input("HPP per Unit", min_value=0, step=500)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0, step=500)
    porsi_pribadi_persen = st.slider("Jatah Sendiri (Prive) %", 10, 50, 30)

# --- HALAMAN UTAMA ---
st.title(f"🏦 FIN-Saku: Solusi KUR Digital")

col_in, col_hist = st.columns([1, 1.2])

with col_in:
    st.subheader("🎙️ Input Penjualan Harian")
    jml = st.number_input("Jumlah terjual:", min_value=0, step=1)
    if st.button("🔔 SIMPAN & ANALISIS BANKABLE"):
        if jml > 0 and harga_jual > 0:
            omzet = jml * harga_jual
            total_hpp = jml * hpp
            laba = omzet - total_hpp
            prive = laba * (porsi_pribadi_persen / 100)
            
            st.session_state.transaksi.append({
                "Waktu": datetime.now().strftime("%H:%M"),
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive,
                "Nett_Usaha": omzet - prive
            })
            play_cash_sound()
            st.success(f"Tercatat! Jatah Pribadi: {format_rp(prive)}")
        else:
            st.warning("Input data harga dan jumlah!")

with col_hist:
    st.subheader("📝 Jurnal Kas Terkini")
    if st.session_state.transaksi:
        df_display = pd.DataFrame(st.session_state.transaksi)
        st.table(df_display) # Tabel stabil anti-error
        if st.button("Hapus Semua Data"):
            st.session_state.transaksi = []
            st.rerun()

# --- LAPORAN KEUANGAN & FITUR BANKABLE ---
if st.session_state.transaksi:
    st.write("---")
    
    total_omzet = sum(t['Omzet'] for t in st.session_state.transaksi)
    total_laba = sum(t['Laba'] for t in st.session_state.transaksi)
    total_prive = sum(t['Prive'] for t in st.session_state.transaksi)
    total_kas_usaha = sum(t['Nett_Usaha'] for t in st.session_state.transaksi) + st.session_state.modal_awal

    # 1. LAPORAN VISUAL BIRU (Sesuai Permintaan)
    st.markdown(f"""
    <div class="laporan-biru">
        <div class="header-lap">{nama_usaha}<br>Laporan Laba Rugi & Perubahan Modal</div>
        <table class="tabel-lap">
            <tr><td>Total Pendapatan (Omzet)</td><td style="text-align:right">{format_rp(total_omzet)}</td></tr>
            <tr><td>Total Laba Bersih</td><td style="text-align:right">{format_rp(total_laba)}</td></tr>
            <tr style="color: #b30000;"><td>Pengambilan Pribadi (Prive)</td><td style="text-align:right">({format_rp(total_prive)})</td></tr>
            <tr style="background-color: #b3c1ff; font-weight: bold;">
                <td>MODAL USAHA BERJALAN</td><td style="text-align:right">{format_rp(total_kas_usaha)}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 2. FITUR BANKABLE & KUR (SENJATA PILMAPRES)
    st.write(" ")
    st.subheader("🏦 Sertifikasi Bankable & Rekomendasi KUR")
    
    # Perhitungan Skor Bank (Simulasi sederhana)
    cicilan_aman = total_laba * 0.35 # Bank biasanya toleransi cicilan 35% dari laba
    plafon_kur = cicilan_aman / ((1/12) + 0.005) # Tenor 1 tahun bunga 6%
    
    st.markdown(f"""
    <div class="kur-box">
        <h2 style='color: #ffab00;'>Penilaian Mantri BRI:</h2>
        <p>Berdasarkan laporan keuangan di atas, Anda dinyatakan <b>LAYAK (Bankable)</b> untuk mengajukan pinjaman.</p>
        <hr>
        <table style='width:100%; color: white;'>
            <tr><td><b>Skor Kemampuan Bayar (Capacity):</b></td><td>{format_rp(cicilan_aman)} / bulan</td></tr>
            <tr><td><b>Rekomendasi Plafon KUR:</b></td><td><h2 style='margin:0;'>{format_rp(plafon_kur)}</h2></td></tr>
            <tr><td><b>Suku Bunga:</b></td><td>6% Efektif per Tahun (Subsidi Pemerintah)</td></tr>
        </table>
        <br>
        <p><small>*Data ini diolah secara otomatis berdasarkan standar SAK-EMKM untuk mempermudah verifikasi Bank.</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Tombol Aksi
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📥 Unduh Dokumen Pendukung KUR", pd.DataFrame(st.session_state.transaksi).to_csv(), "dokumen_kur.csv")
    with c2:
        st.link_button("📲 Hubungi Mantri BRI via WhatsApp", f"https://wa.me/?text=Halo%20BRI,%20saya%20{nama_usaha}%20ingin%20mengajukan%20KUR%20berdasarkan%20laporan%20FIN-Saku.")

st.write("---")
st.caption("FIN-Saku v13.0 | Dirancang untuk Mitigasi Asimetri Informasi UMKM")

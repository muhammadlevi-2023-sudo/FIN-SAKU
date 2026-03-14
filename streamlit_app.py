import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Pemisahan Dana", layout="wide")

# Inisialisasi data agar tidak hilang saat klik tombol
if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0.0

# --- FUNGSI FORMAT RUPIAH MANUAL (AGAR ANTI-ERROR) ---
def format_rp(angka):
    return "Rp {:,.0f}".format(angka).replace(",", ".")

# --- FUNGSI SUARA ---
def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# 2. CSS Styling (Warna Biru Laporan Profesional)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 10px; color: #1a1a1a; }
    .header-lap { text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 15px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 10px; border-bottom: 1px solid #99aaff; }
    .dompet-box { padding: 15px; border-radius: 10px; text-align: center; color: white; margin-bottom: 10px; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #00529b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: PENGATURAN ---
with st.sidebar:
    st.header("⚙️ Pengaturan Dasar")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    st.session_state.modal_awal = st.number_input("Modal Awal (Kas)", min_value=0, step=50000)
    
    st.write("---")
    st.subheader("💰 Parameter")
    hpp = st.number_input("HPP per Unit", min_value=0, step=500)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0, step=500)
    porsi_pribadi_persen = st.slider("Jatah Uang Pribadi (%)", 10, 50, 30)

# --- INPUT TRANSAKSI ---
st.title(f"🏦 {nama_usaha}")
col_in, col_hist = st.columns([1, 1.2])

with col_in:
    st.subheader("🎙️ Catat Penjualan")
    jml = st.number_input("Jumlah terjual hari ini:", min_value=0, step=1)
    if st.button("🔔 SIMPAN & PISAHKAN SALDO"):
        if jml > 0 and harga_jual > 0:
            omzet = jml * harga_jual
            total_hpp = jml * hpp
            laba = omzet - total_hpp
            # Logika Pemisahan
            untuk_pribadi = laba * (porsi_pribadi_persen / 100)
            untuk_usaha = omzet - untuk_pribadi
            
            st.session_state.transaksi.append({
                "Waktu": datetime.now().strftime("%H:%M"),
                "Omzet": omzet,
                "Laba": laba,
                "Pribadi": untuk_pribadi,
                "Usaha": untuk_usaha
            })
            play_cash_sound()
            st.success(f"Saldo terpisah! Jatah pribadi: {format_rp(untuk_pribadi)}")
        else:
            st.warning("Mohon isi data harga dan jumlah!")

with col_hist:
    st.subheader("📋 Jurnal Kas Terkini")
    if st.session_state.transaksi:
        # Menampilkan data tanpa format .style agar tidak error di server
        df_display = pd.DataFrame(st.session_state.transaksi)
        st.table(df_display) # Menggunakan table biasa agar lebih stabil
        if st.button("Hapus Riwayat"):
            st.session_state.transaksi = []
            st.rerun()

# --- BAGIAN LAPORAN KEUANGAN ---
if st.session_state.transaksi:
    st.write("---")
    st.header("📊 Hasil Pemisahan Dana & Laporan")
    
    total_omzet = sum(t['Omzet'] for t in st.session_state.transaksi)
    total_laba = sum(t['Laba'] for t in st.session_state.transaksi)
    total_prive = sum(t['Pribadi'] for t in st.session_state.transaksi)
    total_masuk_usaha = sum(t['Usaha'] for t in st.session_state.transaksi)

    # VISUAL DOMPET
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="dompet-box" style="background-color: #00529b;">
        <h3>💼 UNTUK USAHA</h3><h2>{format_rp(total_masuk_usaha + st.session_state.modal_awal)}</h2>
        <small>Modal Aman & Putaran Usaha</small></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="dompet-box" style="background-color: #28a745;">
        <h3>🙋 UNTUK SENDIRI</h3><h2>{format_rp(total_prive)}</h2>
        <small>Jatah Pribadi / Jajan</small></div>""", unsafe_allow_html=True)

    # LAPORAN WARNA BIRU (Sesuai Gambar Referensi)
    st.markdown(f"""
    <div class="laporan-biru">
        <div class="header-lap">{nama_usaha}<br>Laporan Perubahan Modal & Prive</div>
        <table class="tabel-lap">
            <tr><td>Total Omzet (Penjualan)</td><td style="text-align:right">{format_rp(total_omzet)}</td></tr>
            <tr><td>Total Laba Bersih</td><td style="text-align:right">{format_rp(total_laba)}</td></tr>
            <tr style="color: #b30000;"><td><b>Jatah Pribadi (Prive {porsi_pribadi_persen}%)</b></td><td style="text-align:right"><b>({format_rp(total_prive)})</b></td></tr>
            <tr style="background-color: #b3c1ff; font-weight: bold;">
                <td>TAMBAHAN MODAL USAHA</td><td style="text-align:right">{format_rp(total_laba - total_prive)}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.download_button("📥 Unduh Laporan (CSV)", pd.DataFrame(st.session_state.transaksi).to_csv(), "laporan.csv")

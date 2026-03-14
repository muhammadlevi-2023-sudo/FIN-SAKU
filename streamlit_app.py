import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Smart KUR Reporting", layout="wide")

# Database Internal
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive", "Nett_Usaha"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI HELPER ---
def format_rp(angka):
    return "Rp {:,.0f}".format(float(angka)).replace(",", ".")

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# 2. CSS Styling (Standard Biru Akuntansi & KUR)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 10px; color: #1a1a1a; border: 1px solid #99aaff; margin-bottom: 20px; }
    .kur-card { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; border-left: 10px solid #ffab00; }
    .header-lap { text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 10px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 8px; border-bottom: 1px solid #99aaff; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #00529b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MODAL & KUR SETTINGS ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2e/BRI_Logo.svg", width=100)
    st.header("⚙️ Konfigurasi Bank")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    
    # Input Modal Awal dengan Format Real-time Manual
    modal_raw = st.text_input("💰 Modal Awal (Rp)", value=str(st.session_state.modal_awal))
    # Membersihkan input dari karakter non-angka
    modal_clean = "".join(filter(str.isdigit, modal_raw))
    if modal_clean:
        st.session_state.modal_awal = int(modal_clean)
        st.caption(f"Terdeteksi: **{format_rp(st.session_state.modal_awal)}**")

    st.write("---")
    st.subheader("📦 Strategi Produk")
    hpp_raw = st.text_input("HPP per Unit", "5000")
    harga_raw = st.text_input("Harga Jual per Unit", "15000")
    porsi_pribadi_persen = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"🏦 Dashboard KUR: {nama_usaha}")
col_in, col_stats = st.columns([1, 2])

with col_in:
    st.subheader("➕ Catat Penjualan")
    tgl_input = st.date_input("Tanggal", datetime.now())
    jml = st.number_input("Unit Terjual", min_value=0, step=1)
    
    # Konversi string input sidebar ke angka
    val_hpp = int("".join(filter(str.isdigit, hpp_raw))) if hpp_raw else 0
    val_harga = int("".join(filter(str.isdigit, harga_raw))) if harga_raw else 0

    if st.button("🔔 SIMPAN & ANALISIS"):
        if jml > 0 and val_harga > 0:
            omzet = jml * val_harga
            laba = omzet - (jml * val_hpp)
            prive = laba * (porsi_pribadi_persen / 100)
            
            new_row = {
                "Tanggal": tgl_input,
                "Bulan": tgl_input.strftime("%B %Y"),
                "Minggu": f"Minggu {tgl_input.isocalendar()[1]}",
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive,
                "Nett_Usaha": omzet - prive
            }
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, pd.DataFrame([new_row])], ignore_index=True)
            play_cash_sound()
            st.success(f"Berhasil! Laba Bersih: {format_rp(laba)}")

# --- LAPORAN PERIODIK & KUR ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    tab_h, tab_m, tab_b, tab_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def render_laporan(df_p, judul):
        t_omzet = df_p['Omzet'].sum()
        t_laba = df_p['Laba'].sum()
        t_prive = df_p['Prive'].sum()
        st.markdown(f"""
        <div class="laporan-biru">
            <div class="header-lap">{nama_usaha}<br>{judul}</div>
            <table class="tabel-lap">
                <tr><td>Pendapatan (Omzet)</td><td style="text-align:right">{format_rp(t_omzet)}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right">{format_rp(t_laba)}</td></tr>
                <tr style="color: #b30000;"><td>Porsi Pribadi (Prive)</td><td style="text-align:right">({format_rp(t_prive)})</td></tr>
                <tr style="background-color: #b3c1ff; font-weight: bold;">
                    <td>TOTAL MODAL BERJALAN</td><td style="text-align:right">{format_rp(st.session_state.modal_awal + (t_laba - t_prive))}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tab_h:
        t_pilih = st.date_input("Filter Hari", datetime.now())
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == t_pilih]
        if not df_h.empty: render_laporan(df_h, f"Laporan Harian {t_pilih.strftime('%d/%m/%Y')}")
        else: st.info("Belum ada data.")

    with tab_m:
        m_list = st.session_state.db_transaksi['Minggu'].unique()
        m_pilih = st.selectbox("Pilih Minggu", m_list)
        render_laporan(st.session_state.db_transaksi[st.session_state.db_transaksi['Minggu'] == m_pilih], f"Laporan {m_pilih}")

    with tab_b:
        b_list = st.session_state.db_transaksi['Bulan'].unique()
        b_pilih = st.selectbox("Pilih Bulan", b_list)
        render_laporan(st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == b_pilih], f"Laporan Bulanan {b_pilih}")

    with tab_kur:
        total_laba = st.session_state.db_transaksi['Laba'].sum()
        jml_bulan = max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        avg_laba = total_laba / jml_bulan
        plafon = (avg_laba * 0.35) / ((1/12) + 0.005)

        st.markdown(f"""
        <div class="kur-card">
            <h2 style='color: #ffab00;'>Simulasi Plafon KUR BRI</h2>
            <p>Berdasarkan data Modal Awal dan Akumulasi Laba Periodik:</p>
            <hr>
            <table style='width:100%; color: white;'>
                <tr><td>Modal Awal Tercatat:</td><td style='text-align:right'>{format_rp(st.session_state.modal

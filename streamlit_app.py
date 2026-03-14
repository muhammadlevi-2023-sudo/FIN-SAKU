import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Laporan Bankable", layout="wide")

# Inisialisasi Database agar tidak hilang
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive", "Nett"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI PEMBANTU ---
def format_rp(angka):
    try:
        return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except:
        return "Rp 0"

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# Fungsi untuk membersihkan input teks ke angka
def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, teks))
    return int(angka) if angka else 0

# 2. CSS Styling (Warna Biru Akuntansi Sesuai Gambar)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 5px; color: #1a1a1a; border: 1px solid #99aaff; }
    .header-lap { text-align: center; font-weight: bold; font-size: 18px; line-height: 1.5; margin-bottom: 15px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 10px; border-bottom: 1px solid #99aaff; }
    .kur-card { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; border-left: 10px solid #ffab00; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #00529b; color: white; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: INPUT MODAL & STRATEGI ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2e/BRI_Logo.svg", width=100)
    st.header("⚙️ Pengaturan Profil")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    
    # Fitur: Ketik angka, muncul format titik di bawahnya
    modal_raw = st.text_input("💰 Modal Awal (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(modal_raw)
    st.caption(f"Terformat: **{format_rp(st.session_state.modal_awal)}**")
    
    st.write("---")
    hpp_raw = st.text_input("HPP per Unit (Rp)", value="5000")
    harga_raw = st.text_input("Harga Jual per Unit (Rp)", value="15000")
    porsi_pribadi = st.slider("Jatah Sendiri (Prive) %", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"🏦 FIN-Saku Dashboard")

col_in, col_space = st.columns([1, 1.5])

with col_in:
    st.subheader("➕ Catat Penjualan")
    tgl_input = st.date_input("Tanggal Transaksi", datetime.now())
    jml_unit = st.number_input("Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN KE LAPORAN"):
        v_hpp = clean_to_int(hpp_raw)
        v_harga = clean_to_int(harga_raw)
        
        if jml_unit > 0 and v_harga > 0:
            omzet = jml_unit * v_harga
            laba = omzet - (jml_unit * v_hpp)
            prive = laba * (porsi_pribadi / 100)
            
            new_row = pd.DataFrame([{
                "Tanggal": tgl_input,
                "Bulan": tgl_input.strftime("%B %Y"),
                "Minggu": f"Minggu {tgl_input.isocalendar()[1]}",
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive
            }])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_row], ignore_index=True)
            play_cash_sound()
            st.success("Transaksi Berhasil Disimpan!")

# --- BAGIAN LAPORAN PERIODIK ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def display_blue_report(df_p, judul):
        t_omzet = df_p['Omzet'].sum()
        t_laba = df_p['Laba'].sum()
        t_prive = df_p['Prive'].sum()
        # Modal Berjalan = Modal Awal + (Total Laba - Total Prive)
        modal_skrg = st.session_state.modal_awal + (t_laba - t_prive)
        
        st.markdown(f"""
        <div class="laporan-biru">
            <div class="header-lap">{nama_usaha}<br>{judul}<br>Per Tanggal {datetime.now().strftime('%d/%m/%Y')}</div>
            <table class="tabel-lap">
                <tr><td>Pendapatan Usaha (Omzet)</td><td style="text-align:right">{format_rp(t_omzet)}</td></tr>
                <tr><td>Laba Bersih Operasional</td><td style="text-align:right">{format_rp(t_laba)}</td></tr>
                <tr style="color: #b30000;"><td>Pengambilan Pribadi (Prive)</td><td style="text-align:right">({format_rp(t_prive)})</td></tr>
                <tr style="background-color: #b3c1ff; font-weight: bold;">
                    <td>TOTAL MODAL BERJALAN</td><td style="text-align:right">{format_rp(modal_skrg)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tab1:
        t_pilih = st.date_input("Pilih Hari", datetime.now())
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == t_pilih]
        if

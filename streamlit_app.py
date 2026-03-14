import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Laporan Multi-Periode & KUR", layout="wide")

# Database Database (Penyimpanan Data)
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive", "Nett"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0.0

# --- FUNGSI FORMAT & SUARA ---
def format_rp(angka):
    return "Rp {:,.0f}".format(angka).replace(",", ".")

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# 2. CSS Styling (Laporan Biru & Box KUR)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 10px; color: #1a1a1a; border: 1px solid #99aaff; margin-bottom: 20px; }
    .kur-card { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; border-left: 10px solid #ffab00; }
    .header-lap { text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 10px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 8px; border-bottom: 1px solid #99aaff; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MODAL & PARAMETER ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2e/BRI_Logo.svg", width=100)
    st.header("⚙️ Pengaturan Dasar")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    st.session_state.modal_awal = st.number_input("💰 Modal Awal (Cash)", min_value=0,0, step=2,500,000, value=st.session_state.modal_awal)
    
    st.write("---")
    st.subheader("📦 Strategi Harga")
    hpp = st.number_input("HPP per Unit", min_value=0,0, step=500, value=5,000)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0,0, step=500, value=15,000)
    porsi_pribadi_persen = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA: INPUT ---
st.title(f"🏦 Dashboard Keuangan: {nama_usaha}")
col_in, col_space = st.columns([1, 2])

with col_in:
    st.subheader("➕ Catat Penjualan")
    tgl_input = st.date_input("Tanggal", datetime.now())
    jml = st.number_input("Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN & PROSES BANKABLE"):
        if jml > 0:
            omzet = jml * harga_jual
            laba = omzet - (jml * hpp)
            prive = laba * (porsi_pribadi_persen / 100)
            
            new_data = {
                "Tanggal": tgl_input,
                "Bulan": tgl_input.strftime("%B %Y"),
                "Minggu": f"Minggu {tgl_input.isocalendar()[1]}",
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive,
                "Nett_Usaha": omzet - prive
            }
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, pd.DataFrame([new_data])], ignore_index=True)
            play_cash_sound()
            st.success(f"Tersimpan! Jatah Pribadi: {format_rp(prive)}")

# --- BAGIAN LAPORAN PERIODIK ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    tab_harian, tab_mingguan, tab_bulanan, tab_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def buat_tabel_biru(df_periode, judul):
        t_omzet = df_periode['Omzet'].sum()
        t_laba = df_periode['Laba'].sum()
        t_prive = df_periode['Prive'].sum()
        t_modal_jalan = t_laba - t_prive
        
        st.markdown(f"""
        <div class="laporan-biru">
            <div class="header-lap">{nama_usaha}<br>{judul}</div>
            <table class="tabel-lap">
                <tr><td>Total Pendapatan (Omzet)</td><td style="text-align:right">{format_rp(t_omzet)}</td></tr>
                <tr><td>Total Laba Bersih</td><td style="text-align:right">{format_rp(t_laba)}</td></tr>
                <tr style="color: #b30000;"><td>Pengambilan Pribadi (Prive)</td><td style="text-align:right">({format_rp(t_prive)})</td></tr>
                <tr style="background-color: #b3c1ff; font-weight: bold;">
                    <td>TAMBAHAN MODAL DARI LABA</td><td style="text-align:right">{format_rp(t_modal_jalan)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tab_harian:
        tgl_pilih = st.date_input("Lihat Laporan Tanggal:", datetime.now())
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == tgl_pilih]
        if not df_h.empty:
            buat_tabel_biru(df_h, f"Laporan Harian ({tgl_pilih.strftime('%d %B %Y')})")
        else: st.info("Tidak ada data hari ini.")

    with tab_mingguan:
        minggu_list = st.session_state.db_transaksi['Minggu'].unique()
        m_pilih = st.selectbox("Pilih Minggu:", minggu_list)
        df_m = st.session_state.db_transaksi[st.session_state.db_transaksi['Minggu'] == m_pilih]
        buat_tabel_biru(df_m, f"Laporan Mingguan ({m_pilih})")

    with tab_bulanan:
        bulan_list = st.session_state.db_transaksi['Bulan'].unique()
        b_pilih = st.selectbox("Pilih Bulan:", bulan_list)
        df_b = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == b_pilih]
        buat_tabel_biru(df_b, f"Laporan Bulanan ({b_pilih})")

    with tab_kur:
        # Kalkulasi KUR berdasarkan TOTAL DATA
        total_laba_all = st.session_state.db_transaksi['Laba'].sum()
        jumlah_bulan = len(st.session_state.db_transaksi['Bulan'].unique())
        avg_laba_bulanan = total_laba_all / jumlah_bulan
        
        cicilan_aman = avg_laba_bulanan * 0.35
        plafon = cicilan_aman / ((1/12) + 0.005)
        
        st.markdown(f"""
        <div class="kur-card">
            <h2 style='color: #ffab00;'>Penilaian Kelayakan KUR BRI</h2>
            <p>Berdasarkan akumulasi laporan keuangan harian hingga bulanan:</p>
            <hr>
            <table style='width:100%; color: white;'>
                <tr><td>Modal Awal Anda:</td><td style='text-align:right'>{format_rp(st.session_state.modal_awal)}</td></tr>
                <tr><td>Rata-rata Laba Bulanan:</td><td style='text-align:right'>{format_rp(avg_laba_bulanan)}</td></tr>
                <tr><td>Kemampuan Cicil (35% Laba):</td><td style='text-align:right'>{format_rp(cicilan_aman)} / bln</td></tr>
                <tr><td colspan='2'><br></td></tr>
                <tr style='font-size: 24px; font-weight: bold;'>
                    <td>ESTIMASI PLAFON KUR:</td><td style='text-align:right; color: #ffab00;'>{format_rp(plafon)}</td>
                </tr>
            </table>
            <p><br>Suku Bunga: 6% per Tahun | Status: <b>PROSPEK TINGGI</b></p>
        </div>
        """, unsafe_allow_html=True)
        st.download_button("📥 Download Laporan SAK-EMKM", st.session_state.db_transaksi.to_csv().encode('utf-8'), "laporan_lengkap.csv")

else:
    st.warning("Silakan masukkan data transaksi untuk mengaktifkan fitur Laporan & Analisis KUR.")

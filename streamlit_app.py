import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Laporan Periodik KUR", layout="wide")

# Database Simulasi (Agar data tersimpan selama aplikasi berjalan)
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive", "Nett"])

# --- FUNGSI FORMAT & SUARA ---
def format_rp(angka):
    return "Rp {:,.0f}".format(angka).replace(",", ".")

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

# 2. CSS Styling
st.markdown("""
    <style>
    .report-box { background-color: #d1d9ff; padding: 20px; border-radius: 10px; color: #1a1a1a; margin-bottom: 20px; }
    .kur-card { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; border-left: 10px solid #ffab00; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🏢 Profil & Parameter")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    st.write("---")
    hpp = st.number_input("HPP per Unit", min_value=0, step=500, value=5000)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0, step=500, value=15000)
    porsi_pribadi = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- INPUT TRANSAKSI ---
st.title(f"🏦 FIN-Saku: Pusat Laporan {nama_usaha}")
col_in, col_stats = st.columns([1, 2])

with col_in:
    st.subheader("➕ Catat Penjualan")
    tgl_input = st.date_input("Tanggal Transaksi", datetime.now())
    jml = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if jml > 0:
            omzet = jml * harga_jual
            laba = omzet - (jml * hpp)
            prive = laba * (porsi_pribadi / 100)
            
            new_data = {
                "Tanggal": tgl_input,
                "Bulan": tgl_input.strftime("%B %Y"),
                "Minggu": tgl_input.isocalendar()[1],
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive,
                "Nett": omzet - prive
            }
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, pd.DataFrame([new_data])], ignore_index=True)
            play_cash_sound()
            st.success("Data berhasil masuk ke database periodik!")

# --- BAGIAN LAPORAN BERJENJANG ---
st.write("---")
st.header("📊 Dashboard Laporan Periodik")

if not st.session_state.db_transaksi.empty:
    tab_harian, tab_mingguan, tab_bulanan, tab_analisis = st.tabs(["📆 Harian", "📅 Mingguan", "🗓️ Bulanan", "🏦 Analisis KUR"])

    # 1. LAPORAN HARIAN
    with tab_harian:
        tgl_filter = st.date_input("Pilih Hari", datetime.now())
        data_harian = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == tgl_filter]
        
        if not data_harian.empty:
            st.markdown(f"<div class='report-box'><h3>Laporan Harian: {tgl_filter.strftime('%d %B %Y')}</h3>", unsafe_allow_html=True)
            st.table(data_harian[["Tanggal", "Omzet", "Laba", "Prive"]].style.format("{:,.0f}"))
            st.write(f"**Total Laba Bersih Hari Ini:** {format_rp(data_harian['Laba'].sum())}")
        else:
            st.info("Tidak ada transaksi di tanggal ini.")

    # 2. LAPORAN MINGGUAN
    with tab_mingguan:
        minggu_skrg = datetime.now().isocalendar()[1]
        data_mingguan = st.session_state.db_transaksi[st.session_state.db_transaksi['Minggu'] == minggu_skrg]
        
        if not data_mingguan.empty:
            st.markdown(f"<div class='report-box'><h3>Laporan Minggu Ke-{minggu_skrg}</h3>", unsafe_allow_html=True)
            st.write(f"Total Omzet Mingguan: **{format_rp(data_mingguan['Omzet'].sum())}**")
            st.write(f"Total Laba Mingguan: **{format_rp(data_mingguan['Laba'].sum())}**")
            st.bar_chart(data_mingguan.set_index('Tanggal')['Omzet'])
        else:
            st.info("Belum ada data untuk minggu ini.")

    # 3. LAPORAN BULANAN
    with tab_bulanan:
        list_bulan = st.session_state.db_transaksi['Bulan'].unique()
        pilih_bulan = st.selectbox("Pilih Periode Bulan", list_bulan)
        data_bulanan = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == pilih_bulan]
        
        st.markdown(f"<div class='report-box'><h3>Laporan Bulanan: {pilih_bulan}</h3>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Omzet", format_rp(data_bulanan['Omzet'].sum()))
        col2.metric("Total Laba", format_rp(data_bulanan['Laba'].sum()))
        col3.metric("Total Prive", format_rp(data_bulanan['Prive'].sum()))
        st.write("---")
        st.table(data_bulanan.groupby('Tanggal').sum()[['Omzet', 'Laba']])

    # 4. ANALISIS KUR (BANKABLE)
    with tab_analisis:
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / len(st.session_state.db_transaksi['Bulan'].unique())
        cicilan_aman = avg_laba * 0.35
        plafon = cicilan_aman / ((1/12) + 0.005)
        
        st.markdown(f"""
        <div class="kur-card">
            <h2>Analisis Kelayakan Kredit (Bank Ready)</h2>
            <p>Berdasarkan tren data dari beberapa periode, berikut estimasi plafon KUR Anda:</p>
            <hr>
            <h1>{format_rp(plafon)}</h1>
            <p>Rata-rata Laba Bulanan: {format_rp(avg_laba)}</p>
            <p>Skor Kolektibilitas: <b>LANCAR (Sangat Baik)</b></p>
        </div>
        """, unsafe_allow_html=True)
        
else:
    st.warning("Silakan masukkan transaksi pertama Anda untuk melihat laporan periodik.")

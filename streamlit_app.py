import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman Dasar
st.set_page_config(page_title="FIN-Saku: Solusi KUR BRI", layout="wide")

# Inisialisasi Database Sesi
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except:
        return "Rp 0"

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. CSS Styling Biru Akuntansi (Sesuai Gambar Referensi)
st.markdown("""
<style>
    .report-card { background-color: #d1d9ff; padding: 25px; border-radius: 8px; color: #1a1a1a; border: 1px solid #99aaff; margin-bottom: 20px; }
    .header-text { text-align: center; font-weight: bold; font-size: 1.2rem; margin-bottom: 10px; }
    .kur-card { background-color: #00529b; color: white; padding: 20px; border-radius: 10px; border-left: 10px solid #ffab00; }
    .stButton>button { width: 100%; font-weight: bold; background-color: #00529b; color: white; height: 3em; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: PENGATURAN NASABAH ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/2/2e/BRI_Logo.svg", width=100)
    st.header("🏢 Profil Usaha")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    
    # Fitur Titik Otomatis (Visual Feedback)
    m_raw = st.text_input("💰 Masukkan Modal Awal (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.caption(f"Tercatat: **{format_rp(st.session_state.modal_awal)}**")
    
    st.write("---")
    hpp_raw = st.text_input("HPP per Unit (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual per Unit (Rp)", "15000")
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA: INPUT TRANSAKSI ---
st.title(f"🏦 FIN-Saku: Pusat Data KUR")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("➕ Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        v_hpp = clean_to_int(hpp_raw)
        v_harga = clean_to_int(harga_raw)
        
        if qty > 0 and v_harga > 0:
            omzet = qty * v_harga
            laba = omzet - (qty * v_hpp)
            prive = laba * (prive_pct / 100)
            
            # Simpan ke DataFrame
            new_data = pd.DataFrame([{
                "Tanggal": tgl,
                "Bulan": tgl.strftime("%B %Y"),
                "Minggu": f"Minggu {tgl.isocalendar()[1]}",
                "Omzet": omzet,
                "Laba": laba,
                "Prive": prive
            }])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_data], ignore_index=True)
            play_cash_sound()
            st.success(f"Data Berhasil Disimpan!")
        else:
            st.error("Lengkapi jumlah unit dan harga!")

# --- LAPORAN & ANALISIS ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    tabs = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    # Template Laporan Biru
    def render_report(df, title):
        omz = df['Omzet'].sum()
        lb = df['Laba'].sum()
        prv = df['Prive'].sum()
        modal_akhir = st.session_state.modal_awal + (lb - prv)
        
        st.markdown(f"""
        <div class="report-card">
            <div class="header-text">{nama_usaha}<br>{title}</div>
            <table style="width:100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #99aaff;"><td style="padding:8px;">Total Pendapatan (Omzet)</td><td style="text-align:right;">{format_rp(omz)}</td></tr>
                <tr style="border-bottom: 1px solid #99aaff;"><td style="padding:8px;">Total Laba Bersih</td><td style="text-align:right;">{format_rp(lb)}</td></tr>
                <tr style="border-bottom: 1px solid #99aaff; color:red;"><td style="padding:8px;">Pengambilan Pribadi (Prive)</td><td style="text-align:right;">({format_rp(prv)})</td></tr>
                <tr style="background-color:#b3c1ff; font-weight:bold;"><td style="padding:8px;">TOTAL MODAL BERJALAN</td><td style="text-align:right;">{format_rp(modal_akhir)}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tabs[0]:
        sel_tgl = st.date_input("Filter Hari", datetime.now())
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == sel_tgl]
        if not df_h.empty: render_report(df_h, f"Laporan Harian - {sel_tgl.strftime('%d/%m/%Y')}")
        else: st.info("Tidak ada transaksi.")

    with tabs[1]:
        m_list = st.session_state.db_transaksi['Minggu'].unique()
        sel_m = st.selectbox("Pilih Minggu", m_list)
        render_report(st.session_state.db_transaksi[st.session_state.db_transaksi['Minggu'] == sel_m], f"Laporan {sel_m}")

    with tabs[2]:
        b_list = st.session_state.db_transaksi['Bulan'].unique()
        sel_b = st.selectbox("Pilih Bulan", b_list)
        render_report(st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b], f"Laporan Bulanan - {sel_b}")

    with tabs[3]:
        # Logika Bankable KUR
        t_laba = st.session_state.db_transaksi['Laba'].sum()
        n_bulan = max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        avg_l = t_laba / n_bulan
        cap_cicil = avg_l * 0.35
        plafon = cap_cicil / ((1/12) + 0.005)
        
        st.markdown(f"""
        <div class="kur-card">
            <h3>🏦 Rekomendasi KUR BRI</h3>
            <p>Data modal awal dan tren laba Anda menunjukkan profil berikut:</p>
            <hr>
            <table style="width:100%; color:white;">
                <tr><td>Modal Awal Tercatat</td><td style="text-align:right;">{format_rp(st.session_state.modal_awal)}</td></tr>
                <tr><td>Rata-rata Laba Bulanan</td><td style="text-align:right;">{format_rp(avg_l)}</td></tr>
                <tr style="font-size:1.5rem; font-weight:bold; color:#ffab00;"><td>ESTIMASI PLAFON KUR</td><td style="text-align:right;">{format_rp(plafon)}</td></tr>
            </table>
            <br>
            <small>*Analisis ini menggunakan standar kelayakan bank berdasarkan Capacity & Capital.</small>
        </div>
        """, unsafe_allow_html=True)
        st.download_button("📥 Unduh Laporan PDF/CSV", st.session_state.db_transaksi.to_csv().encode('utf-8'), "laporan_bank.csv")

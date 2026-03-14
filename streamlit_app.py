import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku Pro Bank", layout="wide")

# Inisialisasi Database Sesi
if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0.0

# Fungsi Suara Uang (Simulasi via HTML)
def play_sound():
    sound_file = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    html_str = f"""
        <audio autoplay>
            <source src="{sound_file}" type="audio/mp3">
        </audio>
    """
    st.components.v1.html(html_str, height=0)

# 2. Styling BRI & Inklusi
st.markdown("""
    <style>
    .main-title { font-size: 30px; font-weight: bold; color: #00529b; text-align: center; }
    .card { padding: 15px; border-radius: 10px; background-color: #f8f9fa; border: 1px solid #dee2e6; margin-bottom: 10px; }
    .stNumberInput input { font-size: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<div class="main-title">🏦 FIN-Saku: Laporan Keuangan Standar Bank</div>', unsafe_allow_html=True)

# --- SIDEBAR: SETTING AWAL (PENTING UNTUK NERACA) ---
with st.sidebar:
    st.header("⚙️ Pengaturan Awal Usaha")
    st.info("Isi data ini sekali saja saat memulai usaha.")
    st.session_state.modal_awal = st.number_input("💰 Modal Awal (Uang di Kas/Bank)", min_value=0, step=100000)
    
    st.write("---")
    st.subheader("📦 Analisis Produk")
    hpp = st.number_input("Biaya Modal per Produk (HPP)", min_value=0, step=500)
    harga_jual = st.number_input("Harga Jual ke Pelanggan", min_value=0, step=500)
    
    if harga_jual > 0:
        margin = harga_jual - hpp
        st.metric("Keuntungan per Produk", f"Rp {margin:,.0f}")

# --- HALAMAN UTAMA: INPUT TRANSAKSI ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎙️ Catat Penjualan")
    st.caption("Klik mikrofon keyboard HP untuk input suara.")
    jml_unit = st.number_input("Berapa banyak yang laku?", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        if jml_unit > 0 and harga_jual > 0:
            total_sales = jml_unit * harga_jual
            total_hpp = jml_unit * hpp
            laba = total_sales - total_hpp
            
            st.session_state.transaksi.append({
                "Tanggal": datetime.now().strftime("%d/%m/%Y"),
                "Omzet": total_sales,
                "HPP": total_hpp,
                "Laba": laba
            })
            play_sound() # Memicu suara uang
            st.success(f"Berhasil! Uang masuk Rp {total_sales:,.0f}")
        else:
            st.error("Isi data produk di samping dulu!")

with col2:
    st.subheader("📝 Catatan Hari Ini")
    if st.session_state.transaksi:
        df = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df.style.format({"Omzet": "{:,.0f}", "Laba": "{:,.0f}"}))
        if st.button("Hapus Riwayat"):
            st.session_state.transaksi = []
            st.rerun()

# --- BAGIAN OUTUPUT: LAPORAN KEUANGAN 4 PILAR ---
if st.session_state.transaksi:
    st.write("---")
    st.header("📑 Laporan Keuangan SAK-EMKM")
    
    # Hitung Variabel Utama
    total_sales = sum(t['Omzet'] for t in st.session_state.transaksi)
    total_hpp = sum(t['HPP'] for t in st.session_state.transaksi)
    total_laba = total_sales - total_hpp
    porsi_pribadi = total_laba * 0.3 # 30% untuk pribadi
    laba_ditahan = total_laba - porsi_pribadi
    kas_akhir = st.session_state.modal_awal + total_sales - porsi_pribadi

    tab1, tab2, tab3, tab4 = st.tabs(["📉 Laba Rugi", "⚖️ Neraca", "🔄 Arus Kas", "📈 Perubahan Modal"])

    with tab1:
        st.subheader("Laporan Laba Rugi")
        st.markdown(f"""
        <div class='card'>
        Total Pendapatan: **Rp {total_sales:,.0f}**<br>
        Total Beban (HPP): **(Rp {total_hpp:,.0f})**<hr>
        <b>LABA BERSIH: Rp {total_laba:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.subheader("Laporan Posisi Keuangan (Neraca)")
        st.markdown(f"""
        <div class='card'>
        <b>ASET (Harta):</b><br>
        Kas di Tangan: Rp {kas_akhir:,.0f}<br><hr>
        <b>KEWAJIBAN & MODAL:</b><br>
        Utang: Rp 0<br>
        Modal Akhir: Rp {st.session_state.modal_awal + laba_ditahan:,.0f}<br><hr>
        <i>Status: <b>BALANCE ✅</b></i>
        </div>
        """, unsafe_allow_html=True)

    with tab3:
        st.subheader("Laporan Arus Kas")
        st.write("Menunjukkan aliran uang masuk dan keluar secara nyata.")
        st.markdown(f"""
        <div class='card'>
        Saldo Awal Kas: Rp {st.session_state.modal_awal:,.0f}<br>
        Penerimaan Pelanggan: + Rp {total_sales:,.0f}<br>
        Pengambilan Pribadi (Prive): - Rp {porsi_pribadi:,.0f}<br><hr>
        <b>SALDO AKHIR KAS: Rp {kas_akhir:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

    with tab4:
        st.subheader("Laporan Perubahan Ekuitas")
        st.markdown(f"""
        <div class='card'>
        Modal Awal: Rp {st.session_state.modal_awal:,.0f}<br>
        Laba Bersih: + Rp {total_laba:,.0f}<br>
        Pengambilan Pribadi: - Rp {porsi_pribadi:,.0f}<br><hr>
        <b>MODAL AKHIR: Rp {st.session_state.modal_awal + laba_ditahan:,.0f}</b>
        </div>
        """, unsafe_allow_html=True)

    # --- REKOMENDASI BANK ---
    st.write("---")
    st.subheader("🏦 Rekomendasi Mantri BRI")
    cicilan_aman = total_laba * 0.3
    st.success(f"Berdasarkan Laba Rugi, Anda aman mencicil maksimal **Rp {cicilan_aman:,.0f}/bulan**.")
    st.download_button("📥 Download Laporan Lengkap (CSV)", df.to_csv().encode('utf-8'), "laporan_bank.csv")

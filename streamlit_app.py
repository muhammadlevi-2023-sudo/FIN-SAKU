import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku: Pemisahan Dana", layout="wide")

if 'transaksi' not in st.session_state:
    st.session_state.transaksi = []
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0.0

# --- FUNGSI PENDUKUNG ---
def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}".replace(",", ".")

# 2. CSS Custom (Warna Laporan Sesuai Gambar Referensi)
st.markdown("""
    <style>
    .laporan-biru { background-color: #d1d9ff; padding: 25px; border-radius: 10px; color: #1a1a1a; }
    .header-lap { text-align: center; font-weight: bold; font-size: 20px; margin-bottom: 15px; }
    .tabel-lap { width: 100%; border-collapse: collapse; }
    .tabel-lap td { padding: 10px; border-bottom: 1px solid #99aaff; }
    .total-row { background-color: #b3c1ff; font-weight: bold; }
    .dompet-box { padding: 15px; border-radius: 10px; text-align: center; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Pengaturan Dasar")
    nama_usaha = st.text_input("Nama Usaha", "PT. Enggan Mundur")
    st.session_state.modal_awal = st.number_input("Modal Awal (Uang di Kas)", min_value=0, step=50000)
    
    st.write("---")
    st.subheader("💰 Parameter Keuntungan")
    hpp = st.number_input("HPP per Unit", min_value=0, step=500)
    harga_jual = st.number_input("Harga Jual per Unit", min_value=0, step=500)
    porsi_pribadi_persen = st.slider("Jatah Uang Pribadi (%)", 10, 50, 30)

# --- INPUT TRANSAKSI ---
st.title(f"🏦 {nama_usaha}")
col_in, col_hist = st.columns([1, 1])

with col_in:
    st.subheader("🎙️ Catat Penjualan Hari Ini")
    jml = st.number_input("Jumlah terjual:", min_value=0, step=1)
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
            st.success(f"Saldo terpisah! Jatah pribadi: {format_rupiah(untuk_pribadi)}")
        else:
            st.warning("Lengkapi data harga di samping!")

with col_hist:
    st.subheader("📋 Jurnal Kas Terkini")
    if st.session_state.transaksi:
        df = pd.DataFrame(st.session_state.transaksi)
        st.dataframe(df.style.format("{:,.0f}"))

# --- LAPORAN PEMISAHAN DANA ---
if st.session_state.transaksi:
    st.write("---")
    st.header("📊 Laporan Realisasi Pemisahan Dana")
    
    total_omzet = sum(t['Omzet'] for t in st.session_state.transaksi)
    total_laba = sum(t['Laba'] for t in st.session_state.transaksi)
    total_prive = sum(t['Pribadi'] for t in st.session_state.transaksi)
    total_masuk_usaha = sum(t['Usaha'] for t in st.session_state.transaksi)

    # VISUAL PEMISAHAN (DOMPET)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""<div class="dompet-box" style="background-color: #00529b;">
        <h3>💼 UNTUK USAHA</h3><h2>{format_rupiah(total_masuk_usaha + st.session_state.modal_awal)}</h2>
        <small>(Modal Awal + Putaran Modal)</small></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="dompet-box" style="background-color: #28a745;">
        <h3>🙋 UNTUK SENDIRI</h3><h2>{format_rupiah(total_prive)}</h2>
        <small>(Gaji Owner / Jatah Jajan)</small></div>""", unsafe_allow_html=True)

    # LAPORAN FORMAT AKUNTANSI (WARNA BIRU)
    st.write(" ")
    st.markdown(f"""
    <div class="laporan-biru">
        <div class="header-lap">{nama_usaha}<br>Laporan Perubahan Modal & Prive</div>
        <table class="tabel-lap">
            <tr><td>Pendapatan Usaha (Omzet)</td><td style="text-align:right">{format_rupiah(total_omzet)}</td></tr>
            <tr><td>Total Laba Bersih</td><td style="text-align:right">{format_rupiah(total_laba)}</td></tr>
            <tr style="color: red;"><td><b>Pengambilan Pribadi (Prive {porsi_pribadi_persen}%)</b></td><td style="text-align:right"><b>({format_rupiah(total_prive)})</b></td></tr>
            <tr class="total-row"><td><b>TAMBAHAN MODAL USAHA</b></td><td style="text-align:right"><b>{format_rupiah(total_laba - total_prive)}</b></td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 **Tips Bank:** Dengan memisahkan jatah pribadi secara disiplin, skor kredit Anda di BRI akan meningkat karena modal usaha Anda aman.")

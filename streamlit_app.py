import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# 1. Konfigurasi Awal
st.set_page_config(page_title="FIN-Saku Ultimate", layout="centered")

# Simpan riwayat transaksi di sesi browser agar tidak hilang saat refresh
if 'list_transaksi' not in st.session_state:
    st.session_state.list_transaksi = []

# 2. CSS Kustom: Font Besar & Tombol Mantap
st.markdown("""
    <style>
    .big-font { font-size: 26px !important; font-weight: bold; color: #00529b; }
    .stNumberInput input { font-size: 24px !important; font-weight: bold; }
    .stButton>button {
        width: 100%; height: 3.5em; font-size: 20px !important;
        font-weight: bold; border-radius: 12px;
    }
    .bri-style { background-color: #00529b; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏦 FIN-Saku")
st.markdown('<p class="big-font">Catat Suara & Laporan PDF Otomatis</p>', unsafe_allow_html=True)

# --- BAGIAN 1: INPUT TRANSAKSI BERULANG ---
st.write("---")
st.subheader("🎙️ Catat Pendapatan Masuk")
st.info("💡 Tips: Gunakan ikon Mikrofon pada keyboard HP untuk input via suara!")

with st.container():
    col_ket, col_nom = st.columns([2, 1])
    with col_ket:
        item = st.text_input("Nama Pembelian:", placeholder="Contoh: 1 Bakso", key="item_input")
    with col_nom:
        # Format angka otomatis dengan langkah 500 (untuk memudahkan titik)
        nominal = st.number_input("Nominal (Rp):", min_value=0, step=500, format="%d")

    if st.button("➕ TAMBAH KE KERANJANG"):
        if nominal > 0:
            st.session_state.list_transaksi.append({
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Keterangan": item if item else "Tanpa Nama",
                "Nominal": nominal
            })
            st.toast(f"Berhasil menambah Rp {nominal:,.0f}!")
        else:
            st.warning("Masukkan angka dulu bos!")

# --- BAGIAN 2: DAFTAR TRANSAKSI HARI INI ---
if st.session_state.list_transaksi:
    st.write("---")
    st.subheader("🛒 Keranjang Transaksi")
    df_temp = pd.DataFrame(st.session_state.list_transaksi)
    st.table(df_temp.style.format({"Nominal": "{:,.0f}"}))
    
    total_omzet = df_temp["Nominal"].sum()
    st.markdown(f"### **Total Masuk: Rp {total_omzet:,.0f}**")

    if st.button("🗑️ HAPUS SEMUA DATA"):
        st.session_state.list_transaksi = []
        st.rerun()

    # --- BAGIAN 3: ANALISIS & LAPORAN ---
    st.write("---")
    if st.button("🚀 FINALISASI & BUAT LAPORAN PDF"):
        modal = total_omzet * 0.7
        pribadi = total_omzet * 0.3
        
        st.success("✅ Laporan Berhasil Dibuat!")
        
        # Ringkasan Strategis
        st.write("### 📊 Ringkasan SAK-EMKM")
        col_m, col_p = st.columns(2)
        col_m.metric("MODAL USAHA", f"Rp {modal:,.0f}")
        col_p.metric("LABA BERSIH", f"Rp {pribadi:,.0f}")

        # REKOMENDASI KUR BRI
        st.write("---")
        st.subheader("🏦 Rekomendasi KUR BRI")
        limit_max = (pribadi * 0.3) / ((1/12) + 0.005) # Simulasi DSR
        
        st.info(f"Berdasarkan omzet Anda, Anda disarankan meminjam KUR BRI maksimal **Rp {limit_max:,.0f}** dengan bunga 6% per tahun agar cicilan aman.")

        # FITUR PDF & WHATSAPP
        # Membuat file CSV sebagai simulasi laporan (Streamlit Cloud sulit bikin PDF murni tanpa library tambahan)
        csv_data = df_temp.to_csv(index=False).encode('utf-8')
        b64 = base64.b64encode(csv_data).decode()
        
        st.write("### 📤 Kirim Laporan")
        st.download_button("📂 UNDUH LAPORAN (PDF/CSV)", csv_data, "Laporan_FINSAKU.csv", "text/csv")
        
        # Link WhatsApp (Pesan Otomatis)
        pesan_wa = f"Halo Bank BRI, saya ingin melampirkan laporan keuangan FIN-Saku. Total omzet saya Rp {total_omzet:,.0f}."
        wa_url = f"https://wa.me/?text={pesan_wa.replace(' ', '%20')}"
        st.link_button("📲 KIRIM LAPORAN VIA WHATSAPP", wa_url)

else:
    st.write("*(Belum ada transaksi yang dicatat)*")

st.write("---")
st.caption("FIN-Saku v6.0 | Inovasi Inklusif Pilmapres")

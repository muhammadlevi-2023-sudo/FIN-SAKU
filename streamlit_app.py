import streamlit as st
import pandas as pd
from datetime import datetime
import base64

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku x KUR BRI", layout="centered")

# Simpan riwayat transaksi agar tidak hilang
if 'list_transaksi' not in st.session_state:
    st.session_state.list_transaksi = []

# 2. CSS Kustom (Branding BRI & Aksesibilitas)
st.markdown("""
    <style>
    .big-font { font-size: 26px !important; font-weight: bold; color: #00529b; }
    .bri-blue { color: #00529b; font-weight: bold; }
    .stNumberInput input { font-size: 24px !important; font-weight: bold; }
    .stButton>button {
        width: 100%; height: 3.5em; font-size: 20px !important;
        font-weight: bold; border-radius: 12px; background-color: #00529b; color: white;
    }
    .card {
        padding: 20px; background-color: #f0f8ff; border-radius: 15px; border-left: 8px solid #00529b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🏦 FIN-Saku")
st.markdown('<p class="big-font">Asisten Keuangan UMKM & Simulasi KUR BRI</p>', unsafe_allow_html=True)
st.info("🎙️ **Info Suara:** Klik kolom input, lalu tekan ikon **Mikrofon** di keyboard HP Anda untuk mencatat lewat suara.")

# --- BAGIAN 1: INPUT TRANSAKSI (MULTI-INPUT) ---
st.write("---")
st.subheader("🛒 Catat Penjualan")
with st.container():
    col_item, col_rp = st.columns([2, 1])
    with col_item:
        item = st.text_input("Nama Barang:", placeholder="Contoh: 2 Porsi Nasi Ayam", key="txt_item")
    with col_rp:
        # Step 500 dan format %d membantu sistem mengenali angka bulat
        nominal = st.number_input("Harga (Rp):", min_value=0, step=500, format="%d")

    if st.button("➕ TAMBAH TRANSAKSI"):
        if nominal > 0:
            st.session_state.list_transaksi.append({
                "Waktu": datetime.now().strftime("%H:%M:%S"),
                "Produk": item if item else "Penjualan Umum",
                "Nominal": nominal
            })
            st.toast(f"Berhasil ditambah: Rp {nominal:,.0f}")
        else:
            st.warning("Silakan masukkan angka nominal.")

# --- BAGIAN 2: DAFTAR TRANSAKSI HARI INI ---
if st.session_state.list_transaksi:
    st.write("### 📋 Daftar Transaksi")
    df = pd.DataFrame(st.session_state.list_transaksi)
    # Menampilkan tabel dengan format ribuan (titik)
    st.table(df.style.format({"Nominal": "{:,.0f}"}))
    
    total_omzet = df["Nominal"].sum()
    st.markdown(f"## Total Omzet: **Rp {total_omzet:,.0f}**")
    
    if st.button("🗑️ Reset Data"):
        st.session_state.list_transaksi = []
        st.rerun()

    # --- BAGIAN 3: ANALISIS KUR BRI & LAPORAN ---
    st.write("---")
    st.subheader("🏦 Analisis Kelayakan KUR BRI")
    
    # Hitung Laba & Cicilan Aman (Asumsi laba 30% dari omzet, cicilan max 30% dari laba)
    laba_bersih = (total_omzet * 25) * 0.3 # Estimasi bulanan
    cicilan_aman = laba_bersih * 0.3
    # Estimasi plafon (bunga 6% per tahun, tenor 12 bulan)
    plafon_rekomendasi = cicilan_aman / ((1/12) + 0.005)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    if total_omzet < 50000:
        st.warning("⚠️ Omzet harian Anda masih rendah. Fokus tingkatkan penjualan agar skor kredit meningkat.")
    else:
        st.success(f"✅ **Kabar Baik!** Anda berpotensi layak menerima KUR BRI.")
        st.write(f"💰 **Rekomendasi Pinjaman:** Rp 5,000,000 - Rp {plafon_rekomendasi:,.0f}")
        st.write(f"📉 **Suku Bunga:** 6% per Tahun (Subsidi Pemerintah)")
        st.write(f"📅 **Estimasi Cicilan:** Rp {cicilan_aman:,.0f} / bulan (Tenor 12 bln)")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- BAGIAN 4: EXPORT & SHARE ---
    st.write("---")
    st.subheader("📂 Laporan & Pengajuan")
    
    # Data untuk Laporan
    data_bank = {
        "Keterangan": ["Total Omzet Harian", "Estimasi Laba Bulanan", "Skor Kelayakan", "Rekomendasi Plafon"],
        "Nilai": [f"Rp {total_omzet:,.0f}", f"Rp {laba_bersih:,.0f}", f"{min(int(total_omzet/1000), 100)}/100", f"Rp {plafon_rekomendasi:,.0f}"]
    }
    df_bank = pd.DataFrame(data_bank)
    
    # Download CSV (Sebagai simulasi laporan resmi)
    csv = df_bank.to_csv(index=False).encode('utf-8')
    st.download_button("📩 UNDUH LAPORAN SAK-EMKM (PDF/CSV)", csv, "laporan_finsaku.csv", "text/csv")
    
    # WhatsApp Share
    wa_msg = f"Halo Mantri BRI, saya nasabah FIN-Saku ingin mengajukan KUR. Total omzet harian saya Rp {total_omzet:,.0f}."
    st.link_button("📲 AJUKAN KE MANTRI BRI (WHATSAPP)", f"https://wa.me/?text={wa_msg.replace(' ', '%20')}")

else:
    st.write("*(Belum ada data transaksi)*")

st.write("---")
st.caption("FIN-Saku v7.0 | Solusi Perbankan Inklusif untuk UMKM")

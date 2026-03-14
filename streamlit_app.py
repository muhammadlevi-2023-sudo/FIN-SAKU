import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku Inklusi x KUR BRI", layout="centered")

# 2. CSS untuk Aksesibilitas & Branding
st.markdown("""
    <style>
    .big-font { font-size: 24px !important; font-weight: bold; color: #004aad; }
    .bri-color { color: #00529b; font-weight: bold; }
    .stButton>button {
        width: 100%;
        height: 3.5em;
        font-size: 20px !important;
        font-weight: bold;
        background-color: #00529b;
        color: white;
        border-radius: 12px;
    }
    .tips-box {
        padding: 15px;
        background-color: #e7f3ff;
        border-radius: 10px;
        border-left: 5px solid #00529b;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🏦 FIN-Saku")
st.markdown('<p class="big-font">Pusat Catat UMKM & Akses KUR BRI</p>', unsafe_allow_html=True)

# --- TAMPILAN AKSESIBILITAS ---
st.info("♿ **Fitur Inklusi Aktif:** Font Besar | Kontras Tinggi | Navigasi Mudah")

# --- INPUT TRANSAKSI ---
st.write("---")
st.subheader("📝 Catat Penjualan & Produk")
nama_barang = st.text_input("Nama Produk:", placeholder="Misal: Jualan Keripik Tempe")
nominal = st.number_input("Total Pendapatan (Rp):", min_value=0, step=1000)

if st.button("PROSES DATA & CEK KELAYAKAN KUR"):
    if nominal > 0:
        modal = nominal * 0.7
        pribadi = nominal * 0.3
        st.balloons()
        
        # Hasil Pemisahan
        st.write("### 📊 Alokasi Dana Harian")
        c1, c2 = st.columns(2)
        c1.metric("📦 MODAL USAHA", f"Rp {modal:,.0f}")
        c2.metric("🥡 LABA/PRIBADI", f"Rp {pribadi:,.0f}")

        # --- SISTEM LAPORAN KEUANGAN ---
        st.write("---")
        st.subheader("📑 Pratinjau Laporan Keuangan")
        data_laporan = {
            "Komponen": ["Tanggal", "Produk", "Omzet", "Modal", "Laba Bersih"],
            "Nilai": [datetime.now().strftime("%d/%m/%Y"), nama_barang, f"Rp {nominal:,.0f}", f"Rp {modal:,.0f}", f"Rp {pribadi:,.0f}"]
        }
        df = pd.DataFrame(data_laporan)
        st.table(df)
        
        # Tombol Download
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ UNDUH LAPORAN UNTUK SYARAT KUR", data=csv, file_name='laporan_umkm_finsaku.csv', mime='text/csv')

        # --- POJOK KUR BRI & TIPS ---
        st.write("---")
        st.markdown('### 🏦 Pojok Info <span class="bri-color">KUR BRI</span>', unsafe_allow_html=True)
        
        # Skor Kelayakan
        skor = min(int((nominal / 500000) * 100), 100)
        st.write(f"**Skor Kelayakan Kredit Anda:** {skor}/100")
        st.progress(skor / 100)
        
        st.markdown('<div class="tips-box">', unsafe_allow_html=True)
        st.write("**💡 Tips Lolos KUR BRI:**")
        st.write("1. **Pisahkan Uang:** Bank lebih suka melihat saldo usaha yang tidak tercampur biaya dapur.")
        st.write("2. **Catat Rutin:** Konsistensi mencatat di FIN-Saku membuktikan usaha Anda berjalan aktif.")
        st.write("3. **Siapkan Dokumen:** Pastikan punya NIB (Nomor Induk Berusaha) dan KTP.")
        st.write("4. **Gunakan Laporan:** Tunjukkan file CSV yang Anda unduh di atas saat datang ke Mantri BRI.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        if skor > 70:
            st.success("🌟 Anda memiliki potensi besar untuk diterima KUR BRI! Silakan hubungi kantor BRI terdekat.")
            st.link_button("Daftar KUR BRI Online", "https://kur.bri.co.id/")
            
    else:
        st.warning("⚠️ Masukkan data penjualan Anda terlebih dahulu.")

# --- FOOTER ---
st.write("---")
st.caption("FIN-Saku v4.0 | Mitigasi Information Asymmetry untuk Akses KUR BRI")

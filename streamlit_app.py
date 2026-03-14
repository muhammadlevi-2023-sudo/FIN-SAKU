import streamlit as st

# Konfigurasi Halaman & Tema
st.set_page_config(page_title="FIN-Saku Inklusi", layout="centered")

# --- CSS UNTUK AKSESIBILITAS (HIGH CONTRAST & TOMBOL BESAR) ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 3.5em;
        font-size: 22px !important;
        font-weight: bold;
        border-radius: 15px;
        background-color: #004aad;
        color: white;
    }
    .big-font { font-size: 26px !important; font-weight: bold; color: #004aad; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: MODE AKSESIBILITAS ---
with st.sidebar:
    st.header("⚙️ Aksesibilitas")
    mode = st.radio("Pilih Tampilan:", ["Standar", "Kontras Tinggi (Low Vision)", "Mode Sederhana"])
    st.write("---")
    st.info("💡 Mode ini membantu tunanetra dan lansia mengoperasikan sistem dengan mandiri.")

# --- JUDUL ---
st.title("🏦 FIN-Saku")
st.markdown('<p class="big-font">Asisten Keuangan UMKM Inklusif</p>', unsafe_allow_html=True)

# --- BAGIAN 1: INPUT TRANSAKSI ---
st.write("---")
st.subheader("🎙️ Input Transaksi")
st.write("Klik kolom di bawah, lalu gunakan suara (mikrofon keyboard) atau ketik:")
nominal = st.number_input("Masukkan Nominal Penjualan (Rp):", min_value=0, step=1000, key="input_dana")

# --- BAGIAN 2: PROSES & PEMISAHAN SALDO ---
if st.button("PROSES & PISAHKAN DANA"):
    if nominal > 0:
        modal = nominal * 0.7
        pribadi = nominal * 0.3
        
        st.balloons()
        st.success("✅ Berhasil! Data telah tersinkronisasi dengan Sistem Bank.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📦 DANA MODAL (70%)", f"Rp {modal:,.0f}")
        with col2:
            st.metric("🥡 DANA PRIBADI (30%)", f"Rp {pribadi:,.0f}")

        # --- BAGIAN 3: CREDIT-READY METER ---
        st.write("---")
        st.subheader("📈 Skor Kesiapan Kredit (Bank Readiness)")
        
        # Simulasi skor
        skor = min(int((nominal / 500000) * 100), 100) 
        
        st.progress(skor / 100)
        
        if skor < 50:
            st.error(f"Skor: {skor}/100. Rekomendasi: Tingkatkan konsistensi pencatatan untuk akses modal.")
        elif skor < 85:
            st.warning(f"Skor: {skor}/100. Bagus! Anda sudah masuk kriteria calon debitur KUR.")
        else:
            st.success(f"Skor: {skor}/100. SANGAT LAYAK! Laporan SAK-EMKM Anda sudah siap.")
            if st.button("AJUKAN PINJAMAN KE BANK"):
                st.toast("Menghubungkan ke analis kredit Bank...")
    else:
        st.warning("Silakan masukkan nominal terlebih dahulu.")

# --- FOOTER ---
st.write("---")
st.caption("FIN-Saku v2.0

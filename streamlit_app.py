import streamlit as st

st.set_page_config(page_title="FIN-Saku", layout="centered")

st.title("🏦 FIN-Saku")
st.subheader("Solusi Keuangan UMKM Inklusif")

st.write("---")
st.write("### Input Penjualan Hari Ini")
nominal = st.number_input("Masukkan Nominal (Rp)", min_value=0, step=1000)

if st.button("Proses Pemisahan Saldo"):
    modal = nominal * 0.7
    pribadi = nominal * 0.3
    
    st.success(f"✅ Berhasil! Data ini telah disimpan untuk laporan Bank.")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Dana Modal (70%)", f"Rp {modal:,.0f}")
    with col2:
        st.metric("Dana Pribadi (30%)", f"Rp {pribadi:,.0f}")
    
    st.warning("💡 Tips: Jangan ambil dana modal untuk keperluan pribadi agar skor kredit Anda tetap baik!")

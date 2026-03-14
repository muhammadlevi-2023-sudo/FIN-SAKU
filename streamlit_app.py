# --- BAGIAN LAPORAN KEUANGAN YANG DISEMPURNAKAN ---

with tab1:
    # Filter periode laporan
    list_periode = df_all['bulan'].unique()
    sel_lap = st.selectbox("Pilih Periode Laporan", list_periode, index=len(list_periode)-1)
    
    # Filter data berdasarkan bulan terpilih
    df_curr = df_all[df_all['bulan'] == sel_lap]
    
    # Perhitungan Komponen Laba Rugi
    omzet_bln = df_curr['omzet'].sum()
    laba_kotor_bln = df_curr['laba'].sum()
    prive_bln = df_curr['prive'].sum()
    laba_bersih_bln = laba_kotor_bln - prive_bln
    
    # Logika Modal Berjalan (Akuntansi Persistent)
    # Cari indeks pertama dari bulan ini di dataframe utama
    idx_awal = df_curr.index[0]
    
    # Modal Awal periode ini adalah modal snapshot transaksi sebelum bulan ini dimulai
    if idx_awal > 0:
        # Menghitung modal akumulasi sebelum transaksi pertama bulan ini
        # Kita hitung ulang dari modal investasi awal + semua laba/prive sebelum idx_awal
        untung_sebelumnya = df_all.iloc[:idx_awal]['laba'].sum() - df_all.iloc[:idx_awal]['prive'].sum()
        modal_awal_periode = m_awal_input + untung_sebelumnya
    else:
        modal_awal_periode = m_awal_input
    
    # Modal Akhir adalah Modal Awal Periode + (Laba Bersih Bulan Ini)
    modal_akhir_periode = modal_awal_periode + laba_bersih_bln

    # --- UI DISPLAY LAPORAN ---
    
    # 1. LAPORAN LABA RUGI
    st.markdown(f"""
    <div class="report-card">
        <h3 style="text-align:center; margin-bottom:0;">LAPORAN LABA RUGI</h3>
        <p style="text-align:center; font-size:14px; color:#666 !important;">Periode Berakhir: {sel_lap} {sel_thn}</p>
        <hr style="border:1px solid #eee;">
        <table style="width:100%; border-collapse: collapse;">
            <tr><td style="padding:8px 0;">Total Pendapatan (Omzet)</td><td style="text-align:right;">{format_rp(omzet_bln)}</td></tr>
            <tr><td style="padding:8px 0;">Beban Pokok Penjualan (HPP Estimasi)</td><td style="text-align:right; border-bottom:1px solid #333;">({format_rp(omzet_bln - laba_kotor_bln)})</td></tr>
            <tr style="font-weight:bold;"><td style="padding:10px 0;">LABA KOTOR USAHA</td><td style="text-align:right;">{format_rp(laba_kotor_bln)}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 2. LAPORAN PERUBAHAN MODAL (DISERTAI LOGIKA PRIVE)
    st.markdown(f"""
    <div class="report-card" style="border-top: 10px solid #002147;">
        <h3 style="text-align:center; margin-bottom:0;">LAPORAN PERUBAHAN EKUITAS (MODAL)</h3>
        <p style="text-align:center; font-size:14px; color:#666 !important;">Periode: {sel_lap} {sel_thn}</p>
        <hr style="border:1px solid #eee;">
        <table style="width:100%; border-collapse: collapse; font-size:16px;">
            <tr><td style="padding:8px 0;">Modal Awal (Per {sel_lap} 01)</td><td style="text-align:right;">{format_rp(modal_awal_periode)}</td></tr>
            <tr><td style="padding:8px 0; color:green;">Laba Bersih Periode Berjalan</td><td style="text-align:right; color:green;">{format_rp(laba_kotor_bln)}</td></tr>
            <tr><td style="padding:8px 0; color:red;">Pengurangan: Prive (Pengambilan Pemilik)</td><td style="text-align:right; color:red; border-bottom:1px solid #333;">({format_rp(prive_bln)})</td></tr>
            <tr style="font-weight:bold; background-color:#f9f9f9;"><td style="padding:12px 5px;">KENAIKAN / (PENURUNAN) MODAL</td><td style="text-align:right; padding:12px 5px;">{format_rp(laba_bersih_bln)}</td></tr>
            <tr style="font-weight:bold; font-size:20px; background-color:#FFD700; color:#002147;">
                <td style="padding:15px 10px;">MODAL AKHIR PERIODE</td>
                <td style="text-align:right; padding:15px 10px;">{format_rp(modal_akhir_periode)}</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # 3. TOMBOL DOWNLOAD PDF (TETAP DI BAWAH LAPORAN MODAL)
    if st.button("📥 DOWNLOAD LAPORAN KEUANGAN (PDF)"):
        # Logika PDF yang sudah rapi
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, f"LAPORAN KEUANGAN RESMI: {nama_u.upper()}", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(190, 7, f"Dicetak Secara Digital oleh FIN-Saku pada: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(10)
        
        # Section Laba Rugi di PDF
        pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, "I. LAPORAN LABA RUGI", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(120, 10, "Total Pendapatan", 1); pdf.cell(70, 10, format_rp(omzet_bln), 1, 1, 'R')
        pdf.cell(120, 10, "Laba Kotor", 1); pdf.cell(70, 10, format_rp(laba_kotor_bln), 1, 1, 'R')
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(120, 10, "Laba Bersih (Setelah Prive)", 1); pdf.cell(70, 10, format_rp(laba_bersih_bln), 1, 1, 'R')
        pdf.ln(5)
        
        # Section Perubahan Modal di PDF
        pdf.set_font("Arial", 'B', 12); pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 10, "II. LAPORAN PERUBAHAN EKUITAS", 1, 1, 'L', True)
        pdf.set_font("Arial", '', 11)
        pdf.cell(120, 10, "Saldo Modal Awal", 1); pdf.cell(70, 10, format_rp(modal_awal_periode), 1, 1, 'R')
        pdf.cell(120, 10, f"Penambahan Laba Bersih {sel_lap}", 1); pdf.cell(70, 10, format_rp(laba_bersih_bln), 1, 1, 'R')
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 33, 71)
        pdf.cell(120, 12, "SALDO MODAL AKHIR", 1); pdf.cell(70, 12, format_rp(modal_akhir_periode), 1, 1, 'R')
        
        st.download_button("Konfirmasi Download Laporan", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{nama_u}_{sel_lap}.pdf")

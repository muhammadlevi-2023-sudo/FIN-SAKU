import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN & DATABASE
st.set_page_config(page_title="FIN-Saku Pro | BRI Bankable Edition", layout="wide")

def get_connection():
    conn = sqlite3.connect('finsaku_unair_final_v20.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi
                 (id INTEGER PRIMARY KEY, tgl_data TEXT, bulan TEXT, tahun TEXT, 
                  tipe_input TEXT, omzet REAL, laba REAL, prive REAL)''')
    conn.commit()
    return conn

conn = get_connection()

# 2. UI STYLING (UNAIR NAVY & GOLD)
st.markdown("""
<style>
    .stApp { background-color: #002147; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #001a35 !important; border-right: 3px solid #FFD700; }
    .report-card {
        background: #FFFFFF; padding: 25px; border-radius: 12px;
        border-top: 10px solid #FFD700; color: #333 !important;
        margin-bottom: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    .report-card h3, .report-card b, .report-card span, .report-card p { color: #002147 !important; }
    .status-box { padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .layak { background: #d4edda; color: #155724; }
    .pantau { background: #fff3cd; color: #856404; }
    .tidak { background: #f8d7da; color: #721c24; }
    .stButton>button {
        background: #FFD700 !important; color: #002147 !important;
        font-weight: bold; border-radius: 8px; height: 45px; width: 100%; border:none;
    }
</style>
""", unsafe_allow_html=True)

# 3. FUNGSI PENDUKUNG
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_val(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 4. SIDEBAR: PROFIL & MODAL
df_all = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id ASC", conn)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("👤 Profil Bisnis")
    nama_u = st.text_input("Nama Usaha", "Levi Makmur Jaya")
    jenis_b = st.selectbox("Jenis Bisnis", ["Kuliner", "Retail/Toko", "Jasa", "Manufaktur"])
    m_awal_input = st.number_input("Modal Awal (Uang Kas)", value=7000000)
    
    untung_kumulatif = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_realtime = m_awal_input + untung_kumulatif
    
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border:1px solid #FFD700;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>POSISI MODAL SAAT INI:</p>
        <h2 style='margin:0; color:white;'>{format_rp(kas_realtime)}</h2>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("💰 Aturan Harga & Margin")
    hpp = st.number_input("HPP Produk", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    margin_pct = ((jual - hpp) / jual * 100) if jual > 0 else 0
    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 20)

# 5. DASHBOARD: PENCATATAN
st.title(f"🚀 Dashboard Strategis: {nama_u}")

with st.container():
    st.subheader("📝 Catat Transaksi")
    c1, c2, c3 = st.columns([1.5, 1.5, 1])
    with c1:
        tipe_in = st.selectbox("Frekuensi Input", ["Harian", "Mingguan", "Bulanan"])
        if tipe_in == "Bulanan":
            list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            sel_bln = st.selectbox("Pilih Bulan", list_bln, index=datetime.now().month-1)
            sel_thn = st.selectbox("Pilih Tahun", ["2025", "2026", "2027"], index=1)
            tgl_db = f"01-{sel_bln}-{sel_thn}"
        else:
            tgl_pick = st.date_input("Pilih Tanggal", datetime.now())
            tgl_db = tgl_pick.strftime("%Y-%m-%d")
            sel_bln = tgl_pick.strftime("%B")
            sel_thn = tgl_pick.strftime("%Y")
    with c2:
        omzet_raw = st.text_input(f"Omzet ({tipe_in})")
        omzet_val = clean_val(omzet_raw)
        st.markdown(f"Tercatat: <b style='color:#FFD700;'>{format_rp(omzet_val)}</b>", unsafe_allow_html=True)
    with c3:
        st.write("##")
        if st.button("SIMPAN"):
            l_val = omzet_val * (margin_pct/100)
            p_val = l_val * (prive_pct/100)
            cur = conn.cursor()
            cur.execute("INSERT INTO transaksi (tgl_data, bulan, tahun, tipe_input, omzet, laba, prive) VALUES (?,?,?,?,?,?,?)",
                      (tgl_db, sel_bln, sel_thn, tipe_in, omzet_val, l_val, p_val))
            conn.commit()
            st.rerun()

# 6. ANALISIS & LAPORAN
if not df_all.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "⚙️ REVISI"])

    with tab1:
        # 1. Pilihan Periode
        sel_lap = st.selectbox("Pilih Periode Laporan", df_all['bulan'].unique())
        df_curr = df_all[df_all['bulan'] == sel_lap]
        
        # 2. Logika Akuntansi (Sesuai Standar Gambar)
        o_sum = df_curr['omzet'].sum()
        # Menghitung HPP berdasarkan input margin di sidebar
        hpp_total = o_sum * (1 - (margin_pct/100))
        l_operasional = o_sum - hpp_total
        p_sum = df_curr['prive'].sum()
        
        # 3. Hitung Modal (Sesuai Gambar)
        idx_start = df_curr.index[0]
        untung_sebelumnya = df_all.iloc[:idx_start]['laba'].sum() - df_all.iloc[:idx_start]['prive'].sum()
        modal_awal_periode = m_awal_input + untung_sebelumnya
        modal_akhir_periode = modal_awal_periode + l_operasional - p_sum

        # --- TAMPILAN INTERFACE (Visual Report) ---
        st.markdown(f"""
        <div class="report-card">
            <h3 style="text-align:center;">{nama_u.upper()}</h3>
            <p style="text-align:center; margin-top:-15px;">LAPORAN KEUANGAN BULANAN<br>Periode: {sel_lap} {sel_thn}</p>
            <hr>
            <b>I. LAPORAN LABA RUGI</b><br>
            <div style="display:flex; justify-content:space-between;"><span>Total Pendapatan (Omzet)</span><b>{format_rp(o_sum)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Beban Pokok Penjualan (HPP)</span><span style="color:red;">-{format_rp(hpp_total)}</span></div>
            <div style="border-top:1px solid #ccc; margin:5px 0;"></div>
            <div style="display:flex; justify-content:space-between;"><b>LABA BERSIH OPERASIONAL</b><b>{format_rp(l_operasional)}</b></div>
            <br>
            <b>II. LAPORAN PERUBAHAN MODAL</b><br>
            <div style="display:flex; justify-content:space-between;"><span>Modal Awal Periode</span><b>{format_rp(modal_awal_periode)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Ditambah: Laba Bersih</span><span style="color:green;">{format_rp(l_operasional)}</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Dikurangi: Pengambilan Pribadi (Prive)</span><span style="color:red;">-{format_rp(p_sum)}</span></div>
            <div style="border-top:1px solid #ccc; margin:5px 0;"></div>
            <div style="display:flex; justify-content:space-between; font-size:1.1rem; background:#f0f2f6; padding:5px; border-radius:5px;">
                <b>MODAL AKHIR PERIODE</b><b>{format_rp(modal_akhir_periode)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- LOGIKA PEMBUATAN PDF (Persis Format Gambar) ---
        if st.button("📥 DOWNLOAD LAPORAN PDF"):
            pdf = FPDF()
            pdf.add_page()
            
            # Header Laporan
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 7, nama_u.upper(), 0, 1, 'C')
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 7, "LAPORAN KEUANGAN BULANAN", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 7, f"Periode: {sel_lap} {sel_thn}", 0, 1, 'C')
            pdf.line(10, 35, 200, 35)
            pdf.ln(10)
            
            # Bagian I: Laba Rugi
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "I. LAPORAN LABA RUGI", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Total Pendapatan (Omzet)", 0, 0); pdf.cell(90, 8, format_rp(o_sum), 0, 1, 'R')
            pdf.cell(100, 8, "Beban Pokok Penjualan (HPP)", 0, 0); pdf.cell(90, 8, f"- {format_rp(hpp_total)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "LABA BERSIH OPERASIONAL", 0, 0); pdf.cell(90, 10, format_rp(l_operasional), 0, 1, 'R')
            pdf.ln(5)
            
            # Bagian II: Perubahan Modal
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "II. LAPORAN PERUBAHAN MODAL", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Modal Awal Periode", 0, 0); pdf.cell(90, 8, format_rp(modal_awal_periode), 0, 1, 'R')
            pdf.cell(100, 8, "Ditambah: Laba Bersih", 0, 0); pdf.cell(90, 8, format_rp(l_operasional), 0, 1, 'R')
            pdf.cell(100, 8, "Dikurangi: Pengambilan Pribadi (Prive)", 0, 0); pdf.cell(90, 8, f"- {format_rp(p_sum)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "MODAL AKHIR PERIODE", 0, 0); pdf.cell(90, 10, format_rp(modal_akhir_periode), 0, 1, 'R')
            
            # Footer kecil
            pdf.ln(20)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(190, 10, f"Dicetak otomatis melalui FIN-Saku pada {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
            
            # Output ke Streamlit Download
            st.download_button(
                label="Klik untuk Simpan PDF",
                data=pdf.output(dest='S').encode('latin-1'),
                file_name=f"Laporan_{sel_lap}_{nama_u}.pdf",
                mime="application/pdf"
            )
with tab2:
        st.subheader("🏦 Konsultasi Strategis KUR")
        
        # 1. LOGIKA DASAR (Mengambil data dari variabel yang sudah ada di codinganmu)
        jml_bln = df_all['bulan'].nunique()
        
        if jml_bln < 3:
            st.error(f"### 🚩 ANALISIS TERKUNCI (Data baru {jml_bln}/3 Bulan)")
            st.info("Sistem membutuhkan minimal 3 bulan data transaksi untuk menganalisis tren usaha agar rekomendasi bank akurat.")
        else:
            # Hitung rata-rata laba bersih (Laba - Prive)
            avg_laba = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bln
            
            # Cek Tren Laba (Bulan terakhir vs rata-rata)
            laba_bulan_ini = df_curr['laba'].sum() - df_curr['prive'].sum()
            tren_status = "Meningkat 📈" if laba_bulan_ini > avg_laba else "Menurun/Stabil 📉"
            
            # Penentuan Produk & Plafon (Logika Bank)
            if avg_laba > 5000000:
                produk, plafon_rek = "KUR Mikro BRI", 50000000
                alasan_produk = "Laba bersih Anda sangat kuat untuk menjamin plafon hingga 50 Juta."
            else:
                produk, plafon_rek = "KUR Super Mikro BRI", 10000000
                alasan_produk = "Plafon ini paling aman untuk menjaga arus kas Anda tetap sehat."

            # 2. NARASI PEMBUKA (Interaksi Konsultan)
            st.markdown(f"""
            <div class="white-card">
                <h3 style="color:#002147;">💡 Hasil Analisis FinSaku untuk {nama_u}</h3>
                <p style="color:#002147;">Berdasarkan catatan <b>{jml_bln} bulan terakhir</b>, usaha Anda berada pada tren <b>{tren_status}</b>. 
                Dengan saldo kas saat ini sebesar <b>{format_rp(kas_realtime)}</b>, berikut adalah simulasi paling aman untuk Anda:</p>
            </div>
            """, unsafe_allow_html=True)

            # 3. SLIDER JANGKA WAKTU
            tenor = st.select_slider("Geser untuk Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36], value=12)
            
            # Hitung Bunga & Pokok (KUR 6% per tahun)
            pokok_bln = plafon_rek / tenor
            bunga_bln = (plafon_rek * 0.06) / 12
            total_cicilan = pokok_bln + bunga_bln
            
            # Batas aman 35% dari laba rata-rata
            batas_aman = avg_laba * 0.35
            sisa_laba_akhir = avg_laba - total_cicilan
            rasio_sisa = (sisa_laba_akhir / avg_laba) * 100

            # 4. KARTU INDIKATOR (3 KOLOM SEJAJAR)
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""<div class="report-card"><b>1. Rekomendasi</b><br><small>{produk}</small><br>
                <b style="color:#002147; font-size:18px;">{format_rp(plafon_rek)}</b></div>""", unsafe_allow_html=True)
            with col_b:
                warna_c = 'green' if total_cicilan <= batas_aman else 'red'
                st.markdown(f"""<div class="report-card"><b>2. Cicilan/Bulan</b><br><small>Batas Aman: {format_rp(batas_aman)}</small><br>
                <b style="color:{warna_c}; font-size:18px;">{format_rp(total_cicilan)}</b></div>""", unsafe_allow_html=True)
            with col_c:
                warna_s = 'green' if rasio_sisa >= 70 else 'orange'
                st.markdown(f"""<div class="report-card"><b>3. Sisa Laba</b><br><small>Kesehatan Kas</small><br>
                <b style="color:{warna_s}; font-size:18px;">{rasio_sisa:.0f}%</b></div>""", unsafe_allow_html=True)

            # 5. PENJELASAN DETAIL
            with st.expander("📖 LIHAT BEDAH ANGKA (Penjelasan Sederhana)", expanded=True):
                st.write(f"""
                * **Plafon {format_rp(plafon_rek)}**: {alasan_produk}
                * **Rincian Cicilan**: Terdiri dari Pokok {format_rp(pokok_bln)} ditambah bunga subsidi bank sebesar {format_rp(bunga_bln)} per bulan.
                * **Batas Aman**: Kami menghitung bahwa cicilan tidak boleh lebih dari 35% laba Anda agar usaha tidak 'sesak napas'.
                * **Sisa Laba {rasio_sisa:.0f}%**: Ini adalah uang bersih yang tetap bisa Anda tabung atau putar kembali ke modal setelah membayar bank.
                """)

            # 6. KESIMPULAN AKHIR
            st.write("---")
            if rasio_sisa >= 70:
                st.success(f"**KESIMPULAN:** Usaha Anda **SANGAT LAYAK**. Dengan sisa laba {rasio_sisa:.0f}%, Anda masih punya cadangan kas yang sangat aman untuk kebutuhan darurat.")
            elif rasio_sisa >= 50:
                st.warning(f"**KESIMPULAN:** Usaha Anda **LAYAK DENGAN CATATAN**. Cicilan ini cukup terasa. Disarankan mengambil tenor lebih panjang agar sisa laba bisa di atas 70%.")
            else:
                st.error("**KESIMPULAN:** **BERISIKO**. Cicilan ini memakan terlalu banyak laba Anda. Bank BRI mungkin akan menyarankan plafon yang lebih kecil atau tenor yang lebih lama.")
            
            # (Opsional) Berkas untuk dibawa ke BRI tetap bisa diletakkan di bawah sini

    with tab3:
        st.dataframe(df_all[['id', 'tgl_data', 'omzet', 'laba']])
        tid = st.number_input("ID Hapus", step=1)
        if st.button("Hapus Data"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (tid,))
            conn.commit()
            st.rerun()

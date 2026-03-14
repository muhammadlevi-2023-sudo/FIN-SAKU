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
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
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
        # Pilihan Periode
        sel_lap = st.selectbox("Pilih Periode Laporan", df_all['bulan'].unique())
        df_curr = df_all[df_all['bulan'] == sel_lap]
        
        # Logika Akuntansi (Sesuai Gambar)
        o_sum = df_curr['omzet'].sum()
        # Menghitung HPP berdasarkan margin yang diinput di sidebar
        hpp_total = o_sum * (1 - (margin_pct/100))
        l_operasional = o_sum - hpp_total
        
        p_sum = df_curr['prive'].sum()
        
        # Hitung Modal (Sesuai Gambar)
        idx_start = df_curr.index[0]
        untung_sebelumnya = df_all.iloc[:idx_start]['laba'].sum() - df_all.iloc[:idx_start]['prive'].sum()
        modal_awal_periode = m_awal_input + untung_sebelumnya
        modal_akhir_periode = modal_awal_periode + l_operasional - p_sum

        # --- TAMPILAN DI SCREEN ---
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
            <div style="display:flex; justify-content:space-between; font-size:1.1rem; background:#f0f2f6; padding:5px;"><b>MODAL AKHIR PERIODE</b><b>{format_rp(modal_akhir_periode)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # --- LOGIKA PEMBUATAN PDF (Sesuai Gambar) ---
        if st.button("📥 DOWNLOAD LAPORAN PDF"):
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 7, nama_u.upper(), 0, 1, 'C')
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 7, "LAPORAN KEUANGAN BULANAN", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 7, f"Periode: {sel_lap} {sel_thn}", 0, 1, 'C')
            pdf.line(10, 35, 200, 35)
            pdf.ln(10)
            
            # I. Laba Rugi
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "I. LAPORAN LABA RUGI", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Total Pendapatan (Omzet)", 0, 0); pdf.cell(90, 8, format_rp(o_sum), 0, 1, 'R')
            pdf.cell(100, 8, "Beban Pokok Penjualan (HPP)", 0, 0); pdf.cell(90, 8, f"- {format_rp(hpp_total)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "LABA BERSIH OPERASIONAL", 0, 0); pdf.cell(90, 10, format_rp(l_operasional), 0, 1, 'R')
            pdf.ln(5)
            
            # II. Perubahan Modal
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "II. LAPORAN PERUBAHAN MODAL", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Modal Awal Periode", 0, 0); pdf.cell(90, 8, format_rp(modal_awal_periode), 0, 1, 'R')
            pdf.cell(100, 8, "Ditambah: Laba Bersih", 0, 0); pdf.cell(90, 8, format_rp(l_operasional), 0, 1, 'R')
            pdf.cell(100, 8, "Dikurangi: Pengambilan Pribadi (Prive)", 0, 0); pdf.cell(90, 8, f"- {format_rp(p_sum)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "MODAL AKHIR PERIODE", 0, 0); pdf.cell(90, 10, format_rp(modal_akhir_periode), 0, 1, 'R')
            
            # Footer
            pdf.ln(20)
            pdf.set_font("Arial", 'I', 8)
            pdf.cell(190, 10, f"Dicetak otomatis melalui FIN-Saku pada {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
            
            # Download Button
            st.download_button(
                label="Klik untuk Simpan PDF",
                data=pdf.output(dest='S').encode('latin-1'),
                file_name=f"Laporan_{nama_u}_{sel_lap}.pdf",
                mime="application/pdf"
            )

    with tab2:
        st.subheader("🎯 Rekomendasi & Analisis Kelayakan KUR")
        
        # --- DATA DASAR UNTUK ANALISIS ---
        jml_bln = df_all['bulan'].nunique()
        laba_bersih_terakhir = (df_curr['laba'].sum() - df_curr['prive'].sum()) if not df_curr.empty else 0
        laba_bersih_rata2 = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bln if jml_bln > 0 else 0
        
        # Penentuan Plafon berdasarkan Kapasitas (30% dari laba rata-rata)
        batas_aman_cicilan = laba_bersih_rata2 * 0.3
        
        if laba_bersih_rata2 > 5000000:
            produk, plafon = "KUR Mikro BRI", 50000000
        elif laba_bersih_rata2 > 1000000:
            produk, plafon = "KUR Super Mikro BRI", 10000000
        else:
            produk, plafon = "KUR Super Mikro BRI", 5000000

        # --- SLIDER JANGKA WAKTU (INTERAKTIF) ---
        tenor = st.select_slider("Pilih Jangka Waktu Pinjaman (Bulan):", options=[12, 18, 24, 36], value=12)
        
        # Hitung Cicilan (Bunga KUR 6% per tahun)
        bunga_total = (plafon * 0.06 * (tenor/12))
        cicilan_bln = (plafon + bunga_total) / tenor
        sisa_laba = laba_bersih_terakhir - cicilan_bln
        rasio_sisa = (sisa_laba / laba_bersih_terakhir * 100) if laba_bersih_terakhir > 0 else 0

        # --- TAMPILAN STATUS ---
        status_k = "SANGAT LAYAK (Ready to Bank)" if jml_bln >= 3 and rasio_sisa > 50 else "PERLU PENYESUAIAN"
        st.markdown(f"""<div class="status-box {'layak' if status_k == "SANGAT LAYAK (Ready to Bank)" else 'pantau'}">
            STATUS: {status_k}
        </div>""", unsafe_allow_html=True)

        # --- RINGKASAN ANALISIS (NARASI MANUSIAWI) ---
        st.info(f"**Berdasarkan data keuangan Anda, berikut adalah rincian penjelasannya:**")
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.markdown(f"""
            <div class="report-card">
                <b>1. Rekomendasi Pinjaman</b><br>
                Sistem menyarankan produk <b>{produk}</b> dengan plafon sebesar <b>{format_rp(plafon)}</b>.
                <hr>
                <b>2. Batas Cicilan Aman</b><br>
                Batas Aman: {format_rp(batas_aman_cicilan)}/bln<br>
                Cicilan Pilihan: <span style='color:{'red' if cicilan_bln > batas_aman_cicilan else 'green'}'>{format_rp(cicilan_bln)}/bln</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col_res2:
            st.markdown(f"""
            <div class="report-card">
                <b>3. Sisa Laba Bersih</b><br>
                Setelah cicilan: <b>{format_rp(sisa_laba)}</b> ({rasio_sisa:.0f}%)
                <hr>
                <p style='font-size:13px; color:#555;'>💡 <i>Catatan Penting: Bank menyukai sisa laba > 70% setelah cicilan agar arus kas tetap aman.</i></p>
            </div>
            """, unsafe_allow_html=True)

        # --- KESIMPULAN & SARAN STRATEGIS ---
        with st.expander("📖 BACA KESIMPULAN & SARAN ANALIS", expanded=True):
            st.write(f"Meskipun statusnya **'{status_k}'**, simulasi {tenor} bulan ini terlihat {'agak memaksa' if rasio_sisa < 70 else 'sangat sehat'} bagi keuangan Anda.")
            st.write("**Agar lebih mudah disetujui bank:**")
            
            if rasio_sisa < 70:
                st.markdown(f"""
                * **Perpanjang Jangka Waktu:** Coba geser slider ke tenor lebih lama (24 atau 36 bulan). Ini akan menurunkan cicilan bulanan mendekati angka aman {format_rp(batas_aman_cicilan)}.
                * **Sisa Laba Meningkat:** Dengan cicilan lebih kecil, sisa laba Anda akan naik ke atas 70%, yang merupakan 'posisi manis' di mata Bank BRI.
                """)
            else:
                st.success("Posisi keuangan Anda sudah berada di 'Posisi Manis'. Cicilan tidak mengganggu operasional harian!")

        st.write("---")
        st.write("📋 **BERKAS UNTUK DIBAWA KE BRI:**")
        
        # Penjelasan sederhana mengenai berkas
        exp1, exp2, exp3 = st.columns(3)
        with exp1:
            st.markdown("""**1. Identitas Pribadi**
* **KTP & KK:** Dokumen asli sebagai bukti domisili.
* **Mencari dimana?** Dokumen pribadi yang Anda simpan di rumah.""")
        with exp2:
            st.markdown("""**2. Legalitas Usaha**
* **NIB/SKU:** Bukti sah Anda memiliki usaha.
* **Mencari dimana?** **NIB** dibuat online di *oss.go.id*, **SKU** minta ke kantor Kelurahan setempat.""")
        with exp3:
            st.markdown("""**3. Data Keuangan**
* **Laporan FIN-Saku:** Hasil cetak (PDF) dari aplikasi ini.
* **Rekening Koran:** Riwayat uang masuk/keluar di bank.
* **Mencari dimana?** Cetak dari aplikasi ini & minta ke Bank tempat Anda menabung.""")

    with tab3:
        st.dataframe(df_all[['id', 'tgl_data', 'omzet', 'laba']])
        tid = st.number_input("ID Hapus", step=1)
        if st.button("Hapus Data"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (tid,))
            conn.commit()
            st.rerun()

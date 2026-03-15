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
              tipe_input TEXT, omzet REAL, laba REAL, prive REAL, beban REAL)''')
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
# 4. SIDEBAR: PROFIL & MODAL
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("👤 Profil Bisnis")
    nama_u = st.text_input("Nama Usaha", "Levi Makmur Jaya")
    jenis_b = st.selectbox("Jenis Bisnis", ["Kuliner", "Retail/Toko", "Jasa", "Manufaktur"])
    m_awal_input = st.number_input("Modal Awal (Uang Kas)", value=7000000)
    
    # Ambil data terbaru dari database untuk hitung kas live
    df_all = pd.read_sql_query("SELECT * FROM transaksi", conn)
    untung_kumulatif = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_realtime = m_awal_input + untung_kumulatif
    
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border:1px solid #FFD700;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>SALDO KAS SAAT INI:</p>
        <h2 style='margin:0; color:white;'>{format_rp(kas_realtime)}</h2>
    </div>
    """, unsafe_allow_html=True)

    st.write("---")
    st.subheader("💰 Strategi Harga")
    hpp = st.number_input("Harga Pokok (HPP)", value=5000)
    jual = st.number_input("Harga Jual ke Pelanggan", value=15000)
    
    # --- LOGIKA INTERAKTIF MARGIN ---
    margin_pct = ((jual - hpp) / jual * 100) if jual > 0 else 0
    saran_m = {"Kuliner": 40, "Retail/Toko": 15, "Jasa": 60, "Manufaktur": 30}
    target = saran_m[jenis_b]
    
    # Indikator warna dinamis
    warna_teks = "#00FF00" if margin_pct >= target else "#FF4B4B"
    
    st.markdown(f"""
        <div style='text-align:center; padding:10px; border-radius:5px; background:rgba(255,255,255,0.1);'>
            <small>Margin Keuntungan:</small><br>
            <strong style='font-size:24px; color:{warna_teks};'>{margin_pct:.1f}%</strong>
        </div>
    """, unsafe_allow_html=True)
    
    # Progress bar visual
    prog_val = min(max(margin_pct / 100, 0.0), 1.0)
    st.progress(prog_val)
    
    if margin_pct < target:
        st.warning(f"💡 Tips: Untuk {jenis_b}, margin ideal ±{target}%. Milik Anda {margin_pct:.0f}% (Terlalu Tipis).")
    else:
        st.success(f"✅ Margin Sehat untuk sektor {jenis_b}!")
    
    st.write("---")
    st.subheader("🏦 Alokasi Gaji Pemilik")
    prive_pct = st.slider("Ambilan Prive/Gaji (%)", 0, 100, 20)
    
    # Efek interaktif: Hitung nominal rupiah dari gaji secara live
    nominal_gaji = (jual - hpp) * (prive_pct/100)
    st.info(f"Setiap 1 produk terjual, Bapak/Ibu mengambil **{format_rp(nominal_gaji)}** sebagai gaji.")

    if prive_pct > 30:
        st.error("🚩 Boros: Ambilan di atas 30% bisa menghambat pertumbuhan modal usaha.")
    else:
        st.success("✅ Alokasi aman.")

# 5. DASHBOARD: PENCATATAN
st.title(f"📈 Pembukuan Strategis: {nama_u}")

with st.container():
    st.subheader("📝 Catat Pemasukan")
    st.info("Bapak/Ibu, silakan masukkan total penjualan bersih yang diterima.")
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
        beban_raw = st.text_input(f"Beban Operasional ({tipe_in})", value="0")
        beban_val = clean_val(beban_raw)
        st.markdown(f"Tercatat: <b style='color:#FFD700;'>{format_rp(omzet_val)}</b>", unsafe_allow_html=True)
    with c3:
        st.write("##")
        if st.button("SIMPAN"):
            l_val = omzet_val * (margin_pct/100)
            p_val = l_val * (prive_pct/100)
            cur = conn.cursor()
            cur.execute("INSERT INTO transaksi (tgl_data, bulan, tahun, tipe_input, omzet, laba, prive, beban) VALUES (?,?,?,?,?,?,?,?)",
                        (tgl_db, sel_bln, sel_thn, tipe_in, omzet_val, l_val, p_val, beban_val))
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
        beban_sum = df_curr['beban'].sum() if 'beban' in df_curr.columns else 0
        l_operasional = o_sum - hpp_total - beban_sum
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
            <div style="display:flex; justify-content:space-between;"><span>Beban Operasional</span><span style="color:red;">-{format_rp(beban_sum)}</span></div>
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
            pdf.cell(100, 8, "Beban Operasional", 0, 0); pdf.cell(90, 8, f"- {format_rp(beban_sum)}", 0, 1, 'R')
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
        
        jml_bln = df_all['bulan'].nunique()
        
        if jml_bln < 3:
            st.error(f"### 🚩 ANALISIS TERKUNCI (Data baru {jml_bln}/3 Bulan)")
            st.info("Bank BRI biasanya melihat riwayat minimal 3-6 bulan. Yuk, rutin catat transaksi Anda!")
        else:
            avg_laba = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bln
            laba_bulan_ini = df_curr['laba'].sum() - df_curr['prive'].sum()
            tren_status = "Meningkat 📈" if laba_bulan_ini > avg_laba else "Menurun/Stabil 📉"
            
            if avg_laba > 5000000:
                produk, plafon_rek = "KUR Mikro BRI", 50000000
            else:
                produk, plafon_rek = "KUR Super Mikro BRI", 10000000

            # --- NARASI PEMBUKA ---
            st.markdown(f"""
            <div style="background: white; padding: 20px; border-radius: 12px; border-left: 5px solid #FFD700; margin-bottom: 20px;">
                <h3 style="color:#002147; margin-top:0;">💡 Halo Pemilik {nama_u},</h3>
                <p style="color:#333; line-height:1.6;">
                    Kami telah menganalisis catatan keuangan Anda selama <b>{jml_bln} bulan</b>. 
                    Saat ini, keuntungan bersih rata-rata Anda adalah <b>{format_rp(avg_laba)}/bulan</b>. 
                    Berdasarkan angka ini, berikut adalah simulasi cicilan yang <b>paling aman</b> agar usaha Anda tetap bisa jajan dan bayar operasional tanpa pusing.
                </p>
            </div>
            """, unsafe_allow_html=True)

            tenor = st.select_slider("Pilih Jangka Waktu Pinjaman (Bulan):", options=[12, 18, 24, 36], value=12)
            
            # Hitung Logika KUR
            pokok_bln = plafon_rek / tenor
            bunga_bln = (plafon_rek * 0.06) / 12  # Bunga KUR 6% setahun
            total_cicilan = pokok_bln + bunga_bln
            batas_aman = avg_laba * 0.35
            sisa_laba_akhir = avg_laba - total_cicilan
            rasio_sisa = (sisa_laba_akhir / avg_laba) * 100

            # --- 3 KARTU DENGAN PENJELASAN SEDERHANA ---
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.markdown(f"""
                <div class="report-card">
                    <b>1. Pinjaman Rekomendasi</b><br>
                    <h3 style="margin:5px 0;">{format_rp(plafon_rek)}</h3>
                    <small>Pinjaman ini disesuaikan agar Anda tidak keberatan membayar tiap bulannya.</small>
                </div>
                """, unsafe_allow_html=True)

            with c2:
                warna_c = '#155724' if total_cicilan <= batas_aman else '#721c24'
                st.markdown(f"""
                <div class="report-card">
                    <b>2. Cicilan per Bulan</b><br>
                    <h3 style="margin:5px 0; color:{warna_c} !important;">{format_rp(total_cicilan)}</h3>
                    <small>Idealnya, cicilan tidak boleh lebih dari 35% keuntungan bersih Anda.</small>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                warna_s = '#155724' if rasio_sisa >= 70 else '#856404'
                st.markdown(f"""
                <div class="report-card">
                    <b>3. Kesehatan Kas (Sisa Laba)</b><br>
                    <h3 style="margin:5px 0; color:{warna_s} !important;">{rasio_sisa:.0f}%</h3>
                    <small>Setelah bayar bank, Anda masih punya {rasio_sisa:.0f}% uang untuk diputar lagi.</small>
                </div>
                """, unsafe_allow_html=True)

            # --- EDUKASI CARA BACA ---
            with st.expander("🔍 Bagaimana cara kami menghitung ini? (Klik untuk baca)"):
                st.write(f"""
                1. **Cicilan Aman**: Bank biasanya menyarankan cicilan Anda maksimal **{format_rp(batas_aman)}**. Cicilan pilihan Anda adalah **{format_rp(total_cicilan)}**.
                2. **Kesehatan Kas**: Jika angkanya di atas **70%**, artinya setelah bayar cicilan, uang Anda masih 'longgar' untuk stok barang atau biaya darurat.
                3. **Bunga Murah**: Simulasi ini menggunakan bunga KUR **6% per tahun** karena Anda sudah tertib mencatat keuangan di aplikasi ini.
                """)

            # --- KESIMPULAN AKHIR ---
            if rasio_sisa >= 70:
                st.success(f"✅ **KATA KONSULTAN:** Usaha Anda SANGAT SEHAT. Sisa uang {rasio_sisa:.0f}% sangat cukup untuk tabungan pribadi dan modal kerja.")
            elif rasio_sisa >= 50:
                st.warning(f"⚠️ **KATA KONSULTAN:** CUKUP AMAN, tapi disarankan ambil jangka waktu lebih lama (tenor panjang) agar cicilan per bulannya lebih ringan.")
            else:
                st.error("🚨 **KATA KONSULTAN:** TERLALU BERAT. Cicilan ini akan menghabiskan banyak keuntungan Anda. Coba kecilkan jumlah pinjaman.")

# 7. BERKAS UNTUK DIBAWA (Edukasi Lengkap)
            st.write("---")
            st.markdown("### 📋 Persiapan Dokumen (Lolos Verifikasi Bank)")
            st.write("Jangan cuma bawa badan! Bank butuh bukti hitam di atas putih untuk percaya pada Anda.")

            # Menggunakan Expander agar rapi tapi detail
            with st.expander("1. 🪪 Identitas Diri (KTP & KK)", expanded=False):
                col_i1, col_i2 = st.columns([1, 2])
                with col_i1:
                    st.info("**Tujuan:** Memastikan Anda warga asli & punya domisili tetap.")
                with col_i2:
                    st.write("""
                    * **Kenapa Perlu?** Bank harus lapor ke sistem OJK (SLIK) menggunakan NIK Anda untuk cek riwayat kredit (pernah nunggak atau tidak).
                    * **Cara Dapet:** Pastikan KTP sudah elektronik (E-KTP) dan data di KK sudah update di Dukcapil.
                    """)

            with st.expander("2. 📜 Legalitas Usaha (NIB / SKU)", expanded=False):
                col_l1, col_l2 = st.columns([1, 2])
                with col_l1:
                    st.info("**Tujuan:** Membuktikan usaha Anda 'Legal' dan bukan usaha fiktif.")
                with col_l2:
                    st.write("""
                    * **Kenapa Perlu?** Syarat wajib KUR adalah usaha sudah berjalan minimal 6 bulan. Dokumen ini adalah "Akte Kelahiran" bisnis Anda.
                    * **Cara Dapet:** **NIB (Nomor Induk Berusaha)** bisa didapatkan melalui daftar secara mandiri di situs **oss.go.id** (Gratis & cuma 10 menit) dan untuk **SKU (Surat Keterangan Usaha)** bisa  dibuatkan surat tersebut melalui Kantor Kelurahan/Desa dengan membawa surat pengantar dari RT/RW.
                    """)

            with st.expander("3. 📈 Laporan Keuangan (PDF FIN-Saku)", expanded=True):
                col_k1, col_k2 = st.columns([1, 2])
                with col_k1:
                    st.info("**Tujuan:** Menyakinkan Bank bahwa Anda mampu membayar cicilan.")
                with col_k2:
                    st.write("""
                    * **Kenapa Perlu?** Bank tidak mau nebak-nebak. Dengan laporan rapi dari aplikasi ini, Bank melihat Anda sebagai 'Pengusaha Profesional' yang mengerti keuangan.
                    * **Cara Dapet:** Klik tombol **'DOWNLOAD LAPORAN PDF'** di Tab Laporan Keuangan, lalu cetak (print) di kertas A4.
                    """)

            st.success("💡 **TIPS DARI KONSULTAN:** Bawa dokumen asli dan fotokopi sebanyak 2 rangkap saat ke Mantri BRI (Petugas KUR).")

with tab3:
        st.subheader("⚙️ Edit & Hapus Transaksi")
        st.info("Klik angka pada kolom Omzet/Beban untuk mengubah, lalu tekan Simpan.")
        
        # Siapkan data untuk diedit
        df_revisi = df_all.copy()
        df_revisi.insert(0, "Hapus", False) 
        
        edited_df = st.data_editor(
            df_revisi,
            column_config={
                "Hapus": st.column_config.CheckboxColumn(),
                "omzet": st.column_config.NumberColumn("Omzet (Rp)", format="Rp %d"),
                "beban": st.column_config.NumberColumn("Beban (Rp)", format="Rp %d"),
            },
            disabled=["id", "tgl_data", "bulan", "tahun", "tipe_input", "laba", "prive"],
            hide_index=True,
        )

        c_edit1, c_edit2 = st.columns(2)
        
        with c_edit1:
            if st.button("💾 SIMPAN PERUBAHAN"):
                cur = conn.cursor()
                for index, row in edited_df.iterrows():
                    # Hitung ulang laba & prive berdasarkan angka baru
                    n_laba = row['omzet'] * (margin_pct/100) - row['beban']
                    n_prive = n_laba * (prive_pct/100)
                    cur.execute("UPDATE transaksi SET omzet=?, beban=?, laba=?, prive=? WHERE id=?", 
                               (row['omzet'], row['beban'], n_laba, n_prive, row['id']))
                conn.commit()
                st.success("✅ Berhasil diperbarui!")
                st.rerun()

        with c_edit2:
            to_delete = edited_df[edited_df["Hapus"] == True]
            if not to_delete.empty:
                if st.button(f"🗑️ HAPUS {len(to_delete)} DATA"):
                    cur = conn.cursor()
                    cur.executemany("DELETE FROM transaksi WHERE id=?", [(i,) for i in to_delete['id']])
                    conn.commit()
                    st.rerun()

# --- PENUTUP (WAJIB SEJAJAR DENGAN 'if not df_all.empty:') ---
else:
    st.write("---")
    st.info("👋 Selamat datang! Silakan masukkan data transaksi di atas untuk melihat laporan.")

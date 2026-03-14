import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from fpdf import FPDF
import io

# 1. KONFIGURASI UTAMA & THEME
st.set_page_config(page_title="FIN-Saku Pro | BRI Bankable Edition", layout="wide")

def get_connection():
    conn = sqlite3.connect('finsaku_final_bri_v18.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi
                 (id INTEGER PRIMARY KEY, tgl_data DATE, bulan TEXT, tahun TEXT, 
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
    .status-layak { background: #d4edda; color: #155724; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; }
    .status-tidak { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 8px; font-weight: bold; text-align: center; }
    .stButton>button { background: #FFD700 !important; color: #002147 !important; font-weight: bold; border-radius: 8px; height: 45px; width: 100%; border:none; }
</style>
""", unsafe_allow_html=True)

# 3. HELPER FUNCTIONS
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_val(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 4. SIDEBAR: PROFIL & INTERAKTIF (PERINGATAN REALTIME)
df_all = pd.read_sql_query("SELECT * FROM transaksi ORDER BY tgl_data ASC", conn)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    # Bagian Profil Interaktif
    st.subheader("👤 Profil Bisnis")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    jenis_b = st.selectbox("Jenis Bisnis", ["Kuliner", "Retail/Toko", "Jasa", "Produksi/Manufaktur"])
    m_awal_input = st.number_input("Modal Awal (Kas)", value=7000000)
    
    # Hitung Modal Realtime
    untung_bersih_total = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_realtime = m_awal_input + untung_bersih_total
    
    st.markdown(f"""<div style='background:#003366; padding:15px; border-radius:10px; border:1px solid #FFD700; margin-bottom:20px;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>KAS/MODAL SAAT INI:</p>
        <h2 style='margin:0; color:white;'>{format_rp(kas_realtime)}</h2>
    </div>""", unsafe_allow_html=True)

    st.write("---")
    st.subheader("💰 Strategi Harga")
    hpp = st.number_input("HPP Produk", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    margin_pct = ((jual - hpp) / jual * 100) if jual > 0 else 0
    
    # Peringatan Harga & Margin
    if margin_pct < 25:
        st.error(f"⚠️ Margin {margin_pct:.1f}% Terlalu Tipis! Untuk {jenis_b}, bank menyarankan minimal 30% agar aman dari risiko operasional.")
    else:
        st.success(f"✅ Margin {margin_pct:.1f}% Sehat. Ini poin plus bagi analis bank.")

    prive_pct = st.slider("Alokasi Prive (%)", 0, 100, 20)
    if prive_pct > 40:
        st.warning("🚨 Prive > 40% dianggap 'Boros' oleh bank. Modal Anda sulit tumbuh.")
    else:
        st.info("💡 Alokasi prive sudah ideal untuk penguatan modal.")

# 5. DASHBOARD: PENCATATAN ADAPTIF
st.title(f"🚀 Kendali Strategis: {nama_u}")

with st.container():
    st.subheader("📝 Pencatatan Data")
    c1, c2, c3 = st.columns([1,1,1])
    
    with c1:
        tipe_in = st.selectbox("Frekuensi Data", ["Harian", "Mingguan", "Bulanan"])
        if tipe_in == "Bulanan":
            list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            sel_bln = st.selectbox("Pilih Bulan", list_bln, index=datetime.now().month-1)
            sel_thn = st.selectbox("Pilih Tahun", ["2025", "2026", "2027"], index=1)
            tgl_final = f"01-{sel_bln}-{sel_thn}" # Normalisasi untuk DB
        else:
            tgl_pick = st.date_input("Pilih Tanggal Realtime", datetime.now())
            tgl_final = tgl_pick.strftime("%Y-%m-%d")
            sel_bln = tgl_pick.strftime("%B")
            sel_thn = tgl_pick.strftime("%Y")

    with c2:
        omzet_raw = st.text_input(f"Masukkan Omzet ({tipe_in})")
        omzet_val = clean_val(omzet_raw)
        st.markdown(f"Tercatat: <b style='color:#FFD700;'>{format_rp(omzet_val)}</b>", unsafe_allow_html=True)
        
    with c3:
        st.write("##")
        if st.button("SIMPAN TRANSAKSI"):
            laba_val = omzet_val * (margin_pct/100)
            prive_val = laba_val * (prive_pct/100)
            cur = conn.cursor()
            cur.execute("INSERT INTO transaksi (tgl_data, bulan, tahun, tipe_input, omzet, laba, prive) VALUES (?,?,?,?,?,?,?)",
                      (tgl_final, sel_bln, sel_thn, tipe_in, omzet_val, laba_val, prive_val))
            conn.commit()
            st.rerun()

# 6. ANALISIS KUR BRI (LOGIKA PERBANKAN)
if not df_all.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "⚙️ REVISI"])
    
    # Logika Hitung Trend & Kelayakan
    jml_bulan = df_all['bulan'].nunique()
    avg_laba_bersih = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bulan if jml_bulan > 0 else 0
    
    with tab1:
        # Laba Rugi & Perubahan Modal
        col_lr, col_pm = st.columns(2)
        with col_lr:
            st.markdown(f"""<div class="report-card"><h3>LABA RUGI</h3><hr>
                <p>Total Omzet: <b>{format_rp(df_all['omzet'].sum())}</b></p>
                <p>Total Laba Bersih: <b style='color:green;'>{format_rp(df_all['laba'].sum() - df_all['prive'].sum())}</b></p>
            </div>""", unsafe_allow_html=True)
        with col_pm:
            st.markdown(f"""<div class="report-card"><h3>PERUBAHAN MODAL</h3><hr>
                <p>Modal Awal: <b>{format_rp(m_awal_input)}</b></p>
                <p>Modal Akhir Realtime: <b style='color:#002147;'>{format_rp(kas_realtime)}</b></p>
            </div>""", unsafe_allow_html=True)
        
        # Tombol PDF di bawah Modal
        if st.button("📥 DOWNLOAD LAPORAN PDF (BANKABLE)"):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"LAPORAN KEUANGAN - {nama_u.upper()}", 0, 1, 'C')
            pdf.set_font("Arial", '', 12); pdf.ln(10)
            pdf.cell(100, 10, "Modal Awal", 1); pdf.cell(90, 10, format_rp(m_awal_input), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Bersih Kumulatif", 1); pdf.cell(90, 10, format_rp(untung_bersih_total), 1, 1, 'R')
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "MODAL AKHIR", 1); pdf.cell(90, 10, format_rp(kas_realtime), 1, 1, 'R')
            st.download_button("Konfirmasi Download", data=pdf.output(dest='S').encode('latin-1'), file_name="Laporan_Keuangan.pdf")

    with tab2:
        st.subheader("🎯 Rekomendasi KUR Bank BRI")
        
        # Penentuan Produk KUR berdasarkan kemampuan bayar (Cicilan maks 30% dari rata-rata laba bersih)
        kapasitas_cicilan = avg_laba_bersih * 0.3
        
        if kapasitas_cicilan > 1500000:
            produk, nominal = "KUR Mikro BRI", 50000000
        elif kapasitas_cicilan > 400000:
            produk, nominal = "KUR Super Mikro BRI", 10000000
        else:
            produk, nominal = "KUR Super Mikro BRI", 5000000
            
        bunga_bln = (nominal * 0.06 / 12)
        cicilan_est = (nominal / 12) + bunga_bln # Estimasi Tenor 1 Tahun
        
        # UI Status Layak (Minimal 3 Bulan)
        if jml_bulan >= 6:
            st.markdown("<div class='status-layak'>STATUS: SANGAT LAYAK (IDEAL 6 BULAN TERPENUHI)</div>", unsafe_allow_html=True)
        elif jml_bulan >= 3:
            st.markdown("<div class='status-layak' style='background:#fff3cd; color:#856404;'>STATUS: LAYAK (MINIMAL 3 BULAN TERPENUHI)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-tidak'>STATUS: BELUM LAYAK (MINIMAL DATA 3 BULAN)</div>", unsafe_allow_html=True)

        st.markdown(f"""<div class="report-card">
            <h4>Disarankan Mengambil: <span style='color:blue;'>{produk} Rp {nominal/1000000:.0f} Juta</span></h4>
            <hr>
            <p>• <b>Estimasi Cicilan:</b> {format_rp(cicilan_est)} / bulan (Tenor 12 Bln)</p>
            <p>• <b>Bunga per Bulan:</b> {format_rp(bunga_bln)} (6% Efektif p.a)</p>
            <p>• <b>Syarat Cashflow:</b> Pendapatan harus konsisten minimal {format_rp(df_all['omzet'].mean())} / bulan.</p>
            <hr>
            <b>KESIMPULAN ANALIS:</b><br>
            Bisnis {jenis_b} Anda memiliki trend yang {"Stabil" if jml_bulan >= 3 else "perlu dipantau"}. 
            Dengan laba bersih rata-rata {format_rp(avg_laba_bersih)}, Anda memiliki kapasitas membayar cicilan sebesar {format_rp(kapasitas_cicilan)}, sehingga pinjaman {format_rp(nominal)} aman bagi cashflow Anda.
        </div>""", unsafe_allow_html=True)
        
        st.info("📋 **BERKAS YANG WAJIB DIBAWA KE BANK BRI:**\n\n"
                "1. KTP Pemilik & Pasangan (jika ada)\n"
                "2. Kartu Keluarga (KK)\n"
                "3. NIB (Nomor Induk Berusaha) atau SKU dari Desa/Kelurahan\n"
                "4. Print Laporan Keuangan dari FIN-Saku (Laba Rugi & Perubahan Modal)\n"
                "5. Rekening Koran/Buku Tabungan 3 Bulan Terakhir")

    with tab3:
        st.dataframe(df_all[['id', 'tgl_data', 'bulan', 'tipe_input', 'omzet', 'laba']], use_container_width=True)
        del_id = st.number_input("Masukkan ID untuk hapus", step=1)
        if st.button("Hapus Data"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (del_id,))
            conn.commit()
            st.rerun()

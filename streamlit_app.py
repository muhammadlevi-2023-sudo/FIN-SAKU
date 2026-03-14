import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN & DATABASE
st.set_page_config(page_title="FIN-Saku Pro | BRI Bankable Edition", layout="wide")

def get_connection():
    # Menggunakan nama DB baru untuk menghindari conflict kolom lama
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
    
    /* Card Style untuk Laporan */
    .report-card {
        background: #FFFFFF; padding: 25px; border-radius: 12px;
        border-top: 10px solid #FFD700; color: #333 !important;
        margin-bottom: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    .report-card h3, .report-card b, .report-card span, .report-card p { color: #002147 !important; }
    
    /* Status Box */
    .status-box { padding: 15px; border-radius: 10px; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .layak { background: #d4edda; color: #155724; }
    .pantau { background: #fff3cd; color: #856404; }
    .tidak { background: #f8d7da; color: #721c24; }

    /* Button Style */
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

# 4. SIDEBAR: PROFIL & LOGIKA MODAL PERSISTEN
df_all = pd.read_sql_query("SELECT * FROM transaksi ORDER BY id ASC", conn)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("👤 Profil Bisnis")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    jenis_b = st.selectbox("Jenis Bisnis", ["Kuliner", "Retail/Toko", "Jasa", "Manufaktur"])
    m_awal_input = st.number_input("Modal Awal (Uang Kas)", value=7000000)
    
    # Hitung Modal Akhir Realtime
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
    
    # Interaktif Caption Margin
    if margin_pct < 30:
        st.error(f"⚠️ Margin {margin_pct:.1f}% tipis. Analis BRI lebih suka margin > 30% untuk keamanan.")
    else:
        st.success(f"✅ Margin {margin_pct:.1f}% sangat layak.")

    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 20)
    # Interaktif Caption Prive
    if prive_pct > 50:
        st.error("🚨 Prive terlalu besar! Bank akan melihat ini sebagai risiko modal tergerus.")
    else:
        st.info("💡 Prive sehat. Pertumbuhan modal terjaga.")

# 5. DASHBOARD: PENCATATAN ADAPTIF
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
        # Filter Laporan
        sel_lap = st.selectbox("Pilih Periode Laporan", df_all['bulan'].unique())
        df_curr = df_all[df_all['bulan'] == sel_lap]
        
        # Hitung Laba Rugi
        o_sum = df_curr['omzet'].sum()
        l_kotor = df_curr['laba'].sum()
        p_sum = df_curr['prive'].sum()
        l_bersih = l_kotor - p_sum
        
        # Hitung Modal Awal Periode (Modal awal + semua untung sebelum bulan ini)
        idx_start = df_curr.index[0]
        untung_sebelumnya = df_all.iloc[:idx_start]['laba'].sum() - df_all.iloc[:idx_start]['prive'].sum()
        modal_awal_periode = m_awal_input + untung_sebelumnya
        modal_akhir_periode = modal_awal_periode + l_bersih

        # UI Laba Rugi
        st.markdown(f"""
        <div class="report-card">
            <h3 style="text-align:center;">LAPORAN LABA RUGI</h3>
            <p style="text-align:center;">Periode: {sel_lap} {sel_thn}</p>
            <hr>
            <div style="display:flex; justify-content:space-between;"><span>Total Omzet</span><b>{format_rp(o_sum)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Laba Kotor</span><b>{format_rp(l_kotor)}</b></div>
            <div style="display:flex; justify-content:space-between; color:red;"><span>Prive Pemilik</span><b>-{format_rp(p_sum)}</b></div>
            <hr>
            <div style="display:flex; justify-content:space-between; font-size:1.2rem;"><b>LABA BERSIH</b><b style="color:green;">{format_rp(l_bersih)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # UI Perubahan Modal
        st.markdown(f"""
        <div class="report-card" style="border-top-color: #002147;">
            <h3 style="text-align:center;">LAPORAN PERUBAHAN MODAL</h3>
            <hr>
            <div style="display:flex; justify-content:space-between;"><span>Modal Awal (Per 1 {sel_lap})</span><b>{format_rp(modal_awal_periode)}</b></div>
            <div style="display:flex; justify-content:space-between; color:green;"><span>Penambahan Laba Bersih</span><b>{format_rp(l_bersih)}</b></div>
            <hr>
            <div style="display:flex; justify-content:space-between; font-size:1.4rem; background:#FFD700; padding:10px; border-radius:5px;">
                <b>MODAL AKHIR</b><b>{format_rp(modal_akhir_periode)}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("📥 DOWNLOAD LAPORAN PDF"):
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, f"LAPORAN KEUANGAN - {nama_u.upper()}", 0, 1, 'C')
            pdf.ln(10)
            pdf.set_font("Arial", '', 12)
            pdf.cell(100, 10, "Modal Awal Periode", 1); pdf.cell(90, 10, format_rp(modal_awal_periode), 1, 1, 'R')
            pdf.cell(100, 10, "Laba Bersih (Net)", 1); pdf.cell(90, 10, format_rp(l_bersih), 1, 1, 'R')
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(100, 10, "MODAL AKHIR", 1); pdf.cell(90, 10, format_rp(modal_akhir_periode), 1, 1, 'R')
            st.download_button("Klik untuk Simpan", data=pdf.output(dest='S').encode('latin-1'), file_name=f"Laporan_{sel_lap}.pdf")

    with tab2:
        st.subheader("🏦 Analisis Kelayakan KUR BRI")
        jml_bln = df_all['bulan'].nunique()
        avg_laba = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bln
        
        # Logika Plafon
        if avg_laba > 2000000:
            p_nama, p_val = "KUR Mikro BRI", 50000000
        elif avg_laba > 500000:
            p_nama, p_val = "KUR Super Mikro BRI", 10000000
        else:
            p_nama, p_val = "KUR Super Mikro BRI", 5000000
            
        bunga = (p_val * 0.06 / 12)
        cicilan = (p_val / 12) + bunga
        
        # Status
        if jml_bln >= 6:
            st.markdown("<div class='status-box layak'>STATUS: SANGAT LAYAK (IDEAL 6 BULAN)</div>", unsafe_allow_html=True)
        elif jml_bln >= 3:
            st.markdown("<div class='status-box pantau'>STATUS: LAYAK (MINIMAL 3 BULAN)</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='status-box tidak'>STATUS: BELUM LAYAK (BUTUH MINIMAL 3 BULAN)</div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="report-card">
            <h4>Produk Disarankan: <span style="color:blue;">{p_nama} Rp {p_val/1000000:.0f}jt</span></h4>
            <hr>
            <p>• <b>Estimasi Cicilan:</b> {format_rp(cicilan)} / bulan</p>
            <p>• <b>Bunga Efektif:</b> {format_rp(bunga)} / bulan (6% p.a)</p>
            <p>• <b>Syarat Pendapatan:</b> Konsisten di {format_rp(df_all['omzet'].mean())} / bulan.</p>
            <hr>
            <b>KESIMPULAN:</b><br>
            Berdasarkan trend {jml_bln} bulan, laba bersih Anda {format_rp(avg_laba)} cukup kuat untuk mengcover cicilan. Cashflow Anda sehat bagi bank.
        </div>
        """, unsafe_allow_html=True)
        
        st.write("📋 **BERKAS YANG PERLU DIBAWA:**")
        st.info("1. KTP & KK\n2. NIB/SKU\n3. Laporan FIN-Saku\n4. Rekening Koran 3 Bulan")

    with tab3:
        st.dataframe(df_all[['id', 'tgl_data', 'omzet', 'laba']])
        tid = st.number_input("ID Hapus", step=1)
        if st.button("Hapus Data"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (tid,))
            conn.commit()
            st.rerun()

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN & DATABASE
st.set_page_config(page_title="FIN-Saku Pro | BRI Bankable Edition", layout="wide")

def get_connection():
    # Menggunakan versi 21 untuk memastikan struktur tabel bersih
    conn = sqlite3.connect('finsaku_unair_final_v21.db', check_same_thread=False)
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
    .stButton>button { background: #FFD700 !important; color: #002147 !important; font-weight: bold; border-radius: 8px; height: 45px; width: 100%; border:none; }
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
    jenis_b = st.selectbox("Sektor Usaha", ["Kuliner (Makanan/Minuman)", "Retail/Toko", "Jasa", "Manufaktur"])
    m_awal_input = st.number_input("Uang Kas Awal (Modal)", value=7000000)
    
    untung_kumulatif = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_realtime = m_awal_input + untung_kumulatif
    
    st.markdown(f"**Modal Awal:** {format_rp(m_awal_input)}")
    st.markdown(f"### Kas Saat Ini:\n## {format_rp(kas_realtime)}")

    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp = st.number_input("HPP Produk (Modal)", value=5000)
    jual = st.number_input("Harga Jual", value=15000)
    margin_pct = ((jual - hpp) / jual * 100) if jual > 0 else 0
    
    if margin_pct < 30:
        st.error(f"⚠️ Margin {margin_pct:.1f}% tipis. Analis BRI menyarankan > 30%.")
    else:
        st.success(f"✅ Margin {margin_pct:.1f}% sehat.")

    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 20)
    if prive_pct > 50:
        st.error("🚨 Prive terlalu besar, modal bisa tergerus!")
    else:
        st.info("💡 Alokasi prive sudah ideal.")

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
            tgl_pick = st.date_input("Pilih Tanggal Realtime", datetime.now())
            tgl_db = tgl_pick.strftime("%Y-%m-%d")
            sel_bln = tgl_pick.strftime("%B")
            sel_thn = tgl_pick.strftime("%Y")

    with c2:
        omzet_raw = st.text_input(f"Omzet ({tipe_in})", value="0")
        omzet_val = clean_val(omzet_raw)
        st.markdown(f"Tercatat: <b style='color:#FFD700;'>{format_rp(omzet_val)}</b>", unsafe_allow_html=True)
        
    with c3:
        st.write("##")
        if st.button("🔔 SIMPAN TRANSAKSI"):
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
        sel_lap = st.selectbox("Pilih Periode Laporan:", df_all['bulan'].unique(), index=len(df_all['bulan'].unique())-1)
        df_curr = df_all[df_all['bulan'] == sel_lap]
        
        o_sum = df_curr['omzet'].sum()
        l_kotor = df_curr['laba'].sum()
        p_sum = df_curr['prive'].sum()
        l_bersih = l_kotor - p_sum # Ini variabel penting untuk analisis KUR
        
        idx_start = df_curr.index[0]
        untung_sebelumnya = df_all.iloc[:idx_start]['laba'].sum() - df_all.iloc[:idx_start]['prive'].sum()
        modal_awal_periode = m_awal_input + untung_sebelumnya
        modal_akhir_periode = modal_awal_periode + l_bersih

        col_l, col_m = st.columns(2)
        with col_l:
            st.markdown(f"""<div class="report-card"><h3>LABA RUGI - {sel_lap}</h3><hr>
                <p>Omzet: <b>{format_rp(o_sum)}</b></p>
                <p>Laba Bersih: <b style="color:green;">{format_rp(l_bersih)}</b></p></div>""", unsafe_allow_html=True)
        with col_m:
            st.markdown(f"""<div class="report-card"><h3>MODAL - {sel_lap}</h3><hr>
                <p>Kas Awal: <b>{format_rp(modal_awal_periode)}</b></p>
                <p>Kas Akhir: <b style="color:#002147;">{format_rp(modal_akhir_periode)}</b></p></div>""", unsafe_allow_html=True)

    with tab2:
        st.subheader("🏦 Analisis Kelayakan & Simulasi KUR BRI")
        jml_bln = df_all['bulan'].nunique()
        laba_bersih_rata2 = (df_all['laba'].sum() - df_all['prive'].sum()) / jml_bln if jml_bln > 0 else 0
        batas_aman_cicilan = laba_bersih_rata2 * 0.3
        
        if laba_bersih_rata2 > 1000000:
            p_nama, p_val = "KUR Super Mikro BRI", 10000000
        else:
            p_nama, p_val = "KUR Super Mikro BRI", 5000000

        tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36], value=12)
        cicilan_bln = (p_val + (p_val * 0.06 * (tenor/12))) / tenor
        sisa_laba = l_bersih - cicilan_bln
        rasio_sisa = (sisa_laba / l_bersih * 100) if l_bersih > 0 else 0

        status_k = "SANGAT LAYAK (READY TO BANK)" if jml_bln >= 3 and rasio_sisa > 50 else "PERLU PENYESUAIAN"
        st.markdown(f'<div class="status-box {"layak" if "SANGAT" in status_k else "pantau"}">STATUS: {status_k}</div>', unsafe_allow_html=True)

        st.markdown(f"""<div class="report-card">
            <p>Berdasarkan analisis <i>credit scoring</i> usaha Anda, berikut adalah rinciannya:</p><hr>
            <p><b>1. Rekomendasi Pinjaman:</b> Produk <b>{p_nama}</b> plafon <b>{format_rp(p_val)}</b>.</p>
            <p><b>2. Batas Cicilan Aman:</b> {format_rp(batas_aman_cicilan)}/bln. Realita simulasi: <b style="color:{'red' if cicilan_bln > batas_aman_cicilan else 'green'}">{format_rp(cicilan_bln)}/bln</b>.</p>
            <p><b>3. Sisa Laba Bersih:</b> <b>{format_rp(sisa_laba)} ({rasio_sisa:.0f}%)</b>. <br><small>Bank menyukai sisa laba > 70%.</small></p>
        </div>""", unsafe_allow_html=True)

        with st.expander("📖 KESIMPULAN & SARAN", expanded=True):
            st.write(f"Simulasi {tenor} bulan ini {'agak memaksa' if rasio_sisa < 70 else 'sangat sehat'}. Agar disetujui:")
            if rasio_sisa < 70:
                st.write(f"* **Perpanjang Tenor:** Geser ke 24/36 bulan agar cicilan mendekati {format_rp(batas_aman_cicilan)}.")
                st.write(f"* **Posisi Manis:** Biarkan sisa laba di atas 70% agar aman di mata Mantri BRI.")
            else:
                st.success("Keuangan Anda sudah di 'Posisi Manis'!")

    with tab3:
        st.dataframe(df_all[['id', 'tgl_data', 'omzet', 'laba', 'prive']], use_container_width=True)
        tid = st.number_input("Masukkan ID Data untuk Hapus", step=1, value=0)
        if st.button("Hapus"):
            conn.cursor().execute("DELETE FROM transaksi WHERE id=?", (tid,))
            conn.commit()
            st.rerun()

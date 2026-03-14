import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
# Menggunakan nama database baru untuk memastikan struktur bersih
conn = sqlite3.connect('finsaku_final_fixed.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try:
        abs_angka = abs(float(angka))
        formatted = "{:,.0f}".format(abs_angka).replace(",", ".")
        return f"Rp {formatted}" if angka >= 0 else f"Rp -{formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
# Perbaikan ValueError: Gunakan errors='coerce' agar data rusak tidak membuat aplikasi mati
if not df.empty:
    df['tgl_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df = df.dropna(subset=['tgl_dt'])

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner (Makanan/Minuman)", "Retail", "Jasa", "Produksi"])
    
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal (Modal)", "7000000"))
    
    # Hitung Modal Realtime
    total_laba = df['laba'].sum() if not df.empty else 0
    total_prive = df['prive'].sum() if not df.empty else 0
    kas_sekarang = modal_awal + total_laba - total_prive
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(kas_sekarang)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    if hrg_val > 0:
        margin = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin: **{margin:.1f}%**")
        if "Kuliner" in sektor and margin < 40:
            st.warning("💡 Tips: Kuliner butuh margin min 40% (cover risiko waste).")
    
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)

# --- INPUT TRANSAKSI ---
st.title(f"Dashboard: {nama_u}")
with st.container():
    st.subheader("📝 Catat Penjualan")
    c1, c2 = st.columns(2)
    with c1: tgl_in = st.date_input("Tanggal", datetime.now())
    with c2: omzet_in = st.number_input("Total Omzet", min_value=0, step=10000)

    if st.button("🚀 SIMPAN TRANSAKSI"):
        laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
        p_in = laba_in * (prive_pct / 100)
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?)",
                  (tgl_in.strftime("%Y-%m-%d"), tgl_in.strftime("%B %Y"), f"Minggu {tgl_in.isocalendar()[1]}", omzet_in, laba_in, p_in, "Harian"))
        conn.commit()
        st.rerun()

# --- TAB LAPORAN & KUR ---
if not df.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])

    with tab1:
        # Perbaikan KeyError: Langsung ambil kolom 'bulan'
        list_bulan = sorted(df['bulan'].unique().tolist())
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        
        db_bulan = df[df['bulan'] == sel_b]
        o_bln = db_bulan['omzet'].sum()
        l_bln = db_bulan['laba'].sum()
        
        # Perbaikan Laba/Modal Berjalan
        idx = list_bulan.index(sel_b)
        laba_lalu = df[df['bulan'].isin(list_bulan[:idx])]['laba'].sum()
        prive_lalu = df[df['bulan'].isin(list_bulan[:idx])]['prive'].sum()
        
        m_awal_bln = modal_awal + laba_lalu - prive_lalu
        m_akhir_bln = m_awal_bln + l_bln - db_bulan['prive'].sum()

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f'<div class="white-card"><h3>LABA RUGI - {sel_b}</h3><hr>Omzet: {format_rp(o_bln)}<br>Laba Bersih: <b>{format_rp(l_bln)}</b></div>', unsafe_allow_html=True)
        with col_b:
            st.markdown(f'<div class="white-card"><h3>POSISI KAS - {sel_b}</h3><hr>Kas Awal: {format_rp(m_awal_bln)}<br>Kas Akhir: <b>{format_rp(m_akhir_bln)}</b></div>', unsafe_allow_html=True)

    with tab2:
        st.subheader("🏦 Konsultasi Strategis KUR")
        st.write(f"Histori Data: **{df['bulan'].nunique()} Bulan**")
        
        if df['bulan'].nunique() < 3:
            st.error("### 🚩 STATUS: BELUM LAYAK (DATA MINIMAL 3 BULAN)")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            # Logika Narasi KUR
            max_cicilan = l_bln * 0.35
            plafon = 50000000 if m_akhir_bln > 15000000 else 10000000
            
            st.markdown(f"""
            <div class="white-card">
                <b>Hasil Analisis Scoting:</b><br>
                Rekomendasi Plafon: <b>{format_rp(plafon)}</b><br>
                Batas Cicilan Aman: <b>{format_rp(max_cicilan)}/bln</b>
                <hr>
                <i>Saran: Gunakan pinjaman ini untuk menambah stok barang (Modal Kerja), bukan konsumsi pribadi.</i>
            </div>""", unsafe_allow_html=True)

    with tab3:
        st.subheader("🛠️ Revisi Data")
        target = st.selectbox("Pilih Data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df.sort_values('id', ascending=False).iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Silakan masukkan transaksi pertama untuk melihat laporan.")

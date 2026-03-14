import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku Pro: Konsultan Keuangan", layout="wide")

# --- DATABASE ENGINE (Versi Pro) ---
conn = sqlite3.connect('finsaku_v7_bankable.db', check_same_thread=False)
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

# 2. UI CUSTOM THEME
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
        color: #000000 !important;
    }
    .white-card * { color: #000000 !important; }
    .metric-box { text-align: center; border: 1px solid #ddd; padding: 10px; border-radius: 8px; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; border-radius: 8px; border:none; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    df['tgl_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')

# --- SIDEBAR (INPUT STRATEGIS) ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    
    m_awal_raw = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(m_awal_raw)
    st.markdown(f"<small style='color:#00ff00;'>Tercatat: {format_rp(modal_awal)}</small>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga")
    hpp_raw = st.text_input("HPP Produk", "5000")
    hpp_val = clean_to_int(hpp_raw)
    st.markdown(f"<small style='color:#00ff00;'>Tercatat: {format_rp(hpp_val)}</small>", unsafe_allow_html=True)

    hrg_raw = st.text_input("Harga Jual", "15000")
    hrg_val = clean_to_int(hrg_raw)
    st.markdown(f"<small style='color:#00ff00;'>Tercatat: {format_rp(hrg_val)}</small>", unsafe_allow_html=True)

    if hrg_val > 0:
        margin = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin: **{margin:.1f}%**")
        if margin < 40 and sektor == "Kuliner":
            st.warning("⚠️ Tips: Sektor kuliner rawan waste, margin aman >40%.")

    prive_pct = st.slider("Jatah Prive/Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard: {nama_u}")

with st.container():
    st.subheader("📝 Pencatatan Transaksi")
    col1, col2, col3 = st.columns([1.5, 1.5, 1])
    with col1:
        tgl_in = st.date_input("Tanggal", datetime.now())
    with col2:
        omzet_raw = st.text_input("Total Omzet Hari Ini", "0")
        omzet_in = clean_to_int(omzet_raw)
        st.markdown(f"<small style='color:#00ff00;'>Tercatat: {format_rp(omzet_in)}</small>", unsafe_allow_html=True)
    with col3:
        st.write(" ")
        if st.button("🚀 SIMPAN DATA"):
            laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
            p_in = laba_in * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?,?,?,?,?,?,?)",
                      (tgl_in.strftime("%Y-%m-%d"), tgl_in.strftime("%B %Y"), f"Minggu {tgl_in.isocalendar()[1]}", omzet_in, laba_in, p_in, "Harian"))
            conn.commit()
            st.success("Tersimpan!")
            st.rerun()

# --- LAPORAN & ANALISIS ---
if not df.empty:
    st.write("---")
    tab1, tab2, tab3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS BANKABLE (KUR)", "🛠️ REVISI"])

    with tab1:
        list_bulan = sorted(df['bulan'].unique().tolist())
        sel_b = st.selectbox("Pilih Periode:", list_bulan, index=len(list_bulan)-1)
        
        db_b = df[df['bulan'] == sel_b]
        o_bln = db_b['omzet'].sum()
        l_bln = db_b['laba'].sum()
        p_bln = db_b['prive'].sum()
        
        # Hitung Kas
        idx = list_bulan.index(sel_b)
        laba_akum = df[df['bulan'].isin(list_bulan[:idx])]['laba'].sum()
        prive_akum = df[df['bulan'].isin(list_bulan[:idx])]['prive'].sum()
        k_awal = modal_awal + laba_akum - prive_akum
        k_akhir = k_awal + l_bln - p_bln

        st.markdown(f"""
        <div class="white-card">
            <h3>Rekapitulasi {sel_b}</h3>
            <table style="width:100%; font-size:1.1em;">
                <tr><td>Total Omzet</td><td style="text-align:right;"><b>{format_rp(o_bln)}</b></td></tr>
                <tr><td>Laba Bersih (Estimasi)</td><td style="text-align:right; color:green;"><b>{format_rp(l_bln)}</b></td></tr>
                <tr><td>Prive (Diambil)</td><td style="text-align:right; color:red;">- {format_rp(p_bln)}</td></tr>
                <tr style="border-top:2px solid #000;"><td><b>SALDO KAS AKHIR</b></td><td style="text-align:right;"><b>{format_rp(k_akhir)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        st.subheader("🏦 Bankability Analysis (Scoring KUR)")
        
        avg_omzet = df.groupby('bulan')['omzet'].sum().mean()
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        konsistensi = df['bulan'].nunique()
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Rata-rata Omzet/Bulan", format_rp(avg_omzet))
        col_m2.metric("Rata-rata Laba/Bulan", format_rp(avg_laba))
        col_m3.metric("Lama Data Tercatat", f"{konsistensi} Bulan")

        st.write("---")
        
        # Logika KUR yang lebih dalam
        dscr = (avg_laba / (avg_laba * 0.3)) if avg_laba > 0 else 0
        plafon_max = avg_omzet * 2 # Logika umum bank (2x omzet bulanan)
        
        if konsistensi < 3:
            st.error("🚩 **BELUM LAYAK AJUKAN KUR** (Data minimal harus 3-6 bulan)")
        else:
            st.success("✅ **POTENSI LAYAK AJUKAN KUR**")
            st.markdown(f"""
            <div class="white-card">
                <h4>Hasil Simulasi Analis Kredit:</h4>
                <ul>
                    <li><b>Plafon Maksimal:</b> Up to {format_rp(plafon_max)}</li>
                    <li><b>Kemampuan Cicilan:</b> {format_rp(avg_laba * 0.35)} /bulan (Aman)</li>
                    <li><b>Skor Kolektibilitas:</b> BAIK (Data tercatat rapi)</li>
                </ul>
                <hr>
                <p><i>Tips Bank: Pastikan saldo kas akhir Anda tidak pernah menyentuh angka 0 setiap bulannya untuk menjaga kepercayaan bank.</i></p>
            </div>
            """, unsafe_allow_html=True)

    with tab3:
        target = st.selectbox("Pilih Data dihapus:", [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df.sort_values('id', ascending=False).iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0]),))
            conn.commit()
            st.rerun()
else:
    st.info("👋 Mulailah dengan memasukkan data transaksi harian Anda di atas.")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v10.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 25px; border-radius: 15px; border-left: 10px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
    }
    .white-card *, .white-card p, .white-card b, .white-card td, .white-card h3, .white-card h1 {
        color: #000000 !important; font-weight: 800 !important;
    }
    [data-testid="stSidebar"] { background-color: #001529 !important; border-right: 2px solid #FFD700; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: INPUT MODAL & PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "Levi Makmur Jaya")
    
    # FITUR REQUEST: REAL-TIME FORMATTING MODAL
    modal_input = st.text_input("Modal Kas Awal (Rp)", "0")
    modal_bersih = clean_to_int(modal_input)
    st.markdown(f"**Tercatat: {format_rp(modal_bersih)}**") 
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_raw = st.text_input("HPP (Modal) /Produk", "5000")
    hrg_raw = st.text_input("Harga Jual /Produk", "15000")
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)
    st.caption("Prive merupakan Pendapatan untuk keburutuhan pribadi dan BRI menyarankan Prive < 50% dari laba.")

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

# INPUT TRANSAKSI
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input {rekap_mode}")
    tgl = st.date_input("Tanggal", datetime.now())
    
    if rekap_mode == "Harian":
        input_type = st.radio("Metode:", ["Per Produk", "Total Omzet"], horizontal=True)
        if input_type == "Per Produk":
            qty = st.number_input("Unit Terjual", min_value=0, step=1)
            omzet = qty * clean_to_int(hrg_raw)
            laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
        else:
            omzet = st.number_input("Total Omzet Hari Ini", min_value=0, step=1000)
            ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
            laba = omzet * ratio
    else:
        omzet = st.number_input(f"Total Omzet 1 {rekap_mode}", min_value=0, step=10000)
        ratio = (clean_to_int(hrg_raw) - clean_to_int(hpp_raw)) / clean_to_int(hrg_raw) if clean_to_int(hrg_raw) > 0 else 0
        laba = omzet * ratio

    prive = laba * (prive_pct / 100)

    if st.button("🔔 SIMPAN KE LAPORAN"):
        if omzet > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
            conn.commit()
            st.success("Tersimpan!")
            st.rerun()

with col_guidance:
    st.markdown(f"""
    <div class="white-card">
        <h3>💡 Tips Bankability</h3>
        <p><b>Prive Terkontrol:</b> Anda mengalokasikan {prive_pct}% laba untuk pribadi. BRI lebih suka jika angka ini di bawah 50% agar kas usaha tetap sehat.</p>
        <p><b>Kontinuitas:</b> Pastikan mencatat setiap periode agar grafik keuangan terlihat stabil di mata Mantri BRI.</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN & ANALISIS KUR ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN PERIODIK", "🏦 KELAYAKAN KUR BRI (MENDALAM)"])

    with t_rep:
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        data_b = df[df['bulan'] == sel_b]
        o, l, p = data_b['omzet'].sum(), data_b['laba'].sum(), data_b['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Bulanan: {sel_b}</h3>
            <table style="width:100%; font-size:1.1em;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Laba Bersih</td><td style="text-align:right;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi)</td><td style="text-align:right; color:red;">({format_rp(p)})</td></tr>
                <tr style="background:#fff9c4;"><td><b>SISA KAS USAHA</b></td><td style="text-align:right;"><b>{format_rp(l-p)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        st.subheader("🏦 Analisis Kemampuan Pinjaman & Risiko")
        
        # Hitung Rata-rata Laba
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        avg_prive = df.groupby('bulan')['prive'].sum().mean()
        laba_bebas = avg_laba - avg_prive # Laba yang benar-benar nganggur
        
        # Standar Perbankan: RPC (Repayment Capacity)
        rpc_aman = avg_laba * 0.35 
        
        # Simulasi Pinjaman (Asumsi Bunga KUR 6% / Tahun atau 0.5% / Bulan)
        # Rumus plafon kasar: RPC * 24 bulan
        plafon_max = rpc_aman * 24
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Batas Cicilan Aman", format_rp(rpc_aman))
        col2.metric("Saran Plafon KUR", format_rp(plafon_max))
        col3.metric("Laba Nganggur/Bulan", format_rp(laba_bebas))

        st.markdown("### ⚠️ Analisis Risiko Bunga & Bayar")
        
        # Hitung Bunga per Bulan jika ambil plafon max
        est_bunga_bulan = plafon_max * (0.06 / 12)
        porsi_bunga = (est_bunga_bulan / avg_laba) * 100 if avg_laba > 0 else 0
        
        st.markdown(f"""
        <div class="white-card">
            <h4>Analisis mendalam untuk Anda:</h4>
            <ul>
                <li><b>Risiko Bunga:</b> Jika Anda meminjam {format_rp(plafon_max)}, bunga bulanannya sekitar <b>{format_rp(est_bunga_bulan)}</b>. Ini hanya memakan <b>{porsi_bunga:.1f}%</b> dari total laba Anda. Sangat Aman!</li>
                <li><b>Sumber Bayar:</b> Cicilan bisa dibayar penuh dari Laba Bersih tanpa mengganggu uang jajan (Prive) Anda.</li>
                <li><b>Kelayakan:</b> {"✅ LAYAK. Performa Anda sudah memenuhi syarat 'Kapasitas' BRI." if plafon_max >= 5000000 else "⚠️ BELUM LAYAK KUR MINIMAL."}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        if plafon_max < 5000000:
            target_laba = (5000000 / 24) / 0.35
            st.warning(f"""
            **Strategi Agar Layak:**
            Saat ini kapasitas bayar Anda masih rendah. Agar bisa pinjam minimal Rp 5.000.000 di BRI, 
            Anda harus meningkatkan laba bersih bulanan menjadi minimal **{format_rp(target_laba)}**. 
            (Kurang {format_rp(target_laba - avg_laba)} lagi!)
            """)

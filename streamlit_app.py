import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_final.db', check_same_thread=False)
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
        if angka < 0: return f"Rp -{formatted}"
        return f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM (NAVY & GOLD)
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

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
jumlah_bulan_data = df['bulan'].nunique() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)
    if prive_pct > 30:
        st.warning("⚠️ **Saran Bank:** Prive > 30% dianggap kurang sehat untuk pertumbuhan modal.")
    else:
        st.success("✅ **Saran Bank:** Jatah prive sehat.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_info = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    # Gunakan Aturan Harga Default atau Input Langsung
    hpp_produk = 5000 
    harga_jual = 15000
    
    omzet_in = st.number_input("Total Omzet", value=0, step=10000)
    
    # Analisis Instan
    biaya_hpp = omzet_in * (hpp_produk / harga_jual) if harga_jual > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if omzet_in > 0:
        st.info(f"Estimasi Laba: {format_rp(laba_in)} | Prive: {format_rp(prive_in)}")

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown('<div class="white-card"><h3>💡 Konsultasi Cepat</h3><p>Bank menyukai UMKM yang tertib administrasi. Catatan selama <b>3-6 bulan</b> adalah syarat mutlak KUR.</p></div>', unsafe_allow_html=True)

# --- BAGIAN LAPORAN & KUR ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        df['tgl_dt'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values('tgl_dt')
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        
        db_bulan = df[df['bulan'] == sel_b]
        omzet_bln = db_bulan['omzet'].sum()
        laba_bln = db_bulan['laba'].sum()
        prive_bln = db_bulan['prive'].sum()
        
        idx_bulan = list_bulan.index(sel_b)
        bulan_sebelumnya = list_bulan[:idx_bulan]
        total_laba_lalu = df[df['bulan'].isin(bulan_sebelumnya)]['laba'].sum()
        total_prive_lalu = df[df['bulan'].isin(bulan_sebelumnya)]['prive'].sum()
        
        modal_awal_bln = modal_awal + total_laba_lalu - total_prive_lalu
        modal_akhir_bln = modal_awal_bln + laba_bln - prive_bln

        c_lr, c_pm = st.columns(2)
        with c_lr:
            st.markdown(f"""<div class="white-card"><h3 style="text-align:center;">LABA RUGI - {sel_b}</h3><hr>
                <table style="width:100%;">
                    <tr><td>Pendapatan</td><td style="text-align:right;">{format_rp(omzet_bln)}</td></tr>
                    <tr style="color:red;"><td>Beban HPP</td><td style="text-align:right;">({format_rp(omzet_bln-laba_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; color:{'green' if laba_bln >= 0 else 'red'};">
                        <td>LABA/RUGI</td><td style="text-align:right;">{format_rp(laba_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)
        with c_pm:
            st.markdown(f"""<div class="white-card"><h3 style="text-align:center;">MODAL - {sel_b}</h3><hr>
                <table style="width:100%;">
                    <tr><td>Modal Awal (Saldo Lalu)</td><td style="text-align:right;">{format_rp(modal_awal_bln)}</td></tr>
                    <tr><td>Laba Bulan Ini</td><td style="text-align:right; color:green;">{format_rp(laba_bln)}</td></tr>
                    <tr style="color:red;"><td>Prive</td><td style="text-align:right;">({format_rp(prive_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; background:#FFD700;">
                        <td>MODAL AKHIR (KAS)</td><td style="text-align:right;">{format_rp(modal_akhir_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)

    with tab_kur:
        st.subheader("🏦 Konsultasi Strategis KUR")
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        if jumlah_bulan_data < 3:
            st.error(f"### 🚩 BELUM LAYAK (Butuh {3 - jumlah_bulan_data} bulan lagi)")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid red;">
                <h4>Analisis:</h4>
                <p>Bank BRI mewajibkan usaha minimal berjalan 6 bulan. FIN-Saku menyarankan minimal <b>3 bulan laporan rapi</b> sebelum pengajuan.</p>
                </div>""", unsafe_allow_html=True)
        elif laba_bln < 1000000:
            st.warning("### 🚩 LABA TERLALU KECIL")
            st.markdown('<div class="white-card">Tingkatkan omzet agar laba di atas 1 Juta sebelum meminjam.</div>', unsafe_allow_html=True)
        else:
            st.success("### ✅ LAYAK EKSPANSI")
            plafon = 10000000 if modal_akhir_bln < 15000000 else 50000000
            st.markdown(f'<div class="white-card">Rekomendasi Plafon: <b>{format_rp(plafon)}</b></div>', unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi")
        df_rev = df.sort_values(by='id', ascending=False)
        if not df_rev.empty:
            pilihan = [f"ID:{row['id']} | {row['tanggal']} | {format_rp(row['omzet'])}" for _, row in df_rev.iterrows()]
            target = st.selectbox("Pilih data:", pilihan)
            id_del = int(target.split("|")[0].replace("ID:", ""))
            if st.button("🗑️ HAPUS PERMANEN"):
                c.execute("DELETE FROM transaksi WHERE id = ?", (id_del,))
                conn.commit()
                st.rerun()
else:
    st.info("Silakan masukkan data transaksi pertama Anda.")

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali Modal UMKM", layout="wide")

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

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td, .white-card li { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    # Hitung total akumulasi untuk sidebar stat
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Total Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_info = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet_in = st.number_input(f"Total Omzet", value=0)
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if laba_in < 0: st.error(f"Rugi: {format_rp(laba_in)}")
    else: st.info(f"Laba: {format_rp(laba_in)}")

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown('<div class="white-card"><h3>💡 Info Akuntansi</h3><p>Laba Rugi mencatat kinerja <b>bulan ini saja</b>. Perubahan Modal mencatat <b>akumulasi</b> dari bulan ke bulan.</p></div>', unsafe_allow_html=True)

# --- REVISI BAGIAN LAPORAN & KUR (AKUNTANSI BERTAHAP) ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        # 1. LOGIKA URUTAN BULAN
        df['tgl_dt'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values('tgl_dt')
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        
        # 2. LOGIKA LABA RUGI (Hanya bulan terpilih)
        db_bulan = df[df['bulan'] == sel_b]
        omzet_bln = db_bulan['omzet'].sum()
        laba_bln = db_bulan['laba'].sum()
        prive_bln = db_bulan['prive'].sum()
        
        # 3. LOGIKA PERUBAHAN MODAL (Akumulasi Saldo)
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
                    <tr><td>Laba/Rugi Bulan Ini</td><td style="text-align:right; color:{'green' if laba_bln >= 0 else 'red'};">{format_rp(laba_bln)}</td></tr>
                    <tr style="color:red;"><td>Prive</td><td style="text-align:right;">({format_rp(prive_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; background:#FFD700;">
                        <td>MODAL AKHIR</td><td style="text-align:right;">{format_rp(modal_akhir_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)

        with tab_kur:
        st.subheader(f"🏦 Analisis Kelayakan KUR BRI ({sel_b})")
        
        # --- LOGIKA PENENTUAN PRODUK KUR BRI ---
        # Kita pakai Modal Akhir sebagai 'jaminan' kapasitas usaha
        # BRI biasanya melihat cicilan tidak boleh lebih dari 30-40% laba bulanan
        kapasitas_cicilan = laba_bln * 0.4 
        
        # Penentuan Level Produk berdasarkan Modal Akhir & Laba
        # 1. KUR Super Mikro (Plafon s.d 10 Juta)
        # 2. KUR Mikro (Plafon 10 - 50 Juta)
        # 3. KUR Kecil (Plafon 50 - 500 Juta)
        
        if modal_akhir_bln < 5000000 or laba_bln <= 0:
            # EFEK INTERAKTIF DITOLAK
            st.error("### ❌ STATUS: BELUM LAYAK PENGAJUAN")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""<div class="white-card" style="border-left: 8px solid #ff4b4b;">
                    <h4>Kenapa Belum Layak?</h4>
                    <ul>
                        <li><b>Modal Akhir:</b> {format_rp(modal_akhir_bln)} (Min. 5 Juta)</li>
                        <li><b>Kesehatan Laba:</b> {'Rugi/Nol' if laba_bln <= 0 else 'Oke'}</li>
                    </ul>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""<div class="white-card">
                    <h4>Apa yang harus dilakukan?</h4>
                    <p>1. <b>Tahan Prive:</b> Kurangi ambil uang jajan agar Kas bertumbuh.</p>
                    <p>2. <b>Fokus Omzet:</b> Tingkatkan penjualan hingga laba stabil di atas 2 juta/bulan.</p>
                </div>""", unsafe_allow_html=True)
        
        else:
            # EFEK INTERAKTIF LAYAK
            # Tentukan Plafon
            if modal_akhir_bln >= 5000000 and modal_akhir_bln < 15000000:
                produk = "KUR Super Mikro"
                plafon = 10000000
                warna_lv = "#00c8ff"
            elif modal_akhir_bln >= 15000000 and modal_akhir_bln < 50000000:
                produk = "KUR Mikro"
                plafon = 50000000
                warna_lv = "#00ff88"
            else:
                produk = "KUR Kecil"
                plafon = 100000000
                warna_lv = "#FFD700"

            st.success(f"### ✅ STATUS: LAYAK (Level: {produk})")
            
            # Perhitungan Cicilan (Bunga KUR 6% per tahun)
            tenor_opsi = st.select_slider("Pilih Jangka Waktu (Tenor):", options=[12, 18, 24, 36], value=12)
            
            bunga_per_tahun = 0.06
            pokok_per_bln = plafon / tenor_opsi
            bunga_per_bln = (plafon * bunga_per_tahun) / 12
            total_setoran = pokok_per_bln + bunga_per_bln

            # TAMPILAN INTERAKTIF HASIL
            st.markdown(f"""
            <div class="white-card" style="border-left: 8px solid {warna_lv};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <p style="margin:0;">Produk Pinjaman Disarankan:</p>
                        <h2 style="color:#001f3f; margin:0;">{produk} BRI</h2>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin:0;">Maksimal Plafon:</p>
                        <h2 style="color:#28a745; margin:0;">{format_rp(plafon)}</h2>
                    </div>
                </div>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <p>Modal Terakhir Anda: <b>{format_rp(modal_akhir_bln)}</b></p>
                    <p>Cicilan per Bulan: <b style="font-size: 20px; color:#ff4b4b;">{format_rp(total_setoran)}</b></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # BAGIAN EDUKASI PINJAMAN
            exp = st.expander("🔍 Mengapa ambil KUR ini bagus & Digunakan untuk apa?")
            exp.markdown(f"""
            <div style="color: black;">
            <b>1. Mengapa Bagus?</b><br>
            Bunga KUR hanya 6% efektif per tahun (subsidi pemerintah). Ini adalah bunga termurah untuk UMKM. 
            Dengan Modal Akhir {format_rp(modal_akhir_bln)}, Anda dianggap memiliki "bantalan" aman jika terjadi penurunan penjualan.<br><br>
            
            <b>2. Digunakan untuk apa?</b><br>
            <ul>
                <li><b>Modal Kerja:</b> Beli bahan baku dalam partai besar agar dapat diskon supplier (HPP turun).</li>
                <li><b>Investasi:</b> Beli mesin atau alat yang bisa mempercepat produksi 2x lipat.</li>
            </ul>
            
            <b>3. Mengapa Aman?</b><br>
            Karena cicilan {format_rp(total_setoran)} hanya memakan sebagian kecil dari laba Anda. Anda masih punya sisa uang untuk operasional dan tabungan darurat.
            </div>
            """, unsafe_allow_html=True)

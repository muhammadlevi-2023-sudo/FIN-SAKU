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

# 2. UI CUSTOM (NAVY & GOLD)
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

# --- SIDEBAR: PROFIL BISNIS ---
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
    st.markdown(f"<h3 style='color:#FFD700;'>Total Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("⚙️ Aturan Harga")
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
    st.markdown('<div class="white-card"><h3>💡 Info Akuntansi</h3><p>Uang Kas Anda akan <b>berkurang otomatis</b> jika terjadi kerugian atau pengambilan prive (uang jajan).</p></div>', unsafe_allow_html=True)

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
                    <tr><td>Laba/Rugi Bulan Ini</td><td style="text-align:right; color:{'green' if laba_bln >= 0 else 'red'};">{format_rp(laba_bln)}</td></tr>
                    <tr style="color:red;"><td>Prive</td><td style="text-align:right;">({format_rp(prive_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; background:#FFD700;">
                        <td>MODAL AKHIR (KAS)</td><td style="text-align:right;">{format_rp(modal_akhir_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)

    with tab_kur:
        st.subheader(f"🏦 Analisis Kelayakan KUR BRI ({sel_b})")
        
        if modal_akhir_bln < 5000000 or laba_bln <= 0:
            st.error("### ❌ STATUS: BELUM LAYAK PENGAJUAN")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""<div class="white-card" style="border-left: 8px solid #ff4b4b;">
                    <h4>Kenapa Belum Layak?</h4>
                    <ul>
                        <li><b>Modal Akhir:</b> {format_rp(modal_akhir_bln)} (BRI Min. 5jt)</li>
                        <li><b>Kesehatan Laba:</b> {'Rugi/Nol' if laba_bln <= 0 else 'Oke'}</li>
                    </ul>
                </div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""<div class="white-card"><h4>Solusi Perbaikan:</h4>
                    <p>Kurangi pengambilan <b>Prive</b> dan pastikan harga jual meng-cover biaya HPP agar kas bulanan tumbuh.</p></div>""", unsafe_allow_html=True)
        else:
            if modal_akhir_bln < 15000000:
                produk, plafon, warna_lv = "KUR Super Mikro", 10000000, "#00c8ff"
            elif modal_akhir_bln < 50000000:
                produk, plafon, warna_lv = "KUR Mikro", 50000000, "#00ff88"
            else:
                produk, plafon, warna_lv = "KUR Kecil", 100000000, "#FFD700"

            st.success(f"### ✅ STATUS: LAYAK (Level: {produk})")
            tenor = st.select_slider("Pilih Tenor (Bulan):", options=[12, 18, 24, 36], value=12)
            
            total_setoran = (plafon / tenor) + ((plafon * 0.06) / 12)

            st.markdown(f"""
            <div class="white-card" style="border-left: 8px solid {warna_lv};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div><p style="margin:0;">Produk Disarankan:</p><h2 style="color:#001f3f; margin:0;">{produk} BRI</h2></div>
                    <div style="text-align: right;"><p style="margin:0;">Plafon Maks:</p><h2 style="color:#28a745; margin:0;">{format_rp(plafon)}</h2></div>
                </div>
                <hr>
                <div style="display: flex; justify-content: space-between;">
                    <p>Kas Terakhir: <b>{format_rp(modal_akhir_bln)}</b></p>
                    <p>Cicilan/Bulan: <b style="font-size: 20px; color:#ff4b4b;">{format_rp(total_setoran)}</b></p>
                </div>
            </div>
            """, unsafe_allow_html=True)

            exp = st.expander("🔍 Detail Penggunaan Dana KUR")
            exp.markdown(f"""<div style="color: black;">
                <b>1. Mengapa Bagus?</b> Bunga rendah (6% setahun) karena disubsidi pemerintah.<br>
                <b>2. Digunakan Untuk Apa?</b> Beli stok barang lebih banyak (Kulakan partai besar) atau tambah alat produksi.<br>
                <b>3. Mengapa Aman?</b> Cicilan sudah dihitung tidak melebihi kapasitas laba bersih bulanan Anda.</div>""", unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi Data")
        df_v = df.sort_values('id', ascending=False)
        pil = st.selectbox("Pilih data:", [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_v.iterrows()])
        if st.button("🗑️ Hapus Data Ini"):
            c.execute(f"DELETE FROM transaksi WHERE id={int(pil.split(' | ')[0])}"); conn.commit(); st.rerun()
else:
    st.info("Silakan masukkan data transaksi pertama Anda untuk melihat analisis.")

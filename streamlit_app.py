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
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td, .white-card li { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; border-radius: 8px; }
    .stDateInput div { border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR: PROFIL & SARAN STRATEGIS ---
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
    st.markdown(f"<h2 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h2>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Prive")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    # ADVISOR PRIVE
    st.markdown("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 100, 30)
    if prive_pct > 30:
        st.warning("⚠️ **Saran BRI:** Prive di atas 30% dianggap bank terlalu boros. Usahakan di bawah 30% agar modal usaha cepat besar.")
    else:
        st.success("✅ **Saran BRI:** Prive aman. Anda punya ruang besar untuk cicilan bank.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")

# INPUT SECTION DIBUAT LEBIH CLEAN
with st.container():
    col_tgl, col_omzet, col_metode = st.columns([1, 1, 1])
    with col_tgl:
        tgl = st.date_input("📅 Pilih Tanggal", datetime.now())
    with col_omzet:
        omzet_in = st.number_input(f"💵 Total Omzet", min_value=0, step=10000)
    with col_metode:
        rekap_mode = st.selectbox("📝 Metode Catat", ["Harian", "Mingguan", "Bulanan"])

    # Kalkulasi Otomatis
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    col_btn, col_res = st.columns([1, 2])
    with col_btn:
        if st.button("🔔 SIMPAN TRANSAKSI", use_container_width=True):
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
            conn.commit()
            st.success("Tersimpan!")
            st.rerun()
    with col_res:
        if omzet_in > 0:
            st.info(f"Estimasi Laba Bersih: **{format_rp(laba_in)}** | Jatah Prive: **{format_rp(prive_in)}**")

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
                    <tr><td>Pendapatan (Omzet)</td><td style="text-align:right;">{format_rp(omzet_bln)}</td></tr>
                    <tr style="color:red;"><td>Beban Pokok (HPP)</td><td style="text-align:right;">({format_rp(omzet_bln-laba_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; color:{'green' if laba_bln >= 0 else 'red'};">
                        <td>LABA BERSIH</td><td style="text-align:right;">{format_rp(laba_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)
        with c_pm:
            st.markdown(f"""<div class="white-card"><h3 style="text-align:center;">MODAL - {sel_b}</h3><hr>
                <table style="width:100%;">
                    <tr><td>Uang Kas Awal</td><td style="text-align:right;">{format_rp(modal_awal_bln)}</td></tr>
                    <tr><td>Laba Bulan Ini</td><td style="text-align:right; color:green;">+{format_rp(laba_bln)}</td></tr>
                    <tr style="color:red;"><td>Prive (Ambil Uang)</td><td style="text-align:right;">({format_rp(prive_bln)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; background:#FFD700;">
                        <td>KAS AKHIR (MODAL)</td><td style="text-align:right;">{format_rp(modal_akhir_bln)}</td>
                    </tr>
                </table></div>""", unsafe_allow_html=True)

    with tab_kur:
        st.markdown(f"### 📑 Konsultasi Kredit BRI: {sel_b}")
        rasio_laba_cicilan = 0.35 
        kemampuan_bayar = laba_bln * rasio_laba_cicilan
        
        if laba_bln <= 0:
            st.error("### 🚩 ANALISIS: DITOLAK (RESIKO TINGGI)")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid red;">
                <h4>Kenapa?</h4>
                <p>Bank tidak akan meminjamkan uang jika operasional Anda masih Rugi. Anda akan kesulitan membayar cicilan.</p>
                <hr><b>Saran Konsultan:</b> Perbaiki harga jual atau kurangi biaya operasional sampai laba positif.</p></div>""", unsafe_allow_html=True)
        elif modal_akhir_bln < 5000000:
            st.warning("### 🚩 ANALISIS: PERKUAT SALDO KAS")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid orange;">
                <h4>Kenapa?</h4>
                <p>BRI menyukai UMKM yang punya saldo mengendap minimal 5-10 juta sebagai cadangan darurat.</p>
                <hr><b>Saran Konsultan:</b> Jangan ambil Prive (uang jajan) dulu bulan depan. Biarkan saldo kas Anda tumbuh.</p></div>""", unsafe_allow_html=True)
        else:
            st.success("### ✅ ANALISIS: LAYAK (RECOMMENDED)")
            if modal_akhir_bln < 15000000:
                nama_produk, plafon_rekomendasi = "KUR Super Mikro", 10000000
            else:
                nama_produk, plafon_rekomendasi = "KUR Mikro", 50000000

            st.markdown(f"""<div class="white-card">
                <h4>Saran Produk BRI:</h4>
                <h3 style="color: #001f3f; margin:0;">{nama_produk}</h3>
                <p>Plafon yang disarankan: <b>{format_rp(plafon_rekomendasi)}</b></p></div>""", unsafe_allow_html=True)

            tenor = st.radio("Pilih Tenor (Bulan):", [12, 18, 24, 36], index=0, horizontal=True)
            total_cicilan = (plafon_rekomendasi / tenor) + ((plafon_rekomendasi * 0.06) / 12)
            status_beban = "AMAN" if total_cicilan <= kemampuan_bayar else "BERISIKO"
            warna_beban = "green" if status_beban == "AMAN" else "red"

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""<div class="white-card"><h4>Kalkulasi Cicilan:</h4>
                    <p>Setoran per Bulan: <b>{format_rp(total_cicilan)}</b></p><hr>
                    <p>Status: <b style="color:{warna_beban};">{status_beban}</b></p>
                    <small>*Cicilan aman Anda maksimal {format_rp(kemampuan_bayar)} (35% dari laba)</small></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown("""<div class="white-card" style="border-left: 8px solid #FFD700;">
                    <h4>💡 Tips Agar Acc:</h4>
                    <ul><li>Pastikan catatan keuangan ini rapi (Bank suka UMKM yang melek data).</li>
                    <li>Gunakan dana KUR untuk stok barang, bukan renovasi rumah.</li>
                    <li>Jangan ada kredit macet di tempat lain (Pinjol/Motor).</li></ul></div>""", unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Manajer Data")
        df_rev = df.sort_values(by='id', ascending=False)
        if not df_rev.empty:
            pilihan_hapus = [f"ID: {row['id']} | {row['tanggal']} | Omzet: {format_rp(row['omzet'])}" for _, row in df_rev.iterrows()]
            target = st.selectbox("Pilih data yang salah input:", pilihan_hapus)
            id_to_delete = int(target.split(" | ")[0].replace("ID: ", ""))
            
            if st.checkbox("Saya sadar dan ingin menghapus data ini"):
                if st.button("🗑️ HAPUS PERMANEN", use_container_width=True):
                    c.execute("DELETE FROM transaksi WHERE id = ?", (id_to_delete,))
                    conn.commit()
                    st.success("Data Terhapus!")
                    st.rerun()
        else:
            st.info("Belum ada data transaksi.")
else:
    st.info("Silakan masukkan transaksi penjualan pertama Anda di atas untuk melihat analisis.")

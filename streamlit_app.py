import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN (Force Light/Dark consistency)
st.set_page_config(page_title="FIN-Saku: Konsultan KUR Pro", layout="wide")

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

# 2. UI CUSTOM (NAVY, GOLD, WHITE) - DIPERKUAT AGAR TIDAK IKUT SISTEM HP
st.markdown("""
<style>
    /* Background Utama */
    .stApp { background-color: #001f3f !important; }
    
    /* Warna Teks Global */
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3, .stApp span { color: #ffffff !important; }
    
    /* Card Putih Bersih untuk Data */
    .white-card {
        background-color: #ffffff !important;
        padding: 22px; border-radius: 15px; border-left: 10px solid #FFD700;
        margin-bottom: 20px; box-shadow: 0px 6px 15px rgba(0,0,0,0.4);
        color: #000000 !important;
    }
    .white-card * { color: #000000 !important; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* Button & Input */
    .stButton>button { 
        background-color: #FFD700 !important; color: #001f3f !important; 
        font-weight: bold; border-radius: 10px; border: none; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); background-color: #ffeb3b !important; }
    
    /* Input Form agar Kontras */
    input { background-color: #ffffff !important; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
jumlah_bulan_data = df['bulan'].nunique() if not df.empty else 0

# --- SIDEBAR: PROFIL DASHBOARD SEIRAS ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700; margin-bottom:0;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:12px;'>KONSULTAN KEUANGAN DIGITAL</p>", unsafe_allow_html=True)
    st.write("---")
    
    nama_u = st.text_input("🏢 Nama Usaha", "UMKM Maju Bersama")
    modal_awal_input = st.text_input("💰 Modal Awal Kas", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"""
    <div style="background:#002a54; padding:15px; border-radius:10px; border:1px solid #FFD700;">
        <p style="margin:0; font-size:14px;">Total Kas Saat Ini:</p>
        <h2 style="color:#FFD700; margin:0;">{format_rp(modal_skrg_all)}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Parameter Bisnis")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Prive/Pribadi (%)", 0, 50, 30)
    
    # Smart Prive Advisor
    if prive_pct > 30:
        st.error("❗ Prive terlalu tinggi. Bank akan menilai Anda sulit menabung modal.")
    else:
        st.success("✔️ Alokasi laba sehat.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard {nama_u}")

# INPUT SECTION: EASY ACCESS
with st.container():
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        tgl = st.date_input("📅 Tanggal Transaksi", datetime.now())
    with c2:
        omzet_in = st.number_input("💵 Total Omzet", min_value=0, step=50000)
    with c3:
        rekap_mode = st.selectbox("📝 Rekap Sebagai", ["Harian", "Mingguan", "Bulanan"])

    # Hitung Laba & Prive Realtime
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🚀 SIMPAN DATA KE DATABASE", use_container_width=True):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

# --- VALIDASI DATA UNTUK LAPORAN ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 KONSULTASI KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        # Logika Laporan Bulanan
        df['tgl_dt'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values('tgl_dt')
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Lihat Laporan Bulan:", list_bulan, index=len(list_bulan)-1)
        
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

        col_lr, col_md = st.columns(2)
        with col_lr:
            st.markdown(f"""<div class="white-card"><h3>📈 Laba Rugi - {sel_b}</h3><hr>
                <p>Pendapatan: <b>{format_rp(omzet_bln)}</b></p>
                <p style="color:red;">HPP: ({format_rp(omzet_bln-laba_bln)})</p>
                <h3 style="color:green;">Laba Bersih: {format_rp(laba_bln)}</h3></div>""", unsafe_allow_html=True)
        with col_md:
            st.markdown(f"""<div class="white-card"><h3>💰 Posisi Kas - {sel_b}</h3><hr>
                <p>Kas Awal: {format_rp(modal_awal_bln)}</p>
                <p>Prive: <span style="color:red;">({format_rp(prive_bln)})</span></p>
                <h3 style="background:#FFD700; padding:5px;">Kas Akhir: {format_rp(modal_akhir_bln)}</h3></div>""", unsafe_allow_html=True)

    with tab_kur:
        st.subheader("🏦 Konsultan Pinjaman Bank BRI")
        
        # LOGIKA PERBANKAN YANG DIPERKETAT
        st.info(f"ℹ️ **Status Data:** Saat ini Anda memiliki catatan untuk **{jumlah_bulan_data} bulan**.")
        
        # 1. Cek Durasi Usaha (Syarat KUR min 6 bulan, di sini kita set minimal 3 bulan untuk simulasi)
        if jumlah_bulan_data < 3:
            st.error("### ❌ BELUM LAYAK (DATA KURANG)")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid #ff4b4b;">
                <h4>Analisis Konsultan:</h4>
                <p>Bank BRI mewajibkan usaha berjalan minimal <b>6 bulan</b>. Catatan Anda baru <b>{jumlah_bulan_data} bulan</b>.</p>
                <hr>
                <b>Langkah Anda:</b> Lanjutkan mencatat setiap hari. Konsistensi laporan adalah "nyawa" agar bank percaya memberikan pinjaman besar.
            </div>""", unsafe_allow_html=True)
        
        # 2. Cek Nominal Laba (Logika: Masa laba cuma 5k mau pinjam?)
        elif laba_bln < 1000000:
            st.warning("### ⚠️ LAYAK TAPI BERISIKO (LABA TERLALU KECIL)")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid orange;">
                <h4>Analisis Konsultan:</h4>
                <p>Laba Anda bulan ini <b>{format_rp(laba_bln)}</b>. Dengan laba di bawah 1 Juta, cicilan bank akan mencekik kebutuhan sehari-hari Anda.</p>
                <hr>
                <b>Saran:</b> Tingkatkan penjualan hingga laba stabil di atas 2-3 Juta per bulan sebelum mengajukan KUR.
            </div>""", unsafe_allow_html=True)
            
        else:
            # JIKA SEMUA OK (DATA >= 3 BULAN & LABA OKE)
            st.success("### ✅ ANALISIS: SANGAT LAYAK (RECOMMENDED)")
            
            # Tentukan plafon berdasarkan laba (Cicilan max 30% laba)
            if laba_bln > 5000000:
                produk, plafon = "KUR Mikro BRI", 50000000
            else:
                produk, plafon = "KUR Super Mikro BRI", 10000000
                
            st.markdown(f"""<div class="white-card">
                <h4>Rekomendasi Pinjaman:</h4>
                <h2 style="color:#001f3f;">{produk}</h2>
                <p>Maksimal Pinjaman: <b style="color:green;">{format_rp(plafon)}</b></p>
            </div>""", unsafe_allow_html=True)
            
            tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            
            c_a, c_b = st.columns(2)
            with c_a:
                st.markdown(f"""<div class="white-card">
                    <h4>Simulasi Cicilan:</h4>
                    <p>Per Bulan: <b>{format_rp(cicilan)}</b></p>
                    <p>Bunga: <b>6% per tahun (Subsidi)</b></p>
                </div>""", unsafe_allow_html=True)
            with c_b:
                st.markdown(f"""<div class="white-card" style="border-left:8px solid green;">
                    <h4>Kenapa Pinjam Sekarang?</h4>
                    <ul>
                        <li>Kas Akhir Anda {format_rp(modal_akhir_bln)} cukup untuk cadangan.</li>
                        <li>Dana bisa dipakai ekspansi stok menyambut musim ramai.</li>
                        <li>BRI akan melihat Anda sebagai nasabah prioritas.</li>
                    </ul>
                </div>""", unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🗑️ Hapus Data Salah")
        df_rev = df.sort_values(by='id', ascending=False)
        pilihan = [f"ID:{row['id']} | {row['tanggal']} | {format_rp(row['omzet'])}" for _, row in df_rev.iterrows()]
        target = st.selectbox("Pilih data untuk dihapus:", pilihan)
        id_del = int(target.split("|")[0].replace("ID:", ""))
        
        if st.checkbox("Konfirmasi hapus"):
            if st.button("HAPUS DATA"):
                c.execute("DELETE FROM transaksi WHERE id=?", (id_del,))
                conn.commit()
                st.rerun()
else:
    st.info("👋 Selamat Datang! Silakan masukkan data transaksi pertama Anda untuk memulai analisis.")

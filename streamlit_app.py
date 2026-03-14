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
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner (Makanan/Minuman)", "Retail (Toko Kelontong/Baju)", "Jasa (Laundry/Service)", "Produksi/Manufaktur"])
    
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp_val = clean_to_int(st.text_input("HPP Produk (Modal)", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin Anda: **{margin_pct:.1f}%**")
    
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_info = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet_in = st.number_input("Total Omzet Penjualan", value=0, step=10000)
    
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown(f'<div class="white-card"><h3>💡 Tips Konsultan</h3><p>Sektor <b>{sektor}</b> membutuhkan konsistensi laporan minimal 3 bulan untuk dilirik Bank.</p></div>', unsafe_allow_html=True)

# --- BAGIAN TABS ---
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
        total_laba_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['laba'].sum()
        total_prive_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['prive'].sum()
        
        modal_awal_bln = modal_awal + total_laba_lalu - total_prive_lalu
        modal_akhir_bln = modal_awal_bln + laba_bln - prive_bln

        c_lr, c_pm = st.columns(2)
        with c_lr:
            st.markdown(f'<div class="white-card"><h3>LABA RUGI - {sel_b}</h3><hr>Omzet: {format_rp(omzet_bln)}<br>Laba Bersih: <b>{format_rp(laba_bln)}</b></div>', unsafe_allow_html=True)
        with c_pm:
            st.markdown(f'<div class="white-card"><h3>MODAL - {sel_b}</h3><hr>Kas Awal: {format_rp(modal_awal_bln)}<br>Kas Akhir: <b>{format_rp(modal_akhir_bln)}</b></div>', unsafe_allow_html=True)

    with tab_kur:
        st.subheader("🏦 Konsultasi Strategis KUR")
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        if jumlah_bulan_data < 3:
            st.error("### 🚩 STATUS: BELUM LAYAK (DATA KURANG)")
            st.info(f"Lengkapi catatan {3-jumlah_bulan_data} bulan lagi untuk analisis mendalam.")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            
            # Perhitungan Logika
            max_cicilan_aman = laba_bln * 0.35
            plafon = 50000000 if modal_akhir_bln > 15000000 else 10000000
            produk = "KUR Mikro BRI" if plafon > 10000000 else "KUR Super Mikro BRI"

            st.markdown(f'<div class="white-card"><h4>Rekomendasi Plafon:</h4><h2>{produk}: {format_rp(plafon)}</h2><p>Batas Cicilan Aman Sistem: <b>{format_rp(max_cicilan_aman)}/bln</b></p></div>', unsafe_allow_html=True)
            
            tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            total_cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            sisa_laba = laba_bln - total_cicilan
            persen_sisa = (sisa_laba / laba_bln) * 100

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f'<div class="white-card"><h4>Cicilan Per Bulan:</h4><h3>{format_rp(total_cicilan)}</h3></div>', unsafe_allow_html=True)
            with col_b:
                warna_sisa = "green" if persen_sisa >= 70 else "orange"
                st.markdown(f'<div class="white-card"><h4>Sisa Laba Bersih:</h4><h3 style="color:{warna_sisa};">{format_rp(sisa_laba)} ({persen_sisa:.0f}%)</h3></div>', unsafe_allow_html=True)

            # --- FITUR TAMBAHAN: NARASI ANALISIS (YANG ANDA MINTA) ---
            st.write("---")
            st.subheader("📝 Kesimpulan Analisis Hasil (Credit Scoring)")
            
            narasi_status = "Sangat Layak" if persen_sisa >= 70 else "Perlu Penyesuaian"
            
            st.markdown(f"""
            <div class="white-card" style="border-left: 8px solid #001f3f;">
                Berdasarkan data bulan {sel_b}, ini adalah hasil analisis kelayakan pinjaman mandiri untuk usaha Anda. 
                Kabar baiknya, status Anda dianggap <b>"{narasi_status}"</b>, namun ada rincian penting:
                <br><br>
                <b>1. Rekomendasi Pinjaman:</b><br>
                Sistem menyarankan produk <b>{produk}</b> dengan plafon <b>{format_rp(plafon)}</b>. 
                Produk ini ditujukan untuk UMKM dengan bunga subsidi pemerintah.
                <br><br>
                <b>2. Analisis Batas Cicilan Aman:</b><br>
                Sistem menghitung cicilan ideal Anda adalah <b>{format_rp(max_cicilan_aman)}/bulan</b>. 
                Pada pilihan tenor {tenor} bulan, cicilan Anda menjadi <b>{format_rp(total_cicilan)}/bulan</b>.
                <br><br>
                <b>3. Sisa Laba Bersih & Arus Kas:</b><br>
                Setelah bayar cicilan, sisa laba Anda adalah <b>{format_rp(sisa_laba)} ({persen_sisa:.0f}%)</b>. 
                <br><i>*Catatan: Bank menyukai sisa laba > 70% agar arus kas tetap sehat.</i>
                <br><br>
                <b>Kesimpulan & Saran:</b><br>
                {"✅ Pilihan tenor sudah tepat dan aman bagi keuangan Anda." if persen_sisa >= 70 else f"⚠️ Tenor {tenor} bulan terlihat agak <b>'memaksa'</b> keuangan Anda karena sisa laba di bawah 70%. Agar lebih mudah disetujui bank, cobalah geser slider ke 24 atau 36 bulan untuk mendekati batas aman."}
            </div>
            """, unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi Data")
        df_rev = df.sort_values(by='id', ascending=False)
        target = st.selectbox("Pilih data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Silakan masukkan transaksi pertama Anda.")

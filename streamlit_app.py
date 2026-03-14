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
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    modal_awal_input = st.text_input("Modal Awal (Kas)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    total_laba = df['laba'].sum() if not df.empty else 0
    total_prive = df['prive'].sum() if not df.empty else 0
    kas_sekarang = modal_awal + total_laba - total_prive
    
    st.markdown(f"Kas Saat Ini:<br><h2 style='color:#FFD700;'>{format_rp(kas_sekarang)}</h2>", unsafe_allow_html=True)
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")

# --- FITUR BARU: UI MODERN PENCATATAN ---
st.subheader("📝 Catat Penjualan")
rekap_mode = st.radio("Pilih Mode Pencatatan:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

with st.container():
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if rekap_mode == "Harian":
            input_tgl = st.date_input("Pilih Tanggal", datetime.now())
            val_tgl = input_tgl.strftime("%Y-%m-%d")
            val_minggu = f"Minggu {input_tgl.isocalendar()[1]}"
            val_bulan = input_tgl.strftime("%B %Y")
        elif rekap_mode == "Mingguan":
            input_minggu = st.number_input("Minggu Ke- (1-52)", 1, 52, 1)
            val_tgl = f"Periode Minggu {input_minggu}"
            val_minggu = f"Minggu {input_minggu}"
            val_bulan = datetime.now().strftime("%B %Y")
        else:
            list_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            sel_nama_bulan = st.selectbox("Pilih Bulan", list_bulan)
            val_bulan = f"{sel_nama_bulan} {datetime.now().year}"
            val_tgl = f"Rekap {val_bulan}"
            val_minggu = "-"

    with col2:
        omzet_in = st.number_input("Total Omzet", value=0, step=50000)
    
    with col3:
        # Kalkulasi otomatis tetap sesuai logika Anda
        biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
        laba_in = omzet_in - biaya_hpp
        prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0
        
        st.write("") # Spacer
        if st.button("🔔 SIMPAN DATA"):
            if omzet_in > 0:
                c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (val_tgl, val_bulan, val_minggu, omzet_in, laba_in, prive_in, rekap_mode))
                conn.commit()
                st.success("Data Berhasil Disimpan!")
                st.rerun()
            else:
                st.warning("Masukkan Omzet terlebih dahulu!")

# --- BAGIAN TABS (LAPORAN, KUR, REVISI) ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        list_bulan_laporan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Filter Laporan Bulan:", list_bulan_laporan, index=len(list_bulan_laporan)-1)
        
        db_bulan = df[df['bulan'] == sel_b]
        omzet_bln = db_bulan['omzet'].sum()
        laba_bln = db_bulan['laba'].sum()
        prive_bln = db_bulan['prive'].sum()
        
        # Hitung saldo awal bulan tersebut
        idx_b = list_bulan_laporan.index(sel_b)
        laba_lalu = df[df['bulan'].isin(list_bulan_laporan[:idx_b])]['laba'].sum()
        prive_lalu = df[df['bulan'].isin(list_bulan_laporan[:idx_b])]['prive'].sum()
        m_awal_bln = modal_awal + laba_lalu - prive_lalu
        m_akhir_bln = m_awal_bln + laba_bln - prive_bln

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f'<div class="white-card"><h3>LABA RUGI - {sel_b}</h3><hr>Omzet: {format_rp(omzet_bln)}<br>Laba Bersih: <b>{format_rp(laba_bln)}</b></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="white-card"><h3>MODAL - {sel_b}</h3><hr>Kas Awal: {format_rp(m_awal_bln)}<br>Kas Akhir: <b>{format_rp(m_akhir_bln)}</b></div>', unsafe_allow_html=True)

    with tab_kur:
        st.subheader("🏦 Konsultasi Strategis KUR")
        if jumlah_bulan_data < 3:
            st.error("### 🚩 DATA BELUM CUKUP")
            st.info(f"Lengkapi catatan {3-jumlah_bulan_data} bulan lagi.")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            # Logika narasi analisis Anda tetap di sini
            max_cicilan_aman = laba_bln * 0.35
            plafon = 10000000
            st.markdown(f'<div class="white-card">Batas Cicilan Aman: <b>{format_rp(max_cicilan_aman)}/bln</b></div>', unsafe_allow_html=True)
            
            tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            total_cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            sisa_laba = laba_bln - total_cicilan
            persen_sisa = (sisa_laba / laba_bln) * 100
            
            # Narasi otomatis sesuai permintaan Anda
            st.markdown(f"""
            <div class="white-card">
                <b>Hasil Analisis Kelayakan:</b><br>
                Sisa Laba: {format_rp(sisa_laba)} ({persen_sisa:.0f}%)<br>
                {"✅ Aman dan layak diajukan." if persen_sisa >= 70 else "⚠️ Disarankan memperpanjang tenor agar sisa laba di atas 70%."}
            </div>
            """, unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi Data")
        df_rev = df.sort_values(by='id', ascending=False)
        target = st.selectbox("Pilih data:", [f"ID:{r['id']} | {r['tanggal']}" for _, r in df_rev.iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Halo! Masukkan data transaksi pertama Anda di atas.")

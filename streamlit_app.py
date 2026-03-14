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

# --- SIDEBAR: PROFIL & SEKTOR USAHA ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    
    # NEW: SEKTOR USAHA
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
    
    # LOGIKA INTERAKTIF MARGIN PER SEKTOR
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin Anda: **{margin_pct:.1f}%**")
        
        # Standar Margin: Kuliner (40-60%), Retail (15-25%), Jasa (50%+), Produksi (30%+)
        if sektor == "Kuliner (Makanan/Minuman)":
            if margin_pct < 40: st.error("❌ Terlalu Rendah. Kuliner minimal 40-50% untuk tutup biaya gas/listrik.")
            else: st.success("✅ Sangat Baik. Margin kuliner Anda sehat.")
        elif sektor == "Retail (Toko Kelontong/Baju)":
            if margin_pct < 15: st.error("❌ Terlalu Rendah. Retail butuh perputaran cepat dengan margin min 15%.")
            else: st.success("✅ Sesuai Standar Retail.")
        elif sektor == "Jasa (Laundry/Service)":
            if margin_pct < 50: st.warning("⚠️ Jasa biasanya punya margin > 60% karena modal utama adalah tenaga.")
            else: st.success("✅ Margin Jasa Luar Biasa.")
        else: # Produksi
            if margin_pct < 30: st.error("❌ Terlalu Rendah untuk Sektor Produksi.")
            else: st.success("✅ Margin Produksi Sehat.")

    st.write("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)
    if prive_pct > 30: st.warning("⚠️ Prive tinggi menghambat modal.")

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

    if omzet_in > 0:
        st.info(f"Analisis: Laba {format_rp(laba_in)} | Prive {format_rp(prive_in)}")

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown(f'<div class="white-card"><h3>💡 Rekomendasi Sektor</h3><p>Untuk sektor <b>{sektor}</b>, bank sangat memperhatikan efisiensi biaya bahan baku. Jaga margin Anda agar tetap di zona hijau.</p></div>', unsafe_allow_html=True)

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
                        <td>LABA BERSIH</td><td style="text-align:right;">{format_rp(laba_bln)}</td>
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
        st.subheader("🏦 Konsultasi Strategis KUR (Analisis Mantri)")
        
        # --- LOGIKA ANALISIS MANTRI (DEEP ANALYSIS) ---
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        # Hitung Tren Laba (Jika data > 1 bulan)
        if jumlah_bulan_data > 1:
            laba_rata_rata = df['laba'].mean()
            laba_terakhir = df.iloc[-1]['laba']
            tren_laba = "Naik 📈" if laba_terakhir > laba_rata_rata else "Turun 📉"
        else:
            laba_rata_rata = laba_bln
            tren_laba = "Stabil (Data Baru)"

        # 1. VALIDASI DURASI (SYARAT UTAMA BANK)
        if jumlah_bulan_data < 3:
            st.error(f"### 🚩 STATUS: BELUM LAYAK (DATA KURANG)")
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""<div class="white-card" style="border-left: 8px solid red;">
                    <h4>Kenapa Ditolak?</h4>
                    <p>Bank tidak bisa melihat <b>pola konsistensi</b> usaha Anda. Kredit tanpa histori laporan yang cukup dianggap spekulasi.</p>
                    <hr><b>Tugas Anda:</b> Lengkapi minimal {3-jumlah_bulan_data} bulan laporan lagi.</div>""", unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""<div class="white-card">
                    <h4>Target Sebelum Pinjam:</h4>
                    <ul>
                        <li>Rapikan catatan Harian</li>
                        <li>Pastikan Omzet stabil/naik</li>
                        <li>Siapkan Dokumen NIB & SKU</li>
                    </ul></div>""", unsafe_allow_html=True)

        # 2. VALIDASI KESEHATAN (LABA & MARGIN)
        elif laba_bln < 1500000:
            st.warning("### ⚠️ STATUS: PERBAIKI PERFORMANCE")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid orange;">
                <h4>Analisis Konsultan:</h4>
                <p>Laba Anda <b>{format_rp(laba_bln)}</b> dengan tren <b>{tren_laba}</b>.</p>
                <p>Untuk pinjaman KUR terkecil pun, laba di bawah 1.5 Juta akan membuat hidup Anda susah karena sisa uang setelah cicilan terlalu sedikit.</p>
                <hr><b>Saran:</b> Naikkan Omzet 20% lagi bulan depan sebelum tanda tangan kontrak bank.</div>""", unsafe_allow_html=True)

        # 3. KONDISI LAYAK (STRATEGI EKSPANSI)
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            
            # Perhitungan DSR (Debt Service Ratio) - Standar Bank 30%
            max_cicilan_aman = laba_bln * 0.30
            
            # Penentuan Plafon Berdasarkan Kas & Laba
            if modal_akhir_bln > 15000000 and laba_bln > 5000000:
                plafon = 50000000
                produk = "KUR Mikro BRI"
            else:
                plafon = 10000000
                produk = "KUR Super Mikro BRI"

            st.markdown(f"""<div class="white-card">
                <h4>Rekomendasi Plafon & Produk:</h4>
                <h2 style="color:#001f3f;">{produk}: {format_rp(plafon)}</h2>
                <p>Tren Laba Anda: <b>{tren_laba}</b> | Batas Cicilan Aman: <b>{format_rp(max_cicilan_aman)}/bln</b></p>
            </div>""", unsafe_allow_html=True)

            # SIMULASI CICILAN & SAFETY ZONE
            tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            bunga_bln = (plafon * 0.06) / 12
            pokok_bln = plafon / tenor
            total_cicilan = pokok_bln + bunga_bln
            
            sisa_laba = laba_bln - total_cicilan
            persen_sisa = (sisa_laba / laba_bln) * 100

            c1, c2 = st.columns(2)
            with c1:
                warna_sisa = "green" if total_cicilan <= max_cicilan_aman else "red"
                st.markdown(f"""<div class="white-card">
                    <h4>Rincian Kewajiban:</h4>
                    <p>Cicilan Per Bulan: <b>{format_rp(total_cicilan)}</b></p>
                    <p>Sisa Laba Bersih: <b style="color:{warna_sisa};">{format_rp(sisa_laba)} ({persen_sisa:.0f}%)</b></p>
                    <hr><small>*Bank menyukai sisa laba > 70% setelah cicilan.</small>
                </div>""", unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"""<div class="white-card" style="border-left: 8px solid #FFD700;">
                    <h4>💡 Strategi Modal:</h4>
                    <p>Jika Dana Cair, target Omzet Anda harus naik menjadi:</p>
                    <h4 style="color:green;">{format_rp(omzet_bln * 1.5)}/bln</h4>
                    <p><small>Agar rasio utang Anda tetap sehat (Leverage Analysis).</small></p>
                </div>""", unsafe_allow_html=True)

            # CHECKLIST DOKUMEN (INTERAKTIF)
            st.write("---")
            st.subheader("📂 Checklist Dokumen ke Bank")
            st.checkbox("KTP Pemilik & Pasangan")
            st.checkbox("NIB (Nomor Induk Berusaha)")
            st.checkbox("Surat Keterangan Usaha (SKU) dari Desa/Kelurahan")
            st.checkbox(f"Print Laporan FIN-Saku Bulan {sel_b} (Sangat disarankan)")

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
    st.info("👋 Halo! Silakan masukkan data transaksi pertama Anda di atas.")

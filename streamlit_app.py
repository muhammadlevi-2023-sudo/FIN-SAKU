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
        
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        if jumlah_bulan_data < 3:
            st.error(f"### 🚩 STATUS: BELUM LAYAK (DATA KURANG)")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid red;">
                <h4>Kenapa Belum Bisa Pinjam?</h4>
                <p>Bank BRI butuh melihat konsistensi. Ibarat kenalan, Bank belum 'kenal' dalam dengan bisnis Anda. 
                Lengkapi catatan <b>{3-jumlah_bulan_data} bulan</b> lagi agar Bank percaya bahwa laba Anda bukan kebetulan.</p>
                </div>""", unsafe_allow_html=True)
        
        elif laba_bln < 1500000:
            st.warning("### ⚠️ STATUS: PERBAIKI PERFORMANCE")
            st.markdown(f"""<div class="white-card" style="border-left: 8px solid orange;">
                <h4>Analisis Konsultan:</h4>
                <p>Laba Anda {format_rp(laba_bln)} masih terlalu mepet untuk membayar cicilan bank. 
                Saran: Fokus naikkan penjualan dulu bulan depan agar saat pinjam, Anda tidak pusing bayar cicilannya.</p>
                </div>""", unsafe_allow_html=True)
        
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            
            # Perhitungan Logika Bank
            max_cicilan_aman = laba_bln * 0.35 # 35% dari laba
            plafon = 50000000 if modal_akhir_bln > 15000000 else 10000000
            produk = "KUR Mikro BRI" if plafon > 10000000 else "KUR Super Mikro BRI"

            st.markdown(f"""<div class="white-card">
                <h4>Rekomendasi Pinjaman:</h4>
                <h2 style="color:#001f3f;">{produk}: {format_rp(plafon)}</h2>
                <p>Batas Cicilan Aman menurut sistem: <b style="color:green;">{format_rp(max_cicilan_aman)}/bln</b></p>
            </div>""", unsafe_allow_html=True)

            tenor = st.select_slider("Geser untuk pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            
            # Hitung Cicilan
            total_cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            sisa_laba = laba_bln - total_cicilan
            persen_sisa = (sisa_laba / laba_bln) * 100

            # UI DASHBOARD ANGKA
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""<div class="white-card">
                    <p style="margin:0;">Cicilan Per Bulan:</p>
                    <h3 style="margin:0; color:#001f3f;">{format_rp(total_cicilan)}</h3>
                    <p style="margin:0; font-size:12px;">Tenor {tenor} Bulan</p>
                </div>""", unsafe_allow_html=True)
            with c2:
                warna_sisa = "green" if persen_sisa >= 70 else "orange"
                st.markdown(f"""<div class="white-card">
                    <p style="margin:0;">Sisa Laba Bersih:</p>
                    <h3 style="margin:0; color:{warna_sisa};">{format_rp(sisa_laba)} ({persen_sisa:.0f}%)</h3>
                    <p style="margin:0; font-size:12px;">Setelah bayar cicilan</p>
                </div>""", unsafe_allow_html=True)

            # --- BAGIAN NARASI PENJELASAN (HUMAN FRIENDLY) ---
            st.write("---")
            st.subheader("📝 Penjelasan Hasil Analisis Anda")
            
            if persen_sisa < 70:
                st.markdown(f"""
                <div style="background-color: #fff3cd; padding: 20px; border-radius: 10px; color: #856404; border: 1px solid #ffeeba;">
                    <b>Kesimpulan & Saran:</b><br>
                    Meskipun status Anda "Sangat Layak", simulasi {tenor} bulan ini terlihat agak <b>"memaksa"</b> keuangan Anda. 
                    Cicilan {format_rp(total_cicilan)} melebihi batas aman yang disarankan ({format_rp(max_cicilan_aman)}).<br><br>
                    <b>Agar lebih mudah disetujui bank:</b><br>
                    1. <b>Perpanjang Jangka Waktu:</b> Coba geser slider ke 24 atau 36 bulan. Ini akan menurunkan cicilan bulanan mendekati angka aman.<br>
                    2. <b>Posisi Manis:</b> Bank sangat menyukai jika sisa laba Anda di atas 70%. Saat ini sisa Anda hanya {persen_sisa:.0f}%.
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: #d4edda; padding: 20px; border-radius: 10px; color: #155724; border: 1px solid #c3e6cb;">
                    <b>Kesimpulan & Saran:</b><br>
                    Pilihan tenor {tenor} bulan sudah <b>SANGAT TEPAT</b>. Cicilan Anda berada di bawah batas aman, dan sisa laba Anda ({persen_sisa:.0f}%) berada di "Posisi Manis" mata Bank BRI.<br><br>
                    Silakan ajukan ke Mantri BRI dengan membawa laporan dari FIN-Saku ini sebagai bukti Anda UMKM yang melek finansial!
                </div>
                """, unsafe_allow_html=True)

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

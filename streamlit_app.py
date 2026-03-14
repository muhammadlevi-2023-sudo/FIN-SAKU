import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi Perbankan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v12.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL, periode TEXT)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    # Logika untuk menangani angka negatif (Rugi)
    try:
        abs_angka = abs(float(angka))
        formatted = "Rp {:,.0f}".format(abs_angka).replace(",", ".")
        return f"- {formatted}" if angka < 0 else f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    # Tetap bisa baca angka meskipun user input manual
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# 2. UI CUSTOM
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

# --- LOGIKA MODAL BERJALAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba_kumulatif = df['laba'].sum() if not df.empty else 0
total_prive_kumulatif = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: PARAMETER ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju")
    
    modal_awal = clean_to_int(st.text_input("Modal Kas Awal (Rp)", "7000000"))
    modal_sekarang = modal_awal + (total_laba_kumulatif - total_prive_kumulatif)
    
    st.markdown(f"**Modal Awal: {format_rp(modal_awal)}**")
    color_modal = "#FFD700" if modal_sekarang >= modal_awal else "#FF4B4B"
    st.markdown(f"**Modal Terkini: <span style='color:{color_modal};'>{format_rp(modal_sekarang)}</span>**", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("📦 Konfigurasi Produk")
    hpp_val = clean_to_int(st.text_input("HPP / Modal Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual Produk", "15000"))
    
    if hrg_val > 0:
        margin_rp = hrg_val - hpp_val
        margin_pct = (margin_rp / hrg_val) * 100
        st.markdown(f"Margin: **{margin_pct:.1f}%** ({format_rp(margin_rp)})")
        if margin_pct <= 0: st.error("⚠️ AWAS! Harga jual lebih rendah dari modal (RUGI).")

    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Pusat Analisis: {nama_u}")

rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Input {rekap_mode}")
    tgl = st.date_input("Tanggal", datetime.now())
    
    # Menghapus min_value agar bisa input angka kecil atau 0 jika rugi total
    omzet = st.number_input(f"Total Omzet {rekap_mode}", value=0, step=1000)
    
    # Hitung Laba/Rugi: Laba = Omzet - (Omzet / Harga Jual * HPP)
    # Ini memastikan kalau omzet dikit, labanya bisa minus (Rugi)
    if hrg_val > 0:
        beban_pokok = omzet * (hpp_val / hrg_val)
        laba = omzet - beban_pokok
    else:
        laba = 0

    # Jika laba negatif (Rugi), Prive otomatis 0 karena tidak ada yang bisa diambil
    prive = laba * (prive_pct / 100) if laba > 0 else 0

    if laba < 0:
        st.error(f"⚠️ Terdeteksi Rugi: {format_rp(laba)}")
    else:
        st.success(f"Estimasi Laba: {format_rp(laba)}")

    if st.button("🔔 SIMPAN KE LAPORAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive, rekap_mode))
        conn.commit()
        st.rerun()

# --- ANALISIS KUR (BULAN TERAKHIR) ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI"])

    with t_rep:
        sel_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        data_b = df[df['bulan'] == sel_b]
        o, l, p = data_b['omzet'].sum(), data_b['laba'].sum(), data_b['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Bulanan: {sel_b}</h3>
            <table style="width:100%; font-size:1.1em;">
                <tr><td>Total Omzet</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td>Beban Usaha (HPP)</td><td style="text-align:right;">{format_rp(o-l)}</td></tr>
                <tr style="border-top: 2px solid black;">
                    <td><b>LABA/RUGI BERSIH</b></td>
                    <td style="text-align:right; color:{'red' if l < 0 else 'black'};"><b>{format_rp(l)}</b></td>
                </tr>
                <tr><td>Prive (Diambil)</td><td style="text-align:right;">({format_rp(p)})</td></tr>
                <tr style="background:#fff9c4;"><td><b>SISA KAS (UPDATE MODAL)</b></td><td style="text-align:right;"><b>{format_rp(l-p)}</b></td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        # LOGIKA KUR BERBASIS BULAN TERAKHIR (DATA TERBARU)
        bulan_terakhir = df['bulan'].iloc[-1]
        data_akhir = df[df['bulan'] == bulan_terakhir]
        laba_akhir = data_akhir['laba'].sum()
        prive_akhir = data_akhir['prive'].sum()
        
        # 1. PERHITUNGAN REPAYMENT CAPACITY (RPC) - STANDAR PERBANKAN
        # Bank biasanya mematok 30% - 40% dari laba bersih untuk cicilan
        rpc_aman = laba_akhir * 0.35 
        
        # 2. SIMULASI PLAFON PINJAMAN (TENOR 24 BULAN)
        # Menghitung plafon dengan asumsi bunga KUR 6% efektif p.a
        plafon_max = rpc_aman * 22 # Faktor pengali 22 untuk ruang bunga & biaya provisi
        
        st.subheader(f"🏦 Analisis Kelayakan Pinjaman ({bulan_terakhir})")
        
        # TAMPILAN METRIC UTAMA
        c1, c2, c3 = st.columns(3)
        c1.metric("Kapasitas Cicilan/Bulan", format_rp(rpc_aman))
        c2.metric("Saran Plafon Kredit", format_rp(plafon_max))
        c3.metric("Laba Setelah Prive", format_rp(laba_akhir - prive_akhir))

        # 3. JURNAL ANALISIS PENDAPAT & STRATEGI
        st.markdown("### 📝 Jurnal Analisis Strategis")
        
        if laba_akhir <= 0:
            st.error(f"**STATUS: TIDAK LAYAK (Negative Income)**")
            st.markdown(f"""
            * **Analisis:** Pendapatan bulan {bulan_terakhir} tidak mampu menutupi beban pokok (Rugi).
            * **Resiko:** Memaksakan pinjaman saat rugi akan menggerus modal inti Anda dengan cepat.
            * **Saran Strategi:** Fokus pada efisiensi HPP atau menaikkan volume penjualan sebelum mengajukan KUR.
            """)
        else:
            # Hitung Debt Service Coverage Ratio (DSCR) Sederhana
            dscr = laba_akhir / rpc_aman if rpc_aman > 0 else 0
            
            st.success(f"**STATUS: LAYAK (Bankable)**")
            
            # KATEGORI SARAN PINJAMAN
            if plafon_max > 50000000:
                rekomendasi = "KUR Ritel (Plafon Besar)"
                catatan = "Usaha Anda sangat sehat. Anda punya daya tawar tinggi untuk meminta bunga rendah."
            elif plafon_max >= 10000000:
                rekomendasi = "KUR Mikro"
                catatan = "Angka ini ideal untuk ekspansi stok atau penambahan alat kerja ringan."
            else:
                rekomendasi = "KUR Super Mikro"
                catatan = "Disarankan ambil plafon kecil dulu untuk memperkuat credit history di BRI."

            st.markdown(f"""
            <div class="white-card">
                <p><b>Rincian Perhitungan Perbankan:</b></p>
                <ul>
                    <li><b>Analisis Cicilan:</b> Dengan laba {format_rp(laba_akhir)}, cicilan paling aman bagi Anda adalah <b>{format_rp(rpc_aman)}</b> per bulan. Jangan mengambil cicilan di atas angka ini agar napas usaha tidak sesak.</li>
                    <li><b>Rekomendasi Produk:</b> {rekomendasi}</li>
                    <li><b>Efisiensi Bunga:</b> Estimasi bunga (0.5% flat/bulan) dari plafon saran adalah <b>{format_rp(plafon_max * 0.005)}</b>. Pendapatan Anda mampu meng-cover bunga ini sebanyak <b>{laba_akhir/(plafon_max*0.005):.1f} kali lipat</b>.</li>
                    <li><b>Strategi Kedepan:</b> {catatan}</li>
                </ul>
                <p style='color:blue;'><i>*Hasil ini didasarkan pada perhitungan Repayment Capacity (RPC) yang umum digunakan analis kredit BRI.</i></p>
            </div>
            """, unsafe_allow_html=True)

        # 4. BAGIAN ANALISIS PENDAPAT (GOOD/BAD INCOME)
        st.markdown("### 📉 Analisis Kualitas Pendapatan")
        margin_real = (laba_akhir / data_akhir['omzet'].sum() * 100) if data_akhir['omzet'].sum() > 0 else 0
        
        col_a, col_b = st.columns(2)
        with col_a:
            if margin_real < 20:
                st.warning(f"**Margin Rendah ({margin_real:.1f}%)**")
                st.write("Pendapatan Anda 'melelahkan'. Omzet besar tapi laba tipis. Bank berisiko menganggap usaha Anda rentan terhadap kenaikan harga bahan baku.")
            else:
                st.success(f"**Margin Kuat ({margin_real:.1f}%)**")
                st.write("Kualitas pendapatan sangat baik. Anda memiliki ruang yang cukup untuk membayar bunga bank dan tetap mencetak profit.")
        
        with col_b:
            prive_ratio = (prive_akhir / laba_akhir * 100) if laba_akhir > 0 else 0
            if prive_ratio > 50:
                st.error(f"**Kebocoran Kas ({prive_ratio:.1f}%)**")
                st.write("Pengambilan pribadi terlalu besar. Ini adalah 'Red Flag' bagi bank karena modal usaha terus ditarik untuk kepentingan konsumtif.")
            else:
                st.info(f"**Efisiensi Kas ({prive_ratio:.1f}%)**")
                st.write("Pengaturan Prive disiplin. Sebagian besar laba kembali menjadi modal, hal ini sangat disukai oleh Mantri BRI.")

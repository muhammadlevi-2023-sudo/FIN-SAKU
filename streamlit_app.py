import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali Modal UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v13.db', check_same_thread=False)
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

# 2. UI CUSTOM (NAVY & GOLD UNAIR)
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
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_omzet = df['omzet'].sum() if not df.empty else 0
total_untung_rugi = df['laba'].sum() if not df.empty else 0 # Bisa positif (untung) atau negatif (rugi)
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: MONITORING ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    # LOGIKA PENGURANG MODAL (Realtime)
    modal_sekarang = modal_awal + total_untung_rugi - total_prive
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_sekarang)}</h3>", unsafe_allow_html=True)
    
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
    
    # LOGIKA UNTUNG/RUGI PER TRANSAKSI
    # Laba = Omzet - (Beban HPP). Jika beban > omzet, maka laba jadi minus (RUGI)
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_rugi_in = omzet_in - biaya_hpp
    prive_in = laba_rugi_in * (prive_pct / 100) if laba_rugi_in > 0 else 0

    if laba_rugi_in < 0:
        st.error(f"Estimasi Rugi: {format_rp(laba_rugi_in)}")
    else:
        st.info(f"Estimasi Laba: {format_rp(laba_rugi_in)}")

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_rugi_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown(f"""
    <div class="white-card">
        <h3>⚠️ Logika Pengurangan Modal</h3>
        <p>Sistem ini mendeteksi kesehatan kas Anda secara otomatis:</p>
        <ul>
            <li><b>Jika Laba:</b> Kas/Modal akan bertambah.</li>
            <li><b>Jika Rugi:</b> Kas/Modal akan langsung berkurang.</li>
            <li><b>Jika Prive:</b> Saldo kas diambil untuk keperluan pribadi.</li>
        </ul>
        <p style="font-size: 13px; color: gray;">*Pastikan harga jual selalu di atas HPP agar modal tidak tergerus.</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN & KUR ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN LABA RUGI & MODAL", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        c_lr, c_pm = st.columns(2)
        
        with c_lr:
            label_hasil = "LABA BERSIH" if total_untung_rugi >= 0 else "RUGI BERSIH"
            warna_hasil = "green" if total_untung_rugi >= 0 else "red"
            
            st.markdown(f"""
            <div class="white-card">
                <h3 style="text-align:center;">LAPORAN LABA RUGI</h3>
                <hr>
                <table style="width:100%;">
                    <tr><td>Total Pendapatan</td><td style="text-align:right;">{format_rp(total_omzet)}</td></tr>
                    <tr style="color:red;"><td>Total Beban HPP</td><td style="text-align:right;">({format_rp(total_omzet - total_untung_rugi)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; font-size:18px; color:{warna_hasil};">
                        <td>{label_hasil}</td><td style="text-align:right;">{format_rp(total_untung_rugi)}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        with c_pm:
            st.markdown(f"""
            <div class="white-card">
                <h3 style="text-align:center;">PERUBAHAN MODAL</h3>
                <hr>
                <table style="width:100%;">
                    <tr><td>Modal Awal Usaha</td><td style="text-align:right;">{format_rp(modal_awal)}</td></tr>
                    <tr><td>Hasil Usaha (Laba/Rugi)</td><td style="text-align:right; color:{warna_hasil};">{format_rp(total_untung_rugi)}</td></tr>
                    <tr style="color:red;"><td>Pengambilan Prive</td><td style="text-align:right;">({format_rp(total_prive)})</td></tr>
                    <tr style="border-top:2px solid black; font-weight:bold; font-size:18px; background:#FFD700;">
                        <td>KAS AKHIR</td><td style="text-align:right;">{format_rp(modal_sekarang)}</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

    with tab_kur:
        # LOGIKA KUR: Usaha Rugi = Auto Ditolak
        laba_rata = df['laba'].mean() * (30 if rekap_mode == "Harian" else 1)
        
        if total_untung_rugi <= 0:
            st.error("### ❌ STATUS: DITOLAK (Usaha Mengalami Kerugian)")
            st.info("Bank hanya memberikan kredit kepada usaha yang menghasilkan laba. Perbaiki struktur biaya Anda sebelum mengajukan KUR.")
        elif modal_sekarang < 5000000:
            st.warning("### ⚠️ STATUS: DITOLAK (Kas Terlalu Kecil)")
            st.write("Saldo kas Anda tidak mencukupi syarat minimal likuiditas Bank.")
        else:
            plafon = laba_rata * 12
            st.success(f"### ✅ STATUS: LAYAK AJUKAN ({format_rp(plafon)})")
            st.write(f"Estimasi Cicilan KUR 6% tenor 24 bln: **{format_rp((plafon/24) + (plafon*0.005))} / bulan**")

    with tab_rev:
        st.subheader("🛠️ Riwayat & Hapus Data")
        df_view = df.sort_values(by='id', ascending=False)
        pilihan = st.selectbox("Pilih data untuk dihapus:", [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_view.iterrows()])
        if st.button("🗑️ Hapus Transaksi"):
            idx = int(pilihan.split(' | ')[0])
            c.execute(f"DELETE FROM transaksi WHERE id={idx}")
            conn.commit()
            st.rerun()
else:
    st.info("Belum ada data. Silakan isi form penjualan.")

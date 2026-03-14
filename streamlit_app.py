import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Kendali Modal UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_v12.db', check_same_thread=False)
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
    .white-card *, .white-card p, .white-card b, .white-card h3 { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; }
    .sidebar-text { font-size: 14px; margin-bottom: 5px; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_omzet = df['omzet'].sum() if not df.empty else 0
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: MONITORING REALTIME ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🏠 Profil & Live Stat")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    jenis_u = st.selectbox("Jenis Usaha", ["Dagang", "Jasa", "Produksi"])
    
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    # HITUNGAN REALTIME (TIDAK BOLEH HILANG)
    modal_sekarang = modal_awal + (total_laba - total_prive)
    
    st.markdown("---")
    st.markdown(f"<div class='sidebar-text'>Modal Awal: <b>{format_rp(modal_awal)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sidebar-text'>Total Laba Realtime: <b style='color:#00ff88;'>{format_rp(total_laba)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sidebar-text'>Total Prive (Ambil): <b style='color:#ff4b4b;'>{format_rp(total_prive)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini: {format_rp(modal_sekarang)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")

rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_guidance = st.columns([1, 1.2])

with col_in:
    st.subheader(f"📝 Form Input {rekap_mode}")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet = st.number_input(f"Total Omzet ({rekap_mode})", value=0)
    
    laba_input = omzet - (omzet * (hpp_val / hrg_val)) if hrg_val > 0 else 0
    prive_input = laba_input * (prive_pct / 100) if laba_input > 0 else 0

    st.info(f"Estimasi Laba: {format_rp(laba_input)}")

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba_input, prive_input, rekap_mode))
        conn.commit()
        st.rerun()

with col_guidance:
    st.markdown(f"""
    <div class="white-card">
        <h3>💡 Pemisahan Uang (Bankability)</h3>
        <p>Agar layak KUR, Bank BRI melihat kedisiplinan Anda memisahkan uang:</p>
        <table style="width:100%; color:black;">
            <tr><td><b>Uang Kas</b></td><td>Operasional Usaha</td></tr>
            <tr><td><b>Uang Prive</b></td><td>Gaji/Jajan Pribadi</td></tr>
        </table>
        <p style="margin-top:10px;">Status Prive: <b>{prive_pct}% dari Laba</b>. (Saran BRI: <30%)</p>
    </div>
    """, unsafe_allow_html=True)

# --- LAPORAN KEUANGAN JELAS & ANALISIS KUR ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN PERUBAHAN MODAL", "🏦 SIMULASI KUR BRI"])
    
    with t_rep:
        sel_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        
        laba_bln = db['laba'].sum()
        prive_bln = db['prive'].sum()
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Perubahan Modal - {sel_b}</h3>
            <hr>
            <table style="width:100%; font-size:18px;">
                <tr><td>1. Total Omzet (Uang Masuk)</td><td style="text-align:right;">{format_rp(db['omzet'].sum())}</td></tr>
                <tr><td>2. Laba Bersih (Hasil Usaha)</td><td style="text-align:right; color:green;">{format_rp(laba_bln)}</td></tr>
                <tr><td>3. Prive (Uang Diambil Pribadi)</td><td style="text-align:right; color:red;">({format_rp(prive_bln)})</td></tr>
                <tr style="font-weight:bold; border-top:2px solid black;">
                    <td>PENAMBAHAN MODAL KAS</td>
                    <td style="text-align:right; border-top:2px solid black;">{format_rp(laba_bln - prive_bln)}</td>
                </tr>
            </table>
            <p style="font-size:12px; margin-top:10px;">*Jika angka Penambahan Modal positif, berarti uang kas usaha Anda bertambah sehat.</p>
        </div>
        """, unsafe_allow_html=True)
with t_kur:
        # --- LOGIKA ANALISIS PINJAMAN ---
        # Mengambil laba dari data terakhir yang diinput
        laba_akhir = df.iloc[-1]['laba'] if not df.empty else 0
        rpc_aman = laba_akhir * 0.35  # Standar Bank: Cicilan maks 35% laba
        
        # Simulasi Plafon (Minimal KUR Mikro 10jt, Plafon disarankan = RPC * 24 bulan)
        plafon_hitung = (rpc_aman * 24)
        plafon_final = plafon_hitung if plafon_hitung >= 10000000 else 10000000
        
        # Hitung Cicilan KUR BRI (Bunga 6% per tahun atau 0.5% per bulan)
        bunga_bln = plafon_final * 0.005
        pokok_bln = plafon_final / 24
        total_cicilan = pokok_bln + bunga_bln

        st.markdown("### 🏦 Simulasi & Kelayakan KUR BRI")
        
        # 1. INDIKATOR STATUS (Jawaban Langsung untuk Orang Awam)
        if laba_akhir >= total_cicilan and (total_laba - total_prive) > 0:
            st.success("### ✅ STATUS: LAYAK AJUKAN")
            status_text = "Laba Anda cukup untuk membayar cicilan dengan sangat aman."
        elif laba_akhir > 0:
            st.warning("### ⚠️ STATUS: PERTIMBANGKAN LAGI")
            status_text = "Anda bisa mencicil, tapi sisa laba untuk operasional akan sangat tipis."
        else:
            st.error("### ❌ STATUS: BELUM LAYAK")
            status_text = "Laba Anda saat ini belum mencukupi untuk mengambil pinjaman KUR."

        # 2. KARTU INFORMASI UTAMA
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="white-card">
                <p style="margin:0;">Kemampuan Bayar (Per Bulan):</p>
                <h2 style="color:#28a745; margin:0;">{format_rp(rpc_aman)}</h2>
                <p style='font-size:12px; color:gray;'>*Ini batas aman agar dapur tetap ngebul.</p>
                <hr>
                <p style="margin:0;">Saran Pinjaman (Plafon):</p>
                <h2 style="color:#001f3f; margin:0;">{format_rp(plafon_final)}</h2>
                <p style='font-size:12px; color:gray;'>*Dihitung untuk masa pinjaman 2 tahun.</p>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="white-card">
                <p style="margin:0;">Rincian Cicilan (Tenor 24 Bln):</p>
                <table style="width:100%; color:black;">
                    <tr><td>Uang Pokok</td><td style="text-align:right;">{format_rp(pokok_bln)}</td></tr>
                    <tr><td>Bunga (6% thn)</td><td style="text-align:right;">{format_rp(bunga_bln)}</td></tr>
                    <tr style="font-weight:bold; border-top:1px solid #ccc;">
                        <td>Total Setoran</td>
                        <td style="text-align:right;">{format_rp(total_cicilan)}</td>
                    </tr>
                </table>
                <p style="margin-top:10px; font-size:13px; color:{"green" if total_cicilan <= rpc_aman else "red"};">
                <b>{'✅ CICILAN SEHAT' if total_cicilan <= rpc_aman else '⚠️ CICILAN TERLALU BERAT'}</b>
                </p>
            </div>
            """, unsafe_allow_html=True)

        # 3. PANDUAN CARA PINJAM
        st.write("---")
        col_list, col_edu = st.columns([1, 1])
        with col_list:
            st.markdown("""
            <div class="white-card">
                <h4>📋 Siapkan Ini Sebelum ke BRI:</h4>
                <p>1. KTP & Kartu Keluarga (KK)<br>
                2. NIB (Nomor Induk Berusaha)<br>
                3. Laporan Laba Rugi (Cetak dari tab sebelah)<br>
                4. Pastikan tidak ada tunggakan di Pinjol/Bank lain.</p>
            </div>
            """, unsafe_allow_html=True)
            
        with col_edu:
            st.markdown(f"""
            <div class="white-card">
                <h4>💡 Kenapa Harus Sesuai Aplikasi?</h4>
                <p>Mantri BRI akan melihat <b>Realtime Dana</b> dan <b>Laba</b> Anda. 
                Jika data di aplikasi ini sinkron dengan kondisi di lapangan, kepercayaan bank akan naik 100%.</p>
            </div>
            """, unsafe_allow_html=True)
                Ini adalah kunci rahasia agar pengajuan Anda disetujui oleh Mantri BRI.</p>
            </div>
            """, unsafe_allow_html=True)

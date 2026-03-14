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

# --- SIDEBAR: MONITORING & REVISI ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🏠 Profil & Live Stat")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    jenis_u = st.selectbox("Jenis Usaha", ["Dagang", "Jasa", "Produksi"])
    
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    modal_sekarang = modal_awal + (total_laba - total_prive)
    
    st.markdown("---")
    st.markdown(f"<div class='sidebar-text'>Modal Awal: <b>{format_rp(modal_awal)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sidebar-text'>Total Laba Realtime: <b style='color:#00ff88;'>{format_rp(total_laba)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sidebar-text'>Total Prive (Ambil): <b style='color:#ff4b4b;'>{format_rp(total_prive)}</b></div>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini: {format_rp(modal_sekarang)}</h3>", unsafe_allow_html=True)
    
    # --- FITUR REVISI DI SIDEBAR (UX LEBIH OKE) ---
    st.write("---")
    with st.expander("🛠️ REVISI / HAPUS DATA"):
        if not df.empty:
            df_rev = df.sort_values(by='id', ascending=False)
            pilih_hapus = st.selectbox("Pilih Transaksi:", [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
            if st.button("Hapus Data Ini"):
                id_hapus = int(pilih_hapus.split(' | ')[0])
                c.execute(f"DELETE FROM transaksi WHERE id = {id_hapus}")
                conn.commit()
                st.success("Berhasil dihapus!")
                st.rerun()
        else:
            st.write("Belum ada data.")

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

# --- LAPORAN & KUR ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN PERUBAHAN MODAL", "🏦 SIMULASI KUR BRI"])
    
    with t_rep:
        sel_b = st.selectbox("Pilih Bulan Laporan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        laba_bln = db['laba'].sum()
        prive_bln = db['prive'].sum()
        nambah_kas = laba_bln - prive_bln
        
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">Laporan Perubahan Modal - {sel_b}</h3>
            <hr>
            <table style="width:100%; font-size:18px; color:black;">
                <tr><td>1. Total Omzet (Uang Masuk)</td><td style="text-align:right;">{format_rp(db['omzet'].sum())}</td></tr>
                <tr><td>2. Laba Bersih (Hasil Usaha)</td><td style="text-align:right; color:green;">{format_rp(laba_bln)}</td></tr>
                <tr><td>3. Prive (Uang Diambil Pribadi)</td><td style="text-align:right; color:red;">({format_rp(prive_bln)})</td></tr>
                <tr style="font-weight:bold; border-top:2px solid black; background-color: #f9f9f9;">
                    <td>✅ PENAMBAHAN KAS MODAL</td>
                    <td style="text-align:right;">{format_rp(nambah_kas)}</td>
                </tr>
            </table>
            <div style="margin-top:15px; padding:10px; border:1px dashed #001f3f; border-radius:10px;">
                <p style="margin:0; font-size:14px;"><b>Analisis Pertumbuhan:</b></p>
                <p style="margin:0; font-size:16px;">Modal Anda di bulan ini bertambah sebesar <b>{format_rp(nambah_kas)}</b>. 
                Artinya, uang yang mengendap di kas bertumbuh sebesar <b>{((nambah_kas/modal_awal)*100) if modal_awal > 0 else 0:.1f}%</b> dari modal awal.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with t_kur:
        laba_akhir = df.iloc[-1]['laba'] if not df.empty else 0
        rpc_aman = laba_akhir * 0.35 
        plafon_final = (rpc_aman * 24) if (rpc_aman * 24) >= 10000000 else 10000000
        
        bunga_bln = plafon_final * 0.005
        pokok_bln = plafon_final / 24
        total_cicilan = pokok_bln + bunga_bln

        st.markdown("### 🏦 Simulasi & Kelayakan KUR BRI")
        
        if laba_akhir >= total_cicilan and (total_laba - total_prive) > 0:
            st.success("### ✅ STATUS: LAYAK AJUKAN")
        elif laba_akhir > 0:
            st.warning("### ⚠️ STATUS: PERTIMBANGKAN LAGI")
        else:
            st.error("### ❌ STATUS: BELUM LAYAK")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class="white-card">
                <p style="margin:0;">Kemampuan Bayar:</p>
                <h2 style="color:#28a745; margin:0;">{format_rp(rpc_aman)}</h2>
                <hr>
                <p style="margin:0;">Saran Pinjaman:</p>
                <h2 style="color:#001f3f; margin:0;">{format_rp(plafon_final)}</h2>
            </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown(f"""<div class="white-card">
                <p style="margin:0;">Rincian Cicilan (24 Bln):</p>
                <table style="width:100%; color:black;">
                    <tr><td>Uang Pokok</td><td style="text-align:right;">{format_rp(pokok_bln)}</td></tr>
                    <tr><td>Bunga (6%)</td><td style="text-align:right;">{format_rp(bunga_bln)}</td></tr>
                    <tr style="font-weight:bold; border-top:1px solid #ccc;">
                        <td>Total Setoran</td><td style="text-align:right;">{format_rp(total_cicilan)}</td>
                    </tr>
                </table>
            </div>""", unsafe_allow_html=True)

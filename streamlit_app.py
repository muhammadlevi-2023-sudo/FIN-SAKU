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
</style>
""", unsafe_allow_html=True)

# --- LOGIKA DATA REALTIME ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
total_laba = df['laba'].sum() if not df.empty else 0
total_prive = df['prive'].sum() if not df.empty else 0

# --- SIDEBAR: MONITORING ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    jenis_u = st.selectbox("Jenis Usaha", ["Dagang", "Jasa", "Produksi"])
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal", "7000000"))
    modal_sekarang = modal_awal + (total_laba - total_prive)
    
    st.markdown("---")
    st.markdown(f"Laba Bersih: **{format_rp(total_laba)}**")
    st.markdown(f"Kas Saat Ini: <h3 style='color:#FFD700;'>{format_rp(modal_sekarang)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard: {nama_u}")

# GRID UTAMA: INPUT | REVISI | TIPS
col_in, col_rev, col_tips = st.columns([1.2, 1, 1])

with col_in:
    st.subheader("📝 Input Transaksi")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet = st.number_input("Total Omzet", value=0)
    laba_in = omzet - (omzet * (hpp_val / hrg_val)) if hrg_val > 0 else 0
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0
    if st.button("🔔 SIMPAN"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba_in, prive_in, "Harian"))
        conn.commit()
        st.rerun()

with col_rev:
    st.subheader("🛠️ Revisi Data")
    if not df.empty:
        df_rev = df.sort_values(by='id', ascending=False).head(5)
        pilih = st.selectbox("Pilih yg salah:", [f"{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
        if st.button("🗑️ Hapus"):
            c.execute(f"DELETE FROM transaksi WHERE id = {int(pilih.split(' | ')[0])}")
            conn.commit()
            st.rerun()
    else: st.info("Belum ada data")

with col_tips:
    st.subheader("💡 Tips Bank")
    st.markdown(f"""<div class="white-card" style="padding:10px; font-size:14px;">
        Prive Anda <b>{prive_pct}%</b>. BRI suka jika prive di bawah 30% agar modal usaha tetap kuat.
    </div>""", unsafe_allow_html=True)

# --- AREA LAPORAN & KUR ---
if not df.empty:
    st.write("---")
    t_rep, t_kur = st.tabs(["📊 LAPORAN PERUBAHAN MODAL", "🏦 PRODUK KUR BRI"])
    
    with t_rep:
        sel_b = st.selectbox("Pilih Bulan:", df['bulan'].unique())
        db = df[df['bulan'] == sel_b]
        l_bln, p_bln = db['laba'].sum(), db['prive'].sum()
        
        st.markdown(f"""<div class="white-card">
            <h3 style="text-align:center;">Laporan Kas - {sel_b}</h3>
            <table style="width:100%; font-size:18px; color:black;">
                <tr><td>Laba Bersih</td><td style="text-align:right; color:green;">{format_rp(l_bln)}</td></tr>
                <tr><td>Prive (Jajan)</td><td style="text-align:right; color:red;">({format_rp(p_bln)})</td></tr>
                <tr style="font-weight:bold; border-top:2px solid black;">
                    <td>✅ PENAMBAHAN KAS</td><td style="text-align:right;">{format_rp(l_bln - p_bln)}</td>
                </tr>
            </table>
            <p style="margin-top:10px; font-size:14px;">Modal bertumbuh <b>{format_rp(l_bln-p_bln)}</b> bulan ini.</p>
        </div>""", unsafe_allow_html=True)

    with t_kur:
        laba_akhir = df.iloc[-1]['laba']
        rpc_aman = laba_akhir * 0.35
        
        st.markdown(f"### 🏦 Pilihan Produk KUR sesuai Kemampuan ({format_rp(rpc_aman)}/bln)")
        
        # Simulasi 3 Produk KUR BRI
        produks = [
            {"nama": "KUR Super Mikro", "plafon": 10000000, "tenor": 12},
            {"nama": "KUR Mikro A", "plafon": 25000000, "tenor": 24},
            {"nama": "KUR Mikro B", "plafon": 50000000, "tenor": 36}
        ]
        
        cols = st.columns(3)
        for i, p in enumerate(produks):
            cicilan = (p['plafon']/p['tenor']) + (p['plafon']*0.005)
            is_aman = cicilan <= rpc_aman
            with cols[i]:
                st.markdown(f"""<div class="white-card" style="border-left-color: {'#28a745' if is_aman else '#ff4b4b'};">
                    <h4 style="margin:0;">{p['nama']}</h4>
                    <h2 style="margin:0;">{format_rp(p['plafon'])}</h2>
                    <p style="margin:0;">Tenor: {p['tenor']} Bln</p>
                    <hr>
                    <p style="margin:0;">Cicilan/bln:</p>
                    <b style="font-size:18px; color:{'green' if is_aman else 'red'};">{format_rp(cicilan)}</b>
                    <p style="font-size:12px;">{'✅ AMAN' if is_aman else '⚠️ TERLALU BERAT'}</p>
                </div>""", unsafe_allow_html=True)
        
        st.info("💡 **Mengapa ambil plafon ini?** Pilih yang berstatus ✅ AMAN agar Anda tidak kesulitan membayar dan catatan kredit di BRI tetap bersih.")

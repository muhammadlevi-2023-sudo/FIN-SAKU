import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_ultimate.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS profil 
             (id INTEGER PRIMARY KEY, nama_usaha TEXT, modal_awal REAL)''')
conn.commit()

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: UNAIR NAVY & GOLD (REFINED VERSION)
st.markdown("""
<style>
    .stApp { background-color: #003366 !important; }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] { 
        background-color: #002244 !important; 
        border-right: 3px solid #FFD700; 
    }
    .report-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #FFD700;
        margin-bottom: 20px;
    }
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700; margin-bottom: 20px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { color: #003366 !important; }
    
    /* Tabel Styling */
    table { width: 100%; border-collapse: collapse; color: white; }
    th { text-align: left; border-bottom: 2px solid #FFD700; padding: 10px; }
    td { padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); }
    
    /* Tombol Style */
    .stButton>button { 
        background-color: #FFD700 !important; color: #003366 !important; 
        font-weight: bold; border-radius: 10px; width: 100%;
    }
    .reset-btn>button { background-color: #ff4b4b !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
p_data = c.fetchone()
saved_nama = p_data[1] if p_data else "Usaha Baru"
saved_modal = p_data[2] if p_data else 0.0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", saved_nama, key="f_nama")
    modal_raw = st.text_input("Modal Awal (Rp)", value=str(int(saved_modal)), key="f_modal")
    st.markdown(f"<small>Tercatat: <b>{format_rp(clean_to_int(modal_raw))}</b></small>", unsafe_allow_html=True)
    
    if st.button("💾 SIMPAN PROFIL", key="f_btn_save"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", (nama_u, clean_to_int(modal_raw)))
        conn.commit()
        st.success("Profil Berhasil Diperbarui!")
        st.rerun()

    st.write("---")
    st.subheader("⚙️ Parameter Produk")
    hpp_raw = st.text_input("HPP/Produk", "5000", key="f_hpp")
    st.markdown(f"<small>Tercatat: <b>{format_rp(clean_to_int(hpp_raw))}</b></small>", unsafe_allow_html=True)
    
    hrg_raw = st.text_input("Harga Jual/Produk", "15000", key="f_hrg")
    st.markdown(f"<small>Tercatat: <b>{format_rp(clean_to_int(hrg_raw))}</b></small>", unsafe_allow_html=True)
    
    prive_pct = st.slider("Persentase Prive (%)", 0, 100, 30)
    
    st.write("---")
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("🗑️ RESET SEMUA DATA", key="f_btn_reset"):
        c.execute("DELETE FROM transaksi")
        c.execute("DELETE FROM profil")
        conn.commit()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard: {nama_u}")

st.markdown("""<div class="edu-box">
    <h3>🔍 Mengapa Laporan Keuangan Penting?</h3>
    <p>Bank membutuhkan data riil untuk melihat <b>Kapasitas Bayar</b> Anda. Tanpa catatan, usaha Anda dianggap berisiko tinggi.</p>
</div>""", unsafe_allow_html=True)

# --- INPUT TRANSAKSI ---
col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal", datetime.now(), key="f_date")
    qty = st.number_input("Unit Terjual", min_value=0, key="f_qty")
    if st.button("🔔 SIMPAN TRANSAKSI", key="f_btn_trx"):
        if qty > 0:
            omzet = qty * clean_to_int(hrg_raw)
            laba = qty * (clean_to_int(hrg_raw) - clean_to_int(hpp_raw))
            prive = laba * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.rerun()

# --- LAPORAN KEUANGAN ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def show_report(data_df, title):
        o, l, p = data_df['omzet'].sum(), data_df['laba'].sum(), data_df['prive'].sum()
        total_kas = clean_to_int(modal_raw) + (df['laba'].sum() - df['prive'].sum())
        
        st.markdown(f"""<div class="report-card">
            <h3 style="color:#FFD700; text-align:center;">{title}</h3>
            <table>
                <tr><td>Total Omzet (Penjualan)</td><td style="text-align:right;">{format_rp(o)}</td></tr>
                <tr><td style="color:#FFD700;">Laba Bersih</td><td style="text-align:right; color:#FFD700;">{format_rp(l)}</td></tr>
                <tr><td>Prive (Konsumsi Pribadi)</td><td style="text-align:right; color:#ff4b4b;">({format_rp(p)})</td></tr>
                <tr style="font-size:20px; font-weight:bold; background:rgba(255,215,0,0.2);">
                    <td>SALDO KAS SAAT INI</td><td style="text-align:right;">{format_rp(total_kas)}</td>
                </tr>
            </table>
        </div>""", unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Filter Hari", datetime.now())
        show_report(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan {sel_t.strftime('%d/%b/%Y')}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique())
        show_report(df[df['bulan'] == sel_b], f"Laporan Bulanan: {sel_b}")

    with t_kur:
        # LOGIKA KUR
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        rpc = avg_laba * 0.35 # Batas cicilan aman (35% dari laba)
        plafon_est = rpc * 22  # Estimasi plafon tenor 2 tahun
        
        st.subheader("🏦 Analisis Kelayakan KUR")
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Rata-rata Laba/Bulan", format_rp(avg_laba))
        with col_b:
            st.metric("Kapasitas Cicilan Aman", format_rp(rpc))

        st.markdown(f"""<div class="report-card" style="border: 2px solid #FFD700;">
            <p style="margin:0;">Estimasi Plafon Pinjaman:</p>
            <h1 style="color:#FFD700; margin:0;">{format_rp(plafon_est)}</h1>
        </div>""", unsafe_allow_html=True)

        if plafon_est >= 5000000:
            st.success("✅ STATUS: BANKABLE (LAYAK KUR)")
            st.write("Usaha Anda memiliki kapasitas yang cukup untuk mengajukan KUR Mikro.")
        else:
            st.error("⚠️ STATUS: BELUM LAYAK KUR")
            kekurangan = 5000000 - plafon_est
            target_laba_tambahan = (kekurangan / 22) / 0.35
            st.markdown(f"""
            <div style="background:rgba(255,75,75,0.1); padding:15px; border-radius:10px;">
                <p>Pinjaman minimal Bank biasanya <b>Rp 5.000.000</b>.</p>
                <p>Anda kurang <b>{format_rp(kekurangan)}</b> dari batas minimal plafon.</p>
                <hr>
                <p>💡 <b>Target:</b> Anda perlu meningkatkan laba bersih rata-rata sebesar 
                <b>{format_rp(target_laba_tambahan)}</b> lagi per bulan agar layak KUR.</p>
            </div>
            """, unsafe_allow_html=True)

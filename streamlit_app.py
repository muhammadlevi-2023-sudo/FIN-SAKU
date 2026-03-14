import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# 1. KONFIGURASI HALAMAN UTAMA
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_final_v4.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS transaksi 
             (id INTEGER PRIMARY KEY, tanggal TEXT, bulan TEXT, minggu TEXT, 
              omzet REAL, laba REAL, prive REAL)''')
c.execute('''CREATE TABLE IF NOT EXISTS profil 
             (id INTEGER PRIMARY KEY, nama_usaha TEXT, modal_awal REAL)''')
conn.commit()

# --- FUNGSI FORMAT RUPIAH ---
def format_rp(angka):
    try:
        return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except:
        return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: UNAIR NAVY & GOLD (Anti-Nyaru & Anti-Error)
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
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 15px; 
        border-left: 10px solid #FFD700; 
        margin-bottom: 25px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { 
        color: #003366 !important; 
        font-weight: bold !important;
    }
    button[data-baseweb="tab"] p { 
        color: #FFD700 !important; 
        font-weight: 800 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] { 
        background-color: #FFD700 !important; 
    }
    button[data-baseweb="tab"][aria-selected="true"] p { 
        color: #003366 !important; 
    }
    .stButton>button { 
        background-color: #FFD700 !important; 
        color: #003366 !important; 
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA PROFIL ---
c.execute("SELECT * FROM profil WHERE id=1")
p_data = c.fetchone()
saved_nama = p_data[1] if p_data else "Usaha Baru"
saved_modal = p_data[2] if p_data else 0.0

# --- SIDEBAR: KONFIGURASI USAHA ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.subheader("🏠 Profil Usaha")
    nama_u = st.text_input("Nama Usaha", saved_nama, key="unique_nama_u")
    
    modal_raw = st.text_input("Modal Kas Awal (Rp)", value=str(int(saved_modal)), key="unique_modal_u")
    st.info(f"Tercatat: {format_rp(clean_to_int(modal_raw))}") # Fitur pembaca format angka
    
    if st.button("💾 SIMPAN PROFIL", key="btn_save_profil"):
        c.execute("INSERT OR REPLACE INTO profil (id, nama_usaha, modal_awal) VALUES (1, ?, ?)", 
                  (nama_u, clean_to_int(modal_raw)))
        conn.commit()
        st.success("Profil Disimpan!")
        st.rerun()

    st.write("---")
    st.subheader("⚙️ Setting Produk")
    hpp_val = st.text_input("HPP Produk (Rp)", "5000", key="unique_hpp")
    st.caption(f"Format: {format_rp(clean_to_int(hpp_val))}")
    
    harga_val = st.text_input("Harga Jual (Rp)", "15000", key="unique_harga")
    st.caption(f"Format: {format_rp(clean_to_int(harga_val))}")
    
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30, key="unique_prive")
    
    if st.button("🗑️ RESET SEMUA DATA", key="btn_reset"):
        c.execute("DELETE FROM transaksi")
        conn.commit()
        st.rerun()

# --- HALAMAN UTAMA ---
st.title(f"Pusat Data KUR: {nama_u}")

st.markdown(f"""
<div class="edu-box">
    <h3>🔍 Mengapa FIN-Saku Membuat UMKM Bankable?</h3>
    <p>Bank melihat 3 kriteria utama dari data yang Anda masukkan:</p>
    <ul>
        <li><b>Karakter:</b> Kedisiplinan Anda mencatat transaksi harian.</li>
        <li><b>Kapasitas:</b> Laba bersih bulanan untuk membayar cicilan.</li>
        <li><b>Modal:</b> Pemisahan uang pribadi (Prive) untuk menjaga kas usaha.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# --- INPUT TRANSAKSI ---
col_catat, _ = st.columns([1, 1.2])
with col_catat:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal Transaksi", datetime.now(), key="unique_date")
    qty = st.number_input("Jumlah Unit Terjual", min_value=0, key="unique_qty")
    
    if st.button("🔔 SIMPAN TRANSAKSI", key="btn_trx"):
        if qty > 0:
            omzet = qty * clean_to_int(harga_val)
            laba = qty * (clean_to_int(harga_val) - clean_to_int(hpp_val))
            prive = laba * (prive_pct / 100)
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive) VALUES (?, ?, ?, ?, ?, ?)",
                      (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet, laba, prive))
            conn.commit()
            st.rerun()

# --- LAPORAN & KUR ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
if not df.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def render_data(filtered_df, judul):
        o, l, p = filtered_df['omzet'].sum(), filtered_df['laba'].sum(), filtered_df['prive'].sum()
        total_kas_skrg = clean_to_int(modal_raw) + (df['laba'].sum() - df['prive'].sum())
        st.markdown(f"""
        <div style="border: 2px solid #FFD700; padding: 25px; border-radius: 12px; background: rgba(255,255,255,0.05);">
            <h3 style='text-align:center; color:#FFD700;'>{judul}</h3>
            <hr>
            <p>Total Omzet: <b>{format_rp(o)}</b></p>
            <p style="color:#FFD700;">Laba Bersih: <b>{format_rp(l)}</b></p>
            <p style="color:#ff4b4b;">Prive (Diambil): <b>({format_rp(p)})</b></p>
            <h2 style="text-align:center; background:#FFD700; color:#003366; padding:10px; border-radius:8px;">
                SALDO KAS: {format_rp(total_kas_skrg)}
            </h2>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        sel_t = st.date_input("Pilih Hari", datetime.now(), key="filter_harian")
        render_data(df[df['tanggal'] == sel_t.strftime("%Y-%m-%d")], f"Laporan Hari {sel_t.strftime('%d/%m/%Y')}")

    with t_min:
        sel_m = st.selectbox("Pilih Minggu", df['minggu'].unique(), key="filter_minggu")
        render_data(df[df['minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", df['bulan'].unique(), key="filter_bulan")
        render_data(df[df['bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        # LOGIKA ANALISIS KUR
        avg_laba = df.groupby('bulan')['laba'].sum().mean()
        rpc = avg_laba * 0.35 # Batas cicilan aman 35% laba
        plafon = rpc * 22     # Estimasi plafon tenor 2 tahun
        
        if plafon >= 5000000:
            st.success(f"STATUS: ✅ BANKABLE (LAYAK KUR)")
            st.markdown(f"""<div style="background:#FFD700; color:#003366; padding:20px; border-radius:15px;">
            <h3>Estimasi Plafon: {format_rp(plafon)}</h3>
            <p>Cicilan Aman Maksimal: <b>{format_rp(rpc)}/bulan</b></p>
            </div>""", unsafe_allow_html=True)
        else:
            st.error("STATUS: ⚠️ BELUM LAYAK KUR")
            st.info("Saran: Kurangi persentase Prive atau tingkatkan omzet untuk memperbesar kapasitas bayar (RPC).")

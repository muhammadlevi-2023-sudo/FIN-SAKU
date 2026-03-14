import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. INITIAL SETUP
st.set_page_config(page_title="FIN-Saku | UMKM Bankable Dashboard", layout="wide")

# Database Management (Auto-Migration)
def get_connection():
    conn = sqlite3.connect('finsaku_final_v15.db', check_same_thread=False)
    c = conn.cursor()
    # Pastikan tabel memiliki kolom yang lengkap sesuai kode terbaru
    c.execute('''CREATE TABLE IF NOT EXISTS transaksi
                 (id INTEGER PRIMARY KEY, periode_bln TEXT, periode_thn TEXT, 
                  omzet REAL, laba REAL, prive REAL, hpp REAL, harga_jual REAL)''')
    conn.commit()
    return conn

conn = get_connection()

# 2. UI STYLING (UNAIR NAVY & GOLD)
st.markdown("""
<style>
    /* Base Colors */
    .stApp { background-color: #002147; color: #FFFFFF; }
    section[data-testid="stSidebar"] { 
        background-color: #001a35 !important; 
        border-right: 3px solid #FFD700; 
    }
    
    /* Typography */
    h1, h2, h3, p, label, .stMarkdown { color: #FFFFFF !important; }
    .gold-label { color: #FFD700 !important; font-weight: bold; font-size: 1.1rem; }
    
    /* Modern Card */
    .report-card {
        background: #FFFFFF; padding: 25px; border-radius: 15px;
        border-top: 8px solid #FFD700; color: #002147 !important;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4); margin-bottom: 20px;
    }
    .report-card span, .report-card b, .report-card h3 { color: #002147 !important; }

    /* Button Styling */
    .stButton>button {
        background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%) !important;
        color: #002147 !important; font-weight: bold; border-radius: 8px;
        border: none; height: 50px; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 5px 15px rgba(255,215,0,0.3); }
</style>
""", unsafe_allow_html=True)

# 3. HELPER FUNCTIONS
def format_rp(angka):
    return f"Rp {int(angka):,}".replace(",", ".")

def clean_val(teks):
    return int("".join(filter(str.isdigit, str(teks)))) if teks else 0

# 4. SIDEBAR: PROFIL & KAS REALTIME
df_all = pd.read_sql_query("SELECT * FROM transaksi", conn)

with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    
    nama_usaha = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    kas_awal = st.number_input("Modal Kas Awal (Rp)", value=7000000, step=100000)
    st.markdown(f"Tercatat: <span class='gold-label'>{format_rp(kas_awal)}</span>", unsafe_allow_html=True)
    
    # Perhitungan Kas Realtime yang Akurat
    untung_bersih = (df_all['laba'].sum() - df_all['prive'].sum()) if not df_all.empty else 0
    kas_sekarang = kas_awal + untung_bersih
    
    st.markdown(f"""
    <div style='background:#003366; padding:15px; border-radius:10px; border-left:5px solid #FFD700; margin-top:20px;'>
        <p style='margin:0; font-size:12px; color:#FFD700;'>KAS SAAT INI (REALTIME)</p>
        <h2 style='margin:0;'>{format_rp(kas_sekarang)}</h2>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("Aturan Harga & Margin")
    val_hpp = st.number_input("HPP Produk", value=5000)
    val_jual = st.number_input("Harga Jual", value=15000)
    margin = ((val_jual - val_hpp) / val_jual * 100) if val_jual > 0 else 0
    st.markdown(f"Margin: <span class='gold-label'>{margin:.1f}%</span>", unsafe_allow_html=True)
    
    prive_pct = st.slider("Alokasi Prive Pemilik (%)", 0, 100, 30)

# 5. DASHBOARD: PENCATATAN BULANAN
st.title(f"🚀 Dashboard Strategis: {nama_usaha}")

with st.container():
    st.subheader("📝 Input Transaksi Periode")
    c1, c2, c3 = st.columns([2, 2, 1])
    
    with c1:
        # Picker Bulan & Tahun
        list_bln = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        sel_bln = st.selectbox("Pilih Bulan", list_bln, index=datetime.now().month - 1)
        sel_thn = st.selectbox("Pilih Tahun", ["2024", "2025", "2026", "2027"])
        
    with c2:
        omzet_raw = st.text_input("Total Omzet Periode Ini (Angka Saja)")
        omzet_in = clean_val(omzet_raw)
        st.markdown(f"Tercatat: <span class='gold-label'>{format_rp(omzet_in)}</span>", unsafe_allow_html=True)
        
    with c3:
        st.write("##")
        if st.button("SIMPAN DATA"):
            laba_in = omzet_in * (margin/100)
            prive_in = laba_in * (prive_pct/100)
            cur = conn.cursor()
            cur.execute("INSERT INTO transaksi (periode_bln, periode_thn, omzet, laba, prive, hpp, harga_jual) VALUES (?,?,?,?,?,?,?)",
                      (sel_bln, sel_thn, omzet_in, laba_in, prive_in, val_hpp, val_jual))
            conn.commit()
            st.toast("Transaksi Berhasil Dicatat!")
            st.rerun()

# 6. TABEL LAPORAN & ANALISIS KUR
if not df_all.empty:
    st.write("---")
    t1, t2, t3 = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "⚙️ REVISI DATA"])
    
    with t1:
        f_bln = st.select_slider("Lihat Laporan Bulan:", options=list_bln)
        df_view = df_all[df_all['periode_bln'] == f_bln]
        
        if not df_view.empty:
            o_t = df_view['omzet'].sum(); l_t = df_view['laba'].sum(); p_t = df_view['prive'].sum()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"""
                <div class="report-card">
                    <h3>LABA RUGI - {f_bln.upper()}</h3>
                    <hr>
                    <div style="display:flex; justify-content:space-between;"><span>Omzet</span><b>{format_rp(o_t)}</b></div>
                    <div style="display:flex; justify-content:space-between;"><span>Laba Kotor</span><b>{format_rp(l_t)}</b></div>
                    <div style="display:flex; justify-content:space-between; color:red;"><span>Prive</span><b>-{format_rp(p_t)}</b></div>
                    <hr>
                    <div style="display:flex; justify-content:space-between;"><b>LABA BERSIH</b><b style="color:green;">{format_rp(l_t - p_t)}</b></div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div class="report-card">
                    <h3>POSISI KAS - {f_bln.upper()}</h3>
                    <hr>
                    <p>Kas Awal: <b>{format_rp(kas_sekarang - (l_t - p_t))}</b></p>
                    <p>Penambahan Kas: <b>{format_rp(l_t - p_t)}</b></p>
                    <hr>
                    <p>Total Kas Akhir:</p>
                    <h2 style="color:#002147;">{format_rp(kas_sekarang)}</h2>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning(f"Data untuk bulan {f_bln} tidak ditemukan.")

    with t2:
        st.subheader("🏦 Skor Kredit & Rekomendasi KUR")
        histori = df_all['periode_bln'].nunique()
        
        # Logika KUR BRI Super Mikro vs Mikro
        if kas_sekarang < 15000000:
            produk = "KUR SUPER MIKRO BRI"; plafon = "Maks Rp 10.000.000"
        else:
            produk = "KUR MIKRO BRI"; plafon = "Rp 10.000.000 - Rp 50.000.000"
            
        st.markdown(f"""
        <div class="report-card">
            <h4>Rekomendasi Produk: <span style="color:#002147;">{produk}</span></h4>
            <p>Potensi Plafon: <b>{plafon}</b></p>
            <p>Status Kelayakan: <b>{"✅ LAYAK" if histori >= 3 else "⚠️ BUTUH DATA 3 BULAN"}</b></p>
            <hr>
            <b>Analisis Cashflow:</b> Pendapatan anda konsisten di angka {format_rp(df_all['omzet'].mean())}. 
            Disarankan mengambil cicilan tidak lebih dari {format_rp(df_all['laba'].mean() * 0.3)} / bulan.
        </div>
        """, unsafe_allow_html=True)

    with t3:
        st.subheader("Koreksi Transaksi")
        st.dataframe(df_all[['id', 'periode_bln', 'periode_thn', 'omzet', 'laba']], use_container_width=True)
        target_id = st.number_input("Masukkan ID Transaksi yang ingin dihapus", step=1)
        if st.button("HAPUS DATA"):
            c.execute("DELETE FROM transaksi WHERE id=?", (target_id,))
            conn.commit()
            st.rerun()

else:
    st.info("Silakan masukkan data omzet bulanan Anda untuk memulai analisis.")

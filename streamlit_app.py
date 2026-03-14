import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman Dasar
st.set_page_config(page_title="FIN-Saku: Solusi KUR Digital", layout="wide")

# Inisialisasi Database Sesi
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def play_cash_sound():
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD (WARNA TERKUNCI MATI)
st.markdown("""
<style>
    /* Paksa Background Aplikasi Terang & Teks Gelap agar Terlihat Jelas */
    .stApp, .stApp * { color: #001f3f !important; }

    /* Khusus Sidebar Tetap Navy & Teks Putih */
    [data-testid="stSidebar"], [data-testid="stSidebar"] * { 
        background-color: #001f3f !important; 
        color: #ffffff !important; 
    }

    /* Box Edukasi Kuning - Kunci Teks Hitam Tajam */
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 12px; 
        border-left: 10px solid #FFD700; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .edu-box * { color: #001f3f !important; }

    /* Tab Fix - Paksa Teks Muncul (Harian, Bulanan, dll) */
    button[data-baseweb="tab"] * { color: #001f3f !important; font-weight: bold !important; }

    /* Laporan Biru (Report Card) */
    .report-card { 
        background-color: #dbeafe !important; padding: 25px; 
        border-radius: 10px; border: 2px solid #001f3f; 
    }

    /* Kartu KUR (Navy-Gold) */
    .kur-card { 
        background-color: #001f3f !important; padding: 30px; 
        border-radius: 15px; border: 2px solid #FFD700;
    }
    .kur-card * { color: #FFD700 !important; }

    /* Tombol Gold */
    .stButton>button { 
        background-color: #FFD700 !important; color: #001f3f !important; 
        font-weight: bold; border-radius: 8px; border: none; height: 3.5em; width: 100%;
    }
    .step-tag { background-color: #FFD700; color: #001f3f; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: PENGATURAN USAHA ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_usaha = st.text_input("Nama Usaha", "PT Enggan Mundur")
    
    st.markdown("<span class='step-tag'>STEP 1</span> **Modal & Kas**", unsafe_allow_html=True)
    m_raw = st.text_input("Uang Kas Awal (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.info(f"Tercatat: {format_rp(st.session_state.modal_awal)}")

    st.write("---")
    st.markdown("<span class='step-tag'>STEP 2</span> **Setting Produk**", unsafe_allow_html=True)
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Ambil Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Pusat Data KUR: {nama_usaha}")

st.markdown(f"""
<div class="edu-box">
    <h3>🔍 Mengapa Aplikasi Ini Membuat UMKM Bankable?</h3>
    <p>Bank BRI melihat 3 kriteria utama dari data yang Anda masukkan:</p>
    <ul>
        <li><b>Karakter:</b> Kedisiplinan Anda mencatat transaksi harian.</li>
        <li><b>Kapasitas:</b> Laba bersih bulanan untuk membayar cicilan.</li>
        <li><b>Modal:</b> Pemisahan uang pribadi (Prive) untuk menjaga kas usaha.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col_in, _ = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal Transaksi", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        v_hpp, v_harga = clean_to_int(hpp_raw), clean_to_int(harga_raw)
        if qty > 0:
            omzet = qty * v_harga
            laba = qty * (v_harga - v_hpp)
            prive = laba * (prive_pct / 100)
            
            new_row = pd.DataFrame([{
                "Tanggal": tgl, "Bulan": tgl.strftime("%B %Y"), 
                "Minggu": f"Minggu {tgl.isocalendar()[1]}", 
                "Omzet": omzet, "Laba": laba, "Prive": prive
            }])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_row], ignore_index=True)
            play_cash_sound()
            st.success("Data Tersimpan!")

# --- LAPORAN & ANALISIS ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    def render_report(df, title):
        omz, lb, prv = df['Omzet'].sum(), df['Laba'].sum(), df['Prive'].sum()
        modal_berjalan = st.session_state.modal_awal + (st.session_state.db_transaksi['Laba'].sum() - st.session_state.db_transaksi['Prive'].sum())
        
        st.markdown(f"""
        <div class="report-card">
            <h3 style='text-align:center;'>{nama_usaha}</h3>
            <p style='text-align:center;'><b>{title}</b></p>
            <table style="width:100%; border-collapse: collapse; font-size:18px;">
                <tr style="border-bottom: 2px solid #001f3f;"><td>Pendapatan Usaha</td><td style="text-align:right;">{format_rp(omz)}</td></tr>
                <tr style="border-bottom: 2px solid #001f3f; font-weight:bold;"><td>LABA BERSIH</td><td style="text-align:right;">{format_rp(lb)}</td></tr>
                <tr style="color:#b91c1c;"><td>Ambil Pribadi (Prive)</td><td style="text-align:right;">({format_rp(prv)})</td></tr>
                <tr style="background-color:#FFD700; font-weight:bold; font-size:20px;">
                    <td style="padding:15px;">TOTAL MODAL BERJALAN</td><td style="text-align:right;">{format_rp(modal_berjalan)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        # Menampilkan data hari ini
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == datetime.now().date()]
        if not df_h.empty: render_report(df_h, "Laporan Hari Ini")
        else: st.info("Belum ada transaksi hari ini.")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", st.session_state.db_transaksi['Bulan'].unique())
        render_report(st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b], f"Laporan {sel_b}")

    with t_kur:
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        rpc = avg_laba * 0.35
        plafon = rpc * 22

        st.markdown(f"""
        <div class="kur-card">
            <h2 style='margin-top:0;'>🏦 Analisis Kelayakan Kredit</h2>
            <p>Berdasarkan <b>Repayment Capacity (RPC)</b>:</p>
            <table style="width:100%; font-size:18px;">
                <tr><td>Rata-rata Laba Bersih</td><td style="text-align:right;">{format_rp(avg_laba)}</td></tr>

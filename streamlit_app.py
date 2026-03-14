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
    try:
        return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except:
        return "Rp 0"

def play_cash_sound():
    # Fitur suara koin saat simpan data
    sound_url = "https://www.soundjay.com/misc/sounds/coins-spilled-1.mp3"
    st.components.v1.html(f'<audio autoplay><source src="{sound_url}" type="audio/mp3"></audio>', height=0)

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD (Hard-Locked for All Device Themes)
st.markdown("""
<style>
    /* 1. PAKSA BACKGROUND GELAP UNTUK SELURUH APLIKASI */
    .stApp {
        background-color: #001220 !important; /* Navy Super Gelap */
    }

    /* 2. KUNCI WARNA TEKS UTAMA JADI PUTIH/GOLD */
    .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp li, .stApp span, .stApp label {
        color: #ffffff !important;
    }

    /* 3. SIDEBAR (Navy Original) */
    [data-testid="stSidebar"] {
        background-color: #001f3f !important;
        border-right: 2px solid #FFD700;
    }

    /* 4. BOX EDUKASI (Putih agar menonjol, tapi teks tetap Navy Gelap agar terbaca) */
    .edu-box { 
        background-color: #ffffff !important; 
        padding: 25px; border-radius: 12px; 
        border-left: 10px solid #FFD700; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 25px;
    }
    .edu-box h3, .edu-box p, .edu-box li, .edu-box b { 
        color: #001f3f !important; /* Teks di dalam box putih harus gelap */
    }

    /* 5. TAB (Harian, Bulanan, dll) */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] p {
        color: #FFD700 !important; /* Warna Gold agar terlihat di background gelap */
        font-weight: bold !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        border-bottom-color: #FFD700 !important;
    }

    /* 6. LAPORAN BIRU (Tetap Biru Muda, tapi teks Navy) */
    .report-card { 
        background-color: #dbeafe !important; 
        padding: 30px; border-radius: 10px; 
        border: 2px solid #FFD700; 
        margin-bottom: 20px;
    }
    .report-card h3, .report-card p, .report-card table, .report-card tr, .report-card td {
        color: #001f3f !important;
    }

    /* 7. KARTU KUR (Navy-Gold) */
    .kur-card { 
        background-color: #001f3f !important; 
        padding: 30px; border-radius: 15px; 
        border: 2px solid #FFD700;
        box-shadow: 0 8px 16px rgba(0,0,0,0.5);
    }
    .kur-card h2, .kur-card p, .kur-card td {
        color: #FFD700 !important;
    }

    /* 8. INPUT FIELD (Agar kotak ketik tidak putih polos) */
    .stTextInput input, .stNumberInput input {
        background-color: #001f3f !important;
        color: #ffffff !important;
        border: 1px solid #FFD700 !important;
    }
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
    st.warning(f"Tercatat: {format_rp(st.session_state.modal_awal)}")

    st.write("---")
    st.markdown("<span class='step-tag'>STEP 2</span> **Setting Produk**", unsafe_allow_html=True)
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Ambil Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Pusat Data KUR: {nama_usaha}")

# KOTAK EDUKASI (Teks dipaksa Navy Gelap agar terlihat jelas)
st.markdown(f"""
<div class="edu-box">
    <h3>🔍 Mengapa Aplikasi Ini Membuat UMKM Bankable?</h3>
    <p>Bank BRI melihat 3 kriteria utama dari data yang Anda masukkan:</p>
    <ul>
        <li><b>Karakter:</b> Kedisiplinan Anda mencatat transaksi harian.</li>
        <li><b>Kapasitas (Capacity):</b> Laba bersih bulanan untuk membayar cicilan.</li>
        <li><b>Modal (Capital):</b> Pemisahan uang pribadi (Prive) untuk menjaga kas usaha.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col_in, col_space = st.columns([1, 1.2])
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

# --- LAPORAN & ANALISIS (LENGKAP) ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    t_har, t_min, t_bul, t_kur = st.tabs(["📆 HARIAN", "📅 MINGGUAN", "🗓️ BULANAN", "🏦 ANALISIS KUR"])

    # Template Laporan Biru (Gaya PT Enggan Mundur)
    def render_report(df, title):
        omz, lb, prv = df['Omzet'].sum(), df['Laba'].sum(), df['Prive'].sum()
        modal_berjalan = st.session_state.modal_awal + (st.session_state.db_transaksi['Laba'].sum() - st.session_state.db_transaksi['Prive'].sum())
        
        st.markdown(f"""
        <div class="report-card">
            <h3 style='text-align:center; margin:0;'>{nama_usaha}</h3>
            <p style='text-align:center;'><b>{title}</b></p>
            <table style="width:100%; border-collapse: collapse; font-size:18px; color:#001f3f;">
                <tr style="border-bottom: 2px solid #001f3f;"><td>Pendapatan Usaha</td><td style="text-align:right;">{format_rp(omz)}</td></tr>
                <tr><td>Beban Pokok (HPP)</td><td style="text-align:right;">({format_rp(omz - lb)})</td></tr>
                <tr style="border-bottom: 2px solid #001f3f; font-weight:bold;"><td>LABA BERSIH</td><td style="text-align:right;">{format_rp(lb)}</td></tr>
                <tr style="color:#b91c1c;"><td>Ambil Pribadi (Prive)</td><td style="text-align:right;">({format_rp(prv)})</td></tr>
                <tr style="background-color:#FFD700; font-weight:bold; font-size:20px;">
                    <td style="padding:15px;">TOTAL MODAL BERJALAN</td><td style="text-align:right;">{format_rp(modal_berjalan)}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t_har:
        sel_tgl = st.date_input("Filter Hari", datetime.now())
        df_h = st.session_state.db_transaksi[st.session_state.db_transaksi['Tanggal'] == sel_tgl]
        if not df_h.empty: render_report(df_h, f"Laporan Harian - {sel_tgl.strftime('%d/%m/%Y')}")
        else: st.info("Pilih tanggal transaksi.")

    with t_min:
        sel_m = st.selectbox("Pilih Minggu", st.session_state.db_transaksi['Minggu'].unique())
        render_report(st.session_state.db_transaksi[st.session_state.db_transaksi['Minggu'] == sel_m], f"Laporan {sel_m}")

    with t_bul:
        sel_b = st.selectbox("Pilih Bulan", st.session_state.db_transaksi['Bulan'].unique())
        render_report(st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b], f"Laporan Bulanan - {sel_b}")
        
    with t_kur:
        # Perhitungan Profesional
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        
        # Standar Perbankan (RPC 35%)
        rpc = avg_laba * 0.35 
        
        # Estimasi Plafon (Tenor 24 Bulan, Bunga 6% KUR)
        # Rumus cepat: Plafon = rpc * 22 (asumsi faktor bunga)
        plafon_estimasi = rpc * 22 

        st.markdown(f"""
        <div class="kur-card">
            <h2 style='margin-top:0; color:#FFD700;'>🏦 Analisis Kelayakan Kredit (Bankable)</h2>
            <p style='font-size:16px;'>Berdasarkan <b>Repayment Capacity (RPC)</b>, berikut analisis kami:</p>
            <table style="width:100%; font-size:18px; color:#FFD700;">
                <tr>
                    <td>Rata-rata Laba Bersih</td>
                    <td style="text-align:right; color:white;">{format_rp(avg_laba)}</td>
                </tr>
                <tr>
                    <td>Batas Aman Cicilan (35% Laba)</td>
                    <td style="text-align:right; color:white;">{format_rp(rpc)} /bulan</td>
                </tr>
                <tr style="font-size:28px; font-weight:bold;">
                    <td>REKOMENDASI PINJAMAN</td>
                    <td style="text-align:right;">{format_rp(plafon_estimasi)}</td>
                </tr>
            </table>
            <div style="background-color:rgba(255,255,255,0.1); padding:15px; border-radius:8px; margin-top:15px;">
                <p style="font-size:14px; margin:0; color:white;">
                <b>💡 Mengapa Angka Ini?</b><br>
                Pinjaman ini didasarkan pada aturan perbankan agar cicilan tidak mengganggu operasional usaha Anda. 
                Dengan laba {format_rp(avg_laba)}, Anda dianggap aman mencicil maksimal {format_rp(rpc)} per bulan.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

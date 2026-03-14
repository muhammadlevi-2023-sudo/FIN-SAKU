import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman Dasar
st.set_page_config(page_title="FIN-Saku: Bankable KUR", layout="wide")

# Inisialisasi Database agar data tidak hilang saat refresh (Sesi)
if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI HELPER ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: NAVY & GOLD (Professional Finance)
st.markdown("""
<style>
    .stApp { background-color: #fcfcfc; }
    [data-testid="stSidebar"] { background-color: #001f3f; color: white; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #f0f0f0; }
    
    .edu-box { 
        background-color: #ffffff; padding: 20px; border-radius: 10px; 
        border-left: 8px solid #FFD700; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .report-card { 
        background-color: #dbeafe; padding: 25px; border-radius: 10px; 
        color: #001f3f; border: 1.5px solid #001f3f; 
    }
    .kur-card { 
        background-color: #001f3f; color: #FFD700; padding: 25px; 
        border-radius: 12px; border: 2px solid #FFD700;
    }
    .stButton>button { 
        background-color: #FFD700; color: #001f3f; font-weight: bold; border: none; height: 3em;
    }
    .step-tag { background-color: #FFD700; color: #001f3f; padding: 2px 6px; border-radius: 4px; font-weight: bold; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: INPUT ---
with st.sidebar:
    st.markdown("<h1 style='color:#FFD700; text-align:center;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_usaha = st.text_input("Nama Usaha", "PT Enggan Mundur")
    
    st.markdown("<span class='step-tag'>1</span> **Modal Awal**", unsafe_allow_html=True)
    m_raw = st.text_input("Uang Kas Saat Ini (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.caption(f"Tercatat: **{format_rp(st.session_state.modal_awal)}**")

    st.write("---")
    st.markdown("<span class='step-tag'>2</span> **Setting Produk**", unsafe_allow_html=True)
    hpp_raw = st.text_input("HPP Produk (Rp)", "5000")
    harga_raw = st.text_input("Harga Jual (Rp)", "15000")
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.title(f"Analisis Keuangan: {nama_usaha}")

# EDUKASI UNTUK ORANG AWAM
st.markdown("""
<div class="edu-box">
    <h3>💡 Kenapa Laporan Ini Membuat Anda Layak Dapat KUR BRI?</h3>
    <p>Bank tidak hanya melihat saldo, tapi melihat <b>3 Syarat Utama:</b></p>
    <ul>
        <li><b>Karakter:</b> Anda rajin mencatat tiap ada penjualan.</li>
        <li><b>Kapasitas:</b> Laba bersih Anda cukup untuk membayar cicilan bulanan.</li>
        <li><b>Modal:</b> Anda disiplin memisahkan uang pribadi (Prive) agar modal usaha tidak habis.</li>
    </ul>
</div>
""", unsafe_allow_html=True)

col_in, col_space = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Catat Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah Unit Terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN TRANSAKSI"):
        v_hpp, v_harga = clean_to_int(hpp_raw), clean_to_int(harga_raw)
        if qty > 0:
            omzet = qty * v_harga
            laba = qty * (v_harga - v_hpp)
            prive = laba * (prive_pct / 100)
            new_row = pd.DataFrame([{"Tanggal": tgl, "Bulan": tgl.strftime("%B %Y"), "Minggu": f"Minggu {tgl.isocalendar()[1]}", "Omzet": omzet, "Laba": laba, "Prive": prive}])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_row], ignore_index=True)
            st.success("Berhasil dicatat ke database!")

# --- LAPORAN & KUR ---
if not st.session_state.db_transaksi.empty:
    st.write("---")
    t1, t2 = st.tabs(["📊 Laporan Bulanan (SAK-EMKM)", "🏦 Kelayakan KUR BRI"])
    
    with t1:
        sel_b = st.selectbox("Pilih Bulan", st.session_state.db_transaksi['Bulan'].unique())
        df_b = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b]
        
        st.markdown(f"""
        <div class="report-card">
            <h3 style='text-align:center; margin:0;'>{nama_usaha}</h3>
            <p style='text-align:center;'>Laporan Laba Rugi - {sel_b}</p>
            <hr style='border: 0.5px solid #001f3f;'>
            <table style="width:100%; border-collapse: collapse; font-size:17px;">
                <tr><td>Pendapatan Usaha</td><td style="text-align:right;">{format_rp(df_b['Omzet'].sum())}</td></tr>
                <tr style="border-bottom: 1px solid #001f3f;"><td>Beban Pokok (HPP)</td><td style="text-align:right;">({format_rp(df_b['Omzet'].sum() - df_b['Laba'].sum())})</td></tr>
                <tr style="font-weight:bold;"><td>LABA BERSIH</td><td style="text-align:right;">{format_rp(df_b['Laba'].sum())}</td></tr>
                <tr style="color:#b91c1c;"><td>Ambil Pribadi (Prive)</td><td style="text-align:right;">({format_rp(df_b['Prive'].sum())})</td></tr>
                <tr style="background-color:#FFD700; font-weight:bold;">
                    <td style="padding:10px;">TOTAL MODAL BERJALAN</td><td style="text-align:right;">{format_rp(st.session_state.modal_awal + (df_b['Laba'].sum() - df_b['Prive'].sum()))}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with t2:
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        rpc = avg_laba * 0.35 
        plafon = rpc / ((1/12) + 0.005) 
        
        st.markdown(f"""
        <div class="kur-card">
            <h2 style='color:#FFD700; margin-top:0;'>Analisis Kelayakan KUR BRI</h2>
            <table style="width:100%; font-size:18px;">
                <tr><td>Kemampuan Bayar (RPC)</td><td style="text-align:right;">{format_rp(rpc)} /bulan</td></tr>
                <tr style="font-size:28px; font-weight:bold; color:#FFD700;">
                    <td>ESTIMASI PLAFON KUR</td><td style="text-align:right;">{format_rp(plafon)}</td>
                </tr>
            </table>
            <p style="font-size:12px; margin-top:15px;">*Data ini adalah simulasi berdasarkan suku bunga KUR 6% per tahun.</p>
        </div>
        """, unsafe_allow_html=True)

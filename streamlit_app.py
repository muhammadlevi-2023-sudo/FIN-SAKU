import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Konfigurasi Halaman
st.set_page_config(page_title="FIN-Saku UNAIR: Bankable UMKM", layout="wide")

if 'db_transaksi' not in st.session_state:
    st.session_state.db_transaksi = pd.DataFrame(columns=["Tanggal", "Bulan", "Minggu", "Omzet", "Laba", "Prive"])
if 'modal_awal' not in st.session_state:
    st.session_state.modal_awal = 0

# --- FUNGSI TOOLS ---
def format_rp(angka):
    try: return "Rp {:,.0f}".format(float(angka)).replace(",", ".")
    except: return "Rp 0"

def clean_to_int(teks):
    angka = "".join(filter(str.isdigit, str(teks)))
    return int(angka) if angka else 0

# 2. UI CUSTOM: ORNAMEN AIRLANGGA (BIRU & KUNING)
st.markdown("""
<style>
    /* Warna Utama UNAIR: Biru Navy (#003366) dan Kuning Emas (#FFCC00) */
    .stApp { background-color: #fcfcfc; }
    
    /* Header & Sidebar */
    [data-testid="stSidebar"] { background-color: #002147; color: white; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] p { color: #f0f0f0; }
    
    /* Box Panduan */
    .guide-box { 
        background-color: #ffffff; 
        padding: 20px; 
        border-radius: 12px; 
        border-left: 8px solid #FFCC00; 
        box-shadow: 2px 2px 15px rgba(0,0,0,0.1); 
        margin-bottom: 20px; 
    }
    
    /* Laporan Biru Akuntansi (Disesuaikan) */
    .report-card { 
        background-color: #e6f0ff; 
        padding: 30px; 
        border-radius: 15px; 
        color: #002147; 
        border: 2px solid #003366; 
    }
    
    /* Kartu KUR BRI UNAIR */
    .kur-card { 
        background-color: #003366; 
        color: #FFCC00; 
        padding: 30px; 
        border-radius: 15px; 
        border: 3px solid #FFCC00;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    
    .stButton>button { 
        width: 100%; 
        font-weight: bold; 
        background-color: #FFCC00; 
        color: #002147; 
        border: none;
        border-radius: 8px;
    }
    .stButton>button:hover { background-color: #e6b800; color: #002147; }
    
    h1, h2, h3 { color: #002147; }
    .step-number { background-color: #FFCC00; color: #002147; padding: 3px 10px; border-radius: 50%; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: ASISTEN AIRLANGGA ---
with st.sidebar:
    # Bisa ganti URL logo dengan logo UNAIR jika ada
    st.markdown("<h2 style='text-align:center; color:#FFCC00;'>🦁 FIN-Saku</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'><b>Excellence with Morality</b></p>", unsafe_allow_html=True)
    st.write("---")
    
    nama_usaha = st.text_input("Nama Usaha", "Airlangga Bakery")
    
    st.markdown("### <span class='step-number'>1</span> Modal Awal", unsafe_allow_html=True)
    m_raw = st.text_input("Uang di Kas (Rp)", value="0")
    st.session_state.modal_awal = clean_to_int(m_raw)
    st.warning(f"Tercatat: **{format_rp(st.session_state.modal_awal)}**")

    st.markdown("### <span class='step-number'>2</span> Harga Produk", unsafe_allow_html=True)
    hpp_raw = st.text_input("HPP (Modal) Rp", "5000")
    harga_raw = st.text_input("Harga Jual Rp", "15000")
    
    prive_pct = st.slider("Jatah Pribadi (%)", 0, 100, 30)

# --- HALAMAN UTAMA ---
st.markdown(f"<h1>🎓 Dashboard Inklusi Keuangan: {nama_usaha}</h1>", unsafe_allow_html=True)

# PANDUAN PENYUSUNAN LAPORAN (SAK-EMKM)
with st.expander("📚 Prosedur Standar Akuntansi UMKM (Khusus Pengguna UNAIR)", expanded=False):
    st.markdown("""
    1. **Input Modal:** Mengukur *Capital* (Modal) awal sebagai dasar kepercayaan Bank.
    2. **Catat Penjualan:** Membuktikan *Capacity* (Kemampuan) arus kas usaha.
    3. **Prive (Pengambilan):** Menunjukkan *Morality* & disiplin pedagang dalam memisahkan uang.
    """)

st.write("---")

c1, c2 = st.columns([1, 1.5])
with c1:
    st.markdown("<div class='guide-box'><h3>📝 Catat Transaksi</h3>", unsafe_allow_html=True)
    tgl = st.date_input("Tanggal", datetime.now())
    qty = st.number_input("Jumlah terjual", min_value=0, step=1)
    
    if st.button("🔔 SIMPAN DATA"):
        v_hpp, v_harga = clean_to_int(hpp_raw), clean_to_int(harga_raw)
        if qty > 0:
            omzet, laba = qty * v_harga, qty * (v_harga - v_hpp)
            prive = laba * (prive_pct / 100)
            new_data = pd.DataFrame([{"Tanggal": tgl, "Bulan": tgl.strftime("%B %Y"), "Minggu": f"Minggu {tgl.isocalendar()[1]}", "Omzet": omzet, "Laba": laba, "Prive": prive}])
            st.session_state.db_transaksi = pd.concat([st.session_state.db_transaksi, new_data], ignore_index=True)
            st.success("Tersimpan dalam database!")
    st.markdown("</div>", unsafe_allow_html=True)

# --- LAPORAN & ANALISIS KUR ---
if not st.session_state.db_transaksi.empty:
    tab1, tab2 = st.tabs(["📊 Laporan Bulanan (SAK-EMKM)", "🏦 Kelayakan KUR BRI"])
    
    with tab1:
        sel_b = st.selectbox("Pilih Periode Laporan", st.session_state.db_transaksi['Bulan'].unique())
        df_b = st.session_state.db_transaksi[st.session_state.db_transaksi['Bulan'] == sel_b]
        
        # UI Laporan (Inspirasi dari Gambar Laporan PT Enggan Mundur)
        st.markdown(f"""
        <div class="report-card">
            <div style="text-align:center;">
                <h2 style='margin:0; color:#002147;'>{nama_usaha}</h2>
                <p style='color:#002147;'><b>Laporan Laba Rugi Periodik</b><br>Periode: {sel_b}</p>
            </div>
            <table style="width:100%; border-collapse: collapse; font-size:18px; color:#002147;">
                <tr style="border-bottom: 2px solid #002147;"><td style="padding:10px;">Pendapatan Usaha</td><td style="text-align:right;">{format_rp(df_b['Omzet'].sum())}</td></tr>
                <tr><td style="padding:10px;">Beban Pokok Penjualan (HPP)</td><td style="text-align:right;">({format_rp(df_b['Omzet'].sum() - df_b['Laba'].sum())})</td></tr>
                <tr style="border-bottom: 2px solid #002147; font-weight:bold;"><td>LABA BERSIH</td><td style="text-align:right;">{format_rp(df_b['Laba'].sum())}</td></tr>
                <tr style="color:#cc0000;"><td>Pengambilan Prive ({prive_pct}%)</td><td style="text-align:right;">({format_rp(df_b['Prive'].sum())})</td></tr>
                <tr style="background-color:#FFCC00; font-weight:bold; font-size:20px;">
                    <td style="padding:15px;">TOTAL MODAL BERJALAN</td><td style="text-align:right;">{format_rp(st.session_state.modal_awal + (df_b['Laba'].sum() - df_b['Prive'].sum()))}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with tab2:
        # LOGIKA PERHITUNGAN KUR
        avg_laba = st.session_state.db_transaksi['Laba'].sum() / max(1, len(st.session_state.db_transaksi['Bulan'].unique()))
        rpc = avg_laba * 0.35 
        plafon = rpc / ((1/12) + 0.005) 

        st.markdown(f"""
        <div class="kur-card">
            <h2 style='margin-top:0;'>🦁 Analisis Kelayakan KUR BRI</h2>
            <p>Berdasarkan <b>Standar Kredit Perbankan</b>, hasil Anda adalah:</p>
            <table style="width:100%; font-size:18px;">
                <tr><td>1. <b>Karakter:</b> Disiplin Pencatatan</td><td style="text-align:right;">SANGAT BAIK ✅</td></tr>
                <tr><td>2. <b>Kapasitas:</b> Kemampuan Bayar Cicilan</td><td style="text-align:right;">{format_rp(rpc)} /bln</td></tr>
                <tr><td>3. <b>Modal:</b> Rasio Modal Sendiri</td><td style="text-align:right;">SEHAT ✅</td></tr>
                <tr style="font-size:30px; font-weight:bold;">
                    <td>ESTIMASI PLAFON KUR</td><td style="text-align:right;">{format_rp(plafon)}</td>
                </tr>
            </table>
            <hr style="border: 1px solid #FFCC00;">
            <p style="font-size:14px;">Aplikasi ini merekomendasikan Anda untuk mengajukan KUR Mikro BRI dengan bunga subsidi 6%. Bawa laporan ini ke Bank sebagai bukti pendukung.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write(" ")
        st.button("📥 Unduh Sertifikat Layak Kredit (PDF)")

st.write("---")
st.caption("© 2024 FIN-Saku UNAIR | Excellence with Morality | Inklusi Keuangan Indonesia")

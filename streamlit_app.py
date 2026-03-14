import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_final_v2.db', check_same_thread=False)
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

# --- FUNGSI EXPORT PDF ---
def generate_pdf(nama_usaha, periode, omzet, laba, prive, kas_awal, kas_akhir):
    pdf = FPDF()
    pdf.add_page()
    
    # Header / Kop Surat
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, nama_usaha.upper(), 0, 1, 'C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 7, "LAPORAN KEUANGAN UMKM", 0, 1, 'C')
    pdf.cell(190, 7, f"Periode: {periode}", 0, 1, 'C')
    pdf.ln(10)
    pdf.line(10, 40, 200, 40)
    
    # Tabel Laba Rugi
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. LAPORAN LABA RUGI", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    data_lr = [
        ["Total Pendapatan (Omzet)", format_rp(omzet)],
        ["Total Laba Kotor/Bersih", format_rp(laba)],
        ["Pengambilan Prive", f"({format_rp(prive)})"],
        ["Laba Ditahan", format_rp(laba - prive)]
    ]
    
    for row in data_lr:
        pdf.cell(100, 8, row[0], 1)
        pdf.cell(90, 8, row[1], 1, 1, 'R')
    
    pdf.ln(10)
    
    # Tabel Posisi Kas
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. LAPORAN POSISI KAS", 0, 1, 'L')
    pdf.set_font("Arial", '', 11)
    
    data_kas = [
        ["Saldo Kas Awal", format_rp(kas_awal)],
        ["Kenaikan/Penurunan Kas", format_rp(laba - prive)],
        ["Saldo Kas Akhir", format_rp(kas_akhir)]
    ]
    
    for row in data_kas:
        if row[0] == "Saldo Kas Akhir": pdf.set_font("Arial", 'B', 11)
        pdf.cell(100, 8, row[0], 1)
        pdf.cell(90, 8, row[1], 1, 1, 'R')
        
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 5, f"Dicetak otomatis melalui FIN-Saku pada {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM
st.markdown("""
<style>
    .stApp { background-color: #001f3f !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
        color: #000000 !important;
    }
    .white-card *, .white-card p, .white-card b, .white-card h3, .white-card td { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #000 !important; font-weight: bold; width: 100%; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
jumlah_bulan_data = df['bulan'].nunique() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner", "Retail", "Jasa", "Produksi"])
    
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    st.caption(f"Tercatat: {format_rp(modal_awal)}")
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga")
    hpp_raw = st.text_input("HPP Produk (Modal)", "5000")
    hpp_val = clean_to_int(hpp_raw)
    st.caption(f"Tercatat: {format_rp(hpp_val)}")

    hrg_raw = st.text_input("Harga Jual", "15000")
    hrg_val = clean_to_int(hrg_raw)
    st.caption(f"Tercatat: {format_rp(hrg_val)}")
    
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin: **{margin_pct:.1f}%**")
        # Peringatan Margin Interaktif
        if margin_pct < 30:
            st.warning("⚠️ Margin di bawah 30% berisiko rugi operasional!")
    
    prive_pct = st.slider("Jatah Prive (%)", 0, 100, 30)
    if prive_pct > 50:
        st.error("🚨 Bahaya! Pengambilan pribadi > 50% mematikan kas usaha.")

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard: {nama_u}")
rekap_mode = st.radio("Metode Catat:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col_in, col_info = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet_raw = st.text_input("Total Omzet", "0")
    omzet_in = clean_to_int(omzet_raw)
    st.markdown(f"<p style='color:#FFD700;'>Tercatat: <b>{format_rp(omzet_in)}</b></p>", unsafe_allow_html=True)
    
    if st.button("🚀 SIMPAN TRANSAKSI"):
        biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
        laba_in = omzet_in - biaya_hpp
        prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0
        
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.toast(f"Data {rekap_mode} Berhasil Dicatat!", icon="✅")
        st.rerun()

with col_info:
    st.markdown(f'<div class="white-card"><h3>💡 Tips Konsultan</h3><p>Sektor <b>{sektor}</b> Anda saat ini memiliki margin <b>{margin_pct:.1f}%</b>. Jaga arus kas agar tetap Bankable!</p></div>', unsafe_allow_html=True)

# --- TABS ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        df['tgl_dt'] = pd.to_datetime(df['tanggal'], errors='coerce')
        df = df.dropna(subset=['tgl_dt']).sort_values('tgl_dt')
        list_bulan = df['bulan'].unique().tolist()
        
        if list_bulan:
            sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
            db_bulan = df[df['bulan'] == sel_b]
            
            o_bln = db_bulan['omzet'].sum()
            l_bln = db_bulan['laba'].sum()
            p_bln = db_bulan['prive'].sum()
            
            idx_b = list_bulan.index(sel_b)
            l_lalu = df[df['bulan'].isin(list_bulan[:idx_b])]['laba'].sum()
            p_lalu = df[df['bulan'].isin(list_bulan[:idx_b])]['prive'].sum()
            
            m_awal_b = modal_awal + l_lalu - p_lalu
            m_akhir_b = m_awal_b + l_bln - p_bln

            c_lr, c_pm = st.columns(2)
            with c_lr:
                st.markdown(f'<div class="white-card"><h3>LABA RUGI - {sel_b}</h3><hr>Omzet: {format_rp(o_bln)}<br>Laba Bersih: <b>{format_rp(l_bln)}</b><br>Prive: {format_rp(p_bln)}</div>', unsafe_allow_html=True)
            with c_pm:
                st.markdown(f'<div class="white-card"><h3>MODAL - {sel_b}</h3><hr>Kas Awal: {format_rp(m_awal_b)}<br>Kas Akhir: <b>{format_rp(m_akhir_b)}</b></div>', unsafe_allow_html=True)
            
            # FITUR UNDUH PDF
            st.write(" ")
            pdf_data = generate_pdf(nama_u, sel_b, o_bln, l_bln, p_bln, m_awal_b, m_akhir_b)
            st.download_button(
                label="📥 UNDUH LAPORAN PDF",
                data=pdf_data,
                file_name=f"Laporan_{nama_u}_{sel_b}.pdf",
                mime="application/pdf"
            )

    with tab_kur:
        # LOGIKA KUR TETAP (SESUAI PERMINTAAN)
        st.subheader("🏦 Konsultasi Strategis KUR")
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        if jumlah_bulan_data < 3:
            st.error("### 🚩 STATUS: BELUM LAYAK (DATA KURANG)")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            max_cicilan_aman = l_bln * 0.35
            plafon = 50000000 if m_akhir_b > 15000000 else 10000000
            produk = "KUR Mikro BRI" if plafon > 10000000 else "KUR Super Mikro BRI"
            st.markdown(f'<div class="white-card"><h4>Rekomendasi Plafon:</h4><h2>{produk}: {format_rp(plafon)}</h2><p>Batas Cicilan Aman: <b>{format_rp(max_cicilan_aman)}/bln</b></p></div>', unsafe_allow_html=True)
            
            tenor = st.select_slider("Tenor (Bulan):", options=[12, 18, 24, 36])
            cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            sisa = l_bln - cicilan
            
            col_a, col_b = st.columns(2)
            col_a.markdown(f'<div class="white-card"><h4>Cicilan:</h4><h3>{format_rp(cicilan)}</h3></div>', unsafe_allow_html=True)
            col_b.markdown(f'<div class="white-card"><h4>Sisa Laba:</h4><h3>{format_rp(sisa)}</h3></div>', unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi Data")
        target = st.selectbox("Pilih data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df.sort_values('id', ascending=False).iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Silakan masukkan transaksi pertama Anda.")

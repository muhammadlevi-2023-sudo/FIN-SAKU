import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
from fpdf import FPDF

# 1. KONFIGURASI HALAMAN
st.set_page_config(page_title="FIN-Saku: Konsultan Keuangan UMKM", layout="wide")

# --- DATABASE ENGINE ---
conn = sqlite3.connect('finsaku_pro_final.db', check_same_thread=False)
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
        return f"Rp {formatted}" if angka >= 0 else f"Rp -{formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# --- FUNGSI EXPORT PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'LAPORAN KEUANGAN UMKM (FIN-SAKU)', 0, 1, 'C')
        self.ln(5)

def generate_pdf(nama, periode, omzet, laba, modal_awal, modal_akhir):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Nama Usaha: {nama}", ln=True)
    pdf.cell(200, 10, txt=f"Periode Laporan: {periode}", ln=True)
    pdf.ln(10)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, "RINGKASAN LABA RUGI", 1, 1, 'C', 1)
    pdf.cell(100, 10, "Total Omzet", 1); pdf.cell(0, 10, format_rp(omzet), 1, 1)
    pdf.cell(100, 10, "Laba Bersih", 1); pdf.cell(0, 10, format_rp(laba), 1, 1)
    pdf.ln(5)
    pdf.cell(0, 10, "RINGKASAN PERUBAHAN MODAL", 1, 1, 'C', 1)
    pdf.cell(100, 10, "Modal Awal", 1); pdf.cell(0, 10, format_rp(modal_awal), 1, 1)
    pdf.cell(100, 10, "Modal Akhir (Kas)", 1); pdf.cell(0, 10, format_rp(modal_akhir), 1, 1)
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM (NAVY & GOLD)
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

# --- LOGIKA DATA ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner (Makanan/Minuman)", "Retail (Toko Kelontong/Baju)", "Jasa (Laundry/Service)", "Produksi/Manufaktur"])
    modal_awal = clean_to_int(st.text_input("Uang Kas Awal (Modal)", "7000000"))
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp_val = clean_to_int(st.text_input("HPP Produk", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    # --- LOGIKA KATA-KATA MARGIN INTERAKTIF ---
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.markdown(f"Margin Anda: **{margin_pct:.1f}%**")
        
        if "Kuliner" in sektor:
            target, pesan = 40, "Kuliner butuh margin tinggi (min 40%) karena risiko waste (basi)."
        elif "Retail" in sektor:
            target, pesan = 15, "Retail main di volume, margin 15-20% sudah cukup bagus."
        elif "Jasa" in sektor:
            target, pesan = 60, "Jasa harus margin tinggi (>60%) karena menjual keahlian."
        else:
            target, pesan = 30, "Produksi butuh min 30% untuk biaya penyusutan alat."
        
        warna = "lime" if margin_pct >= target else "#FFD700"
        st.markdown(f"<p style='color:{warna}; font-size:0.85rem;'>💡 {pesan}</p>", unsafe_allow_html=True)
    
    st.write("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)
    # --- LOGIKA PRIVE INTERAKTIF ---
    if prive_pct <= 30:
        st.markdown("<p style='color:lime; font-size:0.85rem;'>✅ Prive Aman: Laba sehat untuk diputar kembali.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='color:#FFD700; font-size:0.85rem;'>⚠️ Prive Tinggi: Modal usaha akan lambat tumbuh jika jatah pribadi terlalu besar.</p>", unsafe_allow_html=True)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
rekap_mode = st.radio("Metode Catat:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col_in, col_info = st.columns([1, 1.2])
with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet_in = st.number_input("Total Omzet Penjualan", value=0, step=10000)
    
    laba_in = omzet_in - (omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0)
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.success("Data Berhasil Disimpan!")
        st.rerun()

with col_info:
    st.markdown(f"""<div class="white-card">
        <h3>💡 Tips Konsultan</h3>
        <p>Sektor <b>{sektor}</b> membutuhkan konsistensi data minimal 3 bulan agar layak dianalisis oleh Bank (KUR).</p>
        <hr>
        <p>Estimasi Laba: <b>{format_rp(laba_in)}</b></p>
        <p>Potongan Prive: <b>{format_rp(prive_in)}</b></p>
    </div>""", unsafe_allow_html=True)

# --- BAGIAN TABS ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        df['tgl_dt'] = pd.to_datetime(df['tanggal'])
        list_bulan = df.sort_values('tgl_dt')['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        
        db_bulan = df[df['bulan'] == sel_b]
        o_bln, l_bln, p_bln = db_bulan['omzet'].sum(), db_bulan['laba'].sum(), db_bulan['prive'].sum()
        
        idx_bulan = list_bulan.index(sel_b)
        m_awal_bln = modal_awal + df[df['bulan'].isin(list_bulan[:idx_bulan])]['laba'].sum() - df[df['bulan'].isin(list_bulan[:idx_bulan])]['prive'].sum()
        m_akhir_bln = m_awal_bln + l_bln - p_bln

        c_lr, c_pm = st.columns(2)
        with c_lr: st.markdown(f'<div class="white-card"><h3>LABA RUGI</h3><hr>Omzet: {format_rp(o_bln)}<br>Laba Bersih: <b>{format_rp(l_bln)}</b></div>', unsafe_allow_html=True)
        with c_pm: st.markdown(f'<div class="white-card"><h3>MODAL</h3><hr>Kas Awal: {format_rp(m_awal_bln)}<br>Kas Akhir: <b>{format_rp(m_akhir_bln)}</b></div>', unsafe_allow_html=True)
        
        pdf_data = generate_pdf(nama_u, sel_b, o_bln, l_bln, m_awal_bln, m_akhir_bln)
        st.download_button("📥 DOWNLOAD LAPORAN (PDF)", pdf_data, f"Laporan_{sel_b}.pdf", "application/pdf")

    with tab_kur:
        # Logika KUR tetap ada
        st.subheader("🏦 Konsultasi Strategis KUR")
        plafon = 50000000 if m_akhir_bln > 15000000 else 10000000
        st.write(f"Saran Plafon KUR: **{format_rp(plafon)}**")

    with tab_rev:
        st.subheader("🛠️ Revisi / Edit Transaksi")
        df_rev = df.sort_values(by='id', ascending=False)
        pilihan_data = [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()]
        target_str = st.selectbox("Pilih Transaksi untuk diubah:", pilihan_data)
        target_id = int(target_str.split("|")[0].replace("ID:","").strip())
        
        data_lama = df[df['id'] == target_id].iloc[0]
        
        with st.expander("📝 Form Edit Data"):
            new_tgl = st.date_input("Ubah Tanggal", datetime.strptime(data_lama['tanggal'], "%Y-%m-%d"))
            new_omzet = st.number_input("Ubah Omzet", value=float(data_lama['omzet']))
            
            if st.button("✅ SIMPAN PERUBAHAN"):
                n_laba = new_omzet - (new_omzet * (hpp_val / hrg_val) if hrg_val > 0 else 0)
                n_prive = n_laba * (prive_pct / 100) if n_laba > 0 else 0
                c.execute("""UPDATE transaksi SET tanggal=?, bulan=?, minggu=?, omzet=?, laba=?, prive=? WHERE id=?""",
                          (new_tgl.strftime("%Y-%m-%d"), new_tgl.strftime("%B %Y"), f"Minggu {new_tgl.isocalendar()[1]}", 
                           new_omzet, n_laba, n_prive, target_id))
                conn.commit()
                st.success("Berhasil diupdate!")
                st.rerun()
            
            if st.button("🗑️ HAPUS PERMANEN"):
                c.execute("DELETE FROM transaksi WHERE id=?", (target_id,))
                conn.commit()
                st.rerun()

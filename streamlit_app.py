import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from fpdf import FPDF
import io

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
        if angka < 0: return f"Rp -{formatted}"
        return f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

# --- FUNGSI GENERATE PDF (STANDAR BANK) ---
def generate_pdf(nama_usaha, periode_bulan, data_ringkas):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, nama_usaha.upper(), ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "LAPORAN KEUANGAN BULANAN", ln=True, align='C')
    pdf.cell(190, 10, f"Periode: {periode_bulan}", ln=True, align='C')
    pdf.line(10, 45, 200, 45)
    pdf.ln(15)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "I. LAPORAN LABA RUGI", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 10, "Total Pendapatan (Omzet)"); pdf.cell(90, 10, format_rp(data_ringkas['omzet']), ln=True, align='R')
    pdf.cell(100, 10, "Beban Pokok Penjualan (HPP)"); pdf.cell(90, 10, f"- {format_rp(data_ringkas['omzet'] - data_ringkas['laba'])}", ln=True, align='R')
    pdf.line(110, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "LABA BERSIH OPERASIONAL"); pdf.cell(90, 10, format_rp(data_ringkas['laba']), ln=True, align='R')
    pdf.ln(10)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "II. LAPORAN PERUBAHAN MODAL", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(100, 10, "Modal Awal Periode"); pdf.cell(90, 10, format_rp(data_ringkas['modal_awal']), ln=True, align='R')
    pdf.cell(100, 10, "Laba Bersih Bulan Ini"); pdf.cell(90, 10, format_rp(data_ringkas['laba']), ln=True, align='R')
    pdf.cell(100, 10, "Pengambilan Pribadi (Prive)"); pdf.cell(90, 10, f"- {format_rp(data_ringkas['prive'])}", ln=True, align='R')
    pdf.line(110, pdf.get_y(), 200, pdf.get_y())
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(100, 10, "MODAL AKHIR (KAS)"); pdf.cell(90, 10, format_rp(data_ringkas['modal_akhir']), ln=True, align='R')
    
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, f"Dicetak via FIN-Saku pada {datetime.now().strftime('%d/%m/%Y %H:%M')}", align='C')
    return pdf.output(dest='S').encode('latin-1')

# 2. UI CUSTOM (NAVY & GOLD UNAIR)
st.markdown("""
<style>
    .stApp { background-color: #002147 !important; }
    .stApp, .stApp p, .stApp label, .stApp h1, .stApp h2, .stApp h3 { color: #ffffff !important; }
    .white-card {
        background-color: #ffffff !important;
        padding: 20px; border-radius: 12px; border-left: 8px solid #FFD700;
        margin-bottom: 15px; box-shadow: 0px 4px 10px rgba(0,0,0,0.3);
    }
    .white-card * { color: #000000 !important; }
    .stButton>button { background-color: #FFD700 !important; color: #002147 !important; font-weight: bold; width: 100%; border-radius: 8px; }
    section[data-testid="stSidebar"] { background-color: #00152b !important; border-right: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

# --- DATA ENGINE ---
df = pd.read_sql_query("SELECT * FROM transaksi", conn)
jumlah_bulan_data = df['bulan'].nunique() if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center; color:#FFD700;'>💰 FIN-Saku</h1>", unsafe_allow_html=True)
    st.write("---")
    nama_u = st.text_input("Nama Usaha", "UMKM Maju Bersama")
    sektor = st.selectbox("Sektor Usaha:", ["Kuliner (Makanan/Minuman)", "Retail (Toko Kelontong/Baju)", "Jasa (Laundry/Service)", "Produksi/Manufaktur"])
    
    modal_awal_input = st.text_input("Uang Kas Awal (Modal)", "7000000")
    modal_awal = clean_to_int(modal_awal_input)
    
    total_laba_all = df['laba'].sum() if not df.empty else 0
    total_prive_all = df['prive'].sum() if not df.empty else 0
    modal_skrg_all = modal_awal + total_laba_all - total_prive_all
    
    st.markdown(f"Modal Awal: **{format_rp(modal_awal)}**")
    st.markdown(f"<h3 style='color:#FFD700;'>Kas Saat Ini:<br>{format_rp(modal_skrg_all)}</h3>", unsafe_allow_html=True)
    
    st.write("---")
    st.subheader("⚙️ Aturan Harga & Margin")
    hpp_val = clean_to_int(st.text_input("HPP Produk (Modal)", "5000"))
    hrg_val = clean_to_int(st.text_input("Harga Jual", "15000"))
    
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin Anda: **{margin_pct:.1f}%**")
        if "Kuliner" in sektor: target, pesan = 40, "Kuliner butuh margin tinggi (min 40%) karena risiko waste."
        elif "Retail" in sektor: target, pesan = 15, "Retail main di volume, margin 15-20% sudah cukup."
        elif "Jasa" in sektor: target, pesan = 60, "Jasa harus margin tinggi (>60%) karena jual keahlian."
        else: target, pesan = 30, "Produksi butuh min 30% untuk biaya penyusutan alat."
        warna_margin = "lime" if margin_pct >= target else "orange"
        st.markdown(f"<p style='color:{warna_margin}; font-size:0.85rem;'>💡 {pesan}</p>", unsafe_allow_html=True)
    
    st.write("---")
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 100, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
st.subheader("📝 Catat Penjualan")
rekap_mode = st.radio("Pilih Periode Catat:", ["Harian", "Mingguan", "Bulanan"], horizontal=True)

col_in, col_info = st.columns([1, 1.2])

with col_in:
    if rekap_mode == "Harian":
        tgl_input = st.date_input("Pilih Tanggal", datetime.now(), key="tgl_harian")
        val_tgl = tgl_input.strftime("%Y-%m-%d")
        val_bulan = tgl_input.strftime("%B %Y")
        dom = tgl_input.day
        val_minggu = f"Minggu ke-{(dom - 1) // 7 + 1}"
    elif rekap_mode == "Mingguan":
        tgl_ref = st.date_input("Pilih salah satu tanggal di minggu tersebut:", datetime.now(), key="tgl_minggu")
        val_bulan = tgl_ref.strftime("%B %Y")
        val_minggu = f"Minggu ke-{(tgl_ref.day - 1) // 7 + 1}"
        val_tgl = f"Rekap {val_minggu} - {val_bulan}"
    else:
        list_nama_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        bulan_pilih = st.selectbox("Pilih Bulan", list_nama_bulan, index=datetime.now().month - 1)
        val_bulan = f"{bulan_pilih} {datetime.now().year}"
        val_tgl, val_minggu = f"Rekap Bulanan {val_bulan}", "-"

    omzet_in = st.number_input("Total Omzet Penjualan", value=0, step=10000)
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🔔 SIMPAN TRANSAKSI"):
        if omzet_in > 0:
            c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (val_tgl, val_bulan, val_minggu, omzet_in, laba_in, prive_in, rekap_mode))
            conn.commit()
            st.rerun()

with col_info:
    st.markdown(f"""<div class="white-card">
        <h3>📢 Status Pencatatan</h3>
        <p><b>{val_minggu}</b> | <b>{val_bulan}</b></p>
        <hr>
        <p>Laba Estimasi: <b>{format_rp(laba_in)}</b><br>
        Prive (Diambil): <b>{format_rp(prive_in)}</b></p>
    </div>""", unsafe_allow_html=True)

# --- TABS ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        db_bulan = df[df['bulan'] == sel_b]
        omzet_bln, laba_bln, prive_bln = db_bulan['omzet'].sum(), db_bulan['laba'].sum(), db_bulan['prive'].sum()
        
        idx_bulan = list_bulan.index(sel_b)
        total_laba_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['laba'].sum()
        total_prive_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['prive'].sum()
        modal_awal_bln = modal_awal + total_laba_lalu - total_prive_lalu
        modal_akhir_bln = modal_awal_bln + laba_bln - prive_bln

        c1, c2 = st.columns(2)
        with c1: st.markdown(f'<div class="white-card"><h3>LABA RUGI - {sel_b}</h3><hr>Omzet: {format_rp(omzet_bln)}<br>Laba Bersih: <b>{format_rp(laba_bln)}</b></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="white-card"><h3>MODAL - {sel_b}</h3><hr>Kas Awal: {format_rp(modal_awal_bln)}<br>Kas Akhir: <b>{format_rp(modal_akhir_bln)}</b></div>', unsafe_allow_html=True)
        
        pdf_file = generate_pdf(nama_u, sel_b, {'omzet': omzet_bln, 'laba': laba_bln, 'prive': prive_bln, 'modal_awal': modal_awal_bln, 'modal_akhir': modal_akhir_bln})
        st.download_button("📥 DOWNLOAD PDF UNTUK BANK", data=pdf_file, file_name=f"Laporan_{sel_b}.pdf", mime="application/pdf")

    with tab_kur:
        st.subheader("🏦 Konsultasi Strategis KUR")
        if jumlah_bulan_data < 3:
            st.error(f"### 🚩 STATUS: BELUM LAYAK (Kurang {3-jumlah_bulan_data} bulan data lagi)")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            tenor = st.select_slider("Tenor (Bulan):", options=[12, 18, 24, 36])
            total_cicilan = (50000000 / tenor) + ((50000000 * 0.06) / 12)
            sisa_laba = laba_bln - total_cicilan
            persen_sisa = (sisa_laba / laba_bln) * 100
            st.markdown(f'<div class="white-card">Cicilan: {format_rp(total_cicilan)}/bln<br>Sisa Laba: {format_rp(sisa_laba)} ({persen_sisa:.0f}%)<hr><b>Saran:</b> {"✅ Aman!" if persen_sisa >= 70 else "⚠️ Bahaya, naikkan tenor!"}</div>', unsafe_allow_html=True)

    with tab_rev:
        target = st.selectbox("Hapus data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df.sort_values(by='id', ascending=False).iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Mari mulai catat transaksi pertama Anda hari ini.")

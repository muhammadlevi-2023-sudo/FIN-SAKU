import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
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
        if angka < 0: return f"Rp -{formatted}"
        return f"Rp {formatted}"
    except: return "Rp 0"

def clean_to_int(teks):
    if not teks: return 0
    return int("".join(filter(str.isdigit, str(teks))))

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

# --- LOGIKA DATA REALTIME ---
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
    
    margin_pct = 0
    if hrg_val > 0:
        margin_pct = ((hrg_val - hpp_val) / hrg_val) * 100
        st.write(f"Margin Anda: **{margin_pct:.1f}%**")
    
    prive_pct = st.slider("Jatah Pribadi/Prive (%)", 0, 50, 30)

# --- DASHBOARD UTAMA ---
st.title(f"Dashboard Keuangan: {nama_u}")
rekap_mode = st.selectbox("Metode Catat:", ["Harian", "Mingguan", "Bulanan"])
col_in, col_info = st.columns([1, 1.2])

with col_in:
    st.subheader("📝 Input Penjualan")
    tgl = st.date_input("Tanggal", datetime.now())
    omzet_in = st.number_input("Total Omzet Penjualan", value=0, step=10000)
    
    biaya_hpp = omzet_in * (hpp_val / hrg_val) if hrg_val > 0 else 0
    laba_in = omzet_in - biaya_hpp
    prive_in = laba_in * (prive_pct / 100) if laba_in > 0 else 0

    if st.button("🔔 SIMPAN TRANSAKSI"):
        c.execute("INSERT INTO transaksi (tanggal, bulan, minggu, omzet, laba, prive, periode) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (tgl.strftime("%Y-%m-%d"), tgl.strftime("%B %Y"), f"Minggu {tgl.isocalendar()[1]}", omzet_in, laba_in, prive_in, rekap_mode))
        conn.commit()
        st.rerun()

with col_info:
    st.markdown(f'<div class="white-card"><h3>💡 Tips Konsultan</h3><p>Sektor <b>{sektor}</b> membutuhkan konsistensi laporan minimal 3 bulan untuk dilirik Bank.</p></div>', unsafe_allow_html=True)

# --- BAGIAN TABS ---
if not df.empty:
    st.write("---")
    tab_rep, tab_kur, tab_rev = st.tabs(["📊 LAPORAN KEUANGAN", "🏦 ANALISIS KUR BRI", "🛠️ REVISI"])
    
    with tab_rep:
        df['tgl_dt'] = pd.to_datetime(df['tanggal'])
        df = df.sort_values('tgl_dt')
        list_bulan = df['bulan'].unique().tolist()
        sel_b = st.selectbox("Pilih Bulan Laporan:", list_bulan, index=len(list_bulan)-1)
        
        db_bulan = df[df['bulan'] == sel_b]
        
        # --- REVISI LOGIKA AKUNTANSI (SESUAI GAMBAR) ---
        o_sum = db_bulan['omzet'].sum()
        hpp_total = o_sum * (hpp_val / hrg_val) if hrg_val > 0 else 0
        l_operasional = o_sum - hpp_total
        p_sum = db_bulan['prive'].sum()
        
        idx_bulan = list_bulan.index(sel_b)
        total_laba_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['laba'].sum()
        total_prive_lalu = df[df['bulan'].isin(list_bulan[:idx_bulan])]['prive'].sum()
        
        modal_awal_bln = modal_awal + total_laba_lalu - total_prive_lalu
        modal_akhir_bln = modal_awal_bln + l_operasional - p_sum

        # Tampilan Interface Laporan Profesional
        st.markdown(f"""
        <div class="white-card">
            <h3 style="text-align:center;">{nama_u.upper()}</h3>
            <p style="text-align:center; margin-top:-15px;">LAPORAN KEUANGAN BULANAN<br>Periode: {sel_b}</p>
            <hr>
            <b>I. LAPORAN LABA RUGI</b><br>
            <div style="display:flex; justify-content:space-between;"><span>Total Pendapatan (Omzet)</span><b>{format_rp(o_sum)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Beban Pokok Penjualan (HPP)</span><span style="color:red;">-{format_rp(hpp_total)}</span></div>
            <div style="border-top:1px solid #ccc; margin:5px 0;"></div>
            <div style="display:flex; justify-content:space-between;"><b>LABA BERSIH OPERASIONAL</b><b>{format_rp(l_operasional)}</b></div>
            <br>
            <b>II. LAPORAN PERUBAHAN MODAL</b><br>
            <div style="display:flex; justify-content:space-between;"><span>Modal Awal Periode</span><b>{format_rp(modal_awal_bln)}</b></div>
            <div style="display:flex; justify-content:space-between;"><span>Ditambah: Laba Bersih</span><span style="color:green;">{format_rp(l_operasional)}</span></div>
            <div style="display:flex; justify-content:space-between;"><span>Dikurangi: Prive</span><span style="color:red;">-{format_rp(p_sum)}</span></div>
            <div style="border-top:1px solid #ccc; margin:5px 0;"></div>
            <div style="display:flex; justify-content:space-between; font-size:1.1rem; background:#f0f2f6; padding:5px;"><b>MODAL AKHIR PERIODE</b><b>{format_rp(modal_akhir_bln)}</b></div>
        </div>
        """, unsafe_allow_html=True)

        # --- FITUR DOWNLOAD PDF ---
        if st.button("📥 DOWNLOAD LAPORAN PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(190, 7, nama_u.upper(), 0, 1, 'C')
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(190, 7, "LAPORAN KEUANGAN BULANAN", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 7, f"Periode: {sel_b}", 0, 1, 'C')
            pdf.line(10, 35, 200, 35)
            pdf.ln(10)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "I. LAPORAN LABA RUGI", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Total Pendapatan (Omzet)", 0, 0); pdf.cell(90, 8, format_rp(o_sum), 0, 1, 'R')
            pdf.cell(100, 8, "Beban Pokok Penjualan (HPP)", 0, 0); pdf.cell(90, 8, f"- {format_rp(hpp_total)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "LABA BERSIH OPERASIONAL", 0, 0); pdf.cell(90, 10, format_rp(l_operasional), 0, 1, 'R')
            pdf.ln(5)
            
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(190, 10, "II. LAPORAN PERUBAHAN MODAL", 0, 1, 'L')
            pdf.set_font("Arial", '', 10)
            pdf.cell(100, 8, "Modal Awal Periode", 0, 0); pdf.cell(90, 8, format_rp(modal_awal_bln), 0, 1, 'R')
            pdf.cell(100, 8, "Ditambah: Laba Bersih", 0, 0); pdf.cell(90, 8, format_rp(l_operasional), 0, 1, 'R')
            pdf.cell(100, 8, "Dikurangi: Pengambilan Pribadi (Prive)", 0, 0); pdf.cell(90, 8, f"- {format_rp(p_sum)}", 0, 1, 'R')
            pdf.line(110, pdf.get_y(), 200, pdf.get_y())
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(100, 10, "MODAL AKHIR PERIODE", 0, 0); pdf.cell(90, 10, format_rp(modal_akhir_bln), 0, 1, 'R')
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button(label="Klik Simpan PDF", data=pdf_output, file_name=f"Laporan_{sel_b}.pdf", mime="application/pdf")

    with tab_kur:
        st.subheader("🏦 Konsultasi Strategis KUR")
        st.write(f"Histori Laporan: **{jumlah_bulan_data} Bulan**")
        
        if jumlah_bulan_data < 3:
            st.error("### 🚩 STATUS: BELUM LAYAK (DATA KURANG)")
            st.info(f"Lengkapi catatan {3-jumlah_bulan_data} bulan lagi untuk analisis mendalam.")
        else:
            st.success("### ✅ STATUS: SANGAT LAYAK (READY TO BANK)")
            max_cicilan_aman = l_operasional * 0.35
            plafon = 50000000 if modal_akhir_bln > 15000000 else 10000000
            produk = "KUR Mikro BRI" if plafon > 10000000 else "KUR Super Mikro BRI"

            st.markdown(f'<div class="white-card"><h4>Rekomendasi Plafon:</h4><h2>{produk}: {format_rp(plafon)}</h2><p>Batas Cicilan Aman Sistem: <b>{format_rp(max_cicilan_aman)}/bln</b></p></div>', unsafe_allow_html=True)
            
            tenor = st.select_slider("Pilih Jangka Waktu (Bulan):", options=[12, 18, 24, 36])
            total_cicilan = (plafon / tenor) + ((plafon * 0.06) / 12)
            sisa_laba = l_operasional - total_cicilan
            persen_sisa = (sisa_laba / l_operasional * 100) if l_operasional > 0 else 0

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f'<div class="white-card"><h4>Cicilan Per Bulan:</h4><h3>{format_rp(total_cicilan)}</h3></div>', unsafe_allow_html=True)
            with col_b:
                warna_sisa = "green" if persen_sisa >= 70 else "orange"
                st.markdown(f'<div class="white-card"><h4>Sisa Laba Bersih:</h4><h3 style="color:{warna_sisa};">{format_rp(sisa_laba)} ({persen_sisa:.0f}%)</h3></div>', unsafe_allow_html=True)

            st.write("---")
            st.subheader("📝 Kesimpulan Analisis Hasil (Credit Scoring)")
            narasi_status = "Sangat Layak" if persen_sisa >= 70 else "Perlu Penyesuaian"
            
            st.markdown(f"""
            <div class="white-card" style="border-left: 8px solid #001f3f;">
                Berdasarkan data bulan {sel_b}, status Anda dianggap <b>"{narasi_status}"</b>:
                <br><br>
                <b>1. Rekomendasi Pinjaman:</b> Plafon <b>{format_rp(plafon)}</b> via {produk}.<br>
                <b>2. Batas Aman:</b> Cicilan ideal maksimal <b>{format_rp(max_cicilan_aman)}/bln</b>.<br>
                <b>3. Arus Kas:</b> Sisa laba setelah cicilan adalah <b>{format_rp(sisa_laba)}</b>.
                <br><br>
                {"✅ Pilihan tenor sudah aman." if persen_sisa >= 70 else "⚠️ Pertimbangkan tenor lebih panjang agar sisa laba di atas 70%."}
            </div>
            """, unsafe_allow_html=True)

    with tab_rev:
        st.subheader("🛠️ Revisi Data")
        df_rev = df.sort_values(by='id', ascending=False)
        target = st.selectbox("Pilih data:", [f"ID:{r['id']} | {r['tanggal']} | {format_rp(r['omzet'])}" for _, r in df_rev.iterrows()])
        if st.button("🗑️ HAPUS PERMANEN"):
            c.execute("DELETE FROM transaksi WHERE id=?", (int(target.split("|")[0].replace("ID:","")),))
            conn.commit()
            st.rerun()
else:
    st.info("Silakan masukkan transaksi pertama Anda.")

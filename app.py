import os
import json
import time
import random
import hashlib
from urllib.parse import quote
from datetime import datetime, date

import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from dotenv import load_dotenv

# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="FinQuest AI — Ruang Akuntansi, Kuis & Mabar",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# 2. LOAD GEMINI API KEY
# =====================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

try:
    if "GEMINI_API_KEY" in st.secrets:
        GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

if not GEMINI_API_KEY:
    st.error(
        "Gemini API Key belum ditemukan! "
        "Silakan isi GEMINI_API_KEY di file .env atau Streamlit Secrets."
    )
    st.stop()

# =====================================================
# 3. INITIALIZE GEMINI CLIENT & SHARED MULTIPLAYER STORE
# =====================================================

client = genai.Client(api_key=GEMINI_API_KEY)

@st.cache_resource
def get_shared_mabar_rooms() -> dict:
    """
    Penyimpanan bersama di memori server agar pemain dari perangkat berbeda (HP/Laptop lain)
    yang masuk ke Kode Room yang sama mendapatkan paket soal yang sama dan saling melihat skor.
    """
    return {}

SHARED_ROOMS = get_shared_mabar_rooms()

# =====================================================
# 4. CONSTANTS, CATALOGS & VERIFIED SOURCES
# =====================================================

THEMES = {
    "Emerald & Mint": {
        "primary": "#0D9488",
        "secondary": "#0F766E",
        "accent": "#2DD4BF",
        "bg_soft": "#F0FDFA",
        "bg_tint": "#CCFBF1",
        "border": "#99F6E4",
        "text": "#0F172A",
        "muted": "#475569"
    },
    "Royal Indigo": {
        "primary": "#4F46E5",
        "secondary": "#3730A3",
        "accent": "#818CF8",
        "bg_soft": "#EEF2FF",
        "bg_tint": "#E0E7FF",
        "border": "#C7D2FE",
        "text": "#0F172A",
        "muted": "#475569"
    },
    "Warm Amber": {
        "primary": "#D97706",
        "secondary": "#B45309",
        "accent": "#FBBF24",
        "bg_soft": "#FFFBEB",
        "bg_tint": "#FEF3C7",
        "border": "#FDE68A",
        "text": "#0F172A",
        "muted": "#475569"
    },
    "Berry Rose": {
        "primary": "#DB2777",
        "secondary": "#9D174D",
        "accent": "#F472B6",
        "bg_soft": "#FDF2F8",
        "bg_tint": "#FCE7F3",
        "border": "#FBCFE8",
        "text": "#0F172A",
        "muted": "#475569"
    }
}

CUTE_AVATARS = {
    "Rubah Cerdas": "🦊",
    "Panda Santai": "🐼",
    "Kucing Akuntan": "🐱",
    "Burung Hantu Analis": "🦉",
    "Katak Ceria": "🐸",
    "Penguin Auditor": "🐧"
}

VERIFIED_SOURCES = [
    {"name": "Ikatan Akuntan Indonesia (IAI)", "url": "https://web.iai.id/"},
    {"name": "IFRS Foundation", "url": "https://www.ifrs.org/"},
    {"name": "Komite Standar Akuntansi Pemerintahan (KSAP)", "url": "https://www.ksap.org/"},
    {"name": "Badan Pemeriksa Keuangan RI (BPK)", "url": "https://www.bpk.go.id/"},
    {"name": "JDIH Kemendagri (Keuangan Desa & Daerah)", "url": "https://jdih.kemendagri.go.id/"},
    {"name": "JDIH LKPP (Pengadaan Barang/Jasa)", "url": "https://jdih.lkpp.go.id/"},
    {"name": "IPSASB (Public Sector Accounting)", "url": "https://www.ipsasb.org/"},
    {"name": "Bank Indonesia (Kebijakan & Fintech)", "url": "https://www.bi.go.id/"}
]

MATERI_DETAILS = {
    "Pengantar Akuntansi 1": {
        "ringkasan": "Persamaan dasar akuntansi, aturan debit-kredit, siklus akuntansi perusahaan jasa & dagang, jurnal umum, buku besar, neraca saldo, ayat jurnal penyesuaian, hingga penyusunan laporan keuangan dasar.",
        "poin_kunci": "Aset = Liabilitas + Ekuitas, basis akrual vs kas, jurnal penyesuaian (akrual & deferal), dan kertas kerja.",
        "contoh": "Membeli peralatan kantor tunai menambah Aset (Peralatan) dan mengurangi Aset (Kas) dengan jumlah yang sama."
    },
    "Pengantar Akuntansi 2": {
        "ringkasan": "Jurnal khusus, sistem pencatatan persediaan periodik & perpetual, metode penilaian persediaan (FIFO/rata-rata), kas kecil, piutang tak tertagih, aset tetap, dan jurnal penutup.",
        "poin_kunci": "FIFO vs rata-rata tertimbang, penyusutan aset tetap, cadangan kerugian piutang, dan penutupan akun nominal.",
        "contoh": "Menjual barang dagang secara kredit mencatat Piutang Usaha di debit dan Penjualan di kredit."
    },
    "Akuntansi Keuangan Menengah": {
        "ringkasan": "Pengakuan, pengukuran, penyajian, dan pengungkapan pos laporan keuangan utama: kas & setara kas, piutang, persediaan, aset tetap, aset tak berwujud, liabilitas jangka panjang, dan ekuitas.",
        "poin_kunci": "Biaya perolehan vs nilai realisasi neto/nilai wajar, penurunan nilai (impairment), obligasi & amortisasi, serta ekuitas.",
        "contoh": "Mengukur persediaan pada nilai yang lebih rendah antara biaya perolehan dan nilai realisasi neto."
    },
    "Akuntansi Keuangan Lanjutan": {
        "ringkasan": "Persekutuan, penjualan konsinyasi, penjualan cicilan, kantor cabang, kombinasi bisnis, transaksi mata uang asing, dan penyusunan laporan keuangan konsolidasian.",
        "poin_kunci": "Eliminasi saldo resiprokal, kepentingan nonpengendali (NCI), goodwill, dan konsolidasi entitas induk & anak.",
        "contoh": "Mengeliminasi investasi entitas induk pada entitas anak beserta ekuitas anak saat menyusun laporan konsolidasi."
    },
    "Analisis Laporan Keuangan": {
        "ringkasan": "Teknik membaca dan mengevaluasi kondisi keuangan serta kinerja entitas melalui analisis horizontal (tren), vertikal (common size), rasio keuangan, dan arus kas.",
        "poin_kunci": "Rasio likuiditas (current ratio, quick ratio), solvabilitas (DER), profitabilitas (ROA, ROE, GPM/NPM), aktivitas, dan analisis tren.",
        "contoh": "Membandingkan Current Ratio dan Debt to Equity Ratio antarperiode untuk menilai kemampuan bayar jangka pendek dan struktur modal."
    },
    "Laporan Keuangan Daerah": {
        "ringkasan": "Laporan pertanggungjawaban pelaksanaan APBD pemerintah daerah berbasis Standar Akuntansi Pemerintahan (SAP) yang terdiri dari 7 komponen utama laporan keuangan daerah.",
        "poin_kunci": "LRA, Laporan Perubahan SAL, Neraca, Laporan Operasional (LO), Laporan Arus Kas (LAK), Laporan Perubahan Ekuitas (LPE), dan Catatan atas Laporan Keuangan (CaLK).",
        "contoh": "Menyajikan realisasi pendapatan daerah dan belanja daerah pada LRA sekaligus beban akrual serta surplus/defisit LO pada Laporan Operasional."
    },
    "Laporan Keuangan Desa": {
        "ringkasan": "Laporan pertanggungjawaban pengelolaan keuangan desa atas APBDes (Dana Desa, ADD, PADes, dan bantuan keuangan) yang disusun oleh Kepala Desa dan disampaikan secara berkala.",
        "poin_kunci": "Laporan Realisasi Pelaksanaan APBDes (awal semester & akhir tahun), Laporan Pertanggungjawaban Realisasi APBDes, Buku Kas Umum, dan Catatan/Lampiran.",
        "contoh": "Melaporkan anggaran, realisasi, serta selisih lebih/kurang belanja pembangunan dan pemberdayaan masyarakat desa per kegiatan."
    },
    "Laporan Keuangan Lainnya (Entitas Bisnis, Nirlaba, Konsolidasian & EMKM)": {
        "ringkasan": "Beragam bentuk laporan keuangan sesuai karakteristik entitas: laporan laba rugi & penghasilan komprehensif lain, posisi keuangan, perubahan ekuitas, arus kas, laporan entitas nirlaba/berorientasi nonlaba, dan laporan berbasis SAK EMKM.",
        "poin_kunci": "Komponen laporan keuangan komersial, penghasilan komprehensif lain (OCI), laporan entitas nirlaba (penghasilan & beban, posisi keuangan, arus kas), serta laporan ringkas UMKM/EMKM.",
        "contoh": "Entitas nirlaba menyajikan klasifikasi aset neto/ekuitas tanpa pembatasan dan dengan pembatasan pemberi sumber daya, sedangkan UMKM dapat memakai format laporan sesuai SAK EMKM."
    },
    "Akuntansi Keuangan Desa": {
        "ringkasan": "Pengelolaan keuangan desa mulai dari perencanaan (APBDes), pelaksanaan, penatausahaan, pelaporan, hingga pertanggungjawaban atas Dana Desa, ADD, PADes, dan bantuan keuangan.",
        "poin_kunci": "APBDes, Buku Kas Umum (BKU), buku pembantu bank/pajak, Laporan Realisasi APBDes, dan pertanggungjawaban.",
        "contoh": "Mencatat pencairan dan realisasi belanja kegiatan pembangunan jalan desa sesuai pos anggaran pada APBDes."
    },
    "Manajemen Biaya & Akuntansi Manajemen": {
        "ringkasan": "Klasifikasi biaya, job order & process costing, Activity-Based Costing (ABC), analisis biaya-volume-laba (CVP/BEP), anggaran, dan pengambilan keputusan taktis.",
        "poin_kunci": "Biaya tetap vs variabel, biaya langsung vs tidak langsung, Break-Even Point (BEP), analisis varians, dan relevan costing.",
        "contoh": "Menghitung BEP unit untuk mengetahui batas minimal penjualan agar operasi tidak mengalami kerugian."
    },
    "Akuntansi Sektor Publik": {
        "ringkasan": "Penganggaran, akuntansi dana, penilaian kinerja, dan akuntabilitas pada organisasi nirlaba serta entitas publik seperti yayasan, rumah sakit publik, dan lembaga sosial.",
        "poin_kunci": "Value for Money (ekonomi, efisiensi, efektivitas), akuntansi dana, anggaran berbasis kinerja, dan transparansi.",
        "contoh": "Menilai efisiensi program layanan publik dengan membandingkan realisasi output terhadap biaya yang diserap."
    },
    "Akuntansi Pemerintahan": {
        "ringkasan": "Standar Akuntansi Pemerintahan (SAP) berbasis akrual untuk pemerintah pusat dan daerah, mencakup LRA, LO, neraca, Laporan Arus Kas, dan jurnal finansial serta anggaran.",
        "poin_kunci": "Laporan Realisasi Anggaran (LRA), Laporan Operasional (LO), jurnal finansial vs jurnal anggaran, dan ekuitas SAL.",
        "contoh": "Mencatat beban pegawai akrual pada LO sekaligus mencatat realisasi belanja pada LRA sesuai ketentuan SAP."
    },
    "Komputer Akuntansi 1": {
        "ringkasan": "Setup perusahaan, perancangan Chart of Accounts (COA), saldo awal, pencatatan transaksi jasa/dagang, rekonsiliasi, dan pelaporan keuangan berbasis aplikasi.",
        "poin_kunci": "Struktur kode akun, linked accounts, transaksi kas/bank/piutang/utang, dan validasi neraca saldo.",
        "contoh": "Mengatur akun penampung otomatis (linked accounts) agar penjualan dan piutang terposting ke buku besar."
    },
    "Komputer Akuntansi 2": {
        "ringkasan": "Pengelolaan persediaan multi-gudang/manufaktur, jadwal penyusutan aset tetap otomatis, pencatatan pajak/rekonsiliasi, audit log, dan analisis laporan keuangan sistem.",
        "poin_kunci": "Kartu stok/BOM, depresiasi otomatis, rekonsiliasi saldo modul dengan buku besar, dan kontrol akses.",
        "contoh": "Menjalankan proses penyusutan aset tetap bulanan dan memeriksa kesesuaian saldo dengan buku besar."
    },
    "Pengadaan Barang dan Jasa": {
        "ringkasan": "Prinsip, etika, perencanaan, pemilihan penyedia, kontrak, serah terima pekerjaan, serta dokumentasi pembayaran dan akuntabilitas pengadaan barang/jasa.",
        "poin_kunci": "Kesesuaian spesifikasi & pagu/HPS, transparansi & persaingan sehat, administrasi kontrak, dan bukti serah terima sah.",
        "contoh": "Memverifikasi berita acara serah terima barang, kontrak, dan bukti pajak sebelum pencairan pembayaran."
    },
    "Audit Organisasi Publik": {
        "ringkasan": "Pemeriksaan independen dan sistematis atas keuangan, kinerja, dan kepatuhan organisasi sektor publik/pemerintahan beserta penyusunan temuan dan rekomendasi.",
        "poin_kunci": "Audit keuangan, audit kinerja, audit kepatuhan, bukti audit cukup & tepat, dan unsur temuan (kondisi, kriteria, sebab, akibat).",
        "contoh": "Menguji kepatuhan penyaluran dan pertanggungjawaban bantuan/hibah terhadap aturan dan bukti pendukung."
    },
    "Sistem Informasi Akuntansi & Manajemen": {
        "ringkasan": "Perancangan, pengendalian internal, siklus transaksi (pendapatan, pengeluaran, produksi, penggajian), dan pemanfaatan sistem informasi untuk keputusan manajerial.",
        "poin_kunci": "Pemisahan fungsi (segregation of duties), pengendalian input/proses/output, dokumen sumber, dan pelaporan manajemen.",
        "contoh": "Memisahkan fungsi penyetuju pembelian, penerima barang, dan pencatat utang untuk menjaga pengendalian internal."
    },
    "Akuntansi Digital": {
        "ringkasan": "Pemanfaatan cloud accounting, otomatisasi jurnal, e-invoicing, big data, dan AI dalam mempercepat pencatatan, rekonsiliasi, serta analisis keuangan.",
        "poin_kunci": "Digitalisasi bukti transaksi, integrasi data real-time, keamanan siber & integritas data, serta analitik keuangan.",
        "contoh": "Merekonsiliasi transaksi e-invoice dan mutasi digital secara otomatis untuk mempercepat penutupan buku."
    },
    "Teknologi Keuangan (Fintech)": {
        "ringkasan": "Ekosistem pembayaran digital, e-wallet, pinjaman digital, open banking, serta pencatatan akuntansi, manajemen risiko, dan kepatuhan regulasi fintech.",
        "poin_kunci": "Alur settlement dana, pencatatan biaya transaksi/potongan gateway, risiko likuiditas & siber, serta perlindungan data.",
        "contoh": "Mencatat penjualan bruto, potongan biaya layanan payment gateway, dan dana bersih yang masuk ke rekening."
    },
    "Standar Nasional & Internasional (PSAK, SAK EMKM, SAP, IFRS, IPSAS)": {
        "ringkasan": "Perbandingan dan penerapan PSAK/IAI, SAK EMKM, SAP (pemerintah), IFRS (bisnis global), dan IPSAS (sektor publik internasional).",
        "poin_kunci": "Kesesuaian standar dengan karakteristik entitas, pengukuran & pengakuan, pengungkapan, dan konvergensi standar.",
        "contoh": "Menerapkan SAK EMKM untuk entitas mikro/kecil yang memenuhi kriteria dan membutuhkan laporan keuangan sederhana."
    }
}

MATERI_AKUNTANSI = list(MATERI_DETAILS.keys())

ENGLISH_TERMS_BANK = [
    {
        "term": "Accrual Basis",
        "id_meaning": "Basis Akrual",
        "explanation": "Pendapatan dan beban diakui saat transaksi terjadi, bukan saat kas diterima atau dibayar.",
        "example": "Recording utility expense incurred in November even if paid in December."
    },
    {
        "term": "Depreciation",
        "id_meaning": "Penyusutan / Depresiasi",
        "explanation": "Alokasi sistematis biaya perolehan aset tetap berwujud selama masa manfaatnya.",
        "example": "Straight-line depreciation reduces equipment carrying amount each period."
    },
    {
        "term": "Liquidity Ratio",
        "id_meaning": "Rasio Likuiditas",
        "explanation": "Kemampuan entitas memenuhi kewajiban jangka pendek menggunakan aset lancar.",
        "example": "Current Ratio = Current Assets / Current Liabilities."
    },
    {
        "term": "Audit Trail",
        "id_meaning": "Jejak Audit",
        "explanation": "Catatan kronologis bukti transaksi dari dokumen sumber hingga buku besar dan laporan.",
        "example": "Every journal adjustment must leave a clear audit trail."
    },
    {
        "term": "Fund Accounting",
        "id_meaning": "Akuntansi Dana",
        "explanation": "Sistem akuntansi pada sektor publik/nirlaba yang memisahkan dana sesuai tujuan atau aturan.",
        "example": "Separating village capital expenditure funds from operational funds."
    },
    {
        "term": "Variance Analysis",
        "id_meaning": "Analisis Varians",
        "explanation": "Perbandingan antara anggaran (budget) dan realisasi (actual) untuk mengevaluasi kinerja.",
        "example": "Favorable vs. unfavorable cost variance in budget control."
    }
]

# =====================================================
# 5. HELPER FUNCTIONS
# =====================================================

def clean_ai_text(text: str) -> str:
    """Membersihkan tanda ** dan # di awal baris agar teks rapi tanpa merusak tabel Markdown."""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        cleaned = line.replace("**", "").replace("__", "")
        stripped = cleaned.lstrip()
        if not stripped.startswith("|") and stripped.startswith("#"):
            parts = stripped.split(" ", 1)
            cleaned = parts[1] if len(parts) > 1 else stripped.lstrip("#").strip()
        lines.append(cleaned)
    return "\n".join(lines).strip()


def evaluate_streak_status(last_played_str: str | None, current_streak: int) -> tuple[int, bool]:
    today = date.today()
    if not last_played_str:
        return 0, False
    try:
        last_dt = date.fromisoformat(last_played_str)
    except ValueError:
        return 0, False

    diff_days = (today - last_dt).days
    if diff_days in (0, 1):
        return max(1, current_streak), True
    return 0, False


def record_daily_play():
    today = date.today()
    last_str = st.session_state.user_profile.get("last_played_date")
    streak = st.session_state.user_profile.get("streak_days", 0)

    if last_str == today.isoformat():
        st.session_state.user_profile["streak_days"] = max(1, streak)
        st.session_state.user_profile["flame_alive"] = True
        return

    if last_str:
        try:
            last_dt = date.fromisoformat(last_str)
            streak = (streak + 1) if (today - last_dt).days == 1 else 1
        except ValueError:
            streak = 1
    else:
        streak = 1

    st.session_state.user_profile["streak_days"] = streak
    st.session_state.user_profile["last_played_date"] = today.isoformat()
    st.session_state.user_profile["flame_alive"] = True


def resolve_active_gemini_models() -> list[str]:
    """Mendapatkan model aktif yang tersedia di akun/API dengan prioritas gemini-2.5-flash."""
    preferred = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-2.0-flash"]
    discovered = []
    try:
        for m in client.models.list():
            m_name = getattr(m, "name", "") or ""
            short_name = m_name.replace("models/", "")
            if short_name and short_name not in discovered:
                discovered.append(short_name)
    except Exception:
        pass

    ordered = []
    for p in preferred:
        if p in discovered and p not in ordered:
            ordered.append(p)
    for p in preferred:
        if p not in ordered:
            ordered.append(p)
    for d in discovered:
        if ("flash" in d or "pro" in d) and d not in ordered:
            ordered.append(d)
    return ordered[:5]


def pick_relevant_sources(query_text: str) -> list[dict]:
    q = (query_text or "").lower()
    chosen = []

    def add_src(idx: int):
        src = VERIFIED_SOURCES[idx]
        if src not in chosen:
            chosen.append(src)

    if any(k in q for k in ["desa", "apbdes", "daerah", "bupati", "kelurahan", "kemendagri"]):
        add_src(4)
        add_src(2)
    if any(k in q for k in ["pemerintah", "sap", "lra", "lo", "apbn", "apbd", "ksap"]):
        add_src(2)
        add_src(3)
    if any(k in q for k in ["audit", "temuan", "pemeriksaan", "bpk", "pengendalian"]):
        add_src(3)
        add_src(6)
    if any(k in q for k in ["pengadaan", "tender", "penyedia", "kontrak", "lkpp"]):
        add_src(5)
        add_src(3)
    if any(k in q for k in ["ifrs", "konsolidasi", "instrumen", "internasional"]):
        add_src(1)
        add_src(0)
    if any(k in q for k in ["fintech", "pembayaran", "bank", "digital", "e-wallet", "bi"]):
        add_src(7)
        add_src(0)
    if any(k in q for k in ["sektor publik", "nirlaba", "ipsas"]):
        add_src(6)
        add_src(2)

    if not chosen:
        add_src(0)
        add_src(1)

    return chosen[:3]


def ask_prof_gemini(question: str, nickname: str, jenjang: str, bahasa: str) -> tuple[str, list[dict], str | None]:
    prompt = f"""
Kamu adalah "Prof", mentor akuntansi yang ramah, seru, jelas, dan penjelasannya sangat mudah dipahami untuk jenjang "{jenjang}".
Sapa pengguna dengan nama panggilan "{nickname}" secara santai dan akrab.
Gunakan bahasa "{bahasa}".

Jawab pertanyaan ini secara langsung, tepat sasaran, dan lengkap:
"{question}"

Aturan:
1. Jawab tepat sesuai isi pertanyaan "{question}" (jangan memberi jawaban umum yang tidak nyambung dengan pertanyaan).
2. Jika pertanyaan terbantu dengan perbandingan, klasifikasi, contoh jurnal/perhitungan, atau komponen, sertakan tabel Markdown yang rapi pada baris terpisah (menggunakan '|' dan '---').
3. Sertakan bagian "Sumber Rujukan" di akhir jawaban menggunakan URL resmi yang valid dan bisa diakses (misalnya IAI: https://web.iai.id/ , IFRS: https://www.ifrs.org/ , KSAP: https://www.ksap.org/ , BPK: https://www.bpk.go.id/ , JDIH Kemendagri: https://jdih.kemendagri.go.id/ , LKPP: https://jdih.lkpp.go.id/).
4. Jangan gunakan tanda ** atau # di awal judul.
"""
    models_to_try = resolve_active_gemini_models()
    last_err = None

    for model_id in models_to_try:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                raw_text = (response.text or "").strip()
                if raw_text:
                    cleaned = clean_ai_text(raw_text)
                    if "http" not in cleaned:
                        srcs = pick_relevant_sources(question)
                        src_lines = "\n".join([f"- {s['name']}: {s['url']}" for s in srcs])
                        cleaned = f"{cleaned}\n\nSumber Rujukan:\n{src_lines}"

                    table_rows = [
                        {
                            "Pertanyaan / Topik": question[:65],
                            "Fokus Pembahasan": "Pengertian, mekanisme/pencatatan, dan contoh sesuai konteks",
                            "Acuan Standar / Sumber": "IAI (https://web.iai.id/) / IFRS (https://www.ifrs.org/)"
                        }
                    ]
                    return cleaned, table_rows, None
            except Exception as e:
                last_err = str(e)
                if ("503" in last_err or "UNAVAILABLE" in last_err or "429" in last_err) and attempt == 0:
                    time.sleep(1.2)
                    continue
                break

    return "", [], last_err


def generate_quiz_batch(topic: str, jenjang: str, bahasa: str, count: int, seed_offset: int = 0) -> list[dict]:
    prompt = f"""
Buatlah tepat {count} soal pilihan ganda berkualitas tentang "{topic}" untuk jenjang "{jenjang}" dalam bahasa "{bahasa}".
Aturan penting:
1. Setiap soal memiliki 4 pilihan jawaban (tanpa awalan huruf/simbol di dalam teks opsi).
2. Letakkan jawaban yang benar di posisi indeks acak (0, 1, 2, atau 3) — jangan selalu di indeks 0.
3. Sertakan penjelasan singkat, jelas, dan mudah dipahami.
4. Kembalikan HANYA JSON valid dengan format list of objects:
[
  {{
    "question": "Pertanyaan...",
    "options": ["Opsi 1", "Opsi 2", "Opsi 3", "Opsi 4"],
    "correct_index": 2,
    "explanation": "Penjelasan..."
  }}
]
Seed variasi: {seed_offset}-{random.randint(1000, 9999)}
"""
    questions = []
    for model_id in resolve_active_gemini_models():
        try:
            response = client.models.generate_content(
                model=model_id,
                contents=prompt
            )
            txt = (response.text or "").strip()
            if "```" in txt:
                for p in txt.split("```"):
                    p_clean = p.strip()
                    if p_clean.startswith("json"):
                        p_clean = p_clean[4:].strip()
                    if p_clean.startswith("["):
                        txt = p_clean
                        break
            parsed = json.loads(txt)
            if isinstance(parsed, list):
                for item in parsed:
                    opts = item.get("options", [])
                    if not isinstance(opts, list) or len(opts) != 4:
                        continue
                    opts = [clean_ai_text(str(o)) for o in opts]
                    corr_idx = int(item.get("correct_index", 0))
                    if corr_idx < 0 or corr_idx > 3:
                        corr_idx = 0

                    correct_text = opts[corr_idx]
                    shuffled_opts = opts[:]
                    random.shuffle(shuffled_opts)

                    questions.append({
                        "question": clean_ai_text(str(item.get("question", "Soal Akuntansi"))),
                        "options": shuffled_opts,
                        "correct_index": shuffled_opts.index(correct_text),
                        "explanation": clean_ai_text(str(item.get("explanation", "Penjelasan konsep akuntansi.")))
                    })
            if questions:
                break
        except Exception:
            continue

    fallback_templates = [
        (
            f"Dalam konteks {topic} untuk {jenjang}, prinsip utama yang menjaga keandalan informasi keuangan adalah...",
            ["Penyajian jujur dan dapat diverifikasi", "Memilih angka paling menguntungkan saja", "Mengabaikan bukti transaksi kecil", "Menunda pencatatan hingga akhir tahun"],
            0,
            f"Pada {topic}, informasi yang andal harus mencerminkan substansi ekonomi secara jujur dan didukung bukti yang dapat diverifikasi."
        ),
        (
            f"Apa fungsi utama pengendalian internal dalam topik {topic}?",
            ["Mempercepat penghapusan catatan", "Melindungi aset dan mencegah kekeliruan atau kecurangan", "Menghilangkan kebutuhan rekonsiliasi", "Menyamakan seluruh tarif pajak"],
            1,
            "Pengendalian internal dirancang untuk mengamankan aset, menjaga keakuratan data, dan mendorong kepatuhan prosedur."
        ),
        (
            f"Ketika terjadi selisih antara catatan dan realisasi pada {topic}, langkah analitis pertama yang tepat adalah...",
            ["Menghapus baris yang berselisih", "Menelusuri dokumen sumber dan waktu pencatatan", "Mengubah saldo awal secara sepihak", "Mengabaikan selisih tanpa catatan"],
            1,
            "Penelusuran ke dokumen sumber serta ketepatan periode/klasifikasi membantu menemukan akar penyebab selisih secara akurat."
        ),
        (
            f"Mengapa dokumentasi dan pelaporan transparan penting dalam {topic}?",
            ["Agar laporan sulit dipahami pihak luar", "Mendukung akuntabilitas dan pengambilan keputusan", "Mengurangi tanggung jawab pengelola", "Menggantikan verifikasi bukti"],
            1,
            "Transparansi dan dokumentasi yang rapi memperkuat akuntabilitas serta menjadi dasar keputusan yang terukur."
        )
    ]

    idx = 0
    while len(questions) < count:
        q_txt, base_opts, corr_i, exp_txt = fallback_templates[idx % len(fallback_templates)]
        correct_ans = base_opts[corr_i]
        opts_copy = base_opts[:]
        random.shuffle(opts_copy)
        questions.append({
            "question": f"[{topic} #{seed_offset + len(questions) + 1}] {q_txt}",
            "options": opts_copy,
            "correct_index": opts_copy.index(correct_ans),
            "explanation": exp_txt
        })
        idx += 1

    return questions[:count]


# =====================================================
# 6. SESSION STATE INITIALIZATION
# =====================================================

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {
        "nickname": "Sobat Jurnal",
        "email": "sobat.akuntansi@contoh.id",
        "jenjang": "Mahasiswa/i",
        "bahasa": "Bahasa Indonesia",
        "tema": "Emerald & Mint",
        "avatar_name": "Rubah Cerdas",
        "custom_avatar_bytes": None,
        "streak_days": 1,
        "last_played_date": date.today().isoformat(),
        "flame_alive": True,
        "email_notif": True,
        "total_xp": 120
    }

streak_now, flame_now = evaluate_streak_status(
    st.session_state.user_profile.get("last_played_date"),
    st.session_state.user_profile.get("streak_days", 0)
)
st.session_state.user_profile["streak_days"] = streak_now
st.session_state.user_profile["flame_alive"] = flame_now

if "prof_messages" not in st.session_state:
    st.session_state.prof_messages = [
        {
            "role": "assistant",
            "content": (
                "Halo! Prof di sini siap nemenin kamu diskusi akuntansi dengan santai, jelas, "
                "pakai tabel kalau perlu, dan lengkap dengan sumber rujukan yang bisa kamu cek sendiri. "
                "Mau tanya apa hari ini?"
            ),
            "table_data": []
        }
    ]

if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = {
        "active": False,
        "finished": False,
        "topic": MATERI_AKUNTANSI[0],
        "jenjang": "Mahasiswa/i",
        "total_questions": 10,
        "questions": [],
        "current_idx": 0,
        "score": 0,
        "answers_log": [],
        "q_start_ts": None
    }

if "mabar_client" not in st.session_state:
    qp_room = st.query_params.get("room", "")
    st.session_state.mabar_client = {
        "active_room": str(qp_room).strip().upper(),
        "q_index": 0,
        "round_start_ts": None,
        "history": []
    }

if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "materi_deep_read" not in st.session_state:
    st.session_state.materi_deep_read = {}


# =====================================================
# 7. MODERN UI POLISH (CSS)
# =====================================================

t = THEMES.get(st.session_state.user_profile.get("tema", "Emerald & Mint"), THEMES["Emerald & Mint"])

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', sans-serif;
    }}

    .stApp {{
        background:
            radial-gradient(circle at 12% 8%, {t["bg_tint"]} 0%, transparent 38%),
            radial-gradient(circle at 90% 12%, {t["bg_soft"]} 0%, transparent 42%),
            #F8FAFC;
        color: {t["text"]};
    }}

    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 1220px;
    }}

    .fq-hero {{
        background: linear-gradient(135deg, {t["secondary"]} 0%, {t["primary"]} 58%, {t["accent"]} 135%);
        color: #FFFFFF;
        border-radius: 22px;
        padding: 24px 28px;
        margin-bottom: 18px;
        box-shadow: 0 14px 30px -10px rgba(15, 23, 42, 0.22);
        border: 1px solid rgba(255, 255, 255, 0.22);
    }}
    .fq-hero h1 {{
        margin: 0 0 6px 0;
        font-size: 1.65rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }}
    .fq-hero p {{
        margin: 0;
        font-size: 0.95rem;
        color: rgba(255, 255, 255, 0.92);
    }}
    .fq-pills {{
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }}
    .fq-pill {{
        background: rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(8px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #FFFFFF;
        padding: 5px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 600;
    }}

    .fq-card {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid {t["primary"]};
        border-radius: 18px;
        padding: 18px 22px;
        margin: 12px 0 16px 0;
        box-shadow: 0 8px 24px -12px rgba(15, 23, 42, 0.08);
    }}
    .fq-card h4 {{
        margin: 0 0 6px 0;
        color: {t["text"]};
        font-weight: 700;
        line-height: 1.45;
    }}
    .fq-card p {{
        margin: 0;
        color: {t["muted"]};
        font-size: 0.92rem;
    }}

    .fq-flame-alive {{
        background: linear-gradient(135deg, #FFF7ED, #FFEDD5);
        border: 1.5px solid #FDBA74;
        color: #9A3412;
        border-radius: 16px;
        padding: 12px 14px;
        margin: 10px 0 14px 0;
        font-weight: 600;
    }}
    .fq-flame-dead {{
        background: #F1F5F9;
        border: 1.5px solid #CBD5E1;
        color: #475569;
        border-radius: 16px;
        padding: 12px 14px;
        margin: 10px 0 14px 0;
        font-weight: 600;
    }}

    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background: #FFFFFF;
        padding: 8px;
        border-radius: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 14px -8px rgba(15, 23, 42, 0.08);
        flex-wrap: wrap;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 12px;
        padding: 8px 14px;
        font-weight: 600;
        font-size: 0.88rem;
        color: {t["muted"]};
        border: none !important;
    }}
    .stTabs [aria-selected="true"] {{
        background: {t["bg_soft"]} !important;
        color: {t["secondary"]} !important;
        font-weight: 700 !important;
    }}

    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, {t["primary"]}, {t["secondary"]});
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        padding: 0.55rem 1.2rem;
        font-weight: 700;
        box-shadow: 0 8px 18px -8px {t["primary"]};
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px);
        box-shadow: 0 12px 22px -8px {t["primary"]};
    }}
    .stButton > button {{
        border-radius: 12px;
        font-weight: 600;
    }}

    [data-testid="stMetric"] {{
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 12px 16px;
        box-shadow: 0 4px 14px -10px rgba(15, 23, 42, 0.08);
    }}

    [data-testid="stDataFrame"] {{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #E2E8F0;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 8. SIDEBAR — PROFIL, API HARIAN & PENGATURAN
# =====================================================

profile = st.session_state.user_profile

with st.sidebar:
    av_emoji = CUTE_AVATARS.get(profile.get("avatar_name", "Rubah Cerdas"), "🦊")

    st.markdown("### Profil & Api Harian")
    col_av1, col_av2 = st.columns([1, 2])
    with col_av1:
        if profile.get("custom_avatar_bytes"):
            st.image(profile["custom_avatar_bytes"], width=72)
        else:
            st.markdown(
                f"<div style='font-size:48px; background:{t['bg_soft']}; border:1.5px solid {t['border']}; "
                f"border-radius:16px; width:72px; height:72px; display:flex; align-items:center; justify-content:center;'>"
                f"{av_emoji}</div>",
                unsafe_allow_html=True
            )
    with col_av2:
        st.markdown(f"**{profile['nickname']}**")
        st.caption(f"{profile['jenjang']} • {profile['total_xp']} XP")
        st.caption(f"{profile['email']}")

    if profile["flame_alive"] and profile["streak_days"] > 0:
        st.markdown(
            f"<div class='fq-flame-alive'>🔥 Api Hidup: {profile['streak_days']} Hari<br>"
            f"<span style='font-size:0.8rem; font-weight:500;'>Mainkan setiap hari agar apinya tetap menyala!</span></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='fq-flame-dead'>🩶 Api Mati (0 Hari)<br>"
            "<span style='font-size:0.8rem; font-weight:500;'>Selesaikan 1 kuis atau diskusi hari ini untuk menyalakan api.</span></div>",
            unsafe_allow_html=True
        )

    with st.expander("Ubah Profil, Avatar & Tema", expanded=False):
        new_nick = st.text_input("Nama Panggilan", value=profile["nickname"])
        new_email = st.text_input("Email Notifikasi", value=profile["email"])
        new_jenjang = st.selectbox(
            "Jenjang",
            ["Siswa", "Mahasiswa/i"],
            index=0 if profile["jenjang"] == "Siswa" else 1
        )
        new_bahasa = st.selectbox(
            "Bahasa Sistem",
            ["Bahasa Indonesia", "English"],
            index=0 if profile["bahasa"] == "Bahasa Indonesia" else 1
        )
        new_tema = st.selectbox(
            "Tema Warna",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(profile["tema"]) if profile["tema"] in THEMES else 0
        )
        new_avatar = st.selectbox(
            "Avatar Lucu Gratis",
            list(CUTE_AVATARS.keys()),
            index=list(CUTE_AVATARS.keys()).index(profile["avatar_name"]) if profile["avatar_name"] in CUTE_AVATARS else 0
        )
        uploaded_photo = st.file_uploader("Unggah Foto Profil (Opsional)", type=["png", "jpg", "jpeg"])
        use_custom_photo = st.checkbox(
            "Gunakan foto unggahan",
            value=bool(profile.get("custom_avatar_bytes"))
        )
        notif_opt = st.checkbox("Notifikasi ringkasan ke email", value=profile.get("email_notif", True))

        if st.button("Simpan Perubahan", type="primary"):
            profile["nickname"] = new_nick.strip() or "Sobat Jurnal"
            profile["email"] = new_email.strip() or "sobat.akuntansi@contoh.id"
            profile["jenjang"] = new_jenjang
            profile["bahasa"] = new_bahasa
            profile["tema"] = new_tema
            profile["avatar_name"] = new_avatar
            profile["email_notif"] = notif_opt
            if uploaded_photo is not None:
                profile["custom_avatar_bytes"] = uploaded_photo.getvalue()
            elif not use_custom_photo:
                profile["custom_avatar_bytes"] = None
            st.success("Pengaturan tersimpan!")
            st.rerun()

    st.caption(f"Cakupan: {len(MATERI_AKUNTANSI)} materi akuntansi nasional & internasional.")


# =====================================================
# 9. HERO HEADER
# =====================================================

flame_text = f"🔥 Api {profile['streak_days']} Hari" if profile["flame_alive"] else "🩶 Api Mati"

st.markdown(
    f"""
    <div class='fq-hero'>
        <h1>FinQuest AI — Accounting Quiz & Learning Hub</h1>
        <p>Kuis 1–100 soal, diskusi bareng Prof dengan tabel & sumber valid, serta mabar real-time lintas perangkat.</p>
        <div class='fq-pills'>
            <span class='fq-pill'>👤 {profile['nickname']}</span>
            <span class='fq-pill'>🎓 {profile['jenjang']}</span>
            <span class='fq-pill'>🌐 {profile['bahasa']}</span>
            <span class='fq-pill'>{flame_text}</span>
            <span class='fq-pill'>⭐ {profile['total_xp']} XP</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 10. MAIN NAVIGATION TABS
# =====================================================

tab_quiz, tab_prof, tab_mabar, tab_english, tab_tugas, tab_materi = st.tabs([
    "🎯 Kuis (1–100 Soal)",
    "👨‍🏫 Ruang Prof",
    "🤝 Mabar Lintas Perangkat",
    "🌐 English Akuntansi",
    "📚 Bantu Tugas",
    "📖 Materi & Varians"
])


# =====================================================
# TAB 1: KUIS
# =====================================================

with tab_quiz:
    st.markdown(
        "<div class='fq-card'><h4>Mode Kuis Akuntansi (60 Detik per Soal)</h4>"
        "<p>Pilih jumlah soal sampai 100 soal, jenjang Siswa atau Mahasiswa/i, dan posisi kunci jawaban yang diacak merata.</p></div>",
        unsafe_allow_html=True
    )

    qs = st.session_state.quiz_state

    col_q1, col_q2, col_q3 = st.columns([2.2, 1, 1])
    with col_q1:
        q_topic = st.selectbox("Topik Akuntansi", MATERI_AKUNTANSI, key="quiz_topic_select")
    with col_q2:
        q_jenjang = st.selectbox("Jenjang", ["Siswa", "Mahasiswa/i"], index=0 if profile["jenjang"] == "Siswa" else 1, key="quiz_jenjang_select")
    with col_q3:
        q_count = st.number_input("Jumlah Soal (1–100)", min_value=1, max_value=100, value=10, step=1, key="quiz_count_input")

    if st.button("Mulai Kuis Baru", type="primary"):
        with st.spinner(f"Menyiapkan {int(q_count)} soal {q_topic}..."):
            all_q = []
            remaining = int(q_count)
            batch_num = 0
            while remaining > 0:
                take = min(10, remaining)
                all_q.extend(generate_quiz_batch(
                    topic=q_topic,
                    jenjang=q_jenjang,
                    bahasa=profile["bahasa"],
                    count=take,
                    seed_offset=batch_num * 10
                ))
                remaining -= take
                batch_num += 1

            st.session_state.quiz_state = {
                "active": True,
                "finished": False,
                "topic": q_topic,
                "jenjang": q_jenjang,
                "total_questions": len(all_q),
                "questions": all_q,
                "current_idx": 0,
                "score": 0,
                "answers_log": [],
                "q_start_ts": datetime.now().timestamp()
            }
            record_daily_play()
            profile["total_xp"] += 15
            st.rerun()

    if qs["active"] and not qs["finished"] and qs["questions"]:
        idx = qs["current_idx"]
        q_item = qs["questions"][idx]
        elapsed = int(datetime.now().timestamp() - (qs["q_start_ts"] or datetime.now().timestamp()))
        remaining_sec = max(0, 60 - elapsed)

        st.progress((idx + 1) / qs["total_questions"])
        c_info1, c_info2, c_info3 = st.columns(3)
        c_info1.metric("Soal", f"{idx + 1} / {qs['total_questions']}")
        c_info2.metric("Skor", f"{qs['score']} Benar")
        c_info3.metric("Sisa Waktu", f"{remaining_sec} detik")

        if remaining_sec == 0:
            st.warning("Waktu 1 menit untuk soal ini telah habis.")

        st.markdown(f"<div class='fq-card'><h4>{q_item['question']}</h4></div>", unsafe_allow_html=True)

        letters = ["A", "B", "C", "D"]
        labeled_options = [f"{letters[i]}. {q_item['options'][i]}" for i in range(4)]
        chosen_label = st.radio("Pilih jawabanmu:", labeled_options, key=f"q_radio_{idx}")

        if st.button("Kirim Jawaban", type="primary"):
            chosen_idx = labeled_options.index(chosen_label)
            is_correct = (chosen_idx == q_item["correct_index"]) and (remaining_sec > 0 or chosen_idx >= 0)
            if is_correct:
                qs["score"] += 1
                profile["total_xp"] += 10

            qs["answers_log"].append({
                "No": idx + 1,
                "Pertanyaan": q_item["question"],
                "Jawaban Kamu": labeled_options[chosen_idx],
                "Kunci Jawaban": labeled_options[q_item["correct_index"]],
                "Status": "Benar" if is_correct else "Perlu Diulas",
                "Penjelasan": q_item["explanation"]
            })

            if idx + 1 < qs["total_questions"]:
                qs["current_idx"] += 1
                qs["q_start_ts"] = datetime.now().timestamp()
            else:
                qs["finished"] = True
                record_daily_play()
            st.rerun()

    elif qs["finished"]:
        total_q = qs["total_questions"]
        benar = qs["score"]
        persen = round((benar / max(1, total_q)) * 100, 1)

        st.success(f"Kuis selesai! Skor kamu: {benar}/{total_q} ({persen}%).")
        st.dataframe(pd.DataFrame(qs["answers_log"]), use_container_width=True)

        if profile.get("email_notif"):
            st.info(f"Ringkasan hasil ({benar}/{total_q} — {persen}%) disiapkan untuk dikirim ke {profile['email']}.")


# =====================================================
# TAB 2: RUANG PROF
# =====================================================

with tab_prof:
    st.markdown(
        "<div class='fq-card'><h4>Ruang Diskusi Bareng Prof</h4>"
        "<p>Tanya apa saja seputar akuntansi—Prof menjawab langsung sesuai pertanyaanmu, lengkap dengan tabel bila relevan dan sumber rujukan yang bisa diakses.</p></div>",
        unsafe_allow_html=True
    )

    for msg in st.session_state.prof_messages:
        avatar_icon = "👨‍🏫" if msg["role"] == "assistant" else (
            profile["custom_avatar_bytes"] if profile.get("custom_avatar_bytes") else CUTE_AVATARS.get(profile["avatar_name"], "🦊")
        )
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.markdown(msg["content"])
            if msg.get("table_data"):
                st.dataframe(pd.DataFrame(msg["table_data"]), use_container_width=True)

    prof_input = st.chat_input("Ketik pertanyaanmu ke Prof (misal: pembelian itu apa, laporan keuangan daerah, dll.)...")
    if prof_input:
        st.session_state.prof_messages.append({"role": "user", "content": prof_input, "table_data": []})
        with st.chat_message("user", avatar=CUTE_AVATARS.get(profile["avatar_name"], "🦊")):
            st.markdown(prof_input)

        with st.spinner("Prof sedang menyiapkan jawaban untuk pertanyaanmu..."):
            ans_text, tbl_data, err_msg = ask_prof_gemini(
                question=prof_input,
                nickname=profile["nickname"],
                jenjang=profile["jenjang"],
                bahasa=profile["bahasa"]
            )

        if ans_text:
            st.session_state.prof_messages.append({
                "role": "assistant",
                "content": ans_text,
                "table_data": tbl_data
            })
            record_daily_play()
            profile["total_xp"] += 5
            with st.chat_message("assistant", avatar="👨‍🏫"):
                st.markdown(ans_text)
                if tbl_data:
                    st.dataframe(pd.DataFrame(tbl_data), use_container_width=True)
        else:
            fail_msg = (
                f"Maaf {profile['nickname']}, Prof belum berhasil terhubung ke layanan AI saat ini. "
                f"Coba kirim ulang pertanyaannya beberapa saat lagi ya.\n\n"
                f"Sumber Rujukan:\n"
                f"- Ikatan Akuntan Indonesia (IAI): https://web.iai.id/\n"
                f"- IFRS Foundation: https://www.ifrs.org/"
            )
            st.session_state.prof_messages.append({"role": "assistant", "content": fail_msg, "table_data": []})
            with st.chat_message("assistant", avatar="👨‍🏫"):
                st.markdown(fail_msg)
            if err_msg:
                st.caption(f"Detail teknis: {err_msg}")


# =====================================================
# TAB 3: MABAR LINTAS PERANGKAT (REAL-TIME SHARED ROOM)
# =====================================================

with tab_mabar:
    st.markdown(
        "<div class='fq-card'><h4>Mabar Lintas Perangkat (HP / Laptop Berbeda)</h4>"
        "<p>1) Host membuat Room lalu membagikan Kode Room / Tautan Undangan ke teman. "
        "2) Teman membuka aplikasi ini di HP/laptop lain, memasukkan Kode Room yang sama, lalu klik Gabung Room. "
        "3) Soal yang muncul sama persis dan skor setiap perangkat langsung masuk ke papan peringkat bersama!</p></div>",
        unsafe_allow_html=True
    )

    mc = st.session_state.mabar_client
    default_code = mc["active_room"] or f"AKUN-{random.randint(100, 999)}"

    col_setup1, col_setup2 = st.columns(2)

    with col_setup1:
        st.markdown("#### A. Buat Room Baru (Host)")
        host_room_code = st.text_input("Kode Room Baru", value=default_code, key="host_room_code_inp")
        host_topic = st.selectbox("Topik Mabar", MATERI_AKUNTANSI, key="host_mabar_topic")
        host_jenjang = st.selectbox("Jenjang", ["Siswa", "Mahasiswa/i"], index=0 if profile["jenjang"] == "Siswa" else 1, key="host_mabar_jenjang")
        host_rounds = st.number_input("Jumlah Soal Mabar", min_value=3, max_value=20, value=5, step=1, key="host_mabar_rounds")

        if st.button("Buat & Masuk Room Sekarang", type="primary"):
            clean_code = "".join(c for c in host_room_code.strip().upper() if c.isalnum() or c in ("-", "_")) or "AKUN-888"
            with st.spinner(f"Membuat Room {clean_code} dan menyiapkan soal bersama..."):
                q_list = generate_quiz_batch(
                    topic=host_topic,
                    jenjang=host_jenjang,
                    bahasa=profile["bahasa"],
                    count=int(host_rounds),
                    seed_offset=sum(ord(c) for c in clean_code)
                )
                player_key = f"{profile['nickname']} ({av_emoji})"
                SHARED_ROOMS[clean_code] = {
                    "room_code": clean_code,
                    "host": player_key,
                    "topic": host_topic,
                    "jenjang": host_jenjang,
                    "created_at": datetime.now().strftime("%H:%M:%S"),
                    "questions": q_list,
                    "players": {
                        player_key: {
                            "score": 0,
                            "answered": 0,
                            "status": "Sedang Bermain",
                            "updated_at": datetime.now().strftime("%H:%M:%S")
                        }
                    }
                }
                mc["active_room"] = clean_code
                mc["q_index"] = 0
                mc["round_start_ts"] = datetime.now().timestamp()
                mc["history"] = []
                st.query_params["room"] = clean_code
                record_daily_play()
                profile["total_xp"] += 15
                st.rerun()

    with col_setup2:
        st.markdown("#### B. Gabung Room Teman (Dari Perangkat Lain)")
        join_code_inp = st.text_input(
            "Masukkan Kode Room dari Teman",
            value=str(st.query_params.get("room", mc["active_room"])).upper(),
            placeholder="Contoh: AKUN-888",
            key="join_room_code_inp"
        )
        guest_nickname = st.text_input(
            "Nama Panggilan Kamu di Room",
            value=profile["nickname"],
            key="join_guest_nick_inp"
        )

        if st.button("Gabung Room Teman", type="primary"):
            target_code = "".join(c for c in join_code_inp.strip().upper() if c.isalnum() or c in ("-", "_"))
            if not target_code or target_code not in SHARED_ROOMS:
                st.error(
                    f"Room '{target_code or '-'}' belum ditemukan. Pastikan Host sudah klik 'Buat & Masuk Room Sekarang' "
                    f"dan kode room yang dimasukkan sama persis."
                )
            else:
                if guest_nickname.strip():
                    profile["nickname"] = guest_nickname.strip()
                player_key = f"{profile['nickname']} ({av_emoji})"
                room_obj = SHARED_ROOMS[target_code]
                if player_key not in room_obj["players"]:
                    room_obj["players"][player_key] = {
                        "score": 0,
                        "answered": 0,
                        "status": "Sedang Bermain",
                        "updated_at": datetime.now().strftime("%H:%M:%S")
                    }
                mc["active_room"] = target_code
                mc["q_index"] = room_obj["players"][player_key]["answered"]
                mc["round_start_ts"] = datetime.now().timestamp()
                mc["history"] = []
                st.query_params["room"] = target_code
                record_daily_play()
                st.rerun()

        if SHARED_ROOMS:
            st.caption("Room Aktif Saat Ini:")
            for r_code, r_data in list(SHARED_ROOMS.items())[-5:]:
                st.write(f"• Kode: {r_code} — Topik: {r_data['topic']} ({len(r_data['players'])} pemain)")

    # TAMPILAN ARENA JIKA SUDAH BERADA DI DALAM ROOM AKTIF
    active_code = mc.get("active_room", "")
    if active_code and active_code in SHARED_ROOMS:
        room_data = SHARED_ROOMS[active_code]
        player_key = f"{profile['nickname']} ({av_emoji})"
        if player_key not in room_data["players"]:
            room_data["players"][player_key] = {
                "score": 0,
                "answered": 0,
                "status": "Sedang Bermain",
                "updated_at": datetime.now().strftime("%H:%M:%S")
            }

        st.divider()
        col_bar1, col_bar2 = st.columns([3, 1])
        with col_bar1:
            st.success(
                f"Terhubung di Room {active_code} | Topik: {room_data['topic']} | "
                f"Bagikan kode '{active_code}' atau tautan dengan akhiran ?room={active_code} ke HP/laptop teman!"
            )
        with col_bar2:
            if st.button("🔄 Refresh Skor Teman"):
                st.rerun()

        st.code(f"Kode Undangan: {active_code}   |   Parameter Link: ?room={quote(active_code)}", language="text")

        q_list = room_data["questions"]
        total_r = len(q_list)
        q_idx = mc["q_index"]
        my_record = room_data["players"][player_key]

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Kode Room", active_code)
        m2.metric("Peserta Aktif", f"{len(room_data['players'])} Orang")
        m3.metric("Progresmu", f"{min(q_idx, total_r)} / {total_r}")
        m4.metric("Skor Kamu", f"{my_record['score']} pts")

        if q_idx < total_r:
            cur_q = q_list[q_idx]
            elapsed_r = max(0, int(datetime.now().timestamp() - (mc["round_start_ts"] or datetime.now().timestamp())))
            speed_bonus = max(0, 15 - (elapsed_r // 4))

            st.markdown(
                f"<div class='fq-card'><h4>Soal {q_idx + 1} dari {total_r}</h4>"
                f"<p style='color:#0F172A; font-size:1.02rem; font-weight:600; margin-top:6px;'>{cur_q['question']}</p></div>",
                unsafe_allow_html=True
            )

            letters = ["A", "B", "C", "D"]
            mabar_labels = [f"{letters[i]}. {cur_q['options'][i]}" for i in range(4)]
            pilihan_mabar = st.radio(
                "Pilih jawabanmu:",
                mabar_labels,
                key=f"shared_mabar_opt_{active_code}_{player_key}_{q_idx}"
            )

            if st.button("Kirim Jawaban Mabar", type="primary"):
                chosen_i = mabar_labels.index(pilihan_mabar)
                correct_i = cur_q["correct_index"]
                if chosen_i == correct_i:
                    earned = 25 + speed_bonus
                    my_record["score"] += earned
                    res_label = f"Benar (+{earned} pts)"
                else:
                    res_label = f"Salah (Kunci: {letters[correct_i]})"

                my_record["answered"] = q_idx + 1
                my_record["updated_at"] = datetime.now().strftime("%H:%M:%S")
                if q_idx + 1 >= total_r:
                    my_record["status"] = "Selesai"

                mc["history"].append({
                    "No": q_idx + 1,
                    "Jawaban Kamu": mabar_labels[chosen_i],
                    "Kunci Jawaban": mabar_labels[correct_i],
                    "Hasil": res_label
                })
                mc["q_index"] += 1
                mc["round_start_ts"] = datetime.now().timestamp()
                st.rerun()
        else:
            st.success(f"Kamu telah menyelesaikan seluruh soal di Room {active_code}! Klik 'Refresh Skor Teman' untuk melihat skor terbaru temanmu.")

        st.markdown("#### 🏆 Papan Peringkat Live Room")
        live_rows = []
        for p_name, p_info in room_data["players"].items():
            live_rows.append({
                "Pemain": p_name,
                "Skor": p_info["score"],
                "Soal Dijawab": f"{p_info['answered']} / {total_r}",
                "Status": p_info["status"],
                "Update Terakhir": p_info["updated_at"]
            })
        live_df = pd.DataFrame(live_rows).sort_values(by=["Skor", "Update Terakhir"], ascending=[False, True]).reset_index(drop=True)
        live_df.index = live_df.index + 1
        st.dataframe(live_df, use_container_width=True)

        if mc["history"]:
            with st.expander("Lihat Detail Jawabanmu di Room Ini"):
                st.dataframe(pd.DataFrame(mc["history"]), use_container_width=True)


# =====================================================
# TAB 4: BAHASA INGGRIS AKUNTANSI
# =====================================================

with tab_english:
    st.markdown(
        "<div class='fq-card'><h4>Belajar Bahasa Inggris Akuntansi</h4>"
        "<p>Pahami istilah-istilah akuntansi dalam bahasa Inggris beserta makna, contoh kalimat, dan penjelasan detail.</p></div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        pd.DataFrame([
            {
                "English Term": item["term"],
                "Istilah Indonesia": item["id_meaning"],
                "Penjelasan": item["explanation"],
                "Contoh Kalimat": item["example"]
            }
            for item in ENGLISH_TERMS_BANK
        ]),
        use_container_width=True
    )

    selected_term = st.selectbox("Pilih istilah untuk dibedah lengkap:", [x["term"] for x in ENGLISH_TERMS_BANK])
    if st.button("Bedah Istilah Ini", type="primary"):
        with st.spinner("Menyiapkan penjelasan istilah..."):
            out_eng, tbl_eng, _ = ask_prof_gemini(
                question=f"Jelaskan istilah akuntansi '{selected_term}', arti padanannya, contoh jurnal/laporan keuangan, dan kesalahan umum.",
                nickname=profile["nickname"],
                jenjang=profile["jenjang"],
                bahasa="Bahasa Indonesia"
            )
        if out_eng:
            st.markdown(out_eng)
            if tbl_eng:
                st.dataframe(pd.DataFrame(tbl_eng), use_container_width=True)
        else:
            item_obj = next((x for x in ENGLISH_TERMS_BANK if x["term"] == selected_term), None)
            if item_obj:
                st.info(f"{item_obj['term']} ({item_obj['id_meaning']}): {item_obj['explanation']} Contoh: {item_obj['example']}")
        record_daily_play()


# =====================================================
# TAB 5: BANTU TUGAS & SUMBER TERPERCAYA
# =====================================================

with tab_tugas:
    st.markdown(
        "<div class='fq-card'><h4>Bantu Tugas & Sumber Rujukan Terpercaya</h4>"
        "<p>Tuliskan soal atau kasus tugasmu—jawaban disusun runtut, memakai tabel bila diperlukan, dan menyertakan sumber rujukan yang bisa diakses.</p></div>",
        unsafe_allow_html=True
    )

    task_topic = st.selectbox("Bidang Materi", MATERI_AKUNTANSI, key="task_topic_sel")
    task_question = st.text_area("Tuliskan soal atau kasus tugas:", height=120)

    if st.button("Bantu Selesaikan Tugas", type="primary"):
        if not task_question.strip():
            st.warning("Silakan tulis soal atau kasus tugas terlebih dahulu.")
        else:
            with st.spinner("Menyusun langkah penyelesaian & sumber rujukan..."):
                ans_task, tbl_task, _ = ask_prof_gemini(
                    question=f"[{task_topic}] Bantu selesaikan tugas berikut secara runtut beserta tabel jika relevan dan sumber rujukan resmi:\n{task_question}",
                    nickname=profile["nickname"],
                    jenjang=profile["jenjang"],
                    bahasa=profile["bahasa"]
                )
            st.session_state.task_history.insert(0, {
                "Topik": task_topic,
                "Tugas": task_question,
                "Jawaban": ans_task or "Belum dapat terhubung ke layanan AI saat ini. Silakan coba lagi sebentar lagi.",
                "Tabel": tbl_task
            })
            record_daily_play()
            profile["total_xp"] += 15
            st.rerun()

    for item in st.session_state.task_history:
        st.markdown(f"<div class='fq-card'><h4>{item['Topik']}</h4><p>{item['Tugas']}</p></div>", unsafe_allow_html=True)
        st.markdown(item["Jawaban"])
        if item.get("Tabel"):
            st.dataframe(pd.DataFrame(item["Tabel"]), use_container_width=True)


# =====================================================
# TAB 6: MATERI BACAAN LENGKAP & VARIANS
# =====================================================

with tab_materi:
    st.markdown(
        "<div class='fq-card'><h4>Ruang Baca Materi Akuntansi & Analisis Varians</h4>"
        "<p>Baca seluruh materi akuntansi langsung di dalam aplikasi—termasuk Analisis Laporan Keuangan, Laporan Keuangan Daerah, "
        "Laporan Keuangan Desa, dan berbagai jenis Laporan Keuangan lainnya.</p></div>",
        unsafe_allow_html=True
    )

    selected_materi = st.selectbox(
        "Pilih materi untuk dibaca & didalami:",
        MATERI_AKUNTANSI,
        key="materi_reader_select"
    )
    info_pilihan = MATERI_DETAILS[selected_materi]

    st.markdown(
        f"<div class='fq-card'>"
        f"<h4>{selected_materi}</h4>"
        f"<p><b>Ringkasan Materi:</b> {info_pilihan['ringkasan']}</p>"
        f"<p style='margin-top:8px;'><b>Poin & Konsep Kunci:</b> {info_pilihan['poin_kunci']}</p>"
        f"<p style='margin-top:8px;'><b>Contoh Penerapan:</b> {info_pilihan['contoh']}</p>"
        f"</div>",
        unsafe_allow_html=True
    )

    if st.button("Buat Penjelasan Bacaan Mendalam Materi Ini", type="primary"):
        with st.spinner(f"Menyusun bahan bacaan lengkap {selected_materi}..."):
            deep_txt, deep_tbl, _ = ask_prof_gemini(
                question=(
                    f"Buatkan bahan bacaan pembelajaran yang jelas, terstruktur, dan mudah dipahami tentang '{selected_materi}' "
                    f"untuk jenjang '{profile['jenjang']}'. Sertakan pengertian, komponen/jenis/rumus utama, contoh kasus/ilustrasi "
                    f"dalam bentuk tabel bila sesuai, serta tips belajar."
                ),
                nickname=profile["nickname"],
                jenjang=profile["jenjang"],
                bahasa=profile["bahasa"]
            )
        if deep_txt:
            st.session_state.materi_deep_read[selected_materi] = {
                "text": deep_txt,
                "table": deep_tbl
            }
            record_daily_play()
            profile["total_xp"] += 10
            st.rerun()

    if selected_materi in st.session_state.materi_deep_read:
        saved_read = st.session_state.materi_deep_read[selected_materi]
        st.markdown(f"<div class='fq-card'><h4>Catatan Bacaan Lengkap: {selected_materi}</h4></div>", unsafe_allow_html=True)
        st.markdown(saved_read["text"])
        if saved_read.get("table"):
            st.dataframe(pd.DataFrame(saved_read["table"]), use_container_width=True)

    with st.expander(f"Lihat Daftar Ringkas Semua {len(MATERI_AKUNTANSI)} Materi Akuntansi"):
        katalog_df = pd.DataFrame([
            {
                "No": i + 1,
                "Materi Akuntansi": m_name,
                "Ringkasan": MATERI_DETAILS[m_name]["ringkasan"],
                "Poin Kunci": MATERI_DETAILS[m_name]["poin_kunci"]
            }
            for i, m_name in enumerate(MATERI_AKUNTANSI)
        ])
        st.dataframe(katalog_df, use_container_width=True)

    st.divider()
    st.subheader("Analisis Budget vs. Actuals (.xlsx)")
    st.write("Unggah file Excel dengan kolom Category, Budget, dan Actual untuk melihat tabel selisih dan grafik.")
    uploaded_file = st.file_uploader("Unggah file Excel (.xlsx)", type=["xlsx"], key="budget_excel_uploader")

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ["Category", "Budget", "Actual"]
            if not all(col in df.columns for col in required_columns):
                st.error("File harus memiliki kolom Category, Budget, dan Actual.")
            else:
                df["Budget"] = pd.to_numeric(df["Budget"], errors="coerce")
                df["Actual"] = pd.to_numeric(df["Actual"], errors="coerce")
                if df[["Budget", "Actual"]].isna().any().any():
                    st.error("Kolom Budget dan Actual harus berupa angka valid.")
                else:
                    df["Variance"] = df["Actual"] - df["Budget"]
                    df["Variance %"] = (df["Variance"] / df["Budget"].replace(0, float("nan"))) * 100
                    st.dataframe(df, use_container_width=True)

                    fig_bar = px.bar(
                        df,
                        x="Category",
                        y="Variance",
                        color="Variance",
                        title="Variance per Kategori",
                        text_auto=".2s"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal memproses file: {str(e)}")

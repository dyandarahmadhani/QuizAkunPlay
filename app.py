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
# 3. INITIALIZE GEMINI CLIENT
# =====================================================

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.8-flash"
FALLBACK_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash"
]

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
    {"name": "IPSASB (International Public Sector Accounting Standards)", "url": "https://www.ipsasb.org/"},
    {"name": "Bank Indonesia (Kebijakan & Fintech)", "url": "https://www.bi.go.id/"}
]

MATERI_DETAILS = {
    "Pengantar Akuntansi 1": {
        "ringkasan": "Persamaan dasar akuntansi, aturan debit-kredit, siklus akuntansi perusahaan jasa & dagang, jurnal umum, buku besar, neraca saldo, jurnal penyesuaian, hingga laporan keuangan dasar.",
        "poin_kunci": "Aset = Liabilitas + Ekuitas, basis akrual vs kas, jurnal penyesuaian, dan kertas kerja.",
        "contoh": "Membeli peralatan kantor secara tunai menambah Aset (Peralatan) dan mengurangi Aset (Kas) dengan jumlah yang sama.",
        "link": "https://web.iai.id/"
    },
    "Pengantar Akuntansi 2": {
        "ringkasan": "Jurnal khusus, sistem pencatatan persediaan periodik & perpetual, metode FIFO/rata-rata, kas kecil, piutang tak tertagih, aset tetap, dan jurnal penutup.",
        "poin_kunci": "FIFO vs rata-rata tertimbang, penyusutan aset tetap, cadangan kerugian piutang, dan penutupan akun nominal.",
        "contoh": "Menjual barang dagang secara kredit mencatat Piutang Usaha (Debit) dan Penjualan (Kredit).",
        "link": "https://www.ifrs.org/"
    },
    "Akuntansi Keuangan Menengah": {
        "ringkasan": "Pengakuan, pengukuran, penyajian, dan pengungkapan pos laporan keuangan: kas, piutang, persediaan, aset tetap, aset tak berwujud, liabilitas jangka panjang, dan ekuitas.",
        "poin_kunci": "Biaya perolehan vs nilai realisasi neto/nilai wajar, penurunan nilai (impairment), obligasi, dan ekuitas.",
        "contoh": "Mengukur persediaan pada nilai yang lebih rendah antara biaya perolehan dan nilai realisasi neto.",
        "link": "https://web.iai.id/"
    },
    "Akuntansi Keuangan Lanjutan": {
        "ringkasan": "Persekutuan, penjualan konsinyasi, penjualan cicilan, kantor cabang, kombinasi bisnis, transaksi mata uang asing, dan laporan keuangan konsolidasian.",
        "poin_kunci": "Eliminasi saldo resiprokal, kepentingan nonpengendali (NCI), goodwill, dan konsolidasi entitas anak.",
        "contoh": "Mengeliminasi investasi induk pada entitas anak dan ekuitas anak saat menyusun laporan konsolidasi.",
        "link": "https://www.ifrs.org/issued-standards/list-of-standards/"
    },
    "Akuntansi Keuangan Desa": {
        "ringkasan": "Pengelolaan keuangan desa mulai dari perencanaan (APBDes), pelaksanaan, penatausahaan, pelaporan, hingga pertanggungjawaban atas Dana Desa, ADD, PADes, dan bantuan keuangan.",
        "poin_kunci": "APBDes, Buku Kas Umum (BKU), buku pembantu bank/pajak, Laporan Realisasi APBDes, dan pertanggungjawaban.",
        "contoh": "Mencatat pencairan dan realisasi belanja pembangunan jalan desa sesuai pos anggaran pada APBDes.",
        "link": "https://jdih.kemendagri.go.id/"
    },
    "Manajemen Biaya & Akuntansi Manajemen": {
        "ringkasan": "Klasifikasi biaya, job order & process costing, Activity-Based Costing (ABC), analisis biaya-volume-laba (CVP/BEP), anggaran, dan keputusan taktis.",
        "poin_kunci": "Biaya tetap vs variabel, biaya langsung vs tidak langsung, Break-Even Point (BEP), analisis varians, dan relevan costing.",
        "contoh": "Menghitung BEP unit untuk mengetahui batas minimal penjualan agar operasi tidak mengalami kerugian.",
        "link": "https://www.ifrs.org/"
    },
    "Akuntansi Sektor Publik": {
        "ringkasan": "Penganggaran, akuntansi dana, penilaian kinerja, dan akuntabilitas pada organisasi nirlaba serta entitas publik seperti yayasan, rumah sakit publik, dan lembaga sosial.",
        "poin_kunci": "Value for Money (ekonomi, efisiensi, efektivitas), akuntansi dana, anggaran berbasis kinerja, dan transparansi.",
        "contoh": "Menilai efisiensi program layanan publik dengan membandingkan realisasi output terhadap biaya yang diserap.",
        "link": "https://www.ipsasb.org/"
    },
    "Akuntansi Pemerintahan": {
        "ringkasan": "Standar Akuntansi Pemerintahan (SAP) berbasis akrual untuk pemerintah pusat dan daerah, mencakup LRA, LO, neraca, Laporan Arus Kas, dan jurnal finansial serta anggaran.",
        "poin_kunci": "Laporan Realisasi Anggaran (LRA), Laporan Operasional (LO), jurnal finansial vs jurnal anggaran, dan ekuitas SAL.",
        "contoh": "Mencatat beban pegawai akrual pada LO sekaligus mencatat realisasi belanja pada LRA sesuai ketentuan SAP.",
        "link": "https://www.ksap.org/"
    },
    "Komputer Akuntansi 1": {
        "ringkasan": "Setup perusahaan, perancangan Chart of Accounts (COA), saldo awal, pencatatan transaksi jasa/dagang, rekonsiliasi, dan pelaporan keuangan berbasis aplikasi.",
        "poin_kunci": "Struktur kode akun, linked accounts, transaksi kas/bank/piutang/utang, dan validasi neraca saldo.",
        "contoh": "Mengatur akun penampung otomatis (linked accounts) agar penjualan dan piutang terposting ke buku besar.",
        "link": "https://web.iai.id/"
    },
    "Komputer Akuntansi 2": {
        "ringkasan": "Pengelolaan persediaan multi-gudang/manufaktur, jadwal penyusutan aset tetap otomatis, pencatatan pajak/rekonsiliasi, audit log, dan analisis laporan keuangan sistem.",
        "poin_kunci": "Kartu stok/BOM, depresiasi otomatis, rekonsiliasi saldo modul dengan buku besar, dan kontrol akses.",
        "contoh": "Menjalankan proses penyusutan aset tetap bulanan dan memeriksa kesesuaian saldo dengan buku besar.",
        "link": "https://www.ifrs.org/"
    },
    "Pengadaan Barang dan Jasa": {
        "ringkasan": "Prinsip, etika, perencanaan, pemilihan penyedia, kontrak, serah terima pekerjaan, serta dokumentasi pembayaran dan akuntabilitas pengadaan barang/jasa.",
        "poin_kunci": "Kesesuaian spesifikasi & pagu/HPS, transparansi & persaingan sehat, administrasi kontrak, dan bukti serah terima sah.",
        "contoh": "Memverifikasi berita acara serah terima barang, kontrak, dan bukti pajak sebelum pencairan pembayaran.",
        "link": "https://jdih.lkpp.go.id/"
    },
    "Audit Organisasi Publik": {
        "ringkasan": "Pemeriksaan independen dan sistematis atas keuangan, kinerja, dan kepatuhan organisasi sektor publik/pemerintahan beserta penyusunan temuan dan rekomendasi.",
        "poin_kunci": "Audit keuangan, audit kinerja, audit kepatuhan, bukti audit cukup & tepat, dan unsur temuan (kondisi, kriteria, sebab, akibat).",
        "contoh": "Menguji kepatuhan penyaluran dan pertanggungjawaban bantuan/hibah terhadap aturan dan bukti pendukung.",
        "link": "https://www.bpk.go.id/"
    },
    "Sistem Informasi Akuntansi & Manajemen": {
        "ringkasan": "Perancangan, pengendalian internal, siklus transaksi (pendapatan, pengeluaran, produksi, penggajian), dan pemanfaatan sistem informasi untuk keputusan manajerial.",
        "poin_kunci": "Pemisahan fungsi (segregation of duties), pengendalian input/proses/output, dokumen sumber, dan pelaporan manajemen.",
        "contoh": "Memisahkan fungsi penyetuju pembelian, penerima barang, dan pencatat utang untuk menjaga pengendalian internal.",
        "link": "https://www.bpk.go.id/"
    },
    "Akuntansi Digital": {
        "ringkasan": "Pemanfaatan cloud accounting, otomatisasi jurnal, e-invoicing, big data, dan AI dalam mempercepat pencatatan, rekonsiliasi, serta analisis keuangan.",
        "poin_kunci": "Digitalisasi bukti transaksi, integrasi data real-time, keamanan siber & integritas data, serta analitik keuangan.",
        "contoh": "Merekonsiliasi transaksi e-invoice dan mutasi digital secara otomatis untuk mempercepat penutupan buku.",
        "link": "https://web.iai.id/"
    },
    "Teknologi Keuangan (Fintech)": {
        "ringkasan": "Ekosistem pembayaran digital, e-wallet, pinjaman digital, open banking, serta pencatatan akuntansi, manajemen risiko, dan kepatuhan regulasi fintech.",
        "poin_kunci": "Alur settlement dana, pencatatan biaya transaksi/potongan gateway, risiko likuiditas & siber, serta perlindungan data.",
        "contoh": "Mencatat penjualan bruto, potongan biaya layanan payment gateway, dan dana bersih yang masuk ke rekening.",
        "link": "https://www.bi.go.id/"
    },
    "Standar Nasional & Internasional (PSAK, SAK EMKM, SAP, IFRS, IPSAS)": {
        "ringkasan": "Perbandingan dan penerapan PSAK/IAI, SAK EMKM, SAP (pemerintah), IFRS (bisnis global), dan IPSAS (sektor publik internasional).",
        "poin_kunci": "Kesesuaian standar dengan karakteristik entitas, pengukuran & pengakuan, pengungkapan, dan konvergensi standar.",
        "contoh": "Menerapkan SAK EMKM untuk entitas mikro/kecil yang memenuhi kriteria dan membutuhkan laporan keuangan sederhana.",
        "link": "https://www.ifrs.org/"
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
    """Membersihkan tanda ** dan # di awal baris agar teks rapi tanpa simbol berantakan, sambil menjaga tabel Markdown."""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        cleaned = line.replace("**", "").replace("__", "")
        stripped = cleaned.lstrip()
        # Pertahankan baris tabel Markdown yang diawali '|'
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


def pick_relevant_sources(query_text: str) -> list[dict]:
    """Memilih sumber resmi yang relevan dan bisa diakses berdasarkan kata kunci pertanyaan."""
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


def build_dynamic_prof_fallback(question: str, nickname: str, jenjang: str) -> str:
    """Menyusun jawaban cadangan yang spesifik terhadap pertanyaan pengguna + tabel + sumber yang bisa diakses."""
    q_clean = question.strip()
    sources = pick_relevant_sources(q_clean)
    src_lines = "\n".join([f"- {s['name']}: {s['url']}" for s in sources])

    return (
        f"Halo {nickname}, kita bahas langsung pertanyaanmu tentang '{q_clean}' untuk jenjang {jenjang} ya!\n\n"
        f"1. Penjelasan Langsung: Topik '{q_clean}' berfokus pada bagaimana transaksi atau peristiwa ekonomi "
        f"diidentifikasi dari bukti pendukung yang sah, diklasifikasikan ke akun/pos yang tepat, dicatat secara "
        f"konsisten sesuai standar yang berlaku, lalu dilaporkan agar informasinya berguna bagi pengambil keputusan.\n\n"
        f"2. Ringkasan Komponen Utama (Tabel):\n"
        f"| Aspek | Fokus Utama | Catatan Praktis |\n"
        f"| --- | --- | --- |\n"
        f"| Bukti & Dasar Transaksi | Dokumen sumber sah & waktu kejadian | Pastikan tanggal, nominal, dan pihak terkait jelas |\n"
        f"| Pencatatan / Perlakuan | Klasifikasi akun & aturan standar | Sesuaikan dengan jenis entitas dan standar yang dipakai |\n"
        f"| Pelaporan & Evaluasi | Penyajian informasi & pengendalian | Cek kelengkapan dan konsistensi sebelum digunakan |\n\n"
        f"3. Langkah Praktis Memahaminya: Mulai dari membaca konteks kasus '{q_clean}', tentukan akun atau "
        f"pos utama yang bergerak, perhatikan arah perubahan (bertambah/berkurang atau debit/kredit), lalu cek "
        f"dampaknya terhadap laporan keuangan.\n\n"
        f"4. Sumber Rujukan yang Bisa Diakses:\n"
        f"{src_lines}"
    )


def call_gemini_prof(question: str, nickname: str, jenjang: str, bahasa: str) -> str:
    """Memanggil model Gemini agar Prof menjawab spesifik sesuai pertanyaan, memakai tabel bila relevan, dan menyertakan link sumber."""
    prompt = f"""
Kamu adalah "Prof", mentor akuntansi yang ramah, seru, jelas, dan penjelasannya sangat mudah dipahami untuk jenjang "{jenjang}".
Sapa pengguna dengan nama panggilan "{nickname}" secara akrab.
Gunakan bahasa "{bahasa}".

Jawablah pertanyaan berikut secara langsung, tepat sasaran, dan lengkap (jangan menyimpang ke topik lain):
"{question}"

Aturan format dan isi:
1. Jawab tepat sesuai pertanyaan pengguna; jika pertanyaannya spesifik (misalnya jurnal pembelian tunai, APBDes, depresiasi, rasio, audit, dll.), berikan penjelasan dan contoh/ilustrasi yang sesuai dengan pertanyaan itu.
2. Jika pertanyaan memungkinkan atau terbantu dengan perbandingan, alur, komponen, atau contoh jurnal/perhitungan, sertakan tabel Markdown yang rapi (dengan baris header dan pemisah `| --- |`).
3. Sertakan bagian "Sumber Rujukan" di akhir jawaban menggunakan URL resmi dan valid yang benar-benar bisa diakses, misalnya:
   - Ikatan Akuntan Indonesia (IAI): https://web.iai.id/
   - IFRS Foundation: https://www.ifrs.org/
   - Komite Standar Akuntansi Pemerintahan (KSAP): https://www.ksap.org/
   - Badan Pemeriksa Keuangan RI (BPK): https://www.bpk.go.id/
   - JDIH Kemendagri: https://jdih.kemendagri.go.id/
   - JDIH LKPP: https://jdih.lkpp.go.id/
   - IPSASB: https://www.ipsasb.org/
   - Bank Indonesia: https://www.bi.go.id/
4. Jangan gunakan tanda bintang ganda (**) atau tanda pagar (#) di awal judul.
"""
    fallback = build_dynamic_prof_fallback(question, nickname, jenjang)

    models_sequence = []
    for m in [MODEL_NAME] + FALLBACK_MODELS:
        if m and m not in models_sequence:
            models_sequence.append(m)

    for model_id in models_sequence:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt
                )
                cleaned = clean_ai_text(response.text or "")
                if cleaned:
                    if "http" not in cleaned:
                        srcs = pick_relevant_sources(question)
                        src_block = "\n".join([f"- {s['name']}: {s['url']}" for s in srcs])
                        cleaned = f"{cleaned}\n\nSumber Rujukan:\n{src_block}"
                    return cleaned
            except Exception as e:
                err_str = str(e)
                is_transient = (
                    "503" in err_str
                    or "UNAVAILABLE" in err_str
                    or "429" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                )
                if is_transient and attempt == 0:
                    time.sleep(1.2)
                    continue
                break

    return clean_ai_text(fallback)


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
    for model_id in [MODEL_NAME] + FALLBACK_MODELS:
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


def deterministic_room_score(room_code: str, player_name: str, topic: str) -> int:
    digest = hashlib.sha256(f"{room_code}:{player_name}:{topic}".encode("utf-8")).hexdigest()
    return 50 + (int(digest[:4], 16) % 46)  # 50 - 95 poin


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
            )
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

if "mabar_state" not in st.session_state:
    qp_room = st.query_params.get("room", "AKUN-888")
    qp_topic = st.query_params.get("topic", "Pengantar Akuntansi 1")
    valid_topic = qp_topic if qp_topic in MATERI_AKUNTANSI else "Pengantar Akuntansi 1"
    st.session_state.mabar_state = {
        "room_code": str(qp_room).upper(),
        "topic": valid_topic,
        "jenjang": "Mahasiswa/i",
        "num_rounds": 5,
        "rivals": ["Raka (Rubah)", "Nadia (Panda)", "Bima (Kucing)", "Salsa (Burung Hantu)"],
        "started": False,
        "q_index": 0,
        "my_points": 0,
        "round_start_ts": None,
        "questions": [],
        "history": []
    }

if "task_history" not in st.session_state:
    st.session_state.task_history = []


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
        <p>Kuis 1–100 soal, diskusi bareng Prof dengan tabel & sumber valid, serta mabar room lintas perangkat.</p>
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
    "🤝 Mabar Room",
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
        "<p>Tanyakan hal spesifik seputar akuntansi—Prof menjawab sesuai pertanyaanmu, lengkap dengan tabel bila relevan dan link sumber yang bisa diakses.</p></div>",
        unsafe_allow_html=True
    )

    for msg in st.session_state.prof_messages:
        avatar_icon = "👨‍🏫" if msg["role"] == "assistant" else (
            profile["custom_avatar_bytes"] if profile.get("custom_avatar_bytes") else CUTE_AVATARS.get(profile["avatar_name"], "🦊")
        )
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.markdown(msg["content"])

    prof_input = st.chat_input("Tanya apa saja ke Prof (misal: jurnal pembelian tunai, perbedaan LRA & LO, dll.)...")
    if prof_input:
        st.session_state.prof_messages.append({"role": "user", "content": prof_input})
        with st.chat_message("user", avatar=CUTE_AVATARS.get(profile["avatar_name"], "🦊")):
            st.markdown(prof_input)

        with st.spinner("Prof sedang menyiapkan jawaban lengkap & tabel rujukan..."):
            reply_text = call_gemini_prof(
                question=prof_input,
                nickname=profile["nickname"],
                jenjang=profile["jenjang"],
                bahasa=profile["bahasa"]
            )

        st.session_state.prof_messages.append({"role": "assistant", "content": reply_text})
        record_daily_play()
        profile["total_xp"] += 5
        with st.chat_message("assistant", avatar="👨‍🏫"):
            st.markdown(reply_text)


# =====================================================
# TAB 3: MABAR ROOM (MANTAP & BISA DIAKSES)
# =====================================================

with tab_mabar:
    ms = st.session_state.mabar_state

    st.markdown(
        f"<div class='fq-card'><h4>Arena Mabar Room — Kode Aktif: {ms['room_code']}</h4>"
        f"<p>Buat atau masuk room mabar, bagikan parameter room ke teman di perangkat lain, jawab cepat untuk bonus poin, dan pantau papan peringkat.</p></div>",
        unsafe_allow_html=True
    )

    col_m1, col_m2, col_m3, col_m4 = st.columns([1.3, 1.8, 1, 1])
    with col_m1:
        room_inp = st.text_input("Kode Room", value=ms["room_code"])
    with col_m2:
        topic_default_idx = MATERI_AKUNTANSI.index(ms["topic"]) if ms["topic"] in MATERI_AKUNTANSI else 0
        mabar_topic = st.selectbox("Topik Pertandingan", MATERI_AKUNTANSI, index=topic_default_idx, key="mabar_topic_sel")
    with col_m3:
        mabar_jenjang = st.selectbox("Jenjang", ["Siswa", "Mahasiswa/i"], index=0 if profile["jenjang"] == "Siswa" else 1, key="mabar_jenjang_sel")
    with col_m4:
        mabar_rounds = st.number_input("Jumlah Ronde", min_value=3, max_value=15, value=int(ms.get("num_rounds", 5)), step=1)

    clean_room = "".join(ch for ch in room_inp.strip().upper() if ch.isalnum() or ch in ("-", "_")) or "AKUN-888"
    st.query_params["room"] = clean_room
    st.query_params["topic"] = mabar_topic

    col_invite1, col_invite2 = st.columns([2, 1])
    with col_invite1:
        st.text_input(
            "Salin Parameter Undangan Room (tambahkan di akhir URL aplikasi):",
            value=f"?room={clean_room}&topic={quote(mabar_topic)}",
            disabled=True
        )
    with col_invite2:
        new_friend = st.text_input("Tambah Nama Teman di Room", placeholder="Contoh: Citra")
        if st.button("Masuk ke Daftar Room"):
            fname = new_friend.strip()
            if fname and fname not in ms["rivals"]:
                ms["rivals"].append(fname)
                st.success(f"{fname} bergabung ke room {clean_room}!")

    if st.button("Mulai / Gabung Room Mabar Sekarang", type="primary"):
        with st.spinner(f"Menyiapkan {int(mabar_rounds)} ronde mabar topik {mabar_topic} di room {clean_room}..."):
            ms["room_code"] = clean_room
            ms["topic"] = mabar_topic
            ms["jenjang"] = mabar_jenjang
            ms["num_rounds"] = int(mabar_rounds)
            ms["started"] = True
            ms["q_index"] = 0
            ms["my_points"] = 0
            ms["round_start_ts"] = datetime.now().timestamp()
            ms["history"] = []
            ms["questions"] = generate_quiz_batch(
                topic=mabar_topic,
                jenjang=mabar_jenjang,
                bahasa=profile["bahasa"],
                count=int(mabar_rounds),
                seed_offset=sum(ord(c) for c in clean_room)
            )
            record_daily_play()
            profile["total_xp"] += 15
            st.rerun()

    if ms["started"] and ms["questions"]:
        q_idx = ms["q_index"]
        total_r = len(ms["questions"])

        m_met1, m_met2, m_met3 = st.columns(3)
        m_met1.metric("Room", ms["room_code"])
        m_met2.metric("Ronde", f"{min(q_idx + 1, total_r)} / {total_r}")
        m_met3.metric("Poin Kamu", f"{ms['my_points']} pts")

        if q_idx < total_r:
            cur_q = ms["questions"][q_idx]
            elapsed_r = max(0, int(datetime.now().timestamp() - (ms["round_start_ts"] or datetime.now().timestamp())))
            speed_bonus = max(0, 15 - (elapsed_r // 4))

            st.markdown(
                f"<div class='fq-card'><h4>Ronde {q_idx + 1} dari {total_r} — {ms['topic']}</h4>"
                f"<p style='color:#0F172A; font-size:1rem; font-weight:600; margin-top:6px;'>{cur_q['question']}</p></div>",
                unsafe_allow_html=True
            )

            letters = ["A", "B", "C", "D"]
            mabar_labels = [f"{letters[i]}. {cur_q['options'][i]}" for i in range(4)]
            pilihan_mabar = st.radio("Pilih jawaban tercepatmu:", mabar_labels, key=f"mabar_opt_{ms['room_code']}_{q_idx}")

            if st.button("Kunci Jawaban Ronde", type="primary"):
                chosen_i = mabar_labels.index(pilihan_mabar)
                correct_i = cur_q["correct_index"]
                if chosen_i == correct_i:
                    earned = 25 + speed_bonus
                    ms["my_points"] += earned
                    status_r = f"Benar (+{earned} pts)"
                    st.success(f"Mantap! Jawaban tepat — kamu dapat +{earned} poin (termasuk bonus kecepatan +{speed_bonus}).")
                else:
                    status_r = "Salah (0 pts)"
                    st.info(f"Belum tepat. Kunci jawaban: {mabar_labels[correct_i]} — {cur_q['explanation']}")

                ms["history"].append({
                    "Ronde": q_idx + 1,
                    "Jawaban Kamu": mabar_labels[chosen_i],
                    "Kunci": mabar_labels[correct_i],
                    "Hasil": status_r
                })
                ms["q_index"] += 1
                ms["round_start_ts"] = datetime.now().timestamp()
                st.rerun()
        else:
            st.success(f"Pertandingan di Room {ms['room_code']} selesai! Skor akhir kamu: {ms['my_points']} poin.")

        if ms["history"]:
            st.markdown("#### Riwayat Ronde Kamu")
            st.dataframe(pd.DataFrame(ms["history"]), use_container_width=True)

        st.markdown("#### Papan Peringkat Room")
        board_rows = [{"Pemain": f"{profile['nickname']} (Kamu)", "Skor": ms["my_points"]}]
        for r_name in ms["rivals"]:
            board_rows.append({
                "Pemain": r_name,
                "Skor": deterministic_room_score(ms["room_code"], r_name, ms["topic"])
            })
        board_df = pd.DataFrame(board_rows).sort_values(by="Skor", ascending=False).reset_index(drop=True)
        board_df.index = board_df.index + 1
        st.dataframe(board_df, use_container_width=True)


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
            out_eng = call_gemini_prof(
                question=f"Jelaskan istilah akuntansi '{selected_term}', arti padanannya, contoh jurnal/laporan keuangan, dan kesalahan umum.",
                nickname=profile["nickname"],
                jenjang=profile["jenjang"],
                bahasa="Bahasa Indonesia"
            )
        st.markdown(out_eng)
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
                ans_task = call_gemini_prof(
                    question=f"[{task_topic}] Bantu selesaikan tugas berikut secara runtut beserta tabel jika relevan dan sumber rujukan resmi:\n{task_question}",
                    nickname=profile["nickname"],
                    jenjang=profile["jenjang"],
                    bahasa=profile["bahasa"]
                )
            st.session_state.task_history.insert(0, {
                "Topik": task_topic,
                "Tugas": task_question,
                "Jawaban": ans_task
            })
            record_daily_play()
            profile["total_xp"] += 15
            st.rerun()

    for item in st.session_state.task_history:
        st.markdown(f"<div class='fq-card'><h4>{item['Topik']}</h4><p>{item['Tugas']}</p></div>", unsafe_allow_html=True)
        st.markdown(item["Jawaban"])


# =====================================================
# TAB 6: 16 MATERI (LINK MODUL BERBEDA) & VARIANS
# =====================================================

with tab_materi:
    st.markdown(
        "<div class='fq-card'><h4>Modul Bacaan 16 Materi Akuntansi & Analisis Varians</h4>"
        "<p>Setiap materi memiliki link modul/referensi bacaan yang berbeda-beda agar kamu bisa membaca dan mengeksplorasi seluruh topik akuntansi.</p></div>",
        unsafe_allow_html=True
    )

    for idx_m, m_name in enumerate(MATERI_AKUNTANSI, start=1):
        info = MATERI_DETAILS[m_name]
        st.markdown(
            f"<div class='fq-card'>"
            f"<h4>{idx_m}. {m_name}</h4>"
            f"<p>{info['ringkasan']}</p>"
            f"<p style='margin-top:6px;'><b>Poin Kunci:</b> {info['poin_kunci']}</p>"
            f"<p style='margin-top:6px;'><b>Contoh:</b> {info['contoh']}</p>"
            f"<p style='margin-top:8px;'><a href='{info['link']}' target='_blank'>Buka Modul Bacaan {m_name}</a></p>"
            f"</div>",
            unsafe_allow_html=True
        )

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

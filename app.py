import os
import json
import time
import random
import hashlib
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
# 4. CONSTANTS & CATALOGS
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

MATERI_DETAILS = {
    "Pengantar Akuntansi 1": {
        "ringkasan": "Membahas dasar pencatatan transaksi keuangan pada perusahaan jasa dan dagang, persamaan dasar akuntansi, siklus akuntansi, jurnal umum, buku besar, neraca saldo, ayat jurnal penyesuaian, hingga penyusunan laporan keuangan dasar.",
        "poin_kunci": "Persamaan Dasar Akuntansi (Aset = Liabilitas + Ekuitas), aturan debit-kredit, jurnal penyesuaian (akrual & deferal), dan kertas kerja.",
        "contoh": "Pembelian peralatan kantor tunai menambah Aset (Peralatan) dan mengurangi Aset (Kas) pada nilai yang sama."
    },
    "Pengantar Akuntansi 2": {
        "ringkasan": "Melanjutkan siklus akuntansi ke perusahaan dagang dan manufaktur/entitas yang lebih kompleks, termasuk jurnal khusus, kartu persediaan, kas kecil, piutang tak tertagih, aset tetap, dan jurnal penutup.",
        "poin_kunci": "Sistem periodik vs perpetual, metode FIFO/rata-rata, penyusutan aset tetap, cadangan kerugian piutang, dan jurnal penutup.",
        "contoh": "Penjualan barang dagang secara kredit mencatat Piutang Usaha di debit dan Penjualan di kredit, serta HPP di sistem perpetual."
    },
    "Akuntansi Keuangan Menengah": {
        "ringkasan": "Mendalami pengakuan, pengukuran, penyajian, dan pengungkapan pos-pos laporan keuangan utama seperti kas & setara kas, piutang, persediaan, aset tetap, aset tak berwujud, liabilitas jangka panjang, dan ekuitas.",
        "poin_kunci": "Nilai wajar vs biaya perolehan, penurunan nilai (impairment), obligasi & amortisasi, serta penyajian laporan posisi keuangan dan laba rugi.",
        "contoh": "Mengukur persediaan pada nilai yang lebih rendah antara biaya perolehan dan nilai realisasi neto."
    },
    "Akuntansi Keuangan Lanjutan": {
        "ringkasan": "Membahas transaksi entitas dengan struktur kompleks seperti persekutuan (firma/CV), penjualan konsinyasi, penjualan cicilan, kantor cabang, kombinasi bisnis, dan penyusunan laporan keuangan konsolidasian.",
        "poin_kunci": "Eliminasi saldo resiprokal, kepentingan nonpengendali (NCI), goodwill, translasi mata uang asing, dan laporan konsolidasi.",
        "contoh": "Mengeliminasi investasi induk pada anak dan ekuitas anak saat menyusun laporan keuangan konsolidasian."
    },
    "Akuntansi Keuangan Desa": {
        "ringkasan": "Fokus pada pengelolaan keuangan desa mulai dari perencanaan (APBDes), pelaksanaan, penatausahaan, pelaporan, hingga pertanggungjawaban atas Dana Desa, ADD, PADes, dan bantuan keuangan.",
        "poin_kunci": "APBDes, buku kas umum, buku pembantu bank/pajak, laporan realisasi APBDes, dan pertanggungjawaban kepala desa.",
        "contoh": "Mencatat pencairan dan realisasi belanja kegiatan pembangunan jalan desa sesuai pos APBDes."
    },
    "Manajemen Biaya & Akuntansi Manajemen": {
        "ringkasan": "Membahas penggolongan biaya, perhitungan harga pokok produksi (job order & process costing), Activity-Based Costing (ABC), analisis biaya-volume-laba (CVP), anggaran operasional, dan pengambilan keputusan taktis.",
        "poin_kunci": "Biaya tetap vs variabel, biaya langsung vs tidak langsung, titik impas (BEP), varians biaya, dan relevan costing.",
        "contoh": "Menghitung Break-Even Point (BEP) unit untuk mengetahui jumlah penjualan minimal agar tidak merugi."
    },
    "Akuntansi Sektor Publik": {
        "ringkasan": "Membahas sistem akuntansi dan pengelolaan keuangan pada organisasi nirlaba serta entitas publik seperti lembaga pemerintah, yayasan, rumah sakit publik, dan perguruan tinggi.",
        "poin_kunci": "Value for Money (ekonomi, efisiensi, efektivitas), penganggaran publik, akuntansi dana, dan akuntabilitas kinerja.",
        "contoh": "Mengevaluasi efisiensi program pelayanan publik dengan membandingkan output layanan terhadap biaya yang dikeluarkan."
    },
    "Akuntansi Pemerintahan": {
        "ringkasan": "Mengulas prinsip dan standar akuntansi keuangan pemerintah pusat dan daerah berbasis Standar Akuntansi Pemerintahan (SAP), termasuk akuntansi anggaran, akrual, LO, LRA, neraca, dan LAK.",
        "poin_kunci": "Basis akrual vs basis kas menuju akrual, Laporan Realisasi Anggaran (LRA), Laporan Operasional (LO), dan jurnal finansial serta anggaran.",
        "contoh": "Mencatat alokasi pagu anggaran belanja sekaligus jurnal akrual saat beban jasa pemerintahan terjadi."
    },
    "Komputer Akuntansi 1": {
        "ringkasan": "Penerapan aplikasi akuntansi komputerisasi untuk perusahaan jasa dan dagang, mulai dari setup perusahaan, daftar akun (Chart of Accounts), saldo awal, pencatatan transaksi, hingga cetak laporan keuangan.",
        "poin_kunci": "Struktur kode akun, linked accounts, pencatatan penjualan/pembelian/kas, rekonsiliasi, dan validasi neraca saldo.",
        "contoh": "Menyiapkan Chart of Accounts dan mencatat transaksi penerimaan kas pelanggan agar buku besar serta neraca terbarui otomatis."
    },
    "Komputer Akuntansi 2": {
        "ringkasan": "Kelanjutan komputerisasi akuntansi untuk transaksi yang lebih rinci seperti manufaktur/persediaan multi-gudang, aset tetap, perpajakan/rekonsiliasi, serta analisis laporan keuangan berbasis sistem.",
        "poin_kunci": "Pengelolaan kartu stok/BOM, jadwal penyusutan otomatis, backup & audit log, serta evaluasi akurasi output sistem.",
        "contoh": "Menjalankan proses penyusutan aset tetap bulanan dan memeriksa kesesuaian saldo buku besar dengan laporan rincian."
    },
    "Pengadaan Barang dan Jasa": {
        "ringkasan": "Membahas prinsip, etika, perencanaan, pemilihan penyedia, pelaksanaan kontrak, hingga serah terima dan dokumentasi keuangan dalam pengadaan barang/jasa secara transparan dan akuntabel.",
        "poin_kunci": "Kesesuaian spesifikasi & HPS/anggaran, transparansi & persaingan sehat, administrasi kontrak, serta bukti pembayaran sah.",
        "contoh": "Memastikan berita acara serah terima barang, faktur, dan dokumen kontrak lengkap sebelum pembayaran dilakukan."
    },
    "Audit Organisasi Publik": {
        "ringkasan": "Membahas proses pemeriksaan independen dan sistematis atas pengelolaan serta tanggung jawab keuangan organisasi sektor publik/pemerintahan, mencakup audit keuangan, audit kinerja, dan audit kepatuhan.",
        "poin_kunci": "Bukti audit yang cukup dan tepat, pengendalian internal, temuan audit (kriteria, kondisi, sebab, akibat), dan rekomendasi.",
        "contoh": "Menguji kepatuhan realisasi belanja hibah terhadap ketentuan regulasi dan dokumen pertanggungjawaban penerima."
    },
    "Sistem Informasi Akuntansi & Manajemen": {
        "ringkasan": "Membahas perancangan, pengendalian, dan pemanfaatan sistem informasi untuk mengumpulkan, menyimpan, memproses, dan menyajikan data keuangan serta informasi manajerial.",
        "poin_kunci": "Siklus transaksi (pendapatan, pengeluaran, produksi, SDM/penggajian), pengendalian aplikasi & akses data, dan pelaporan manajemen.",
        "contoh": "Memisahkan tugas antara bagian otorisasi pembelian, penerima barang, dan pencatat utang untuk mencegah kecurangan."
    },
    "Akuntansi Digital": {
        "ringkasan": "Membahas transformasi proses akuntansi melalui cloud accounting, otomatisasi pencatatan, e-invoicing, big data analytics, dan kecerdasan buatan dalam pelaporan serta analisis keuangan.",
        "poin_kunci": "Digitalisasi dokumen sumber, integrasi data real-time, keamanan siber & integritas data, serta analitik prediktif.",
        "contoh": "Mengotomatisasi pencocokan invoice digital dengan bukti pembayaran dan memantau arus kas secara real-time."
    },
    "Teknologi Keuangan (Fintech)": {
        "ringkasan": "Membahas inovasi teknologi dalam layanan keuangan seperti pembayaran digital, e-wallet, peer-to-peer lending, open banking, dan implikasinya terhadap pencatatan, risiko, serta kepatuhan keuangan.",
        "poin_kunci": "Alur transaksi digital, rekonsiliasi gateway pembayaran, manajemen risiko likuiditas & siber, serta regulasi perlindungan konsumen.",
        "contoh": "Merekonsiliasi settlement dana dari payment gateway dengan catatan penjualan harian dan potongan biaya transaksi."
    },
    "Standar Nasional & Internasional (PSAK, SAK EMKM, SAP, IFRS, IPSAS)": {
        "ringkasan": "Membandingkan kerangka pelaporan keuangan nasional dan global: PSAK/IAI dan SAK EMKM untuk entitas bisnis, SAP untuk pemerintahan Indonesia, serta IFRS dan IPSAS untuk standar internasional.",
        "poin_kunci": "Kesesuaian standar dengan bentuk entitas, prinsip pengakuan & pengukuran, pengungkapan wajib, dan konvergensi standar.",
        "contoh": "Menggunakan SAK EMKM untuk usaha mikro/kecil yang belum wajib menyusun laporan keuangan lengkap berbasis PSAK umum."
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
    """Membersihkan tanda ** dan # agar teks mudah dibaca tanpa simbol berantakan."""
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        cleaned = line.replace("**", "").replace("__", "")
        stripped = cleaned.lstrip()
        if stripped.startswith("#"):
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


def safe_generate_text(prompt: str, fallback_text: str) -> str:
    """Memanggil Gemini dengan retry otomatis & model cadangan tanpa memunculkan error mentah."""
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
                    time.sleep(1.5)
                    continue
                break

    return clean_ai_text(fallback_text)


def generate_quiz_batch(topic: str, jenjang: str, bahasa: str, count: int, seed_offset: int = 0) -> list[dict]:
    prompt = f"""
Buatlah tepat {count} soal pilihan ganda berkualitas tentang "{topic}" untuk jenjang "{jenjang}" dalam bahasa "{bahasa}".
Aturan penting:
1. Setiap soal memiliki 4 pilihan jawaban (tanpa awalan huruf/simbol di dalam teks opsi).
2. Letakkan jawaban yang benar di posisi indeks acak (0, 1, 2, atau 3) — jangan selalu di indeks 0.
3. Sertakan penjelasan singkat, jelas, dan mudah dipahami.
4. Kembalikan HANYA JSON valid dengan format list

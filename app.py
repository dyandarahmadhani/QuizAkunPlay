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
    return 55 + (int(digest[:4], 16) % 41)


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
                "Halo! Prof di sini siap nemenin kamu ngobrolin akuntansi tanpa bikin kepala ngebul. "
                "Mau bahas jurnal, anggaran desa, audit, atau sekadar tanya bedanya beban dan biaya? Yuk mulai!"
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
    qp_room = st.query_params.get("room", "AKUN-777")
    st.session_state.mabar_state = {
        "room_code": str(qp_room).upper(),
        "topic": "Pengantar Akuntansi 1",
        "jenjang": "Mahasiswa/i",
        "players": ["Raka (Rubah)", "Nadia (Panda)", "Bima (Kucing)"],
        "started": False,
        "q_index": 0,
        "my_points": 0,
        "questions": []
    }

if "task_history" not in st.session_state:
    st.session_state.task_history = []

if "reading_notes" not in st.session_state:
    st.session_state.reading_notes = {}


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
        <p>Belajar akuntansi lebih seru lewat kuis 1–100 soal, diskusi santai bareng Prof, dan mabar lintas perangkat.</p>
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
    "🤝 Mabar",
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
        "<p>Atur jumlah soal hingga 100 soal, pilih jenjang Siswa atau Mahasiswa/i, dan nikmati posisi jawaban acak agar tidak selalu A.</p></div>",
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
        "<p>Tanya konsep, studi kasus, atau istilah akuntansi dengan gaya bahasa yang santai, seru, dan dijelaskan dengan lengkap.</p></div>",
        unsafe_allow_html=True
    )

    for msg in st.session_state.prof_messages:
        avatar_icon = "👨‍🏫" if msg["role"] == "assistant" else (
            profile["custom_avatar_bytes"] if profile.get("custom_avatar_bytes") else CUTE_AVATARS.get(profile["avatar_name"], "🦊")
        )
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.write(msg["content"])

    prof_input = st.chat_input("Ketik pertanyaanmu ke Prof di sini...")
    if prof_input:
        st.session_state.prof_messages.append({"role": "user", "content": prof_input})
        with st.chat_message("user", avatar=CUTE_AVATARS.get(profile["avatar_name"], "🦊")):
            st.write(prof_input)

        prompt_prof = f"""
Kamu adalah "Prof", mentor akuntansi yang ramah, seru, antusias, dan penjelasannya sangat jelas serta mudah dipahami untuk jenjang "{profile['jenjang']}".
Sapa pengguna dengan nama panggilan "{profile['nickname']}" secara hangat dan akrab.
Gunakan bahasa "{profile['bahasa']}".

Aturan gaya jawaban:
1. Jangan menjawab terlalu singkat atau setengah-setengah; jelaskan dengan benar dan tuntas.
2. Susun penjelasan secara runtut menggunakan poin bernomor (1, 2, 3, dst.) atau paragraf pendek yang rapi:
   - Pengertian inti dengan bahasa sederhana
   - Cara kerja / logika akuntansinya
   - Contoh kasus atau analogi sehari-hari yang konkret
   - Hal penting atau kekeliruan umum yang perlu diperhatikan
3. Jangan gunakan tanda bintang ganda (**) atau tanda pagar (#) di awal judul.

Pertanyaan atau topik diskusi:
{prof_input}
"""
        fallback_prof = (
            f"Halo {profile['nickname']}, pertanyaan yang bagus banget! "
            f"1. Pengertian inti: Akuntansi adalah proses mencatat, mengklasifikasikan, meringkas, dan melaporkan "
            f"transaksi keuangan agar menghasilkan informasi yang relevan dan dapat diandalkan untuk pengambilan keputusan.\n"
            f"2. Cara kerjanya: Setiap transaksi yang bernilai ekonomi ditelusuri dari bukti transaksinya, lalu dicatat "
            f"ke dalam akun yang sesuai (aset, liabilitas/kewajiban, ekuitas, pendapatan, atau beban) sehingga keseimbangan "
            f"persamaan dasar akuntansi tetap terjaga.\n"
            f"3. Contoh sederhana: Ketika kamu membeli perlengkapan tulis secara tunai, kas berkurang dan perlengkapan bertambah "
            f"dengan nilai yang sama. Artinya, komposisi aset berubah tanpa menghilangkan nilai ekonomi secara tiba-tiba.\n"
            f"4. Hal yang sering keliru: Banyak pemula mengira akuntansi hanya sekadar hitung-menghitung angka atau bikin laporan "
            f"di akhir periode, padahal ketepatan bukti transaksi, klasifikasi akun, dan konsistensi aturan jauh lebih menentukan."
        )

        with st.spinner("Prof sedang menyiapkan penjelasan lengkap..."):
            reply_text = safe_generate_text(prompt_prof, fallback_prof)

        st.session_state.prof_messages.append({"role": "assistant", "content": reply_text})
        record_daily_play()
        profile["total_xp"] += 5
        with st.chat_message("assistant", avatar="👨‍🏫"):
            st.write(reply_text)


# =====================================================
# TAB 3: MABAR
# =====================================================

with tab_mabar:
    st.markdown(
        "<div class='fq-card'><h4>Mabar Kuis Antar Perangkat</h4>"
        "<p>Bagikan kode room ke temanmu agar bisa adu skor akuntansi bersama.</p></div>",
        unsafe_allow_html=True
    )

    ms = st.session_state.mabar_state
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        room_inp = st.text_input("Kode Room", value=ms["room_code"])
    with col_m2:
        mabar_topic = st.selectbox("Topik", MATERI_AKUNTANSI, key="mabar_topic_sel")
    with col_m3:
        mabar_jenjang = st.selectbox("Jenjang", ["Siswa", "Mahasiswa/i"], key="mabar_jenjang_sel")

    clean_room = room_inp.strip().upper() or "AKUN-777"
    st.query_params["room"] = clean_room
    st.code(f"Kode Room: {clean_room}  |  Query Room: ?room={clean_room}", language="text")

    if st.button("Mulai / Gabung Room", type="primary"):
        ms["room_code"] = clean_room
        ms["topic"] = mabar_topic
        ms["jenjang"] = mabar_jenjang
        ms["started"] = True
        ms["q_index"] = 0
        ms["my_points"] = 0
        ms["questions"] = generate_quiz_batch(
            topic=mabar_topic,
            jenjang=mabar_jenjang,
            bahasa=profile["bahasa"],
            count=5,
            seed_offset=len(clean_room)
        )
        record_daily_play()
        st.rerun()

    if ms["started"] and ms["questions"]:
        q_idx = ms["q_index"]
        if q_idx < len(ms["questions"]):
            cur_q = ms["questions"][q_idx]
            st.markdown(f"<div class='fq-card'><h4>Ronde {q_idx + 1} / {len(ms['questions'])}: {cur_q['question']}</h4></div>", unsafe_allow_html=True)
            pilihan_mabar = st.radio("Jawabanmu:", cur_q["options"], key=f"mabar_opt_{q_idx}")
            if st.button("Kunci Jawaban", type="primary"):
                if cur_q["options"].index(pilihan_mabar) == cur_q["correct_index"]:
                    ms["my_points"] += 20
                    st.success("Tepat! +20 poin.")
                else:
                    st.info(f"Kunci jawaban: {cur_q['options'][cur_q['correct_index']]}")
                ms["q_index"] += 1
                st.rerun()
        else:
            st.success("Ronde mabar selesai! Lihat papan peringkat di bawah.")

        board_rows = [{"Pemain": f"{profile['nickname']} (Kamu)", "Skor": ms["my_points"]}]
        for p_name in ms["players"]:
            board_rows.append({
                "Pemain": p_name,
                "Skor": deterministic_room_score(ms["room_code"], p_name, ms["topic"])
            })
        board_df = pd.DataFrame(board_rows).sort_values(by="Skor", ascending=False).reset_index(drop=True)
        board_df.index = board_df.index + 1
        st.dataframe(board_df, use_container_width=True)


# =====================================================
# TAB 4: BAHASA INGGRIS AKUNTANSI
# =====================================================

with tab_english:
    st.markdown(
        "<div class='fq-card'><h4>Kamus & Latihan Bahasa Inggris Akuntansi</h4>"
        "<p>Kenali istilah akuntansi berbahasa Inggris beserta arti dan contoh penggunaannya.</p></div>",
        unsafe_allow_html=True
    )

    st.dataframe(
        pd.DataFrame([
            {
                "English Term": item["term"],
                "Istilah Indonesia": item["id_meaning"],
                "Penjelasan": item["explanation"],
                "Contoh": item["example"]
            }
            for item in ENGLISH_TERMS_BANK
        ]),
        use_container_width=True
    )

    selected_term = st.selectbox("Pilih istilah untuk dibahas detail:", [x["term"] for x in ENGLISH_TERMS_BANK])
    if st.button("Bedah Istilah Ini", type="primary"):
        prompt_eng = (
            f"Jelaskan istilah akuntansi '{selected_term}' untuk {profile['jenjang']} dalam bahasa Indonesia yang jelas dan lengkap. "
            f"Sertakan makna akuntansi, contoh pemakaian di laporan keuangan, dan hal yang sering keliru. Tanpa tanda ** atau #."
        )
        fb_eng = f"{selected_term} adalah istilah penting dalam akuntansi untuk memahami pelaporan dan standar keuangan global."
        with st.spinner("Menyiapkan penjelasan..."):
            st.write(safe_generate_text(prompt_eng, fb_eng))
        record_daily_play()


# =====================================================
# TAB 5: BANTU TUGAS & SUMBER TERPERCAYA
# =====================================================

with tab_tugas:
    st.markdown(
        "<div class='fq-card'><h4>Bantu Tugas & Rujukan Sumber Terpercaya</h4>"
        "<p>Tuliskan soal atau kasus tugasmu untuk dibantu langkah penyelesaiannya lengkap dengan sumber rujukan kredibel.</p></div>",
        unsafe_allow_html=True
    )

    task_topic = st.selectbox("Bidang Materi", MATERI_AKUNTANSI, key="task_topic_sel")
    task_question = st.text_area("Tuliskan soal atau kasus tugas:", height=120)

    if st.button("Bantu Selesaikan", type="primary"):
        if not task_question.strip():
            st.warning("Silakan isi soal atau kasus tugas terlebih dahulu.")
        else:
            prompt_task = f"""
Bantu selesaikan tugas berikut pada bidang "{task_topic}" untuk jenjang "{profile['jenjang']}".
Susun rapi dan lengkap (jangan terlalu singkat):
1. Konsep / Dasar Aturan
2. Langkah Penyelesaian Runtut
3. Hasil / Kesimpulan
4. Sumber Rujukan Terpercaya (sebutkan standar/regulasi/literatur relevan seperti PSAK/IAI, SAK EMKM, SAP/PP, IFRS, IPSAS, atau buku teks akuntansi)

Gunakan bahasa yang jelas dan tanpa tanda ** atau #.

Tugas:
{task_question}
"""
            fb_task = (
                f"Identifikasi akun dan dasar perlakuan akuntansi pada {task_topic}, hitung atau susun pencatatan secara runtut, "
                f"lalu rujuk standar terkait (PSAK/IAI, SAK EMKM, SAP, IFRS, atau IPSAS)."
            )
            with st.spinner("Menyusun jawaban & sumber rujukan..."):
                ans_task = safe_generate_text(prompt_task, fb_task)

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
        st.write(item["Jawaban"])


# =====================================================
# TAB 6: KATALOG MATERI (BISA DIBACA SEMUA) & VARIANS
# =====================================================

with tab_materi:
    st.markdown(
        "<div class='fq-card'><h4>Ruang Baca Materi Akuntansi Lengkap (Nasional & Internasional)</h4>"
        "<p>Pilih dan baca materi mana saja secara langsung—tersedia ringkasan, poin utama, contoh penerapan, serta materi bacaan panjang dari Prof.</p></div>",
        unsafe_allow_html=True
    )

    selected_read_topic = st.selectbox(
        "Pilih materi untuk dibaca fokus:",
        MATERI_AKUNTANSI,
        key="read_topic_selector"
    )
    detail = MATERI_DETAILS[selected_read_topic]

    st.markdown(
        f"<div class='fq-card'><h4>{selected_read_topic}</h4>"
        f"<p><b>Ringkasan Materi:</b> {detail['ringkasan']}</p>"
        f"<p style='margin-top:8px;'><b>Poin & Rumus/Konsep Kunci:</b> {detail['poin_kunci']}</p>"
        f"<p style='margin-top:8px;'><b>Contoh Penerapan:</b> {detail['contoh']}</p></div>",
        unsafe_allow_html=True
    )

    if st.button("Buat Modul Bacaan Lengkap Materi Ini", type="primary"):
        prompt_read = f"""
Buatkan modul bacaan lengkap dan mudah dipahami tentang materi "{selected_read_topic}" untuk jenjang "{profile['jenjang']}" dalam bahasa "{profile['bahasa']}".
Jelaskan secara runtut dan menyeluruh (tidak singkat):
1. Gambaran Besar & Mengapa Materi Ini Penting
2. Konsep Inti, Komponen, atau Alur Pencatatan/Prosesnya
3. Contoh Kasus & Simulasi Sederhana
4. Tips Belajar & Kesalahan Umum yang Sering Terjadi
5. Rujukan Standar / Referensi Terpercaya

Gunakan bahasa yang hangat, jelas, dan tanpa tanda ** atau #.
"""
        fb_read = (
            f"Modul Bacaan — {selected_read_topic}\n"
            f"1. Gambaran Besar: {detail['ringkasan']}\n"
            f"2. Konsep Kunci: {detail['poin_kunci']}\n"
            f"3. Contoh Penerapan: {detail['contoh']}\n"
            f"4. Tips Belajar: Pahami tujuan pelaporan dan logika transaksinya terlebih dahulu sebelum menghafal format atau rumus."
        )
        with st.spinner(f"Menyiapkan modul bacaan {selected_read_topic}..."):
            st.session_state.reading_notes[selected_read_topic] = safe_generate_text(prompt_read, fb_read)
        record_daily_play()
        profile["total_xp"] += 10
        st.rerun()

    if selected_read_topic in st.session_state.reading_notes:
        st.markdown(
            f"<div class='fq-card'><h4>Modul Bacaan: {selected_read_topic}</h4></div>",
            unsafe_allow_html=True
        )
        st.write(st.session_state.reading_notes[selected_read_topic])

    with st.expander("Lihat & Buka Semua 16 Materi Akuntansi Sekaligus"):
        for idx_m, m_name in enumerate(MATERI_AKUNTANSI, start=1):
            m_info = MATERI_DETAILS[m_name]
            st.markdown(f"**{idx_m}. {m_name}**")
            st.write(m_info["ringkasan"])
            st.caption(f"Fokus utama: {m_info['poin_kunci']}")
            st.divider()

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

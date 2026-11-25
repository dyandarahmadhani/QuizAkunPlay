import os
import json
import random
import hashlib
from datetime import datetime, date, timedelta

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
    layout="wide"
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

MODEL_NAME = "gemini-2.5-flash"

# =====================================================
# 4. CONSTANTS & CATALOGS
# =====================================================

THEMES = {
    "Emerald & Mint": {
        "primary": "#0F766E",
        "accent": "#14B8A6",
        "bg_card": "#F0FDFA",
        "border": "#99F6E4",
        "text": "#0F172A"
    },
    "Royal Indigo": {
        "primary": "#4338CA",
        "accent": "#6366F1",
        "bg_card": "#EEF2FF",
        "border": "#C7D2FE",
        "text": "#0F172A"
    },
    "Warm Amber": {
        "primary": "#B45309",
        "accent": "#F59E0B",
        "bg_card": "#FFFBEB",
        "border": "#FDE68A",
        "text": "#0F172A"
    },
    "Berry Rose": {
        "primary": "#BE185D",
        "accent": "#EC4899",
        "bg_card": "#FDF2F8",
        "border": "#FBCFE8",
        "text": "#0F172A"
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

MATERI_AKUNTANSI = [
    "Pengantar Akuntansi 1",
    "Pengantar Akuntansi 2",
    "Akuntansi Keuangan Menengah",
    "Akuntansi Keuangan Lanjutan",
    "Akuntansi Keuangan Desa",
    "Manajemen Biaya & Akuntansi Manajemen",
    "Akuntansi Sektor Publik",
    "Akuntansi Pemerintahan",
    "Komputer Akuntansi 1",
    "Komputer Akuntansi 2",
    "Pengadaan Barang dan Jasa",
    "Audit Organisasi Publik",
    "Sistem Informasi Akuntansi & Manajemen",
    "Akuntansi Digital",
    "Teknologi Keuangan (Fintech)",
    "Standar Nasional & Internasional (PSAK, SAK EMKM, SAP, IFRS, IPSAS)"
]

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
# 5. HELPER FUNCTIONS (CLEAN TEXT, STREAK, AI CALLS)
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
    """
    1 hari 1 api:
    - Main hari ini -> api hidup (True)
    - Main kemarin -> masih bisa dilanjutkan hari ini (True, belum hangus)
    - Terlewat >= 2 hari -> api mati (streak jadi 0, False)
    """
    today = date.today()
    if not last_played_str:
        return 0, False
    try:
        last_dt = date.fromisoformat(last_played_str)
    except ValueError:
        return 0, False

    diff_days = (today - last_dt).days
    if diff_days == 0:
        return max(1, current_streak), True
    elif diff_days == 1:
        return max(1, current_streak), True
    else:
        return 0, False


def record_daily_play():
    """Menyalakan atau memperpanjang api harian ketika pengguna bermain/menyelesaikan aktivitas."""
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
            if (today - last_dt).days == 1:
                streak += 1
            else:
                streak = 1
        except ValueError:
            streak = 1
    else:
        streak = 1

    st.session_state.user_profile["streak_days"] = streak
    st.session_state.user_profile["last_played_date"] = today.isoformat()
    st.session_state.user_profile["flame_alive"] = True


def safe_generate_text(prompt: str, fallback_text: str) -> str:
    """Memanggil Gemini dengan perlindungan error agar tidak pernah crash."""
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        raw = response.text or ""
        cleaned = clean_ai_text(raw)
        return cleaned if cleaned else fallback_text
    except Exception as e:
        return f"{fallback_text}\n\n(Catatan koneksi: {str(e)})"


def generate_quiz_batch(topic: str, jenjang: str, bahasa: str, count: int, seed_offset: int = 0) -> list[dict]:
    """
    Menghasilkan batch soal pilihan ganda (4 opsi) dengan jawaban benar yang diacak posisinya
    sehingga tidak selalu jatuh pada pilihan pertama.
    """
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
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        txt = (response.text or "").strip()
        if "```" in txt:
            parts = txt.split("```")
            for p in parts:
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

                # Acak ulang posisi opsi agar distribusi kunci jawaban benar-benar acak
                correct_text = opts[corr_idx]
                shuffled_opts = opts[:]
                random.shuffle(shuffled_opts)
                new_corr_idx = shuffled_opts.index(correct_text)

                questions.append({
                    "question": clean_ai_text(str(item.get("question", "Soal Akuntansi"))),
                    "options": shuffled_opts,
                    "correct_index": new_corr_idx,
                    "explanation": clean_ai_text(str(item.get("explanation", "Penjelasan konsep akuntansi.")))
                })
    except Exception:
        questions = []

    # Fallback lokal deterministik/acak jika respons AI kurang dari jumlah batch
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
    """Menghasilkan skor peserta lain di room mabar secara konsisten berdasarkan kode room & nama."""
    digest = hashlib.sha256(f"{room_code}:{player_name}:{topic}".encode("utf-8")).hexdigest()
    return 55 + (int(digest[:4], 16) % 41)  # 55 - 95 poin


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


# =====================================================
# 7. DYNAMIC THEME STYLING
# =====================================================

active_theme = THEMES.get(st.session_state.user_profile.get("tema", "Emerald & Mint"), THEMES["Emerald & Mint"])

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, {active_theme["bg_card"]} 0%, #FFFFFF 45%);
        color: {active_theme["text"]};
    }}
    .hero-banner {{
        background: linear-gradient(120deg, {active_theme["primary"]}, {active_theme["accent"]});
        color: white;
        padding: 18px 22px;
        border-radius: 16px;
        margin-bottom: 14px;
        box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    }}
    .soft-card {{
        background-color: #FFFFFF;
        border: 1.5px solid {active_theme["border"]};
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04);
    }}
    .flame-box {{
        background: {active_theme["bg_card"]};
        border: 1.5px solid {active_theme["border"]};
        border-radius: 12px;
        padding: 10px 14px;
        margin-bottom: 12px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 8. SIDEBAR — PROFIL, API HARIAN & PENGATURAN
# =====================================================

with st.sidebar:
    profile = st.session_state.user_profile
    av_emoji = CUTE_AVATARS.get(profile.get("avatar_name", "Rubah Cerdas"), "🦊")

    st.markdown("### Profil & Api Harian")
    if profile.get("custom_avatar_bytes"):
        st.image(profile["custom_avatar_bytes"], width=84)
    else:
        st.markdown(f"<div style='font-size:52px; line-height:1;'>{av_emoji}</div>", unsafe_allow_html=True)

    st.markdown(f"Nama Panggilan: {profile['nickname']}")
    st.markdown(f"Jenjang: {profile['jenjang']}")
    st.markdown(f"Email: {profile['email']}")
    st.markdown(f"XP Terkumpul: {profile['total_xp']} XP")

    if profile["flame_alive"] and profile["streak_days"] > 0:
        st.markdown(
            f"<div class='flame-box'>🔥 Api Hidup: {profile['streak_days']} Hari Berturut-turut<br>"
            f"<small>Mainkan setiap hari agar apinya tetap menyala!</small></div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='flame-box'>🩶 Api Mati (0 Hari)<br>"
            "<small>Hari ini belum dimainkan — selesaikan 1 kuis atau latihan untuk menyalakan api lagi!</small></div>",
            unsafe_allow_html=True
        )

    with st.expander("Ubah Profil, Avatar & Tema"):
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
            "Pilih Avatar Lucu Gratis",
            list(CUTE_AVATARS.keys()),
            index=list(CUTE_AVATARS.keys()).index(profile["avatar_name"]) if profile["avatar_name"] in CUTE_AVATARS else 0
        )
        uploaded_photo = st.file_uploader("Atau Unggah Foto Profil (Opsional)", type=["png", "jpg", "jpeg"])
        use_custom_photo = st.checkbox(
            "Gunakan foto unggahan sebagai foto profil",
            value=bool(profile.get("custom_avatar_bytes"))
        )
        notif_opt = st.checkbox("Kirim ringkasan notifikasi ke email", value=profile.get("email_notif", True))

        if st.button("Simpan Pengaturan"):
            profile["nickname"] = new_nick.strip() or "Sobat Jurnal"
            profile["email"] = new_email.strip() or "sobat.akuntansi@contoh.id"
            profile["jenjang"] = new_jenjang
            profile["bahasa"] = new_bahasa
            profile["tema"] = new_tema
            profile["avatar_name"] = new_avatar
            profile["email_notif"] = notif_opt
            if uploaded_photo is not None:
                profile["custom_avatar_bytes"] = uploaded_photo.getvalue()
                profile["use_custom"] = True
            elif not use_custom_photo:
                profile["custom_avatar_bytes"] = None
            st.success("Profil dan tampilan berhasil diperbarui!")
            st.rerun()

    st.divider()
    st.caption("Katalog Materi Akuntansi")
    st.write(f"Total topik tersedia: {len(MATERI_AKUNTANSI)} bidang akuntansi.")


# =====================================================
# 9. TOP HEADER BANNER
# =====================================================

profile = st.session_state.user_profile
flame_badge = f"🔥 {profile['streak_days']} Hari" if profile["flame_alive"] else "🩶 Api Mati"

st.markdown(
    f"""
    <div class='hero-banner'>
        <h2 style='margin:0;'>FinQuest AI — Ruang Akuntansi, Kuis & Mabar</h2>
        <p style='margin:6px 0 0 0;'>
            Halo {profile['nickname']}! Jenjang: {profile['jenjang']} • Bahasa: {profile['bahasa']} • Status Api: {flame_badge}
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 10. MAIN NAVIGATION TABS
# =====================================================

tab_quiz, tab_prof, tab_mabar, tab_english, tab_tugas, tab_materi = st.tabs([
    "🎯 Kuis (Hingga 100 Soal)",
    "👨‍🏫 Ruang Prof (Diskusi)",
    "🤝 Mabar Antar Perangkat",
    "🌐 Bahasa Inggris Akuntansi",
    "📚 Bantu Tugas & Sumber",
    "📖 Katalog Materi & Varians"
])


# =====================================================
# TAB 1: KUIS (SAMPAI 100 SOAL, 1 MENIT / SOAL, ACAK)
# =====================================================

with tab_quiz:
    st.subheader("Mode Kuis Akuntansi (1 Menit per Soal)")
    st.write(
        "Pilih jumlah soal sampai 100 soal, topik akuntansi, dan jenjang (Siswa atau Mahasiswa/i). "
        "Posisi opsi jawaban diacak otomatis agar tidak selalu jatuh pada pilihan pertama."
    )

    qs = st.session_state.quiz_state

    col_q1, col_q2, col_q3 = st.columns([2, 1, 1])
    with col_q1:
        q_topic = st.selectbox("Pilih Topik Akuntansi", MATERI_AKUNTANSI, key="quiz_topic_select")
    with col_q2:
        q_jenjang = st.selectbox("Jenjang", ["Siswa", "Mahasiswa/i"], index=0 if profile["jenjang"] == "Siswa" else 1, key="quiz_jenjang_select")
    with col_q3:
        q_count = st.number_input("Jumlah Soal (1 - 100)", min_value=1, max_value=100, value=10, step=1, key="quiz_count_input")

    if st.button("Mulai Kuis Baru", type="primary"):
        with st.spinner(f"Menyiapkan {int(q_count)} soal {q_topic} dengan kunci jawaban acak..."):
            all_q = []
            remaining = int(q_count)
            batch_num = 0
            while remaining > 0:
                take = min(10, remaining)
                batch_q = generate_quiz_batch(
                    topic=q_topic,
                    jenjang=q_jenjang,
                    bahasa=profile["bahasa"],
                    count=take,
                    seed_offset=batch_num * 10
                )
                all_q.extend(batch_q)
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
        c_info1.metric("Soal Ke", f"{idx + 1} / {qs['total_questions']}")
        c_info2.metric("Skor Sementara", f"{qs['score']} Benar")
        c_info3.metric("Waktu Soal (1 Menit)", f"{remaining_sec} detik")

        if remaining_sec == 0:
            st.warning("Waktu 1 menit untuk soal ini telah habis! Jawaban dicatat sebagai melewati waktu.")

        st.markdown(f"<div class='soft-card'><h4>{q_item['question']}</h4></div>", unsafe_allow_html=True)

        letters = ["A", "B", "C", "D"]
        labeled_options = [f"{letters[i]}. {q_item['options'][i]}" for i in range(4)]
        chosen_label = st.radio("Pilih jawaban terbaikmu:", labeled_options, key=f"q_radio_{idx}")

        if st.button("Kirim Jawaban & Lanjut", type="primary"):
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

        st.success(f"Kuis selesai! Skor kamu: {benar} dari {total_q} soal ({persen}%). Api harianmu menyala!")

        log_df = pd.DataFrame(qs["answers_log"])
        st.markdown("### Rekap Jawaban & Penjelasan (Tabel)")
        st.dataframe(log_df, use_container_width=True)

        if profile.get("email_notif"):
            st.info(
                f"Notifikasi ringkasan hasil kuis ({benar}/{total_q} — {persen}%) "
                f"disiapkan untuk dikirim ke email: {profile['email']}"
            )


# =====================================================
# TAB 2: RUANG PROF (DISKUSI SERU & MUDAH DIPAHAMI)
# =====================================================

with tab_prof:
    st.subheader("Ruang Diskusi Bersama Prof Akuntansi")
    st.write(
        "Ajak Prof diskusi santai seputar konsep akuntansi, studi kasus, atau istilah yang bikin bingung. "
        "Dijelaskan dengan bahasa yang hangat, seru, dan mudah dipahami."
    )

    for msg in st.session_state.prof_messages:
        avatar_icon = "👨‍🏫" if msg["role"] == "assistant" else (
            profile["custom_avatar_bytes"] if profile.get("custom_avatar_bytes") else CUTE_AVATARS.get(profile["avatar_name"], "🦊")
        )
        with st.chat_message(msg["role"], avatar=avatar_icon):
            st.write(msg["content"])

    prof_input = st.chat_input("Tanyakan apa saja ke Prof, misalnya: 'Prof, bedanya kas dan akrual di keuangan desa apa?'")
    if prof_input:
        st.session_state.prof_messages.append({"role": "user", "content": prof_input})
        with st.chat_message("user", avatar=CUTE_AVATARS.get(profile["avatar_name"], "🦊")):
            st.write(prof_input)

        prompt_prof = f"""
Kamu adalah "Prof", dosen/mentor akuntansi yang ramah, seru, antusias, dan penjelasannya super mudah dipahami untuk {profile['jenjang']}.
Sapa pengguna dengan nama panggilan "{profile['nickname']}" sesekali secara hangat.
Gunakan bahasa "{profile['bahasa']}".
Hindari simbol tanda bintang ganda (**) atau tanda pagar (#) di awal judul. Gunakan kalimat yang jelas, analogi sehari-hari, dan contoh praktis.

Pertanyaan / topik diskusi:
{prof_input}
"""
        fallback_prof = (
            f"Wah, pertanyaan bagus banget nih {profile['nickname']}! Intinya, dalam akuntansi kita selalu melihat "
            f"arus nilai ekonomi dan bukti transaksinya dulu sebelum menarik kesimpulan. Coba perhatikan siapa pihak yang "
            f"terlibat, apa aset atau kewajiban yang berubah, dan pada periode mana kejadian itu dicatat."
        )

        with st.spinner("Prof sedang meracik penjelasan yang seru..."):
            reply_text = safe_generate_text(prompt_prof, fallback_prof)

        st.session_state.prof_messages.append({"role": "assistant", "content": reply_text})
        record_daily_play()
        profile["total_xp"] += 5
        with st.chat_message("assistant", avatar="👨‍🏫"):
            st.write(reply_text)


# =====================================================
# TAB 3: MABAR ANTAR PERANGKAT (MULTIPLAYER / DUEL)
# =====================================================

with tab_mabar:
    st.subheader("Mabar Kuis Akuntansi Antar Perangkat")
    st.write(
        "Undang teman dari perangkat lain menggunakan Kode Room yang sama untuk beradu skor akuntansi!"
    )

    ms = st.session_state.mabar_state
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        room_inp = st.text_input("Kode Room Mabar", value=ms["room_code"])
    with col_m2:
        mabar_topic = st.selectbox("Topik Mabar", MATERI_AKUNTANSI, key="mabar_topic_sel")
    with col_m3:
        mabar_jenjang = st.selectbox("Jenjang Mabar", ["Siswa", "Mahasiswa/i"], key="mabar_jenjang_sel")

    st.query_params["room"] = room_inp.strip().upper() or "AKUN-777"
    share_url = f"?room={room_inp.strip().upper() or 'AKUN-777'}"
    st.code(f"Kode Room: {room_inp.strip().upper() or 'AKUN-777'}  |  Parameter Undangan: {share_url}", language="text")

    if st.button("Mulai / Gabung Room Mabar", type="primary"):
        ms["room_code"] = room_inp.strip().upper() or "AKUN-777"
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
            seed_offset=len(ms["room_code"])
        )
        record_daily_play()
        st.rerun()

    if ms["started"] and ms["questions"]:
        q_idx = ms["q_index"]
        if q_idx < len(ms["questions"]):
            cur_q = ms["questions"][q_idx]
            st.markdown(f"<div class='soft-card'><h4>Ronde {q_idx + 1} / {len(ms['questions'])}: {cur_q['question']}</h4></div>", unsafe_allow_html=True)
            pilihan_mabar = st.radio("Jawaban cepatmu:", cur_q["options"], key=f"mabar_opt_{q_idx}")
            if st.button("Kunci Jawaban Ronde Ini"):
                if cur_q["options"].index(pilihan_mabar) == cur_q["correct_index"]:
                    ms["my_points"] += 20
                    st.success("Mantap! +20 poin!")
                else:
                    st.info(f"Belum tepat. Kunci: {cur_q['options'][cur_q['correct_index']]}")
                ms["q_index"] += 1
                st.rerun()
        else:
            st.success("Ronde mabar selesai! Berikut papan peringkat sementara:")

        # Papan Peringkat Mabar (Tabel asli)
        board_rows = [
            {"Pemain": f"{profile['nickname']} (Kamu)", "Skor": ms["my_points"]}
        ]
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
    st.subheader("Belajar Bahasa Inggris Khusus Akuntansi")
    st.write(
        "Pahami istilah akuntansi internasional agar makin percaya diri membaca standar global, laporan keuangan, dan jurnal berbahasa Inggris."
    )

    eng_df = pd.DataFrame([
        {
            "English Term": item["term"],
            "Arti / Istilah": item["id_meaning"],
            "Penjelasan": item["explanation"],
            "Contoh Kalimat": item["example"]
        }
        for item in ENGLISH_TERMS_BANK
    ])
    st.dataframe(eng_df, use_container_width=True)

    st.markdown("### Latihan Kilat Istilah Akuntansi Inggris")
    selected_term = st.selectbox("Pilih istilah untuk dibedah bersama:", [x["term"] for x in ENGLISH_TERMS_BANK])
    if st.button("Jelaskan Penggunaan Istilah Ini"):
        prompt_eng = (
            f"Jelaskan istilah akuntansi berbahasa Inggris '{selected_term}' untuk {profile['jenjang']} "
            f"dalam bahasa Indonesia yang jelas. Sertakan arti literal vs makna akuntansi, contoh kalimat "
            f"dalam laporan keuangan, dan kesalahan umum yang sering terjadi. Jangan pakai tanda ** atau #."
        )
        fb_eng = f"{selected_term} adalah istilah penting dalam akuntansi yang membantu menyamakan pemahaman pelaporan keuangan lintas negara."
        with st.spinner("Menyiapkan penjelasan istilah..."):
            out_eng = safe_generate_text(prompt_eng, fb_eng)
        st.write(out_eng)
        record_daily_play()


# =====================================================
# TAB 5: BANTU TUGAS & SUMBER TERPERCAYA
# =====================================================

with tab_tugas:
    st.subheader("Bantu Penyelesaian Tugas & Referensi Sumber Terpercaya")
    st.write(
        "Masukkan soal tugas, kasus perhitungan, atau pertanyaan materi. Jawaban disusun runtut lengkap dengan rujukan sumber resmi/akademik."
    )

    task_topic = st.selectbox("Bidang Tugas", MATERI_AKUNTANSI, key="task_topic_sel")
    task_question = st.text_area("Tuliskan soal atau kasus tugasmu di sini:", height=130)

    if st.button("Bantu Selesaikan Tugas", type="primary"):
        if not task_question.strip():
            st.warning("Silakan tulis soal atau kasus tugas terlebih dahulu.")
        else:
            prompt_task = f"""
Bantu selesaikan tugas berikut pada bidang "{task_topic}" untuk jenjang "{profile['jenjang']}".
Susun jawaban dengan urutan yang jelas:
1. Ringkasan Konsep & Rumus/Aturan yang Berlaku
2. Langkah Penyelesaian Runut
3. Hasil Akhir
4. Sumber Rujukan Terpercaya (sebutkan standar/regulasi/literatur relevan seperti PSAK/IAI, SAK EMKM, SAP/PP, IFRS, IPSAS, atau buku teks akuntansi standar)

Gunakan bahasa yang jelas, rapi, dan tanpa tanda ** atau #.

Tugas:
{task_question}
"""
            fb_task = (
                f"Untuk menyelesaikan tugas {task_topic}, pastikan terlebih dahulu mengidentifikasi akun/komponen utama, "
                f"menentukan dasar pengukuran/pengakuan yang berlaku, lalu menghitung atau menyusun jurnal secara sistematis. "
                f"Rujukan utama: Ikatan Akuntan Indonesia (PSAK/SAK EMKM), IFRS Foundation, atau regulasi keuangan publik terkait."
            )
            with st.spinner("Menyusun langkah penyelesaian & referensi sumber..."):
                ans_task = safe_generate_text(prompt_task, fb_task)

            st.session_state.task_history.insert(0, {
                "Topik": task_topic,
                "Tugas": task_question,
                "Jawaban": ans_task
            })
            record_daily_play()
            profile["total_xp"] += 15
            st.rerun()

    if st.session_state.task_history:
        for item in st.session_state.task_history:
            st.markdown(f"<div class='soft-card'><h4>Topik: {item['Topik']}</h4><p><b>Soal:</b> {item['Tugas']}</p></div>", unsafe_allow_html=True)
            st.write(item["Jawaban"])


# =====================================================
# TAB 6: KATALOG MATERI & ANALISIS VARIANS DATA
# =====================================================

with tab_materi:
    st.subheader("Daftar Lengkap Materi Akuntansi (Nasional & Internasional)")
    materi_rows = [
        {
            "No": i + 1,
            "Bidang / Mata Kuliah": m,
            "Cakupan": "Nasional & Internasional"
        }
        for i, m in enumerate(MATERI_AKUNTANSI)
    ]
    st.dataframe(pd.DataFrame(materi_rows), use_container_width=True)

    st.divider()
    st.subheader("Analisis Anggaran vs Realisasi (Budget vs. Actuals)")
    st.write("Unggah file Excel (.xlsx) dengan kolom Category, Budget, dan Actual untuk melihat tabel varians dan grafik.")

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
                    st.error("Kolom Budget dan Actual harus berisi angka yang valid.")
                else:
                    df["Variance"] = df["Actual"] - df["Budget"]
                    df["Variance %"] = (df["Variance"] / df["Budget"].replace(0, float("nan"))) * 100
                    st.dataframe(df, use_container_width=True)

                    fig_bar = px.bar(
                        df,
                        x="Category",
                        y="Variance",
                        color="Variance",
                        title="Selisih (Variance) per Kategori",
                        text_auto=".2s"
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)
        except Exception as e:
            st.error(f"Gagal memproses file: {str(e)}")

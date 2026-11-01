import asyncio
import aiohttp
import sqlite3
import math
import random
import urllib.parse
import os
import re
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus, ChatType
import re
import os

# --- VIKTORINA FAYLLARINI TO'LIQ AVTOMATIK TUZATISH TIZIMI ---
quiz_files = ["quiz_tarix.py", "quiz_hadis.py", "quiz_quron.py", "quiz_shariat.py"]
for file in quiz_files:
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Tushib qolgan vergullarni qo'shish (} { -> }, {)
            content = re.sub(r'\}(\s*)\{', r'},\1{', content)

            # 2. Xato qo'shtirnoqlarni tuzatish (savol oxiri ' bo'lib qolgan bo'lsa)
            # Masalan: "q": "... kelgan?', "options":  ->  "q": "... kelgan?", "options":
            content = re.sub(r'\',\s*[\'\"]options[\'\"]\s*:', r'", "options":', content)
            content = re.sub(r'\'\s*,\s*[\'\"]options[\'\"]\s*:', r'", "options":', content)

            # 3. Fayl oxiridagi yopilmagan qavsni qo'shish
            if "QUESTIONS = [" in content:
                if not content.strip().endswith("]"):
                    content = content.strip() + "\n]\n"

            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
                
            print(f"✅ {file} muvaffaqiyatli tekshirildi va tuzatildi!")
        except Exception as e:
            print(f"⚠️ {file} faylini tuzatishda xatolik: {e}")
# -------------------------------------------------------------

# --- FAYLLARNI YUKLASH ---
try:
    from hadiths_data import HADITHS
except ImportError:
    HADITHS = ["Hadislar topilmadi."]

try:
    from marifiy_data import ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT
except ImportError:
    ALL_NAMES = [("Xatolik", "Fayl topilmadi", "marifiy_data.py yuklanmagan.")]
    SIYRAT_TEXT = TAHORAT_TEXT = RAMAZON_TEXT = "Ma'lumot yuklanmadi."

try:
    from duolar_data import DUOLAR
except ImportError:
    DUOLAR = {"xato": {"nomi": "Xatolik", "arabcha": "", "oqilishi": "", "tarjima": "duolar_data.py yuklanmagan", "manba": ""}}

try:
    from quiz_tarix import TARIX_QUESTIONS
    from quiz_hadis import HADIS_QUESTIONS
    from quiz_quron import QURON_QUESTIONS
    from quiz_shariat import SHARIAT_QUESTIONS
except ImportError:
    TARIX_QUESTIONS = HADIS_QUESTIONS = QURON_QUESTIONS = SHARIAT_QUESTIONS = []

# --- SOZLAMALAR ---
BOT_TOKEN = "9251800638:AAFPMR4CNKS_2hQASTLfs-31aK6mONiE9Mg"
API_ID = 24348700
API_HASH = "2e5778fd17289b5388a364c0ac495a64"

app = Client(
    "quran_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- GLOBAL HOLATLAR ---
USER_STATES = {}
TEMP_FAV = {}
SEARCH_CACHE = {}
ACTIVE_QUIZZES = {}

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS favorites
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS group_settings
                  (chat_id INTEGER PRIMARY KEY, timer INTEGER DEFAULT 15)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_stats
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, chat_id INTEGER, 
                   username TEXT, score INTEGER DEFAULT 0, date TEXT)''')
conn.commit()

try:
    quran_conn = sqlite3.connect('quran.db', check_same_thread=False)
    q_cursor_check = quran_conn.cursor()
    q_cursor_check.execute("SELECT COUNT(*) FROM quran")
    print(f"✅ QURAN.DB YUKLANDI: {q_cursor_check.fetchone()[0]} ta oyat!")
except Exception as e:
    print(f"❌ QURAN.DB XATO: {e}")
    quran_conn = None

# --- MA'LUMOTLAR ---
TASBEH_DHIKRS = [
    "Subhanalloh", "Alhamdulilloh", "Allohu Akbar", "La ilaha illalloh",
    "Astag'firulloh", "La havla va la quvvata illa billah",
    "Subhanallohi va bihamdihi", "Subhanallohil 'Aziym",
    "La ilaha illallohu vahdahu la sharika lah",
    "Allohumma solli 'ala Muhammad", "Bismillah",
    "Hasbunallohu va ni'mal vakil"
]
TASBEH_COUNTS = {}

RECITERS = {
    "Mishariy Alafasiy": "https://server8.mp3quran.net/afs/",
    "Abdulbosit Abdussamad": "https://server7.mp3quran.net/basit/",
    "Abdulloh Al-Juhaniy": "https://server13.mp3quran.net/jhn/",
    "Abdulmohsin Al-Qosim": "https://server8.mp3quran.net/qasm/",
    "Abdulvaliy Al-Arkoniy": "https://server6.mp3quran.net/arkani/",
    "Odil Al-Xalboniy": "https://server8.mp3quran.net/a_klb/",
    "Ahmad Al-Ajmiy": "https://server10.mp3quran.net/ajm/",
    "Abdurahmon As-Sudays": "https://server11.mp3quran.net/sds/",
    "Sa'd Ash-Shuraym": "https://server7.mp3quran.net/shur/",
    "Aliy Al-Huzayfiy": "https://server8.mp3quran.net/hthfi/"
}

SURA_NAMES = [
    "Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus",
    "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha",
    "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum",
    "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir",
    "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof",
    "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana",
    "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij",
    "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa",
    "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad",
    "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot",
    "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr",
    "Masad", "Ixlos", "Falaq", "Nos"
]

# --- YORDAMCHI FUNKSIYALAR ---
async def fetch_prayer_times(lat: float, lon: float) -> dict:
    url = "https://api.aladhan.com/v1/timings"
    params = {"latitude": lat, "longitude": lon, "method": 3}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            return (await resp.json())["data"]["timings"]

def calculate_qibla(lat: float, lon: float) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, 21.4225, 39.8262])
    x = math.sin(lon2 - lon1)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def get_direction_name(degree: float) -> str:
    if 337.5 <= degree or degree < 22.5: return "Shimol (North) ⬆️"
    elif 22.5 <= degree < 67.5: return "Shimoli-Sharq (North-East) ↗️"
    elif 67.5 <= degree < 112.5: return "Sharq (East) ➡️"
    elif 112.5 <= degree < 157.5: return "Janubi-Sharq (South-East) ↘️"
    elif 157.5 <= degree < 202.5: return "Janub (South) ⬇️"
    elif 202.5 <= degree < 247.5: return "Janubi-G'arb (South-West) ↙️"
    elif 247.5 <= degree < 292.5: return "G'arb (West) ⬅️"
    elif 292.5 <= degree < 337.5: return "Shimoli-G'arb (North-West) ↖️"
    return "Noma'lum"

def ramazon_days_left():
    delta = (datetime(2027, 2, 8, tzinfo=ZoneInfo("Asia/Tashkent")) - datetime.now(ZoneInfo("Asia/Tashkent"))).days
    return f"Ramazon oyiga {delta} kun qoldi." if delta > 0 else ("Bugun Ramazonning birinchi kuni!" if delta == 0 else "Ramazon oyi tugagan.")

# --- KLAVIATURALAR ---
def main_menu(rem=False, is_group=False):
    if is_group: return None
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")],
        [KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")],
        [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")],
        [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")],
        [KeyboardButton("🎮 Viktorina"), KeyboardButton("🏆 Haftalik Reyting")],
        [KeyboardButton("🔍 Qidiruv tizimi"), KeyboardButton("📚 Diniy ma'rifiy")]
    ], resize_keyboard=True)

def quiz_categories_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕋 Islom tarixi", callback_data="quiz_cat:tarix"), InlineKeyboardButton("📜 Hadislar", callback_data="quiz_cat:hadis")],
        [InlineKeyboardButton("📖 Qur'on", callback_data="quiz_cat:quron"), InlineKeyboardButton("⚖️ Shariat", callback_data="quiz_cat:shariat")]
    ])

def reciters_menu(page=0):
    items = list(RECITERS.items())[page*10:(page*10)+10]
    btns = [[InlineKeyboardButton(n, callback_data=f"reciter:{n}")] for n, u in items]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"reciter_page:{page-1}"))
    if (page*10)+10 < len(RECITERS): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"reciter_page:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

def surahs_menu(r_name, page=0):
    btns = [[InlineKeyboardButton(f"{i+1}. {SURA_NAMES[i]}", callback_data=f"surah:{r_name}:{i+1}")] for i in range(page*10, min((page*10)+10, 114))]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"surah_page:{r_name}:{page-1}"))
    if (page*10)+10 < 114: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"surah_page:{r_name}:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

def duolar_menu():
    btns = [[InlineKeyboardButton(d["nomi"], callback_data=f"duo:{k}")] for k, d in DUOLAR.items()]
    return InlineKeyboardMarkup(btns)

def tasbeh_dhikrs_menu():
    btns = []
    for i, dhikr in enumerate(TASBEH_DHIKRS):
        if i % 2 == 0: btns.append([InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}")])
        else: btns[-1].append(InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}"))
    return InlineKeyboardMarkup(btns)

def tasbeh_counter_menu(index, count):
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"🔢 Sanoq: {count}", callback_data="noop")], [InlineKeyboardButton("➕ Sanoqni oshirish", callback_data=f"tasbeh_add:{index}")], [InlineKeyboardButton("🔄 Tozalash", callback_data=f"tasbeh_reset:{index}")], [InlineKeyboardButton("⬅️ Zikrlar ro'yxati", callback_data="tasbeh_back")]])

def ilmiy_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🕋 Payg'ambar siyrati", callback_data="ilmiy:siyrat"), InlineKeyboardButton("🌙 Ramazon rejimi", callback_data="ilmiy:ramazon")], [InlineKeyboardButton("💧 Tahorat va Namoz", callback_data="ilmiy:tahorat"), InlineKeyboardButton("🌟 Allohning 99 ismi", callback_data="ilmiy:ismlar")]])

def names_menu(page=0):
    btns = [[InlineKeyboardButton(ALL_NAMES[i][0], callback_data=f"name:{i}")] for i in range(page*10, min((page*10)+10, len(ALL_NAMES)))]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"name_page:{page-1}"))
    if (page*10)+10 < len(ALL_NAMES): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"name_page:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

async def send_long_text(message_or_cb, text, kb=None):
    if len(text) <= 4000:
        if isinstance(message_or_cb, CallbackQuery):
            await message_or_cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
        else:
            await message_or_cb.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    else:
        if isinstance(message_or_cb, CallbackQuery):
            await message_or_cb.message.edit_text(text[:4000], disable_web_page_preview=True)
            msg_obj = message_or_cb.message
        else:
            await message_or_cb.edit_text(text[:4000], disable_web_page_preview=True)
            msg_obj = message_or_cb
            
        remaining_text = text[4000:]
        while len(remaining_text) > 0:
            chunk = remaining_text[:4000]
            await msg_obj.reply(chunk, disable_web_page_preview=True)
            remaining_text = remaining_text[4000:]
        if kb:
            await msg_obj.reply("⬆️ Yuqoridagi ma'lumotlarning davomi.", reply_markup=kb)
            # --- VIKTORINA YORDAMCHILARI ---
def prepare_questions(category):
    if category == "tarix": pool = TARIX_QUESTIONS[:]
    elif category == "hadis": pool = HADIS_QUESTIONS[:]
    elif category == "quron": pool = QURON_QUESTIONS[:]
    elif category == "shariat": pool = SHARIAT_QUESTIONS[:]
    else: pool = []

    if not pool: return []
    
    random.shuffle(pool)
    questions = []
    # O'yin uchun 10 ta savol olamiz
    for q in pool[:10]:
        options = list(q["options"])
        correct = q["answer"]
        if correct not in options or len(options) < 4: continue
        
        # Agar variantlar 4 tadan ko'p bo'lsa, 3 tasini random tanlab, to'g'risini qo'shamiz
        if len(options) > 4:
            options = random.sample([o for o in options if o != correct], 3) + [correct]
            
        random.shuffle(options)
        questions.append({"q": q["q"], "options": options, "correct_idx": options.index(correct)})
    return questions

# --- VIKTORINA ASOSIY MANTIG'I ---
@app.on_message(filters.command("viktorina"))
async def start_quiz_cmd(client, message: Message):
    # Guruhda ham, lichkada ham ishlaydi
    await message.reply("🎮 **Viktorina bo'limini tanlang:**", reply_markup=quiz_categories_menu())

@app.on_message(filters.regex(r"^🎮 Viktorina$") & filters.private)
async def start_quiz_btn(client, message: Message):
    await message.reply("🎮 **Viktorina bo'limini tanlang:**", reply_markup=quiz_categories_menu())

@app.on_callback_query(filters.regex(r"^quiz_cat:"))
async def select_quiz_category(client, callback_query: CallbackQuery):
    category = callback_query.data.split(":")[1]
    chat_id = callback_query.message.chat.id
    questions = prepare_questions(category)
    
    if not questions:
        return await callback_query.answer("Kechirasiz, bu bo'limda hozircha savollar yo'q!", show_alert=True)

    # Guruh sozlamalaridan vaqtni olamiz (agar guruh bo'lsa)
    timer = 15 # standart
    if callback_query.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        cursor.execute("SELECT timer FROM group_settings WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row: timer = row[0]

    ACTIVE_QUIZZES[chat_id] = {
        "questions": questions,
        "idx": 0,
        "timer": timer,
        "msg_id": None,
        "answered_by": set()
    }
    
    await callback_query.message.delete()
    await show_question(client, chat_id)

async def show_question(client, chat_id):
    state = ACTIVE_QUIZZES.get(chat_id)
    if not state: return
    
    if state["idx"] >= len(state["questions"]):
        return await end_quiz(client, chat_id)

    q = state["questions"][state["idx"]]
    text = f"❓ **Savol {state['idx']+1}/{len(state['questions'])}**\n\n{q['q']}"
    
    # Har bir variant uchun tugma
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(o, callback_data=f"ans:{state['idx']}:{i}")]
        for i, o in enumerate(q["options"])
    ])

    msg = await client.send_message(chat_id, text, reply_markup=kb)
    state["msg_id"] = msg.id
    state["answered_by"] = set()

    # Taymerni ishga tushirish (orqa fonda)
    asyncio.create_task(quiz_timer(client, chat_id, state["idx"], state["timer"]))

async def quiz_timer(client, chat_id, q_idx, timer_sec):
    await asyncio.sleep(timer_sec)
    state = ACTIVE_QUIZZES.get(chat_id)
    
    # Agar savol o'zgargan bo'lsa yoki o'yin tugagan bo'lsa, to'xtatamiz
    if not state or state["idx"] != q_idx: return 

    q = state["questions"][q_idx]
    correct_text = q["options"][q["correct_idx"]]
    
    try:
        await client.edit_message_text(
            chat_id, 
            state["msg_id"], 
            f"⏰ **Vaqt tugadi!**\n\n❓ {q['q']}\n\n✅ **To'g'ri javob:** {correct_text}", 
            reply_markup=None
        )
    except:
        pass

    await asyncio.sleep(2) # Keyingi savolga o'tishdan oldin 2 soniya kutish
    state["idx"] += 1
    await show_question(client, chat_id)

@app.on_callback_query(filters.regex(r"^ans:"))
async def check_answer(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    state = ACTIVE_QUIZZES.get(chat_id)
    
    if not state: 
        return await callback_query.answer("O'yin topilmadi yoki allaqachon tugagan.", show_alert=True)

    _, q_idx, opt_idx = callback_query.data.split(":")
    q_idx, opt_idx = int(q_idx), int(opt_idx)
    user = callback_query.from_user

    # Eski savolga javob berishga urinsa
    if q_idx != state["idx"]:
        return await callback_query.answer("Bu savol eskirgan.", show_alert=True)

    # Agar foydalanuvchi allaqachon javob bergan bo'lsa
    if user.id in state["answered_by"]:
        return await callback_query.answer("Siz bu savolga allaqachon javob bergansiz!", show_alert=True)

    # Javobni qabul qilamiz
    state["answered_by"].add(user.id)
    q = state["questions"][q_idx]
    correct_idx = q["correct_idx"]

    # Bazaga yozish (Haftalik reyting uchun)
    date_str = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
    score = 1 if opt_idx == correct_idx else 0
    
    cursor.execute(
        "INSERT INTO quiz_stats (user_id, chat_id, username, score, date) VALUES (?, ?, ?, ?, ?)",
        (user.id, chat_id, user.first_name, score, date_str)
    )
    conn.commit()

    if opt_idx == correct_idx:
        await callback_query.answer("✅ To'g'ri javob! +1 ball", show_alert=True)
    else:
        await callback_query.answer("❌ Xato javob!", show_alert=True)

async def end_quiz(client, chat_id):
    ACTIVE_QUIZZES.pop(chat_id, None)
    await client.send_message(
        chat_id, 
        "🏁 **Viktorina tugadi!**\n\nNatijalarni ko'rish uchun `/top` buyrug'ini bering yoki menyudan 'Haftalik Reyting'ni tanlang."
    )

# --- GURUH ADMINI UCHUN VAQT SOZLASH ---
@app.on_message(filters.command("vaqt"))
async def set_quiz_time(client, message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Faqatgina guruh adminlari vaqtni o'zgartira oladi!")
    except Exception:
        return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.reply("To'g'ri format: `/vaqt 20` (soniyalarda)")

    timer = int(parts[1])
    if timer < 5 or timer > 120:
        return await message.reply("Vaqt 5 soniyadan 120 soniyagacha bo'lishi kerak.")

    cursor.execute("INSERT OR REPLACE INTO group_settings (chat_id, timer) VALUES (?, ?)", (message.chat.id, timer))
    conn.commit()
    await message.reply(f"✅ Savolga beriladigan vaqt **{timer} soniya** etib belgilandi.")

# --- HAFTALIK REYTING (TOP 30) ---
@app.on_message(filters.command("top") | filters.regex(r"^🏆 Haftalik Reyting$"))
async def show_weekly_top(client, message: Message):
    chat_id = message.chat.id
    
    # Hafta boshlanish sanasini hisoblaymiz
    today = datetime.now(ZoneInfo("Asia/Tashkent"))
    start_of_week = today - timedelta(days=today.weekday())
    start_str = start_of_week.strftime("%Y-%m-%d")

    # Faqat shu chat_id (guruh yoki lichka) uchun va shu hafta ichida to'plangan ballarni hisoblaymiz
    cursor.execute(
        "SELECT username, SUM(score) as total FROM quiz_stats WHERE chat_id = ? AND date >= ? GROUP BY user_id ORDER BY total DESC LIMIT 30",
        (chat_id, start_str)
    )
    rows = cursor.fetchall()

    if not rows:
        return await message.reply("🏆 Bu hafta hali hech kim viktorinada qatnashmadi.")

    text = "🏆 **Haftalik TOP 30 Reyting:**\n\n"
    for i, row in enumerate(rows):
        name = row[0] or "Foydalanuvchi"
        score = row[1]
        # Medallar
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        text += f"{medal} {name} — **{score} ball**\n"
        
    await message.reply(text)
    # --- INLINE / CALLBACK HANDLERLARI ---
@app.on_callback_query(filters.regex(r"^reciter:"))
async def select_reciter(client, callback_query: CallbackQuery):
    reciter_name = callback_query.data.split(":", 1)[1]
    await callback_query.message.edit_text(f"🎧 **{reciter_name}**", reply_markup=surahs_menu(reciter_name, 0))

@app.on_callback_query(filters.regex(r"^reciter_page:"))
async def reciter_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_text("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(page))

@app.on_callback_query(filters.regex(r"^surah_page:"))
async def surah_page(client, callback_query: CallbackQuery):
    _, reciter_name, page_s = callback_query.data.split(":")
    page = int(page_s)
    await callback_query.message.edit_text(f"🎧 **{reciter_name}**", reply_markup=surahs_menu(reciter_name, page))

@app.on_callback_query(filters.regex(r"^surah:"))
async def send_audio(client, callback_query: CallbackQuery):
    await callback_query.answer("⏳ Audio yuklanmoqda...")
    _, reciter_name, surah_num = callback_query.data.split(":")
    surah_num = int(surah_num)
    audio_url = f"{RECITERS[reciter_name]}{surah_num:03d}.mp3"
    temp_file = f"temp_{surah_num}.mp3"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url, headers=headers) as resp:
                if resp.status != 200: raise Exception("Server xatosi")
                with open(temp_file, "wb") as f: f.write(await resp.read())
        await client.send_audio(callback_query.from_user.id, audio=temp_file, title=f"{surah_num}-sura", performer=reciter_name)
        await callback_query.message.delete()
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Xato: {str(e)}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

@app.on_callback_query(filters.regex(r"^duo:"))
async def send_duo(client, callback_query: CallbackQuery):
    key = callback_query.data.split(":")[1]
    duo = DUOLAR.get(key)
    if not duo:
        return await callback_query.answer("Topilmadi", show_alert=True)
    text = f"**{duo['nomi']}**\n\n**{duo['arabcha']}**\n\n**O'qilishi:** {duo['oqilishi']}\n\n**Ma'nosi:** {duo['tarjima']}\n\n**Manba:** {duo['manba']}"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"{duo['nomi']} - {duo['tarjima']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:duo:{fav_id}")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="duo_back")]])
    await callback_query.message.edit_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex(r"^duo_back$"))
async def duo_back(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("🤲 **Duolar**", reply_markup=duolar_menu())

@app.on_callback_query(filters.regex(r"^fav_save:"))
async def save_favorite(client, callback_query: CallbackQuery):
    _, ftype, fav_id = callback_query.data.split(":")
    fav_text = TEMP_FAV.get(fav_id)
    
    if fav_text:
        cursor.execute("INSERT INTO favorites (user_id, fav_type, fav_text) VALUES (?, ?, ?)", (callback_query.from_user.id, ftype, fav_text))
        conn.commit()
        del TEMP_FAV[fav_id]
        await callback_query.answer("⭐ Saqlandi!", show_alert=True)
        
        if ftype == "search":
            current_kb = callback_query.message.reply_markup.inline_keyboard
            new_kb = []
            for row in current_kb:
                new_row = []
                for btn in row:
                    if "Saqlash" in btn.text:
                        new_row.append(InlineKeyboardButton("✅ Saqlangan", callback_data="noop"))
                    else:
                        new_row.append(btn)
                new_kb.append(new_row)
            await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(new_kb))
        else:
            await callback_query.message.edit_reply_markup(reply_markup=None)
    else:
        await callback_query.answer("Xatolik: Ma'lumot topilmadi.", show_alert=True)

@app.on_callback_query(filters.regex(r"^tasbeh_select:"))
async def tasbeh_select(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    await callback_query.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[index]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(index, 0))

@app.on_callback_query(filters.regex(r"^tasbeh_add:"))
async def tasbeh_add(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = TASBEH_COUNTS.get(callback_query.from_user.id, 0) + 1
    await callback_query.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[index]}\n\n*Sanoq: {TASBEH_COUNTS[callback_query.from_user.id]}*", reply_markup=tasbeh_counter_menu(index, TASBEH_COUNTS[callback_query.from_user.id]))

@app.on_callback_query(filters.regex(r"^tasbeh_reset:"))
async def tasbeh_reset(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    await callback_query.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[index]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(index, 0))

@app.on_callback_query(filters.regex(r"^tasbeh_back$"))
async def tasbeh_back(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("📿 **Raqamli Tasbeh**\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_callback_query(filters.regex(r"^noop$"))
async def noop(client, callback_query: CallbackQuery):
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^ilmiy:"))
async def ilmiy_show(client, callback_query: CallbackQuery):
    q = callback_query.data.split(":")[1]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    if q == "siyrat":
        await send_long_text(callback_query, SIYRAT_TEXT, kb)
        return
    elif q == "ramazon":
        text = f"**🌙 Ramazon**\n\n{RAMAZON_TEXT}\n\n_{ramazon_days_left()}_"
    elif q == "tahorat":
        text = TAHORAT_TEXT
    elif q == "ismlar":
        text = "**🌟 Allohning 99 ismi**\n\nO'rganish uchun ismni tanlang:"
        kb = names_menu(0)
    else:
        text = "📚 Bo'limni tanlang:"
        kb = ilmiy_menu()
    await callback_query.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, callback_query: CallbackQuery):
    idx = int(callback_query.data.split(":")[1])
    name, meaning, tafsir = ALL_NAMES[idx]
    await callback_query.message.edit_text(f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n**Tafsiri:** {tafsir}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:ismlar")]]))

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_text("🌟 **Allohning 99 ismi**", reply_markup=names_menu(page))

# --- LOKATSIYANI YANGILASH (CALLBACK) ---
@app.on_callback_query(filters.regex(r"^update_location$"))
async def update_loc_callback(client, callback_query: CallbackQuery):
    await callback_query.message.delete()
    kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)], [KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)
    await callback_query.message.reply("Yangi lokatsiyangizni yuboring:", reply_markup=kb)

@app.on_message(filters.regex(r"^⬅️ Orqaga$"))
async def back_to_main_menu(client, message: Message):
    await message.reply("Asosiy menyu:", reply_markup=main_menu(False))

# --- ASOSIY XABAR HANDLERLARI ---
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message: Message):
    USER_STATES[message.from_user.id] = None
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    await message.reply("Assalomu alaykum! 🕌\nKerakli bo'limni tanlang:", reply_markup=main_menu(bool(user[0]) if user else False))

@app.on_message(filters.regex(r"^🎧 Qorilar va qiroatlar$"))
async def show_reciters(client, message: Message):
    await message.reply("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(0))

@app.on_message(filters.regex(r"^🤲 Duolar$"))
async def show_duolar(client, message: Message):
    await message.reply("🤲 **Sahih hadislardan olingan duolar**\n\nVaziyatni tanlang:", reply_markup=duolar_menu())

@app.on_message(filters.regex(r"^📿 Raqamli Tasbeh$"))
async def tasbeh_start(client, message: Message):
    TASBEH_COUNTS[message.from_user.id] = 0
    await message.reply("📿 **Raqamli Tasbeh**\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_message(filters.regex(r"^📖 Kunlik oyat$"))
async def get_ayah(client, message: Message):
    msg = await message.reply("⏳ Oyat qidirilmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alquran.cloud/v1/ayah/random/uz.sodik") as resp:
                data = await resp.json()
                ayah = data["data"]
                text = f"📖 **Kunlik oyat**\n\n_{ayah['text']}_\n\n*{ayah['surah']['name']} surasi, {ayah['numberInSurah']}-oyat*"
                fav_id = str(uuid.uuid4())
                TEMP_FAV[fav_id] = text
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:oyat:{fav_id}")]])
                await msg.edit_text(text, reply_markup=kb)
    except:
        await msg.edit_text("❌ Xatolik.")

@app.on_message(filters.regex(r"^📜 Kunlik hadis$"))
async def get_hadith(client, message: Message):
    hadith_text = random.choice(HADITHS)
    text = f"📜 **Hadis**\n\n_{hadith_text}_"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = text
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:hadis:{fav_id}")]])
    await message.reply(text, reply_markup=kb)

@app.on_message(filters.regex(r"^⭐ Sevimlilar$"))
async def show_favorites(client, message: Message):
    cursor.execute("SELECT fav_text FROM favorites WHERE user_id = ?", (message.from_user.id,))
    favs = cursor.fetchall()
    if not favs: return await message.reply("⭐ Sizda hali sevimli ma'lumotlar yo'q.")
    text = "⭐ **Sevimlilar:**\n\n"
    for fav in favs: text += f"• {fav[0][:100]}...\n\n"
    await message.reply(text)

@app.on_message(filters.regex(r"^📚 Diniy ma'rifiy$"))
async def ilmiy_menu_show(client, message: Message):
    await message.reply("📚 **Bo'limni tanlang:**", reply_markup=ilmiy_menu())

# --- QIDIRUV TIZIMI (Handlerlar) ---
async def show_search_result(message_or_cb, user_id: int, is_edit=False):
    cache = SEARCH_CACHE.get(user_id)
    if not cache or not cache["results"]: return
    
    idx = cache["idx"]
    total = len(cache["results"])
    surah_num, ayah_num, uzbek_text = cache["results"][idx]
    
    surah_name = SURA_NAMES[surah_num - 1] if 1 <= surah_num <= 114 else f"{surah_num}-sura"
    text = f"🔍 **'{cache['query']}' so'zi bo'yicha natija:**\n\n"
    text += f"📖 **{surah_name} surasi, {ayah_num}-oyat:**\n_{uzbek_text}_\n\n"
    
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"📖 {surah_name} surasi, {ayah_num}-oyat:\n{uzbek_text}"
    
    save_btn = [InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:search:{fav_id}")]
    
    nav = []
    if idx > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data="search_page:prev"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"))
    if idx < total - 1: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data="search_page:next"))
        
    kb = InlineKeyboardMarkup([save_btn, nav])
    
    if is_edit:
        await message_or_cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await message_or_cb.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^search_page:"))
async def search_pagination(client, callback_query: CallbackQuery):
    action = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    cache = SEARCH_CACHE.get(user_id)
    
    if not cache: return await callback_query.answer("Qidiruv natijasi eskirgan. Qaytadan qidiring.", show_alert=True)
        
    if action == "next" and cache["idx"] < len(cache["results"]) - 1: cache["idx"] += 1
    elif action == "prev" and cache["idx"] > 0: cache["idx"] -= 1
        
    await callback_query.answer()
    await show_search_result(callback_query, user_id, is_edit=True)

@app.on_message(filters.regex(r"^🔍 Qidiruv tizimi$"))
async def search_start(client, message: Message):
    USER_STATES[message.from_user.id] = "search"
    await message.reply("🔍 **Qidiruv rejimi yoqildi.**\n\nKetma-ket qidiruv uchun so'zlarni yozib yuboraverasiz. Qidiruvdan chiqish uchun boshqa bo'limni tanlang yoki /start bosing.")

@app.on_message(filters.text & filters.private & ~filters.regex(r"^/"))
async def handle_search_input(client, message: Message):
    if USER_STATES.get(message.from_user.id) != "search": return
        
    text = message.text.strip()
    
    menu_buttons = ["🕌 Namoz vaqtlari", "🧭 Qibla yo'nalishi", "🎧 Qorilar va qiroatlar", "🤲 Duolar", "📿 Raqamli Tasbeh", "📖 Kunlik oyat", "📜 Kunlik hadis", "⭐ Sevimlilar", "🎮 Viktorina", "🏆 Haftalik Reyting", "🔍 Qidiruv tizimi", "📚 Diniy ma'rifiy"]
    if text in menu_buttons:
        USER_STATES[message.from_user.id] = None
        return
        
    msg = await message.reply("⏳ Qur'on ichidan qidirilmoqda...")
    try:
        search_query = f"%{text.lower()}%"
        quran_cursor = quran_conn.cursor()
        quran_cursor.execute("SELECT surah_num, ayah_num, uzbek FROM quran WHERE LOWER(uzbek) LIKE ? LIMIT 50", (search_query,))
        results = quran_cursor.fetchall()
        
        if results:
            SEARCH_CACHE[message.from_user.id] = {"results": results, "idx": 0, "query": text}
            await show_search_result(msg, message.from_user.id)
        else:
            await msg.edit_text(f"❌ Kechirasiz, '{text}' so'zi bo'yicha hech narsa topilmadi.\n\nYana boshqa so'z yozib ko'rishingiz mumkin.", reply_markup=main_menu(False))
    except Exception as e:
        print(f"Qidiruv xatosi: {e}")
        await msg.edit_text("❌ Qidiruvda xatolik yuz berdi.", reply_markup=main_menu(False))

# --- ESLATMALAR ---
@app.on_message(filters.regex(r"^(🔔 Eslatmani yoqish|🔕 Eslatmani o'chirish)$"))
async def toggle_reminders(client, message: Message):
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, message.from_user.id))
    conn.commit()
    await message.reply("✅ Namoz eslatmalari yoqildi." if new_status == 1 else "🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu(new_status == 1))


# =====================================================================
# --- ENG PASTDAGI HANDLERLAR (QIDIRUV BILAN ARALASHMASLIGI UCHUN) ---
# =====================================================================

@app.on_message(filters.location)
async def handle_location(client, message: Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    cursor.execute("UPDATE users SET lat = ?, lon = ? WHERE user_id = ?", (message.location.latitude, message.location.longitude, message.from_user.id))
    conn.commit()
    await message.reply("✅ Lokatsiya saqlandi!", reply_markup=main_menu(False))

@app.on_message(filters.regex(r"^🕌 Namoz vaqtlari$"))
async def get_times(client, message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    
    if not user or not user[0]:
        kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)], [KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)
        return await message.reply("Namoz vaqtlarini aniqlash uchun iltimos, lokatsiyangizni yuboring:", reply_markup=kb)
        
    msg = await message.reply("⏳ Hisoblanmoqda...")
    try:
        timings = await fetch_prayer_times(user[0], user[1])
        text = f"🕌 **Bugungi namoz vaqtlari**\n\n" + "\n".join([f"• {label}: **{timings[name]}**" for name, label in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]])
        
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("📍 Lokatsiyani yangilash", callback_data="update_location")]])
        await msg.edit_text(text, reply_markup=kb)
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {e}")

@app.on_message(filters.regex(r"^🧭 Qibla yo'nalishi$"))
async def get_qibla(client, message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    
    if not user or not user[0]:
        kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)], [KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)
        return await message.reply("Qibla yo'nalishini aniqlash uchun iltimos, lokatsiyangizni yuboring:", reply_markup=kb)
        
    degree = calculate_qibla(user[0], user[1])
    direction = get_direction_name(degree)
    
    text = f"🧭 **Qibla yo'nalishi:**\n\n"
    text += f"Burchak: **{degree:.1f}°**\n"
    text += f"Yo'nalish: **{direction}**\n\n"
    text += f"📍 *Telefoningizdagi kompasni ochib, Shimolni toping va {degree:.1f}° burchakka yuzlaning.*"
    
    # Google Maps havolasi (Ka'ba koordinatalari: 21.4225, 39.8262)
    maps_url = "https://www.google.com/maps/dir/?api=1&destination=21.4225,39.8262"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🗺 Xaritada ko'rish", url=maps_url)],
        [InlineKeyboardButton("📍 Lokatsiyani yangilash", callback_data="update_location")]
    ])
    
    await message.reply(text, reply_markup=kb, disable_web_page_preview=True)

# --- ASOSIY LOOP ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

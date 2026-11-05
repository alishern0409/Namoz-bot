import asyncio
import aiohttp
import sqlite3
import math
import random
import urllib.parse
import os
import json
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

# --- AL-FALAK (OFFLINE NAMOZ VAQTI) ---
from alfalak import PrayerTimes, CalculationMethod, Coordinates

# --- AVTOMATIK TUZATUVCHI KOD ---
quiz_files = ["quiz_tarix.py", "quiz_hadis.py", "quiz_quron.py", "quiz_shariat.py"]
for file in quiz_files:
    if os.path.exists(file):
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            content = re.sub(r'\}(\s*)\{', r'},\1{', content)
            content = re.sub(r'\',\s*[\'\"]options[\'\"]\s*:', r'", "options":', content)
            content = re.sub(r'\'\s*,\s*[\'\"]options[\'\"]\s*:', r'", "options":', content)
            if "QUESTIONS = [" in content:
                if not content.strip().endswith("]"):
                    content = content.strip() + "\n]\n"
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception: pass

# --- FAYLLARNI YUKLASH ---
try: from hadiths_data import HADITHS
except: HADITHS = ["Hadislar topilmadi."]
try: from marifiy_data import ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT
except: ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT = [("Xatolik", "", "")], "", "", ""
try: from duolar_data import DUOLAR
except: DUOLAR = {"xato": {"nomi": "Xatolik", "arabcha": "", "oqilishi": "", "tarjima": "duolar_data.py yuklanmagan", "manba": ""}}
try:
    from quiz_tarix import TARIX_QUESTIONS
    from quiz_hadis import HADIS_QUESTIONS
    from quiz_quron import QURON_QUESTIONS
    from quiz_shariat import SHARIAT_QUESTIONS
except: TARIX_QUESTIONS = HADIS_QUESTIONS = QURON_QUESTIONS = SHARIAT_QUESTIONS = []

# --- SOZLAMALAR ---
BOT_TOKEN = "9251800638:AAFPMR4CNKS_2hQASTLfs-31aK6mONiE9Mg" # O'zingizning tokeningiz
API_ID = 24348700
API_HASH = "2e5778fd17289b5388a364c0ac495a64"
app = Client("quran_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- GLOBAL HOLATLAR ---
USER_STATES, TEMP_FAV, SEARCH_CACHE, ACTIVE_QUIZZES = {}, {}, {}, {}
TASBEH_COUNTS = {}

# --- QORILAR BAZASI (GITHUB UCHUN) ---
RECITERS = {}
# Agar internet yoki GitHub ishlamay qolsa, bot qulamayishi uchun zaxira:
DEFAULT_RECITERS = {
    "Mishariy Alafasiy": "https://server8.mp3quran.net/afs/",
    "Abdulbosit Abdussamad": "https://server7.mp3quran.net/basit/",
    "Abdulloh Al-Juhaniy": "https://server13.mp3quran.net/jhn/"
}

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS group_settings (chat_id INTEGER PRIMARY KEY, timer INTEGER DEFAULT 15)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, chat_id INTEGER, username TEXT, score INTEGER DEFAULT 0, date TEXT)''')
conn.commit()

try: 
    quran_conn = sqlite3.connect('quran.db', check_same_thread=False)
    print("✅ QURAN.DB MUVAFFAQIYATLI YUKLANDI!")
except: 
    quran_conn = None

# --- MA'LUMOTLAR ---
TASBEH_DHIKRS = ["Subhanalloh", "Alhamdulilloh", "Allohu Akbar", "La ilaha illalloh", "Astag'firulloh", "La havla va la quvvata illa billah", "Subhanallohi va bihamdihi", "Subhanallohil 'Aziym", "La ilaha illallohu vahdahu la sharika lah", "Allohumma solli 'ala Muhammad", "Bismillah", "Hasbunallohu va ni'mal vakil"]
SURA_NAMES = ["Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus", "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha", "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum", "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir", "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof", "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana", "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij", "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa", "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad", "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot", "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr", "Masad", "Ixlos", "Falaq", "Nos"]

def main_menu(rem=False, is_group=False):
    if is_group: return None
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")],
        [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")],
        [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")],
        [KeyboardButton("🎮 Viktorina"), KeyboardButton("🔍 Qidiruv tizimi")],
        [KeyboardButton("📚 Diniy ma'rifiy")],
        [KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")]
    ], resize_keyboard=True)

def duolar_menu(page=0):
    items = list(DUOLAR.items())
    start, end = page * 5, (page * 5) + 5
    btns = [[InlineKeyboardButton(d["nomi"], callback_data=f"duo:{k}")] for k, d in items[start:end]]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"duo_page:{page-1}"))
    if end < len(items): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"duo_page:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

def quiz_categories_menu():
    bot_link = "https://t.me/IslomiyBot?startgroup=true"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕋 Islom tarixi", callback_data="quiz_cat:tarix"), InlineKeyboardButton("📜 Hadislar", callback_data="quiz_cat:hadis")],
        [InlineKeyboardButton("📖 Qur'on", callback_data="quiz_cat:quron"), InlineKeyboardButton("⚖️ Shariat", callback_data="quiz_cat:shariat")],
        [InlineKeyboardButton("➕ Botni guruhga qo'shish", url=bot_link)]
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

# --- YORDAMCHI FUNKSIYALAR ---
async def load_reciters_from_github():
    global RECITERS
    # SIZNING GITHUB HAVOLANGIZ (Rasmdan olindi)
    github_url = "https://raw.githubusercontent.com/alishern0409/Namoz-bot/main/reciters.json"
    
    try:
       async with aiohttp.ClientSession() as session:
    async with session.get(github_url, timeout=10) as resp:
        if resp.status == 200:
            text_data = await resp.text() # Matn ko'rinishida o'qiymiz
            RECITERS = json.loads(text_data) # O'zimiz JSON ga aylantiramiz 
                    print(f"✅ GitHub'dan {len(RECITERS)} ta qori yuklandi!")
                else:
                    print("❌ GitHub'dan yuklashda xatolik. Status:", resp.status)
                    RECITERS = DEFAULT_RECITERS
    except Exception as e:
        print(f"❌ GitHub bilan aloqa yo'q: {e}")
        RECITERS = DEFAULT_RECITERS

async def fetch_prayer_times(lat: float, lon: float) -> dict:
    try:
        coords = Coordinates(lat, lon)
        tz = ZoneInfo("Asia/Tashkent")
        pt = PrayerTimes(coords, datetime.now(tz), CalculationMethod.MUSLIM_WORLD_LEAGUE, time_zone=tz)
        return {
            "Fajr": pt.fajr.strftime("%H:%M"),
            "Dhuhr": pt.dhuhr.strftime("%H:%M"),
            "Asr": pt.asr.strftime("%H:%M"),
            "Maghrib": pt.maghrib.strftime("%H:%M"),
            "Isha": pt.isha.strftime("%H:%M")
        }
    except Exception as e:
        print(f"❌ Hisoblashda xatolik: {e}")
        return None

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
def prepare_questions(category, count):
    if category == "tarix": pool = TARIX_QUESTIONS[:]
    elif category == "hadis": pool = HADIS_QUESTIONS[:]
    elif category == "quron": pool = QURON_QUESTIONS[:]
    elif category == "shariat": pool = SHARIAT_QUESTIONS[:]
    else: pool = []

    if not pool: return []
    
    random.shuffle(pool)
    questions = []
    for q in pool[:count]:
        options = list(q["options"])
        correct = q["answer"]
        if correct not in options or len(options) < 4: continue
        if len(options) > 4:
            options = random.sample([o for o in options if o != correct], 3) + [correct]
        random.shuffle(options)
        questions.append({"q": q["q"], "options": options, "correct_idx": options.index(correct)})
    return questions

@app.on_message(filters.command("viktorina"))
async def start_quiz_cmd(client, message: Message):
    await message.reply("🎮 **Viktorina bo'limini tanlang:**", reply_markup=quiz_categories_menu())

@app.on_message(filters.regex(r"^🎮 Viktorina$") & filters.private)
async def start_quiz_btn(client, message: Message):
    await message.reply("🎮 **Viktorina bo'limini tanlang:**", reply_markup=quiz_categories_menu())

@app.on_callback_query(filters.regex(r"^quiz_cat:"))
async def select_quiz_category(client, callback_query: CallbackQuery):
    category = callback_query.data.split(":")[1]
    USER_STATES[callback_query.from_user.id] = f"quiz_cat_{category}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ 10 ta savol", callback_data=f"quiz_len:10"), InlineKeyboardButton("2️⃣ 20 ta savol", callback_data=f"quiz_len:20")],
        [InlineKeyboardButton("3️⃣ 30 ta savol", callback_data=f"quiz_len:30"), InlineKeyboardButton("5️⃣ 50 ta savol", callback_data=f"quiz_len:50")]
    ])
    await callback_query.message.edit_text("Nechta savol o'ynaysiz? Tanlang:", reply_markup=kb)

@app.on_callback_query(filters.regex(r"^quiz_len:"))
async def start_quiz_actual(client, callback_query: CallbackQuery):
    count = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id
    chat_id = callback_query.message.chat.id
    
    state_val = USER_STATES.get(user_id)
    if not state_val or not state_val.startswith("quiz_cat_"):
        return await callback_query.answer("Xatolik. Qaytadan urinib ko'ring.", show_alert=True)
        
    category = state_val.replace("quiz_cat_", "")
    questions = prepare_questions(category, count)
    
    if not questions:
        return await callback_query.answer("Kechirasiz, bu bo'limda savollar tugagan!", show_alert=True)

    timer = 15
    if callback_query.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        cursor.execute("SELECT timer FROM group_settings WHERE chat_id = ?", (chat_id,))
        row = cursor.fetchone()
        if row: timer = row[0]

    ACTIVE_QUIZZES[chat_id] = {
        "questions": questions,
        "idx": 0,
        "timer": timer,
        "msg_id": None,
        "answered_by": set(),
        "session_scores": {} 
    }
    
    await callback_query.message.delete()
    await show_question(client, chat_id)

async def show_question(client, chat_id):
    state = ACTIVE_QUIZZES.get(chat_id)
    if not state: return
    
    if state["idx"] >= len(state["questions"]):
        return await end_quiz(client, chat_id)

    q = state["questions"][state["idx"]]
    text = f"❓ **Savol {state['idx']+1}/{len(state['questions'])}**\n⏳ _Vaqt: {state['timer']} soniya_\n\n{q['q']}"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(o, callback_data=f"ans:{state['idx']}:{i}")]
        for i, o in enumerate(q["options"])
    ])

    msg = await client.send_message(chat_id, text, reply_markup=kb)
    state["msg_id"] = msg.id
    state["answered_by"] = set()

    asyncio.create_task(quiz_timer(client, chat_id, state["idx"], state["timer"]))

async def quiz_timer(client, chat_id, q_idx, timer_sec):
    state = ACTIVE_QUIZZES.get(chat_id)
    if not state: return
    q = state["questions"][q_idx]
    
    for remaining in range(timer_sec - 3, 0, -3):
        await asyncio.sleep(3)
        if not ACTIVE_QUIZZES.get(chat_id) or ACTIVE_QUIZZES[chat_id]["idx"] != q_idx: return
        try:
            await client.edit_message_text(
                chat_id, state["msg_id"], 
                f"❓ **Savol {q_idx+1}/{len(state['questions'])}**\n⏳ _Qolgan vaqt: {remaining} soniya_\n\n{q['q']}"
            )
        except: pass

    await asyncio.sleep(timer_sec % 3 if timer_sec % 3 != 0 else 3)
    
    if not ACTIVE_QUIZZES.get(chat_id) or ACTIVE_QUIZZES[chat_id]["idx"] != q_idx: return 

    correct_text = q["options"][q["correct_idx"]]
    try:
        await client.edit_message_text(
            chat_id, state["msg_id"], 
            f"⏰ **Vaqt tugadi!**\n\n❓ {q['q']}\n\n✅ **To'g'ri javob:** {correct_text}", 
            reply_markup=None
        )
    except: pass

    await asyncio.sleep(2) 
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

    if q_idx != state["idx"]:
        return await callback_query.answer("Bu savol eskirgan.", show_alert=True)

    if user.id in state["answered_by"]:
        return await callback_query.answer("Siz bu savolga allaqachon javob bergansiz!", show_alert=True)

    state["answered_by"].add(user.id)
    q = state["questions"][q_idx]
    correct_idx = q["correct_idx"]

    if opt_idx == correct_idx:
        if user.id not in state["session_scores"]:
            state["session_scores"][user.id] = {"name": user.first_name, "score": 0}
        state["session_scores"][user.id]["score"] += 1
        
        date_str = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO quiz_stats (user_id, chat_id, username, score, date) VALUES (?, ?, ?, ?, ?)", (user.id, chat_id, user.first_name, 1, date_str))
        conn.commit()
        
        await callback_query.answer("✅ To'g'ri javob! +1 ball", show_alert=True)
    else:
        await callback_query.answer("❌ Xato javob!", show_alert=True)

async def end_quiz(client, chat_id):
    state = ACTIVE_QUIZZES.pop(chat_id, None)
    if not state: return
    
    scores = state.get("session_scores", {})
    if not scores:
        return await client.send_message(chat_id, "🏁 **Viktorina tugadi!**\n\nAfsuski, hech kim to'g'ri javob bera olmadi.")
        
    sorted_scores = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    
    text = "🏁 **Viktorina tugadi!**\n\n🏆 **O'yin natijalari (Top 10):**\n\n"
    for i, data in enumerate(sorted_scores[:10]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        text += f"{medal} {data['name']} — **{data['score']} ball**\n"
        
    await client.send_message(chat_id, text)

@app.on_message(filters.command("vaqt"))
async def set_quiz_time(client, message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        return await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
        
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply("Faqatgina guruh adminlari vaqtni o'zgartira oladi!")
    except: return

    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.reply("To'g'ri format: `/vaqt 20` (soniyalarda)")

    timer = int(parts[1])
    if timer < 5 or timer > 120:
        return await message.reply("Vaqt 5 soniyadan 120 soniyagacha bo'lishi kerak.")

    cursor.execute("INSERT OR REPLACE INTO group_settings (chat_id, timer) VALUES (?, ?)", (message.chat.id, timer))
    conn.commit()
    await message.reply(f"✅ Savolga beriladigan vaqt **{timer} soniya** etib belgilandi.")

@app.on_message(filters.command("top") & filters.private)
async def show_weekly_top(client, message: Message):
    today = datetime.now(ZoneInfo("Asia/Tashkent"))
    start_of_week = today - timedelta(days=today.weekday())
    start_str = start_of_week.strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT username, SUM(score) as total FROM quiz_stats WHERE date >= ? GROUP BY user_id ORDER BY total DESC LIMIT 30",
        (start_str,)
    )
    rows = cursor.fetchall()

    if not rows:
        return await message.reply("🏆 Bu hafta hali hech kim viktorinada qatnashmadi.")

    text = "🏆 **Haftalik TOP 30 Reyting (Barcha o'yinlar bo'yicha):**\n\n"
    for i, row in enumerate(rows):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        text += f"{medal} {row[0]} — **{row[1]} ball**\n"
        
    await message.reply(text)

# --- CALLBACK HANDLERLAR ---
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
    
    if reciter_name not in RECITERS:
        return await callback_query.answer("Xatolik: Qori topilmadi", show_alert=True)
        
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
    if not duo: return await callback_query.answer("Topilmadi", show_alert=True)
    text = f"**{duo['nomi']}**\n\n**{duo['arabcha']}**\n\n**O'qilishi:** {duo['oqilishi']}\n\n**Ma'nosi:** {duo['tarjima']}\n\n**Manba:** {duo['manba']}"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"{duo['nomi']} - {duo['tarjima']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:duo:{fav_id}")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="duo_back")]])
    await callback_query.message.edit_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex(r"^duo_back$"))
async def duo_back(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("🤲 **Duolar**", reply_markup=duolar_menu(0))

@app.on_callback_query(filters.regex(r"^duo_page:"))
async def duo_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_text("🤲 **Duolar**", reply_markup=duolar_menu(page))

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
                new_row = [InlineKeyboardButton("✅ Saqlangan", callback_data="noop") if "Saqlash" in btn.text else btn for btn in row]
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
    if q == "siyrat": await send_long_text(callback_query, SIYRAT_TEXT, kb); return
    elif q == "ramazon": text = f"**🌙 Ramazon**\n\n{RAMAZON_TEXT}\n\n_{ramazon_days_left()}_"
    elif q == "tahorat": text = TAHORAT_TEXT
    elif q == "ismlar": text = "**🌟 Allohning 99 ismi**\n\nO'rganish uchun ismni tanlang:"; kb = names_menu(0)
    else: text = "📚 Bo'limni tanlang:"; kb = ilmiy_menu()
    await callback_query.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, callback_query: CallbackQuery):
    name, meaning, tafsir = ALL_NAMES[int(callback_query.data.split(":")[1])]
    await callback_query.message.edit_text(f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n**Tafsiri:** {tafsir}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:ismlar")]]))

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("🌟 **Allohning 99 ismi**", reply_markup=names_menu(int(callback_query.data.split(":")[1])))

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
    USER_STATES[message.from_user.id] = None
    await message.reply("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(0))

@app.on_message(filters.regex(r"^🤲 Duolar$"))
async def show_duolar(client, message: Message): 
    USER_STATES[message.from_user.id] = None
    await message.reply("🤲 **Sahih hadislardan olingan duolar**\n\nVaziyatni tanlang:", reply_markup=duolar_menu(0))

@app.on_message(filters.regex(r"^📿 Raqamli Tasbeh$"))
async def tasbeh_start(client, message: Message):
    USER_STATES[message.from_user.id] = None
    TASBEH_COUNTS[message.from_user.id] = 0
    await message.reply("📿 **Raqamli Tasbeh**\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_message(filters.regex(r"^📖 Kunlik oyat$"))
async def get_ayah(client, message: Message):
    USER_STATES[message.from_user.id] = None
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
    except: await msg.edit_text("❌ Xatolik.")

@app.on_message(filters.regex(r"^📜 Kunlik hadis$"))
async def get_hadith(client, message: Message):
    USER_STATES[message.from_user.id] = None
    hadith_text = random.choice(HADITHS)
    text = f"📜 **Hadis**\n\n_{hadith_text}_"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = text
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:hadis:{fav_id}")]])
    await message.reply(text, reply_markup=kb)

@app.on_message(filters.regex(r"^⭐ Sevimlilar$"))
async def show_favorites(client, message: Message):
    USER_STATES[message.from_user.id] = None
    cursor.execute("SELECT fav_text FROM favorites WHERE user_id = ?", (message.from_user.id,))
    favs = cursor.fetchall()
    if not favs: return await message.reply("⭐ Sizda hali sevimli ma'lumotlar yo'q.")
    text = "⭐ **Sevimlilar:**\n\n"
    for fav in favs: text += f"• {fav[0][:100]}...\n\n"
    await message.reply(text)

@app.on_message(filters.regex(r"^📚 Diniy ma'rifiy$"))
async def ilmiy_menu_show(client, message: Message): 
    USER_STATES[message.from_user.id] = None
    await message.reply("📚 **Bo'limni tanlang:**", reply_markup=ilmiy_menu())

# --- QIDIRUV TIZIMI ---
async def show_search_result(message_or_cb, user_id: int, is_edit=False):
    cache = SEARCH_CACHE.get(user_id)
    if not cache or not cache["results"]: return
    idx = cache["idx"]
    total = len(cache["results"])
    surah_num, ayah_num, uzbek_text = cache["results"][idx]
    surah_name = SURA_NAMES[surah_num - 1] if 1 <= surah_num <= 114 else f"{surah_num}-sura"
    text = f"🔍 **'{cache['query']}' so'zi bo'yicha natija:**\n\n📖 **{surah_name} surasi, {ayah_num}-oyat:**\n_{uzbek_text}_\n\n"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"📖 {surah_name} surasi, {ayah_num}-oyat:\n{uzbek_text}"
    save_btn = [InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:search:{fav_id}")]
    nav = []
    if idx > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data="search_page:prev"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"))
    if idx < total - 1: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data="search_page:next"))
    kb = InlineKeyboardMarkup([save_btn, nav])
    if is_edit: await message_or_cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    else: await message_or_cb.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

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
            await msg.edit_text(f"❌ Kechirasiz, '{text}' so'zi bo'yicha hech narsa topilmadi.\n\nYana boshqa so'z yozib ko'rishingiz mumkin.")
    except Exception as e:
        print(f"Qidiruv xatosi: {e}")
        await msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

@app.on_message(filters.regex(r"^(🔔 Eslatmani yoqish|🔕 Eslatmani o'chirish)$"))
async def toggle_reminders(client, message: Message):
    USER_STATES[message.from_user.id] = None
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, message.from_user.id))
    conn.commit()
    await message.reply("✅ Namoz eslatmalari yoqildi." if new_status == 1 else "🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu(new_status == 1))


# ===== NAMOZ VAQTI VA QIBLA =====
namoz_kb = ReplyKeyboardMarkup(
    [
        [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)],
        [KeyboardButton("⬅️ Orqaga")]
    ], 
    resize_keyboard=True
)

@app.on_message(filters.text & filters.private, group=-1)
async def namoz_qibla_text_catch(client, message: Message):
    if "Namoz vaqtlari" in message.text:
        await message.reply("📍 Namoz vaqtlarini bilish uchun joylashuvingizni yuboring:", reply_markup=namoz_kb)
    elif "Qibla yo'nalishi" in message.text:
        await message.reply("🧭 Qibla yo'nalishini bilish uchun joylashuvni yuboring:", reply_markup=namoz_kb)

@app.on_message(filters.command("namoz"))
async def namoz_cmd(client, message: Message):
    await message.reply("📍 Namoz vaqtlarini bilish uchun joylashuvingizni yuboring:", reply_markup=namoz_kb)

@app.on_message(filters.command("qibla"))
async def qibla_cmd(client, message: Message):
    await message.reply("🧭 Qibla yo'nalishini bilish uchun joylashuvni yuboring:", reply_markup=namoz_kb)

@app.on_message(filters.location)
async def namoz_qibla_handler(client, message: Message):
    lat = message.location.latitude
    lon = message.location.longitude

    cursor.execute("INSERT OR REPLACE INTO users (user_id, lat, lon) VALUES (?, ?, ?)", (message.from_user.id, lat, lon))
    conn.commit()

    msg = await message.reply("⏳ Hisoblanmoqda...")

    try:
        times = await fetch_prayer_times(lat, lon)
        
        if not times:
            return await msg.edit_text("❌ Namoz vaqtlarini hisoblashda xatolik yuz berdi.")

        qibla = calculate_qibla(lat, lon)
        direction = get_direction_name(qibla)

        text = (
            f"🕌 **Namoz vaqtlari** (Mintaqangiz bo'yicha)\n\n"
            f"🌅 Bomdod: **{times['Fajr']}**\n"
            f"☀️ Peshin: **{times['Dhuhr']}**\n"
            f"🌤 Asr: **{times['Asr']}**\n"
            f"🌇 Shom: **{times['Maghrib']}**\n"
            f"🌙 Xufton: **{times['Isha']}**\n\n"
            f"🧭 **Qibla:** {qibla:.1f}° ({direction})\n"
            f"📍 Koordinatalar: {lat:.4f}, {lon:.4f}"
        )
        
        await msg.edit_text(text)
        await message.reply("Asosiy menyu:", reply_markup=main_menu())

    except Exception as e:
        try:
            await msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")
        except:
            pass

# --- ASOSIY LOOP ---
async def main():
    print("Bot ishga tushmoqda...")
    
    # GITHUB'DAN QORILARNI YUKLASH (Bot ishga tushishidan oldin)
    await load_reciters_from_github()
    
    await app.start()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

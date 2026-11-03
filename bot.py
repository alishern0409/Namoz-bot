import asyncio
import aiohttp
import sqlite3
import math
import random
import urllib.parse
import os
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, CallbackQuery, 
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)

# ==========================================
# --- MA'LUMOTLARNI YUKLASH ---
# ==========================================
try:
    from hadiths_data import HADITHS
except ImportError:
    HADITHS = ["Hadis fayli topilmadi."]

try:
    from duolar_data import DUOLAR
except ImportError:
    DUOLAR = {}

try:
    from marifiy_data import ALL_NAMES, TAHORAT_TEXT, RAMAZON_TEXT, SIYRAT_TEXT
except ImportError:
    ALL_NAMES = []
    TAHORAT_TEXT = "Tahorat ma'lumoti topilmadi."
    RAMAZON_TEXT = "Ramazon ma'lumoti topilmadi."
    SIYRAT_TEXT = "Siyrat ma'lumoti topilmadi."

try:
    from quiz_quron import QURON_QUESTIONS
except ImportError:
    QURON_QUESTIONS = [{"q": "Qur'on fayli topilmadi?", "options": ["A", "B"], "answer": "A"}]

try:
    from quiz_hadis import HADIS_QUESTIONS
except ImportError:
    HADIS_QUESTIONS = [{"q": "Hadis fayli topilmadi?", "options": ["A", "B"], "answer": "A"}]

try:
    from quiz_tarix import TARIX_QUESTIONS
except ImportError:
    TARIX_QUESTIONS = [{"q": "Tarix fayli topilmadi?", "options": ["A", "B"], "answer": "A"}]

try:
    from quiz_shariat import SHARIAT_QUESTIONS
except ImportError:
    SHARIAT_QUESTIONS = [{"q": "Shariat fayli topilmadi?", "options": ["A", "B"], "answer": "A"}]


# --- SOZLAMALAR ---
BOT_TOKEN = "9244020327:AAE4ae-hddNmTu52OU8bkq-aTObXHIROsss"
ADMIN_ID = 8718072369
API_ID = 24348700
API_HASH = "2e5778fd17289b5388a364c0ac495a64"

app = Client(
    "quran_bot_session",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# --- HOLATLAR VA VAQTINCHALIK XOTIRA ---
USER_STATES = {}
TEMP_FAV = {} 
TASBEH_COUNTS = {}

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS favorites
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)''')
conn.commit()

# --- 20 TA TASBEH ZIKRLARI ---
TASBEH_DHIKRS = [
    "Subhanalloh", "Alhamdulilloh", "Allohu Akbar", "La ilaha illalloh",
    "Astag'firulloh", "La havla va la quvvata illa billah", 
    "Subhanallohi va bihamdihi", "Subhanallohil 'Aziym",
    "La ilaha illallohu vahdahu la sharika lah", 
    "Allohumma solli 'ala Muhammad", "Bismillah",
    "Hasbunallohu va ni'mal vakil", 
    "La ilaha illa anta subhanaka inni kuntu minaz zolimin",
    "Ya Hayyu ya Qayyum birahmatika astag'is",
    "Rabbana atina fid dunya hasanatan va fil akhirati hasanatan va qina 'azaban nar",
    "Allohumma inni as'alukal jannata va a'uzu bika minan nar",
    "Robbi zidni 'ilma", "Robbi ighfir li va li validayya",
    "Allohumma ighfir li zanbi kullahu",
    "Subhanallohi va bihamdihi subhanallohil 'Aziym"
]

# --- QORILAR ---
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
    "Aliy Al-Huzayfiy": "https://server8.mp3quran.net/hthfi/",
    "Faris Abbod": "https://server8.mp3quran.net/frs_a/",
    "Solih Bukhotir": "https://server8.mp3quran.net/bu_khtr/",
    "Muhammad Al-Minshoviy": "https://server10.mp3quran.net/minsh/",
    "Mustafo Ismoil": "https://server8.mp3quran.net/mustafa/",
    "Mahmud Al-Banno": "https://server8.mp3quran.net/banna/",
    "Nosir Al-Qatamiy": "https://server8.mp3quran.net/qat/",
    "Mohir Al-Muayqliy": "https://server12.mp3quran.net/maher/",
    "Honiy Ar-Rifoiy": "https://server8.mp3quran.net/hani/",
    "Yosir Ad-Dosariy": "https://server11.mp3quran.net/yasser/",
    "Abu Bakr Ash-Shatriy": "https://server11.mp3quran.net/shatri/"
}

SURA_NAMES = ["Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus", "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha", "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum", "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir", "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof", "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana", "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij", "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa", "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad", "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot", "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr", "Masad", "Ixlos", "Falaq", "Nos"]

# --- YORDAMCHI FUNKSIYALAR ---
async def fetch_prayer_times(lat: float, lon: float) -> dict:
    url = "https://api.aladhan.com/v1/timings"
    params = {"latitude": lat, "longitude": lon, "method": 3}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            return data["data"]["timings"]

def calculate_qibla(lat: float, lon: float) -> float:
    kaaba_lat, kaaba_lon = 21.4225, 39.8262
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, kaaba_lat, kaaba_lon])
    diff_lon = lon2 - lon1
    x = math.sin(diff_lon)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(diff_lon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

def ramazon_days_left():
    now = datetime.now(ZoneInfo("Asia/Tashkent"))
    ramazon_start = datetime(2027, 2, 8, tzinfo=ZoneInfo("Asia/Tashkent"))
    delta = (ramazon_start - now).days
    if delta > 0: return f"Ramazon oyiga {delta} kun qoldi."
    elif delta == 0: return "Bugun Ramazonning birinchi kuni!"
    else: return "Ramazon oyi tugagan."

# --- KLAVIATURALAR ---
def main_menu(reminders_status=False):
    belgi = "🔕 Eslatmani o'chirish" if reminders_status else "🔔 Eslatmani yoqish"
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")],
        [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")],
        [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")],
        [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")],
        [KeyboardButton("🎮 Viktorina"), KeyboardButton("🔍 Qidiruv tizimi")],
        [KeyboardButton("📚 Diniy ma'rifiy"), KeyboardButton(belgi)],
        [KeyboardButton("📍 Lokatsiyani yangilash", request_location=True)]
    ], resize_keyboard=True)

def reciters_menu(page=0):
    items = list(RECITERS.items())
    buttons = []
    start, end = page * 10, (page * 10) + 10
    for name, url in items[start:end]:
        buttons.append([InlineKeyboardButton(name, callback_data=f"reciter:{name}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"reciter_page:{page-1}"))
    if end < len(items): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"reciter_page:{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

def surahs_menu(reciter_name, page=0):
    buttons = []
    start, end = page * 10, (page * 10) + 10
    for i in range(start, min(end, 114)):
        buttons.append([InlineKeyboardButton(f"{i+1}. {SURA_NAMES[i]}", callback_data=f"surah:{reciter_name}:{i+1}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"surah_page:{reciter_name}:{page-1}"))
    if end < 114: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"surah_page:{reciter_name}:{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

def duolar_menu():
    buttons = []
    for key, duo in DUOLAR.items():
        buttons.append([InlineKeyboardButton(duo["nomi"], callback_data=f"duo:{key}")])
    return InlineKeyboardMarkup(buttons)

def tasbeh_dhikrs_menu():
    buttons = []
    for i, dhikr in enumerate(TASBEH_DHIKRS):
        if i % 2 == 0:
            buttons.append([InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}")])
        else:
            buttons[-1].append(InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}"))
    return InlineKeyboardMarkup(buttons)

def tasbeh_counter_menu(index, count):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🔢 Sanoq: {count}", callback_data="noop")],
        [InlineKeyboardButton("➕ Sanoqni oshirish", callback_data=f"tasbeh_add:{index}")],
        [InlineKeyboardButton("🔄 Tozalash", callback_data=f"tasbeh_reset:{index}")],
        [InlineKeyboardButton("⬅️ Zikrlar ro'yxati", callback_data="tasbeh_back")]
    ])

def ilmiy_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕋 Payg'ambar siyrati", callback_data="ilmiy:siyrat"), InlineKeyboardButton("🌙 Ramazon rejimi", callback_data="ilmiy:ramazon")],
        [InlineKeyboardButton("💧 Tahorat va Namoz", callback_data="ilmiy:tahorat"), InlineKeyboardButton("🌟 Allohning 99 ismi", callback_data="ilmiy:ismlar")]
    ])

def names_menu(page=0):
    buttons = []
    start, end = page * 10, (page * 10) + 10
    for i in range(start, min(end, len(ALL_NAMES))):
        buttons.append([InlineKeyboardButton(ALL_NAMES[i][0], callback_data=f"name:{i}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"name_page:{page-1}"))
    if end < len(ALL_NAMES): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"name_page:{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

def viktorina_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕋 Islom tarixi", callback_data="quiz_start:tarix"), InlineKeyboardButton("📜 Hadislar", callback_data="quiz_start:hadis")],
        [InlineKeyboardButton("📖 Qur'on", callback_data="quiz_start:quron"), InlineKeyboardButton("⚖️ Shariat", callback_data="quiz_start:shariat")]
    ])


# ==========================================
# --- DISPATCHER (BARCHA MATNLAR UCHUN) ---
# ==========================================
@app.on_message(filters.text & filters.private & ~filters.regex(r"^/"))
async def handle_text_messages(client, message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # 1. QIDIRUV REJIMI
    if USER_STATES.get(user_id) == "search":
        menu_buttons = [
            "🕌 Namoz vaqtlari", "🧭 Qibla yo'nalishi", "🎧 Qorilar va qiroatlar", 
            "🤲 Duolar", "📿 Raqamli Tasbeh", "📖 Kunlik oyat", "📜 Kunlik hadis", 
            "⭐ Sevimlilar", "🎮 Viktorina", "🔍 Qidiruv tizimi", "📚 Diniy ma'rifiy", 
            "⚙️ Sozlamalar", "📍 Lokatsiyani yangilash", "🔔 Eslatmani yoqish", "🔕 Eslatmani o'chirish"
        ]
        
        if text not in menu_buttons:
            USER_STATES[user_id] = None
            msg = await message.reply("⏳ Qidirilmoqda...")
            try:
                encoded_text = urllib.parse.quote(text)
                url = f"https://api.alquran.cloud/v1/search/{encoded_text}/all/uz.sodik"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as resp:
                        data = await resp.json()
                        if data["code"] == 200 and data["data"]["count"] > 0:
                            res = f"🔍 **'{text}' so'zi bo'yicha natijalar:**\n\n"
                            for match in data["data"]["matches"][:5]:
                                res += f"📖 **{match['surah']['name']} {match['numberInSurah']}-oyat:**\n_{match['text']}_\n\n"
                            await msg.edit_text(res, reply_markup=main_menu(False))
                        else:
                            await msg.edit_text(f"❌ Kechirasiz, '{text}' so'zi bo'yicha hech narsa topilmadi.", reply_markup=main_menu(False))
            except Exception as e:
                await msg.edit_text("❌ Qidiruvda xatolik yuz berdi.", reply_markup=main_menu(False))
            return

    # 2. MENYU TUGMALARI
    if text == "🕌 Namoz vaqtlari":
        cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user or user[0] is None or user[1] is None:
            return await message.reply("Iltimos, avval pastdagi **'📍 Lokatsiyani yangilash'** tugmasini bosib, lokatsiya yuboring.")
        
        msg = await message.reply("⏳ Hisoblanmoqda...")
        try:
            timings = await fetch_prayer_times(user[0], user[1])
            res_text = f"🕌 **Bugungi namoz vaqtlari**\n\n" + "\n".join([f"• {label}: **{timings[name]}**" for name, label in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]])
            await msg.edit_text(res_text)
        except Exception:
            await msg.edit_text("❌ Xatolik: API server javob bermayapti. Internet aloqasini tekshiring.")

    elif text == "🧭 Qibla yo'nalishi":
        cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user or user[0] is None or user[1] is None:
            return await message.reply("Iltimos, avval pastdagi **'📍 Lokatsiyani yangilash'** tugmasini bosib, lokatsiya yuboring.")
        
        degree = calculate_qibla(user[0], user[1])
        await message.reply(f"🧭 **Qibla yo'nalishi:** **{degree:.1f}°**")

    elif text == "🎧 Qorilar va qiroatlar":
        await message.reply("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(0))

    elif text == "🤲 Duolar":
        await message.reply("🤲 **Sahih hadislardan olingan duolar**\n\nVaziyatni tanlang:", reply_markup=duolar_menu())

    elif text == "📿 Raqamli Tasbeh":
        TASBEH_COUNTS[user_id] = 0
        await message.reply("📿 **Raqamli Tasbeh**\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", reply_markup=tasbeh_dhikrs_menu())

    elif text == "📖 Kunlik oyat":
        msg = await message.reply("⏳ Oyat qidirilmoqda...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.alquran.cloud/v1/ayah/random/uz.sodik") as resp:
                    data = await resp.json()
                    ayah = data["data"]
                    ayah_text = f"📖 **Kunlik oyat**\n\n_{ayah['text']}_\n\n*{ayah['surah']['name']} surasi, {ayah['numberInSurah']}-oyat*"
                    
                    fav_id = str(uuid.uuid4())
                    TEMP_FAV[fav_id] = ayah_text
                    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:oyat:{fav_id}")]])
                    await msg.edit_text(ayah_text, reply_markup=kb)
        except:
            await msg.edit_text("❌ Xatolik yuz berdi.")

    elif text == "📜 Kunlik hadis":
        if not HADITHS: return await message.reply("Hadislar topilmadi.")
        hadith_text = random.choice(HADITHS)
        hadith_msg = f"📜 **Hadis**\n\n_{hadith_text}_"
        fav_id = str(uuid.uuid4())
        TEMP_FAV[fav_id] = hadith_msg
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:hadis:{fav_id}")]])
        await message.reply(hadith_msg, reply_markup=kb)

    elif text == "⭐ Sevimlilar":
        cursor.execute("SELECT fav_text FROM favorites WHERE user_id = ?", (user_id,))
        favs = cursor.fetchall()
        if not favs: return await message.reply("⭐ Sizda hali sevimli ma'lumotlar yo'q.")
        res = "⭐ **Sevimlilar:**\n\n"
        for fav in favs: res += f"• {fav[0][:100]}...\n\n"
        await message.reply(res)

    elif text == "🎮 Viktorina":
        await message.reply("🎮 **Viktorina bo'limini tanlang:**", reply_markup=viktorina_menu())

    elif text == "📚 Diniy ma'rifiy":
        await message.reply("📚 **Bo'limni tanlang:**", reply_markup=ilmiy_menu())

    elif text == "🔍 Qidiruv tizimi":
        USER_STATES[user_id] = "search"
        await message.reply("🔍 **Qidiruv rejimi yoqildi.**\n\nKetma-ket qidiruv uchun so'zlarni yozib yuboraverasiz. Qidiruvdan chiqish uchun boshqa bo'limni tanlang yoki /start bosing.")

    elif text in ["🔔 Eslatmani yoqish", "🔕 Eslatmani o'chirish"]:
        cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user: 
            return await message.reply("Iltimos, avval lokatsiya yuboring.")
        
        new_status = 0 if user[0] == 1 else 1
        cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, user_id))
        conn.commit()
        await message.reply("✅ Namoz eslatmalari yoqildi." if new_status == 1 else "🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu(new_status == 1))

# ==========================================
# --- LOKATSIYA VA START ---
# ==========================================
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message: Message):
    USER_STATES[message.from_user.id] = None 
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    await message.reply("Assalomu alaykum! 🕌\nKerakli bo'limni tanlang:", reply_markup=main_menu(bool(user[0]) if user else False))

@app.on_message(filters.location)
async def handle_location(client, message: Message):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    cursor.execute("UPDATE users SET lat = ?, lon = ? WHERE user_id = ?", (message.location.latitude, message.location.longitude, message.from_user.id))
    conn.commit()
    await message.reply("✅ Lokatsiya saqlandi! Endi namoz vaqtlari va qiblani bilib olishingiz mumkin.", reply_markup=main_menu(False))

# ==========================================
# --- INLINE / CALLBACK HANDLERLARI ---
# ==========================================
@app.on_callback_query(filters.regex(r"^reciter:"))
async def select_reciter(client, callback_query: CallbackQuery):
    reciter_name = callback_query.data.split(":")[1]
    await callback_query.message.edit_text(f"🎧 **{reciter_name}**", reply_markup=surahs_menu(reciter_name, 0))

@app.on_callback_query(filters.regex(r"^reciter_page:"))
async def reciter_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_reply_markup(reply_markup=reciters_menu(page))

@app.on_callback_query(filters.regex(r"^surah_page:"))
async def surah_page(client, callback_query: CallbackQuery):
    _, reciter_name, page = callback_query.data.split(":")
    await callback_query.message.edit_reply_markup(reply_markup=surahs_menu(reciter_name, int(page)))

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
        await callback_query.message.edit_text(f"❌ Xato: Audio yuklab bo'lmadi.")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

@app.on_callback_query(filters.regex(r"^duo:"))
async def send_duo(client, callback_query: CallbackQuery):
    key = callback_query.data.split(":")[1]
    duo = DUOLAR.get(key)
    if not duo: return await callback_query.answer("Duo topilmadi.", show_alert=True)
    
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
        await callback_query.message.edit_reply_markup(reply_markup=None)
    else:
        await callback_query.answer("Xatolik: Ma'lumot eskirgan.", show_alert=True)

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
    await callback_query.message.edit_text("📿 **Raqamli Tasbeh**\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_callback_query(filters.regex(r"^ilmiy:"))
async def ilmiy_show(client, callback_query: CallbackQuery):
    q = callback_query.data.split(":")[1]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    
    if q == "siyrat": text = SIYRAT_TEXT
    elif q == "ramazon": text = f"**🌙 Ramazon**\n\n{RAMAZON_TEXT}\n\n{ramazon_days_left()}"
    elif q == "tahorat": text = TAHORAT_TEXT
    elif q == "ismlar": 
        text = "**🌟 Allohning 99 ismi**"
        kb = names_menu(0)
    else: 
        text = "📚 **Bo'limni tanlang:**"
        kb = ilmiy_menu()
        
    if len(text) > 4000:
        # Agar matn juda uzun bo'lsa bo'lib yuborish kerak, lekin hozircha qisqartiramiz
        text = text[:4000] + "..."
        
    await callback_query.message.edit_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_reply_markup(reply_markup=names_menu(page))

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, callback_query: CallbackQuery):
    idx = int(callback_query.data.split(":")[1])
    if idx >= len(ALL_NAMES): return await callback_query.answer("Topilmadi.")
    name, meaning, tafsir = ALL_NAMES[idx]
    await callback_query.message.edit_text(f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n**Tafsiri:** {tafsir}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:ismlar")]]))

# --- VIKTORINA ---
@app.on_callback_query(filters.regex(r"^quiz_start:"))
async def quiz_start(client, callback_query: CallbackQuery):
    q_type = callback_query.data.split(":")[1]
    if q_type == "tarix": questions = TARIX_QUESTIONS
    elif q_type == "hadis": questions = HADIS_QUESTIONS
    elif q_type == "quron": questions = QURON_QUESTIONS
    elif q_type == "shariat": questions = SHARIAT_QUESTIONS
    else: return await callback_query.answer("Mavzu topilmadi.")

    q = random.choice(questions)
    # Variantlarni aralashtirish
    opts = q['options'][:]
    random.shuffle(opts)
    
    kb = InlineKeyboardMarkup([[InlineKeyboardButton(o, callback_data=f"quiz_ans:{q['answer']}:{o}")] for o in opts])
    await callback_query.message.edit_text(f"🎮 **Viktorina**\n\n{q['q']}", reply_markup=kb)

@app.on_callback_query(filters.regex(r"^quiz_ans:"))
async def quiz_answer(client, callback_query: CallbackQuery):
    _, correct, chosen = callback_query.data.split(":")
    if chosen == correct:
        await callback_query.answer("✅ To'g'ri javob!", show_alert=True)
    else:
        await callback_query.answer(f"❌ Xato! To'g'ri javob: {correct}", show_alert=True)

# ==========================================
# --- ISHGA TUSHIRISH ---
# ==========================================
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

import asyncio, aiohttp, sqlite3, math, random, urllib.parse, os, re, uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pyrogram import Client, filters, idle
from pyrogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- FAYLLARNI YUKLASH ---
if os.path.exists("quiz_data.py"):
    try:
        with open("quiz_data.py", "r", encoding="utf-8") as f: content = f.read()
        fixed_content = re.sub(r'\}(\s*)\{', r'},\1{', content)
        if fixed_content != content:
            with open("quiz_data.py", "w", encoding="utf-8") as f: f.write(fixed_content)
    except Exception: pass

try: from hadiths_data import HADITHS
except ImportError: HADITHS = ["Hadislar fayli topilmadi."]

try: from quiz_data import QUIZ_QUESTIONS
except Exception: QUIZ_QUESTIONS = []

try:
    from marifiy_data import ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT
except ImportError:
    ALL_NAMES = [("Xatolik", "Fayl topilmadi", "marifiy_data.py yuklanmagan.")]
    SIYRAT_TEXT = TAHORAT_TEXT = RAMAZON_TEXT = "Ma'lumot yuklanmadi."

# --- SOZLAMALAR ---
BOT_TOKEN = "9244020327:AAE4ae-hddNmTu52OU8bkq-aTObXHIROsss"
API_ID = 24348700
API_HASH = "2e5778fd17289b5388a364c0ac495a64"
app = Client("quran_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

USER_STATES, TEMP_FAV, QUIZ_STATE = {}, {}, {}
QUESTIONS_PER_QUIZ = 10

conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0)')
cursor.execute('CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)')
conn.commit()

TASBEH_DHIKRS = ["Subhanalloh", "Alhamdulilloh", "Allohu Akbar", "La ilaha illalloh", "Astag'firulloh", "La havla va la quvvata illa billah", "Subhanallohi va bihamdihi", "Subhanallohil 'Aziym", "La ilaha illallohu vahdahu la sharika lah", "Allohumma solli 'ala Muhammad", "Bismillah", "Hasbunallohu va ni'mal vakil", "La ilaha illa anta subhanaka inni kuntu minaz zolimin", "Ya Hayyu ya Qayyum birahmatika astag'is", "Rabbana atina fid dunya hasanatan va fil akhirati hasanatan va qina 'azaban nar", "Allohumma inni as'alukal jannata va a'uzu bika minan nar", "Robbi zidni 'ilma", "Robbi ighfir li va li validayya", "Allohumma ighfir li zanbi kullahu", "Subhanallohi va bihamdihi subhanallohil 'Aziym"]
TASBEH_COUNTS = {}

DUOLAR = {
    "uydan_chiqish": {"nomi": "🚪 Uydan chiqish", "arabcha": "بِسْمِ اللَّهِ، تَوَكَّلْتُ عَلَى اللَّهِ، وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ", "oqilishi": "Bismillahi, tavakkaltu 'alallohi, va la havla va la quvvata illa billah.", "tarjima": "Allohning nomi bilan (chiqaman). Allohga tavakkal qildim.", "manba": "Abu Dovud"},
    "uyga_kirish": {"nomi": "🏠 Uyga kirish", "arabcha": "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ الْمَوْلَجِ وَخَيْرَ الْمَخْرَجِ", "oqilishi": "Allohumma inni as'aluka xayral mavlaji va xayral maxraji.", "tarjima": "Allohim, Sendan eng yaxshi kirish va chiqishni so'rayman.", "manba": "Abu Dovud"},
    "ovqatdan_oldin": {"nomi": "🍽 Ovqatdan oldin", "arabcha": "بِسْمِ اللَّهِ", "oqilishi": "Bismillah.", "tarjima": "Allohning nomi bilan.", "manba": "Buxoriy"},
    "ovqatdan_keyin": {"nomi": "🍽 Ovqatdan keyin", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مِنَ الْمُسْلِمِينَ", "oqilishi": "Alhamdulillahillazi at'amana va saqona va ja'alana minal muslimin.", "tarjima": "Bizni taomlantirgan Allohga hamd bo'lsin.", "manba": "Termiziy"},
    "uyqudan_oldin": {"nomi": "🌙 Uyqudan oldin", "arabcha": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "oqilishi": "Bismikallohumma amutu va ahya.", "tarjima": "Allohim, Sening isming bilan o'laman va tirilaman.", "manba": "Buxoriy"},
    "uyqudan_uygonish": {"nomi": "☀️ Uyqudan uyg'onish", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ", "oqilishi": "Alhamdulillahillazi ahyana ba'da ma amatana va ilayhin nushur.", "tarjima": "Bizni tiriltirgan Allohga hamd bo'lsin.", "manba": "Buxoriy"},
    "istigfor": {"nomi": "🤲 Sayyidul Istig'for", "arabcha": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ", "oqilishi": "Allohumma anta Robbi la ilaha illa anta, xalaqtani va ana 'abduka.", "tarjima": "Allohim, Sen mening Rabbimsan, Meni yaratding, men Sening bandangman.", "manba": "Buxoriy"}
}

RECITERS = {"Mishariy Alafasiy": "https://server8.mp3quran.net/afs/", "Abdulbosit Abdussamad": "https://server7.mp3quran.net/basit/", "Abdulloh Al-Juhaniy": "https://server13.mp3quran.net/jhn/", "Abdulmohsin Al-Qosim": "https://server8.mp3quran.net/qasm/", "Abdulvaliy Al-Arkoniy": "https://server6.mp3quran.net/arkani/", "Odil Al-Xalboniy": "https://server8.mp3quran.net/a_klb/", "Ahmad Al-Ajmiy": "https://server10.mp3quran.net/ajm/", "Abdurahmon As-Sudays": "https://server11.mp3quran.net/sds/", "Sa'd Ash-Shuraym": "https://server7.mp3quran.net/shur/", "Aliy Al-Huzayfiy": "https://server8.mp3quran.net/hthfi/", "Faris Abbod": "https://server8.mp3quran.net/frs_a/", "Solih Bukhotir": "https://server8.mp3quran.net/bu_khtr/", "Muhammad Al-Minshoviy": "https://server10.mp3quran.net/minsh/", "Mustafo Ismoil": "https://server8.mp3quran.net/mustafa/", "Mahmud Al-Banno": "https://server8.mp3quran.net/banna/", "Nosir Al-Qatamiy": "https://server8.mp3quran.net/qat/", "Mohir Al-Muayqliy": "https://server12.mp3quran.net/maher/", "Honiy Ar-Rifoiy": "https://server8.mp3quran.net/hani/", "Yosir Ad-Dosariy": "https://server11.mp3quran.net/yasser/", "Abu Bakr Ash-Shatriy": "https://server11.mp3quran.net/shatri/"}

SURA_NAMES = ["Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus", "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha", "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum", "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir", "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof", "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana", "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij", "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa", "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad", "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot", "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr", "Masad", "Ixlos", "Falaq", "Nos"]

async def fetch_prayer_times(lat, lon):
    async with aiohttp.ClientSession() as s:
        async with s.get("https://api.aladhan.com/v1/timings", params={"latitude": lat, "longitude": lon, "method": 3}) as r:
            return (await r.json())["data"]["timings"]

def calculate_qibla(lat, lon):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, 21.4225, 39.8262])
    x = math.sin(lon2 - lon1)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def ramazon_days_left():
    delta = (datetime(2027, 2, 8, tzinfo=ZoneInfo("Asia/Tashkent")) - datetime.now(ZoneInfo("Asia/Tashkent"))).days
    return f"Ramazon oyiga {delta} kun qoldi." if delta > 0 else ("Bugun Ramazonning birinchi kuni!" if delta == 0 else "Ramazon oyi tugagan.")

# --- KLAVIATURALAR ---
def main_menu(rem=False):
    return ReplyKeyboardMarkup([[KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")], [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")], [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")], [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")], [KeyboardButton("🎮 Viktorina"), KeyboardButton("🔍 Qidiruv tizimi")], [KeyboardButton("📚 Diniy ma'rifiy"), KeyboardButton("⚙️ Sozlamalar")], [KeyboardButton("📍 Lokatsiyani yangilash", request_location=True)]], resize_keyboard=True)

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
    return InlineKeyboardMarkup([[InlineKeyboardButton(d["nomi"], callback_data=f"duo:{k}")] for k, d in DUOLAR.items()])

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

# --- VIKTORINA YORDAMCHILARI ---
def prepare_quiz_question(raw):
    options = list(raw.get("options") or [])
    correct = raw.get("answer")
    if len(options) < 4 or correct not in options: return None
    if len(options) > 4:
        others = [o for o in options if o != correct]
        options = random.sample(others, 3) + [correct]
    random.shuffle(options)
    return {"q": raw["q"], "options": options, "correct_idx": options.index(correct)}

def pick_quiz_questions(count):
    if not QUIZ_QUESTIONS: return []
    pool = QUIZ_QUESTIONS[:]
    random.shuffle(pool)
    result = []
    for raw in pool:
        q = prepare_quiz_question(raw)
        if q: result.append(q)
        if len(result) >= count: break
    return result

def build_quiz_kb(q_idx, options):
    return InlineKeyboardMarkup([[InlineKeyboardButton(o, callback_data=f"qz:{q_idx}:{i}")] for i, o in enumerate(options)])

async def send_quiz_question(client, chat_id, uid):
    state = QUIZ_STATE.get(uid)
    if not state or state["idx"] >= len(state["questions"]):
        score = state["score"] if state else 0
        total = len(state["questions"]) if state else 0
        QUIZ_STATE.pop(uid, None)
        return await client.send_message(chat_id, f"🏁 **Viktorina tugadi!**\n\n✅ To'g'ri javoblar: **{score}/{total}**", reply_markup=main_menu(False))
    q = state["questions"][state["idx"]]
    text = f"🎮 **Viktorina** ({state['idx']+1}/{len(state['questions'])})\n\n❓ {q['q']}"
    await client.send_message(chat_id, text, reply_markup=build_quiz_kb(state["idx"], q["options"]))

# --- KATTA MATNLARNI BO'LAKLARGA BO'LIB YUBORISH ---
async def send_long_text(callback_query, text, kb=None):
    if len(text) <= 4000:
        await callback_query.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    else:
        await callback_query.message.edit_text(text[:4000], disable_web_page_preview=True)
        remaining_text = text[4000:]
        while len(remaining_text) > 0:
            chunk = remaining_text[:4000]
            await callback_query.message.reply(chunk, disable_web_page_preview=True)
            remaining_text = remaining_text[4000:]
        if kb: await callback_query.message.reply("⬆️ Yuqoridagi ma'lumotlarning davomi.", reply_markup=kb)

# --- HANDLERLAR ---
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
    await message.reply("✅ Lokatsiya saqlandi!", reply_markup=main_menu(False))

@app.on_message(filters.regex(r"^🕌 Namoz vaqtlari$"))
async def get_times(client, message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user or not user[0]: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    msg = await message.reply("⏳ Hisoblanmoqda...")
    try:
        timings = await fetch_prayer_times(user[0], user[1])
        text = f"🕌 **Bugungi namoz vaqtlari**\n\n" + "\n".join([f"• {label}: **{timings[name]}**" for name, label in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]])
        await msg.edit_text(text)
    except Exception as e: await msg.edit_text(f"❌ Xatolik: {e}")

@app.on_message(filters.regex(r"^🧭 Qibla yo'nalishi$"))
async def get_qibla(client, message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user or not user[0]: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    degree = calculate_qibla(user[0], user[1])
    await message.reply(f"🧭 **Qibla yo'nalishi:** **{degree:.1f}°**")

@app.on_message(filters.regex(r"^🎧 Qorilar va qiroatlar$"))
async def show_reciters(client, message: Message): await message.reply("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(0))

@app.on_message(filters.regex(r"^🤲 Duolar$"))
async def show_duolar(client, message: Message): await message.reply("🤲 **Sahih hadislardan olingan duolar**\n\nVaziyatni tanlang:", reply_markup=duolar_menu())

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
    except: await msg.edit_text("❌ Xatolik.")

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
    text = "⭐ **Sevimlilar:**\n\n" + "".join([f"• {fav[0][:100]}...\n\n" for fav in favs])
    await message.reply(text)

@app.on_message(filters.regex(r"^🎮 Viktorina$"))
async def quiz_start(client, message: Message):
    questions = pick_quiz_questions(QUESTIONS_PER_QUIZ)
    if not questions: return await message.reply("Hozircha savollar mavjud emas.")
    QUIZ_STATE[message.from_user.id] = {"questions": questions, "idx": 0, "score": 0}
    await send_quiz_question(client, message.chat.id, message.from_user.id)

@app.on_message(filters.regex(r"^📚 Diniy ma'rifiy$"))
async def ilmiy_menu_show(client, message: Message): await message.reply("📚 **Bo'limni tanlang:**", reply_markup=ilmiy_menu())

@app.on_message(filters.regex(r"^🔍 Qidiruv tizimi$"))
async def search_start(client, message: Message):
    USER_STATES[message.from_user.id] = "search"
    await message.reply("🔍 **Qidiruv**\n\nSo'zni yozing (masalan: *sabr*, *jannat*).")

@app.on_callback_query(filters.regex(r"^reciter:"))
async def select_reciter(client, cb: CallbackQuery): await cb.message.edit_text(f"🎧 **{cb.data.split(':', 1)[1]}**", reply_markup=surahs_menu(cb.data.split(':', 1)[1], 0))

@app.on_callback_query(filters.regex(r"^reciter_page:"))
async def reciter_page(client, cb: CallbackQuery): await cb.message.edit_text("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(int(cb.data.split(":")[1])))

@app.on_callback_query(filters.regex(r"^surah_page:"))
async def surah_page(client, cb: CallbackQuery):
    _, r_name, p = cb.data.split(":")
    await cb.message.edit_text(f"🎧 **{r_name}**", reply_markup=surahs_menu(r_name, int(p)))

@app.on_callback_query(filters.regex(r"^surah:"))
async def send_audio(client, cb: CallbackQuery):
    await cb.answer("⏳ Audio yuklanmoqda...")
    _, r_name, s_num = cb.data.split(":")
    s_num = int(s_num)
    temp_file = f"temp_{s_num}.mp3"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{RECITERS[r_name]}{s_num:03d}.mp3", headers={'User-Agent': 'Mozilla/5.0'}) as resp:
                if resp.status != 200: raise Exception("Server xatosi")
                with open(temp_file, "wb") as f: f.write(await resp.read())
        await client.send_audio(cb.from_user.id, audio=temp_file, title=f"{s_num}-sura", performer=r_name)
        await cb.message.delete()
    except Exception as e: await cb.message.edit_text(f"❌ Xato: {str(e)}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

@app.on_callback_query(filters.regex(r"^duo:"))
async def send_duo(client, cb: CallbackQuery):
    duo = DUOLAR.get(cb.data.split(":")[1])
    text = f"**{duo['nomi']}**\n\n**{duo['arabcha']}**\n\n**O'qilishi:** {duo['oqilishi']}\n\n**Ma'nosi:** {duo['tarjima']}"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"{duo['nomi']} - {duo['tarjima']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:duo:{fav_id}")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="duo_back")]])
    await cb.message.edit_text(text, reply_markup=kb)

@app.on_callback_query(filters.regex(r"^duo_back$"))
async def duo_back(client, cb: CallbackQuery): await cb.message.edit_text("🤲 **Duolar**", reply_markup=duolar_menu())

@app.on_callback_query(filters.regex(r"^fav_save:"))
async def save_favorite(client, cb: CallbackQuery):
    _, ftype, fav_id = cb.data.split(":")
    fav_text = TEMP_FAV.get(fav_id)
    if fav_text:
        cursor.execute("INSERT INTO favorites (user_id, fav_type, fav_text) VALUES (?, ?, ?)", (cb.from_user.id, ftype, fav_text))
        conn.commit()
        del TEMP_FAV[fav_id]
        await cb.answer("⭐ Saqlandi!", show_alert=True)
        await cb.message.edit_reply_markup(reply_markup=None)
    else: await cb.answer("Xatolik.", show_alert=True)

@app.on_callback_query(filters.regex(r"^tasbeh_select:"))
async def tasbeh_select(client, cb: CallbackQuery):
    idx = int(cb.data.split(":")[1])
    TASBEH_COUNTS[cb.from_user.id] = 0
    await cb.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[idx]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(idx, 0))

@app.on_callback_query(filters.regex(r"^tasbeh_add:"))
async def tasbeh_add(client, cb: CallbackQuery):
    idx = int(cb.data.split(":")[1])
    TASBEH_COUNTS[cb.from_user.id] = TASBEH_COUNTS.get(cb.from_user.id, 0) + 1
    await cb.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[idx]}\n\n*Sanoq: {TASBEH_COUNTS[cb.from_user.id]}*", reply_markup=tasbeh_counter_menu(idx, TASBEH_COUNTS[cb.from_user.id]))

@app.on_callback_query(filters.regex(r"^tasbeh_reset:"))
async def tasbeh_reset(client, cb: CallbackQuery):
    idx = int(cb.data.split(":")[1])
    TASBEH_COUNTS[cb.from_user.id] = 0
    await cb.message.edit_text(f"📿 **Zikr:** {TASBEH_DHIKRS[idx]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(idx, 0))

@app.on_callback_query(filters.regex(r"^tasbeh_back$"))
async def tasbeh_back(client, cb: CallbackQuery): await cb.message.edit_text("📿 **Raqamli Tasbeh**\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_callback_query(filters.regex(r"^noop$"))
async def noop(client, cb: CallbackQuery): await cb.answer()

@app.on_callback_query(filters.regex(r"^qz:"))
async def quiz_answer(client, cb: CallbackQuery):
    _, q_idx, opt_idx = cb.data.split(":")
    q_idx, opt_idx = int(q_idx), int(opt_idx)
    state = QUIZ_STATE.get(cb.from_user.id)
    if not state or state["idx"] != q_idx: return await cb.answer("Bu savol eskirgan.", show_alert=True)
    q = state["questions"][state["idx"]]
    if opt_idx == q["correct_idx"]:
        state["score"] += 1
        await cb.answer("✅ To'g'ri!")
    else: await cb.answer(f"❌ Xato! To'g'ri javob: {q['options'][q['correct_idx']]}", show_alert=True)
    state["idx"] += 1
    try: await cb.message.delete()
    except Exception: pass
    await send_quiz_question(client, cb.message.chat.id, cb.from_user.id)

@app.on_callback_query(filters.regex(r"^ilmiy:"))
async def ilmiy_show(client, cb: CallbackQuery):
    q = cb.data.split(":")[1]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    if q == "siyrat":
        await send_long_text(cb, SIYRAT_TEXT, kb)
        return
    elif q == "ramazon": text = f"**🌙 Ramazon**\n\n{RAMAZON_TEXT}\n\n_{ramazon_days_left()}_"
    elif q == "tahorat": text = TAHORAT_TEXT
    elif q == "ismlar": text = "**🌟 Allohning 99 ismi**\n\nO'rganish uchun ismni tanlang:"; kb = names_menu(0)
    else: text = "📚 Bo'limni tanlang:"; kb = ilmiy_menu()
    await cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, cb: CallbackQuery):
    idx = int(cb.data.split(":")[1])
    name, meaning, tafsir = ALL_NAMES[idx]
    await cb.message.edit_text(f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n**Tafsiri:** {tafsir}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:ismlar")]]))

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, cb: CallbackQuery): await cb.message.edit_text("🌟 **Allohning 99 ismi**", reply_markup=names_menu(int(cb.data.split(":")[1])))

@app.on_message(filters.text & filters.private & ~filters.regex(r"^/"))
async def handle_search_input(client, message: Message):
    if USER_STATES.get(message.from_user.id) != "search": return
    text = message.text.strip()
    USER_STATES[message.from_user.id] = None
    msg = await message.reply("⏳ Qidirilmoqda...")
    try:
        url = f"https://api.alquran.cloud/v1/search/{urllib.parse.quote(text)}/all/uz.sodik"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                data = await resp.json()
                if data["code"] == 200 and data["data"]["count"] > 0:
                    res = f"🔍 **'{text}' so'zi bo'yicha natijalar:**\n\n" + "".join([f"📖 **{m['surah']['name']} {m['numberInSurah']}-oyat:**\n_{m['text']}_\n\n" for m in data["data"]["matches"][:5]])
                    await msg.edit_text(res, reply_markup=main_menu(False))
                else: await msg.edit_text(f"❌ Kechirasiz, '{text}' bo'yicha hech narsa topilmadi.", reply_markup=main_menu(False))
    except Exception: await msg.edit_text("❌ Qidiruvda xatolik yuz berdi.", reply_markup=main_menu(False))

@app.on_message(filters.regex(r"^(🔔 Eslatmani yoqish|🔕 Eslatmani o'chirish)$"))
async def toggle_reminders(client, message: Message):
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, message.from_user.id))
    conn.commit()
    await message.reply("✅ Namoz eslatmalari yoqildi." if new_status == 1 else "🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu(new_status == 1))

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

import asyncio
import aiohttp
import sqlite3
import math
import random
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, CallbackQuery, InlineKeyboardButton, 
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    BufferedInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN = "9244020327:AAE4ae-hddNmTu52OU8bkq-aTObXHIROsss"
ADMIN_ID = 8718072369

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0, 
                   active_reciter TEXT DEFAULT '', lang TEXT DEFAULT 'uz', prayer_offset INTEGER DEFAULT 0)''')
try:
    cursor.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'")
    cursor.execute("ALTER TABLE users ADD COLUMN prayer_offset INTEGER DEFAULT 0")
except: pass
cursor.execute('''CREATE TABLE IF NOT EXISTS favorites
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)''')
conn.commit()

# --- 30 TA SAHIH HADIS ---
HADITHS = [
    "Amallar niyatga ko'ra bo'ladi. Har kimga niyat qilgan narsasi bo'ladi. (Buxoriy)",
    "Sizlardan birortangiz o'ziga yaxshi ko'rgan narsasini birodariga ham yaxshi ko'rmaguncha iymon keltirgan hisoblanmaydi. (Buxoriy, Muslim)",
    "Musulmon — o'z tili va qo'li bilan boshqa musulmonlarga zarar yetkazmaydigan kishidir. (Buxoriy)",
    "Kim Allohga va oxirat kuniga iymon keltirsa, yaxshi so'z aytsin yoki jim tursin. (Buxoriy)",
    "Osonlashtiring, qiyinlashtirmang. Xushxabar bering, nafratlantirmang. (Buxoriy)",
    "Insonning Islomni yaxshi tutishi, o'ziga aloqasi yo'q narsalarni tark etishidir. (Termiziy)",
    "Sadaqa qilish bilan mol kamaymaydi. (Muslim)",
    "Alloh sizlarning suratlaringizga va mollarigizga qaramaydi, balki qalblaringizga va amallaringizga qaraydi. (Muslim)",
    "Ota-onasining roziligini topgan kishi jannatga kiradi. (Termiziy)",
    "Kim Allohdan qo'rqsa, Alloh uni har narsadan asraydi va rizqini o'zi bermagan joydan beradi. (Termiziy)",
    "Yaxshilik — bu go'zal xulqdir. (Muslim)",
    "Kulgi ko'p bo'lsa, qalb o'ladi. (Termiziy)",
    "Ilm izlash har bir musulmon uchun farzdir. (Ibn Moja)",
    "Kim bir kishining gunohini yashirsa, Alloh uning oxiratdagi gunohlarini yashiradi. (Muslim)",
    "Sizlarning eng yaxshilaringiz qur'onni o'rganib, boshqalarga o'rgatganlaringizdir. (Buxoriy)",
    "Toza bo'lish iymonning yarmidir. (Muslim)",
    "Alloh jamolga ega va jamolni yaxshi ko'radi. (Muslim)",
    "Birodaringga tabassum qilishing ham sadaqadir. (Termiziy)",
    "Tilingizni tiyib turing, aks holda u sizni halokatga olib boradi. (Termiziy)",
    "Kim Allohdan boshqa iloh yo'qligini bilib o'lsa, jannatga kiradi. (Muslim)",
    "Musofirga yordam berish sadaqadir. (Buxoriy)",
    "G'iybat qiluvchi jannatga kirmaydi. (Buxoriy, Muslim)",
    "O'z qo'li bilan topgan halol rizq eng yaxshi rizqdir. (Buxoriy)",
    "Birodaringizga qilgan har qanday yaxshiligingiz sadaqadir. (Muslim)",
    "Kim yolg'on guvohlik bersa, u mo'min emas. (Abu Dovud)",
    "Namoz — bu mo'minning me'rojidir. (Hadis)",
    "Jannat onalar oyog'i ostidadir. (Hadis)",
    "Sizlardan hech biringiz o'zini o'ldirmasin. Zero, mo'min hech qachon o'zini xor qilmaydi. (Abu Dovud)",
    "Bir kishi o'z ukasi uchun qilgan yaxshiligi unga o'zi uchun qilganidan yaxshiroqdir. (Muslim)",
    "Yaxshilik qilishdan charchamang, chunki u sizni yomonlikdan saqlaydi. (Hadis)"
]

# --- TASBEH ---
TASBEH_COUNTS = {}
TASBEH_DHIKRS = ["Subhanalloh", "Alhamdulilloh", "Allohu Akbar", "La ilaha illalloh", "Astag'firulloh", "La havla va la quvvata illa billah", "Subhanallohi va bihamdihi", "Subhanallohil 'Aziym", "La ilaha illallohu vahdahu la sharika lah", "Allohumma solli 'ala Muhammad", "Bismillah", "Hasbunallohu va ni'mal vakil", "La ilaha illa anta subhanaka inni kuntu minaz zolimin", "Ya Hayyu ya Qayyum birahmatika astag'is", "Rabbana atina fid dunya hasanatan va fil akhirati hasanatan va qina 'azaban nar", "Allohumma inni as'alukal jannata va a'uzu bika minan nar", "Robbi zidni 'ilma", "Robbi ighfir li va li validayya", "Allohumma ighfir li zanbi kullahu", "Subhanallohi va bihamdihi subhanallohil 'Aziym"]

# --- QORILAR (Sluglar to'g'rilandi) ---
RECITERS = {
    "Mishary Alafasy": "ar.alafasy",
    "Abdul Basit": "ar.abdulbasitmurattal",
    "Saad Al-Ghamdi": "ar.saadalghamdi",
    "Maher Al-Muaiqly": "ar.mahermuaiqly",
    "Abu Bakr Al-Shatri": "ar.abubakralshatri",
    "Yasser Al-Dosari": "ar.yasseraldosari",
    "Nasser Al-Qatami": "ar.nasserqatami",
    "Hani Ar-Rifai": "ar.hanirifai",
    "Muhammad Al-Luhaidan": "ar.muhammadalluhaidan",
    "Mahmoud Al-Hussary": "ar.mahmoudkhalilalhusary",
    "Abdul Rahman Al-Sudais": "ar.abdurrahmaansudais",
    "Saud Al-Shuraim": "ar.saoodshuraym",
    "Ali Al-Hudhaify": "ar.alihudhaify",
    "Ahmad Al-Ajmi": "ar.ahmadalajmi",
    "Fares Abbad": "ar.faresabbad",
    "Salah Bukhatir": "ar.salahbukhatir",
    "Muhammad Al-Minshawi": "ar.muhammadsiddiqalminshawi",
    "Mustafa Ismail": "ar.mustafaalismail",
    "Mahmoud Al-Banna": "ar.mahmoudalibanna",
    "Abdullah Al-Juhany": "ar.abdullahaljuhany"
}

SURA_NAMES = ["Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus", "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha", "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum", "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir", "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof", "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana", "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij", "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa", "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad", "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot", "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr", "Masad", "Ixlos", "Falaq", "Nos"]

# --- DUOLAR ---
DUOLAR = {"uydan_chiqish": {"nomi": "🚪 Uydan chiqish duosi", "arabcha": "بِسْمِ اللَّهِ، تَوَكَّلْتُ عَلَى اللَّهِ، وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ", "oqilishi": "Bismillahi, tavakkaltu 'alallohi, va la havla va la quvvata illa billah.", "tarjima": "Allohning nomi bilan (chiqaman). Allohga tavakkal qildim. Kuch-quvvat faqat Allohdan.", "manba": "Abu Dovud, Termiziy (sahih)"}, "uyga_kirish": {"nomi": "🏠 Uyga kirish duosi", "arabcha": "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ الْمَوْلَجِ وَخَيْرَ الْمَخْرَجِ", "oqilishi": "Allohumma inni as'aluka xayral mavlaji va xayral maxraji.", "tarjima": "Allohim, men Sendan eng yaxshi kirish va eng yaxshi chiqishni so'rayman.", "manba": "Abu Dovud (sahih)"}, "ovqatdan_oldin": {"nomi": "🍽 Ovqatdan oldin", "arabcha": "بِسْمِ اللَّهِ", "oqilishi": "Bismillah.", "tarjima": "Allohning nomi bilan.", "manba": "Buxoriy, Muslim"}, "ovqatdan_keyin": {"nomi": "🍽 Ovqatdan keyin", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مِنَ الْمُسْلِمِينَ", "oqilishi": "Alhamdulillahillazi at'amana va saqona va ja'alana minal muslimin.", "tarjima": "Bizni taomlantirgan, suv ichirgan va muslimlardan qilgan Allohga hamd bo'lsin.", "manba": "Termiziy, Abu Dovud (sahih)"}, "uyqudan_oldin": {"nomi": "🌙 Uyqudan oldin", "arabcha": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "oqilishi": "Bismikallohumma amutu va ahya.", "tarjima": "Allohim, Sening isming bilan o'laman va tirilaman.", "manba": "Buxoriy"}, "uyqudan_uygonish": {"nomi": "☀️ Uyqudan uyg'onish", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ", "oqilishi": "Alhamdulillahillazi ahyana ba'da ma amatana va ilayhin nushur.", "tarjima": "Bizni o'ldirgandan keyin tiriltirgan Allohga hamd bo'lsin, qaytish Uning O'zigadir.", "manba": "Buxoriy"}, "safar": {"nomi": "✈️ Safar duosi", "arabcha": "سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ", "oqilishi": "Subhanallazi saxkhara lana haza va ma kunna lahu muqrinin, va inna ila Robbina lamunqalibun.", "tarjima": "Buni bizga bo'ysundirgan Zot pokdir. Biz bunga qodir emas edik. Albatta, biz Rabbimizga qaytuvchimiz.", "manba": "Muslim"}, "masjidga_kirish": {"nomi": "🕌 Masjidga kirish", "arabcha": "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ", "oqilishi": "Allohummaftah li abvaba rohmatik.", "tarjima": "Allohim, menga rahmat eshiklarini och.", "manba": "Muslim"}, "masjiddan_chiqish": {"nomi": "🕌 Masjiddan chiqish", "arabcha": "اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ", "oqilishi": "Allohumma inni as'aluka min fadlik.", "tarjima": "Allohim, men Sendan fazlingdan so'rayman.", "manba": "Muslim"}, "istigfor": {"nomi": "🤲 Sayyidul Istig'for", "arabcha": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ", "oqilishi": "Allohumma anta Robbi la ilaha illa anta, xalaqtani va ana 'abduka, va ana 'ala 'ahdika va va'dika mastata'tu, a'uzu bika min sharri ma sana'tu, abu'u laka bini'matika 'alayya, va abu'u bi zanbi, fag'fir li fa innahu la yag'firuz zunuba illa anta.", "tarjima": "Allohim, Sen mening Rabbimsan, Sendan boshqa iloh yo'q. Meni yaratding, men Sening bandangman. Qo'limdan kelgancha ahdu vafoga turmoqdaman. Qilgan ishlarimning yomonligidan Sendan panoh tilayman. Menga bergan ne'matlaringni tan olaman va gunohimni iqror bo'laman. Meni mag'firat qil, chunki Sendan boshqa gunohlarni mag'firat qiluvchi yo'q.", "manba": "Buxoriy"}}

# --- 99 ISM ---
ALL_NAMES = [("Ar-Rahman", "Rahmli"), ("Ar-Rahim", "Mehribon"), ("Al-Malik", "Podsho"), ("Al-Quddus", "Muqaddas"), ("As-Salam", "Tinchlik"), ("Al-Mu'min", "Ishonch beruvchi"), ("Al-Muhaymin", "Nazorat qiluvchi"), ("Al-Aziz", "Qudratli"), ("Al-Jabbar", "Kuchli"), ("Al-Mutakabbir", "Ulug'"), ("Al-Khaliq", "Yaratuvchi"), ("Al-Bari'", "Ijodkor"), ("Al-Musawwir", "Shakl beruvchi"), ("Al-Ghaffar", "Kechiruvchi"), ("Al-Qahhar", "G'olib"), ("Al-Wahhab", "Sovg'a beruvchi"), ("Ar-Razzaq", "Rizq beruvchi"), ("Al-Fattah", "Ochuvchi"), ("Al-Alim", "Biluvchi"), ("Al-Qabid", "Ushlab turuvchi")]

# --- VIKTORINA ---
QUIZ_QUESTIONS = [
    {"q": "Qur'onda nechta sura bor?", "options": ["110", "114", "120", "99"], "answer": "114"},
    {"q": "Eng birinchi nozil bo'lgan sura qaysi?", "options": ["Fotiha", "Baqara", "Alaq", "Nos"], "answer": "Alaq"},
    {"q": "Musulmonlar uchun qibla qaysi shahar?", "options": ["Madina", "Makka", "Quddus", "Toif"], "answer": "Makka"},
    {"q": "Kuniga nechta vaqt farz namoz o'qiladi?", "options": ["3", "5", "7", "10"], "answer": "5"},
    {"q": "Qur'onning eng uzun surasi qaysi?", "options": ["Oli Imron", "Niso", "Baqara", "Moida"], "answer": "Baqara"},
    {"q": "Payg'ambarimiz (s.a.v) qaysi shaharda tug'ilganlar?", "options": ["Madina", "Makka", "Toif", "Quddus"], "answer": "Makka"},
    {"q": "Ramazon oyida ro'za tutish hukmi nima?", "options": ["Sunna", "Farz", "Mustahab", "Makruh"], "answer": "Farz"},
    {"q": "Zakot miqdori qancha?", "options": ["1/10", "1/20", "1/40", "1/50"], "answer": "1/40"},
    {"q": "Qur'onda jami nechta juz bor?", "options": ["20", "30", "40", "60"], "answer": "30"},
    {"q": "Eng birinchi xalifa kim bo'lgan?", "options": ["Umar (r.a)", "Usmon (r.a)", "Ali (r.a)", "Abu Bakr (r.a)"], "answer": "Abu Bakr (r.a)"},
    {"q": "Namozda qaysi sura o'qilmasa, namoz bo'lmaydi?", "options": ["Ixlos", "Fotiha", "Nos", "Kavsar"], "answer": "Fotiha"},
    {"q": "Payg'ambarimiz (s.a.v) necha yoshida payg'ambarlikka erishdilar?", "options": ["30", "35", "40", "45"], "answer": "40"},
    {"q": "Qur'on qaysi oyda nozil bo'la boshlagan?", "options": ["Rajab", "Ramazon", "Shavvol", "Muharram"], "answer": "Ramazon"},
    {"q": "Qaysi amal Islomning eng muhim rukni hisoblanadi?", "options": ["Ro'za", "Zakot", "Kalimai shahodat", "Haj"], "answer": "Kalimai shahodat"},
    {"q": "Qur'onda nechta oyat bor (taxminan)?", "options": ["5000", "6000", "6236", "7000"], "answer": "6236"}
]

# --- KLAVIATURALAR ---
def main_menu(lang='uz', reminders_status=False):
    belgi = "🔕 Eslatmani o'chirish" if reminders_status else "🔔 Eslatmani yoqish"
    if lang == 'ru':
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🕌 Время намаза"), KeyboardButton(text="🧭 Кибла")],
            [KeyboardButton(text="🎧 Кораны"), KeyboardButton(text="🤲 Дуа")],
            [KeyboardButton(text="📿 Тасбих"), KeyboardButton(text="📖 Аят дня")],
            [KeyboardButton(text="📜 Хадис дня"), KeyboardButton(text="⭐ Избранное")],
            [KeyboardButton(text="🎮 Викторина"), KeyboardButton(text="🔍 Поиск")],
            [KeyboardButton(text="📚 Исламские знания"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="📍 Обновить локацию", request_location=True)]
        ], resize_keyboard=True)
    else:
        return ReplyKeyboardMarkup(keyboard=[
            [KeyboardButton(text="🕌 Namoz vaqtlari"), KeyboardButton(text="🧭 Qibla yo'nalishi")],
            [KeyboardButton(text="🎧 Qorilar va qiroatlar"), KeyboardButton(text="🤲 Duolar")],
            [KeyboardButton(text="📿 Raqamli Tasbeh"), KeyboardButton(text="📖 Kunlik oyat")],
            [KeyboardButton(text="📜 Kunlik hadis"), KeyboardButton(text="⭐ Sevimlilar")],
            [KeyboardButton(text="🎮 Viktorina"), KeyboardButton(text="🔍 Qidiruv tizimi")],
            [KeyboardButton(text="📚 Diniy ma'rifiy"), KeyboardButton(text="⚙️ Sozlamalar")],
            [KeyboardButton(text="📍 Lokatsiyani yangilash", request_location=True)]
        ], resize_keyboard=True)

def lang_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 O'zbekcha", callback_data="set_lang:uz")
    kb.button(text="🇷🇺 Русский", callback_data="set_lang:ru")
    return kb.as_markup()

def update_location_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📍 Lokatsiyani yuborish", request_location=True)]], resize_keyboard=True, one_time_keyboard=True)

def reciters_menu(page=0):
    kb = InlineKeyboardBuilder()
    items = list(RECITERS.items())
    start, end = page * 10, (page * 10) + 10
    for name, url in items[start:end]:
        kb.button(text=name, callback_data=f"reciter:{name}")
    kb.adjust(2)
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"reciter_page:{page-1}"))
    if end < len(items): nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"reciter_page:{page+1}"))
    if nav: kb.row(*nav)
    return kb.as_markup()

def surahs_menu(reciter_name, page=0):
    kb = InlineKeyboardBuilder()
    start, end = page * 10, (page * 10) + 10
    for i in range(start, min(end, 114)):
        kb.button(text=f"{i+1}. {SURA_NAMES[i]}", callback_data=f"surah:{reciter_name}:{i+1}")
    kb.adjust(2)
    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"surah_page:{reciter_name}:{page-1}"))
    if end < 114: nav.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"surah_page:{reciter_name}:{page+1}"))
    if nav: kb.row(*nav)
    return kb.as_markup()

def duolar_menu():
    kb = InlineKeyboardBuilder()
    for key, duo in DUOLAR.items():
        kb.button(text=duo["nomi"], callback_data=f"duo:{key}")
    kb.adjust(2)
    return kb.as_markup()

def tasbeh_dhikrs_menu():
    kb = InlineKeyboardBuilder()
    for i, dhikr in enumerate(TASBEH_DHIKRS):
        kb.button(text=f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}")
    kb.adjust(2)
    return kb.as_markup()

def tasbeh_counter_menu(index, count):
    kb = InlineKeyboardBuilder()
    kb.button(text=f"🔢 Sanoq: {count}", callback_data="tasbeh_noop")
    kb.button(text="➕ Sanoqni oshirish", callback_data=f"tasbeh_add:{index}")
    kb.button(text="🔄 Tozalash", callback_data=f"tasbeh_reset:{index}")
    kb.button(text="⬅️ Zikrlar ro'yxati", callback_data="tasbeh_back")
    kb.adjust(1)
    return kb.as_markup()

def ilmiy_menu():
    kb = InlineKeyboardBuilder()
    kb.button(text="🕋 Payg'ambar siyrati", callback_data="ilmiy:siyrat")
    kb.button(text="🌙 Ramazon rejimi", callback_data="ilmiy:ramazon")
    kb.button(text="💧 Tahorat va Namoz", callback_data="ilmiy:tahorat")
    kb.button(text="🌟 Allohning 99 ismi", callback_data="ilmiy:ismlar")
    kb.adjust(2)
    return kb.as_markup()

def settings_menu(offset):
    kb = InlineKeyboardBuilder()
    kb.button(text="🇺🇿 Tilni o'zgartirish", callback_data="change_lang")
    kb.button(text=f"⏱ Namoz vaqti (Offset: {offset} daq)", callback_data="offset_noop")
    kb.button(text="-10 daq", callback_data="offset:-10")
    kb.button(text="-5 daq", callback_data="offset:-5")
    kb.button(text="0 daq", callback_data="offset:0")
    kb.button(text="+5 daq", callback_data="offset:5")
    kb.button(text="+10 daq", callback_data="offset:10")
    kb.adjust(1, 1, 2, 3)
    return kb.as_markup()

# --- YORDAMCHI FUNKSIYALAR ---
async def fetch_prayer_times(lat: float, lon: float, offset: int = 0) -> dict:
    today = datetime.now().strftime("%d-%m-%Y")
    url = "https://api.aladhan.com/v1/timings"
    params = {"latitude": lat, "longitude": lon, "method": 3, "date": today}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            timings = data["data"]["timings"]
            if offset != 0:
                for k, v in timings.items():
                    if ":" in v and len(v) == 5:
                        t = datetime.strptime(v, "%H:%M")
                        t = t + timedelta(minutes=offset)
                        timings[k] = t.strftime("%H:%M")
            return timings

def calculate_qibla(lat: float, lon: float) -> float:
    kaaba_lat, kaaba_lon = 21.4225, 39.8262
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, kaaba_lat, kaaba_lon])
    diff_lon = lon2 - lon1
    x = math.sin(diff_lon)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(diff_lon)
    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360

# --- ADMIN ---
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    cursor.execute("SELECT count(*) FROM users")
    count = cursor.fetchone()[0]
    await message.answer(f"👑 <b>Admin panel</b>\nFoydalanuvchilar: {count}\n\nXabar yuborish: <code>/send matn</code>", parse_mode="HTML")

@dp.message(Command("send"))
async def broadcast(message: Message):
    if message.from_user.id != ADMIN_ID: return
    text_to_send = message.text.replace("/send ", "")
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    count = 0
    for user in users:
        try:
            await bot.send_message(user[0], text_to_send)
            count += 1
            await asyncio.sleep(0.05)
        except: pass
    await message.answer(f"✅ Xabar {count} kishiga yuborildi.")

# --- INLINE REJIM ---
@dp.inline_query()
async def inline_search(query: InlineQuery):
    text = query.query.strip()
    if not text: return
    results = []
    try:
        encoded_text = urllib.parse.quote(text)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.alquran.cloud/v1/search/{encoded_text}/all/uz.sodik") as resp:
                data = await resp.json()
                if data["code"] == 200 and data["data"]["count"] > 0:
                    for match in data["data"]["matches"][:10]:
                        ayah_text = f"📖 {match['surah']['name']} surasi, {match['numberInSurah']}-oyat:\n\n{match['text']}"
                        results.append(InlineQueryResultArticle(
                            id=str(match['number']), title=f"{match['surah']['name']} {match['numberInSurah']}-oyat",
                            input_message_content=InputTextMessageContent(message_text=ayah_text)
                        ))
    except: pass
    
    if not results:
        results.append(InlineQueryResultArticle(id="0", title="Natija topilmadi", input_message_content=InputTextMessageContent(message_text="Hech narsa topilmadi.")))
        
    await query.answer(results, cache_time=1, is_personal=True)

# --- ASOSIY HANDLERLAR ---
@dp.message(Command("start"))
async def cmd_start(message: Message):
    cursor.execute("SELECT lat, lon, reminders, lang FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if user:
        await message.answer("Assalomu alaykum! 🕌\nKerakli bo'limni tanlang:", reply_markup=main_menu(user[3], bool(user[2])))
    else:
        await message.answer("Assalomu alaykum! 🕌\nTizimga xush kelibsiz. Iltimos, tilni tanlang:", reply_markup=lang_menu())

@dp.callback_query(F.data.startswith("set_lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    cursor.execute("INSERT OR IGNORE INTO users (user_id, lang) VALUES (?, ?)", (call.from_user.id, lang))
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, call.from_user.id))
    conn.commit()
    msg = "Выберите действие:" if lang == "ru" else "Kerakli bo'limni tanlang:"
    await call.message.edit_text("✅ Til saqlandi!" if lang == "uz" else "✅ Язык сохранен!")
    await call.message.answer(msg, reply_markup=main_menu(lang, False))
    await call.answer()

@dp.message(F.text.in_(["⚙️ Sozlamalar", "⚙️ Настройки"]))
async def settings(message: Message):
    cursor.execute("SELECT prayer_offset FROM users WHERE user_id = ?", (message.from_user.id,))
    offset = cursor.fetchone()[0]
    await message.answer("⚙️ <b>Sozlamalar</b>\nNamoz vaqtiga tuzatish kiritishingiz yoki tilni o'zgartirishingiz mumkin:", parse_mode="HTML", reply_markup=settings_menu(offset))

@dp.callback_query(F.data == "change_lang")
async def change_lang(call: CallbackQuery):
    await call.message.edit_text("Tilni tanlang / Выберите язык:", reply_markup=lang_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("offset:"))
async def set_offset(call: CallbackQuery):
    offset = int(call.data.split(":")[1])
    cursor.execute("UPDATE users SET prayer_offset = ? WHERE user_id = ?", (offset, call.from_user.id))
    conn.commit()
    await call.message.edit_reply_markup(reply_markup=settings_menu(offset))
    await call.answer("Vaqt tuzatildi!")

@dp.message(F.location)
async def handle_location(message: Message):
    lat, lon = message.location.latitude, message.location.longitude
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    cursor.execute("UPDATE users SET lat = ?, lon = ? WHERE user_id = ?", (lat, lon, message.from_user.id))
    conn.commit()
    await message.answer("✅ Lokatsiya saqlandi! Endi pastdagi menyudan foydalanishingiz mumkin.", reply_markup=main_menu('uz', False))

# --- QIDIRUV TIZIMI ---
@dp.message(F.text.in_(["🔍 Qidiruv tizimi", "🔍 Поиск"]))
async def search_start(message: Message):
    await message.answer("🔍 <b>Qidiruv</b>\n\nQur'ondan qidirmoqchi bo'lgan so'zingizni yuborish uchun quyidagi formatdan foydalaning:\n\n<code>/qidiruv sabr</code>\n\n(Masalan: <i>sabr</i> yoki <i>jannat</i>)", parse_mode="HTML")

@dp.message(Command("qidiruv"))
async def process_search(message: Message):
    text = message.text.replace("/qidiruv", "").strip()
    if not text:
        return await message.answer("Iltimos, qidirayotgan so'zingizni yozing. Masalan: <code>/qidiruv sabr</code>", parse_mode="HTML")
    
    await message.answer("⏳ Qidirilmoqda...")
    try:
        encoded_text = urllib.parse.quote(text)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.alquran.cloud/v1/search/{encoded_text}/all/uz.sodik") as resp:
                data = await resp.json()
                if data["code"] == 200 and data["data"]["count"] > 0:
                    res = "🔍 <b>Natijalar:</b>\n\n"
                    for match in data["data"]["matches"][:5]:
                        res += f"📖 <b>{match['surah']['name']} {match['numberInSurah']}-oyat:</b>\n<blockquote>{match['text']}</blockquote>\n\n"
                    await message.answer(res, parse_mode="HTML")
                else:
                    await message.answer("❌ Hech narsa topilmadi.")
    except:
        await message.answer("❌ Xatolik yuz berdi. (Internet yoki VPN bilan muammo bo'lishi mumkin)")

# --- VIKTORINA ---
def get_quiz_keyboard(q):
    kb = InlineKeyboardBuilder()
    for opt in q["options"]:
        kb.button(text=opt, callback_data=f"quiz:{opt}:{q['answer']}")
    kb.adjust(2)
    return kb.as_markup()

@dp.message(F.text.in_(["🎮 Viktorina", "🎮 Викторина"]))
async def quiz_start(message: Message):
    q = random.choice(QUIZ_QUESTIONS)
    await message.answer(f"🎮 <b>Diniy Viktorina</b>\n\nSavol: {q['q']}", parse_mode="HTML", reply_markup=get_quiz_keyboard(q))

@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_answer(call: CallbackQuery):
    _, chosen, correct = call.data.split(":")
    if chosen == correct:
        await call.answer("✅ To'g'ri javob!", show_alert=True)
        await call.message.edit_text(call.message.text + f"\n\n✅ <b>To'g'ri javob: {correct}</b>", parse_mode="HTML")
    else:
        await call.answer(f"❌ Xato! To'g'ri javob: {correct}", show_alert=True)
        await call.message.edit_text(call.message.text + f"\n\n❌ <b>Sizning javobingiz: {chosen}</b>\n✅ <b>To'g'ri javob: {correct}</b>", parse_mode="HTML")
    
    kb = InlineKeyboardBuilder()
    kb.button(text="➡️ Keyingi savol", callback_data="quiz_next")
    await call.message.edit_reply_markup(reply_markup=kb.as_markup())

@dp.callback_query(F.data == "quiz_next")
async def quiz_next(call: CallbackQuery):
    q = random.choice(QUIZ_QUESTIONS)
    await call.message.edit_text(f"🎮 <b>Diniy Viktorina</b>\n\nSavol: {q['q']}", parse_mode="HTML", reply_markup=get_quiz_keyboard(q))
    await call.answer()

# --- SEVIMLILAR ---
@dp.message(F.text.in_(["⭐ Sevimlilar", "⭐ Избранное"]))
async def show_favorites(message: Message):
    cursor.execute("SELECT fav_type, fav_text FROM favorites WHERE user_id = ?", (message.from_user.id,))
    favs = cursor.fetchall()
    if not favs:
        return await message.answer('Sizda hali sevimli ma\'lumotlar yo\'q. O\'qiyotganingizda "⭐" belgisini bosing.')
    
    text = "⭐ <b>Sizning sevimlilaringiz:</b>\n\n"
    for fav in favs:
        text += f"• {fav[1]}\n\n"
    await message.answer(text, parse_mode="HTML")

@dp.callback_query(F.data.startswith("fav_save:"))
async def save_fav(call: CallbackQuery):
    _, ftype, ftext = call.data.split(":", 2)
    cursor.execute("INSERT INTO favorites (user_id, fav_type, fav_text) VALUES (?, ?, ?)", (call.from_user.id, ftype, ftext))
    conn.commit()
    await call.answer("⭐ Sevimlilarga saqlandi!", show_alert=True)

# --- DINIY MA'RIFIY ---
@dp.message(F.text.in_(["📚 Diniy ma'rifiy", "📚 Исламские знания"]))
async def ilmiy_menu_show(message: Message):
    await message.answer("📚 <b>Diniy va ma'rifiy qo'shimchalar</b>\n\nBo'limni tanlang:", parse_mode="HTML", reply_markup=ilmiy_menu())

@dp.callback_query(F.data.startswith("ilmiy:"))
async def ilmiy_show(call: CallbackQuery):
    q = call.data.split(":")[1]
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ Orqaga", callback_data="ilmiy:back")
    
    if q == "siyrat":
        text = "<b>🕋 Payg'ambarimiz (s.a.v) siyrati</b>\n\n<b>1. Tug'ilishi:</b> Muhammad (s.a.v) 570-yilda Makkada tavallud topdilar. Otalari Abdulloh ular tug'ilmasdan vafot etgan.\n\n<b>2. Bolaligi:</b> Onalari Omina 6 yoshida vafot etib, bobolari Abdulmuttolib, so'ngra amakilari Abu Tolib tarbiyasida qoldilar.\n\n<b>3. Payg'ambarlik:</b> 40 yoshida Hiro g'orida birinchi vahiy (Alaq surasi) nozil bo'ldi.\n\n<b>4. Hijrat:</b> Makkaliklar zulmi sabab 622-yilda Madinaga hijrat qildilar.\n\n<b>5. Vafoti:</b> 632-yilda Madinada vafot etdilar."
    elif q == "ramazon":
        text = "<b>🌙 Ramazon rejimi</b>\n\nRamazon — Qur'on nozil bo'lgan oy. Bu oyda barcha balog'atga yetgan, sog'lom musulmonlar ro'za tutishlari farz.\n\n<b>Ro'za shartlari:</b>\n- Saharlik vaqti (Bomdodgacha) yeb-ichib, niyat qilish.\n- Tongdan to Shom namozigacha yeb-ichish, jinsiy aloqadan tiyilish.\n- Fitr sadaqasini (Fitr bayramiga qadar) berish.\n\n<i>Botingizdagi Namoz vaqtlari bo'limi orqali aniq Saharlik va Iftorlik vaqtlarini bilib oling.</i>"
    elif q == "tahorat":
        text = "<b>💧 Tahorat va Namoz o'qish</b>\n\n<b>Tahorat olish tartibi:</b>\n1. Niyat qilib, qo'llarni yuvish.\n2. Og'izni 3 marta chayish.\n3. Burunni 3 marta yuvish.\n4. Yuzni 3 marta yuvish.\n5. Qo'llarni tirsakkacha 3 marta yuvish.\n6. Boshga mas'h tortish.\n7. Quloqlarni artish.\n8. Oyoqlarni to'piqqacha 3 marta yuvish.\n\n<b>Namoz o'qish:</b>\n1. Takbir (Allohu Akbar) aytish.\n2. Fotiha va sura o'qish.\n3. Ruku (belni egish).\n4. Sajda (erga ta'zim).\n5. Qiyom (tik turish)."
    elif q == "ismlar":
        text = "<b>🌟 Allohning 99 ismi (Asmaul Husna)</b>\n\n"
        for name, meaning in ALL_NAMES:
            text += f"• <b>{name}</b> — {meaning}\n"
        text += "\n<i>(Botda 20 ta asosiy ism keltirilgan)</i>"
    else:
        text = "📚 <b>Diniy va ma'rifiy qo'shimchalar</b>\n\nBo'limni tanlang:"
        kb = ilmiy_menu()
        return await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await call.answer()

# --- OYAT VA HADIS ---
@dp.message(F.text.in_(["📖 Kunlik oyat", "📖 Аят дня"]))
async def get_ayah(message: Message):
    await message.answer("⏳ Oyat qidirilmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alquran.cloud/v1/ayah/random/uz.sodik") as resp:
                data = await resp.json()
                ayah = data["data"]
                text = f"📖 <b>Kunlik oyat</b>\n\n<blockquote>{ayah['text']}</blockquote>\n\n<i>{ayah['surah']['name']} surasi, {ayah['numberInSurah']}-oyat</i>"
                kb = InlineKeyboardBuilder()
                kb.button(text="⭐ Sevimlilarga saqlash", callback_data=f"fav_save:oyat:{ayah['surah']['name']} {ayah['numberInSurah']}")
                await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    except: await message.answer("❌ Xatolik.")

@dp.message(F.text.in_(["📜 Kunlik hadis", "📜 Хадис дня"]))
async def get_hadith(message: Message):
    hadith = random.choice(HADITHS)
    text = f"📜 <b>Hadis</b>\n\n<blockquote>{hadith}</blockquote>"
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Sevimlilarga saqlash", callback_data=f"fav_save:hadis:{hadith[:50]}...")
    await message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())

# --- QOLGAN FUNKSIYALAR ---
@dp.message(F.text.in_(["🕌 Namoz vaqtlari", "🕌 Время намаза"]))
async def get_times_button(message: Message):
    cursor.execute("SELECT lat, lon, prayer_offset FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user or not user[0]: return await message.answer("Iltimos, avval lokatsiya yuboring.", reply_markup=update_location_menu())
    await message.answer("⏳ Hisoblanmoqda...")
    try:
        timings = await fetch_prayer_times(user[0], user[1], user[2])
        text = f"🕌 <b>Bugungi namoz vaqtlari</b> (Tuzatish: {user[2]} daq)\n\n"
        for name, label in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]:
            text += f"• {label}: <b>{timings[name]}</b>\n"
        await message.answer(text, parse_mode="HTML")
    except Exception as e: await message.answer(f"❌ Xatolik: {e}")

@dp.message(F.text.in_(["🧭 Qibla yo'nalishi", "🧭 Кибла"]))
async def get_qibla(message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.answer("Iltimos, avval lokatsiya yuboring.", reply_markup=update_location_menu())
    degree = calculate_qibla(user[0], user[1])
    await message.answer(f"🧭 <b>Qibla yo'nalishi</b>\n\nKa'baga qarab yo'nalish: <b>{degree:.1f}°</b> daraja.", parse_mode="HTML")

@dp.message(F.text.in_(["🤲 Duolar", "🤲 Дуа"]))
async def show_duolar(message: Message):
    await message.answer("🤲 <b>Sahih hadislardan olingan duolar</b>\n\nVaziyatni tanlang:", parse_mode="HTML", reply_markup=duolar_menu())

@dp.callback_query(F.data.startswith("duo:"))
async def send_duo(call: CallbackQuery):
    key = call.data.split(":")[1]
    duo = DUOLAR.get(key)
    if not duo: return await call.answer("Duo topilmadi.", show_alert=True)
    text = f"<b>{duo['nomi']}</b>\n\n<blockquote>{duo['arabcha']}</blockquote>\n\n<b>O'qilishi:</b> <i>{duo['oqilishi']}</i>\n\n<b>Ma'nosi:</b> {duo['tarjima']}\n\n<i>Manba: {duo['manba']}</i>"
    kb = InlineKeyboardBuilder()
    kb.button(text="⭐ Sevimlilarga saqlash", callback_data=f"fav_save:duo:{duo['nomi']}")
    kb.button(text="⬅️ Duolar ro'yxati", callback_data="duo_back")
    kb.adjust(1)
    await call.message.answer(text, parse_mode="HTML", reply_markup=kb.as_markup())
    await call.answer()

@dp.callback_query(F.data == "duo_back")
async def duo_back(call: CallbackQuery):
    await call.message.edit_text("🤲 <b>Sahih hadislardan olingan duolar</b>\n\nVaziyatni tanlang:", parse_mode="HTML", reply_markup=duolar_menu())
    await call.answer()

@dp.message(F.text.in_(["📿 Raqamli Tasbeh", "📿 Тасбих"]))
async def tasbeh_start(message: Message):
    TASBEH_COUNTS[message.from_user.id] = 0
    await message.answer("📿 <b>Raqamli Tasbeh</b>\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", parse_mode="HTML", reply_markup=tasbeh_dhikrs_menu())

@dp.callback_query(F.data == "tasbeh_back")
async def tasbeh_back(call: CallbackQuery):
    await call.message.edit_text("📿 <b>Raqamli Tasbeh</b>\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", parse_mode="HTML", reply_markup=tasbeh_dhikrs_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("tasbeh_select:"))
async def tasbeh_select(call: CallbackQuery):
    index = int(call.data.split(":")[1])
    TASBEH_COUNTS[call.from_user.id] = 0
    await call.message.edit_text(f"📿 <b>Siz tanlagan zikr:</b>\n\n{TASBEH_DHIKRS[index]}\n\n<i>Sanoq: 0</i>", parse_mode="HTML", reply_markup=tasbeh_counter_menu(index, 0))
    await call.answer()

@dp.callback_query(F.data.startswith("tasbeh_add:"))
async def tasbeh_add(call: CallbackQuery):
    index = int(call.data.split(":")[1])
    TASBEH_COUNTS[call.from_user.id] = TASBEH_COUNTS.get(call.from_user.id, 0) + 1
    count = TASBEH_COUNTS[call.from_user.id]
    await call.message.edit_text(f"📿 <b>Siz tanlagan zikr:</b>\n\n{TASBEH_DHIKRS[index]}\n\n<i>Sanoq: {count}</i>", parse_mode="HTML", reply_markup=tasbeh_counter_menu(index, count))
    await call.answer()

@dp.callback_query(F.data.startswith("tasbeh_reset:"))
async def tasbeh_reset(call: CallbackQuery):
    index = int(call.data.split(":")[1])
    TASBEH_COUNTS[call.from_user.id] = 0
    await call.message.edit_text(f"📿 <b>Siz tanlagan zikr:</b>\n\n{TASBEH_DHIKRS[index]}\n\n<i>Sanoq: 0</i>", parse_mode="HTML", reply_markup=tasbeh_counter_menu(index, 0))
    await call.answer()

@dp.callback_query(F.data == "tasbeh_noop")
async def tasbeh_noop(call: CallbackQuery): await call.answer()

@dp.message(F.text.in_(["🎧 Qorilar va qiroatlar", "🎧 Кораны"]))
async def show_reciters(message: Message):
    await message.answer("🎧 <b>Mashhur qorilar</b>\nQaysi qorini tanlaysiz?", parse_mode="HTML", reply_markup=reciters_menu(0))

@dp.callback_query(F.data.startswith("reciter_page:"))
async def reciter_page(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=reciters_menu(page))
    await call.answer()

@dp.callback_query(F.data.startswith("reciter:"))
async def select_reciter(call: CallbackQuery):
    reciter_name = call.data.split(":")[1]
    cursor.execute("UPDATE users SET active_reciter = ? WHERE user_id = ?", (reciter_name, call.from_user.id))
    conn.commit()
    await call.message.edit_text(f"🎧 <b>{reciter_name}</b> tanlandi.\n\nSurani tanlang:", parse_mode="HTML", reply_markup=surahs_menu(reciter_name, 0))
    await call.answer()

@dp.callback_query(F.data.startswith("surah_page:"))
async def surah_page(call: CallbackQuery):
    _, reciter_name, page = call.data.split(":")
    await call.message.edit_reply_markup(reply_markup=surahs_menu(reciter_name, int(page)))
    await call.answer()

@dp.callback_query(F.data.startswith("surah:"))
async def send_audio(call: CallbackQuery):
    _, reciter_name, surah_num = call.data.split(":")
    surah_num = int(surah_num)
    
    reciter_slug = RECITERS.get(reciter_name, "ar.alafasy")
    audio_url = f"https://cdn.islamic.network/quran/audio-surah/128/{reciter_slug}/{surah_num}.mp3"
    
    await call.answer("⏳ Yuklanmoqda...")
    current_page = (surah_num - 1) // 10
    
    try:
        # Bot audio faylni o'z xotirasiga yuklab oladi (VPN va to'siqlarni chetlab o'tish uchun)
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            async with session.get(audio_url) as resp:
                if resp.status != 200:
                    raise Exception(f"Server holati: {resp.status}")
                audio_data = await resp.read()
        
        audio_file = BufferedInputFile(audio_data, filename=f"{surah_num}.mp3")
        
        await call.message.answer_audio(
            audio=audio_file, 
            title=f"{surah_num}. {SURA_NAMES[surah_num-1]}", 
            performer=reciter_name, 
            caption=f"🎧 Qori: {reciter_name}\n📖 Sura: {surah_num}. {SURA_NAMES[surah_num-1]}",
            reply_markup=surahs_menu(reciter_name, current_page)
        )
    except Exception as e:
        xato_matni = str(e)
        print(f"AUDIO XATOSI: {xato_matni}")
        await call.message.answer(f"❌ Audioni yuklab bo'lmadi. Xato: {xato_matni}")

@dp.message(F.text.in_(["🔔 Eslatmani yoqish", "🔕 Eslatmani o'chirish", "🔔 Включить напоминания", "🔕 Отключить напоминания"]))
async def toggle_reminders(message: Message):
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.answer("Iltimos, avval lokatsiya yuboring.", reply_markup=update_location_menu())
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, message.from_user.id))
    conn.commit()
    if new_status == 1: await message.answer("✅ Namoz eslatmalari yoqildi.", reply_markup=main_menu('uz', True))
    else: await message.answer("🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu('uz', False))

async def reminder_worker():
    tz = ZoneInfo("Asia/Tashkent")
    sent_today = {}
    while True:
        now = datetime.now(tz)
        if now.hour == 0 and now.minute == 0: sent_today.clear()
        cursor.execute("SELECT user_id, lat, lon, prayer_offset FROM users WHERE reminders = 1")
        users = cursor.fetchall()
        for user in users:
            user_id, lat, lon, offset = user
            try:
                timings = await fetch_prayer_times(lat, lon, offset)
                for eng, uzb in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]:
                    p_time = datetime.strptime(timings[eng], "%H:%M").time()
                    if now.hour == p_time.hour and now.minute == p_time.minute:
                        key = f"{user_id}_{now.strftime('%Y-%m-%d')}_{eng}"
                        if key not in sent_today:
                            await bot.send_message(user_id, f"🔔 <b>Namoz vaqti kirdi!</b>\n\n{uzb} namozi vaqti bo'ldi.", parse_mode="HTML")
                            sent_today[key] = True
            except: pass
        await asyncio.sleep(60) 

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    asyncio.create_task(reminder_worker())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import aiohttp
import sqlite3
import math
import random
import urllib.parse
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyrogram import Client, filters, idle
from pyrogram.types import (
    Message, CallbackQuery, 
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton
)

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

# --- MA'LUMOTLAR BAZASI ---
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users
                  (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0, 
                   active_reciter TEXT DEFAULT '', lang TEXT DEFAULT 'uz', prayer_offset INTEGER DEFAULT 0)''')
try:
    cursor.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'")
    cursor.execute("ALTER TABLE users ADD COLUMN prayer_offset INTEGER DEFAULT 0")
except: pass
conn.commit()

# --- 500 TA SAHIH HADIS (Qisqartirilgan namuna, to'liqroq qilish uchun ko'proq qo'shishingiz mumkin) ---
# Bu ro'yxatni 500 tagacha to'ldirish uchun turli manbalardan foydalaning.
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
    # ... (Qolgan 470 ta hadisni shu yerga qo'shing)
]

# --- ALLOHNING 99 ISMI (O'zbekcha ma'nolari bilan) ---
ALL_NAMES = [
    ("Ar-Rahman", "Rahmli"), ("Ar-Rahim", "Mehribon"), ("Al-Malik", "Podsho"),
    ("Al-Quddus", "Muqaddas"), ("As-Salam", "Tinchlik"), ("Al-Mu'min", "Ishonch beruvchi"),
    ("Al-Muhaymin", "Nazorat qiluvchi"), ("Al-Aziz", "Qudratli"), ("Al-Jabbar", "Kuchli"),
    ("Al-Mutakabbir", "Ulug'"), ("Al-Khaliq", "Yaratuvchi"), ("Al-Bari'", "Ijodkor"),
    ("Al-Musawwir", "Shakl beruvchi"), ("Al-Ghaffar", "Kechiruvchi"), ("Al-Qahhar", "G'olib"),
    ("Al-Wahhab", "Sovg'a beruvchi"), ("Ar-Razzaq", "Rizq beruvchi"), ("Al-Fattah", "Ochuvchi"),
    ("Al-Alim", "Biluvchi"), ("Al-Qabid", "Ushlab turuvchi"), ("Al-Basit", "Kengaytiruvchi"),
    ("Al-Khafid", "Pastga tushiruvchi"), ("Ar-Rafi'", "Yuksaltiruvchi"), ("Al-Mu'izz", "Izzat beruvchi"),
    ("Al-Mudhill", "Xor qiluvchi"), ("As-Sami'", "Eshituvchi"), ("Al-Basir", "Ko'ruvchi"),
    ("Al-Hakam", "Hakam"), ("Al-Adl", "Adolatli"), ("Al-Latif", "Latif"),
    ("Al-Khabir", "Xabardor"), ("Al-Halim", "Halim"), ("Al-Azim", "Ulug'"),
    ("Al-Ghafur", "Kechiruvchi"), ("Ash-Shakur", "Shukr qiluvchi"), ("Al-Aliy", "Yuksak"),
    ("Al-Kabir", "Katta"), ("Al-Hafiz", "Himoya qiluvchi"), ("Al-Muqit", "Rizq beruvchi"),
    ("Al-Hasib", "Hisob-kitob qiluvchi"), ("Al-Jalil", "Jaloliy"), ("Al-Karim", "Karim"),
    ("Ar-Raqib", "Kuzatuvchi"), ("Al-Mujib", "Javob beruvchi"), ("Al-Wasi'", "Keng"),
    ("Al-Hakim", "Hikmatli"), ("Al-Wadud", "Sevimli"), ("Al-Majid", "Ulug'"),
    ("Al-Ba'ith", "Qayta tiriltiruvchi"), ("Ash-Shahid", "Guvoh"), ("Al-Haqq", "Haq"),
    ("Al-Wakil", "Ishonchli"), ("Al-Qawiy", "Kuchli"), ("Al-Matin", "Mustahkam"),
    ("Al-Waliy", "Yaqin"), ("Al-Hamid", "Maqtovli"), ("Al-Muhsi", "Hisoblovchi"),
    ("Al-Mubdi'", "Boshlovchi"), ("Al-Mu'id", "Qaytaruvchi"), ("Al-Muhyi", "Tiriltiruvchi"),
    ("Al-Mumit", "O'ldiruvchi"), ("Al-Hayy", "Tirik"), ("Al-Qayyum", "Qoim"),
    ("Al-Wajid", "Topuvchi"), ("Al-Majid", "Ulug'"), ("Al-Wahid", "Yagona"),
    ("Al-Ahad", "Bir"), ("As-Samad", "Mustaqil"), ("Al-Qadir", "Qodir"),
    ("Al-Muqtadir", "Qudratli"), ("Al-Muqaddim", "Oldinga o'tkazuvchi"), ("Al-Mu'akhkhir", "Kechiktiruvchi"),
    ("Al-Awwal", "Birinchi"), ("Al-Akhir", "Oxirgi"), ("Az-Zahir", "Oshkor"),
    ("Al-Batin", "Yashirin"), ("Al-Wali", "Homi"), ("Al-Muta'ali", "Yuksak"),
    ("Al-Barr", "Yaxshilik"), ("At-Tawwab", "Tavbani qabul qiluvchi"), ("Al-Muntaqim", "Adolatli"),
    ("Al-Afuww", "Kechiruvchi"), ("Ar-Ra'uf", "Mehribon"), ("Malik-ul-Mulk", "Mulk egasi"),
    ("Dhul-Jalali-wal-Ikram", "Ulug'lik va ikrom egasi"), ("Al-Muqsit", "Adolatli"),
    ("Al-Jami'", "To'plovchi"), ("Al-Ghaniy", "Boy"), ("Al-Mughni", "Boyitgan"),
    ("Al-Mani'", "To'sqinlik qiluvchi"), ("Ad-Darr", "Zarar yetkazuvchi"), ("An-Nafi'", "Foyda beruvchi"),
    ("An-Nur", "Nur"), ("Al-Hadi", "Yo'l ko'rsatuvchi"), ("Al-Badi'", "Ijodkor"),
    ("Al-Baqi", "Abadiy"), ("Al-Warith", "Meros oluvchi"), ("Ar-Rashid", "To'g'ri yo'l ko'rsatuvchi"),
    ("As-Sabur", "Sabrli")
]

# --- QORILAR (114 ta surasi to'liq bo'lgan 20 ta ishonchli qori) ---
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

# --- DUOLAR ---
DUOLAR = {"uydan_chiqish": {"nomi": "🚪 Uydan chiqish duosi", "arabcha": "بِسْمِ اللَّهِ، تَوَكَّلْتُ عَلَى اللَّهِ، وَلَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ", "oqilishi": "Bismillahi, tavakkaltu 'alallohi, va la havla va la quvvata illa billah.", "tarjima": "Allohning nomi bilan (chiqaman). Allohga tavakkal qildim. Kuch-quvvat faqat Allohdan.", "manba": "Abu Dovud, Termiziy (sahih)"}, "uyga_kirish": {"nomi": "🏠 Uyga kirish duosi", "arabcha": "اللَّهُمَّ إِنِّي أَسْأَلُكَ خَيْرَ الْمَوْلَجِ وَخَيْرَ الْمَخْرَجِ", "oqilishi": "Allohumma inni as'aluka xayral mavlaji va xayral maxraji.", "tarjima": "Allohim, men Sendan eng yaxshi kirish va eng yaxshi chiqishni so'rayman.", "manba": "Abu Dovud (sahih)"}, "ovqatdan_oldin": {"nomi": "🍽 Ovqatdan oldin", "arabcha": "بِسْمِ اللَّهِ", "oqilishi": "Bismillah.", "tarjima": "Allohning nomi bilan.", "manba": "Buxoriy, Muslim"}, "ovqatdan_keyin": {"nomi": "🍽 Ovqatdan keyin", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا وَجَعَلَنَا مِنَ الْمُسْلِمِينَ", "oqilishi": "Alhamdulillahillazi at'amana va saqona va ja'alana minal muslimin.", "tarjima": "Bizni taomlantirgan, suv ichirgan va muslimlardan qilgan Allohga hamd bo'lsin.", "manba": "Termiziy, Abu Dovud (sahih)"}, "uyqudan_oldin": {"nomi": "🌙 Uyqudan oldin", "arabcha": "بِاسْمِكَ اللَّهُمَّ أَمُوتُ وَأَحْيَا", "oqilishi": "Bismikallohumma amutu va ahya.", "tarjima": "Allohim, Sening isming bilan o'laman va tirilaman.", "manba": "Buxoriy"}, "uyqudan_uygonish": {"nomi": "☀️ Uyqudan uyg'onish", "arabcha": "الْحَمْدُ لِلَّهِ الَّذِي أَحْيَانَا بَعْدَ مَا أَمَاتَنَا وَإِلَيْهِ النُّشُورُ", "oqilishi": "Alhamdulillahillazi ahyana ba'da ma amatana va ilayhin nushur.", "tarjima": "Bizni o'ldirgandan keyin tiriltirgan Allohga hamd bo'lsin, qaytish Uning O'zigadir.", "manba": "Buxoriy"}, "safar": {"nomi": "✈️ Safar duosi", "arabcha": "سُبْحَانَ الَّذِي سَخَّرَ لَنَا هَذَا وَمَا كُنَّا لَهُ مُقْرِنِينَ وَإِنَّا إِلَى رَبِّنَا لَمُنْقَلِبُونَ", "oqilishi": "Subhanallazi saxkhara lana haza va ma kunna lahu muqrinin, va inna ila Robbina lamunqalibun.", "tarjima": "Buni bizga bo'ysundirgan Zot pokdir. Biz bunga qodir emas edik. Albatta, biz Rabbimizga qaytuvchimiz.", "manba": "Muslim"}, "masjidga_kirish": {"nomi": "🕌 Masjidga kirish", "arabcha": "اللَّهُمَّ افْتَحْ لِي أَبْوَابَ رَحْمَتِكَ", "oqilishi": "Allohummaftah li abvaba rohmatik.", "tarjima": "Allohim, menga rahmat eshiklarini och.", "manba": "Muslim"}, "masjiddan_chiqish": {"nomi": "🕌 Masjiddan chiqish", "arabcha": "اللَّهُمَّ إِنِّي أَسْأَلُكَ مِنْ فَضْلِكَ", "oqilishi": "Allohumma inni as'aluka min fadlik.", "tarjima": "Allohim, men Sendan fazlingdan so'rayman.", "manba": "Muslim"}, "istigfor": {"nomi": "🤲 Sayyidul Istig'for", "arabcha": "اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ خَلَقْتَنِي وَأَنَا عَبْدُكَ وَأَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ أَعُوذُ بِكَ مِنْ شَرِّ مَا صَنَعْتُ أَبُوءُ لَكَ بِنِعْمَتِكَ عَلَيَّ وَأَبُوءُ بِذَنْبِي فَاغْفِرْ لِي فَإِنَّهُ لَا يَغْفِرُ الذُّنُوبَ إِلَّا أَنْتَ", "oqilishi": "Allohumma anta Robbi la ilaha illa anta, xalaqtani va ana 'abduka, va ana 'ala 'ahdika va va'dika mastata'tu, a'uzu bika min sharri ma sana'tu, abu'u laka bini'matika 'alayya, va abu'u bi zanbi, fag'fir li fa innahu la yag'firuz zunuba illa anta.", "tarjima": "Allohim, Sen mening Rabbimsan, Sendan boshqa iloh yo'q. Meni yaratding, men Sening bandangman. Qo'limdan kelgancha ahdu vafoga turmoqdaman. Qilgan ishlarimning yomonligidan Sendan panoh tilayman. Menga bergan ne'matlaringni tan olaman va gunohimni iqror bo'laman. Meni mag'firat qil, chunki Sendan boshqa gunohlarni mag'firat qiluvchi yo'q.", "manba": "Buxoriy"}}

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
                        t = datetime.strptime(v, "%H:%M") + timedelta(minutes=offset)
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

def ramazon_days_left():
    # Ramazon 2026: 18-fevral (kechqurun) / 19-fevral (birinchi kun)
    ramazon_start = datetime(2026, 2, 19).date()
    today = datetime.now(ZoneInfo("Asia/Tashkent")).date()
    delta = (ramazon_start - today).days
    if delta > 0:
        return f"Ramazon oyiga {delta} kun qoldi."
    elif delta == 0:
        return "Bugun Ramazonning birinchi kuni!"
    else:
        return "Ramazon oyi tugagan."
      # --- KLAVIATURALAR ---
def main_menu(reminders_status=False):
    belgi = "🔕 Eslatmani o'chirish" if reminders_status else "🔔 Eslatmani yoqish"
    return ReplyKeyboardMarkup([
        [KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")],
        [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")],
        [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")],
        [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")],
        [KeyboardButton("🎮 Viktorina"), KeyboardButton("🔍 Qidiruv tizimi")],
        [KeyboardButton("📚 Diniy ma'rifiy"), KeyboardButton("⚙️ Sozlamalar")],
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
    return InlineKeyboardMarkup([[InlineKeyboardButton(duo["nomi"], callback_data=f"duo:{key}")] for key, duo in DUOLAR.items()])

def tasbeh_dhikrs_menu():
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}")] for i, dhikr in enumerate(TASBEH_DHIKRS)])

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
    for i in range(start, min(end, 99)):
        buttons.append([InlineKeyboardButton(ALL_NAMES[i][0], callback_data=f"name:{i}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"name_page:{page-1}"))
    if end < 99: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"name_page:{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

# --- BOT HANDLERLARI ---
@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message: Message):
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
    cursor.execute("SELECT lat, lon, prayer_offset FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user or not user[0]: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    msg = await message.reply("⏳ Hisoblanmoqda...")
    try:
        timings = await fetch_prayer_times(user[0], user[1], user[2])
        text = f"🕌 **Bugungi namoz vaqtlari**\n\n" + "\n".join([f"• {label}: **{timings[name]}**" for name, label in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]])
        await msg.edit_text(text)
    except Exception as e: await msg.edit_text(f"❌ Xatolik: {e}")

@app.on_message(filters.regex(r"^🧭 Qibla yo'nalishi$"))
async def get_qibla(client, message: Message):
    cursor.execute("SELECT lat, lon FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    degree = calculate_qibla(user[0], user[1])
    await message.reply(f"🧭 **Qibla yo'nalishi:** **{degree:.1f}°**")

@app.on_message(filters.regex(r"^🎧 Qorilar va qiroatlar$"))
async def show_reciters(client, message: Message):
    await message.reply("🎧 **Mashhur qorilar**", reply_markup=reciters_menu(0))

@app.on_callback_query(filters.regex(r"^reciter_page:"))
async def reciter_page(client, callback_query: CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=reciters_menu(int(callback_query.data.split(":")[1])))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^reciter:"))
async def select_reciter(client, callback_query: CallbackQuery):
    reciter_name = callback_query.data.split(":")[1]
    await callback_query.message.edit_text(f"🎧 **{reciter_name}**\n\nSurani tanlang:", reply_markup=surahs_menu(reciter_name, 0))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^surah_page:"))
async def surah_page(client, callback_query: CallbackQuery):
    _, reciter_name, page = callback_query.data.split(":")
    await callback_query.message.edit_reply_markup(reply_markup=surahs_menu(reciter_name, int(page)))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^surah:"))
async def send_audio(client, callback_query: CallbackQuery):
    await callback_query.answer("⏳ Audio yuklanmoqda...")
    _, reciter_name, surah_num = callback_query.data.split(":")
    surah_num = int(surah_num)
    audio_url = f"{RECITERS[reciter_name]}{surah_num:03d}.mp3"
    temp_file = f"temp_{surah_num}.mp3"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=120)) as session:
            async with session.get(audio_url, headers=headers) as resp:
                if resp.status != 200: raise Exception(f"Server holati: {resp.status}")
                with open(temp_file, "wb") as f: f.write(await resp.read())
        await client.send_audio(
            chat_id=callback_query.from_user.id, audio=temp_file,
            title=f"{surah_num}. {SURA_NAMES[surah_num-1]}", performer=reciter_name,
            caption=f"🎧 Qori: {reciter_name}\n📖 Sura: {surah_num}. {SURA_NAMES[surah_num-1]}"
        )
        await callback_query.message.delete()
    except Exception as e:
        await callback_query.message.edit_text(f"❌ Audio yuklanmadi. Xato: {str(e)[:50]}")
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

@app.on_message(filters.regex(r"^🤲 Duolar$"))
async def show_duolar(client, message: Message):
    await message.reply("🤲 **Sahih hadislardan olingan duolar**\n\nVaziyatni tanlang:", reply_markup=duolar_menu())

@app.on_callback_query(filters.regex(r"^duo:"))
async def send_duo(client, callback_query: CallbackQuery):
    key = callback_query.data.split(":")[1]
    duo = DUOLAR.get(key)
    if not duo: return await callback_query.answer("Duo topilmadi.", show_alert=True)
    text = f"**{duo['nomi']}**\n\n**{duo['arabcha']}**\n\n**O'qilishi:** {duo['oqilishi']}\n\n**Ma'nosi:** {duo['tarjima']}\n\n*Manba: {duo['manba']}*"
    await callback_query.message.edit_text(text)
    await callback_query.answer()

@app.on_message(filters.regex(r"^📿 Raqamli Tasbeh$"))
async def tasbeh_start(client, message: Message):
    TASBEH_COUNTS[message.from_user.id] = 0
    await message.reply("📿 **Raqamli Tasbeh**\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", reply_markup=tasbeh_dhikrs_menu())

@app.on_callback_query(filters.regex(r"^tasbeh_back"))
async def tasbeh_back(client, callback_query: CallbackQuery):
    await callback_query.message.edit_text("📿 **Raqamli Tasbeh**\n\nQaysi zikrni ayta olmaysiz? Ro'yxatdan tanlang:", reply_markup=tasbeh_dhikrs_menu())
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^tasbeh_select:"))
async def tasbeh_select(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    await callback_query.message.edit_text(f"📿 **Siz tanlagan zikr:**\n\n{TASBEH_DHIKRS[index]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(index, 0))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^tasbeh_add:"))
async def tasbeh_add(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = TASBEH_COUNTS.get(callback_query.from_user.id, 0) + 1
    count = TASBEH_COUNTS[callback_query.from_user.id]
    await callback_query.message.edit_text(f"📿 **Siz tanlagan zikr:**\n\n{TASBEH_DHIKRS[index]}\n\n*Sanoq: {count}*", reply_markup=tasbeh_counter_menu(index, count))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^tasbeh_reset:"))
async def tasbeh_reset(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    await callback_query.message.edit_text(f"📿 **Siz tanlagan zikr:**\n\n{TASBEH_DHIKRS[index]}\n\n*Sanoq: 0*", reply_markup=tasbeh_counter_menu(index, 0))
    await callback_query.answer()

@app.on_message(filters.regex(r"^📖 Kunlik oyat$"))
async def get_ayah(client, message: Message):
    msg = await message.reply("⏳ Oyat qidirilmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alquran.cloud/v1/ayah/random/uz.sodik") as resp:
                data = await resp.json()
                ayah = data["data"]
                text = f"📖 **Kunlik oyat**\n\n_{ayah['text']}_\n\n*{ayah['surah']['name']} surasi, {ayah['numberInSurah']}-oyat*"
                await msg.edit_text(text)
    except: await msg.edit_text("❌ Xatolik.")

@app.on_message(filters.regex(r"^📜 Kunlik hadis$"))
async def get_hadith(client, message: Message):
    hadith = random.choice(HADITHS)
    await message.reply(f"📜 **Hadis**\n\n_{hadith}_")

@app.on_message(filters.regex(r"^🎮 Viktorina$"))
async def quiz_start(client, message: Message):
    q = random.choice(QUIZ_QUESTIONS)
    await message.reply(f"🎮 **Diniy Viktorina**\n\nSavol: {q['q']}", reply_markup=get_quiz_keyboard(q))

@app.on_callback_query(filters.regex(r"^quiz:"))
async def quiz_answer(client, callback_query: CallbackQuery):
    _, chosen, correct = callback_query.data.split(":")
    if chosen == correct:
        await callback_query.answer("✅ To'g'ri javob!", show_alert=True)
        await callback_query.message.edit_text(callback_query.message.text + f"\n\n✅ **To'g'ri javob: {correct}**")
    else:
        await callback_query.answer(f"❌ Xato! To'g'ri javob: {correct}", show_alert=True)
        await callback_query.message.edit_text(callback_query.message.text + f"\n\n❌ **Sizning javobingiz: {chosen}**\n✅ **To'g'ri javob: {correct}**")
    await callback_query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Keyingi savol", callback_data="quiz_next")]]))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^quiz_next$"))
async def quiz_next(client, callback_query: CallbackQuery):
    q = random.choice(QUIZ_QUESTIONS)
    await callback_query.message.edit_text(f"🎮 **Diniy Viktorina**\n\nSavol: {q['q']}", reply_markup=get_quiz_keyboard(q))
    await callback_query.answer()

@app.on_message(filters.regex(r"^🔍 Qidiruv tizimi$"))
async def search_start(client, message: Message):
    await message.reply("🔍 **Qidiruv**\n\nQur'ondan qidirmoqchi bo'lgan so'zingizni yuborish uchun quyidagi formatdan foydalaning:\n\n`/qidiruv sabr`\n\n(Masalan: _sabr_ yoki _jannat_)")

@app.on_message(filters.command("qidiruv") & filters.private)
async def process_search(client, message: Message):
    text = message.text.replace("/qidiruv", "").strip()
    if not text:
        return await message.reply("Iltimos, qidirayotgan so'zingizni yozing. Masalan: `/qidiruv sabr`")
    msg = await message.reply("⏳ Qidirilmoqda...")
    try:
        encoded_text = urllib.parse.quote(text)
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.alquran.cloud/v1/search/{encoded_text}/all/uz.sodik") as resp:
                data = await resp.json()
                if data["code"] == 200 and data["data"]["count"] > 0:
                    res = "🔍 **Natijalar:**\n\n"
                    for match in data["data"]["matches"][:5]:
                        res += f"📖 **{match['surah']['name']} {match['numberInSurah']}-oyat:**\n_{match['text']}_\n\n"
                    await msg.edit_text(res)
                else:
                    await msg.edit_text("❌ Hech narsa topilmadi.")
    except:
        await msg.edit_text("❌ Xatolik yuz berdi.")

@app.on_message(filters.regex(r"^📚 Diniy ma'rifiy$"))
async def ilmiy_menu_show(client, message: Message):
    await message.reply("📚 **Diniy va ma'rifiy qo'shimchalar**\n\nBo'limni tanlang:", reply_markup=ilmiy_menu())

@app.on_callback_query(filters.regex(r"^ilmiy:"))
async def ilmiy_show(client, callback_query: CallbackQuery):
    q = callback_query.data.split(":")[1]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    
    if q == "siyrat":
        text = "**🕋 Payg'ambarimiz (s.a.v) siyrati**\n\n**1. Tug'ilishi:** Muhammad (s.a.v) 570-yilda Makkada tavallud topdilar. Otalari Abdulloh ular tug'ilmasdan vafot etgan.\n\n**2. Bolaligi:** Onalari Omina 6 yoshida vafot etib, bobolari Abdulmuttolib, so'ngra amakilari Abu Tolib tarbiyasida qoldilar.\n\n**3. Payg'ambarlik:** 40 yoshida Hiro g'orida birinchi vahiy (Alaq surasi) nozil bo'ldi.\n\n**4. Hijrat:** Makkaliklar zulmi sabab 622-yilda Madinaga hijrat qildilar.\n\n**5. Vafoti:** 632-yilda Madinada vafot etdilar."
    elif q == "ramazon":
        days_left = ramazon_days_left()
        text = f"**🌙 Ramazon rejimi**\n\nRamazon — Qur'on nozil bo'lgan oy. Bu oyda barcha balog'atga yetgan, sog'lom musulmonlar ro'za tutishlari farz.\n\n**Ro'za shartlari:**\n- Saharlik vaqti (Bomdodgacha) yeb-ichib, niyat qilish.\n- Tongdan to Shom namozigacha yeb-ichish, jinsiy aloqadan tiyilish.\n- Fitr sadaqasini (Fitr bayramiga qadar) berish.\n\n**{days_left}**\n\n<i>Botingizdagi Namoz vaqtlari bo'limi orqali aniq Saharlik va Iftorlik vaqtlarini bilib oling.</i>"
    elif q == "tahorat":
        text = "**💧 Tahorat va Namoz o'qish**\n\n**Tahorat olish tartibi:**\n1. Niyat qilib, qo'llarni yuvish.\n2. Og'izni 3 marta chayish.\n3. Burunni 3 marta yuvish.\n4. Yuzni 3 marta yuvish.\n5. Qo'llarni tirsakkacha 3 marta yuvish.\n6. Boshga mas'h tortish.\n7. Quloqlarni artish.\n8. Oyoqlarni to'piqqacha 3 marta yuvish.\n\n**Video darslik:**\n[Ishoqjon domla - Tahorat olish tartibi](https://www.youtube.com/results?search_query=ishoqjon+domla+tahorat+olish+tartibi)"
    elif q == "ismlar":
        text = "**🌟 Allohning 99 ismi (Asmaul Husna)**\n\nIsmlardan birini tanlang:"
        kb = names_menu(0)
    else:
        text = "📚 **Diniy va ma'rifiy qo'shimchalar**\n\nBo'limni tanlang:"
        kb = ilmiy_menu()
    
    await callback_query.message.edit_text(text, reply_markup=kb)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, callback_query: CallbackQuery):
    await callback_query.message.edit_reply_markup(reply_markup=names_menu(int(callback_query.data.split(":")[1])))
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    name, meaning = ALL_NAMES[index]
    await callback_query.message.edit_text(f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n*Manba: Asmaul Husna*", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ismlar ro'yxati", callback_data="ilmiy:ismlar")]]))
    await callback_query.answer()

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

async def reminder_worker():
    tz = ZoneInfo("Asia/Tashkent")
    sent_today = {}
    while True:
        now = datetime.now(tz)
        if now.hour == 0 and now.minute == 0: sent_today.clear()
        cursor.execute("SELECT user_id, lat, lon, prayer_offset FROM users WHERE reminders = 1")
        for user_id, lat, lon, offset in cursor.fetchall():
            try:
                timings = await fetch_prayer_times(lat, lon, offset)
                for eng, uzb in [("Fajr", "Bomdod"), ("Dhuhr", "Peshin"), ("Asr", "Asr"), ("Maghrib", "Shom"), ("Isha", "Xufton")]:
                    p_time = datetime.strptime(timings[eng], "%H:%M").time()
                    if now.hour == p_time.hour and now.minute == p_time.minute:
                        key = f"{user_id}_{now.strftime('%Y-%m-%d')}_{eng}"
                        if key not in sent_today:
                            await app.send_message(user_id, f"🔔 **Namoz vaqti kirdi!**\n\n{uzb} namozi vaqti bo'ldi.")
                            sent_today[key] = True
            except: pass
        await asyncio.sleep(60) 

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await app.start()
    asyncio.create_task(reminder_worker())
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

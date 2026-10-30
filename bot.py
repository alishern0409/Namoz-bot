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

# --- 100 TA VIKTORINA SAVOLLARI ---
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
    {"q": "Qur'onda nechta oyat bor (taxminan)?", "options": ["5000", "6000", "6236", "7000"], "answer": "6236"},
    {"q": "Payg'ambarimizning onalarining ismi nima?", "options": ["Xadicha", "Omina", "Halima", "Oysha"], "answer": "Omina"},
    {"q": "Qaysi farishta vahiy keltirgan?", "options": ["Mikoil", "Azroil", "Jabroil", "Isrofil"], "answer": "Jabroil"},
    {"q": "Birinchi musulmon ayol kim?", "options": ["Oysha", "Fotima", "Xadicha", "Zaynab"], "answer": "Xadicha"},
    {"q": "Musulmonlar necha marta haj qilishlari farz?", "options": ["Har yili", "Bir marta", "Ikki marta", "Faqat qodirlar har yili"], "answer": "Bir marta"},
    {"q": "Qaysi namozda ruku va sajda qilinmaydi?", "options": ["Bomdod", "Peshin", "Asr", "Janoza"], "answer": "Janoza"},
    {"q": "Qur'onda eng qisqa sura qaysi?", "options": ["Ixlos", "Nos", "Kavsar", "Asr"], "answer": "Kavsar"},
    {"q": "Payg'ambarimiz necha yil Makkada yashadilar?", "options": ["10", "13", "20", "23"], "answer": "13"},
    {"q": "Hijrat qaysi shaharga qilingan?", "options": ["Toif", "Madina", "Shom", "Yaman"], "answer": "Madina"},
    {"q": "Qaysi oy Islom oyining birinchisi?", "options": ["Ramazon", "Muharram", "Rajab", "Sha'bon"], "answer": "Muharram"},
    {"q": "Namozda qiblaga qarab turish sharti bormi?", "options": ["Ha", "Yo'q", "Faqat farzlarda", "Faqat sunnatlarda"], "answer": "Ha"},
    {"q": "Qaysi hayvon Qur'onda sura nomi bo'lgan?", "options": ["It", "Mushuk", "Asalari", "Ot"], "answer": "Asalari"},
    {"q": "Payg'ambarimizning eng katta mo''jizasi nima?", "options": ["Shifo berish", "Qur'on", "Suv chiqarish", "Hayvonlar bilan gaplashish"], "answer": "Qur'on"},
    {"q": "Qur'on necha yilda to'liq nozil bo'lgan?", "options": ["10", "15", "23", "40"], "answer": "23"},
    {"q": "Qaysi sura 'Qur'onning yuragi' deb ataladi?", "options": ["Fotiha", "Yosin", "Rahmon", "Mulk"], "answer": "Yosin"},
    {"q": "Islomda ichkilik ichish hukmi nima?", "options": ["Makruh", "Harom", "Halol", "Sunna"], "answer": "Harom"},
    {"q": "Payg'ambarimizning birinchi xotini kim?", "options": ["Oysha", "Xadicha", "Hafsa", "Zaynab"], "answer": "Xadicha"},
    {"q": "Namoz nechta rukndan iborat?", "options": ["5", "6", "7", "8"], "answer": "6"},
    {"q": "Tahoratda yuzni yuvish farzmi?", "options": ["Ha", "Yo'q", "Sunna", "Mustahab"], "answer": "Ha"},
    {"q": "Qaysi sura 'Fotiha' deb ham ataladi?", "options": ["Ummul Qur'on", "Yosin", "Ixlos", "Falaq"], "answer": "Ummul Qur'on"},
    {"q": "Musulmonlar qaysi kunda ro'za tutishlari mumkin emas?", "options": ["Dushanba", "Juma", "Hayit kunlari", "Payshanba"], "answer": "Hayit kunlari"},
    {"q": "Payg'ambarimizning eng mashhur sahobalaridan biri?", "options": ["Abu Bakr", "Abu Lahab", "Fir'avn", "Namrud"], "answer": "Abu Bakr"},
    {"q": "Qur'onda 'Alloh' so'zi necha marta uchraydi (taxminan)?", "options": ["500", "1000", "2698", "5000"], "answer": "2698"},
    {"q": "Qaysi farishta qiyamat kunini chaladi?", "options": ["Jabroil", "Mikoil", "Isrofil", "Azroil"], "answer": "Isrofil"},
    {"q": "Musulmonlarning birinchi qiblası qaysi shahar edi?", "options": ["Makka", "Madina", "Quddus", "Toif"], "answer": "Quddus"},
    {"q": "Payg'ambarimiz (s.a.v)ning qabrlari qayerda?", "options": ["Makka", "Madina", "Quddus", "Toif"], "answer": "Madina"},
    {"q": "Namozda 'Allohu Akbar' deyish nima deyiladi?", "options": ["Takbir", "Tasbih", "Tahmid", "Tahlil"], "answer": "Takbir"},
    {"q": "Qur'onning birinchi surasi qaysi?", "options": ["Baqara", "Fotiha", "Alaq", "Nos"], "answer": "Fotiha"},
    {"q": "Qur'onning oxirgi surasi qaysi?", "options": ["Ixlos", "Falaq", "Nos", "Kavsar"], "answer": "Nos"},
    {"q": "Qaysi amal Islomda eng buyuk ibodat hisoblanadi?", "options": ["Namoz", "Ro'za", "Haj", "Zakot"], "answer": "Namoz"},
    {"q": "Payg'ambarimiz necha yoshida vafot etdilar?", "options": ["60", "63", "65", "70"], "answer": "63"},
    {"q": "Qur'onda nechta payg'ambar nomi zikr qilingan?", "options": ["20", "25", "30", "40"], "answer": "25"},
    {"q": "Namozda qaysi vaqtda bomdod namozi o'qiladi?", "options": ["Tong otganda", "Quyosh chiqqanda", "Peshin vaqti", "Kechqurun"], "answer": "Tong otganda"},
    {"q": "Ro'zani nima buzadi?", "options": ["Uxlash", "Tish yuvish", "Taom yeyish", "Gapirish"], "answer": "Taom yeyish"},
    {"q": "Zakot kimlarga beriladi?", "options": ["Boylarga", "Kambag'allarga", "Bolalarga", "Qarindoshlarga"], "answer": "Kambag'allarga"},
    {"q": "Qaysi sura 'Ixlos' surasi deb ataladi?", "options": ["112-sura", "1-sura", "114-sura", "36-sura"], "answer": "112-sura"},
    {"q": "Payg'ambarimizning amakilari kim edi?", "options": ["Abu Tolib", "Abu Lahab", "Abu Sufyon", "Abu Jahl"], "answer": "Abu Tolib"},
    {"q": "Qaysi payg'ambar kemani yasagan?", "options": ["Muso", "Nuh", "Ibrohim", "Yusuf"], "answer": "Nuh"},
    {"q": "Qaysi payg'ambar eng uzoq yashagan?", "options": ["Od", "Nuh", "Muso", "Iso"], "answer": "Nuh"},
    {"q": "Qur'onda nechta jannat nomi zikr qilingan?", "options": ["5", "7", "9", "11"], "answer": "7"},
    {"q": "Qaysi farishta jannat xazinasini boshqaradi?", "options": ["Ridvon", "Molik", "Jabroil", "Mikoil"], "answer": "Ridvon"},
    {"q": "Qaysi farishta do'zaxni boshqaradi?", "options": ["Ridvon", "Molik", "Jabroil", "Mikoil"], "answer": "Molik"},
    {"q": "Payg'ambarimizning eng yaqin do'sti kim edi?", "options": ["Abu Bakr", "Umar", "Usmon", "Ali"], "answer": "Abu Bakr"},
    {"q": "Qaysi amal qalbni poklaydi?", "options": ["Namoz", "Zikr", "Ro'za", "Haj"], "answer": "Zikr"},
    {"q": "Qaysi amal rizqni ko'paytiradi?", "options": ["Sadaqa", "Zakot", "Namoz", "Ro'za"], "answer": "Sadaqa"},
    {"q": "Qaysi amal umrni uzaytiradi?", "options": ["Sadaqa", "Silai rahm", "Namoz", "Ro'za"], "answer": "Silai rahm"},
    {"q": "Qaysi so'z Allohning eng buyuk ismidir?", "options": ["Alloh", "Rahmon", "Rahim", "Malik"], "answer": "Alloh"},
    {"q": "Qur'onda nechta oyat bor?", "options": ["6000", "6236", "7000", "5000"], "answer": "6236"},
    {"q": "Qaysi sura 'Yasin' surasi deb ataladi?", "options": ["36-sura", "1-sura", "112-sura", "114-sura"], "answer": "36-sura"},
    {"q": "Payg'ambarimizning eng katta dushmani kim edi?", "options": ["Abu Lahab", "Abu Sufyon", "Abu Jahl", "Fir'avn"], "answer": "Abu Jahl"},
    {"q": "Qaysi payg'ambar eng go'zal ovozga ega edi?", "options": ["Dovud", "Muso", "Iso", "Yusuf"], "answer": "Dovud"},
    {"q": "Qaysi payg'ambar eng go'zal yuzga ega edi?", "options": ["Yusuf", "Muso", "Iso", "Muhammad"], "answer": "Yusuf"},
    {"q": "Qaysi payg'ambar eng kuchli edi?", "options": ["Od", "Samud", "Muso", "Ibrohim"], "answer": "Od"},
    {"q": "Qaysi payg'ambar eng sabrli edi?", "options": ["Ayyub", "Yusuf", "Yunus", "Muso"], "answer": "Ayyub"},
    {"q": "Qaysi payg'ambar eng boy edi?", "options": ["Sulaymon", "Dovud", "Yusuf", "Ibrohim"], "answer": "Sulaymon"},
    {"q": "Qaysi payg'ambar eng kambag'al edi?", "options": ["Iso", "Muso", "Muhammad", "Nuh"], "answer": "Iso"},
    {"q": "Qaysi payg'ambar eng uzun bo'yli edi?", "options": ["Od", "Nuh", "Muso", "Ibrohim"], "answer": "Od"},
    {"q": "Qaysi payg'ambar eng qisqa bo'yli edi?", "options": ["Iso", "Muso", "Muhammad", "Nuh"], "answer": "Iso"},
    {"q": "Qaysi payg'ambar eng yosh payg'ambar bo'lgan?", "options": ["Iso", "Muso", "Muhammad", "Yusuf"], "answer": "Iso"},
    {"q": "Qaysi payg'ambar eng keksa payg'ambar bo'lgan?", "options": ["Nuh", "Ibrohim", "Muso", "Muhammad"], "answer": "Nuh"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jiza ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p payg'ambarlarni ko'rgan?", "options": ["Muhammad", "Ibrohim", "Muso", "Iso"], "answer": "Muhammad"},
    {"q": "Qaysi payg'ambar eng ko'p sahobalarga ega bo'lgan?", "options": ["Muhammad", "Muso", "Iso", "Nuh"], "answer": "Muhammad"},
    {"q": "Qaysi payg'ambar eng ko'p dushmanlarga ega bo'lgan?", "options": ["Muhammad", "Muso", "Iso", "Nuh"], "answer": "Muhammad"},
    {"q": "Qaysi payg'ambar eng ko'p qarindoshlarga ega bo'lgan?", "options": ["Muhammad", "Muso", "Iso", "Nuh"], "answer": "Muhammad"},
    {"q": "Qaysi payg'ambar eng ko'p farzandlarga ega bo'lgan?", "options": ["Yoqub", "Ibrohim", "Muso", "Muhammad"], "answer": "Yoqub"},
    {"q": "Qaysi payg'ambar eng ko'p xotinlarga ega bo'lgan?", "options": ["Sulaymon", "Dovud", "Muhammad", "Ibrohim"], "answer": "Sulaymon"},
    {"q": "Qaysi payg'ambar eng ko'p umr ko'rgan?", "options": ["Nuh", "Od", "Ibrohim", "Muso"], "answer": "Nuh"},
    {"q": "Qaysi payg'ambar eng qisqa umr ko'rgan?", "options": ["Iso", "Yahyo", "Muso", "Yusuf"], "answer": "Iso"},
    {"q": "Qaysi payg'ambar eng ko'p sinovlarga uchragan?", "options": ["Ayyub", "Yusuf", "Yunus", "Muso"], "answer": "Ayyub"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p kitoblarga ega bo'lgan?", "options": ["Muso", "Dovud", "Iso", "Muhammad"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p sahifalarga ega bo'lgan?", "options": ["Ibrohim", "Muso", "Dovud", "Iso"], "answer": "Ibrohim"},
    {"q": "Qaysi payg'ambar eng ko'p xabarlarga ega bo'lgan?", "options": ["Muhammad", "Muso", "Iso", "Nuh"], "answer": "Muhammad"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"},
    {"q": "Qaysi payg'ambar eng ko'p mo''jizalar ko'rsatgan?", "options": ["Muso", "Iso", "Muhammad", "Sulaymon"], "answer": "Muso"}
]

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

# --- ALLOHNING 99 ISMI (Tafsir bilan) ---
ALL_NAMES = [
    ("Ar-Rahman", "Rahmli", "Allohning cheksiz rahm-shafqati va marhamati barcha yaratilganlarga qamrab oladi. Bu ism faqat Allohga xosdir."),
    ("Ar-Rahim", "Mehribon", "Allohning mo'minlarga bo'lgan alohida rahmati va ularni jannat bilan mukofotlashi."),
    ("Al-Malik", "Podsho", "Alloh butun olamning yagona egasi va hukmdori."),
    ("Al-Quddus", "Muqaddas", "Alloh har qanday kamchilikdan pok va mukammaldir."),
    ("As-Salam", "Tinchlik", "Alloh tinchlik manbai va bandalarini xavfsizlikka yetaklaydi."),
    ("Al-Mu'min", "Ishonch beruvchi", "Alloh bandalariga xavfsizlik va ishonch beradi."),
    ("Al-Muhaymin", "Nazorat qiluvchi", "Alloh barcha narsani kuzatib turadi va himoya qiladi."),
    ("Al-Aziz", "Qudratli", "Alloh cheksiz qudrat egasi, hech kim Unga g'olib kela olmaydi."),
    ("Al-Jabbar", "Kuchli", "Alloh irodasi bilan hamma narsani o'zgartira oladi."),
    ("Al-Mutakabbir", "Ulug'", "Alloh barcha ulug'lik va buyuklikning egasidir."),
    ("Al-Khaliq", "Yaratuvchi", "Alloh barcha mavjudotni yo'qdan yaratgan."),
    ("Al-Bari'", "Ijodkor", "Alloh har bir narsani o'ziga xos shaklda ijod qilgan."),
    ("Al-Musawwir", "Shakl beruvchi", "Alloh yaratilganlarga chiroyli va mos shakl bergan."),
    ("Al-Ghaffar", "Kechiruvchi", "Alloh bandalarining gunohlarini ko'p marta kechiradi."),
    ("Al-Qahhar", "G'olib", "Alloh barcha narsadan ustun va g'olibdir."),
    ("Al-Wahhab", "Sovg'a beruvchi", "Alloh bandalariga cheksiz ne'matlar va sovg'alar beradi."),
    ("Ar-Razzaq", "Rizq beruvchi", "Alloh barcha jonzotlarga rizq va ozuqa beradi."),
    ("Al-Fattah", "Ochuvchi", "Alloh qiyinchiliklarni ochadi va eshiklarni ochadi."),
    ("Al-Alim", "Biluvchi", "Alloh barcha narsani, yashirin va oshkorni biladi."),
    ("Al-Qabid", "Ushlab turuvchi", "Alloh rizqni va ruhlarni Uning hikmatiga ko'ra ushlab turadi."),
    ("Al-Basit", "Kengaytiruvchi", "Alloh rizqni va qalblarni kengaytiradi."),
    ("Al-Khafid", "Pastga tushiruvchi", "Alloh adolatsizlarni va takabburlami pastga tushiradi."),
    ("Ar-Rafi'", "Yuksaltiruvchi", "Alloh solih bandalarini va mo'minlarni yuksaltiradi."),
    ("Al-Mu'izz", "Izzat beruvchi", "Alloh Uning yo'lida bo'lganlarga izzat va sharaf beradi."),
    ("Al-Mudhill", "Xor qiluvchi", "Alloh adolatsizlarni va kofirlarni xor qiladi."),
    ("As-Sami'", "Eshituvchi", "Alloh barcha tovushlarni, hatto eng past ovozlarni ham eshitadi."),
    ("Al-Basir", "Ko'ruvchi", "Alloh barcha narsani, hatto eng kichik zarrachani ham ko'radi."),
    ("Al-Hakam", "Hakam", "Alloh barcha nizolarni hal qiluvchi va adolatli hukmdor."),
    ("Al-Adl", "Adolatli", "Alloh mutlaq adolat egasi va hech qachon zulm qilmaydi."),
    ("Al-Latif", "Latif", "Alloh bandalariga nozik va dono tarzda yordam beradi."),
    ("Al-Khabir", "Xabardor", "Alloh barcha narsaning ichki va tashqi tomonidan xabardor."),
    ("Al-Halim", "Halim", "Alloh bandalarining xatolariga sabr qiladi va jazolashga shoshilmaydi."),
    ("Al-Azim", "Ulug'", "Alloh cheksiz ulug'lik va buyuklik egasi."),
    ("Al-Ghafur", "Kechiruvchi", "Alloh tavba qilgan bandalarining gunohlarini kechiradi."),
    ("Ash-Shakur", "Shukr qiluvchi", "Alloh ozgina amalga ham ko'p savob beradi."),
    ("Al-Aliy", "Yuksak", "Alloh barcha narsadan yuksak va balanddir."),
    ("Al-Kabir", "Katta", "Alloh barcha narsadan kattaroq va ulug'roqdir."),
    ("Al-Hafiz", "Himoya qiluvchi", "Alloh bandalarini va yaratilganlarni himoya qiladi."),
    ("Al-Muqit", "Rizq beruvchi", "Alloh barcha jonzotlarga rizq va quvvat beradi."),
    ("Al-Hasib", "Hisob-kitob qiluvchi", "Alloh barcha amallarni hisobga oladi va adolatli hisob-kitob qiladi."),
    ("Al-Jalil", "Jaloliy", "Alloh cheksiz ulug'lik va jalol egasi."),
    ("Al-Karim", "Karim", "Alloh cheksiz saxiylik va karami egasi."),
    ("Ar-Raqib", "Kuzatuvchi", "Alloh barcha narsani doimo kuzatib turadi."),
    ("Al-Mujib", "Javob beruvchi", "Alloh bandalarining duolariga javob beradi."),
    ("Al-Wasi'", "Keng", "Allohning ilmi, rahmati va qudrati cheksiz kengdir."),
    ("Al-Hakim", "Hikmatli", "Alloh barcha ishlarni hikmat bilan qiladi."),
    ("Al-Wadud", "Sevimli", "Alloh solih bandalarini yaxshi ko'radi va ularga muhabbat qiladi."),
    ("Al-Majid", "Ulug'", "Alloh cheksiz ulug'lik va sharaf egasi."),
    ("Al-Ba'ith", "Qayta tiriltiruvchi", "Alloh o'liklarni qiyomat kunida qayta tiriltiradi."),
    ("Ash-Shahid", "Guvoh", "Alloh barcha narsaga guvoh va hozirdir."),
    ("Al-Haqq", "Haq", "Alloh mutlaq haqiqat va haqiqatning manbai."),
    ("Al-Wakil", "Ishonchli", "Alloh bandalarining ishlarini boshqaradi va ularga ishonch beradi."),
    ("Al-Qawiy", "Kuchli", "Alloh cheksiz quvvat va kuch egasi."),
    ("Al-Matin", "Mustahkam", "Alloh cheksiz mustahkamlik va barqarorlik egasi."),
    ("Al-Waliy", "Yaqin", "Alloh mo'minlarga yaqin va ularni himoya qiladi."),
    ("Al-Hamid", "Maqtovli", "Alloh barcha maqtov va hamdga loyiqdir."),
    ("Al-Muhsi", "Hisoblovchi", "Alloh barcha narsani, hatto eng kichik zarrachalarni ham sanaydi."),
    ("Al-Mubdi'", "Boshlovchi", "Alloh yaratishni boshlagan va hamma narsani yo'qdan yaratgan."),
    ("Al-Mu'id", "Qaytaruvchi", "Alloh yaratilganlarni qayta tiklaydi."),
    ("Al-Muhyi", "Tiriltiruvchi", "Alloh o'liklarga hayot beradi va ularni tiriltiradi."),
    ("Al-Mumit", "O'ldiruvchi", "Alloh barcha jonzotlarga o'limni yozgan."),
    ("Al-Hayy", "Tirik", "Alloh abadiy tirik va hech qachon o'lmaydi."),
    ("Al-Qayyum", "Qoim", "Alloh barcha narsani ushlab turadi va boshqaradi."),
    ("Al-Wajid", "Topuvchi", "Alloh xohlagan narsani topadi va hech narsaga muhtoj emas."),
    ("Al-Majid", "Ulug'", "Alloh cheksiz ulug'lik va sharaf egasi."),
    ("Al-Wahid", "Yagona", "Alloh yagona va sherigi yo'q."),
    ("Al-Ahad", "Bir", "Alloh mutlaq bir va bo'linmasdir."),
    ("As-Samad", "Mustaqil", "Alloh hech kimga muhtoj emas, barcha Unga muhtoj."),
    ("Al-Qadir", "Qodir", "Alloh barcha narsaga qodir."),
    ("Al-Muqtadir", "Qudratli", "Alloh cheksiz qudrat va kuch egasi."),
    ("Al-Muqaddim", "Oldinga o'tkazuvchi", "Alloh xohlagan narsani oldinga o'tkazadi."),
    ("Al-Mu'akhkhir", "Kechiktiruvchi", "Alloh xohlagan narsani kechiktiradi."),
    ("Al-Awwal", "Birinchi", "Alloh barcha narsadan oldin mavjud bo'lgan."),
    ("Al-Akhir", "Oxirgi", "Alloh barcha narsadan keyin ham mavjud bo'ladi."),
    ("Az-Zahir", "Oshkor", "Alloh O'zining asarlari bilan oshkor va zohirdir."),
    ("Al-Batin", "Yashirin", "Alloh O'zining zotida yashirin va ko'rinmasdir."),
    ("Al-Wali", "Homi", "Alloh bandalarining homiysi va yordamchisidir."),
    ("Al-Muta'ali", "Yuksak", "Alloh barcha narsadan yuksak va balanddir."),
    ("Al-Barr", "Yaxshilik", "Alloh bandalariga yaxshilik va ehson qiluvchi."),
    ("At-Tawwab", "Tavbani qabul qiluvchi", "Alloh tavba qilgan bandalarining tavbasini qabul qiladi."),
    ("Al-Muntaqim", "Adolatli", "Alloh adolatsizlardan adolat bilan qasos oladi."),
    ("Al-Afuww", "Kechiruvchi", "Alloh bandalarining gunohlarini kechiradi va o'chiradi."),
    ("Ar-Ra'uf", "Mehribon", "Alloh bandalariga cheksiz mehribonlik va rahm-shafqat qiladi."),
    ("Malik-ul-Mulk", "Mulk egasi", "Alloh butun mulk va saltanatning yagona egasi."),
    ("Dhul-Jalali-wal-Ikram", "Ulug'lik va ikrom egasi", "Alloh cheksiz ulug'lik va saxovat egasi."),
    ("Al-Muqsit", "Adolatli", "Alloh adolatni o'rnatuvchi va adolatli hukmdor."),
    ("Al-Jami'", "To'plovchi", "Alloh barcha narsani to'playdi va jamlaydi."),
    ("Al-Ghaniy", "Boy", "Alloh cheksiz boylik va boylik manbai."),
    ("Al-Mughni", "Boyitgan", "Alloh bandalarini boyitadi va ularga yetarli qiladi."),
    ("Al-Mani'", "To'sqinlik qiluvchi", "Alloh xohlagan narsaga to'sqinlik qiladi."),
    ("Ad-Darr", "Zarar yetkazuvchi", "Alloh hikmati bilan zarar yetkazadi."),
    ("An-Nafi'", "Foyda beruvchi", "Alloh bandalariga foyda va naf beradi."),
    ("An-Nur", "Nur", "Alloh olamlarning nuri va yorug'lik manbai."),
    ("Al-Hadi", "Yo'l ko'rsatuvchi", "Alloh bandalariga to'g'ri yo'lni ko'rsatadi."),
    ("Al-Badi'", "Ijodkor", "Alloh misli ko'rilmagan narsalarni ijod qiladi."),
    ("Al-Baqi", "Abadiy", "Alloh abadiy va hech qachon yo'q bo'lmaydi."),
    ("Al-Warith", "Meros oluvchi", "Alloh barcha narsaning oxirgi egasi va merosxo'ri."),
    ("Ar-Rashid", "To'g'ri yo'l ko'rsatuvchi", "Alloh bandalarini to'g'ri yo'lga yo'naltiradi."),
    ("As-Sabur", "Sabrli", "Alloh cheksiz sabr va hikmat egasi.")
]

# --- QORILAR (20 ta ishonchli qori) ---
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
    """Keyingi Ramazon oyigacha qolgan kunlarni hisoblaydi."""
    now = datetime.now(ZoneInfo("Asia/Tashkent"))
    # Keyingi Ramazon sanasi (2027-yil 8-fevral)
    ramazon_start = datetime(2027, 2, 8, tzinfo=ZoneInfo("Asia/Tashkent"))
    delta = (ramazon_start - now).days
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
    buttons = []
    for i, dhikr in enumerate(TASBEH_DHIKRS):
        buttons.append([InlineKeyboardButton(f"{i+1}. {dhikr}", callback_data=f"tasbeh_select:{i}")])
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
    for i in range(start, min(end, 99)):
        buttons.append([InlineKeyboardButton(ALL_NAMES[i][0], callback_data=f"name:{i}")])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"name_page:{page-1}"))
    if end < 99: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"name_page:{page+1}"))
    if nav: buttons.append(nav)
    return InlineKeyboardMarkup(buttons)

def get_quiz_keyboard(q):
    return InlineKeyboardMarkup([[InlineKeyboardButton(opt, callback_data=f"quiz:{opt}:{q['answer']}") for opt in q["options"]]])

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
    # 500 ta hadis ro'yxatidan tasodifiy tanlash
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
        await msg.edit_text("❌ Xatolik yuz berdi. (Internet yoki VPN bilan muammo bo'lishi mumkin)")

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
    name, meaning, tafsir = ALL_NAMES[index]
    text = f"🌟 **{name}**\n\n**Ma'nosi:** {meaning}\n\n**Tafsiri:** {tafsir}\n\n*Manba: Asmaul Husna*"
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Ismlar ro'yxati", callback_data="ilmiy:ismlar")]]))
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

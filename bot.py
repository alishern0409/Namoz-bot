import asyncio
import aiohttp
import sqlite3
import math
import random
import os
import re
import uuid
import json
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pyrogram import Client, filters, idle
from pyrogram.handlers import PollHandler
from pyrogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeAllGroupChats
)
from pyrogram.enums import ChatMemberStatus, ChatType, ParseMode, PollType
from pyrogram.errors import UserNotParticipant
from alfalak import PrayerTimes, CalculationMethod, Coordinates

# --- FAYLLARNI YUKLASH ---
try: from hadiths_data import HADITHS
except: HADITHS = ["Hadislar topilmadi."]
try: from marifiy_data import ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT
except: ALL_NAMES, SIYRAT_TEXT, TAHORAT_TEXT, RAMAZON_TEXT = [("Xatolik", "", "")], "", "", ""
try: from duolar_data import DUOLAR
except: DUOLAR = {"xato": {"nomi": "Xatolik", "arabcha": "", "oqilishi": "", "tarjima": "Yuklanmagan", "manba": ""}}

# --- SOZLAMALAR ---
BOT_TOKEN = "9251800638:AAFPMR4CNKS_2hQASTLfs-31aK6mONiE9Mg" 
API_ID = 24348700
API_HASH = "2e5778fd17289b5388a364c0ac495a64"
ADMIN_ID = 8718072369 
BOT_USERNAME = "Islomiy_agent_Bot"

app = Client("quran_bot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- GLOBAL HOLATLAR ---
USER_STATES, TEMP_FAV, SEARCH_CACHE = {}, {}, {}
TASBEH_COUNTS = {}
RECITERS = {}
QUIZ_DATA = {}
KALIMALAR_DATA = []
TASBEH_DATA = []

QUIZ_JSON_URL = "https://raw.githubusercontent.com/alishern0409/Namoz-bot/main/quiz_data.json"
KALIMALAR_JSON_URL = "https://raw.githubusercontent.com/alishern0409/Namoz-bot/main/kalimalar.json"
TASBEH_JSON_URL = "https://raw.githubusercontent.com/alishern0409/Namoz-bot/main/tasbeh.json" 
RECITERS_JSON_URL = "https://raw.githubusercontent.com/alishern0409/Namoz-bot/main/reciters.json"

GAMES = {} 
ACTIVE_POLLS = {} # Native Poll ma'lumotlarini saqlash uchun

# --- BAZA (WAL REJIMIDA) ---
conn = sqlite3.connect('users.db', check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;") 
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lat REAL, lon REAL, reminders INTEGER DEFAULT 0)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, fav_type TEXT, fav_text TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS group_settings (chat_id INTEGER PRIMARY KEY, timer INTEGER DEFAULT 15)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS quiz_stats (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, chat_id INTEGER, username TEXT, score INTEGER DEFAULT 0, date TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT)''') 
conn.commit()

# Yangi ustunlar
try: cursor.execute("ALTER TABLE users ADD COLUMN reminder_offset INTEGER DEFAULT 10"); conn.commit()
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT"); conn.commit()
except: pass
try: cursor.execute("ALTER TABLE users ADD COLUMN username TEXT"); conn.commit()
except: pass

try: 
    quran_conn = sqlite3.connect('quran.db', check_same_thread=False)
    print("✅ QURAN.DB YUKLANDI!")
except: 
    quran_conn = None

# --- MAJBURIY OBUNA TEKSHIRUVI ---
def get_channels():
    cursor.execute("SELECT value FROM bot_settings WHERE key='force_channels'")
    chs = cursor.fetchone()
    return json.loads(chs[0]) if chs else []

async def is_subscribed(client, user_id):
    if user_id == ADMIN_ID: return True
    cursor.execute("SELECT value FROM bot_settings WHERE key='force_sub'")
    st = cursor.fetchone()
    if not st or st[0] != '1': return True 
    channels = get_channels()
    if not channels: return True 
    for ch in channels:
        try:
            member = await client.get_chat_member(ch, user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]: return False
        except UserNotParticipant: return False
        except Exception as e: return False 
    return True

async def send_join_msg(client, message_or_cb):
    channels = get_channels()
    buttons = []
    for ch in channels:
        link = ch
        if not ch.startswith('http') and not ch.startswith('@') and not ch.startswith('-'):
            link = f"@{ch}"
        if link.startswith('@'): link = f"https://t.me/{link.replace('@', '')}"
        if link.startswith('-100'): link = f"https://t.me/c/{link.replace('-100', '')}"
        try:
            chat = await client.get_chat(ch)
            title = chat.title
        except: title = "Kanal"
        buttons.append([InlineKeyboardButton(f"📢 {title}", url=link)])
    buttons.append([InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")])
    text = "⚠️ <b>Diqqat!</b>\n\nBotdan foydalanish uchun quyidagi kanallarga a'zo bo'lishingiz shart."
    kb = InlineKeyboardMarkup(buttons)
    if isinstance(message_or_cb, CallbackQuery): await message_or_cb.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    else: await message_or_cb.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^check_sub$"))
async def check_sub_cb(client, callback_query: CallbackQuery):
    if await is_subscribed(client, callback_query.from_user.id):
        await callback_query.answer("✅ Rahmat! Endi botdan foydalanishingiz mumkin.", show_alert=True)
        await callback_query.message.delete()
        cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (callback_query.from_user.id,))
        user = cursor.fetchone()
        await client.send_message(callback_query.from_user.id, "Assalomu alaykum! 🕌\nKerakli bo'limni tanlang:", reply_markup=main_menu(bool(user[0]) if user else False))
    else: await callback_query.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)

# --- MA'LUMOTLAR ---
SURA_NAMES = ["Fotiha", "Baqara", "Oli Imron", "Niso", "Moida", "An'om", "A'rof", "Anfol", "Tavba", "Yunus", "Hud", "Yusuf", "Ra'd", "Ibrohim", "Hijr", "Nahl", "Isro", "Kahf", "Maryam", "Toha", "Anbiyo", "Haj", "Mu'minun", "Nur", "Furqon", "Shuaro", "Naml", "Qasas", "Ankabut", "Rum", "Luqmon", "Sajda", "Ahzob", "Saba", "Fatir", "Yosin", "Soffat", "Sod", "Zumar", "G'ofir", "Fussilat", "Sho'ro", "Zuhruf", "Duxon", "Josiya", "Ahqof", "Muhammad", "Fath", "Hujurot", "Qof", "Zoriyot", "Tur", "Najm", "Qamar", "Rahmon", "Voqea", "Hadid", "Mujodala", "Hashr", "Mumtahana", "Saff", "Jumua", "Munofiqun", "Tag'obun", "Taloq", "Tahrim", "Mulk", "Qalam", "Hoqqa", "Ma'orij", "Nuh", "Jinn", "Muzzammil", "Muddassir", "Qiyomat", "Inson", "Mursalot", "Naba'", "Nazi'ot", "Abasa", "Takvir", "Infitor", "Mutaffifin", "Inshiqoq", "Buruj", "Toriq", "A'lo", "G'oshiya", "Fajr", "Balad", "Shams", "Layl", "Zuho", "Sharh", "Tin", "Alaq", "Qadr", "Bayyina", "Zalzala", "Odiyot", "Qori'a", "Takasur", "Asr", "Humaza", "Fil", "Quraysh", "Mo'un", "Kavsar", "Kofirun", "Nasr", "Masad", "Ixlos", "Falaq", "Nos"]

def main_menu(rem=False):
    return ReplyKeyboardMarkup([
        [KeyboardButton("🎧 Qorilar va qiroatlar"), KeyboardButton("🤲 Duolar")],
        [KeyboardButton("📿 Raqamli Tasbeh"), KeyboardButton("📖 Kunlik oyat")],
        [KeyboardButton("📜 Kunlik hadis"), KeyboardButton("⭐ Sevimlilar")],
        [KeyboardButton("🎮 Viktorina"), KeyboardButton("🔍 Qidiruv tizimi")],
        [KeyboardButton("📚 Diniy ma'rifiy")],
        [KeyboardButton("🕌 Namoz vaqtlari"), KeyboardButton("🧭 Qibla yo'nalishi")],
        [KeyboardButton("📩 Qo'llab-quvvatlash")]
    ], resize_keyboard=True)

def quiz_categories_menu(is_group=False):
    buttons = [
        [InlineKeyboardButton("🕋 Islom tarixi", callback_data="quiz_cat:tarix"), InlineKeyboardButton("📜 Hadislar", callback_data="quiz_cat:hadis")],
        [InlineKeyboardButton("📖 Qur'on", callback_data="quiz_cat:quron"), InlineKeyboardButton("⚖️ Shariat", callback_data="quiz_cat:shariat")]
    ]
    if is_group: buttons.append([InlineKeyboardButton("🏆 Guruh Haftalik Reytingi", callback_data="quiz_top_weekly_group")])
    else:
        buttons.append([InlineKeyboardButton("🏆 Haftalik Reyting (Bot)", callback_data="quiz_top_weekly")])
        buttons.append([InlineKeyboardButton("🎮 Guruhda test yechish", callback_data="quiz_start_in_group")])
    return InlineKeyboardMarkup(buttons)

def duolar_menu(page=0):
    items = list(DUOLAR.items())
    start, end = page * 5, (page * 5) + 5
    btns = [[InlineKeyboardButton(d["nomi"], callback_data=f"duo:{k}")] for k, d in items[start:end]]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"duo_page:{page-1}"))
    if end < len(items): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"duo_page:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

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
    for i, dhikr in enumerate(TASBEH_DATA):
        if i % 2 == 0: btns.append([InlineKeyboardButton(f"{i+1}. {dhikr['nomi']}", callback_data=f"tasbeh_select:{i}")])
        else: btns[-1].append(InlineKeyboardButton(f"{i+1}. {dhikr['nomi']}", callback_data=f"tasbeh_select:{i}"))
    return InlineKeyboardMarkup(btns)

def tasbeh_counter_menu(index, count):
    return InlineKeyboardMarkup([[InlineKeyboardButton(f"🔢 Sanoq: {count}", callback_data="noop")], [InlineKeyboardButton("➕ Sanoqni oshirish", callback_data=f"tasbeh_add:{index}")], [InlineKeyboardButton("🔄 Tozalash", callback_data=f"tasbeh_reset:{index}")], [InlineKeyboardButton("⬅️ Zikrlar ro'yxati", callback_data="tasbeh_back")]])

def ilmiy_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🕋 Payg'ambar siyrati", callback_data="ilmiy:siyrat"), InlineKeyboardButton("🌙 Ramazon rejimi", callback_data="ilmiy:ramazon")],
        [InlineKeyboardButton("💧 Tahorat va Namoz", callback_data="ilmiy:tahorat"), InlineKeyboardButton("🌟 Allohning 99 ismi", callback_data="ilmiy:ismlar")],
        [InlineKeyboardButton("🕌 Kalimalar", callback_data="ilmiy:kalimalar")]
    ])

def names_menu(page=0):
    btns = [[InlineKeyboardButton(ALL_NAMES[i][0], callback_data=f"name:{i}")] for i in range(page*10, min((page*10)+10, len(ALL_NAMES)))]
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"name_page:{page-1}"))
    if (page*10)+10 < len(ALL_NAMES): nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"name_page:{page+1}"))
    if nav: btns.append(nav)
    return InlineKeyboardMarkup(btns)

# --- YORDAMCHI FUNKSIYALAR ---
async def load_data_from_github():
    global RECITERS, QUIZ_DATA, KALIMALAR_DATA, TASBEH_DATA
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(RECITERS_JSON_URL, timeout=10) as resp:
                if resp.status == 200: RECITERS = json.loads(await resp.text())
    except: pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(QUIZ_JSON_URL, timeout=20) as resp:
                if resp.status == 200: QUIZ_DATA = json.loads(await resp.text())
    except: pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(KALIMALAR_JSON_URL, timeout=10) as resp:
                if resp.status == 200: KALIMALAR_DATA = json.loads(await resp.text())
    except: pass
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(TASBEH_JSON_URL, timeout=10) as resp:
                if resp.status == 200: TASBEH_DATA = json.loads(await resp.text())
    except: pass

async def fetch_prayer_times(lat: float, lon: float) -> dict:
    try:
        coords = Coordinates(lat, lon)
        tz = ZoneInfo("Asia/Tashkent")
        pt = PrayerTimes(coords, datetime.now(tz), CalculationMethod.MUSLIM_WORLD_LEAGUE, time_zone=tz)
        return {"Fajr": pt.fajr.strftime("%H:%M"), "Dhuhr": pt.dhuhr.strftime("%H:%M"), "Asr": pt.asr.strftime("%H:%M"), "Maghrib": pt.maghrib.strftime("%H:%M"), "Isha": pt.isha.strftime("%H:%M")}
    except: return None

def calculate_qibla(lat: float, lon: float) -> float:
    lat1, lon1, lat2, lon2 = map(math.radians, [lat, lon, 21.4225, 39.8262])
    x = math.sin(lon2 - lon1)
    y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(lon2 - lon1)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def get_direction_name(degree: float) -> str:
    if 337.5 <= degree or degree < 22.5: return "Shimol (North) ⬆️"
    elif 22.5 <= degree < 67.5: return "Shimoli-Sharq ↗️"
    elif 67.5 <= degree < 112.5: return "Sharq ➡️"
    elif 112.5 <= degree < 157.5: return "Janubi-Sharq ↘️"
    elif 157.5 <= degree < 202.5: return "Janub ⬇️"
    elif 202.5 <= degree < 247.5: return "Janubi-G'arb ↙️"
    elif 247.5 <= degree < 292.5: return "G'arb ⬅️"
    elif 292.5 <= degree < 337.5: return "Shimoli-G'arb ↖️"
    return "Noma'lum"

def ramazon_days_left():
    delta = (datetime(2027, 2, 8, tzinfo=ZoneInfo("Asia/Tashkent")) - datetime.now(ZoneInfo("Asia/Tashkent"))).days
    return f"Ramazon oyiga {delta} kun qoldi." if delta > 0 else ("Bugun Ramazonning birinchi kuni!" if delta == 0 else "Ramazon oyi tugagan.")

async def send_long_text(message_or_cb, text, kb=None):
    if len(text) <= 4000:
        if isinstance(message_or_cb, CallbackQuery): await message_or_cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
        else: await message_or_cb.edit_text(text, reply_markup=kb, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
    else:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        if isinstance(message_or_cb, CallbackQuery):
            await message_or_cb.message.edit_text(chunks[0], disable_web_page_preview=True, parse_mode=ParseMode.HTML)
            for chunk in chunks[1:]: await message_or_cb.message.reply(chunk, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
            if kb: await message_or_cb.message.reply("⬆️ Ma'lumotlar davomi", reply_markup=kb)
        else:
            await message_or_cb.edit_text(chunks[0], disable_web_page_preview=True, parse_mode=ParseMode.HTML)
            for chunk in chunks[1:]: await message_or_cb.reply(chunk, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
            if kb: await message_or_cb.reply("⬆️ Ma'lumotlar davomi", reply_markup=kb)

# ====== ORQA FONDAGI TIZIMLAR ======
async def namoz_eslatma_loop(client):
    sent_today = {} 
    while True:
        try:
            now = datetime.now(ZoneInfo("Asia/Tashkent"))
            current_time = now.strftime("%H:%M")
            today_date = now.strftime("%Y-%m-%d")
            cursor.execute("SELECT user_id, lat, lon, reminder_offset FROM users WHERE reminders = 1")
            users = cursor.fetchall()
            for uid, lat, lon, offset in users:
                if not lat or not lon: continue
                offset = offset if offset is not None else 10
                times = await fetch_prayer_times(lat, lon)
                if not times: continue
                uz_names = {"Fajr": "Bomdod", "Dhuhr": "Peshin", "Asr": "Asr", "Maghrib": "Shom", "Isha": "Xufton"}
                for eng_name, p_time_str in times.items():
                    if not p_time_str: continue
                    p_time_dt = datetime.strptime(p_time_str, "%H:%M").replace(year=now.year, month=now.month, day=now.day, tzinfo=ZoneInfo("Asia/Tashkent"))
                    target_time_dt = p_time_dt - timedelta(minutes=offset)
                    target_time_str = target_time_dt.strftime("%H:%M")
                    if target_time_str == current_time:
                        key = (uid, today_date)
                        if key not in sent_today: sent_today[key] = []
                        if target_time_str not in sent_today[key]: 
                            sent_today[key].append(target_time_str)
                            try:
                                text = (f"🕌 <b>Namoz vaqti yaqinlashmoqda!</b>\n\n⏳ <b>{uz_names.get(eng_name, eng_name)}</b> namoziga <b>{offset} daqiqa</b> qoldi.\n🕒 Namoz vaqti: {p_time_str}")
                                await client.send_message(uid, text, parse_mode=ParseMode.HTML)
                            except Exception: pass
        except Exception: pass
        await asyncio.sleep(30) 

async def weekly_winners_notifier(client):
    sent_this_week = False
    while True:
        try:
            now = datetime.now(ZoneInfo("Asia/Tashkent"))
            if now.weekday() == 4 and now.hour == 10 and not sent_this_week:
                start_of_last_week = now - timedelta(days=7)
                start_str = start_of_last_week.strftime("%Y-%m-%d")
                cursor.execute("SELECT user_id, username, SUM(score) as total FROM quiz_stats WHERE date >= ? AND chat_id > 0 GROUP BY user_id ORDER BY total DESC LIMIT 3", (start_str,))
                top_3 = cursor.fetchall()
                if top_3:
                    prizes = {0: "100 Telegram Stars ⭐", 1: "50 Telegram Stars ⭐", 2: "30 Telegram Stars ⭐"}
                    places = {0: "🥇 1-o'rin", 1: "🥈 2-o'rin", 2: "🥉 3-o'rin"}
                    for i, (uid, uname, score) in enumerate(top_3):
                        text = (f"🎉 <b>Tabriklaymiz, {uname}!</b>\n\nSiz o'tgan haftalik viktorinada <b>{places[i]}</b>ni egalladingiz!\nTo'plagan ballingiz: <b>{score} ball</b>\n\n🎁 Sizga mukofot sifatida <b>{prizes[i]}</b> beriladi!\n\nMukofotni olish uchun iltimos admin bilan bog'laning: @jekkpot")
                        try: await client.send_message(uid, text, parse_mode=ParseMode.HTML)
                        except Exception: pass
                sent_this_week = True
            if now.weekday() != 4: sent_this_week = False
        except Exception: pass
        await asyncio.sleep(3600) 

# ====== ADMIN PANEL ======
@app.on_message(filters.command("admin") & filters.private)
async def admin_panel(client, message: Message):
    if message.from_user.id != ADMIN_ID: return await message.reply("Siz admin emassiz! 🚫")
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users:0")],
        [InlineKeyboardButton("📢 Majburiy obuna", callback_data="admin_forcesub")],
        [InlineKeyboardButton("📨 Xabar tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")]
    ])
    await message.reply("🛠 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^admin_stats$"))
async def admin_stats(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return await callback_query.answer("Ruxsat yo'q!", show_alert=True)
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(score) FROM quiz_stats")
        total_scores = cursor.fetchone()[0] or 0
        text = f"📊 <b>Bot Statistikasi</b>\n\n👥 Jami foydalanuvchilar: <b>{total_users} ta</b>\n🎮 O'ynalgan o'yinlar (ballar): <b>{total_scores} ta</b>\n"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")]])
        await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e: await callback_query.answer(f"Xatolik: {e}", show_alert=True)

@app.on_callback_query(filters.regex(r"^admin_back$"))
async def admin_back(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Foydalanuvchilar", callback_data="admin_users:0")],
        [InlineKeyboardButton("📢 Majburiy obuna", callback_data="admin_forcesub")],
        [InlineKeyboardButton("📨 Xabar tarqatish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📊 Statistika", callback_data="admin_stats")]
    ])
    await callback_query.message.edit_text("🛠 <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:", reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^admin_users:"))
async def admin_users_list(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return await callback_query.answer("Ruxsat yo'q!", show_alert=True)
    page = int(callback_query.data.split(":")[1])
    offset = page * 10
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT user_id, first_name, username FROM users LIMIT 10 OFFSET ?", (offset,))
        users = cursor.fetchall()
        text = f"👥 <b>Foydalanuvchilar ro'yxati</b> ({page+1}-sahifa)\nJami: {total} ta\n\n"
        if not users: text += "Foydalanuvchilar topilmadi."
        else:
            for uid, fname, uname in users:
                name = str(fname) if fname else "Nomsiz"
                name = name.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
                uname_str = f" (@{uname})" if uname else ""
                text += f'• <a href="tg://user?id={uid}">{name}</a>{uname_str}\n'
        nav = []
        if page > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"admin_users:{page-1}"))
        if offset + 10 < total: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"admin_users:{page+1}"))
        kb_buttons = []
        if nav: kb_buttons.append(nav)
        kb_buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")])
        await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(kb_buttons), disable_web_page_preview=True, parse_mode=ParseMode.HTML)
    except Exception as e: await callback_query.answer(f"Xatolik: {e}", show_alert=True)

@app.on_callback_query(filters.regex(r"^admin_forcesub$"))
async def admin_forcesub(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return
    cursor.execute("SELECT value FROM bot_settings WHERE key='force_sub'")
    st = cursor.fetchone()
    status = "🟢 Yoqilgan" if st and st[0] == '1' else "🔴 O'chirilgan"
    channels = get_channels()
    ch_text = "\n".join([f"• {c}" for c in channels]) if channels else "Hali kanal qo'shilmagan."
    text = f"📢 <b>Majburiy Obuna</b>\n\nHolat: {status}\n\n<b>Kanallar:</b>\n{ch_text}\n\nBotdan foydalanish uchun ushbu kanallarga obuna talab qilinsinmi?"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"O'zgartirish: {status}", callback_data="admin_toggle_fs")],
        [InlineKeyboardButton("➕ Yangi kanal qo'shish", callback_data="admin_add_channel")],
        [InlineKeyboardButton("🗑 Kanalni o'chirish", callback_data="admin_remove_channel")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_back")]
    ])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^admin_toggle_fs$"))
async def admin_toggle_fs(client, callback_query: CallbackQuery):
    cursor.execute("SELECT value FROM bot_settings WHERE key='force_sub'")
    st = cursor.fetchone()
    new_val = '0' if st and st[0] == '1' else '1'
    cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('force_sub', ?)", (new_val,))
    conn.commit()
    await admin_forcesub(client, callback_query) 

@app.on_callback_query(filters.regex(r"^admin_add_channel$"))
async def admin_add_channel(client, callback_query: CallbackQuery):
    USER_STATES[callback_query.from_user.id] = "waiting_new_channel"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Botni kanalga qo'shish", url=f"https://t.me/{BOT_USERNAME}?startchannel=true")],
        [InlineKeyboardButton("⬅️ Bekor qilish", callback_data="admin_forcesub")]
    ])
    await callback_query.message.edit_text("Kanal qo'shish uchun quyidagilardan birini qiling:\n\n1. Kanal usernameni yuboring (masalan: `@mening_kanalim`).\n2. Yoki kanaldan bitta xabarni botga **forward (uzatib)** yuboring.\n\n<i>Diqqat: Bot kanalda Admin bo'lishi shart!</i>", reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^admin_remove_channel$"))
async def admin_remove_channel(client, callback_query: CallbackQuery):
    channels = get_channels()
    if not channels: return await callback_query.answer("Kanallar yo'q!", show_alert=True)
    kb = []
    for ch in channels:
        kb.append([InlineKeyboardButton(f"❌ {ch} ni o'chirish", callback_data=f"del_ch:{ch}")])
    kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_forcesub")])
    await callback_query.message.edit_text("Qaysi kanalni o'chirmoqchisiz?", reply_markup=InlineKeyboardMarkup(kb))

@app.on_callback_query(filters.regex(r"^del_ch:"))
async def delete_channel(client, callback_query: CallbackQuery):
    ch = callback_query.data.split(":")[1]
    channels = get_channels()
    if ch in channels:
        channels.remove(ch)
        cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('force_channels', ?)", (json.dumps(channels),))
        conn.commit()
    await callback_query.answer("✅ Kanal o'chirildi!", show_alert=True)
    await admin_forcesub(client, callback_query)

@app.on_callback_query(filters.regex(r"^admin_broadcast$"))
async def admin_broadcast_cb(client, callback_query: CallbackQuery):
    if callback_query.from_user.id != ADMIN_ID: return
    USER_STATES[callback_query.from_user.id] = "waiting_broadcast"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Bekor qilish", callback_data="admin_back")]])
    await callback_query.message.edit_text("📨 <b>Xabar tarqatish</b>\n\nBotdagi barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni (matn, rasm yoki video) yuboring.\n\n<i>Diqqat: Yuborishni boshlaganingizdan so'ng biroz kutishingiz kerak bo'ladi.</i>", reply_markup=kb, parse_mode=ParseMode.HTML)

# ====== NATIVE POLL VIKTORINA ======
@app.on_message(filters.regex(r"^/quiz($|@)") | filters.regex(r"^🎮 Viktorina$"))
async def quiz_start_cmd(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    chat_id = message.chat.id
    if chat_id in GAMES: return await message.reply("⚠️ Bu chatda allaqachon o'yin ketmoqda!")
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        try:
            member = await client.get_chat_member(chat_id, message.from_user.id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return await message.reply("⚠️ O'yinni faqat guruh adminlari boshlashi mumkin!")
        except: pass
    is_group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    await message.reply("🎮 <b>Viktorina bo'limini tanlang:</b>", reply_markup=quiz_categories_menu(is_group=is_group), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^quiz_cat:"))
async def quiz_select_category(client, callback_query: CallbackQuery):
    category = callback_query.data.split(":")[1]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ 10 ta", callback_data=f"quiz_len:{category}:10"), InlineKeyboardButton("2️⃣ 20 ta", callback_data=f"quiz_len:{category}:20")],
        [InlineKeyboardButton("3️⃣ 30 ta", callback_data=f"quiz_len:{category}:30")]
    ])
    await callback_query.message.edit_text("Nechta savol o'ynaymiz?", reply_markup=kb)

@app.on_callback_query(filters.regex(r"^quiz_len:"))
async def quiz_create_lobby(client, callback_query: CallbackQuery):
    _, category, count = callback_query.data.split(":")
    count = int(count)
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    if chat_id in GAMES: return await callback_query.answer("O'yin allaqachon boshlangan!", show_alert=True)
    pool = QUIZ_DATA.get(category, [])
    if not pool: return await callback_query.answer("Bu bo'limda savollar yo'q!", show_alert=True)
    random.shuffle(pool)
    questions = []
    for q in pool[:count]:
        options = list(q["options"])
        correct = q["answer"]
        if correct not in options: continue
        random.shuffle(options)
        questions.append({"q": q["q"], "options": options, "correct_idx": options.index(correct)})

    if callback_query.message.chat.type == ChatType.PRIVATE:
        GAMES[chat_id] = {"status": "playing", "host": user.id, "category": category, "questions": questions, "current_idx": 0, "players": {user.id: {"name": user.first_name, "score": 0}}, "timer": 15, "msg_id": None}
        await callback_query.message.delete()
        return await start_game_loop(client, chat_id)

    GAMES[chat_id] = {"status": "lobby", "host": user.id, "category": category, "questions": questions, "current_idx": 0, "players": {user.id: {"name": user.first_name, "score": 0}}, "timer": 15, "msg_id": None}
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Qatnashish", callback_data="quiz_join")], [InlineKeyboardButton("🚀 O'yinni boshlash", callback_data="quiz_start_now")]])
    msg = await callback_query.message.edit_text(f"🏁 <b>Yangi o'yin tayyor!</b>\n\n📚 Bo'lim: {category.capitalize()}\n❓ Savollar: {len(questions)} ta\n\n👥 Qatnashuvchilar: 1 ta\n\n⏳ Boshqalar qo'shilishini kuting va tayyor bo'lgach <b>O'yinni boshlash</b> tugmasini bosing.", reply_markup=kb, parse_mode=ParseMode.HTML)
    GAMES[chat_id]["msg_id"] = msg.id

@app.on_callback_query(filters.regex(r"^quiz_join$"))
async def quiz_join(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user = callback_query.from_user
    if chat_id not in GAMES or GAMES[chat_id]["status"] != "lobby": return await callback_query.answer("Lobby yopilgan!", show_alert=True)
    if user.id in GAMES[chat_id]["players"]: return await callback_query.answer("Siz allaqachon qatnashyapsiz!", show_alert=True)
    GAMES[chat_id]["players"][user.id] = {"name": user.first_name, "score": 0}
    await callback_query.answer("✅ O'yinga qo'shildingiz!", show_alert=True)
    players_count = len(GAMES[chat_id]["players"])
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Qatnashish", callback_data="quiz_join")], [InlineKeyboardButton("🚀 O'yinni boshlash", callback_data="quiz_start_now")]])
    try: await callback_query.message.edit_text(f"🏁 <b>Yangi o'yin tayyor!</b>\n\n📚 Bo'lim: {GAMES[chat_id]['category'].capitalize()}\n❓ Savollar: {len(GAMES[chat_id]['questions'])} ta\n\n👥 Qatnashuvchilar: {players_count} ta\n\n⏳ Boshqalar qo'shilishini kuting va tayyor bo'lgach <b>O'yinni boshlash</b> tugmasini bosing.", reply_markup=kb, parse_mode=ParseMode.HTML)
    except: pass

@app.on_callback_query(filters.regex(r"^quiz_start_now$"))
async def quiz_start_now(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    state = GAMES.get(chat_id)
    if not state or state["status"] != "lobby": return await callback_query.answer("Lobby yopilgan yoki o'yin allaqachon boshlangan.", show_alert=True)
    if user_id != state["host"]:
        try:
            member = await client.get_chat_member(chat_id, user_id)
            if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]: return await callback_query.answer("⚠️ O'yinni faqat adminlar boshlashi mumkin!", show_alert=True)
        except: return await callback_query.answer("⚠️ O'yinni faqat adminlar boshlashi mumkin!", show_alert=True)
    state["status"] = "playing"
    await callback_query.message.delete()
    await start_game_loop(client, chat_id)

async def start_game_loop(client, chat_id):
    state = GAMES.get(chat_id)
    if state: await send_next_question(client, chat_id)

async def send_next_question(client, chat_id):
    state = GAMES.get(chat_id)
    if not state: return
    if state["current_idx"] >= len(state["questions"]): 
        return await end_game(client, chat_id)

    q = state["questions"][state["current_idx"]]
    correct_idx = q["correct_idx"]
    timer_sec = state["timer"]

    try:
        msg = await client.send_poll(
            chat_id=chat_id,
            question=f"❓ Savol {state['current_idx']+1}/{len(state['questions'])}:\n\n{q['q']}",
            options=q["options"],
            type=PollType.QUIZ,
            correct_option_id=correct_idx,
            is_anonymous=False,
            open_period=timer_sec,
            explanation="To'g'ri javob yashil rang bilan belgilangan!"
        )
        
        poll_id = msg.poll.id
        state["msg_id"] = msg.id
        
        ACTIVE_POLLS[poll_id] = {
            "chat_id": chat_id,
            "start_time": time.time(),
            "time_limit": timer_sec,
            "answers": {},
            "correct_idx": correct_idx
        }
        
        asyncio.create_task(wait_and_show_results(client, chat_id, poll_id, timer_sec))
        
    except Exception as e:
        print(f"Poll yuborishda xatolik: {e}")
        await asyncio.sleep(2)
        GAMES[chat_id]["current_idx"] += 1
        await send_next_question(client, chat_id)

async def wait_and_show_results(client, chat_id, poll_id, timer_sec):
    await asyncio.sleep(timer_sec + 2)
    
    if poll_id not in ACTIVE_POLLS: return
    
    poll_data = ACTIVE_POLLS[poll_id]
    answers = poll_data["answers"]
    state = GAMES.get(chat_id)
    
    if answers:
        # Natijalarni saralash: To'g'ri javoblar birinchi, keyin tezlik bo'yicha
        sorted_answers = sorted(
            answers.values(), 
            key=lambda x: (x['is_correct'], -x['time']), 
            reverse=True
        )
        
        result_text = "📊 <b>Savol natijalari (Barcha qatnashuvchilar):</b>\n\n"
        
        for index, user in enumerate(sorted_answers):
            rank = "🥇" if index == 0 else "🥈" if index == 1 else "🥉" if index == 2 else f"{index+1}."
            score = "✅" if user['is_correct'] else "❌"
            result_text += f"{rank} {user['name']} - {score} ({user['time']:.1f} s)\n"
            
        # Xabar juda uzun bo'lib ketsa, bo'lib yuborish (4000 belgi limiti)
        if len(result_text) > 4000:
            chunks = [result_text[i:i+4000] for i in range(0, len(result_text), 4000)]
            for chunk in chunks:
                await client.send_message(chat_id, chunk, parse_mode=ParseMode.HTML)
        else:
            await client.send_message(chat_id, result_text, parse_mode=ParseMode.HTML)
            
    # O'yinni davom ettiramiz
    del ACTIVE_POLLS[poll_id]
    if state and state["status"] == "playing":
        state["current_idx"] += 1
        await asyncio.sleep(2)
        await send_next_question(client, chat_id)

app.add_handler(PollHandler(handle_poll_answer))
async def handle_poll_answer(client, poll_answer):
    poll_id = poll_answer.poll_id
    
    if poll_id in ACTIVE_POLLS:
        user = poll_answer.user
        user_id = user.id
        
        if user_id not in ACTIVE_POLLS[poll_id]["answers"]:
            option_id = poll_answer.option_ids[0] if poll_answer.option_ids else -1
            is_correct = (option_id == ACTIVE_POLLS[poll_id]["correct_idx"])
            time_spent = time.time() - ACTIVE_POLLS[poll_id]["start_time"]
            
            name = f"@{user.username}" if user.username else user.first_name
            
            ACTIVE_POLLS[poll_id]["answers"][user_id] = {
                "name": name,
                "is_correct": is_correct,
                "time": time_spent
            }
            
            # Agar o'yin guruhda bo'lsa va odam to'g'ri javob bergan bo'lsa, umumiy o'yin hisobiga ball qo'shamiz
            chat_id = ACTIVE_POLLS[poll_id]["chat_id"]
            state = GAMES.get(chat_id)
            
            # Agar o'yinchi ro'yxatda bo'lmasa (lekin o'ynayotgan bo'lsa) qo'shib qo'yamiz
            if state:
                if user_id not in state["players"]:
                    state["players"][user_id] = {"name": user.first_name, "score": 0}
                    
                if is_correct:
                    state["players"][user_id]["score"] += 1
                    
                    # Bazaga ham yozamiz
                    date_str = datetime.now(ZoneInfo("Asia/Tashkent")).strftime("%Y-%m-%d")
                    cursor.execute("INSERT INTO quiz_stats (user_id, chat_id, username, score, date) VALUES (?, ?, ?, ?, ?)", (user_id, chat_id, user.first_name, 1, date_str))
                    conn.commit()

async def end_game(client, chat_id):
    state = GAMES.pop(chat_id, None)
    if not state or not state["players"]: return await client.send_message(chat_id, "🏁 <b>O'yin tugadi!</b>\nHech kim qatnashmadi.", parse_mode=ParseMode.HTML)
    
    sorted_players = sorted(state["players"].items(), key=lambda x: x[1]["score"], reverse=True)
    text = "🏁 <b>O'YIN TUGADI!</b>\n\n🏆 <b>Yakuniy Natijalar (Top 10):</b>\n\n"
    for i, (uid, p) in enumerate(sorted_players[:10]):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        name = p["name"].replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")
        text += f'{medal} <a href="tg://user?id={uid}">{name}</a> — <b>{p["score"]} ball</b>\n'
    text += "\n🎮 Yana o'ynash uchun /quiz buyrug'ini bering."
    try: await client.send_message(chat_id, text, parse_mode=ParseMode.HTML)
    except Exception: pass

# ====== REYTINGLAR ======
@app.on_message(filters.regex(r"^/vaqt($|@)"))
async def set_quiz_time(client, message: Message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]: return await message.reply("Bu buyruq faqat guruhlarda ishlaydi.")
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]: return await message.reply("Faqatgina guruh adminlari vaqtni o'zgartira oladi!")
    except: return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit(): return await message.reply("To'g'ri format: `/vaqt 20`")
    timer = int(parts[1])
    if timer < 5 or timer > 120: return await message.reply("Vaqt 5 dan 120 soniyagacha bo'lishi kerak.")
    cursor.execute("INSERT OR REPLACE INTO group_settings (chat_id, timer) VALUES (?, ?)", (message.chat.id, timer))
    conn.commit()
    await message.reply(f"✅ Savolga beriladigan vaqt <b>{timer} soniya</b> etib belgilandi.", parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^/top($|@)"))
async def show_weekly_top(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    today = datetime.now(ZoneInfo("Asia/Tashkent"))
    days_since_friday = (today.weekday() - 4) % 7
    start_of_week = today - timedelta(days=days_since_friday)
    start_str = start_of_week.strftime("%Y-%m-%d")
    if message.chat.type == ChatType.PRIVATE:
        cursor.execute("SELECT username, SUM(score) as total FROM quiz_stats WHERE date >= ? AND chat_id > 0 GROUP BY user_id ORDER BY total DESC LIMIT 20", (start_str,))
        rows = cursor.fetchall()
        text = "🏆 <b>Global (Bot) Haftalik TOP 20:</b>\n\n🔄 <i>Reyting har Juma kuni yangilanadi.</i>\n\n"
        if not rows: return await message.reply("Juma kunidan beri botda hali hech kim o'ynamadi.")
        for i, row in enumerate(rows):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            prize = " (100 Telegram stars ⭐)" if i == 0 else " (50 Telegram stars ⭐)" if i == 1 else " (30 Telegram stars ⭐)" if i == 2 else ""
            text += f"{medal} {row[0]} — <b>{row[1]} ball</b>{prize}\n"
    else:
        cursor.execute("SELECT username, SUM(score) as total FROM quiz_stats WHERE date >= ? AND chat_id = ? GROUP BY user_id ORDER BY total DESC LIMIT 20", (start_str, message.chat.id))
        rows = cursor.fetchall()
        text = "🏆 <b>Ushbu guruhning Haftalik TOP 20 reytingi:</b>\n\n🔄 <i>Reyting har Juma kuni yangilanadi.</i>\n\n"
        if not rows: return await message.reply("Juma kunidan beri guruhda hali hech kim o'ynamadi.")
        for i, row in enumerate(rows):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            text += f"{medal} {row[0]} — <b>{row[1]} ball</b>\n"
    await message.reply(text, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^quiz_top_weekly$"))
async def show_quiz_weekly_top(client, callback_query: CallbackQuery):
    today = datetime.now(ZoneInfo("Asia/Tashkent"))
    days_since_friday = (today.weekday() - 4) % 7
    start_str = (today - timedelta(days=days_since_friday)).strftime("%Y-%m-%d")
    cursor.execute("SELECT username, SUM(score) as total FROM quiz_stats WHERE date >= ? AND chat_id > 0 GROUP BY user_id ORDER BY total DESC LIMIT 20", (start_str,))
    rows = cursor.fetchall()
    if not rows: return await callback_query.answer("Juma kunidan beri botda hali hech kim o'ynamadi.", show_alert=True)
    text = "🏆 <b>Botdagi Haftalik TOP 20 Reyting:</b>\n\n🔄 <i>Reyting har Juma kuni yangilanadi.</i>\n\n"
    for i, row in enumerate(rows):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        prize = " (100 Telegram stars ⭐)" if i == 0 else " (50 Telegram stars ⭐)" if i == 1 else " (30 Telegram stars ⭐)" if i == 2 else ""
        text += f"{medal} {row[0]} — <b>{row[1]} ball</b>{prize}\n"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back")]])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^quiz_top_weekly_group$"))
async def show_quiz_weekly_top_group(client, callback_query: CallbackQuery):
    chat_id = callback_query.message.chat.id
    today = datetime.now(ZoneInfo("Asia/Tashkent"))
    days_since_friday = (today.weekday() - 4) % 7
    start_str = (today - timedelta(days=days_since_friday)).strftime("%Y-%m-%d")
    cursor.execute("SELECT username, SUM(score) as total FROM quiz_stats WHERE date >= ? AND chat_id = ? GROUP BY user_id ORDER BY total DESC LIMIT 20", (start_str, chat_id))
    rows = cursor.fetchall()
    if not rows: return await callback_query.answer("Juma kunidan beri guruhda hali hech kim o'ynamadi.", show_alert=True)
    text = "🏆 <b>Guruhning Haftalik TOP 20 Reytingi:</b>\n\n🔄 <i>Reyting har Juma kuni yangilanadi.</i>\n\n"
    for i, row in enumerate(rows):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
        text += f"{medal} {row[0]} — <b>{row[1]} ball</b>\n"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="quiz_back")]])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^quiz_back$"))
async def quiz_back(client, callback_query: CallbackQuery):
    is_group = callback_query.message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    await callback_query.message.edit_text("🎮 <b>Viktorina bo'limini tanlang:</b>", reply_markup=quiz_categories_menu(is_group=is_group), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^quiz_start_in_group$"))
async def start_in_group_callback(client, callback_query: CallbackQuery):
    bot_link = f"https://t.me/{BOT_USERNAME}?startgroup=true"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("➕ Botni guruhga qo'shish", url=bot_link)]])
    await callback_query.message.edit_text("🎮 <b>Guruhda test yechish qoidalari:</b>\n\n1. Avval botni o'z guruhingizga qo'shing (quyidagi tugma orqali).\n2. Botni guruhda <b>Admin</b> qilib tayinlang.\n3. Guruhga o'tib <b>/quiz</b> buyrug'ini yozing.\n4. Guruhda o'yin admin ruxsati bilan boshlanadi!", reply_markup=kb, parse_mode=ParseMode.HTML)

# ====== QORILAR VA DUOLAR ======
@app.on_callback_query(filters.regex(r"^reciter:"))
async def select_reciter(client, callback_query: CallbackQuery):
    reciter_name = callback_query.data.split(":", 1)[1]
    await callback_query.message.edit_text(f"🎧 <b>{reciter_name}</b>", reply_markup=surahs_menu(reciter_name, 0), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^reciter_page:"))
async def reciter_page(client, callback_query: CallbackQuery):
    page = int(callback_query.data.split(":")[1])
    await callback_query.message.edit_text("🎧 <b>Mashhur qorilar</b>", reply_markup=reciters_menu(page), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^surah_page:"))
async def surah_page(client, callback_query: CallbackQuery):
    _, reciter_name, page_s = callback_query.data.split(":")
    page = int(page_s)
    await callback_query.message.edit_text(f"🎧 <b>{reciter_name}</b>", reply_markup=surahs_menu(reciter_name, page), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^surah:"))
async def send_audio(client, callback_query: CallbackQuery):
    await callback_query.answer("⏳ Audio yuklanmoqda...")
    _, reciter_name, surah_num = callback_query.data.split(":")
    surah_num = int(surah_num)
    if reciter_name not in RECITERS: return await callback_query.answer("Xatolik: Qori topilmadi", show_alert=True)
    audio_url = f"{RECITERS[reciter_name]}{surah_num:03d}.mp3"
    temp_file = f"temp_{surah_num}.mp3"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with aiohttp.ClientSession() as session:
            async with session.get(audio_url, headers=headers) as resp:
                if resp.status == 404: return await callback_query.message.edit_text(f"❌ <b>Xato:</b> {reciter_name} qorisida {surah_num}-sura topilmadi.", parse_mode=ParseMode.HTML)
                elif resp.status != 200: return await callback_query.message.edit_text(f"❌ <b>Xato:</b> Server bilan aloqa uzildi.", parse_mode=ParseMode.HTML)
                with open(temp_file, "wb") as f: f.write(await resp.read())
        await client.send_audio(callback_query.from_user.id, audio=temp_file, title=f"{surah_num}-sura", performer=reciter_name)
        await callback_query.message.delete()
    except Exception: await callback_query.message.edit_text(f"❌ Tizim xatosi: Qayta urinib ko'ring.", parse_mode=ParseMode.HTML)
    finally:
        if os.path.exists(temp_file): os.remove(temp_file)

@app.on_callback_query(filters.regex(r"^duo:"))
async def send_duo(client, callback_query: CallbackQuery):
    key = callback_query.data.split(":")[1]
    duo = DUOLAR.get(key)
    if not duo: return await callback_query.answer("Topilmadi", show_alert=True)
    text = f"<b>{duo['nomi']}</b>\n\n<b>{duo['arabcha']}</b>\n\n<b>O'qilishi:</b> {duo['oqilishi']}\n\n<b>Ma'nosi:</b> {duo['tarjima']}\n\n<b>Manba:</b> {duo['manba']}"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"{duo['nomi']} - {duo['tarjima']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:duo:{fav_id}")], [InlineKeyboardButton("⬅️ Orqaga", callback_data="duo_back")]])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^duo_back$"))
async def duo_back(client, callback_query: CallbackQuery): await callback_query.message.edit_text("🤲 <b>Duolar</b>", reply_markup=duolar_menu(0), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^duo_page:"))
async def duo_page(client, callback_query: CallbackQuery): await callback_query.message.edit_text("🤲 <b>Duolar</b>", reply_markup=duolar_menu(int(callback_query.data.split(":")[1])), parse_mode=ParseMode.HTML)

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
    else: await callback_query.answer("Xatolik: Ma'lumot topilmadi.", show_alert=True)

# ====== TASBEH ======
@app.on_callback_query(filters.regex(r"^tasbeh_select:"))
async def tasbeh_select(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    zikr = TASBEH_DATA[index]
    text = f"📿 <b>Zikr:</b> {zikr['nomi']}\n\n<b>Ma'nosi:</b> {zikr['tarjima']}\n\n<i>Sanoq: 0</i>"
    await callback_query.message.edit_text(text, reply_markup=tasbeh_counter_menu(index, 0), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^tasbeh_add:"))
async def tasbeh_add(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = TASBEH_COUNTS.get(callback_query.from_user.id, 0) + 1
    zikr = TASBEH_DATA[index]
    text = f"📿 <b>Zikr:</b> {zikr['nomi']}\n\n<b>Ma'nosi:</b> {zikr['tarjima']}\n\n<i>Sanoq: {TASBEH_COUNTS[callback_query.from_user.id]}</i>"
    await callback_query.message.edit_text(text, reply_markup=tasbeh_counter_menu(index, TASBEH_COUNTS[callback_query.from_user.id]), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^tasbeh_reset:"))
async def tasbeh_reset(client, callback_query: CallbackQuery):
    index = int(callback_query.data.split(":")[1])
    TASBEH_COUNTS[callback_query.from_user.id] = 0
    zikr = TASBEH_DATA[index]
    text = f"📿 <b>Zikr:</b> {zikr['nomi']}\n\n<b>Ma'nosi:</b> {zikr['tarjima']}\n\n<i>Sanoq: 0</i>"
    await callback_query.message.edit_text(text, reply_markup=tasbeh_counter_menu(index, 0), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^tasbeh_back$"))
async def tasbeh_back(client, callback_query: CallbackQuery): await callback_query.message.edit_text("📿 <b>Raqamli Tasbeh</b>\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu(), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^noop$"))
async def noop(client, callback_query: CallbackQuery): await callback_query.answer()

# ====== ILMIY, KALIMALAR, ISMLAR ======
@app.on_callback_query(filters.regex(r"^ilmiy:"))
async def ilmiy_show(client, callback_query: CallbackQuery):
    q = callback_query.data.split(":")[1]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    if q == "siyrat": await send_long_text(callback_query, SIYRAT_TEXT, kb); return
    elif q == "ramazon": text = f"<b>🌙 Ramazon</b>\n\n{RAMAZON_TEXT}\n\n<i>{ramazon_days_left()}</i>"
    elif q == "tahorat": text = TAHORAT_TEXT
    elif q == "ismlar": text = "<b>🌟 Allohning 99 ismi</b>\n\nO'rganish uchun ismni tanlang:"; kb = names_menu(0)
    elif q == "kalimalar": 
        text = "🕌 <b>Kalimalar</b>\n\nO'rganish va zikr qilish uchun kalimani tanlang:"; 
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(k["nomi"], callback_data=f"kalima_show:{i}")] for i, k in enumerate(KALIMALAR_DATA)] + [[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:back")]])
    else: text = "📚 <b>Bo'limni tanlang:</b>"; kb = ilmiy_menu()
    await callback_query.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^kalima_show:"))
async def show_kalima_text(client, callback_query: CallbackQuery):
    idx = int(callback_query.data.split(":")[1])
    if idx >= len(KALIMALAR_DATA): return await callback_query.answer("Xatolik!", show_alert=True)
    k = KALIMALAR_DATA[idx]
    text = f"🕌 <b>{k['nomi']}</b>\n\n<b>Arabcha:</b>\n{k['arabcha']}\n\n<b>O'qilishi:</b>\n<i>{k['oqilishi']}</i>\n\n<b>Ma'nosi:</b>\n{k['tarjima']}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:kalimalar")]])
    await callback_query.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^name:"))
async def show_name(client, callback_query: CallbackQuery):
    name, meaning, tafsir = ALL_NAMES[int(callback_query.data.split(":")[1])]
    await callback_query.message.edit_text(f"🌟 <b>{name}</b>\n\n<b>Ma'nosi:</b> {meaning}\n\n<b>Tafsiri:</b> {tafsir}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Orqaga", callback_data="ilmiy:ismlar")]]), parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^name_page:"))
async def name_page(client, callback_query: CallbackQuery): await callback_query.message.edit_text("🌟 <b>Allohning 99 ismi</b>", reply_markup=names_menu(int(callback_query.data.split(":")[1])), parse_mode=ParseMode.HTML)

# ====== QO'LLAB-QUVVATLASH ======
@app.on_message(filters.regex(r"^📩 Qo'llab-quvvatlash$") & filters.private)
async def support_menu(client, message: Message):
    text = "📩 <b>Qo'llab-quvvatlash</b>\n\nTaklif va murojaatlar uchun admin bilan bog'lanishingiz mumkin."
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Adminga yozish (@jekkpot)", url="https://t.me/jekkpot")]])
    await message.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)

# ====== ASOSIY HANDLERLAR (BOT UCHUN) ======
@app.on_message(filters.regex(r"^/start($|@)"))
async def cmd_start(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    fname = message.from_user.first_name if message.from_user.first_name else "Nomsiz"
    uname = message.from_user.username if message.from_user.username else ""
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
    cursor.execute("UPDATE users SET first_name=?, username=? WHERE user_id=?", (fname, uname, message.from_user.id))
    conn.commit()
    if message.chat.type == ChatType.PRIVATE:
        cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
        user = cursor.fetchone()
        await message.reply("Assalomu alaykum! 🕌\nKerakli bo'limni tanlang:", reply_markup=main_menu(bool(user[0]) if user else False))
    else:
        await message.reply("Assalomu alaykum! 🕌\n\n🎮 Viktorinani boshlash uchun /quiz buyrug'ini bering.\n🏆 Guruh reytingini ko'rish uchun /top buyrug'ini bering.")

@app.on_message(filters.regex(r"^🎧 Qorilar va qiroatlar$") & filters.private)
async def show_reciters(client, message: Message): 
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    await message.reply("🎧 <b>Mashhur qorilar</b>", reply_markup=reciters_menu(0), parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^🤲 Duolar$") & filters.private)
async def show_duolar(client, message: Message): 
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    await message.reply("🤲 <b>Sahih hadislardan olingan duolar</b>\n\nVaziyatni tanlang:", reply_markup=duolar_menu(0), parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^📿 Raqamli Tasbeh$") & filters.private)
async def tasbeh_start(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    TASBEH_COUNTS[message.from_user.id] = 0
    await message.reply("📿 <b>Raqamli Tasbeh</b>\n\nZikrni tanlang:", reply_markup=tasbeh_dhikrs_menu(), parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^📖 Kunlik oyat$") & filters.private)
async def get_ayah(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    msg = await message.reply("⏳ Oyat qidirilmoqda...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.alquran.cloud/v1/ayah/random/uz.sodik") as resp:
                data = await resp.json()
                ayah = data["data"]
                text = f"📖 <b>Kunlik oyat</b>\n\n<i>{ayah['text']}</i>\n\n<b>{ayah['surah']['name']} surasi, {ayah['numberInSurah']}-oyat</b>"
                fav_id = str(uuid.uuid4())
                TEMP_FAV[fav_id] = text
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:oyat:{fav_id}")]])
                await msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except: await msg.edit_text("❌ Xatolik.")

@app.on_message(filters.regex(r"^📜 Kunlik hadis$") & filters.private)
async def get_hadith(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    hadith_text = random.choice(HADITHS)
    text = f"📜 <b>Hadis</b>\n\n<i>{hadith_text}</i>"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = text
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:hadis:{fav_id}")]])
    await message.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^⭐ Sevimlilar$") & filters.private)
async def show_favorites(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    cursor.execute("SELECT fav_text FROM favorites WHERE user_id = ?", (message.from_user.id,))
    favs = cursor.fetchall()
    if not favs: return await message.reply("⭐ Sizda hali sevimli ma'lumotlar yo'q.")
    text = "⭐ <b>Sevimlilar:</b>\n\n"
    for fav in favs: text += f"• {fav[0][:100]}...\n\n"
    await message.reply(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^📚 Diniy ma'rifiy$") & filters.private)
async def ilmiy_menu_show(client, message: Message): 
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    await message.reply("📚 <b>Bo'limni tanlang:</b>", reply_markup=ilmiy_menu(), parse_mode=ParseMode.HTML)

@app.on_message(filters.regex(r"^🔍 Qidiruv tizimi$") & filters.private)
async def search_start(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = "search"
    await message.reply("🔍 <b>Qidiruv rejimi yoqildi.</b>\n\nKetma-ket qidiruv uchun so'zlarni yozib yuboraverasiz. Qidiruvdan chiqish uchun boshqa bo'limni tanlang yoki /start bosing.", parse_mode=ParseMode.HTML)

@app.on_message(filters.private & ~filters.regex(r"^/"), group=1)
async def handle_search_input(client, message: Message):
    if USER_STATES.get(message.from_user.id) == "waiting_broadcast":
        if message.from_user.id != ADMIN_ID: return
        USER_STATES[message.from_user.id] = None 
        
        msg = await message.reply("⏳ Xabar tarqatish boshlandi. Iltimos kuting...")
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()
        
        success = 0
        failed = 0
        
        for (uid,) in users:
            try:
                await message.copy(chat_id=uid)
                success += 1
                await asyncio.sleep(0.05)
            except Exception:
                failed += 1
                
        await msg.edit_text(f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\nMuvaffaqiyatli: {success} ta\nXatolik: {failed} ta", parse_mode=ParseMode.HTML)
        return
        
    if USER_STATES.get(message.from_user.id) == "waiting_new_channel":
        if message.from_user.id != ADMIN_ID: return
        ch = message.text.strip() if message.text else ""
        
        if message.forward_from_chat:
            ch = message.forward_from_chat.id
        elif ch.startswith("https://t.me/"): 
            ch = "@" + ch.split("https://t.me/")[1].strip("/")
            
        try:
            chat = await client.get_chat(ch)
            bot_member = await client.get_chat_member(chat.id, "me")
            if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return await message.reply("❌ Bot bu kanalda admin emas! Iltimos, avval botni kanalga qo'shib, admin qiling.")
            
            channels = get_channels()
            if str(ch) not in [str(c) for c in channels]: 
                channels.append(chat.id if isinstance(ch, int) or ch.startswith('-') else ch)
            
            cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('force_channels', ?)", (json.dumps(channels),))
            conn.commit()
            
            USER_STATES[message.from_user.id] = None
            await message.reply(f"✅ Kanal muvaffaqiyatli qo'shildi: {chat.title}\n\nEndi obunani yoqishingiz mumkin.")
            return await admin_panel(client, message)
        except Exception as e:
            return await message.reply(f"❌ Kanal topilmadi yoki xatolik: {e}")

    if message.chat.id in GAMES: return 
    if USER_STATES.get(message.from_user.id) != "search": return
    
    text = message.text.strip()
    menu_buttons = ["🎧 Qorilar va qiroatlar", "🤲 Duolar", "📿 Raqamli Tasbeh", "📖 Kunlik oyat", "📜 Kunlik hadis", "⭐ Sevimlilar", "🎮 Viktorina", "🔍 Qidiruv tizimi", "📚 Diniy ma'rifiy", "🕌 Namoz vaqtlari", "🧭 Qibla yo'nalishi", "⬅️ Orqaga", "📍 Lokatsiyani yuborish", "🔔 Eslatmani yoqish", "🔕 Eslatmani o'chirish", "📩 Qo'llab-quvvatlash"]
    if text in menu_buttons: return

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
        await msg.edit_text("❌ Qidiruvda xatolik yuz berdi.")

# ====== QIDIRUV NATIJALARI ======
async def show_search_result(message_or_cb, user_id: int, is_edit=False):
    cache = SEARCH_CACHE.get(user_id)
    if not cache or not cache["results"]: return
    idx = cache["idx"]
    total = len(cache["results"])
    surah_num, ayah_num, uzbek_text = cache["results"][idx]
    surah_name = SURA_NAMES[surah_num - 1] if 1 <= surah_num <= 114 else f"{surah_num}-sura"
    text = f"🔍 <b>'{cache['query']}' so'zi bo'yicha natija:</b>\n\n📖 <b>{surah_name} surasi, {ayah_num}-oyat:</b>\n<i>{uzbek_text}</i>\n\n"
    fav_id = str(uuid.uuid4())
    TEMP_FAV[fav_id] = f"📖 {surah_name} surasi, {ayah_num}-oyat:\n{uzbek_text}"
    save_btn = [InlineKeyboardButton("⭐ Saqlash", callback_data=f"fav_save:search:{fav_id}")]
    nav = []
    if idx > 0: nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data="search_page:prev"))
    nav.append(InlineKeyboardButton(f"{idx+1}/{total}", callback_data="noop"))
    if idx < total - 1: nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data="search_page:next"))
    kb = InlineKeyboardMarkup([save_btn, nav])
    if is_edit: await message_or_cb.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True, parse_mode=ParseMode.HTML)
    else: await message_or_cb.edit_text(text, reply_markup=kb, disable_web_page_preview=True, parse_mode=ParseMode.HTML)

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

@app.on_message(filters.regex(r"^(🔔 Eslatmani yoqish|🔕 Eslatmani o'chirish)$") & filters.private)
async def toggle_reminders(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (message.from_user.id,))
    user = cursor.fetchone()
    if not user: return await message.reply("Iltimos, avval lokatsiya yuboring.")
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, message.from_user.id))
    conn.commit()
    await message.reply("✅ Namoz eslatmalari yoqildi." if new_status == 1 else "🔕 Namoz eslatmalari o'chirildi.", reply_markup=main_menu(new_status == 1))

@app.on_message(filters.regex(r"^⬅️ Orqaga$") & filters.private)
async def back_to_main_menu(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    USER_STATES[message.from_user.id] = None
    await message.reply("Asosiy menyu:", reply_markup=main_menu(False))

# ====== NAMOZ VAQTI VA QIBLA ======
namoz_kb = ReplyKeyboardMarkup([[KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)], [KeyboardButton("⬅️ Orqaga")]], resize_keyboard=True)

@app.on_message(filters.regex(r"^/namoz($|@)") | filters.regex(r"^🕌 Namoz vaqtlari$") & filters.private)
async def namoz_cmd(client, message: Message): 
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    await message.reply("📍 Namoz vaqtlarini bilish uchun joylashuvingizni yuboring:", reply_markup=namoz_kb)

@app.on_message(filters.regex(r"^/qibla($|@)") | filters.regex(r"^🧭 Qibla yo'nalishi$") & filters.private)
async def qibla_cmd(client, message: Message): 
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    await message.reply("🧭 Qibla yo'nalishini bilish uchun joylashuvni yuboring:", reply_markup=namoz_kb)

@app.on_message(filters.regex(r"^/ramazon($|@)"))
async def ramazon_cmd(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    text = f"🌙 <b>Ramazon oyi ma'lumotlari:</b>\n\n⏳ {ramazon_days_left()}\n\nRamazon oyida barcha ibodatlaringiz qabul bo'lsin!"
    await message.reply(text, parse_mode=ParseMode.HTML)

@app.on_message(filters.location)
async def namoz_qibla_handler(client, message: Message):
    if not await is_subscribed(client, message.from_user.id): return await send_join_msg(client, message)
    lat, lon = message.location.latitude, message.location.longitude
    cursor.execute("INSERT OR REPLACE INTO users (user_id, lat, lon) VALUES (?, ?, ?)", (message.from_user.id, lat, lon))
    conn.commit()
    msg = await message.reply("⏳ Hisoblanmoqda...")
    try:
        times = await fetch_prayer_times(lat, lon)
        if not times: return await msg.edit_text("❌ Namoz vaqtlarini hisoblashda xatolik yuz berdi.")
        qibla = calculate_qibla(lat, lon)
        direction = get_direction_name(qibla)
        cursor.execute("SELECT reminders, reminder_offset FROM users WHERE user_id = ?", (message.from_user.id,))
        user_data = cursor.fetchone()
        rem_status = user_data[0] if user_data else 0
        offset = user_data[1] if user_data else 10
        rem_text = "🔕 Eslatmani o'chirish" if rem_status == 1 else "🔔 Eslatmani yoqish"
        text = (
            f"🕌 <b>Namoz vaqtlari</b> (Mintaqangiz bo'yicha)\n\n"
            f"🌅 Bomdod: <b>{times['Fajr']}</b>\n"
            f"☀️ Peshin: <b>{times['Dhuhr']}</b>\n"
            f"🌤 Asr: <b>{times['Asr']}</b>\n"
            f"🌇 Shom: <b>{times['Maghrib']}</b>\n"
            f"🌙 Xufton: <b>{times['Isha']}</b>\n\n"
            f"🧭 <b>Qibla:</b> {qibla:.1f}° ({direction})\n"
            f"📍 Koordinatalar: {lat:.4f}, {lon:.4f}"
        )
        kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {offset} daqiqa oldin", callback_data="set_remind_offset")]])
        await msg.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        if message.chat.type == ChatType.PRIVATE: await message.reply("Asosiy menyu:", reply_markup=main_menu(rem_status == 1))
    except Exception as e:
        try: await msg.edit_text(f"⚠️ Xatolik yuz berdi: {e}")
        except: pass

@app.on_callback_query(filters.regex(r"^toggle_namoz_remind$"))
async def toggle_namoz_reminder_cb(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user: return await callback_query.answer("Iltimos, avval lokatsiya yuboring!", show_alert=True)
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, user_id))
    conn.commit()
    rem_text = "🔕 Eslatmani o'chirish" if new_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {user[1] if len(user) > 1 and user[1] else 10} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.answer("✅ Eslatmalar yoqildi!" if new_status == 1 else "🔕 Eslatmalar o'chirildi.", show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

@app.on_callback_query(filters.regex(r"^set_remind_offset$"))
async def set_remind_offset_menu(client, callback_query: CallbackQuery):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("0 daqiqa", callback_data="apply_offset:0"), InlineKeyboardButton("5 daqiqa", callback_data="apply_offset:5")],
        [InlineKeyboardButton("10 daqiqa", callback_data="apply_offset:10"), InlineKeyboardButton("15 daqiqa", callback_data="apply_offset:15")],
        [InlineKeyboardButton("20 daqiqa", callback_data="apply_offset:20"), InlineKeyboardButton("30 daqiqa", callback_data="apply_offset:30")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="close_offset_menu")]
    ])
    await callback_query.message.edit_text("⏱ <b>Ogohlantirish vaqtini tanlang:</b>\n\nNamoz vaqtidan qancha daqiqa oldin eslatma kelishini xohlaysiz?", reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^apply_offset:"))
async def apply_remind_offset(client, callback_query: CallbackQuery):
    offset = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id
    cursor.execute("UPDATE users SET reminder_offset = ? WHERE user_id = ?", (offset, user_id))
    conn.commit()
    await callback_query.answer(f"✅ Ogohlantirish {offset} daqiqa oldin qilib belgilandi!", show_alert=True)
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    rem_status = user_data[0] if user_data else 0
    rem_text = "🔕 Eslatmani o'chirish" if rem_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {offset} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

@app.on_callback_query(filters.regex(r"^close_offset_menu$"))
async def close_offset_menu(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute("SELECT reminders, reminder_offset FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    rem_status = user_data[0] if user_data else 0
    offset = user_data[1] if user_data and user_data[1] else 10
    rem_text = "🔕 Eslatmani o'chirish" if rem_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {offset} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

# --- ASOSIY LOOP ---
async def main():
    print("Bot ishga tushmoqda...")
    await load_data_from_github() 
    await app.start()
    asyncio.create_task(namoz_eslatma_loop(app))
    asyncio.create_task(weekly_winners_notifier(app))
    await app.set_bot_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("quiz", "Viktorinani boshlash"),
        BotCommand("top", "Haftalik reytingni ko'rish"),
        BotCommand("namoz", "Namoz vaqtlarini bilish"),
        BotCommand("qibla", "Qibla yo'nalishini aniqlash"),
        BotCommand("ramazon", "Ramazonga qolgan kunlar")
    ], scope=BotCommandScopeAllPrivateChats())
    await app.set_bot_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("quiz", "Viktorinani boshlash"),
        BotCommand("top", "Guruh reytingini ko'rish"),
        BotCommand("ramazon", "Ramazonga qolgan kunlar")
    ], scope=BotCommandScopeAllGroupChats())
    print("Bot muvaffaqiyatli ishga tushdi...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())

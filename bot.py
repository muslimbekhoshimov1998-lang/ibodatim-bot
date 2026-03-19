import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

import os
API_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

conn = sqlite3.connect("ibodatim.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    item_name TEXT,
    item_value TEXT,
    record_date TEXT
)
""")
conn.commit()

user_state = {}

PRAYERS = ["Bomdod", "Peshin", "Asr", "Shom", "Xufton", "Vitr"]

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Bomdod"), KeyboardButton(text="Peshin"), KeyboardButton(text="Asr")],
            [KeyboardButton(text="Shom"), KeyboardButton(text="Xufton"), KeyboardButton(text="Vitr")],
            [KeyboardButton(text="Tahajjud"), KeyboardButton(text="Qur'on"), KeyboardButton(text="Zikr")],
            [KeyboardButton(text="/today")]
        ],
        resize_keyboard=True
    )

def prayer_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Ado qildim"), KeyboardButton(text="Qazo bo'ldi")],
            [KeyboardButton(text="Jamoat bilan")],
            [KeyboardButton(text="Orqaga")]
        ],
        resize_keyboard=True
    )

def quran_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅"), KeyboardButton(text="❌")],
            [KeyboardButton(text="Orqaga")]
        ],
        resize_keyboard=True
    )

def zikr_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="300"), KeyboardButton(text="500"), KeyboardButton(text="1000")],
            [KeyboardButton(text="Orqaga")]
        ],
        resize_keyboard=True
    )

def report_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Kunlik hisobot")],
            [KeyboardButton(text="Haftalik hisobot")],
            [KeyboardButton(text="Oylik hisobot")],
            [KeyboardButton(text="Orqaga")]
        ],
        resize_keyboard=True
    )

def save_record(user_id, item_name, item_value, record_date):
    cursor.execute("""
    DELETE FROM records
    WHERE user_id = ? AND item_name = ? AND record_date = ?
    """, (user_id, item_name, record_date))

    cursor.execute("""
    INSERT INTO records (user_id, item_name, item_value, record_date)
    VALUES (?, ?, ?, ?)
    """, (user_id, item_name, item_value, record_date))

    conn.commit()

def get_day_report(user_id, record_date):
    cursor.execute("""
    SELECT item_name, item_value FROM records
    WHERE user_id = ? AND record_date = ?
    """, (user_id, record_date))
    rows = cursor.fetchall()

    data = {
        "Bomdod": "—",
        "Peshin": "—",
        "Asr": "—",
        "Shom": "—",
        "Xufton": "—",
        "Vitr": "—",
        "Tahajjud": "—",
        "Qur'on": "—",
        "Zikr": "—"
    }

    for name, value in rows:
        data[name] = value

    text = f"📅 Sana: {record_date}\n\n"
    text += "Bomdod: " + data["Bomdod"] + "\n"
    text += "Peshin: " + data["Peshin"] + "\n"
    text += "Asr: " + data["Asr"] + "\n"
    text += "Shom: " + data["Shom"] + "\n"
    text += "Xufton: " + data["Xufton"] + "\n"
    text += "Vitr: " + data["Vitr"] + "\n"
    text += "Tahajjud: " + data["Tahajjud"] + "\n"
    text += "Qur'on: " + data["Qur'on"] + "\n"
    text += "Zikr: " + data["Zikr"]

    return text

@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "Kerakli bo'limni tanlang:",
        reply_markup=main_keyboard()
    )

@dp.message(Command("today"))
async def today_handler(message: Message):
    await message.answer(
        "Hisobot turini tanlang:",
        reply_markup=report_keyboard()
    )

@dp.message(F.text == "Orqaga")
async def back_handler(message: Message):
    user_state.pop(message.from_user.id, None)
    await message.answer("Asosiy menyu:", reply_markup=main_keyboard())

@dp.message(F.text.in_(PRAYERS))
async def prayer_select_handler(message: Message):
    user_state[message.from_user.id] = message.text
    await message.answer(
        f"{message.text} uchun holatni tanlang:",
        reply_markup=prayer_keyboard()
    )

@dp.message(F.text.in_(["Ado qildim", "Qazo bo'ldi", "Jamoat bilan"]))
async def prayer_action_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_state:
        await message.answer("Avval namozni tanlang.", reply_markup=main_keyboard())
        return

    prayer_name = user_state[user_id]
    if prayer_name not in PRAYERS:
        await message.answer("Avval namozni tanlang.", reply_markup=main_keyboard())
        return

    save_record(user_id, prayer_name, message.text, today_str())
    user_state.pop(user_id, None)

    await message.answer(f"{prayer_name} saqlandi ✅", reply_markup=main_keyboard())

@dp.message(F.text == "Tahajjud")
async def tahajjud_handler(message: Message):
    save_record(message.from_user.id, "Tahajjud", "✅", today_str())
    await message.answer("Tahajjud saqlandi ✅", reply_markup=main_keyboard())

@dp.message(F.text == "Qur'on")
async def quran_handler(message: Message):
    user_state[message.from_user.id] = "Qur'on"
    await message.answer("Qur'on uchun holatni tanlang:", reply_markup=quran_keyboard())

@dp.message(F.text.in_(["✅", "❌"]))
async def quran_action_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_state or user_state[user_id] != "Qur'on":
        await message.answer("Avval Qur'on tugmasini bosing.", reply_markup=main_keyboard())
        return

    save_record(user_id, "Qur'on", message.text, today_str())
    user_state.pop(user_id, None)

    await message.answer("Qur'on saqlandi ✅", reply_markup=main_keyboard())

@dp.message(F.text == "Zikr")
async def zikr_handler(message: Message):
    user_state[message.from_user.id] = "Zikr"
    await message.answer("Zikr miqdorini tanlang:", reply_markup=zikr_keyboard())

@dp.message(F.text.in_(["300", "500", "1000"]))
async def zikr_action_handler(message: Message):
    user_id = message.from_user.id

    if user_id not in user_state or user_state[user_id] != "Zikr":
        await message.answer("Avval Zikr tugmasini bosing.", reply_markup=main_keyboard())
        return

    save_record(user_id, "Zikr", message.text, today_str())
    user_state.pop(user_id, None)

    await message.answer("Zikr saqlandi ✅", reply_markup=main_keyboard())

@dp.message(F.text == "Kunlik hisobot")
async def daily_report_handler(message: Message):
    text = get_day_report(message.from_user.id, today_str())
    await message.answer(text, reply_markup=report_keyboard())

@dp.message(F.text == "Haftalik hisobot")
async def weekly_report_handler(message: Message):
    today = datetime.now().date()
    start_day = today - timedelta(days=6)

    text = "📊 Haftalik hisobot\n\n"
    for i in range(7):
        current_day = start_day + timedelta(days=i)
        text += get_day_report(message.from_user.id, current_day.strftime("%Y-%m-%d"))
        text += "\n\n--------------------\n\n"

    for i in range(0, len(text), 3500):
        await message.answer(text[i:i+3500], reply_markup=report_keyboard())

@dp.message(F.text == "Oylik hisobot")
async def monthly_report_handler(message: Message):
    today = datetime.now().date()
    start_day = today - timedelta(days=29)

    text = "📊 Oylik hisobot\n\n"
    for i in range(30):
        current_day = start_day + timedelta(days=i)
        text += get_day_report(message.from_user.id, current_day.strftime("%Y-%m-%d"))
        text += "\n\n--------------------\n\n"

    for i in range(0, len(text), 3500):
        await message.answer(text[i:i+3500], reply_markup=report_keyboard())

@dp.message()
async def fallback_handler(message: Message):
    await message.answer(
        "Tugmalardan foydalaning.",
        reply_markup=main_keyboard()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
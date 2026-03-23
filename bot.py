import telebot
from telebot import types
import sqlite3
from datetime import datetime, date
import random

TOKEN = "8437626033:AAGeXXzGuN26DMMbD2QS0In5MZqCpD5tLjY"
bot = telebot.TeleBot(TOKEN)

# ================== БАЗА ДАННЫХ ==================
conn = sqlite3.connect("sobaken.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    tg_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    nickname TEXT,
    reg_date TEXT,
    facts_read INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS fact_day (
    day TEXT UNIQUE,
    fact TEXT
)
""")

conn.commit()

# ================== ФАКТЫ ==================
FACTS = {
    "light": [
        "Собаки могут узнавать хозяина по шагам.",
        "Собака понимает до 250 слов.",
        "Хвост — это язык эмоций собаки."
    ],
    "mind": [
        "Мозг не чувствует боли.",
        "Ты видишь прошлое — свету нужно время, чтобы дойти до глаз.",
        "Сознание может отключаться без сна."
    ],
    "weird": [
        "Бананы — это ягоды, а клубника — нет.",
        "У осьминога три сердца.",
        "В космосе нельзя плакать."
    ],
    "dogs": [
        "Отпечаток носа у собаки уникален.",
        "Собаки чувствуют болезни по запаху.",
        "Собаки видят сны."
    ],
    "brain_break": [
        "Ты никогда не видишь мир в реальном времени.",
        "Мысли появляются раньше, чем ты осознаёшь их.",
        "Мозг принимает решения за тебя."
    ]
}

# ================== ВСПОМОГАТЕЛЬНОЕ ==================
def is_registered(user_id):
    cursor.execute("SELECT nickname FROM users WHERE tg_id = ?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] is not None

def block_if_not_registered(message):
    if not is_registered(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🐶 Сначала регистрация 👇",
            reply_markup=register_keyboard()
        )
        return True
    return False

def increment_facts(user_id):
    cursor.execute(
        "UPDATE users SET facts_read = facts_read + 1 WHERE tg_id = ?",
        (user_id,)
    )
    conn.commit()

# ================== КЛАВИАТУРЫ ==================
def register_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📝 Регистрация")
    return kb

def main_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📌 Факт дня", "🔁 Случайный факт")
    kb.add("⚡ Быстрый факт", "🎭 Факт по настроению")
    kb.add("🤯 Сломай мозг")
    kb.add("👤 Профиль")
    return kb

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(message):
    cursor.execute(
        "INSERT OR IGNORE INTO users (tg_id, username, first_name, reg_date) VALUES (?, ?, ?, ?)",
        (
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    conn.commit()

    if not is_registered(message.from_user.id):
        bot.send_message(
            message.chat.id,
            "🐶 *Собакен бот*\n\n"
            "Факты. Мозг. Залипание.\n"
            "Сначала регистрация 👇",
            parse_mode="Markdown",
            reply_markup=register_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            "🐾 С возвращением!",
            reply_markup=main_keyboard()
        )

# ================== РЕГИСТРАЦИЯ ==================
@bot.message_handler(func=lambda m: m.text == "📝 Регистрация")
def register(message):
    if is_registered(message.from_user.id):
        bot.send_message(message.chat.id, "✅ Ты уже зарегистрирован", reply_markup=main_keyboard())
        return

    msg = bot.send_message(message.chat.id, "✍️ Введи ник (без пробелов):")
    bot.register_next_step_handler(msg, save_nick)

def save_nick(message):
    nick = message.text.strip()
    if " " in nick or len(nick) < 3:
        msg = bot.send_message(message.chat.id, "❌ Минимум 3 символа, без пробелов")
        bot.register_next_step_handler(msg, save_nick)
        return

    cursor.execute(
        "UPDATE users SET nickname = ? WHERE tg_id = ?",
        (nick, message.from_user.id)
    )
    conn.commit()

    bot.send_message(
        message.chat.id,
        f"🎉 Добро пожаловать, *{nick}* 🐶",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

# ================== ФАКТ ДНЯ ==================
@bot.message_handler(func=lambda m: m.text == "📌 Факт дня")
def fact_day(message):
    if block_if_not_registered(message): return

    today = date.today().isoformat()
    cursor.execute("SELECT fact FROM fact_day WHERE day = ?", (today,))
    row = cursor.fetchone()

    if row:
        fact = row[0]
    else:
        all_facts = sum(FACTS.values(), [])
        fact = random.choice(all_facts)
        cursor.execute("INSERT OR IGNORE INTO fact_day VALUES (?, ?)", (today, fact))
        conn.commit()

    increment_facts(message.from_user.id)
    bot.send_message(message.chat.id, f"📌 *Факт дня:*\n\n{fact}", parse_mode="Markdown")

# ================== СЛУЧАЙНЫЙ ФАКТ ==================
@bot.message_handler(func=lambda m: m.text == "🔁 Случайный факт")
def random_fact(message):
    if block_if_not_registered(message): return
    fact = random.choice(sum(FACTS.values(), []))
    increment_facts(message.from_user.id)
    bot.send_message(message.chat.id, f"🐾 {fact}")

# ================== БЫСТРЫЙ ФАКТ ==================
@bot.message_handler(func=lambda m: m.text == "⚡ Быстрый факт")
def fast_fact(message):
    if block_if_not_registered(message): return
    fact = random.choice(FACTS["light"])
    increment_facts(message.from_user.id)
    bot.send_message(message.chat.id, f"⚡ {fact}")

# ================== ФАКТ ПО НАСТРОЕНИЮ ==================
@bot.message_handler(func=lambda m: m.text == "🎭 Факт по настроению")
def mood(message):
    if block_if_not_registered(message): return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("😄 Лёгкий", "🤯 Мозговзрыв")
    kb.add("😳 Странный", "🐶 Про собак")
    kb.add("◀️ Назад")

    bot.send_message(message.chat.id, "Выбери настроение:", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text in ["😄 Лёгкий", "🤯 Мозговзрыв", "😳 Странный", "🐶 Про собак"])
def mood_fact(message):
    if block_if_not_registered(message): return

    mapping = {
        "😄 Лёгкий": "light",
        "🤯 Мозговзрыв": "mind",
        "😳 Странный": "weird",
        "🐶 Про собак": "dogs"
    }

    fact = random.choice(FACTS[mapping[message.text]])
    increment_facts(message.from_user.id)
    bot.send_message(message.chat.id, fact, reply_markup=main_keyboard())

# ================== СЛОМАЙ МОЗГ ==================
@bot.message_handler(func=lambda m: m.text == "🤯 Сломай мозг")
def brain_break(message):
    if block_if_not_registered(message): return
    fact = random.choice(FACTS["brain_break"])
    increment_facts(message.from_user.id)
    bot.send_message(message.chat.id, f"🤯 {fact}")

# ================== ПРОФИЛЬ ==================
@bot.message_handler(func=lambda m: m.text == "👤 Профиль")
def profile(message):
    if block_if_not_registered(message): return

    cursor.execute(
        "SELECT nickname, facts_read, reg_date FROM users WHERE tg_id = ?",
        (message.from_user.id,)
    )
    nick, facts, reg = cursor.fetchone()

    bot.send_message(
        message.chat.id,
        f"👤 *Профиль*\n\n"
        f"🐶 Ник: {nick}\n"
        f"📖 Фактов прочитано: {facts}\n"
        f"📅 Регистрация: {reg}",
        parse_mode="Markdown"
    )

# ================== НАЗАД ==================
@bot.message_handler(func=lambda m: m.text == "◀️ Назад")
def back(message):
    bot.send_message(message.chat.id, "🏠 Главное меню", reply_markup=main_keyboard())

# ================== ЗАПУСК ==================
print("🐶 Собакен бот запущен")
bot.infinity_polling()

import telebot
import sqlite3
from telebot import types
import time
import logging

# Настройка логирования
logging.basicConfig(filename='vpn_bot.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Токен бота от BotFather
TOKEN = '7558450757:AAGD8hw5Ohovquir5jmIaExYSfAG1M609CE'
bot = telebot.TeleBot(TOKEN)

# ID администратора (замените на свой Telegram ID)
ADMIN_ID = 7853333670

# Инициализация базы данных SQLite
def init_db():
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS vpns (vpn_id INTEGER PRIMARY KEY AUTOINCREMENT, vpn_link TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS channels (
                         channel_name TEXT PRIMARY KEY, 
                         channel_title TEXT)''')
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")

# Получение списка каналов из базы данных
def get_channels():
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("SELECT channel_name, channel_title FROM channels")
            channels = [(row[0], row[1]) for row in c.fetchall()]
        return channels
    except sqlite3.Error as e:
        logging.error(f"Error fetching channels: {e}")
        return []

# Проверка подписки на каналы
def check_subscription(user_id):
    channels = get_channels()
    if not channels:
        return True
    for channel_name, _ in channels:
        try:
            status = bot.get_chat_member(channel_name, user_id).status
            if status not in ['member', 'administrator', 'creator']:
                return False
        except telebot.apihelper.ApiTelegramException as e:
            logging.error(f"Error checking subscription for {channel_name}: {e}")
            return False
    return True

# Получение всех доступных VPN
def get_available_vpns():
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("SELECT vpn_link FROM vpns")
            vpns = [row[0] for row in c.fetchall()]
        return vpns
    except sqlite3.Error as e:
        logging.error(f"Error fetching VPNs: {e}")
        return []

# Главное меню пользователя
def main_menu(message):
    markup = types.InlineKeyboardMarkup()

    try:
        channels = get_channels()
        if channels:
            channel_text = "📢 *Kanallara ýazylyň:*\n"
            for channel_name, channel_title in channels:
                display_name = channel_title if channel_title else channel_name
                if channel_name and channel_name.startswith('@'):
                    markup.add(types.InlineKeyboardButton(f"{display_name}", url=f"https://t.me/{channel_name[1:]}"))
                else:
                    logging.error(f"Invalid channel name: {channel_name}")
        else:
            channel_text = "Häzirlikçe kanal ýok.\n"
    except Exception as e:
        logging.error(f"Error in main_menu: {e}")
        channel_text = "❌ Kanallary ýüklemekde ýalňyşlyk ýüze çykdy.\n"

    # Добавляем кнопки "VPN alyň" и "Admin Panel" внизу
    markup.add(types.InlineKeyboardButton("Agza boldum ✅", callback_data="get_vpn"))
    if message.chat.id == ADMIN_ID:
        markup.add(types.InlineKeyboardButton("Admin Panel", callback_data="admin_panel"))

    bot.send_message(message.chat.id, 
                     f"🌐 *Salam! VPN botymyza hoş geldiňiz!*\n"
                     f"VPN almak üçin kanallara agza boluň we, 'Agza boldum' düwmesini basyň.\n\n"
                     f"{channel_text}", 
                     parse_mode='Markdown', reply_markup=markup)

# Админ-панель
def admin_panel(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "Bu bölüm diňe adminler üçin!")
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("VPN goş", callback_data="add_vpn"))
    markup.add(types.InlineKeyboardButton("VPN aýyr", callback_data="remove_vpn"))
    markup.add(types.InlineKeyboardButton("Kanal goş", callback_data="add_channel"))
    markup.add(types.InlineKeyboardButton("Kanal aýyr", callback_data="remove_channel"))
    markup.add(types.InlineKeyboardButton("Statistika gör", callback_data="stats"))
    markup.add(types.InlineKeyboardButton("Habar ýollamak", callback_data="broadcast"))
    bot.send_message(message.chat.id, 
                     "⚙️ *Admin Panel*\n"
                     "Aşakdaky funksiýalary saýlaň:", 
                     parse_mode='Markdown', reply_markup=markup)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "NoUsername"
    join_date = time.strftime("%Y-%m-%d %H:%M:%S")

    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO users (user_id, username, join_date) VALUES (?, ?, ?)", 
                      (user_id, username, join_date))
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error adding user: {e}")

    main_menu(message)

# Обработка callback-запросов
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == "get_vpn":
        if check_subscription(user_id):
            vpns = get_available_vpns()
            if vpns:
                vpn_text = "\n".join(vpns)
                bot.send_message(call.message.chat.id, 
                                 f"✨ *Agza bolanyñyz üçin sagboluň!*\n"
                                 f"Siziň VPN:\n{vpn_text}", 
                                 parse_mode='Markdown')
            else:
                bot.send_message(call.message.chat.id, 
                                 "❌ VPN tapylmady, admin bilen habarlaşyň!", 
                                 parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, 
                             "⚠️ Kanallara ýazylmadyňyz!\n"
                             "Ýokardaky kanallara ýazylyp, täzeden 'VPN alyň' düwmesini basyň.", 
                             parse_mode='Markdown')

    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        admin_panel(call.message)

    elif call.data == "add_vpn" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "VPN baglanyşygyny ýazyň:")
        bot.register_next_step_handler(msg, process_add_vpn)

    elif call.data == "remove_vpn" and user_id == ADMIN_ID:
        try:
            with sqlite3.connect('vpn_bot7J.db') as conn:
                c = conn.cursor()
                c.execute("SELECT vpn_id, vpn_link FROM vpns")
                vpns = c.fetchall()
                if vpns:
                    markup = types.InlineKeyboardMarkup()
                    for vpn in vpns:
                        markup.add(types.InlineKeyboardButton(f"ID: {vpn[0]} - {vpn[1]}", callback_data=f"del_vpn_{vpn[0]}"))
                    bot.send_message(call.message.chat.id, "Aýyrmak üçin VPN saýlaň:", reply_markup=markup)
                else:
                    bot.send_message(call.message.chat.id, "VPN ýok!")
        except sqlite3.Error as e:
            bot.send_message(call.message.chat.id, f"❌ VPN aýyrmakda ýalňyşlyk: {e}")

    elif call.data.startswith("del_vpn_") and user_id == ADMIN_ID:
        vpn_id = call.data.split("_")[2]
        try:
            with sqlite3.connect('vpn_bot7J.db') as conn:
                c = conn.cursor()
                c.execute("DELETE FROM vpns WHERE vpn_id = ?", (vpn_id,))
                conn.commit()
            bot.send_message(call.message.chat.id, "✅ VPN aýyryldy!")
        except sqlite3.Error as e:
            bot.send_message(call.message.chat.id, f"❌ VPN aýyrmakda ýalňyşlyk: {e}")

    elif call.data == "add_channel" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "Kanalyň adyny ýazyň (meselem, @ChannelName):")
        bot.register_next_step_handler(msg, process_add_channel_step1)

    elif call.data == "remove_channel" and user_id == ADMIN_ID:
        channels = get_channels()
        if channels:
            markup = types.InlineKeyboardMarkup()
            for channel_name, channel_title in channels:
                display_name = channel_title if channel_title else channel_name
                markup.add(types.InlineKeyboardButton(f"{display_name} ({channel_name})", callback_data=f"del_channel_{channel_name}"))
            bot.send_message(call.message.chat.id, "Aýyrmak üçin kanal saýlaň:", reply_markup=markup)
        else:
            bot.send_message(call.message.chat.id, "Kanal ýok!")

    elif call.data.startswith("del_channel_") and user_id == ADMIN_ID:
        channel_name = call.data.split("_")[2]
        try:
            with sqlite3.connect('vpn_bot7J.db') as conn:
                c = conn.cursor()
                c.execute("DELETE FROM channels WHERE channel_name = ?", (channel_name,))
                conn.commit()
            bot.send_message(call.message.chat.id, "✅ Kanal aýyryldy!")
        except sqlite3.Error as e:
            bot.send_message(call.message.chat.id, f"❌ Kanal aýyrmakda ýalňyşlyk: {e}")

    elif call.data == "stats" and user_id == ADMIN_ID:
        try:
            with sqlite3.connect('vpn_bot7J.db') as conn:
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM users")
                user_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM vpns")
                vpn_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM channels")
                channel_count = c.fetchone()[0]
            bot.send_message(call.message.chat.id, 
                             f"📊 *Statistika*\n"
                             f"Ulanyjylar: {user_count}\n"
                             f"VPN-ler: {vpn_count}\n"
                             f"Kanallar: {channel_count}", 
                             parse_mode='Markdown')
        except sqlite3.Error as e:
            bot.send_message(call.message.chat.id, f"❌ Statistika ýüklenmede ýalňyşlyk: {e}")

    elif call.data == "broadcast" and user_id == ADMIN_ID:
        msg = bot.send_message(call.message.chat.id, "Ýollanyljak habary ýazyň:")
        bot.register_next_step_handler(msg, process_broadcast)

# Добавление VPN
def process_add_vpn(message):
    if message.chat.id != ADMIN_ID:
        return
    vpn_link = message.text
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO vpns (vpn_link) VALUES (?)", (vpn_link,))
            conn.commit()
        bot.send_message(message.chat.id, "✅ VPN goşuldy!")
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"❌ VPN goşmakda ýalňyşlyk: {e}")

# Добавление канала (шаг 1)
def process_add_channel_step1(message):
    if message.chat.id != ADMIN_ID:
        return
    channel_name = message.text
    if not channel_name.startswith('@'):
        bot.send_message(message.chat.id, "Kanalyň ady @ bilen başlamaly!")
        return
    try:
        chat = bot.get_chat(channel_name)
        member = bot.get_chat_member(channel_name, bot.get_me().id)
        if member.status not in ['administrator', 'creator']:
            bot.send_message(message.chat.id, "❌ Botuň bu kanalda adminlik hukugy ýok!")
            return
        msg = bot.send_message(message.chat.id, "Kanalyň başlygyny (atyny) ýazyň (meselem, 'Meniň Kanalym'): ")
        bot.register_next_step_handler(msg, process_add_channel_step2, channel_name)
    except telebot.apihelper.ApiTelegramException as e:
        bot.send_message(message.chat.id, f"❌ Kanalyň ady ýalňyş ýa-da botuň adminlik hukugy ýok! ({e})")

# Добавление канала (шаг 2)
def process_add_channel_step2(message, channel_name):
    if message.chat.id != ADMIN_ID:
        return
    channel_title = message.text
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO channels (channel_name, channel_title) VALUES (?, ?)", 
                      (channel_name, channel_title))
            conn.commit()
        bot.send_message(message.chat.id, "✅ Kanal goşuldy!")
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"❌ Kanal goşmakda ýalňyşlyk: {e}")

# Рассылка сообщений
def process_broadcast(message):
    if message.chat.id != ADMIN_ID:
        return
    text = message.text
    try:
        with sqlite3.connect('vpn_bot7J.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM users")
            users = c.fetchall()
        for user in users:
            try:
                bot.send_message(user[0], text, parse_mode='Markdown')
            except telebot.apihelper.ApiTelegramException as e:
                logging.error(f"Error sending broadcast to {user[0]}: {e}")
        bot.send_message(message.chat.id, "✅ Habar ýollandy!")
    except sqlite3.Error as e:
        bot.send_message(message.chat.id, f"❌ Habar ýollamakda ýalňyşlyk: {e}")

# Запуск бота
if __name__ == "__main__":
    init_db()
    logging.info("Bot started")
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Polling error: {e}")
            time.sleep(5)
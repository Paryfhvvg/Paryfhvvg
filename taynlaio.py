import telebot
import json
from telebot import types

# Токен вашего бота от BotFather
TOKEN = '7558450757:AAGD8hw5Ohovquir5jmIaExYSfAG1M609CE'
# ID администратора (замените на свой Telegram ID)
ADMIN_ID = 7853333670

# Инициализация бота
bot = telebot.TeleBot(TOKEN)

# Файлы для хранения данных
CHANNELS_FILE = '112channels.json'
VPN_KEYS_FILE = '112vpn_keys.json'
USERS_FILE = '112users.json'

# Загрузка данных
def load_data(filename, default):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return default

# Сохранение данных
def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Экранирование специальных символов для Markdown
def escape_markdown(text):
    special_chars = ['*', '_', '`', '[', ']', '(', ')', '~', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

# Преобразование ссылки в полный URL
def format_channel_url(link):
    if link.startswith('@'):
        return f"https://t.me/{link[1:]}"
    elif link.startswith('https://t.me/'):
        return link
    else:
        return f"https://t.me/{link}"

# Инициализация данных
channels = load_data(CHANNELS_FILE, [])
vpn_keys = load_data(VPN_KEYS_FILE, ["vpn_key1"])  # Список ключей, замените на свои
users = load_data(USERS_FILE, [])  # Список ID пользователей

# Добавление пользователя в список
def add_user(user_id):
    if user_id not in users:
        users.append(user_id)
        save_data(users, USERS_FILE)

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    add_user(message.from_user.id)
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        full_url = format_channel_url(channel['link'])
        display_name = escape_markdown(channel['name'])
        try:
            keyboard.add(types.InlineKeyboardButton(f" {display_name}", url=full_url))
        except telebot.apihelper.ApiTelegramException as e:
            bot.send_message(message.chat.id, f"❌ Ýalňyşlyk kanal goşulmady: {e.description}")
    keyboard.add(types.InlineKeyboardButton("🔍 Agza boldum", callback_data="check_subscription"))
    welcome_text = (
        "👋 *Salam!* VPN açar almak üçin aşakdaky kanallara agza boluň we agza boldum düwmä basyň:"
        f"{'Häzirlikçe kanallar ýok.' if not channels else ''}"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Проверка подписки и выдача ключа
@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_subscription(call):
    user_id = call.from_user.id
    all_subscribed = True

    for channel in channels:
        try:
            member = bot.get_chat_member(channel['id'], user_id)
            if member.status == 'left':
                all_subscribed = False
                break
        except Exception:
            all_subscribed = False
            break

    if all_subscribed and channels:
        if vpn_keys:
            key = vpn_keys[0]
            escaped_key = escape_markdown(key)
            bot.send_message(
                call.from_user.id,
                f"🎉 *Siziň VPN açaryňyz:* `{escaped_key}`\n✨ Agza bolunyňyz üçin sagboluň!",
                parse_mode="Markdown"
            )
        else:
            bot.send_message(call.from_user.id, "❌ Açarlar gutardy. Admin bilen habarlaşyň!")
    else:
        bot.send_message(
            call.from_user.id,
            "⚠️ Siz ähli kanallara Agza bolmadyňyz. Agza boluň we täzeden synanyşyň!"
        )
    bot.answer_callback_query(call.id, "Barlag tamamlandy")

# Команды админа
@bot.message_handler(commands=['admin'], func=lambda message: message.from_user.id == ADMIN_ID)
def admin_panel(message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("➕ Kanal goş", callback_data="add_channel"),
        types.InlineKeyboardButton("➖ Kanal aýyr", callback_data="remove_channel")
    )
    keyboard.add(
        types.InlineKeyboardButton("📋 Kanallaryň sanawy", callback_data="list_channels"),
        types.InlineKeyboardButton("📊 Statistikalar", callback_data="show_stats")
    )
    keyboard.add(
        types.InlineKeyboardButton("📩 Ýaýlym", callback_data="start_broadcast"),
        types.InlineKeyboardButton("🔐 VPN goş", callback_data="add_vpn")
    )
    keyboard.add(
        types.InlineKeyboardButton("🗑️ VPN aýyr", callback_data="remove_vpn")
    )
    bot.send_message(
        message.chat.id,
        "🔧 *Admin paneli:*",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

# Добавление канала
@bot.callback_query_handler(func=lambda call: call.data == "add_channel")
def add_channel_start(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    bot.send_message(
        call.from_user.id,
        "📩 Kanalyň ssylkasyny we adyny ýazyň (meselem: @mychannel Ady).\n"
        "Kanaly goşmak isleýärsiňizmi?:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.from_user.id, process_add_channel_inline)
    bot.answer_callback_query(call.id)

def process_add_channel_inline(message):
    try:
        # Разбиваем на ссылку и имя
        parts = message.text.split(" ", 1)
        if len(parts) < 2:
            raise ValueError("Kanalyň ssylkasyny we adyny ýazyň (meselem: @mychannel Ady)")
        
        link = parts[0].strip()  # Первая часть — ссылка
        name = parts[1].strip()  # Вторая часть — имя
        
        # Проверяем формат ссылки
        if link.startswith("https://t.me/"):
            chat_id = link.replace("https://t.me/", "@")
        elif link.startswith("@"):
            chat_id = link
        else:
            raise ValueError("Ssylka @ ýa-da https://t.me/ bilen başlamaly")
        
        # Проверяем существование канала
        chat = bot.get_chat(chat_id)
        
        # Экранируем текст для Markdown
        escaped_name = escape_markdown(name)
        escaped_link = escape_markdown(link)
        
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Howa", callback_data=f"confirm_add_channel_{chat.id}_{link}_{name}"),
            types.InlineKeyboardButton("❌ Ýatyr", callback_data="cancel_action")
        )
        
        # Отправляем сообщение с отладочной информацией
        bot.send_message(
            message.chat.id,
            f"Kanal: *{escaped_name}* ({escaped_link})\nGoşmak üçin howa düwmä basyň:\n"
            f"[Debug] Link: {link}, Name: {name}",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except ValueError as ve:
        bot.send_message(message.chat.id, f"❌ Ýalňyşlyk: {str(ve)}. Ssylkaň formatyny barlaň.")
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 400 and "chat not found" in e.description.lower():
            bot.send_message(
                message.chat.id,
                "❌ Ýalňyşlyk: Kanal tapylmady. Şuny barlaň:\n"
                "1. Ssylka dogry (@mychannel ýa-da https://t.me/mychannel).\n"
                "2. Bot kanala administrator hökmünde goşuldy."
            )
        else:
            bot.send_message(message.chat.id, f"❌ Telegram API ýalňyşlygy: {e.description}")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Näbelli ýalňyşlyk: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_add_channel_"))
def confirm_add_channel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    data = call.data.split("_")[3:]  # chat_id, link, name
    chat_id, link, name = data[0], data[1], " ".join(data[2:])
    channels.append({"id": int(chat_id), "link": link, "name": name})
    save_data(channels, CHANNELS_FILE)
    bot.send_message(call.from_user.id, f"✅ Kanal *{escape_markdown(name)}* üstünlikli goşuldy!", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# Удаление канала
@bot.callback_query_handler(func=lambda call: call.data == "remove_channel")
def remove_channel_start(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    if not channels:
        bot.send_message(call.from_user.id, "📭 Kanallaryň sanawy boş.")
        bot.answer_callback_query(call.id)
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for channel in channels:
        keyboard.add(types.InlineKeyboardButton(f" {channel['name']}", callback_data=f"del_channel_{channel['name']}"))
    bot.send_message(
        call.from_user.id,
        "🗑️ Aýyrmak üçin kanaly saýlaň:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_channel_"))
def process_remove_channel(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    channel_name = call.data.replace("del_channel_", "")
    global channels
    channels = [c for c in channels if c['name'] != channel_name]
    save_data(channels, CHANNELS_FILE)
    bot.send_message(call.from_user.id, f"✅ Kanal *{escape_markdown(channel_name)}* aýyryldy!", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# Список каналов
@bot.callback_query_handler(func=lambda call: call.data == "list_channels")
def list_channels(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    if channels:
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for channel in channels:
            full_url = format_channel_url(channel['link'])
            display_name = escape_markdown(channel['name'])
            try:
                keyboard.add(types.InlineKeyboardButton(f" {display_name}", url=full_url))
            except telebot.apihelper.ApiTelegramException as e:
                bot.send_message(call.from_user.id, f"❌ Ýalňyşlyk kanal görkezilmedi: {e.description}")
        bot.send_message(
            call.from_user.id,
            "📜 *Häzirki kanallar:*",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(call.from_user.id, "📭 Kanallaryň sanawy boş.")
    bot.answer_callback_query(call.id)

# Статистика бота
@bot.callback_query_handler(func=lambda call: call.data == "show_stats")
def show_stats(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    total_keys = len(vpn_keys)
    total_users = len(users)
    stats = (
        "📊 *Botuň statistikasy:*\n"
        f"🔑 Jemi VPN açarlary: {total_keys}\n"
        f"👥 Jemi ulanyjylar: {total_users}"
    )
    bot.send_message(call.from_user.id, stats, parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# Рассылка сообщений
@bot.callback_query_handler(func=lambda call: call.data == "start_broadcast")
def start_broadcast(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    bot.send_message(
        call.from_user.id,
        "📬 Ýaýlym üçin habary ýazyň we dogrulamak üçin düwmä basyň:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.from_user.id, process_broadcast_inline)
    bot.answer_callback_query(call.id)

def process_broadcast_inline(message):
    broadcast_text = message.text
    escaped_text = escape_markdown(broadcast_text)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Iber", callback_data=f"confirm_broadcast_{broadcast_text}"),
        types.InlineKeyboardButton("❌ Ýatyr", callback_data="cancel_action")
    )
    bot.send_message(
        message.chat.id,
        f"Ýaýlym habary: *{escaped_text}*\niberiljekmi?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_broadcast_"))
def confirm_broadcast(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    broadcast_text = "_".join(call.data.split("_")[2:])
    escaped_text = escape_markdown(broadcast_text)
    success_count = 0
    fail_count = 0
    
    for user_id in users:
        try:
            bot.send_message(user_id, f"📢 *Paradox Sponsor:*\n{escaped_text}", parse_mode="Markdown")
            success_count += 1
        except Exception:
            fail_count += 1
    
    bot.send_message(
        call.from_user.id,
        f"✅ Ýaýlym tamamlandy!\n"
        f"👥 Iberildi: {success_count}\n"
        f"❌ Iberilmedi: {fail_count}",
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

# Добавление VPN ключа
@bot.callback_query_handler(func=lambda call: call.data == "add_vpn")
def add_vpn_start(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    bot.send_message(
        call.from_user.id,
        "🔐 Täze VPN açar ýazyň we dogrulamak üçin düwmä basyň:",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler_by_chat_id(call.from_user.id, process_add_vpn_inline)
    bot.answer_callback_query(call.id)

def process_add_vpn_inline(message):
    key = message.text.strip()
    if key:
        escaped_key = escape_markdown(key)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Dogrula", callback_data=f"confirm_add_vpn_{key}"),
            types.InlineKeyboardButton("❌ Ýatyr", callback_data="cancel_action")
        )
        bot.send_message(
            message.chat.id,
            f"Täze VPN açar: *{escaped_key}*\nGoşmak üçin dogrulaň:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, "❌ Açar boş bolup bilmez!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_add_vpn_"))
def confirm_add_vpn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    key = call.data.replace("confirm_add_vpn_", "")
    if key not in vpn_keys:
        vpn_keys.append(key)
        save_data(vpn_keys, VPN_KEYS_FILE)
        bot.send_message(call.from_user.id, f"✅ VPN açar *{escape_markdown(key)}* goşuldy!", parse_mode="Markdown")
    else:
        bot.send_message(call.from_user.id, "❌ Bu açar eýýäm bar!")
    bot.answer_callback_query(call.id)

# Удаление VPN ключа
@bot.callback_query_handler(func=lambda call: call.data == "remove_vpn")
def remove_vpn_start(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    if not vpn_keys:
        bot.send_message(call.from_user.id, "🔐 VPN açarlaryň sanawy boş.")
        bot.answer_callback_query(call.id)
        return
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key in vpn_keys:
        keyboard.add(types.InlineKeyboardButton(f"🔑 {key}", callback_data=f"del_vpn_{key}"))
    bot.send_message(
        call.from_user.id,
        "🗑️ Aýyrmak üçin VPN açary saýlaň:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_vpn_"))
def process_remove_vpn(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "Size rugsat ýok!")
        return
    key = call.data.replace("del_vpn_", "")
    global vpn_keys
    vpn_keys = [k for k in vpn_keys if k != key]
    save_data(vpn_keys, VPN_KEYS_FILE)
    bot.send_message(call.from_user.id, f"✅ VPN açar *{escape_markdown(key)}* aýyryldy!", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# Отмена действия
@bot.callback_query_handler(func=lambda call: call.data == "cancel_action")
def cancel_action(call):
    bot.send_message(call.from_user.id, "❌ Amal ýatyryldy.", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
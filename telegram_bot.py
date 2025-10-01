import os
import telebot
import logging
import re
from telebot import types
from telebot.handler_backends import State, StatesGroup
from telebot.custom_filters import StateFilter
from dotenv import load_dotenv
from main import find_similar_issues, load_issues
from yandex_tracker import force_fetch_issues, get_cache_update_time, get_issues_count_from_cache

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TG_BOT_APIKEY = os.getenv('TG_BOT_APIKEY')

bot = telebot.TeleBot(TG_BOT_APIKEY)

def escape_markdown(text):
    """Экранирует специальные символы для MarkdownV2."""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

ALLOWED_USERS = {
    112444633: "Дмитрий",
    730289007: "Андрей",
    378606353: "Лилия"
}

def is_allowed(message):
    user_id = message.from_user.id
    if user_id in ALLOWED_USERS:
        return True
    logging.warning(f"Неавторизованный доступ от пользователя с ID: {user_id}")
    return False

class MyStates(StatesGroup):
    search = State()
    initial = State()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    user_name = ALLOWED_USERS.get(user_id, "Неизвестный")
    
    if not is_allowed(message):
        bot.send_message(message.chat.id, "Доступ запрещен.")
        return
    
    logging.info(f"Пользователь {user_name} ({user_id}) запустил бота.")
    welcome_msg = f"Привет, {user_name}!\nВыберите действие:"
    
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_search = types.KeyboardButton('Поиск дублей')
    btn_update = types.KeyboardButton('Обновить БД принудительно')
    markup.add(btn_search, btn_update)
    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.initial, message.chat.id)

@bot.message_handler(state=MyStates.initial, func=lambda message: is_allowed(message) and message.text == 'Поиск дублей')
def request_search_text(message):
    user_id = message.from_user.id
    user_name = ALLOWED_USERS.get(user_id, "Неизвестный")
    logging.info(f"Пользователь {user_name} ({user_id}) нажал 'Поиск дублей'.")
    bot.send_message(message.chat.id, "Отправьте заголовок и, по желанию, описание новой задачи для поиска.")
    bot.set_state(message.from_user.id, MyStates.search, message.chat.id)

@bot.message_handler(state=MyStates.initial, func=lambda message: is_allowed(message) and message.text == 'Обновить БД принудительно')
def force_update_db(message):
    user_id = message.from_user.id
    user_name = ALLOWED_USERS.get(user_id, "Неизвестный")
    logging.info(f"Пользователь {user_name} ({user_id}) нажал 'Обновить БД принудительно'.")
    bot.send_message(message.chat.id, "Начинаю принудительное обновление базы данных...")
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_search = types.KeyboardButton('Поиск дублей')
    btn_update = types.KeyboardButton('Обновить БД принудительно')
    markup.add(btn_search, btn_update)
    try:
        force_fetch_issues()
        bot.send_message(message.chat.id, "База данных успешно обновлена.", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка при обновлении: {e}", reply_markup=markup)

@bot.message_handler(state=MyStates.search, func=is_allowed)
def handle_search_text(message):
    user_id = message.from_user.id
    user_name = ALLOWED_USERS.get(user_id, "Неизвестный")
    logging.info(f"Пользователь {user_name} ({user_id}) отправил поисковый запрос: '{message.text}'")

    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['text'] = message.text
    
    text_parts = data['text'].split('\n', 1)
    summary = text_parts[0]
    description = text_parts[1] if len(text_parts) > 1 else ''
    
    bot.reply_to(message, "Загружаю задачи из Yandex Tracker...")
    issues = load_issues()
    bot.reply_to(message, "Ищу похожие задачи...")
    similar_issues = find_similar_issues(summary, description, issues)
    
    if not similar_issues.empty:
        response = "Найдены похожие задачи:\n\n"
        for index, row in similar_issues.iterrows():
            issue_key = row['key']
            issue_link = f"https://tracker.yandex.ru/{issue_key}"
            summary_escaped = escape_markdown(row['summary'])
            similarity_percent = f"{row['similarity']:.2%}"
            response += f"[{escape_markdown(issue_key)}]({issue_link}) \\- {summary_escaped} \\(Схожесть: {escape_markdown(similarity_percent)}\\)\n"
    else:
        response = "Похожих задач не найдено\\."
        
    bot.reply_to(message, response, parse_mode='MarkdownV2')
    update_time = get_cache_update_time()
    issues_count = get_issues_count_from_cache()
    update_time = escape_markdown(get_cache_update_time())
    issues_count = get_issues_count_from_cache()
    bot.send_message(message.chat.id,
                     f"Можете отправить следующий запрос для поиска или вернуться в главное меню, нажав /start\\.\n"
                     f"\\(БД актуальна на: {update_time}, Записей: {issues_count}\\)", parse_mode='MarkdownV2')
    bot.set_state(message.from_user.id, MyStates.search, message.chat.id)

@bot.message_handler(state="*", func=lambda message: is_allowed(message) and message.text not in ['Поиск дублей', 'Обновить БД принудительно'])
def handle_other_messages(message):
    bot.send_message(message.chat.id, "Пожалуйста, используйте кнопки для навигации.")

if __name__ == '__main__':
    bot.add_custom_filter(StateFilter(bot))
    bot.polling(none_stop=True)
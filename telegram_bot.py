import os
import telebot
from dotenv import load_dotenv
from main import find_similar_issues, load_issues

load_dotenv()

TG_BOT_APIKEY = os.getenv('TG_BOT_APIKEY')

bot = telebot.TeleBot(TG_BOT_APIKEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Отправь мне заголовок и, по желанию, описание новой задачи, чтобы я поискал дубликаты.")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text_parts = message.text.split('\n', 1)
    summary = text_parts[0]
    description = text_parts[1] if len(text_parts) > 1 else ''
    
    issues = load_issues()
    similar_issues = find_similar_issues(summary, description, issues)
    
    if similar_issues:
        response = "Найдены похожие задачи:\n\n"
        for issue in similar_issues:
            response += f"[{issue['key']}]({issue['link']}) - {issue['summary']}\n"
    else:
        response = "Похожих задач не найдено."
        
    bot.reply_to(message, response, parse_mode='Markdown')

if __name__ == '__main__':
    bot.polling(none_stop=True)
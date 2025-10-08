# yandex_tracker.py

import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
from dotenv import load_dotenv
from yandex_tracker_client import TrackerClient

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем токен и ID организации из переменных окружения
# В .env файле должны быть определены YANDEX_TRACKER_TOKEN и YA_TRACKER_ORG_ID
TOKEN = os.getenv("YANDEX_TRACKER_TOKEN")
ORG_ID = os.getenv("YA_TRACKER_ORG_ID")
# значение фильтра берется из env
FILTER_QUERY = os.getenv("FILTER_QUERY")

# Инициализация клиента Yandex Tracker
if not TOKEN or not ORG_ID:
    raise ValueError("Необходимо задать YANDEX_TRACKER_TOKEN и YA_TRACKER_ORG_ID в .env файле")

client = TrackerClient(token=TOKEN, org_id=ORG_ID)

def get_issues():
    """
    Выполняет запрос к API Yandex Tracker для получения задач.

    Фильтр запроса жестко задан для получения задач из определенных очередей
    и с определенными статусами.

    Returns:
        pd.DataFrame: DataFrame с задачами, содержащий поля 'key', 'summary' и 'description'.
    """

    
    # Выполняем запрос к API
    issues_from_tracker = client.issues.find(query=FILTER_QUERY)
    
    # Извлекаем только необходимые поля
    issues_data = []
    for issue in issues_from_tracker:
        issues_data.append({
            'key': issue.key,
            'summary': issue.summary,
            'description': issue.description or ''  # Присваиваем пустую строку, если описание отсутствует
        })
    
    logging.info(f"Загружено {len(issues_data)} задач из Yandex Tracker.")
    
    # Возвращаем данные в виде DataFrame
    return pd.DataFrame(issues_data)

def load_or_fetch_issues(cache_file='issues.json', cache_hours=1):
    """
    Загружает задачи из кэша или выполняет новый запрос, если кэш устарел.

    Args:
        cache_file (str): Путь к файлу кэша.
        cache_hours (int): Время жизни кэша в часах.

    Returns:
        pd.DataFrame: DataFrame с актуальными задачами.
    """
    # Проверяем, существует ли файл кэша и актуален ли он
    if os.path.exists(cache_file):
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        if datetime.now() - file_mod_time < timedelta(hours=cache_hours):
            logging.info(f"Загрузка задач из кэша '{cache_file}'.")
            return pd.read_json(cache_file)

    # Если кэш устарел или не существует, получаем свежие данные
    logging.info("Кэш не найден или устарел. Загрузка свежих задач...")
    issues_df = get_issues()
    
    # Сохраняем свежие данные в кэш
    issues_df.to_json(cache_file, orient='records', force_ascii=False, indent=4)
    logging.info(f"Задачи сохранены в кэш '{cache_file}'.")
    
    return issues_df

def force_fetch_issues(cache_file='issues.json'):
    """
    Принудительно загружает свежие задачи и обновляет кэш.
    """
    logging.info("Принудительная загрузка свежих задач...")
    issues_df = get_issues()
    issues_df.to_json(cache_file, orient='records', force_ascii=False, indent=4)
    logging.info(f"Кэш '{cache_file}' принудительно обновлен.")
    return issues_df

if __name__ == '__main__':
    # Пример использования:
    # При первом запуске данные будут загружены из API и сохранены в issues.json.
    # При последующих запусках в течение часа данные будут загружаться из файла.
    issues = load_or_fetch_issues()
    logging.info("\nПример полученных данных:")
    logging.info(issues.head())

def get_cache_update_time(cache_file='issues.json'):
    """
    Возвращает время последнего обновления кэша.
    """
    if os.path.exists(cache_file):
        mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        return mod_time.strftime('%Y-%m-%d %H:%M:%S')
    return "Кэш еще не создан."

def get_issues_count_from_cache(cache_file='issues.json'):
    """
    Возвращает количество задач в кэше.
    """
    if os.path.exists(cache_file):
        try:
            df = pd.read_json(cache_file)
            return len(df)
        except Exception:
            return 0
    return 0

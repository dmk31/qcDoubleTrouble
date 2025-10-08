import pandas as pd
import sys
import logging
from logger_config import setup_logger
from yandex_tracker import load_or_fetch_issues as load_issues
from similarity_checker import find_similar_issues as find_issues


def find_similar_issues(summary, description, issues):
    """
    Находит похожие задачи на основе предоставленных данных.

    Args:
        summary (str): Заголовок новой задачи.
        description (str): Описание новой задачи.
        issues (pd.DataFrame): DataFrame с существующими задачами.

    Returns:
        pd.DataFrame: DataFrame с похожими задачами.
    """
    return find_issues(summary, description, issues)


def interactive_main():
    """
    Основная функция для интерактивного поиска похожих задач в командной строке.
    """
    setup_logger()
    logging.info("Загрузка задач из Yandex.Tracker...")
    try:
        issues_df = load_issues()
        logging.info("Задачи успешно загружены.")
    except Exception as e:
        logging.error(f"Ошибка при загрузке задач: {e}")
        return

    while True:
        try:
            logging.info("\nВведите данные новой задачи для поиска похожих.")
            logging.info("Для выхода введите 'exit' или 'quit'.")

            title = input("Заголовок: ")
            if title.lower() in ['exit', 'quit']:
                break

            description = input("Описание (нажмите Enter, если нет): ")
            if description.lower() in ['exit', 'quit']:
                break

            similar_issues = find_similar_issues(title, description, issues_df)

            if similar_issues.empty:
                logging.info("\nПохожих задач не найдено.")
            else:
                logging.info("\nНайдены похожие задачи:")
                # Создаем DataFrame для красивого вывода
                results_df = pd.DataFrame(similar_issues)
                results_df['similarity'] = results_df['similarity'].map(lambda x: f"{x:.2%}")

                # Настройка вывода pandas
                pd.set_option('display.max_rows', None)
                pd.set_option('display.max_columns', None)
                pd.set_option('display.width', None)
                pd.set_option('display.max_colwidth', 50)

                # Переименовываем колонки для вывода
                results_df.rename(columns={
                    'key': 'Ключ',
                    'similarity': 'Схожесть',
                    'found_in': 'Найдено по',
                    'summary': 'Название'
                }, inplace=True)

                logging.info(results_df.to_string(index=False))

        except (ValueError, TypeError) as e:
            logging.error(f"Произошла ошибка: {e}")
            logging.info("Пожалуйста, попробуйте еще раз.")


if __name__ == "__main__":
    try:
        interactive_main()
    except KeyboardInterrupt:
        logging.info("\nПрограмма завершена пользователем.")
        sys.exit(0)

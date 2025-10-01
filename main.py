import pandas as pd
import sys
from yandex_tracker import load_or_fetch_issues
from similarity_checker import find_similar_issues


def main():
    """
    Основная функция для поиска похожих задач.
    """
    # Конфигурация для корректного чтения ввода в PowerShell
    if sys.platform == "win32":
        sys.stdin.reconfigure(encoding='utf-8')
        sys.stdout.reconfigure(encoding='utf-8')

    print("Загрузка задач из Yandex.Tracker...")
    try:
        issues_df = load_or_fetch_issues()
        print("Задачи успешно загружены.")
    except Exception as e:
        print(f"Ошибка при загрузке задач: {e}")
        return

    while True:
        try:
            print("\nВведите данные новой задачи для поиска похожих.")
            print("Для выхода введите 'exit' или 'quit'.")

            title = input("Заголовок: ")
            if title.lower() in ['exit', 'quit']:
                break

            description = input("Описание (нажмите Enter, если нет): ")
            if description.lower() in ['exit', 'quit']:
                break

            similar_issues = find_similar_issues(title, description, issues_df)

            if similar_issues.empty:
                print("\nПохожих задач не найдено.")
            else:
                print("\nНайдены похожие задачи:")
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

                print(results_df.to_string(index=False))

        except (ValueError, TypeError) as e:
            print(f"Произошла ошибка: {e}")
            print("Пожалуйста, попробуйте еще раз.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nПрограмма завершена пользователем.")
        sys.exit(0)

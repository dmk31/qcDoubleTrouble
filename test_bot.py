import unittest
from unittest.mock import patch, MagicMock
import pandas as pd

# Импортируем функции для тестирования
from main import find_similar_issues
from telegram_bot import handle_text

class TestBotLogic(unittest.TestCase):

    def test_find_similar_issues(self):
        """
        Тест для функции find_similar_issues.
        Проверяет, что функция правильно находит похожие задачи.
        """
        # 1. Создаем мок-данные для задач
        issues_data = {
            'key': ['TEST-1', 'TEST-2', 'TEST-3'],
            'summary': [
                'Ошибка при авторизации пользователя',
                'Не работает кнопка "Сохранить"',
                'Проблема с отображением профиля'
            ],
            'description': [
                'Пользователь не может войти в систему.',
                'Кнопка неактивна после заполнения формы.',
                'Аватар пользователя не загружается.'
            ],
            'link': [
                'http://test.com/TEST-1',
                'http://test.com/TEST-2',
                'http://test.com/TEST-3'
            ]
        }
        issues_df = pd.DataFrame(issues_data)

        # 2. Определяем входные данные для теста
        summary = 'Проблема с логином'
        description = 'Юзер не может зайти'

        # 3. Мокаем зависимую функцию find_issues, чтобы контролировать ее вывод
        with patch('main.find_issues') as mock_find_issues:
            # 4. Настраиваем мок-объект на возврат ожидаемого результата
            expected_result_data = {
                'key': ['TEST-1'],
                'summary': ['Ошибка при авторизации пользователя'],
                'link': ['http://test.com/TEST-1']
            }
            expected_df = pd.DataFrame(expected_result_data)
            # Конвертируем DataFrame в список словарей, как это делает реальная функция
            mock_find_issues.return_value = expected_df.to_dict('records')

            # 5. Вызываем тестируемую функцию
            result = find_similar_issues(summary, description, issues_df)

            # 6. Проверяем, что результат соответствует ожиданиям
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]['key'], 'TEST-1')
            self.assertEqual(result[0]['summary'], 'Ошибка при авторизации пользователя')
            mock_find_issues.assert_called_once_with(summary, description, issues_df)


    @patch('telegram_bot.bot') # Мокаем объект бота
    @patch('telegram_bot.load_issues') # Мокаем загрузку задач
    @patch('telegram_bot.find_similar_issues') # Мокаем поиск похожих задач
    def test_handle_text_with_similar_issues(self, mock_find_similar_issues, mock_load_issues, mock_bot):
        """
        Тест для обработчика сообщений handle_text, когда найдены похожие задачи.
        """
        # 1. Настраиваем моки
        # Мок для find_similar_issues
        mock_find_similar_issues.return_value = [
            {'key': 'SIMILAR-1', 'summary': 'Очень похожая задача', 'link': 'http://similar.com/1'}
        ]
        # Мок для load_issues
        mock_load_issues.return_value = pd.DataFrame() # Возвращаем пустой DataFrame, т.к. find_similar_issues уже замокана

        # 2. Создаем мок-сообщение от пользователя
        mock_message = MagicMock()
        mock_message.text = 'Новая задача\nОписание новой задачи'

        # 3. Вызываем обработчик
        handle_text(mock_message)

        # 4. Проверяем, что бот отправил правильный ответ
        expected_response = (
            "Найдены похожие задачи:\n\n"
            "[SIMILAR-1](http://similar.com/1) - Очень похожая задача\n"
        )
        mock_bot.reply_to.assert_called_once_with(mock_message, expected_response, parse_mode='Markdown')


    @patch('telegram_bot.bot')
    @patch('telegram_bot.load_issues')
    @patch('telegram_bot.find_similar_issues')
    def test_handle_text_no_similar_issues(self, mock_find_similar_issues, mock_load_issues, mock_bot):
        """
        Тест для обработчика сообщений handle_text, когда похожих задач не найдено.
        """
        # 1. Настраиваем моки
        mock_find_similar_issues.return_value = [] # Возвращаем пустой список
        mock_load_issues.return_value = pd.DataFrame()

        # 2. Создаем мок-сообщение
        mock_message = MagicMock()
        mock_message.text = 'Уникальная задача\nНи на что не похожа'

        # 3. Вызываем обработчик
        handle_text(mock_message)

        # 4. Проверяем, что бот отправил правильный ответ
        expected_response = "Похожих задач не найдено."
        mock_bot.reply_to.assert_called_once_with(mock_message, expected_response, parse_mode='Markdown')


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
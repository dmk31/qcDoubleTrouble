import logging
import sys

def setup_logger():
    """
    Настраивает логгер для вывода в консоль и в файл.
    """
    # Создаем логгер
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Удаляем существующие обработчики, чтобы избежать дублирования
    if logger.hasHandlers():
        logger.handlers.clear()

    # Форматтер для логов
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Обработчик для записи в файл
    file_handler = logging.FileHandler('app.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Обработчик для вывода в консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # Перенаправляем stdout и stderr в логгер
    sys.stdout = StreamToLogger(logger, logging.INFO)
    sys.stderr = StreamToLogger(logger, logging.ERROR)

class StreamToLogger:
    """
    Класс для перенаправления потоков вывода (stdout, stderr) в логгер.
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass

"""
Модуль для настройки логгирования
"""
import logging
import os


def setup_logger():
    """Настраивает и возвращает логгер"""
    # Создаем директорию для логов если ее нет
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Настройка формата логов
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Создаем логгер
    logger = logging.getLogger('price_monitor')
    logger.setLevel(logging.INFO)

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Обработчик для файла
    file_handler = logging.FileHandler(
        'logs/price_monitor.log',
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)

    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', date_format)
    console_handler.setFormatter(console_formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Основной файл запуска мониторинга цен Ozon с настройкой headless режима
"""
import time
import threading
import json
import os
from datetime import datetime
from colorama import init, Fore, Style

from config_manager import ConfigManager
from url_manager import URLManager
from price_monitor import PriceMonitor
from console_interface import ConsoleInterface
from database import DatabaseManager
from logger import setup_logger

# Инициализация colorama
init(autoreset=True)


def load_database_config():
    """Загружает конфигурацию базы данных"""
    config_file = 'database_config.json'

    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except:
            pass

    # Конфигурация по умолчанию
    default_config = {
        "database": {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "price_monitor"
        },
        "monitoring": {
            "save_to_database": True,
            "save_html_pages": False,
            "cleanup_days": 30
        }
    }

    # Сохраняем конфигурацию по умолчанию
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
    except:
        pass

    return default_config


def main():
    """Основная функция запуска программы"""
    try:
        # Настройка логгера
        logger = setup_logger()

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print(f"{'МОНИТОРИНГ ЦЕН OZON':^80}")
        print(f"{'=' * 80}{Style.RESET_ALL}")

        # Инициализация менеджеров
        config_manager = ConfigManager()
        url_manager = URLManager()

        # Показываем текущие настройки headless режима
        headless_enabled = config_manager.is_headless_enabled()
        headless_status = f"{Fore.GREEN}ВКЛЮЧЕН" if headless_enabled else f"{Fore.YELLOW}ОТКЛЮЧЕН"
        print(f"{Fore.WHITE}Headless режим: {headless_status}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}(Изменить в config.json: 'browser_headless': true/false){Style.RESET_ALL}")

        # Загружаем конфигурацию базы данных
        db_config_data = load_database_config()
        db_config = db_config_data.get('database', {})
        monitoring_config = db_config_data.get('monitoring', {})

        # Инициализация базы данных
        db_manager = None
        use_database = monitoring_config.get('save_to_database', False)

        if use_database:
            print(f"{Fore.CYAN}Попытка подключения к базе данных MySQL...{Style.RESET_ALL}")

            db_manager = DatabaseManager(
                host=db_config.get('host', 'localhost'),
                user=db_config.get('user', 'root'),
                password=db_config.get('password', ''),
                database=db_config.get('database', 'price_monitor')
            )

            if db_manager.connect():
                print(f"{Fore.GREEN}✓ База данных подключена успешно{Style.RESET_ALL}")
                print(f"  Хост: {db_config.get('host')}")
                print(f"  База данных: {db_config.get('database')}")
            else:
                print(f"{Fore.YELLOW}⚠ Не удалось подключиться к базе данных{Style.RESET_ALL}")
                print(f"{Fore.CYAN}  Данные будут сохраняться только в файлы JSON/CSV{Style.RESET_ALL}")
                db_manager = None
                use_database = False
        else:
            print(f"{Fore.YELLOW}⚠ База данных отключена в настройках{Style.RESET_ALL}")
            print(f"{Fore.CYAN}  Данные будут сохраняться в файлы JSON/CSV{Style.RESET_ALL}")

        # Создание монитора цен
        price_monitor = PriceMonitor(config_manager, url_manager, logger, db_manager)

        # Создание консольного интерфейса
        console = ConsoleInterface(config_manager, url_manager, price_monitor, db_manager)

        print(f"\n{Fore.GREEN}{'=' * 80}")
        print(f"🚀 ЗАПУСК МОНИТОРИНГА ЦЕН")
        print(f"Headless режим: {'ДА' if headless_enabled else 'НЕТ'}")
        print(f"База данных: {'ПОДКЛЮЧЕНА' if use_database else 'НЕ ИСПОЛЬЗУЕТСЯ'}")
        print(f"Товаров для отслеживания: {url_manager.get_page_count()}")
        print(f"Интервал проверки: {config_manager.get_monitoring_interval()} мин.")
        print(f"Начало: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        # Преимущества headless режима
        if headless_enabled:
            print(f"{Fore.GREEN}🎯 Преимущества headless режима:")
            print(f"  • Работает в фоне без открытия окон")
            print(f"  • Экономит ресурсы системы")
            print(f"  • Быстрее запускается и работает")
            print(f"  • Можно запускать на сервере без GUI{Style.RESET_ALL}\n")
        else:
            print(f"{Fore.YELLOW}⚠ GUI режим:")
            print(f"  • Будут открываться окна браузера")
            print(f"  • Полезно для отладки")
            print(f"  • Для продакшена используйте headless режим{Style.RESET_ALL}\n")

        # Выводим справку
        print(f"{Fore.CYAN}💡 Справка:")
        print(f"  • Для управления используйте меню")
        print(f"  • Добавьте товары через пункт 2")
        print(f"  • Запустите проверку через пункт 5")
        print(f"  • Настройки: пункт 10 в меню")
        print(f"  • База данных: пункт 11 в меню")
        print(f"  • Выход: пункт 0{Style.RESET_ALL}\n")

        # Запуск мониторинга в отдельном потоке
        monitor_thread = threading.Thread(
            target=price_monitor.start_monitoring,
            daemon=True,
            name="MonitorThread"
        )
        monitor_thread.start()

        # Даем время для первой проверки
        time.sleep(3)

        # Запуск консольного интерфейса
        console.run()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Мониторинг остановлен пользователем{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Критическая ошибка: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()

        input(f"\n{Fore.YELLOW}Нажмите Enter для выхода...{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
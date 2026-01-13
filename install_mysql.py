#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для установки и настройки MySQL
"""
import subprocess
import sys
import os
from colorama import init, Fore, Style

init(autoreset=True)


def install_mysql_connector():
    """Устанавливает MySQL Connector для Python"""
    print(f"\n{Fore.CYAN}Установка MySQL Connector для Python...{Style.RESET_ALL}")

    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python==8.2.0"])
        print(f"{Fore.GREEN}✓ MySQL Connector установлен{Style.RESET_ALL}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}✗ Ошибка установки MySQL Connector: {e}{Style.RESET_ALL}")
        return False


def check_mysql_installation():
    """Проверяет установку MySQL"""
    print(f"\n{Fore.CYAN}Проверка установки MySQL...{Style.RESET_ALL}")

    # Проверяем наличие MySQL в PATH
    try:
        result = subprocess.run(['mysql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"{Fore.GREEN}✓ MySQL установлен: {result.stdout.strip()}{Style.RESET_ALL}")
            return True
    except FileNotFoundError:
        pass

    print(f"{Fore.YELLOW}MySQL не найден в системе{Style.RESET_ALL}")
    return False


def setup_mysql_database():
    """Настраивает базу данных для мониторинга"""
    print(f"\n{Fore.CYAN}Настройка базы данных...{Style.RESET_ALL}")

    try:
        import mysql.connector
        from mysql.connector import Error

        # Параметры подключения
        config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'price_monitor'
        }

        # Пытаемся подключиться
        try:
            connection = mysql.connector.connect(**config)
            if connection.is_connected():
                print(f"{Fore.GREEN}✓ База данных уже существует и доступна{Style.RESET_ALL}")
                connection.close()
                return True

        except Error as e:
            if "Unknown database" in str(e):
                print(f"{Fore.YELLOW}База данных не существует, создаем...{Style.RESET_ALL}")

                # Подключаемся без указания базы данных
                config_no_db = config.copy()
                config_no_db.pop('database', None)

                try:
                    connection = mysql.connector.connect(**config_no_db)
                    cursor = connection.cursor()

                    # Создаем базу данных
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']}")
                    print(f"{Fore.GREEN}✓ База данных создана: {config['database']}{Style.RESET_ALL}")

                    cursor.close()
                    connection.close()
                    return True

                except Error as e:
                    print(f"{Fore.RED}✗ Ошибка создания базы данных: {e}{Style.RESET_ALL}")
                    return False
            else:
                print(f"{Fore.RED}✗ Ошибка подключения к MySQL: {e}{Style.RESET_ALL}")
                return False

    except ImportError:
        print(f"{Fore.RED}✗ MySQL Connector не установлен{Style.RESET_ALL}")
        return False


def create_sample_config():
    """Создает пример конфигурационного файла для базы данных"""
    print(f"\n{Fore.CYAN}Создание конфигурационного файла...{Style.RESET_ALL}")

    config_content = '''{
    "database": {
        "host": "localhost",
        "user": "root",
        "password": "",
        "database": "price_monitor"
    },
    "monitoring": {
        "interval_minutes": 5,
        "save_to_database": true,
        "save_html_pages": true,
        "cleanup_days": 30
    }
}
'''

    try:
        with open('database_config.json', 'w', encoding='utf-8') as f:
            f.write(config_content)

        print(f"{Fore.GREEN}✓ Конфигурационный файл создан: database_config.json{Style.RESET_ALL}")
        return True
    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка создания конфигурационного файла: {e}{Style.RESET_ALL}")
        return False


def main():
    """Основная функция установки"""
    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{'УСТАНОВКА И НАСТРОЙКА MYSQL':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    # Шаг 1: Установка MySQL Connector
    if not install_mysql_connector():
        return

    # Шаг 2: Проверка установки MySQL
    mysql_installed = check_mysql_installation()

    if not mysql_installed:
        print(f"\n{Fore.YELLOW}Для работы с MySQL требуется:")
        print(f"1. Установить MySQL Server")
        print(f"2. Добавить MySQL в PATH")
        print(f"3. Создать пользователя root без пароля (для тестов)")
        print(f"\nСсылки для скачивания:")
        print(f"- MySQL Installer: https://dev.mysql.com/downloads/installer/")
        print(f"- XAMPP (включает MySQL): https://www.apachefriends.org/{Style.RESET_ALL}")

        continue_anyway = input(f"\n{Fore.YELLOW}Продолжить без MySQL? (y/n): {Style.RESET_ALL}")
        if continue_anyway.lower() != 'y':
            return

    # Шаг 3: Настройка базы данных
    if mysql_installed:
        if not setup_mysql_database():
            print(f"{Fore.YELLOW}Продолжаем без базы данных...{Style.RESET_ALL}")

    # Шаг 4: Создание конфигурации
    create_sample_config()

    print(f"\n{Fore.GREEN}{'=' * 60}")
    print(f"{'УСТАНОВКА ЗАВЕРШЕНА':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}Следующие шаги:")
    print(f"1. Запустите программу: python main.py")
    print(f"2. В главном меню выберите пункт 11 для управления базой данных")
    print(f"3. Настройте параметры подключения в database_config.json{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
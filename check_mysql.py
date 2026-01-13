#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки и настройки MySQL
"""
import mysql.connector
from mysql.connector import Error
import os
from colorama import init, Fore, Style

init(autoreset=True)


def check_mysql_connection():
    """Проверяет подключение к MySQL"""
    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{'ПРОВЕРКА ПОДКЛЮЧЕНИЯ К MYSQL':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    # Варианты конфигурации для теста
    test_configs = [
        {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'price_monitor'
        },
        {
            'host': 'localhost',
            'user': 'root',
            'password': 'password',
            'database': 'price_monitor'
        },
        {
            'host': '127.0.0.1',
            'user': 'root',
            'password': '',
            'database': 'price_monitor'
        },
        {
            'host': 'localhost',
            'user': 'root',
            'password': 'root',
            'database': 'price_monitor'
        }
    ]

    for i, config in enumerate(test_configs, 1):
        print(f"\n{Fore.YELLOW}Попытка #{i}:")
        print(f"  Хост: {config['host']}")
        print(f"  Пользователь: {config['user']}")
        print(f"  Пароль: {'****' if config['password'] else '(пустой)'}")
        print(f"  База данных: {config['database']}{Style.RESET_ALL}")

        try:
            # Пытаемся подключиться
            connection = mysql.connector.connect(
                host=config['host'],
                user=config['user'],
                password=config['password']
            )

            if connection.is_connected():
                print(f"{Fore.GREEN}✓ Успешное подключение к MySQL серверу!{Style.RESET_ALL}")

                cursor = connection.cursor()

                # Проверяем существование базы данных
                cursor.execute(f"SHOW DATABASES LIKE '{config['database']}'")
                result = cursor.fetchone()

                if result:
                    print(f"{Fore.GREEN}✓ База данных '{config['database']}' существует{Style.RESET_ALL}")

                    # Подключаемся к конкретной базе данных
                    connection.database = config['database']

                    # Проверяем таблицы
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()

                    if tables:
                        print(f"{Fore.GREEN}✓ В базе данных найдены таблицы: {len(tables)} шт.{Style.RESET_ALL}")
                        for table in tables:
                            print(f"  - {table[0]}")
                    else:
                        print(f"{Fore.YELLOW}⚠ В базе данных нет таблиц{Style.RESET_ALL}")

                else:
                    print(f"{Fore.YELLOW}База данных '{config['database']}' не существует{Style.RESET_ALL}")

                    # Предлагаем создать базу данных
                    create = input(f"{Fore.CYAN}Создать базу данных '{config['database']}'? (y/n): {Style.RESET_ALL}")
                    if create.lower() == 'y':
                        cursor.execute(
                            f"CREATE DATABASE {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                        print(f"{Fore.GREEN}✓ База данных создана{Style.RESET_ALL}")

                        # Создаем таблицы
                        create_tables(cursor, config['database'])

                cursor.close()
                connection.close()

                # Сохраняем рабочую конфигурацию
                save_config(config)
                return config

        except Error as e:
            print(f"{Fore.RED}✗ Ошибка подключения: {e}{Style.RESET_ALL}")

    print(f"\n{Fore.RED}{'=' * 60}")
    print(f"{'НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ К MYSQL':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}Возможные причины:")
    print("1. MySQL сервер не запущен")
    print("2. Неправильные учетные данные")
    print("3. Порт MySQL заблокирован")
    print(f"\n{Fore.CYAN}Рекомендуемые действия:")
    print("1. Запустите MySQL сервер")
    print("2. Установите XAMPP или WAMP (включают MySQL)")
    print("3. Проверьте логин и пароль")
    print(f"\n{Fore.GREEN}Альтернатива:")
    print("Программа будет работать без базы данных")
    print("Данные будут сохраняться только в файлы JSON/CSV{Style.RESET_ALL}")

    return None


def create_tables(cursor, database_name):
    """Создает таблицы в базе данных"""
    print(f"\n{Fore.CYAN}Создание таблиц...{Style.RESET_ALL}")

    # Используем базу данных
    cursor.execute(f"USE {database_name}")

    # SQL для создания таблиц
    tables_sql = [
        # Таблица товаров
        """
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(50) UNIQUE NOT NULL,
            url VARCHAR(500) NOT NULL,
            name VARCHAR(255),
            category VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_product_id (product_id),
            INDEX idx_url (url(100))
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # Таблица истории цен
        """
        CREATE TABLE IF NOT EXISTS price_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(50) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            price_formatted VARCHAR(50),
            currency VARCHAR(10) DEFAULT 'RUB',
            source VARCHAR(100),
            cycle INT DEFAULT 0,
            timestamp DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_product_id (product_id),
            INDEX idx_timestamp (timestamp),
            INDEX idx_cycle (cycle),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # Таблица изменений цен
        """
        CREATE TABLE IF NOT EXISTS price_changes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(50) NOT NULL,
            current_price DECIMAL(10, 2),
            previous_price DECIMAL(10, 2),
            change_amount DECIMAL(10, 2),
            change_percentage DECIMAL(5, 2),
            change_status ENUM('increased', 'decreased', 'no_change', 'new', 'error') DEFAULT 'no_change',
            significance VARCHAR(50),
            cycle INT DEFAULT 0,
            timestamp DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_product_id (product_id),
            INDEX idx_status (change_status),
            INDEX idx_timestamp (timestamp),
            INDEX idx_cycle (cycle),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # Таблица статистики мониторинга
        """
        CREATE TABLE IF NOT EXISTS monitoring_stats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            cycle INT NOT NULL,
            total_products INT DEFAULT 0,
            successful_parses INT DEFAULT 0,
            failed_parses INT DEFAULT 0,
            price_changes INT DEFAULT 0,
            increased INT DEFAULT 0,
            decreased INT DEFAULT 0,
            new_products INT DEFAULT 0,
            timestamp DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_cycle (cycle),
            INDEX idx_cycle (cycle),
            INDEX idx_timestamp (timestamp)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,

        # Таблица HTML страниц (опционально)
        """
        CREATE TABLE IF NOT EXISTS html_pages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id VARCHAR(50) NOT NULL,
            filename VARCHAR(255),
            html_content LONGTEXT,
            content_length INT,
            status_code INT,
            cycle INT DEFAULT 0,
            timestamp DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_product_id (product_id),
            INDEX idx_cycle (cycle),
            INDEX idx_timestamp (timestamp),
            FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    ]

    for i, sql in enumerate(tables_sql, 1):
        try:
            cursor.execute(sql)
            print(f"{Fore.GREEN}✓ Таблица #{i} создана{Style.RESET_ALL}")
        except Error as e:
            print(f"{Fore.RED}✗ Ошибка создания таблицы #{i}: {e}{Style.RESET_ALL}")

    print(f"{Fore.GREEN}✓ Все таблицы успешно созданы!{Style.RESET_ALL}")


def save_config(config):
    """Сохраняет конфигурацию в файл"""
    config_data = {
        "database": config,
        "monitoring": {
            "save_to_database": True,
            "save_html_pages": False,
            "cleanup_days": 30,
            "optimize_tables": True
        }
    }

    try:
        with open('database_config.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        print(f"{Fore.GREEN}✓ Конфигурация сохранена в database_config.json{Style.RESET_ALL}")
        print(f"\n{Fore.CYAN}Конфигурация подключения:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        print(f"{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка сохранения конфигурации: {e}{Style.RESET_ALL}")


def setup_without_database():
    """Настраивает работу без базы данных"""
    print(f"\n{Fore.CYAN}Настройка работы без базы данных...{Style.RESET_ALL}")

    config_data = {
        "database": {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "price_monitor"
        },
        "monitoring": {
            "save_to_database": False,  # Ключевой параметр!
            "save_html_pages": False,
            "cleanup_days": 30,
            "optimize_tables": False
        }
    }

    try:
        with open('database_config.json', 'w', encoding='utf-8') as f:
            import json
            json.dump(config_data, f, ensure_ascii=False, indent=2)

        print(f"{Fore.GREEN}✓ Конфигурация сохранена (без базы данных){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}⚠ Программа будет работать только с файлами JSON/CSV{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка сохранения конфигурации: {e}{Style.RESET_ALL}")


def main():
    """Основная функция"""
    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{'МАСТЕР НАСТРОЙКИ MYSQL':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    print(f"\n{Fore.YELLOW}Этот мастер поможет настроить подключение к MySQL")
    print(f"или настроить работу без базы данных.{Style.RESET_ALL}")

    choice = input(f"\n{Fore.CYAN}Выберите действие:\n"
                   f"1. Автоматическая настройка MySQL\n"
                   f"2. Работать без базы данных (только файлы)\n"
                   f"3. Выход\n"
                   f"Ваш выбор (1-3): {Style.RESET_ALL}")

    if choice == '1':
        config = check_mysql_connection()
        if not config:
            # Если не удалось подключиться, предлагаем работать без БД
            choice2 = input(
                f"\n{Fore.YELLOW}Не удалось подключиться к MySQL. Работать без базы данных? (y/n): {Style.RESET_ALL}")
            if choice2.lower() == 'y':
                setup_without_database()
    elif choice == '2':
        setup_without_database()
    elif choice == '3':
        print(f"{Fore.YELLOW}Выход...{Style.RESET_ALL}")
        return

    print(f"\n{Fore.GREEN}{'=' * 60}")
    print(f"{'НАСТРОЙКА ЗАВЕРШЕНА':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}Следующие шаги:")
    print(f"1. Запустите программу: python main.py")
    print(f"2. В главном меню выберите пункт 11 для управления базой данных")
    print(f"3. Если база данных не подключена, данные будут сохраняться в файлы{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
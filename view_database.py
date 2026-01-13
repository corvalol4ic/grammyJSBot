#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для просмотра содержимого базы данных
"""
import mysql.connector
from mysql.connector import Error
from colorama import init, Fore, Style

init(autoreset=True)


def view_database():
    """Показывает содержимое базы данных"""
    print(f"{Fore.CYAN}{'=' * 80}")
    print(f"{'ПРОСМОТР БАЗЫ ДАННЫХ PRICE_MONITOR':^80}")
    print(f"{'=' * 80}{Style.RESET_ALL}")

    try:
        # Подключаемся к базе данных
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',  # ваш пароль, если есть
            database='price_monitor'
        )

        if connection.is_connected():
            cursor = connection.cursor(dictionary=True)
            print(f"{Fore.GREEN}✓ Успешное подключение к базе данных{Style.RESET_ALL}")

            # Получаем список таблиц
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            print(f"\n{Fore.YELLOW}📊 ТАБЛИЦЫ В БАЗЕ ДАННЫХ:{Style.RESET_ALL}")
            for table in tables:
                table_name = list(table.values())[0]
                print(f"  • {table_name}")

            # Просматриваем каждую таблицу
            for table in tables:
                table_name = list(table.values())[0]

                print(f"\n{Fore.CYAN}{'=' * 60}")
                print(f"ТАБЛИЦА: {table_name}")
                print(f"{'=' * 60}{Style.RESET_ALL}")

                # Получаем количество записей
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count = cursor.fetchone()['count']
                print(f"{Fore.WHITE}Записей: {Fore.GREEN}{count}{Style.RESET_ALL}")

                # Получаем структуру таблицы
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()

                print(f"\n{Fore.YELLOW}Структура:{Style.RESET_ALL}")
                for col in columns:
                    print(f"  {col['Field']}: {col['Type']} ({col['Null']})")

                # Показываем первые 5 записей
                if count > 0:
                    print(f"\n{Fore.YELLOW}Первые 5 записей:{Style.RESET_ALL}")
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                    rows = cursor.fetchall()

                    for i, row in enumerate(rows, 1):
                        print(f"\n{Fore.CYAN}Запись #{i}:{Style.RESET_ALL}")
                        for key, value in row.items():
                            if value:
                                print(f"  {key}: {Fore.GREEN}{value}{Style.RESET_ALL}")
                            else:
                                print(f"  {key}: {Fore.YELLOW}(пусто){Style.RESET_ALL}")

            # Статистика по всей базе
            print(f"\n{Fore.CYAN}{'=' * 80}")
            print(f"{'СТАТИСТИКА БАЗЫ ДАННЫХ':^80}")
            print(f"{'=' * 80}{Style.RESET_ALL}")

            stats_queries = [
                ("Всего товаров", "SELECT COUNT(*) as count FROM products"),
                ("Всего цен в истории", "SELECT COUNT(*) as count FROM price_history"),
                ("Изменений цен", "SELECT COUNT(*) as count FROM price_changes"),
                ("Уникальных дней с данными", "SELECT COUNT(DISTINCT DATE(timestamp)) as days FROM price_history"),
                ("Последняя проверка", "SELECT MAX(timestamp) as last_check FROM price_history"),
                ("Среднее количество цен на товар",
                 "SELECT AVG(cnt) as avg FROM (SELECT COUNT(*) as cnt FROM price_history GROUP BY product_id) as sub"),
            ]

            for label, query in stats_queries:
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    print(
                        f"{Fore.WHITE}{label}:{Fore.GREEN} {result['count'] if 'count' in result else result.get('last_check', 'N/A')}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.WHITE}{label}:{Fore.RED} N/A{Style.RESET_ALL}")

            # Примеры сложных запросов
            print(f"\n{Fore.YELLOW}📈 ПРИМЕРЫ АНАЛИТИКИ:{Style.RESET_ALL}")

            # Самые популярные товары
            cursor.execute("""
                SELECT product_id, COUNT(*) as check_count 
                FROM price_history 
                GROUP BY product_id 
                ORDER BY check_count DESC 
                LIMIT 5
            """)
            print(f"\n{Fore.CYAN}Самые проверяемые товары:{Style.RESET_ALL}")
            for row in cursor.fetchall():
                print(f"  {row['product_id']}: {row['check_count']} проверок")

            # Изменения цен за последние 7 дней
            cursor.execute("""
                SELECT DATE(timestamp) as day, 
                       COUNT(*) as changes,
                       SUM(CASE WHEN change_status = 'increased' THEN 1 ELSE 0 END) as increased,
                       SUM(CASE WHEN change_status = 'decreased' THEN 1 ELSE 0 END) as decreased
                FROM price_changes 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                GROUP BY DATE(timestamp)
                ORDER BY day DESC
            """)

            changes = cursor.fetchall()
            if changes:
                print(f"\n{Fore.CYAN}Изменения цен за последние 7 дней:{Style.RESET_ALL}")
                for row in changes:
                    print(f"  {row['day']}: {row['changes']} изменений "
                          f"({Fore.RED}+{row['increased']}{Style.RESET_ALL}/"
                          f"{Fore.GREEN}-{row['decreased']}{Style.RESET_ALL})")

            cursor.close()
            connection.close()
            print(f"\n{Fore.GREEN}✓ Соединение закрыто{Style.RESET_ALL}")

    except Error as e:
        print(f"{Fore.RED}✗ Ошибка подключения: {e}{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}Проверьте:")
        print("1. Запущен ли MySQL сервер")
        print("2. Правильные ли параметры подключения")
        print("3. Существует ли база данных 'price_monitor'")
        print(f"\n{Fore.CYAN}Попробуйте создать базу данных:{Style.RESET_ALL}")
        print("""
import mysql.connector
connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password=''
)
cursor = connection.cursor()
cursor.execute("CREATE DATABASE IF NOT EXISTS price_monitor")
print("База данных создана")
        """)


def export_to_csv():
    """Экспортирует данные из базы в CSV файлы"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='price_monitor'
        )

        cursor = connection.cursor(dictionary=True)

        import csv
        from datetime import datetime

        # Экспортируем каждую таблицу
        tables = ['products', 'price_history', 'price_changes', 'monitoring_stats']

        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            if rows:
                filename = f"{table}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                    writer.writeheader()
                    writer.writerows(rows)

                print(f"{Fore.GREEN}✓ Экспортировано {len(rows)} записей из {table} в {filename}{Style.RESET_ALL}")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка экспорта: {e}{Style.RESET_ALL}")


def backup_database():
    """Создает резервную копию базы данных"""
    try:
        import subprocess
        import os

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"price_monitor_backup_{timestamp}.sql"

        command = [
            'mysqldump',
            '--host=localhost',
            '--user=root',
            '--password=',
            'price_monitor'
        ]

        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                file_size = os.path.getsize(backup_file) / 1024  # KB
                print(f"{Fore.GREEN}✓ Резервная копия создана: {backup_file}")
                print(f"  Размер: {file_size:.1f} KB{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}✗ Ошибка создания резервной копии: {result.stderr}{Style.RESET_ALL}")

    except Exception as e:
        print(f"{Fore.RED}✗ Ошибка: {e}{Style.RESET_ALL}")


def main():
    """Главное меню"""
    while True:
        print(f"\n{Fore.CYAN}{'=' * 60}")
        print(f"{'УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ':^60}")
        print(f"{'=' * 60}{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Просмотреть содержимое базы")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Экспорт в CSV")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Создать резервную копию")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Выполнить SQL запрос")
        print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Выход")

        choice = input(f"\n{Fore.GREEN}Выберите действие: {Style.RESET_ALL}")

        if choice == '1':
            view_database()
        elif choice == '2':
            export_to_csv()
        elif choice == '3':
            backup_database()
        elif choice == '4':
            execute_sql_query()
        elif choice == '0':
            print(f"{Fore.YELLOW}Выход...{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Неверный выбор{Style.RESET_ALL}")

        if choice != '0':
            input(f"\n{Fore.CYAN}Нажмите Enter чтобы продолжить...{Style.RESET_ALL}")


def execute_sql_query():
    """Выполняет произвольный SQL запрос"""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='price_monitor'
        )

        cursor = connection.cursor(dictionary=True)

        print(f"\n{Fore.YELLOW}Введите SQL запрос (или 'exit' для выхода):{Style.RESET_ALL}")

        while True:
            query = input(f"{Fore.CYAN}SQL> {Style.RESET_ALL}").strip()

            if query.lower() == 'exit':
                break

            if not query:
                continue

            try:
                cursor.execute(query)

                if query.strip().upper().startswith('SELECT'):
                    # Для SELECT запросов показываем результаты
                    rows = cursor.fetchall()
                    if rows:
                        print(f"\n{Fore.GREEN}Результат ({len(rows)} строк):{Style.RESET_ALL}")

                        # Показываем заголовки
                        headers = rows[0].keys()
                        print(f"{Fore.YELLOW}{' | '.join(headers)}{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}{'-' * 60}{Style.RESET_ALL}")

                        # Показываем данные
                        for row in rows[:20]:  # Ограничиваем 20 строками
                            values = [str(row[h])[:30] for h in headers]
                            print(f"{Fore.WHITE}{' | '.join(values)}{Style.RESET_ALL}")

                        if len(rows) > 20:
                            print(f"{Fore.YELLOW}... и еще {len(rows) - 20} строк{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.YELLOW}Запрос не вернул результатов{Style.RESET_ALL}")
                else:
                    # Для не-SELECT запросов показываем количество затронутых строк
                    print(f"{Fore.GREEN}Выполнено. Затронуто строк: {cursor.rowcount}{Style.RESET_ALL}")
                    connection.commit()

            except Exception as e:
                print(f"{Fore.RED}Ошибка SQL: {e}{Style.RESET_ALL}")

        cursor.close()
        connection.close()

    except Exception as e:
        print(f"{Fore.RED}Ошибка подключения: {e}{Style.RESET_ALL}")


if __name__ == "__main__":
    main()
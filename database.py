"""
Модуль для работы с MySQL базой данных (упрощенный и надежный)
"""
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import csv
import os
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Класс для управления MySQL базой данных"""

    def __init__(self, host='localhost', user='root', password='', database='price_monitor'):
        """
        Инициализация подключения к базе данных
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
        self.is_connected = False

    def connect(self, auto_create=True):
        """Подключение к базе данных"""
        try:
            logger.info(f"Попытка подключения к MySQL: {self.host}/{self.database}")

            # Сначала пробуем подключиться без указания базы данных
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                autocommit=True
            )

            if self.connection.is_connected():
                self.cursor = self.connection.cursor(dictionary=True)
                logger.info(f"Успешное подключение к MySQL серверу")

                # Проверяем существование базы данных
                self.cursor.execute(f"SHOW DATABASES LIKE '{self.database}'")
                result = self.cursor.fetchone()

                if not result and auto_create:
                    logger.info(f"База данных '{self.database}' не существует, создаем...")
                    self.create_database()
                elif not result:
                    logger.error(f"База данных '{self.database}' не существует")
                    return False

                # Подключаемся к конкретной базе данных
                self.connection.database = self.database
                self.is_connected = True

                # Проверяем/создаем таблицы
                self.create_tables()

                logger.info(f"Успешное подключение к базе данных {self.database}")
                return True

        except Error as e:
            logger.error(f"Ошибка подключения к MySQL: {e}")

            # Если это ошибка "Unknown database", пробуем создать базу
            if "Unknown database" in str(e) and auto_create:
                logger.info("Пробуем создать базу данных...")
                return self.create_database_and_connect()

            return False

    def create_database_and_connect(self):
        """Создает базу данных и подключается к ней"""
        try:
            # Создаем временное подключение без базы данных
            temp_conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                autocommit=True
            )
            temp_cursor = temp_conn.cursor()

            # Создаем базу данных
            temp_cursor.execute(f"CREATE DATABASE {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"База данных {self.database} создана")

            temp_cursor.close()
            temp_conn.close()

            # Подключаемся к созданной базе
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=True
            )
            self.cursor = self.connection.cursor(dictionary=True)

            # Создаем таблицы
            self.create_tables()

            self.is_connected = True
            logger.info("Все таблицы успешно созданы")
            return True

        except Error as e:
            logger.error(f"Ошибка создания базы данных: {e}")
            return False

    def create_database(self):
        """Создает базу данных"""
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"База данных {self.database} создана/проверена")
            return True
        except Error as e:
            logger.error(f"Ошибка создания базы данных: {e}")
            return False

    def create_tables(self):
        """Создает необходимые таблицы в базе данных"""
        try:
            # Упрощенные таблицы (без внешних ключей для начала)
            tables = {
                'products': """
                    CREATE TABLE IF NOT EXISTS products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_id VARCHAR(50) UNIQUE NOT NULL,
                        url VARCHAR(500) NOT NULL,
                        name VARCHAR(255),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_product_id (product_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,

                'price_history': """
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
                        INDEX idx_timestamp (timestamp)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,

                'price_changes': """
                    CREATE TABLE IF NOT EXISTS price_changes (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_id VARCHAR(50) NOT NULL,
                        current_price DECIMAL(10, 2),
                        previous_price DECIMAL(10, 2),
                        change_amount DECIMAL(10, 2),
                        change_percentage DECIMAL(5, 2),
                        change_status VARCHAR(20) DEFAULT 'no_change',
                        significance VARCHAR(50),
                        cycle INT DEFAULT 0,
                        timestamp DATETIME NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_product_id (product_id),
                        INDEX idx_status (change_status)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,

                'monitoring_stats': """
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
                        INDEX idx_cycle (cycle)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """,

                'html_pages': """
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
                        INDEX idx_timestamp (timestamp)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            }

            for table_name, create_query in tables.items():
                try:
                    self.cursor.execute(create_query)
                    logger.debug(f"Таблица {table_name} создана/проверена")
                except Error as e:
                    logger.error(f"Ошибка создания таблицы {table_name}: {e}")

            logger.info("Все таблицы успешно созданы/проверены")
            return True

        except Error as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            return False

    def save_product(self, product_data: Dict[str, Any]) -> bool:
        """Сохраняет или обновляет информацию о товаре"""
        if not self.is_connected:
            return False

        try:
            query = """
                INSERT INTO products (product_id, url, name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    url = VALUES(url),
                    name = VALUES(name),
                    updated_at = CURRENT_TIMESTAMP
            """

            values = (
                product_data.get('product_id'),
                product_data.get('url'),
                product_data.get('name', f"Товар {product_data.get('product_id')}")
            )

            self.cursor.execute(query, values)
            return True

        except Error as e:
            logger.error(f"Ошибка сохранения товара: {e}")
            return False

    def save_price(self, price_data: Dict[str, Any]) -> bool:
        """Сохраняет цену в историю"""
        if not self.is_connected:
            return False

        try:
            # Сначала сохраняем товар
            self.save_product({
                'product_id': price_data.get('product_id'),
                'url': price_data.get('url', ''),
                'name': f"Товар {price_data.get('product_id')}"
            })

            query = """
                INSERT INTO price_history 
                (product_id, price, price_formatted, currency, source, cycle, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                price_data.get('product_id'),
                price_data.get('price'),
                price_data.get('price_formatted'),
                price_data.get('currency', 'RUB'),
                price_data.get('source', 'unknown'),
                price_data.get('cycle', 0),
                price_data.get('timestamp')
            )

            self.cursor.execute(query, values)
            return True

        except Error as e:
            logger.error(f"Ошибка сохранения цены: {e}")
            return False

    def save_price_change(self, change_data: Dict[str, Any]) -> bool:
        """Сохраняет информацию об изменении цены"""
        if not self.is_connected:
            return False

        try:
            query = """
                INSERT INTO price_changes 
                (product_id, current_price, previous_price, change_amount, 
                 change_percentage, change_status, significance, cycle, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                change_data.get('product_id'),
                change_data.get('current_price'),
                change_data.get('previous_price'),
                change_data.get('change_amount'),
                change_data.get('change_percentage'),
                change_data.get('change_status', 'no_change'),
                change_data.get('significance', ''),
                change_data.get('cycle', 0),
                change_data.get('timestamp')
            )

            self.cursor.execute(query, values)
            return True

        except Error as e:
            logger.error(f"Ошибка сохранения изменения цены: {e}")
            return False

    def save_monitoring_stats(self, stats_data: Dict[str, Any]) -> bool:
        """Сохраняет статистику мониторинга"""
        if not self.is_connected:
            return False

        try:
            query = """
                INSERT INTO monitoring_stats 
                (cycle, total_products, successful_parses, failed_parses, 
                 price_changes, increased, decreased, new_products, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    total_products = VALUES(total_products),
                    successful_parses = VALUES(successful_parses),
                    failed_parses = VALUES(failed_parses),
                    price_changes = VALUES(price_changes),
                    increased = VALUES(increased),
                    decreased = VALUES(decreased),
                    new_products = VALUES(new_products),
                    timestamp = VALUES(timestamp)
            """

            values = (
                stats_data.get('cycle'),
                stats_data.get('total_products', 0),
                stats_data.get('successful_parses', 0),
                stats_data.get('failed_parses', 0),
                stats_data.get('price_changes', 0),
                stats_data.get('increased', 0),
                stats_data.get('decreased', 0),
                stats_data.get('new_products', 0),
                stats_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )

            self.cursor.execute(query, values)
            return True

        except Error as e:
            logger.error(f"Ошибка сохранения статистики: {e}")
            return False

    def save_html_page(self, page_data: Dict[str, Any]) -> bool:
        """Сохраняет HTML страницу в базу данных"""
        if not self.is_connected:
            return False

        try:
            # Сначала сохраняем товар
            self.save_product({
                'product_id': page_data.get('product_id'),
                'url': '',  # URL может быть неизвестен для HTML страницы
                'name': f"Товар {page_data.get('product_id')}"
            })

            query = """
                INSERT INTO html_pages 
                (product_id, filename, html_content, content_length, status_code, cycle, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            # Читаем HTML из файла если нужно
            html_content = page_data.get('html_content', '')
            if not html_content and 'filename' in page_data:
                try:
                    with open(page_data['filename'], 'r', encoding='utf-8') as f:
                        html_content = f.read()
                except:
                    html_content = ''
                    logger.warning(f"Не удалось прочитать HTML файл: {page_data.get('filename')}")

            values = (
                page_data.get('product_id'),
                page_data.get('filename', ''),
                html_content,
                page_data.get('content_length', 0),
                page_data.get('status_code', 0),
                page_data.get('cycle', 0),
                page_data.get('timestamp')
            )

            self.cursor.execute(query, values)
            return True

        except Error as e:
            logger.error(f"Ошибка сохранения HTML страницы: {e}")
            return False

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Получает список всех товаров"""
        if not self.is_connected:
            return []

        try:
            query = """
                SELECT p.*, 
                       (SELECT price FROM price_history 
                        WHERE product_id = p.product_id 
                        ORDER BY timestamp DESC LIMIT 1) as last_price,
                       (SELECT price_formatted FROM price_history 
                        WHERE product_id = p.product_id 
                        ORDER BY timestamp DESC LIMIT 1) as last_price_formatted,
                       (SELECT timestamp FROM price_history 
                        WHERE product_id = p.product_id 
                        ORDER BY timestamp DESC LIMIT 1) as last_check
                FROM products p
                ORDER BY p.created_at DESC
            """

            self.cursor.execute(query)
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Ошибка получения списка товаров: {e}")
            return []

    def get_price_history(self, product_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Получает историю цен для товара"""
        if not self.is_connected:
            return []

        try:
            query = """
                SELECT * FROM price_history 
                WHERE product_id = %s 
                ORDER BY timestamp DESC 
                LIMIT %s
            """

            self.cursor.execute(query, (product_id, limit))
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Ошибка получения истории цен: {e}")
            return []

    def get_price_changes(self, days: int = 7) -> List[Dict[str, Any]]:
        """Получает изменения цен за указанный период"""
        if not self.is_connected:
            return []

        try:
            query = """
                SELECT pc.*, p.url 
                FROM price_changes pc
                LEFT JOIN products p ON pc.product_id = p.product_id
                WHERE pc.timestamp >= DATE_SUB(NOW(), INTERVAL %s DAY)
                AND pc.change_status IN ('increased', 'decreased')
                ORDER BY pc.timestamp DESC
            """

            self.cursor.execute(query, (days,))
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Ошибка получения изменений цен: {e}")
            return []

    def get_monitoring_stats(self, cycles: int = 10) -> List[Dict[str, Any]]:
        """Получает статистику мониторинга"""
        if not self.is_connected:
            return []

        try:
            query = """
                SELECT * FROM monitoring_stats 
                ORDER BY cycle DESC 
                LIMIT %s
            """

            self.cursor.execute(query, (cycles,))
            return self.cursor.fetchall()

        except Error as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return []

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Получает статистику для дашборда"""
        if not self.is_connected:
            return {}

        try:
            stats = {}

            # Общее количество товаров
            self.cursor.execute("SELECT COUNT(*) as count FROM products")
            stats['total_products'] = self.cursor.fetchone()['count']

            # Количество проверок сегодня
            self.cursor.execute("""
                SELECT COUNT(DISTINCT product_id) as count 
                FROM price_history 
                WHERE DATE(timestamp) = CURDATE()
            """)
            stats['checked_today'] = self.cursor.fetchone()['count']

            # Изменения цен сегодня
            self.cursor.execute("""
                SELECT COUNT(*) as count 
                FROM price_changes 
                WHERE DATE(timestamp) = CURDATE()
                AND change_status IN ('increased', 'decreased')
            """)
            stats['changes_today'] = self.cursor.fetchone()['count']

            # Последний цикл
            self.cursor.execute("""
                SELECT * FROM monitoring_stats 
                ORDER BY cycle DESC LIMIT 1
            """)
            last_cycle = self.cursor.fetchone()
            if last_cycle:
                stats.update(last_cycle)

            return stats

        except Error as e:
            logger.error(f"Ошибка получения статистики дашборда: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30) -> int:
        """Очищает старые данные из базы"""
        if not self.is_connected:
            return 0

        try:
            queries = [
                f"DELETE FROM price_history WHERE timestamp < DATE_SUB(NOW(), INTERVAL {days} DAY)",
                f"DELETE FROM price_changes WHERE timestamp < DATE_SUB(NOW(), INTERVAL {days} DAY)",
                f"DELETE FROM html_pages WHERE timestamp < DATE_SUB(NOW(), INTERVAL {days} DAY)",
                f"DELETE FROM monitoring_stats WHERE timestamp < DATE_SUB(NOW(), INTERVAL {days} DAY)"
            ]

            total_deleted = 0
            for query in queries:
                self.cursor.execute(query)
                total_deleted += self.cursor.rowcount

            self.connection.commit()
            return total_deleted

        except Error as e:
            logger.error(f"Ошибка очистки данных: {e}")
            return 0

    def backup_database(self, backup_path: str = None) -> str:
        """Создает резервную копию базы данных"""
        if not self.is_connected:
            return ""

        if backup_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"backup_{timestamp}.sql"

        try:
            import subprocess

            command = [
                'mysqldump',
                '--host=' + self.host,
                '--user=' + self.user,
                '--password=' + self.password,
                self.database
            ]

            with open(backup_path, 'w', encoding='utf-8') as f:
                result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

                if result.returncode == 0:
                    logger.info(f"Резервная копия создана: {backup_path}")
                    return backup_path
                else:
                    logger.error(f"Ошибка создания резервной копии: {result.stderr}")
                    return ""

        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            return ""

    def test_connection(self) -> bool:
        """Тестирует соединение с базой данных"""
        return self.is_connected and self.connection.is_connected()

    def close(self):
        """Закрывает соединение с базой данных"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("Соединение с базой данных закрыто")
        except:
            pass
        finally:
            self.is_connected = False

    def __enter__(self):
        """Контекстный менеджер"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер"""
        self.close()


class DatabaseConsole:
    """Класс для работы с базой данных через консоль"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def show_menu(self):
        """Показывает меню управления базой данных"""
        from colorama import Fore, Style

        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{'УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ':^60}")
        print(f"{'='*60}{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}1.{Style.RESET_ALL} Показать все товары")
        print(f"{Fore.YELLOW}2.{Style.RESET_ALL} Показать историю цен товара")
        print(f"{Fore.YELLOW}3.{Style.RESET_ALL} Показать изменения цен")
        print(f"{Fore.YELLOW}4.{Style.RESET_ALL} Показать статистику мониторинга")
        print(f"{Fore.YELLOW}5.{Style.RESET_ALL} Дашборд")
        print(f"{Fore.YELLOW}6.{Style.RESET_ALL} Создать резервную копию")
        print(f"{Fore.YELLOW}7.{Style.RESET_ALL} Очистить старые данные")
        print(f"{Fore.YELLOW}8.{Style.RESET_ALL} Проверить соединение")
        print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Назад")

    def run(self):
        """Запускает интерфейс управления базой данных"""
        from colorama import Fore, Style

        while True:
            self.show_menu()
            choice = input(f"\n{Fore.GREEN}Выберите действие: {Style.RESET_ALL}")

            if choice == '1':
                self.show_all_products()
            elif choice == '2':
                self.show_product_history()
            elif choice == '3':
                self.show_price_changes()
            elif choice == '4':
                self.show_monitoring_stats()
            elif choice == '5':
                self.show_dashboard()
            elif choice == '6':
                self.create_backup()
            elif choice == '7':
                self.cleanup_old_data()
            elif choice == '8':
                self.test_connection()
            elif choice == '0':
                break
            else:
                print(f"{Fore.RED}Неверный выбор{Style.RESET_ALL}")

            if choice != '0':
                input(f"\n{Fore.CYAN}Нажмите Enter чтобы продолжить...{Style.RESET_ALL}")

    def show_all_products(self):
        """Показывает все товары в базе"""
        from colorama import Fore, Style

        products = self.db.get_all_products()

        if not products:
            print(f"{Fore.YELLOW}Нет товаров в базе данных{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*100}")
        print(f"{'СПИСОК ТОВАРОВ':^100}")
        print(f"{'='*100}{Style.RESET_ALL}")

        print(f"{Fore.YELLOW}{'ID':<15} {'Название':<30} {'URL':<40} {'Последняя цена':<15} {'Проверка':<20}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'-'*100}{Style.RESET_ALL}")

        for product in products:
            print(f"{Fore.WHITE}{product['product_id'][:15]:<15} "
                  f"{product.get('name', '')[:28]:<30} "
                  f"{product['url'][:38]:<40} "
                  f"{Fore.GREEN}{product.get('last_price_formatted', 'N/A'):<15} "
                  f"{Fore.WHITE}{str(product.get('last_check', ''))[:19]:<20}{Style.RESET_ALL}")

    def show_product_history(self):
        """Показывает историю цен для конкретного товара"""
        from colorama import Fore, Style

        product_id = input(f"{Fore.CYAN}Введите ID товара: {Style.RESET_ALL}")

        history = self.db.get_price_history(product_id, 20)

        if not history:
            print(f"{Fore.YELLOW}Нет истории цен для товара {product_id}{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"ИСТОРИЯ ЦЕН: {product_id}")
        print(f"{'='*80}{Style.RESET_ALL}")

        for record in history:
            print(f"{Fore.WHITE}{record['timestamp']} | "
                  f"{Fore.GREEN}{record['price_formatted']:<15} | "
                  f"{Fore.CYAN}{record['source']:<20} | "
                  f"Цикл: {record['cycle']}{Style.RESET_ALL}")

    def show_price_changes(self):
        """Показывает изменения цен"""
        from colorama import Fore, Style

        days = input(f"{Fore.CYAN}За сколько дней показать изменения? (по умолчанию 7): {Style.RESET_ALL}")
        days = int(days) if days.isdigit() else 7

        changes = self.db.get_price_changes(days)

        if not changes:
            print(f"{Fore.YELLOW}Нет изменений цен за последние {days} дней{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*100}")
        print(f"ИЗМЕНЕНИЯ ЦЕН ЗА ПОСЛЕДНИЕ {days} ДНЕЙ")
        print(f"{'='*100}{Style.RESET_ALL}")

        for change in changes:
            status_color = Fore.RED if change['change_status'] == 'increased' else Fore.GREEN
            symbol = "📈" if change['change_status'] == 'increased' else "📉"

            print(f"\n{status_color}{symbol} {change['product_id']}")
            print(f"  Статус: {change['change_status']}")
            print(f"  Было: {change['previous_price']} ₽, Стало: {change['current_price']} ₽")
            print(f"  Изменение: {change['change_amount']} ₽ ({change['change_percentage']}%)")
            print(f"  Время: {change['timestamp']}")
            print(f"  URL: {change.get('url', '')[:60]}...{Style.RESET_ALL}")

    def show_monitoring_stats(self):
        """Показывает статистику мониторинга"""
        from colorama import Fore, Style

        cycles = input(f"{Fore.CYAN}Сколько последних циклов показать? (по умолчанию 10): {Style.RESET_ALL}")
        cycles = int(cycles) if cycles.isdigit() else 10

        stats = self.db.get_monitoring_stats(cycles)

        if not stats:
            print(f"{Fore.YELLOW}Нет статистики мониторинга{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*100}")
        print(f"СТАТИСТИКА МОНИТОРИНГА (последние {len(stats)} циклов)")
        print(f"{'='*100}{Style.RESET_ALL}")

        for stat in stats:
            print(f"\n{Fore.YELLOW}Цикл #{stat['cycle']} - {stat['timestamp']}")
            print(f"  Товаров: {stat['total_products']}")
            print(f"  Успешно спарсено: {stat['successful_parses']}")
            print(f"  Изменений цен: {stat['price_changes']}")
            print(f"  Повышений: {Fore.RED}{stat['increased']}{Fore.YELLOW}, Понижений: {Fore.GREEN}{stat['decreased']}{Style.RESET_ALL}")

    def show_dashboard(self):
        """Показывает дашборд с основной статистикой"""
        from colorama import Fore, Style

        stats = self.db.get_dashboard_stats()

        if not stats:
            print(f"{Fore.YELLOW}Нет данных для дашборда{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'ДАШБОРД МОНИТОРИНГА ЦЕН':^80}")
        print(f"{'='*80}{Style.RESET_ALL}")

        print(f"\n{Fore.YELLOW}📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"  Всего товаров: {Fore.GREEN}{stats.get('total_products', 0)}")
        print(f"  Проверено сегодня: {Fore.GREEN}{stats.get('checked_today', 0)}")
        print(f"  Изменений сегодня: {Fore.GREEN}{stats.get('changes_today', 0)}")

        if 'cycle' in stats:
            print(f"\n{Fore.YELLOW}📈 ПОСЛЕДНИЙ ЦИКЛ (#{stats['cycle']}):")
            print(f"  Успешных парсингов: {Fore.GREEN}{stats.get('successful_parses', 0)}")
            print(f"  Изменений цен: {Fore.GREEN}{stats.get('price_changes', 0)}")
            print(f"  Повышений: {Fore.RED}{stats.get('increased', 0)}{Fore.YELLOW}, "
                  f"Понижений: {Fore.GREEN}{stats.get('decreased', 0)}")

        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    def create_backup(self):
        """Создает резервную копию базы данных"""
        from colorama import Fore, Style

        backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

        if self.db.backup_database(backup_file):
            print(f"{Fore.GREEN}✓ Резервная копия создана: {backup_file}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Не удалось создать резервную копию{Style.RESET_ALL}")

    def cleanup_old_data(self):
        """Очищает старые данные"""
        from colorama import Fore, Style

        days = input(f"{Fore.CYAN}Удалить данные старше скольки дней? (по умолчанию 30): {Style.RESET_ALL}")
        days = int(days) if days.isdigit() else 30

        confirm = input(f"{Fore.RED}Вы уверены, что хотите удалить данные старше {days} дней? (y/n): {Style.RESET_ALL}")

        if confirm.lower() == 'y':
            deleted_count = self.db.cleanup_old_data(days)
            if deleted_count > 0:
                print(f"{Fore.GREEN}✓ Удалено {deleted_count} записей старше {days} дней{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Нет данных для удаления{Style.RESET_ALL}")

    def test_connection(self):
        """Проверяет соединение с базой данных"""
        from colorama import Fore, Style

        if self.db.test_connection():
            print(f"{Fore.GREEN}✓ Соединение с базой данных активно{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Нет соединения с базой данных{Style.RESET_ALL}")
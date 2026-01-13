"""
Модуль для мониторинга цен на Ozon с headless браузером
"""
import time
import schedule
import threading
import random
import glob
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from colorama import Fore, Style

from browser_manager import BrowserManager
from html_parser import HTMLParser
from price_history import PriceHistory
from price_comparator import PriceComparator


class PriceMonitor:
    """Основной класс мониторинга цен с headless браузером"""

    def __init__(self, config_manager, url_manager, logger, db_manager=None):
        self.config_manager = config_manager
        self.url_manager = url_manager
        self.logger = logger
        self.db_manager = db_manager

        self.current_cycle = 0
        self.last_results = None
        self.is_running = True

        # Получаем настройку headless режима
        headless_enabled = config_manager.is_headless_enabled()

        # Инициализация компонентов с headless режимом
        self.browser_manager = BrowserManager(headless=headless_enabled)
        self.html_parser = HTMLParser()
        self.price_history = PriceHistory()
        self.price_comparator = PriceComparator()

        if headless_enabled:
            self.logger.info("Используется headless режим браузера")
        else:
            self.logger.info("Используется GUI режим браузера")

        if db_manager and db_manager.is_connected:
            self.logger.info("Используется MySQL база данных")
        elif db_manager:
            self.logger.info("MySQL база данных не подключена")
            self.db_manager = None
        else:
            self.logger.info("MySQL база данных не используется")

    def start_monitoring(self):
        """Запускает мониторинг в отдельном потоке"""
        self.logger.info("Запуск фонового мониторинга...")

        # Первый запуск
        self.run_monitoring_cycle()

        # Настройка расписания
        interval = self.config_manager.get_monitoring_interval()
        schedule.every(interval).minutes.do(self.run_monitoring_cycle)

        # Очистка файлов раз в день
        schedule.every().day.at("02:00").do(self.cleanup_old_files)

        # Очистка старых данных из базы раз в неделю
        if self.db_manager and self.db_manager.is_connected:
            schedule.every().sunday.at("03:00").do(self.cleanup_old_database_data)

        self.logger.info(f"Мониторинг запущен с интервалом {interval} минут")

        # Основной цикл планировщика
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

    # ... остальные методы остаются без изменений ...
    # (используйте тот же код, что был в предыдущей версии price_monitor.py)

    def run_monitoring_cycle(self):
        """Выполняет один цикл мониторинга"""
        self.current_cycle += 1
        cycle_num = self.current_cycle

        pages = self.url_manager.get_pages()

        if not pages:
            self.logger.warning("Нет товаров для мониторинга")
            print(f"{Fore.YELLOW}Нет товаров для мониторинга. Добавьте URL товаров.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"🔄 ЗАПУСК ПАРСИНГА #{cycle_num}")
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Товаров в мониторинге: {len(pages)}")
        print(f"{'='*80}{Style.RESET_ALL}")

        try:
            # Получаем данные браузера
            self.logger.info(f"Получение cookies для цикла #{cycle_num}")
            browser_data = self.browser_manager.get_cookies()
            if not browser_data:
                self.logger.error("Не удалось получить данные браузера")
                print(f"{Fore.RED}Не удалось получить данные браузера. Пропускаем цикл.{Style.RESET_ALL}")
                return

            # Парсим страницы
            pages_data = self.scrape_pages(pages, browser_data, cycle_num)

            # Извлекаем цены
            current_prices = self.extract_prices(pages_data)

            # Сохраняем в историю (и в базу данных если есть)
            if current_prices:
                # Сохраняем в файл
                self.price_history.save_prices(current_prices, cycle_num)

                # Сохраняем в базу данных если подключена
                if self.db_manager and self.db_manager.is_connected:
                    self.save_to_database(pages_data, current_prices, cycle_num)

                # Сравниваем цены
                previous_prices = self.price_history.get_previous_prices(current_prices)
                price_changes = self.price_comparator.compare_prices(
                    current_prices, previous_prices
                )

                # Логируем изменения
                self.log_price_changes(price_changes)

                # Сохраняем изменения цен в базу данных
                if self.db_manager and self.db_manager.is_connected:
                    for change in price_changes:
                        if change.get('change_status') in ['increased', 'decreased']:
                            self.db_manager.save_price_change(change)

                # Сохраняем результаты
                self.last_results = {
                    "cycle": cycle_num,
                    "prices": current_prices,
                    "changes": price_changes,
                    "stats": {
                        "total_products": len(pages),
                        "successful_parses": len(current_prices),
                        "failed_parses": len(pages) - len(current_prices),
                        "price_changes": len([c for c in price_changes
                                            if c['change_status'] in ['increased', 'decreased']]),
                        "increased": len([c for c in price_changes
                                         if c['change_status'] == 'increased']),
                        "decreased": len([c for c in price_changes
                                         if c['change_status'] == 'decreased']),
                        "new_products": len([c for c in price_changes
                                           if c['change_status'] == 'new'])
                    }
                }

                # Сохраняем статистику в базу данных
                if (self.db_manager and self.db_manager.is_connected and
                    self.last_results.get('stats')):
                    self.db_manager.save_monitoring_stats({
                        'cycle': cycle_num,
                        **self.last_results['stats'],
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })

                self.logger.info(f"Цикл #{cycle_num} завершен успешно")
                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✓ Цикл #{cycle_num} завершен{Style.RESET_ALL}")

                # Показываем сводку
                self.print_summary(cycle_num, current_prices, price_changes)
            else:
                self.logger.warning(f"В цикле #{cycle_num} не удалось получить ни одной цены")
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠ Цикл #{cycle_num}: цены не получены{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Ошибка в цикле мониторинга: {e}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ✗ Ошибка в цикле #{cycle_num}: {e}{Style.RESET_ALL}")

    def scrape_pages(self, pages: list, browser_data: dict, cycle_num: int) -> list:
        """Парсит список страниц"""
        pages_data = []
        headers = self.browser_manager.generate_headers(browser_data)
        cookies_dict = browser_data.get("cookies", {})

        self.logger.info(f"Начинаем парсинг {len(pages)} страниц")

        for index, page_url in enumerate(pages, 1):
            try:
                self.logger.info(f"Обработка страницы {index}/{len(pages)}: {page_url[:50]}...")
                print(f"{Fore.CYAN}[{index}/{len(pages)}] Обработка: {page_url[:50]}...{Style.RESET_ALL}")

                # Делаем запрос с повторными попытками
                response = self.browser_manager.make_request(
                    page_url, cookies_dict, headers
                )

                if response and response.status_code == 200:
                    product_id = self.url_manager.extract_product_id(page_url)

                    # Генерируем имя файла
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"product_{product_id}_{timestamp}_cycle{cycle_num}.html"

                    # Сохраняем HTML
                    with open(filename, "w", encoding="utf-8") as file:
                        file.write(response.text)

                    page_data = {
                        "cycle": cycle_num,
                        "index": index,
                        "url": page_url,
                        "product_id": product_id,
                        "filename": filename,
                        "status": "success",
                        "status_code": 200,
                        "content_length": len(response.text),
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "timestamp_iso": datetime.now().isoformat()
                    }
                    pages_data.append(page_data)

                    print(f"{Fore.GREEN}  ✓ Успешно: {filename}{Style.RESET_ALL}")

                else:
                    status_code = response.status_code if response else 0
                    page_data = {
                        "cycle": cycle_num,
                        "index": index,
                        "url": page_url,
                        "status": "error",
                        "status_code": status_code,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    pages_data.append(page_data)

                    print(f"{Fore.RED}  ✗ Ошибка: статус {status_code}{Style.RESET_ALL}")

            except Exception as e:
                self.logger.error(f"Ошибка при обработке страницы {page_url}: {e}")
                page_data = {
                    "cycle": cycle_num,
                    "index": index,
                    "url": page_url,
                    "status": "exception",
                    "error": str(e),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                pages_data.append(page_data)

                print(f"{Fore.RED}  ✗ Исключение: {str(e)[:50]}...{Style.RESET_ALL}")

            # Пауза между запросами для имитации человека
            if index < len(pages):
                pause_time = random.uniform(2, 5)
                time.sleep(pause_time)

        return pages_data

    def extract_prices(self, pages_data: list) -> list:
        """Извлекает цены из данных страниц"""
        current_prices = []
        successful = 0
        failed = 0

        self.logger.info("Извлечение цен из HTML файлов...")
        print(f"{Fore.CYAN}Извлечение цен...{Style.RESET_ALL}")

        for page in pages_data:
            if page.get("status") == "success":
                filename = page.get("filename")
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        html_content = f.read()

                    price_info = self.html_parser.extract_price(html_content, page['url'])
                    if price_info:
                        price_data = {
                            "cycle": page['cycle'],
                            "index": page['index'],
                            "product_id": page['product_id'],
                            "filename": filename,
                            "url": page['url'],
                            "price": price_info['price'],
                            "price_formatted": price_info['price_formatted'],
                            "currency": price_info.get('currency', 'RUB'),
                            "source": price_info.get('source', 'unknown'),
                            "timestamp": page['timestamp'],
                            "timestamp_iso": page.get('timestamp_iso', datetime.now().isoformat())
                        }
                        current_prices.append(price_data)
                        successful += 1

                        # Цвет в зависимости от источника
                        source_color = Fore.CYAN if 'json' in price_info.get('source', '') else Fore.GREEN
                        print(f"{Fore.WHITE}  Товар #{page['index']}: {source_color}{price_info['price_formatted']} "
                              f"{Fore.WHITE}({price_info.get('source', 'unknown')}){Style.RESET_ALL}")
                    else:
                        failed += 1
                        print(f"{Fore.YELLOW}  Товар #{page['index']}: цена не найдена{Style.RESET_ALL}")

                except Exception as e:
                    self.logger.error(f"Ошибка при чтении файла {filename}: {e}")
                    failed += 1
                    print(f"{Fore.RED}  Товар #{page['index']}: ошибка чтения файла{Style.RESET_ALL}")
            else:
                failed += 1

        self.logger.info(f"Извлечение завершено: успешно {successful}, неудачно {failed}")
        return current_prices

    def save_to_database(self, pages_data: List[Dict], current_prices: List[Dict], cycle_num: int):
        """Сохраняет данные в MySQL базу данных"""
        try:
            self.logger.info("Сохранение данных в базу данных...")

            # Сохраняем HTML страницы (только если конфигурация разрешает)
            save_html = self.config_manager.get('save_html_pages', False)

            for page in pages_data:
                if page.get('status') == 'success':
                    page_data = {
                        'product_id': page.get('product_id'),
                        'filename': page.get('filename'),
                        'content_length': page.get('content_length', 0),
                        'status_code': page.get('status_code', 0),
                        'cycle': cycle_num,
                        'timestamp': page.get('timestamp')
                    }

                    if save_html:
                        # Сохраняем HTML контент
                        try:
                            with open(page.get('filename'), 'r', encoding='utf-8') as f:
                                page_data['html_content'] = f.read()
                        except:
                            page_data['html_content'] = ''

                    # Используем новый метод save_html_page
                    if hasattr(self.db_manager, 'save_html_page'):
                        self.db_manager.save_html_page(page_data)

            # Сохраняем цены и информацию о товарах
            for price in current_prices:
                # Сохраняем цену
                self.db_manager.save_price(price)

                # Сохраняем информацию о товаре
                self.db_manager.save_product({
                    'product_id': price.get('product_id'),
                    'url': price.get('url'),
                    'name': f"Товар {price.get('product_id')}",
                    'category': 'other'
                })

            self.logger.info(f"Данные цикла #{cycle_num} сохранены в базу данных")

        except Exception as e:
            self.logger.error(f"Ошибка сохранения в базу данных: {e}")
            # Продолжаем работу даже если не удалось сохранить в БД

    def log_price_changes(self, changes: list):
        """Логирует изменения цен"""
        if not changes:
            return

        # Фильтруем только реальные изменения
        significant_changes = [
            c for c in changes
            if c['change_status'] in ['increased', 'decreased']
        ]

        if significant_changes:
            print(f"\n{Fore.YELLOW}{'!'*80}")
            print(f"{Fore.YELLOW}🔔 ОБНАРУЖЕНЫ ИЗМЕНЕНИЯ ЦЕН!")
            print(f"{Fore.YELLOW}{'!'*80}{Style.RESET_ALL}")

            for change in significant_changes:
                symbol = "📈" if change['change_status'] == 'increased' else "📉"
                direction = "увеличилась" if change['change_status'] == 'increased' else "уменьшилась"
                color = Fore.RED if change['change_status'] == 'increased' else Fore.GREEN

                print(f"\n{color}{symbol} Товар #{change['product_index']} (ID: {change['product_id']})")
                print(f"   Цена {direction}: {abs(change['change_amount']):.0f} ₽ ({abs(change['change_percentage']):.1f}%)")
                print(f"   Было: {change['previous_price_formatted']}")
                print(f"   Стало: {change['current_price_formatted']}")
                print(f"   Значимость: {change.get('change_significance', 'неопределено')}")
                print(f"   Источник данных: {change.get('source', 'unknown')}{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.GREEN}✓ Изменений цен не обнаружено{Style.RESET_ALL}")

    def print_summary(self, cycle_num: int, current_prices: List[Dict], price_changes: List[Dict]):
        """Печатает сводку по циклу"""
        if not self.last_results or 'stats' not in self.last_results:
            return

        stats = self.last_results['stats']

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"📊 СВОДКА ЦИКЛА #{cycle_num}")
        print(f"{'='*80}{Style.RESET_ALL}")

        print(f"{Fore.WHITE}Всего товаров: {stats['total_products']}")
        print(f"Успешно спарсено: {Fore.GREEN}{stats['successful_parses']}{Fore.WHITE}")
        print(f"Не удалось спарсить: {Fore.RED if stats['failed_parses'] > 0 else Fore.YELLOW}{stats['failed_parses']}{Fore.WHITE}")

        if stats['price_changes'] > 0:
            print(f"Изменений цен: {Fore.YELLOW}{stats['price_changes']}")
            print(f"  Повышений: {Fore.RED}{stats['increased']}")
            print(f"  Понижений: {Fore.GREEN}{stats['decreased']}")
        else:
            print(f"Изменений цен: {Fore.GREEN}нет")

        if stats['new_products'] > 0:
            print(f"Новых товаров: {Fore.BLUE}{stats['new_products']}")

        # Средняя цена
        if current_prices:
            avg_price = sum(p.get('price', 0) for p in current_prices) / len(current_prices)
            print(f"Средняя цена: {Fore.YELLOW}{avg_price:,.0f} ₽".replace(',', ' '))

        # Информация о базе данных
        if self.db_manager and self.db_manager.is_connected:
            print(f"База данных: {Fore.GREEN}активна")
        elif self.db_manager:
            print(f"База данных: {Fore.YELLOW}не подключена")

        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    def cleanup_old_files(self, days_to_keep: int = None):
        """Очищает старые HTML файлы"""
        if days_to_keep is None:
            days_to_keep = self.config_manager.get('auto_cleanup_days', 7)

        self.logger.info(f"Очистка файлов старше {days_to_keep} дней...")
        print(f"{Fore.CYAN}Очистка старых файлов...{Style.RESET_ALL}")

        html_patterns = ["product_*.html"]
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        deleted_count = 0

        for pattern in html_patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
                        deleted_count += 1
                        self.logger.debug(f"Удален: {file_path}")
                except Exception as e:
                    self.logger.warning(f"Не удалось удалить {file_path}: {e}")

        self.logger.info(f"Удалено {deleted_count} старых файлов")
        print(f"{Fore.GREEN}✓ Удалено {deleted_count} старых файлов{Style.RESET_ALL}")

        return deleted_count

    def cleanup_old_database_data(self, days_to_keep: int = 30):
        """Очищает старые данные из базы данных"""
        if not self.db_manager or not self.db_manager.is_connected:
            return

        try:
            self.logger.info(f"Очистка старых данных из базы данных старше {days_to_keep} дней...")

            deleted_count = self.db_manager.cleanup_old_data(days_to_keep)

            if deleted_count > 0:
                self.logger.info(f"Удалено {deleted_count} записей из базы данных")
                print(f"{Fore.GREEN}✓ Удалено {deleted_count} старых записей из базы данных{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Нет старых данных для удаления{Style.RESET_ALL}")

        except Exception as e:
            self.logger.error(f"Ошибка при очистке базы данных: {e}")
            print(f"{Fore.RED}✗ Ошибка при очистке базы данных: {e}{Style.RESET_ALL}")

    def get_last_results(self) -> Optional[Dict[str, Any]]:
        """Возвращает результаты последнего парсинга"""
        return self.last_results

    def get_current_cycle(self) -> int:
        """Возвращает текущий номер цикла"""
        return self.current_cycle

    def get_database_stats(self) -> Dict[str, Any]:
        """Возвращает статистику из базы данных"""
        if not self.db_manager or not self.db_manager.is_connected:
            return {}

        try:
            return self.db_manager.get_dashboard_stats()
        except Exception as e:
            self.logger.error(f"Ошибка получения статистики из базы данных: {e}")
            return {}

    def run_manual_check(self):
        """Запускает ручную проверку (синхронно)"""
        print(f"{Fore.YELLOW}Запуск ручной проверки...{Style.RESET_ALL}")
        self.run_monitoring_cycle()
        print(f"{Fore.GREEN}✓ Ручная проверка завершена{Style.RESET_ALL}")

    def stop_monitoring(self):
        """Останавливает мониторинг"""
        self.is_running = False
        schedule.clear()
        self.logger.info("Мониторинг остановлен")

        # Закрываем соединение с базой данных
        if self.db_manager:
            self.db_manager.close()
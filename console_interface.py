"""
Модуль консольного интерфейса для управления мониторингом с MySQL
"""
import csv
import os
import glob
from datetime import datetime, timedelta
from colorama import Fore, Style


class ConsoleInterface:
    """Класс консольного интерфейса с поддержкой MySQL"""

    def __init__(self, config_manager, url_manager, price_monitor, db_manager=None):
        self.config_manager = config_manager
        self.url_manager = url_manager
        self.price_monitor = price_monitor
        self.db_manager = db_manager

        # Импортируем DatabaseConsole здесь, а не вверху файла
        from database import DatabaseConsole
        self.db_console = DatabaseConsole(db_manager) if db_manager else None

    def run(self):
        """Запускает главное меню"""
        while True:
            self.display_main_menu()
            choice = input(f"\n{Fore.GREEN}Выберите действие: {Style.RESET_ALL}")

            if choice == '1':
                self.display_current_prices()
            elif choice == '2':
                self.add_product()
            elif choice == '3':
                self.remove_product()
            elif choice == '4':
                self.display_all_products()
            elif choice == '5':
                self.run_manual_check()
            elif choice == '6':
                self.export_to_excel()
            elif choice == '7':
                self.cleanup_files()
            elif choice == '8':
                self.display_price_history()
            elif choice == '9':
                self.display_statistics()
            elif choice == '10':
                self.display_configuration()
            elif choice == '11' and self.db_console:
                self.db_console.run()
            elif choice == '0':
                print(f"{Fore.YELLOW}Выход из программы...{Style.RESET_ALL}")
                self.price_monitor.stop_monitoring()
                if self.db_manager:
                    self.db_manager.close()
                break
            else:
                print(f"{Fore.RED}Неверный выбор{Style.RESET_ALL}")

            if choice != '0':
                input(f"\n{Fore.CYAN}Нажмите Enter чтобы продолжить...{Style.RESET_ALL}")

    def display_main_menu(self):
        """Отображает главное меню"""
        print(f"\n{Fore.MAGENTA}{'═'*70}")
        print(f"{'МОНИТОРИНГ ЦЕН OZON':^70}")
        print(f"{'═'*70}{Style.RESET_ALL}")

        print(f"{Fore.CYAN}1.{Style.RESET_ALL} Показать текущие цены")
        print(f"{Fore.CYAN}2.{Style.RESET_ALL} Добавить товар для отслеживания")
        print(f"{Fore.CYAN}3.{Style.RESET_ALL} Удалить товар из отслеживания")
        print(f"{Fore.CYAN}4.{Style.RESET_ALL} Показать список отслеживаемых товаров")
        print(f"{Fore.CYAN}5.{Style.RESET_ALL} Запустить проверку сейчас")
        print(f"{Fore.CYAN}6.{Style.RESET_ALL} Экспорт данных в Excel")
        print(f"{Fore.CYAN}7.{Style.RESET_ALL} Очистить старые файлы")
        print(f"{Fore.CYAN}8.{Style.RESET_ALL} Показать историю изменений цен")
        print(f"{Fore.CYAN}9.{Style.RESET_ALL} Статистика мониторинга")
        print(f"{Fore.CYAN}10.{Style.RESET_ALL} Настройки конфигурации")

        if self.db_console:
            print(f"{Fore.CYAN}11.{Style.RESET_ALL} Управление базой данных {Fore.GREEN}✓{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}11.{Style.RESET_ALL} Управление базой данных {Fore.RED}(недоступно){Style.RESET_ALL}")

        print(f"{Fore.YELLOW}0.{Style.RESET_ALL} Выход")

        print(f"{Fore.MAGENTA}{'═'*70}{Style.RESET_ALL}")

        print(f"{Fore.WHITE}Текущий цикл: {self.price_monitor.get_current_cycle()}")
        print(f"Товаров отслеживается: {self.url_manager.get_page_count()}")
        if self.db_manager:
            print(f"База данных: {Fore.GREEN}Подключена{Style.RESET_ALL}")
        else:
            print(f"База данных: {Fore.YELLOW}Не используется{Style.RESET_ALL}")

    # Остальные методы оставляем без изменений
    def display_current_prices(self):
        """Показывает текущие цены"""
        last_results = self.price_monitor.get_last_results()

        print(f"\n{Fore.CYAN}{'='*80}")
        print("ТЕКУЩИЕ ЦЕНЫ")
        print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*80}{Style.RESET_ALL}")

        if last_results and 'prices' in last_results:
            for price in sorted(last_results['prices'], key=lambda x: x.get('index', 0)):
                status_color = Fore.WHITE
                if 'changes' in last_results:
                    for change in last_results['changes']:
                        if change['product_id'] == price['product_id']:
                            if change['change_status'] == 'increased':
                                status_color = Fore.RED
                            elif change['change_status'] == 'decreased':
                                status_color = Fore.GREEN
                            elif change['change_status'] == 'new':
                                status_color = Fore.BLUE
                            break

                print(f"{Fore.WHITE}#{price.get('index', 'N/A'):<3} | "
                      f"{status_color}{price.get('product_id', 'unknown')[:15]:<15} | "
                      f"{status_color}{price.get('price_formatted', 'N/A'):<15} | "
                      f"{Fore.WHITE}{price.get('timestamp', 'N/A')}")
        else:
            print(f"{Fore.YELLOW}Нет данных о текущих ценах{Style.RESET_ALL}")

        # Показываем статистику
        if last_results and 'stats' in last_results:
            stats = last_results['stats']
            print(f"{Fore.CYAN}{'='*80}")
            print(f"📊 СТАТИСТИКА: Всего товаров: {stats.get('total_products', 0)} | "
                  f"Успешно спарсено: {stats.get('successful_parses', 0)} | "
                  f"Изменений: {stats.get('price_changes', 0)}")
            print(f"{'='*80}{Style.RESET_ALL}")

    def add_product(self):
        """Добавляет новый товар"""
        url = input(f"{Fore.CYAN}Введите URL товара Ozon: {Style.RESET_ALL}")
        if self.url_manager.add_page(url):
            print(f"{Fore.GREEN}✓ Товар успешно добавлен!{Style.RESET_ALL}")
            print(f"ID товара: {self.url_manager.extract_product_id(url)}")
            print(f"Всего товаров: {self.url_manager.get_page_count()}")
        else:
            print(f"{Fore.RED}✗ Не удалось добавить товар{Style.RESET_ALL}")

    def remove_product(self):
        """Удаляет товар"""
        self.display_all_products()
        pages = self.url_manager.get_pages()

        if not pages:
            print(f"{Fore.YELLOW}Нет товаров для удаления{Style.RESET_ALL}")
            return

        try:
            index = int(input(f"{Fore.CYAN}Введите номер товара для удаления: {Style.RESET_ALL}"))
            if 1 <= index <= len(pages):
                if self.url_manager.remove_page_by_index(index - 1):
                    print(f"{Fore.GREEN}✓ Товар успешно удален!{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}✗ Не удалось удалить товар{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Неверный номер товара{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Некорректный ввод{Style.RESET_ALL}")

    def display_all_products(self):
        """Показывает все отслеживаемые товары"""
        pages = self.url_manager.get_pages()

        if not pages:
            print(f"{Fore.YELLOW}Нет товаров для отслеживания.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'ОТСЛЕЖИВАЕМЫЕ ТОВАРЫ':^80}")
        print(f"{'='*80}{Style.RESET_ALL}")

        for i, url in enumerate(pages, 1):
            product_id = self.url_manager.extract_product_id(url)
            print(f"{Fore.WHITE}{i:>3}. {Fore.CYAN}{product_id[:15]:<15} "
                  f"{Fore.WHITE}| {url[:60]}...")

        print(f"{Fore.CYAN}{'='*80}")
        print(f"Всего товаров: {len(pages)}{Style.RESET_ALL}")

    def run_manual_check(self):
        """Запускает ручную проверку"""
        print(f"{Fore.YELLOW}Запуск проверки...{Style.RESET_ALL}")
        # Создаем новый поток для проверки
        import threading

        def run_check():
            self.price_monitor.run_manual_check()

        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()
        print(f"{Fore.GREEN}✓ Проверка запущена в фоновом режиме{Style.RESET_ALL}")

    def export_to_excel(self):
        """Экспортирует данные в Excel"""
        from price_history import PriceHistory
        history = PriceHistory()
        filename = history.export_to_excel()

        if filename:
            print(f"{Fore.GREEN}✓ Данные экспортированы в {filename}{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Не удалось экспортировать данные{Style.RESET_ALL}")

    def cleanup_files(self):
        """Очищает старые файлы"""
        days = input(f"{Fore.CYAN}Удалить файлы старше скольки дней? (по умолчанию 7): {Style.RESET_ALL}")
        try:
            days = int(days) if days else 7
            self.price_monitor.cleanup_old_files(days)
            print(f"{Fore.GREEN}✓ Очистка выполнена{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Некорректное количество дней{Style.RESET_ALL}")

    def display_price_history(self):
        """Показывает историю изменений цен"""
        changes_file = "price_changes.csv"

        if not os.path.exists(changes_file):
            print(f"{Fore.YELLOW}Файл истории изменений пока не создан.{Style.RESET_ALL}")
            return

        try:
            print(f"\n{Fore.CYAN}{'='*100}")
            print(f"{'ИСТОРИЯ ИЗМЕНЕНИЙ ЦЕН':^100}")
            print(f"{'='*100}{Style.RESET_ALL}")

            with open(changes_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')
                headers = next(reader)

                print(f"{Fore.YELLOW}{' | '.join(headers[:7]):<80}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}{'-'*100}{Style.RESET_ALL}")

                rows = list(reader)
                for row in rows[-20:]:  # Последние 20 записей
                    if len(row) >= 8:
                        status = row[8]
                        status_color = (Fore.RED if status == 'increased'
                                      else Fore.GREEN if status == 'decreased'
                                      else Fore.WHITE)
                        print(f"{Fore.WHITE}{row[0]:<20} | {row[1]:<4} | {row[2]:<15} | "
                              f"{row[3]:<4} | {Fore.YELLOW}{row[4]:<10} | {row[5]:<10} | "
                              f"{status_color}{row[6]:<15}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Ошибка при чтении истории: {e}{Style.RESET_ALL}")

    def display_statistics(self):
        """Показывает статистику мониторинга"""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'СТАТИСТИКА МОНИТОРИНГА':^80}")
        print(f"{'='*80}{Style.RESET_ALL}")

        print(f"{Fore.WHITE}Всего товаров в мониторинге:{Fore.YELLOW} {self.url_manager.get_page_count()}")
        print(f"{Fore.WHITE}Текущий цикл:{Fore.YELLOW} {self.price_monitor.get_current_cycle()}")

        last_results = self.price_monitor.get_last_results()
        if last_results:
            stats = last_results.get('stats', {})
            print(f"{Fore.WHITE}Успешно спарсено в последнем цикле:{Fore.YELLOW} {stats.get('successful_parses', 0)}")
            print(f"{Fore.WHITE}Изменений цен обнаружено:{Fore.YELLOW} {stats.get('price_changes', 0)}")

        # Размеры файлов
        files_info = [
            ("price_history.json", "История цен"),
            ("price_changes.csv", "Изменения цен"),
            ("target_pages.json", "Список товаров"),
            ("config.json", "Конфигурация")
        ]

        for filename, description in files_info:
            if os.path.exists(filename):
                size = os.path.getsize(filename)
                print(f"{Fore.WHITE}{description}:{Fore.YELLOW} {size / 1024:.1f} KB")

        # HTML файлы
        html_files = glob.glob("product_*.html")
        print(f"{Fore.WHITE}Сохраненных HTML файлов:{Fore.YELLOW} {len(html_files)}")

        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")

    def display_configuration(self):
        """Показывает и редактирует конфигурацию"""
        config = self.config_manager.config

        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"{'НАСТРОЙКИ КОНФИГУРАЦИИ':^80}")
        print(f"{'='*80}{Style.RESET_ALL}")

        for key, value in config.items():
            print(f"{Fore.WHITE}{key}:{Fore.YELLOW} {value}")

        print(f"\n{Fore.CYAN}Редактировать настройки? (y/n): {Style.RESET_ALL}")
        choice = input().lower()

        if choice == 'y':
            print(f"{Fore.YELLOW}Введите название параметра для изменения: {Style.RESET_ALL}")
            param = input()

            if param in config:
                print(f"{Fore.YELLOW}Текущее значение: {config[param]}")
                print(f"Новое значение: {Style.RESET_ALL}")
                new_value = input()

                # Преобразуем тип значения
                if isinstance(config[param], bool):
                    new_value = new_value.lower() in ('true', '1', 'yes', 'y')
                elif isinstance(config[param], int):
                    try:
                        new_value = int(new_value)
                    except:
                        print(f"{Fore.RED}Некорректное значение{Style.RESET_ALL}")
                        return
                elif isinstance(config[param], float):
                    try:
                        new_value = float(new_value)
                    except:
                        print(f"{Fore.RED}Некорректное значение{Style.RESET_ALL}")
                        return

                self.config_manager.set(param, new_value)
                print(f"{Fore.GREEN}✓ Параметр обновлен{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Параметр не найден{Style.RESET_ALL}")
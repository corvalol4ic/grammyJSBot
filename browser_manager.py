"""
Модуль для управления браузером и запросами с поддержкой headless режима
"""
import time
import random
import json
import logging
from curl_cffi import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class BrowserManager:
    """Класс для управления браузером и HTTP-запросами с headless режимом"""

    def __init__(self, headless=True):
        """
        Инициализация менеджера браузера

        Args:
            headless: Запускать ли браузер в headless режиме (без GUI)
        """
        self.headless = headless
        self.driver = None

    def get_cookies(self, use_headless=None):
        """
        Получает cookies с использованием браузера

        Args:
            use_headless: Переопределить настройку headless (если None - использовать self.headless)

        Returns:
            dict: Данные браузера или None в случае ошибки
        """
        if use_headless is None:
            use_headless = self.headless

        driver = None
        try:
            # Настройка опций Chrome
            chrome_options = Options()

            # Включаем headless режим если нужно
            if use_headless:
                chrome_options.add_argument("--headless=new")  # Новый headless режим Chrome
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                logger.info("Используется headless режим браузера")

            # Опции для маскировки и улучшения производительности
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Добавляем пользовательский user-agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            # Отключаем индикатор автоматизации
            chrome_options.add_argument("--disable-blink-features")

            # Другие полезные опции для headless режима
            chrome_options.add_argument("--disable-gpu")  # Ускорение для headless
            chrome_options.add_argument("--window-size=1920,1080")  # Размер окна

            # Опции для ускорения и экономии ресурсов
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-notifications")

            # Отключаем изображения для ускорения (опционально)
            if use_headless:
                prefs = {
                    "profile.managed_default_content_settings.images": 2,  # 2 = Блокировать
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_setting_values.javascript": 1,  # 1 = Разрешить
                }
                chrome_options.add_experimental_option("prefs", prefs)

            # Используем WebDriver Manager для автоматической установки драйвера
            service = Service(ChromeDriverManager().install())

            # Создаем драйвер
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # Выполняем скрипты для маскировки
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })

            # Открываем Ozon
            logger.info("Открываем Ozon для получения cookies...")
            driver.get("https://www.ozon.ru")

            # Ждем загрузки (меньше времени для headless)
            wait_time = 3 if use_headless else 5
            time.sleep(wait_time)

            # Для headless режима эмулируем прокрутку
            if use_headless:
                driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(0.5)
                driver.execute_script("window.scrollTo(0, 600);")
                time.sleep(0.5)
            else:
                # Для GUI режима обычная прокрутка
                driver.execute_script("window.scrollTo(0, 300);")
                time.sleep(1)
                driver.execute_script("window.scrollTo(0, 600);")
                time.sleep(1)

            # Получаем данные
            user_agent = driver.execute_script("return navigator.userAgent")
            cookies = driver.get_cookies()
            accept_language = driver.execute_script("return navigator.language || navigator.userLanguage")
            platform = driver.execute_script("return navigator.platform")

            # Преобразуем cookies в словарь
            cookies_dict = {}
            for cookie in cookies:
                cookies_dict[cookie['name']] = cookie['value']

            browser_data = {
                "user_agent": user_agent,
                "accept_language": accept_language or "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "platform": platform or "Win32",
                "cookies": cookies_dict,
                "viewport": driver.execute_script("return {width: window.innerWidth, height: window.innerHeight}"),
                "headless": use_headless
            }

            logger.info(f"Cookies получены: {len(cookies_dict)} шт. (headless: {use_headless})")
            return browser_data

        except Exception as e:
            logger.error(f"Ошибка при получении cookies (headless={use_headless}): {str(e)}")

            # Пробуем получить cookies без браузера
            if use_headless:
                logger.info("Пробуем получить cookies без браузера...")
                return self.get_fallback_cookies()
            else:
                # Если не сработал GUI режим, пробуем headless
                logger.info("Пробуем headless режим...")
                return self.get_cookies(use_headless=True)

        finally:
            if driver:
                try:
                    driver.quit()
                    logger.debug("Браузер закрыт")
                except:
                    pass

    def get_fallback_cookies(self):
        """Возвращает стандартные cookies если браузер не работает"""
        logger.info("Используем стандартные cookies")
        return {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "accept_language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "platform": "Win32",
            "cookies": {
                "__Secure-refresh_token": "dummy_token",
                "csrf_token": "dummy_csrf",
                "sessionid": "dummy_session",
            },
            "viewport": {"width": 1920, "height": 1080},
            "headless": True
        }

    def close_browser(self):
        """Закрывает браузер если он открыт"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Браузер закрыт")
            except:
                pass
            self.driver = None

    def generate_headers(self, browser_data):
        """Генерация реалистичных заголовков"""
        user_agent = browser_data.get("user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

        accept_language = browser_data.get("accept_language", "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7")

        headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": accept_language,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
            "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "DNT": "1",
            "Referer": "https://www.ozon.ru/",
        }

        return headers

    def make_request(self, url, cookies_dict, headers, max_retries=3):
        """Выполняет запрос с повторными попытками"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = random.uniform(3, 8)
                    logger.debug(f"Повторная попытка {attempt + 1} через {delay:.1f} сек")
                    time.sleep(delay)

                # Меняем заголовки для каждой попытки
                current_headers = headers.copy()
                if attempt > 0:
                    current_headers["Cache-Control"] = "no-cache"
                    current_headers["Pragma"] = "no-cache"
                    # Немного меняем User-Agent
                    if attempt == 1:
                        current_headers["User-Agent"] = current_headers["User-Agent"].replace("Chrome/120", "Chrome/121")

                logger.debug(f"Запрос к {url} (попытка {attempt + 1})")

                # Используем curl_cffi с имитацией браузера
                response = requests.get(
                    url,
                    cookies=cookies_dict,
                    headers=current_headers,
                    timeout=30,
                    impersonate="chrome110"
                )

                logger.debug(f"Статус ответа: {response.status_code}")

                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    logger.warning(f"Получен 403 Forbidden для {url}")
                    continue
                elif response.status_code == 429:
                    logger.warning("Слишком много запросов, ждем...")
                    time.sleep(15)
                    continue
                elif response.status_code == 404:
                    logger.error(f"Страница не найдена: {url}")
                    return response

            except requests.exceptions.Timeout:
                logger.warning(f"Таймаут запроса к {url}")
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"Ошибка запроса: {str(e)}")
                continue
            except Exception as e:
                logger.error(f"Неожиданная ошибка: {str(e)}")
                continue

        logger.error(f"Все попытки запроса к {url} не удались")
        return None
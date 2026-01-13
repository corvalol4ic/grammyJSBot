"""
Модуль для парсинга HTML и извлечения цен
"""
import json
import re
from bs4 import BeautifulSoup


class HTMLParser:
    """Класс для парсинга HTML и извлечения данных"""

    def extract_price(self, html_content: str, url: str) -> dict:
        """Извлекает цену из HTML содержимого"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # 1. Пытаемся найти в JSON-LD данных
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if 'offers' in data and 'price' in data['offers']:
                            price = data['offers']['price']
                            return {
                                'price': float(price),
                                'price_formatted': self.format_price(price),
                                'source': 'json-ld',
                                'currency': data['offers'].get('priceCurrency', 'RUB')
                            }
                        elif 'mainEntity' in data and 'offers' in data['mainEntity']:
                            if 'price' in data['mainEntity']['offers']:
                                price = data['mainEntity']['offers']['price']
                                return {
                                    'price': float(price),
                                    'price_formatted': self.format_price(price),
                                    'source': 'json-ld-main',
                                    'currency': data['mainEntity']['offers'].get('priceCurrency', 'RUB')
                                }
                except:
                    continue

            # 2. Ищем в script тегах с данными
            scripts = soup.find_all('script')
            price_patterns = [
                r'"price"\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?',
                r'"finalPrice"\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?',
                r'"value"\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?\s*,\s*"currency"',
                r'\\"price\\"\s*:\s*\\"(\d+(?:\.\d+)?)\\"',
                r'currentPrice.*?(\d+(?:\.\d+)?)',
            ]

            for script in scripts:
                if script.string:
                    script_text = script.string
                    for pattern in price_patterns:
                        matches = re.search(pattern, script_text, re.IGNORECASE)
                        if matches:
                            try:
                                price = float(matches.group(1))
                                if price > 10:
                                    return {
                                        'price': price,
                                        'price_formatted': self.format_price(price),
                                        'source': 'script-regex',
                                        'currency': 'RUB'
                                    }
                            except:
                                continue

            # 3. Ищем по селекторам классов Ozon
            selectors = [
                '[data-widget="webPrice"]',
                '.ui-p9',
                '.q9k1',
                '.l9k1',
                '.s9k1',
                '.ui-q1',
                '[class*="price"]',
                '[class*="Price"]',
                'span[data-widget="webPrice"]',
                'div[data-widget="webPrice"]',
            ]

            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    price_match = re.search(r'(\d[\d\s]*)\s*[₽ррубRUB]', text, re.IGNORECASE)
                    if price_match:
                        try:
                            price_str = price_match.group(1).replace(' ', '').replace('\xa0', '')
                            price = float(price_str)
                            if price > 10:
                                return {
                                    'price': price,
                                    'price_formatted': self.format_price(price),
                                    'source': f'selector: {selector[:30]}',
                                    'currency': 'RUB'
                                }
                        except:
                            continue

            # 4. Ищем по всему HTML
            html_text = soup.get_text()
            html_price_patterns = [
                r'(\d[\d\s]{3,})\s*₽',
                r'цена\D*(\d[\d\s]*)',
                r'стоимость\D*(\d[\d\s]*)',
                r'(\d+)\s*рубл',
                r'руб\D*(\d[\d\s]*)',
            ]

            for pattern in html_price_patterns:
                matches = re.search(pattern, html_text, re.IGNORECASE)
                if matches:
                    try:
                        price_str = matches.group(1).replace(' ', '').replace('\xa0', '')
                        price = float(price_str)
                        if price > 10:
                            return {
                                'price': price,
                                'price_formatted': self.format_price(price),
                                'source': 'html-regex',
                                'currency': 'RUB'
                            }
                    except:
                        continue

            # 5. Ищем в атрибутах data-*
            for tag in soup.find_all(attrs={"data-price": True}):
                try:
                    price = float(tag['data-price'])
                    if price > 10:
                        return {
                            'price': price,
                            'price_formatted': self.format_price(price),
                            'source': 'data-attribute',
                            'currency': 'RUB'
                        }
                except:
                    continue

            return None

        except Exception as e:
            print(f"Ошибка при извлечении цены: {e}")
            return None

    def format_price(self, price):
        """Форматирует цену для отображения"""
        try:
            price_num = float(price)
            return f"{price_num:,.0f} ₽".replace(',', ' ')
        except:
            return str(price)
"""
Модуль для управления списком отслеживаемых товаров
"""
import json
import os
import re
import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse


class URLManager:
    """Класс для управления списком URL товаров"""

    def __init__(self, pages_file="target_pages.json"):
        self.pages_file = pages_file
        self.pages = self.load_pages()

    def load_pages(self) -> List[str]:
        """Загружает список страниц из файла"""
        default_pages = [
            'https://www.ozon.ru/product/kostyum-sportivnyy-2214535916/',
            'https://www.ozon.ru/product/komplekt-odezhdy-2361803914/',
            'https://www.ozon.ru/product/futbolka-interesnaya-futbolka-s-izobrazheniem-kosmonavta-i-koshki-2080842787/'
        ]

        if os.path.exists(self.pages_file):
            try:
                with open(self.pages_file, "r", encoding="utf-8") as f:
                    pages_data = json.load(f)
                    return pages_data.get("pages", default_pages)
            except Exception as e:
                print(f"Ошибка загрузки страниц: {e}")

        self.save_pages(default_pages)
        return default_pages

    def save_pages(self, pages: List[str] = None) -> None:
        """Сохраняет список страниц в файл"""
        if pages is None:
            pages = self.pages

        data = {
            "pages": pages,
            "last_updated": self._get_current_timestamp(),
            "total_pages": len(pages)
        }

        try:
            with open(self.pages_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения страниц: {e}")

    def normalize_url(self, url: str) -> str:
        """Нормализует URL для Ozon"""
        url = url.strip()

        # Удаляем мобильную версию если есть
        url = url.replace('m.ozon.ru', 'www.ozon.ru')
        url = url.replace('ozon.ru', 'www.ozon.ru')

        # Добавляем протокол если нет
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Убедимся что это www.ozon.ru
        if not url.startswith('https://www.ozon.ru'):
            if 'ozon.ru' in url:
                url = url.replace('http://', 'https://')
                if not url.startswith('https://www.'):
                    url = url.replace('https://', 'https://www.')

        # Удаляем лишние параметры
        if '?' in url:
            url = url.split('?')[0]

        # Убедимся что URL заканчивается на /
        if not url.endswith('/'):
            url += '/'

        return url

    def extract_product_id(self, url: str) -> str:
        """Извлекает ID продукта из URL"""
        try:
            parts = url.rstrip('/').split('/')
            for part in reversed(parts):
                if part.isdigit() and len(part) > 6:
                    return part
            return hashlib.md5(url.encode()).hexdigest()[:10]
        except:
            return "unknown"

    def add_page(self, url: str) -> bool:
        """Добавляет новую страницу в список мониторинга"""
        normalized_url = self.normalize_url(url)

        # Проверяем дубликаты
        if normalized_url in self.pages:
            print(f"Страница уже в списке: {normalized_url}")
            return False

        # Проверяем что это URL товара Ozon
        if '/product/' not in normalized_url:
            print(f"URL не является страницей товара Ozon: {normalized_url}")
            return False

        # Добавляем в список
        self.pages.append(normalized_url)
        self.save_pages()
        return True

    def remove_page(self, url: str) -> bool:
        """Удаляет страницу из списка мониторинга"""
        if url in self.pages:
            self.pages.remove(url)
            self.save_pages()
            return True
        return False

    def remove_page_by_index(self, index: int) -> bool:
        """Удаляет страницу по индексу"""
        if 0 <= index < len(self.pages):
            self.pages.pop(index)
            self.save_pages()
            return True
        return False

    def get_pages(self) -> List[str]:
        """Возвращает список страниц"""
        return self.pages.copy()

    def get_page_count(self) -> int:
        """Возвращает количество страниц"""
        return len(self.pages)

    def get_page_info(self, index: int) -> Dict[str, Any]:
        """Возвращает информацию о странице по индексу"""
        if 0 <= index < len(self.pages):
            url = self.pages[index]
            return {
                'index': index + 1,
                'url': url,
                'product_id': self.extract_product_id(url),
                'short_url': url[:60] + '...' if len(url) > 60 else url
            }
        return {}

    def _get_current_timestamp(self) -> str:
        """Возвращает текущую временную метку"""
        from datetime import datetime
        return datetime.now().isoformat()
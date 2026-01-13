"""
Модуль для управления историей цен
"""
import json
import os
import pandas as pd
from typing import List, Dict, Any


class PriceHistory:
    """Класс для управления историей цен"""

    def __init__(self, history_file="price_history.json"):
        self.history_file = history_file
        self.history = self.load_history()

    def load_history(self) -> Dict[str, Any]:
        """Загружает историю цен из файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"history": [], "last_cycle": 0}
        return {"history": [], "last_cycle": 0}

    def save_history(self, history_data: Dict[str, Any] = None) -> None:
        """Сохраняет историю цен в файл"""
        if history_data is None:
            history_data = self.history

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения истории: {e}")

    def save_prices(self, prices: List[Dict[str, Any]], cycle_num: int) -> None:
        """Сохраняет цены в историю"""
        if not prices:
            return

        self.history.setdefault("history", []).extend(prices)
        self.history["last_cycle"] = cycle_num
        self.history["last_update"] = self._get_current_timestamp()
        self.save_history()

    def get_previous_prices(self, current_prices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Возвращает предыдущие цены для сравнения"""
        if not self.history or 'history' not in self.history:
            return []

        # Исключаем текущие цены из истории
        all_history = self.history.get('history', [])
        if len(all_history) <= len(current_prices):
            return []

        return all_history[:-len(current_prices)]

    def get_recent_prices(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Возвращает последние записи истории"""
        if not self.history or 'history' not in self.history:
            return []

        return self.history.get('history', [])[-limit:]

    def get_product_history(self, product_id: str) -> List[Dict[str, Any]]:
        """Возвращает историю цен для конкретного товара"""
        if not self.history or 'history' not in self.history:
            return []

        return [
            entry for entry in self.history.get('history', [])
            if entry.get('product_id') == product_id
        ]

    def export_to_excel(self) -> str:
        """Экспортирует историю цен в Excel"""
        try:
            if not self.history or 'history' not in self.history or not self.history['history']:
                return None

            # Создаем DataFrame
            df = pd.DataFrame(self.history['history'])

            # Сохраняем в Excel
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"price_history_export_{timestamp}.xlsx"

            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='История цен', index=False)

                # Создаем сводный лист
                if 'product_id' in df.columns and 'price' in df.columns:
                    summary = df.groupby('product_id').agg({
                        'price': ['min', 'max', 'last'],
                        'timestamp': 'count'
                    }).round(2)
                    summary.to_excel(writer, sheet_name='Сводка')

            return filename

        except Exception as e:
            print(f"Ошибка при экспорте в Excel: {e}")
            return None

    def _get_current_timestamp(self) -> str:
        """Возвращает текущую временную метку"""
        from datetime import datetime
        return datetime.now().isoformat()
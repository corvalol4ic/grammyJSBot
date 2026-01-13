"""
Модуль для сравнения цен и обнаружения изменений
"""
import csv
import os
from typing import List, Dict, Any, Optional


class PriceComparator:
    """Класс для сравнения цен и обнаружения изменений"""

    def __init__(self, changes_file="price_changes.csv"):
        self.changes_file = changes_file

    def compare_prices(self, current_prices: List[Dict[str, Any]],
                       previous_prices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Сравнивает текущие цены с предыдущими"""
        changes = []

        for current_price in current_prices:
            product_id = current_price['product_id']
            current_value = current_price.get('price')

            # Ищем предыдущую цену
            previous_price = self._find_previous_price(product_id, previous_prices)

            change_info = self._create_change_info(
                current_price, previous_price, current_value
            )

            changes.append(change_info)

        # Сохраняем изменения в CSV
        self.save_changes_to_csv(changes)

        return changes

    def _find_previous_price(self, product_id: str,
                             previous_prices: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Находит предыдущую цену для товара"""
        if not previous_prices:
            return None

        previous_entries = [
            p for p in previous_prices
            if p.get('product_id') == product_id and p.get('price') is not None
        ]

        if previous_entries:
            previous_entries.sort(key=lambda x: x.get('timestamp_iso', ''), reverse=True)
            return previous_entries[0]

        return None

    def _create_change_info(self, current_price: Dict[str, Any],
                            previous_price: Optional[Dict[str, Any]],
                            current_value: float) -> Dict[str, Any]:
        """Создает информацию об изменении цены"""
        change_info = {
            'product_id': current_price['product_id'],
            'product_index': current_price['index'],
            'url': current_price['url'],
            'current_price': current_value,
            'current_price_formatted': current_price['price_formatted'],
            'previous_price': previous_price.get('price') if previous_price else None,
            'previous_price_formatted': previous_price.get('price_formatted', 'Нет данных')
            if previous_price else 'Нет данных',
            'change_amount': None,
            'change_percentage': None,
            'change_status': 'new' if not previous_price else 'no_change',
            'timestamp': current_price['timestamp'],
            'cycle': current_price.get('cycle', 0),
            'source': current_price.get('source', 'unknown')
        }

        # Если есть обе цены
        if current_value is not None and previous_price and previous_price.get('price') is not None:
            prev_value = previous_price['price']

            if abs(current_value - prev_value) > 0.99:  # Более 1 рубля разницы
                change_amount = current_value - prev_value
                change_percentage = (change_amount / prev_value) * 100

                change_info['change_amount'] = change_amount
                change_info['change_percentage'] = change_percentage

                if abs(change_percentage) < 0.1:  # Менее 0.1% - без изменений
                    change_info['change_status'] = 'no_change'
                else:
                    change_info['change_status'] = 'increased' if change_amount > 0 else 'decreased'
                    change_info['change_significance'] = self._get_change_significance(change_percentage)

        return change_info

    def _get_change_significance(self, percentage: float) -> str:
        """Определяет значимость изменения цены"""
        abs_percentage = abs(percentage)
        if abs_percentage < 1:
            return "незначительное"
        elif abs_percentage < 5:
            return "небольшое"
        elif abs_percentage < 10:
            return "среднее"
        elif abs_percentage < 20:
            return "значительное"
        else:
            return "очень значительное"

    def save_changes_to_csv(self, changes: List[Dict[str, Any]]) -> None:
        """Сохраняет изменения в CSV"""
        file_exists = os.path.exists(self.changes_file)

        try:
            with open(self.changes_file, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')

                if not file_exists:
                    writer.writerow([
                        'timestamp', 'cycle', 'product_id', 'product_index',
                        'current_price', 'previous_price', 'change_amount',
                        'change_percentage', 'change_status', 'significance', 'url'
                    ])

                for change in changes:
                    writer.writerow([
                        change['timestamp'],
                        change['cycle'],
                        change['product_id'],
                        change['product_index'],
                        change['current_price'] if change['current_price'] else '',
                        change['previous_price'] if change['previous_price'] else '',
                        f"{change['change_amount']:.2f}" if change['change_amount'] else '',
                        f"{change['change_percentage']:.2f}" if change['change_percentage'] else '',
                        change['change_status'],
                        change.get('change_significance', ''),
                        change['url']
                    ])
        except Exception as e:
            print(f"Ошибка при сохранении изменений в CSV: {e}")
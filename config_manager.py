"""
Модуль для управления конфигурацией приложения с настройкой headless режима
"""
import json
import os
from typing import Dict, Any


class ConfigManager:
    """Класс для управления конфигурацией приложения"""

    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        default_config = {
            "monitoring_interval_minutes": 5,
            "request_timeout": 30,
            "max_retries": 3,
            "random_delay_between_requests": True,
            "min_delay": 3,
            "max_delay": 7,
            "save_html_pages": True,
            "browser_headless": True,  # По умолчанию включен headless режим!
            "notification_threshold_percent": 1.0,
            "auto_cleanup_days": 30,
            "browser_use_proxy": False,
            "browser_disable_images": True,  # Отключаем изображения в headless режиме
            "browser_window_width": 1920,
            "browser_window_height": 1080
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")

        # Сохраняем обновленную конфигурацию
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Сохраняет конфигурацию в файл"""
        if config is None:
            config = self.config

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    def get(self, key: str, default=None) -> Any:
        """Получает значение конфигурации по ключу"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Устанавливает значение конфигурации"""
        self.config[key] = value
        self.save_config()

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Обновляет конфигурацию"""
        self.config.update(new_config)
        self.save_config()

    def get_monitoring_interval(self) -> int:
        """Возвращает интервал мониторинга в минутах"""
        return self.get("monitoring_interval_minutes", 5)

    def is_headless_enabled(self) -> bool:
        """Проверяет включен ли headless режим"""
        return self.get("browser_headless", True)
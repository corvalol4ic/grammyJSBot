"""
Модуль для управления конфигурацией базы данных
"""
import json
import os
from typing import Dict, Any


class DBConfigManager:
    """Класс для управления конфигурацией базы данных"""

    def __init__(self, config_file="database_config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию базы данных"""
        default_config = {
            "database": {
                "host": "localhost",
                "user": "root",
                "password": "",
                "database": "price_monitor"
            },
            "monitoring": {
                "save_to_database": True,
                "save_html_pages": False,
                "cleanup_days": 30,
                "optimize_tables": True
            }
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации БД: {e}")

        # Сохраняем обновленную конфигурацию
        self.save_config(default_config)
        return default_config

    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Сохраняет конфигурацию базы данных"""
        if config is None:
            config = self.config

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации БД: {e}")

    def get_database_config(self) -> Dict[str, str]:
        """Возвращает конфигурацию подключения к БД"""
        return self.config.get("database", {})

    def get_monitoring_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию мониторинга"""
        return self.config.get("monitoring", {})

    def update_database_config(self, new_config: Dict[str, str]) -> None:
        """Обновляет конфигурацию подключения к БД"""
        if "database" not in self.config:
            self.config["database"] = {}

        self.config["database"].update(new_config)
        self.save_config()
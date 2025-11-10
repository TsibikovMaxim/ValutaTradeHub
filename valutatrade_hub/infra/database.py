"""Singleton для работы с JSON-хранилищем."""

import json
import os
from typing import Any


class DatabaseManager:
    """Singleton для управления JSON-файлами."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def read_json(self, filepath: str) -> Any:
        """Читает данные из JSON-файла."""
        if not os.path.exists(filepath):
            return [] if filepath.endswith(("users.json", "portfolios.json", "exchange_rates.json")) else {"pairs": {}, "last_refresh": None}

        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def write_json(self, filepath: str, data: Any):
        """Записывает данные в JSON-файл атомарно."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        temp_filepath = filepath + ".tmp"

        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        os.replace(temp_filepath, filepath)

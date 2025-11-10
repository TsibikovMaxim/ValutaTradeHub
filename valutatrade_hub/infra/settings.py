"""Singleton для управления настройками проекта."""

import os


class SettingsLoader:
    """Singleton для загрузки и кеширования конфигурации."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.data_dir = os.getenv("DATA_DIR", "data")
        self.users_file = os.path.join(self.data_dir, "users.json")
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self.rates_file = os.path.join(self.data_dir, "rates.json")
        self.exchange_rates_file = os.path.join(
            self.data_dir, "exchange_rates.json"
        )

        self.rates_ttl_seconds = int(os.getenv("RATES_TTL_SECONDS", 300))

        self.default_base_currency = os.getenv("BASE_CURRENCY", "USD")

        self.log_file = os.getenv("LOG_FILE", "logs/actions.log")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        self._initialized = True

    def get(self, key: str, default=None):
        """Получить значение настройки по ключу."""
        return getattr(self, key, default)

    def reload(self):
        """Перезагрузить настройки (для будущего расширения)."""
        self._initialized = False
        self.__init__()

"""Конфигурация Parser Service."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ParserConfig:
    """Настройки парсера курсов."""

    # API ключи
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Списки валют
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")

    # Маппинг ID для CoinGecko
    CRYPTO_ID_MAP: dict = None

    def __post_init__(self):
        self.CRYPTO_ID_MAP = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
        }

    # Пути
    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    # Параметры сети
    REQUEST_TIMEOUT: int = 10

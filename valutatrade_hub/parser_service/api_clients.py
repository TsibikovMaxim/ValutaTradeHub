"""API клиенты для получения курсов."""

from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.parser_service.config import ParserConfig


class BaseApiClient(ABC):
    """Базовый класс для API-клиентов."""

    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Возвращает словарь курсов в формате {PAIR_KEY: rate}."""
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для CoinGecko API."""

    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        vs_currencies = self.config.BASE_CURRENCY.lower()

        url = f"{self.config.COINGECKO_URL}?ids={ids}&vs_currencies={vs_currencies}"

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            rates = {}
            for code, coin_id in self.config.CRYPTO_ID_MAP.items():
                if coin_id in data:
                    rate = data[coin_id].get(vs_currencies)
                    if rate:
                        rates[f"{code}_{self.config.BASE_CURRENCY}"] = rate

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"CoinGecko: {str(e)}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для ExchangeRate-API."""

    def fetch_rates(self) -> Dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("ExchangeRate-API: отсутствует API-ключ")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
        )

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(
                    f"ExchangeRate-API: {data.get('error-type', 'Unknown error')}"
                )

            rates_raw = data.get("rates", {})
            rates = {}

            for currency in self.config.FIAT_CURRENCIES:
                if currency in rates_raw:
                    # Инвертируем курс: 1 EUR = X USD -> EUR_USD
                    rate = 1 / rates_raw[currency] if rates_raw[currency] else 0
                    rates[f"{currency}_{self.config.BASE_CURRENCY}"] = rate

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API: {str(e)}")

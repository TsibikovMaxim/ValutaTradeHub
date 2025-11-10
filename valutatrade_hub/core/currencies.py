"""Иерархия классов валют с поддержкой фиатных и криптовалют."""

from abc import ABC, abstractmethod


class Currency(ABC):
    """Абстрактный базовый класс для валют."""

    def __init__(self, name: str, code: str):
        if not code or not code.isupper() or not (2 <= len(code) <= 5):
            raise ValueError(
                "Код валюты должен быть в верхнем регистре, 2-5 символов"
            )
        if not name:
            raise ValueError("Имя валюты не может быть пустым")

        self.name = name
        self.code = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для UI."""
        pass


class FiatCurrency(Currency):
    """Фиатная валюта."""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Криптовалюта."""

    def __init__(
        self, name: str, code: str, algorithm: str, market_cap: float = 0.0
    ):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )


CURRENCY_REGISTRY = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.5e11),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 3.2e10),
}


def get_currency(code: str) -> Currency:
    """Возвращает объект валюты по коду."""
    from valutatrade_hub.core.exceptions import CurrencyNotFoundError

    code = code.upper()
    if code not in CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code)
    return CURRENCY_REGISTRY[code]

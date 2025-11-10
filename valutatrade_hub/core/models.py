"""Основные классы: User, Wallet, Portfolio."""

import hashlib
import secrets
from datetime import datetime
from typing import Dict, Optional


class User:
    """Класс пользователя системы."""

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: str,
    ):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value:
            raise ValueError("Имя не может быть пустым")
        self._username = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> str:
        return self._registration_date

    def get_user_info(self) -> dict:
        """Возвращает информацию о пользователе без пароля."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date,
        }

    def change_password(self, new_password: str):
        """Изменяет пароль пользователя с хешированием."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        self._salt = secrets.token_hex(8)
        self._hashed_password = hashlib.sha256(
            (new_password + self._salt).encode()
        ).hexdigest()

    def verify_password(self, password: str) -> bool:
        """Проверяет совпадение пароля."""
        hashed = hashlib.sha256((password + self._salt).encode()).hexdigest()
        return hashed == self._hashed_password

    @staticmethod
    def create_user(user_id: int, username: str, password: str) -> "User":
        """Создаёт нового пользователя с хешированием пароля."""
        if not username:
            raise ValueError("Имя не может быть пустым")
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        salt = secrets.token_hex(8)
        hashed_password = hashlib.sha256(
            (password + salt).encode()
        ).hexdigest()
        registration_date = datetime.utcnow().isoformat()

        return User(user_id, username, hashed_password, salt, registration_date)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date,
        }


class Wallet:
    """Кошелёк для одной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float):
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = value

    def deposit(self, amount: float):
        """Пополнение баланса."""
        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительной")
        self._balance += amount

    def withdraw(self, amount: float):
        """Снятие средств."""
        if amount <= 0:
            raise ValueError("Сумма снятия должна быть положительной")

        from valutatrade_hub.core.exceptions import InsufficientFundsError

        if amount > self._balance:
            raise InsufficientFundsError(self._balance, amount, self.currency_code)

        self._balance -= amount

    def get_balance_info(self) -> str:
        """Информация о балансе."""
        return f"{self.currency_code}: {self._balance:.4f}"

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {"currency_code": self.currency_code, "balance": self._balance}


class Portfolio:
    """Портфель пользователя."""

    def __init__(self, user_id: int, wallets: Optional[Dict[str, Wallet]] = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        """Добавляет новую валюту в портфель."""
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            raise ValueError(f"Валюта {currency_code} уже есть в портфеле")

        self._wallets[currency_code] = Wallet(currency_code)

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        """Возвращает кошелёк по коду валюты."""
        return self._wallets.get(currency_code.upper())

    def get_total_value(self, exchange_rates: dict, base_currency: str = "USD") -> float:
        """Возвращает общую стоимость портфеля в базовой валюте."""
        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base_currency:
                total += wallet.balance
            else:
                pair_key = f"{code}_{base_currency}"
                rate = exchange_rates.get(pair_key, {}).get("rate", 0)
                total += wallet.balance * rate
        return total

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "user_id": self._user_id,
            "wallets": {code: w.to_dict() for code, w in self._wallets.items()},
        }

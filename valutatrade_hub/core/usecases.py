"""Бизнес-логика: регистрация, аутентификация, buy/sell/get_rate."""

from datetime import datetime, timedelta
from typing import Optional

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import Portfolio, User, Wallet
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

settings = SettingsLoader()
db = DatabaseManager()


def register_user(username: str, password: str) -> dict:
    """Регистрирует нового пользователя."""
    users = db.read_json(settings.users_file)

    if any(u["username"] == username for u in users):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    user_id = max([u["user_id"] for u in users], default=0) + 1
    user = User.create_user(user_id, username, password)

    users.append(user.to_dict())
    db.write_json(settings.users_file, users)

    portfolios = db.read_json(settings.portfolios_file)
    portfolios.append({"user_id": user_id, "wallets": {}})
    db.write_json(settings.portfolios_file, portfolios)

    return {"user_id": user_id, "username": username}


def login_user(username: str, password: str) -> Optional[User]:
    """Выполняет вход пользователя."""
    users = db.read_json(settings.users_file)

    for u_data in users:
        if u_data["username"] == username:
            user = User(**u_data)
            if user.verify_password(password):
                return user
            else:
                raise ValueError("Неверный пароль")

    raise ValueError(f"Пользователь '{username}' не найден")


def load_portfolio(user_id: int) -> Portfolio:
    """Загружает портфель пользователя."""
    portfolios = db.read_json(settings.portfolios_file)

    for p_data in portfolios:
        if p_data["user_id"] == user_id:
            wallets = {
                code: Wallet(**w_data)
                for code, w_data in p_data.get("wallets", {}).items()
            }
            return Portfolio(user_id, wallets)

    return Portfolio(user_id)


def save_portfolio(portfolio: Portfolio):
    """Сохраняет портфель пользователя."""
    portfolios = db.read_json(settings.portfolios_file)

    for i, p_data in enumerate(portfolios):
        if p_data["user_id"] == portfolio.user_id:
            portfolios[i] = portfolio.to_dict()
            break
    else:
        portfolios.append(portfolio.to_dict())

    db.write_json(settings.portfolios_file, portfolios)


@log_action("BUY")
def buy(user_id: int, currency_code: str, amount: float) -> dict:
    """Покупка валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        raise e

    portfolio = load_portfolio(user_id)

    if currency_code.upper() not in portfolio.wallets:
        portfolio.add_currency(currency_code)

    wallet = portfolio.get_wallet(currency_code)

    old_balance = wallet.balance
    wallet.deposit(amount)
    new_balance = wallet.balance

    save_portfolio(portfolio)

    rates = db.read_json(settings.rates_file)
    pair_key = f"{currency_code.upper()}_USD"
    rate = rates.get("pairs", {}).get(pair_key, {}).get("rate", 0)
    estimated_cost = amount * rate if rate else None

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "estimated_cost": estimated_cost,
    }


@log_action("SELL")
def sell(user_id: int, currency_code: str, amount: float) -> dict:
    """Продажа валюты."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    try:
        get_currency(currency_code)
    except CurrencyNotFoundError as e:
        raise e

    portfolio = load_portfolio(user_id)
    wallet = portfolio.get_wallet(currency_code)

    if not wallet:
        raise ValueError(
            f"У вас нет кошелька '{currency_code}'. "
            "Добавьте валюту: она создаётся автоматически при первой покупке."
        )

    old_balance = wallet.balance
    try:
        wallet.withdraw(amount)
    except InsufficientFundsError as e:
        raise e
    new_balance = wallet.balance

    save_portfolio(portfolio)

    rates = db.read_json(settings.rates_file)
    pair_key = f"{currency_code.upper()}_USD"
    rate = rates.get("pairs", {}).get(pair_key, {}).get("rate", 0)
    estimated_revenue = amount * rate if rate else None

    return {
        "currency": currency_code,
        "amount": amount,
        "old_balance": old_balance,
        "new_balance": new_balance,
        "rate": rate,
        "estimated_revenue": estimated_revenue,
    }


def get_rate(from_code: str, to_code: str) -> dict:
    """Получает курс валюты."""
    try:
        get_currency(from_code)
        get_currency(to_code)
    except CurrencyNotFoundError as e:
        raise e

    rates = db.read_json(settings.rates_file)
    pair_key = f"{from_code.upper()}_{to_code.upper()}"

    rate_data = rates.get("pairs", {}).get(pair_key)

    if not rate_data:
        raise ApiRequestError(
            f"Курс {from_code}→{to_code} недоступен. Повторите попытку позже."
        )

    updated_at_str = rate_data.get("updated_at")
    if updated_at_str:
        updated_at = datetime.fromisoformat(updated_at_str.replace("Z", ""))
        age = datetime.utcnow() - updated_at
        ttl = timedelta(seconds=settings.rates_ttl_seconds)

        if age > ttl:
            raise ApiRequestError(
                f"Данные курса устарели (обновлено: {updated_at_str}). "
                "Выполните 'update-rates'."
            )

    return {
        "from": from_code.upper(),
        "to": to_code.upper(),
        "rate": rate_data.get("rate"),
        "updated_at": rate_data.get("updated_at"),
        "source": rate_data.get("source"),
    }

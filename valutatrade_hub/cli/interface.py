"""Командный интерфейс (CLI)."""

from prettytable import PrettyTable

from valutatrade_hub.core import usecases
from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.updater import RatesUpdater

current_user = None


def parse_args(command_line: str) -> tuple:
    """Парсит строку команды."""
    parts = command_line.strip().split()
    if not parts:
        return None, {}

    command = parts[0]
    args = {}

    i = 1
    while i < len(parts):
        if parts[i].startswith("--"):
            key = parts[i][2:]
            if i + 1 < len(parts) and not parts[i + 1].startswith("--"):
                value = parts[i + 1]
                i += 2
            else:
                value = True
                i += 1
            args[key] = value
        else:
            i += 1

    return command, args


def cmd_register(args):
    """Команда register."""
    username = args.get("username")
    password = args.get("password")

    if not username or not password:
        print("Использование: register --username <name> --password <pass>")
        return

    try:
        result = usecases.register_user(username, password)
        print(
            f"Пользователь '{result['username']}' зарегистрирован "
            f"(id={result['user_id']}). "
            f"Войдите: login --username {username} --password ****"
        )
    except ValueError as e:
        print(f"Ошибка: {e}")


def cmd_login(args):
    """Команда login."""
    global current_user

    username = args.get("username")
    password = args.get("password")

    if not username or not password:
        print("Использование: login --username <name> --password <pass>")
        return

    try:
        user = usecases.login_user(username, password)
        current_user = user
        print(f"Вы вошли как '{user.username}'")
    except ValueError as e:
        print(f"Ошибка: {e}")


def get_rate(pairs, from_code: str, to_code: str) -> float:
    """Получает курс между валютами"""
    if from_code == to_code:
        return 1.0

    direct = pairs.get(f"{from_code}_{to_code}")
    if direct:
        return direct["rate"]

    reverse = pairs.get(f"{to_code}_{from_code}")
    if reverse and reverse["rate"]:
        return 1 / reverse["rate"]

    if from_code != "USD" and to_code != "USD":
        usd_base = get_rate(pairs, from_code, "USD")
        usd_target = get_rate(pairs, "USD", to_code)
        return usd_base * usd_target if usd_base and usd_target else 0.0

    return 0.0


def calculate_portfolio_value(pairs, wallets_dict, base):
    total = 0.0
    rows = []
    for code, wallet in wallets_dict.items():
        balance = wallet.balance
        rate = get_rate(pairs, code, base)
        value = balance * rate
        total += value
        rows.append((code, balance, value))
    return total, rows


def cmd_show_portfolio(args):
    """Команда show-portfolio с prettytable и конвертацией базовой валюты."""
    if not current_user:
        print("Сначала выполните login")
        return

    base_currency = args.get("base", "USD").upper()

    try:
        portfolio = usecases.load_portfolio(current_user.user_id)
        wallets = portfolio.wallets
        if not wallets:
            print(f"Портфель пользователя '{current_user.username}' пуст.")
            return

        settings = SettingsLoader()
        db = DatabaseManager()
        pairs = db.read_json(settings.rates_file).get("pairs", {})

        total_value, rows = calculate_portfolio_value(pairs, wallets, base_currency)
        print(f"\nПортфель пользователя '{current_user.username}' (база: {base_currency}):\n")

        table = PrettyTable()
        table.field_names = ["Валюта", "Баланс", f"Стоимость ({base_currency})"]

        for code, balance, value in rows:
            table.add_row([code, f"{balance:.4f}", f"{value:.2f}"])

        print(table)
        print(f"\nИТОГО: {total_value:,.2f} {base_currency}\n")

    except Exception as e:
        print(f"Ошибка: {e}")


def cmd_buy(args):
    """Команда buy."""
    if not current_user:
        print("Сначала выполните login")
        return

    currency = args.get("currency")
    amount = args.get("amount")

    if not currency or not amount:
        print("Использование: buy --currency <CODE> --amount <float>")
        return

    try:
        amount = float(amount)
        result = usecases.buy(current_user.user_id, currency, amount)

        print(
            f"Покупка выполнена: {result['amount']:.4f} {result['currency']} "
            f"по курсу {result['rate']:.2f} USD/{result['currency']}"
        )
        print("Изменения в портфеле:")
        print(
            f"- {result['currency']}: было {result['old_balance']:.4f} "
            f"→ стало {result['new_balance']:.4f}"
        )
        if result.get("estimated_cost"):
            print(
                f"Оценочная стоимость покупки: {result['estimated_cost']:.2f} USD"
            )

    except (ValueError, CurrencyNotFoundError) as e:
        print(f"Ошибка: {e}")


def cmd_sell(args):
    """Команда sell."""
    if not current_user:
        print("Сначала выполните login")
        return

    currency = args.get("currency")
    amount = args.get("amount")

    if not currency or not amount:
        print("Использование: sell --currency <CODE> --amount <float>")
        return

    try:
        amount = float(amount)
        result = usecases.sell(current_user.user_id, currency, amount)

        print(
            f"Продажа выполнена: {result['amount']:.4f} {result['currency']} "
            f"по курсу {result['rate']:.2f} USD/{result['currency']}"
        )
        print("Изменения в портфеле:")
        print(
            f"- {result['currency']}: было {result['old_balance']:.4f} "
            f"→ стало {result['new_balance']:.4f}"
        )
        if result.get("estimated_revenue"):
            print(
                f"Оценочная выручка: {result['estimated_revenue']:.2f} USD"
            )

    except (ValueError, CurrencyNotFoundError, InsufficientFundsError) as e:
        print(f"Ошибка: {e}")


def cmd_get_rate(args):
    """Команда get-rate."""
    from_code = args.get("from")
    to_code = args.get("to")

    if not from_code or not to_code:
        print("Использование: get-rate --from <CODE> --to <CODE>")
        return

    try:
        result = usecases.get_rate(from_code, to_code)
        print(
            f"Курс {result['from']}→{result['to']}: {result['rate']:.8f} "
            f"(обновлено: {result['updated_at']})"
        )
        if result['rate']:
            reverse = 1 / result['rate']
            print(f"Обратный курс {result['to']}→{result['from']}: {reverse:.8f}")

    except (CurrencyNotFoundError, ApiRequestError) as e:
        print(f"Ошибка: {e}")


def cmd_update_rates(args):
    """Команда update-rates."""
    try:
        config = ParserConfig()
        clients = [CoinGeckoClient(config), ExchangeRateApiClient(config)]
        updater = RatesUpdater(clients, config)

        result = updater.run_update()

        print(
            f"Update successful. Total rates updated: {result['total_rates']}. "
            f"Last refresh: {result['last_refresh']}"
        )

        if result["errors"]:
            print("Update completed with errors:")
            for err in result["errors"]:
                print(f"  - {err}")

    except ApiRequestError as e:
        print(f"Ошибка обновления: {e}")


def cmd_help(args):
    """Команда help."""
    print("""
Доступные команды:
  register --username <name> --password <pass>   Регистрация
  login --username <name> --password <pass>      Вход
  show-portfolio [--base <CURRENCY>]             Показать портфель
  buy --currency <CODE> --amount <float>         Купить валюту
  sell --currency <CODE> --amount <float>        Продать валюту
  get-rate --from <CODE> --to <CODE>             Показать курс
  update-rates                                    Обновить курсы
  help                                            Справка
  exit                                            Выход
""")


def run_cli():
    """Основной цикл CLI."""
    print("=== ValutaTrade Hub ===")
    print("Введите 'help' для справки\n")

    commands = {
        "help": cmd_help,
        "register": cmd_register,
        "login": cmd_login,
        "show-portfolio": cmd_show_portfolio,
        "buy": cmd_buy,
        "sell": cmd_sell,
        "get-rate": cmd_get_rate,
        "update-rates": cmd_update_rates,
        "exit": None,
    }

    while True:
        try:
            line = input("> ").strip()
            if not line:
                continue

            command, args = parse_args(line)
            if not command:
                continue

            if command == "exit":
                print("До свидания!")
                break

            cmd_func = commands.get(command)
            if cmd_func:
                cmd_func(args)
            else:
                print(f"Неизвестная команда: {command}")

        except KeyboardInterrupt:
            print("\nДо свидания!")
            break
        except Exception as e:
            print(f"Непредвиденная ошибка: {e}")

# ValutaTrade Hub

## Идея проекта

ValutaTrade Hub — консольное приложение для симуляции торговли валютами: фиатными и криптовалютами. Пользователь может зарегистрироваться, управлять портфелем, покупать и продавать валюты, а также отслеживать курсы в реальном времени через внешний Parser Service.

---

## Структура каталогов

```
finalproject_tsibikov_m25_555/
├── data/
│ ├── users.json
│ ├── portfolios.json
│ ├── rates.json
│ └── exchange_rates.json
├── valutatrade_hub/
│ ├── core/
│ ├── infra/
│ ├── cli/
│ └── parser_service/
├── logs/
├── main.py
├── Makefile
├── poetry.lock
├── pyproject.toml
├── README.md
└── .gitignore
```

---

## Установка

1. Клонируйте репозиторий или скопируйте структуру проекта.
2. Установите зависимости с помощью Poetry:
    ```
    make install
    # или
    poetry install
    ```

---

## Запуск

Запустить приложение можно так:

- Через Makefile:
    ```
    make project
    ```

- Через Poetry напрямую:
    ```
    poetry run project
    ```

- Или через Python (если всё собрали):
    ```
    python main.py
    ```

---

## Примеры команд CLI

```
- `register --username alice --password 1234` — зарегистрировать пользователя.
- `login --username alice --password 1234` — войти пользователю.
- `show-portfolio` — показать портфель пользователя.
- `show-portfolio --base EUR` — портфель (конвертация в EUR).
- `buy --currency BTC --amount 0.05` — купить криптовалюту.
- `buy --currency EUR --amount 100` — купить фиатную валюту.
- `sell --currency BTC --amount 0.01` — продать криптовалюту.
- `get-rate --from BTC --to USD` — получить курс одной валюты к другой.
- `update-rates` — обновить курсы валют через Parser Service.
- `help` — справка по командам.
- `exit` — выйти из приложения.
```

---

## Кэширование курсов и TTL

- Курсы валют хранятся в файле `data/rates.json` (текущий срез).
- История всех измерений сохраняется в `data/exchange_rates.json`.
- Актуальность кэша определяется параметром TTL (по умолчанию 300 секунд). Если данные устарели — приложение предложит обновить курсы через команду `update-rates`.

---

## Как включить Parser Service

Parser Service обновляет курсы валют, используя публичные API CoinGecko (для криптовалют) и ExchangeRate-API (для фиатных валют).

### Ключ для ExchangeRate-API

1. Зарегистрируйтесь на [exchangerate-api.com](https://www.exchangerate-api.com/).
2. Получите ваш бесплатный API-ключ.
3. Создайте файл `.env` в корне проекта с содержимым:

    ```
    EXCHANGERATE_API_KEY=ВАШ_КЛЮЧ
    ```

4. При наличии ключа команда `update-rates` будет получать все курсы (фиатные и криптовалютные).
5. Если ключ отсутствует, будут доступны только криптовалюты (через CoinGecko).

---

## Описание важных файлов

- `users.json` — все зарегистрированные пользователи.
- `portfolios.json` — структуры портфелей и кошельков пользователей.
- `rates.json` — актуальные курсы валют по валютным парам.
- `exchange_rates.json` — история полученных курсов для дальнейшего анализа.

---

## Пример сценария для быстрой проверки

```
register --username alice --password 1234
login --username alice --password 1234
update-rates
buy --currency BTC --amount 0.04
buy --currency EUR --amount 1000
show-portfolio
get-rate --from BTC --to USD
sell --currency BTC --amount 0.01
show-portfolio --base EUR
exit
```

---

## Дополнительные сведения

- Для проверки и форматирования кода используйте:
    ```
    make lint
    # или
    poetry run ruff check .
    ```

- Все действия пользователя и обновления логируются в папку `logs/`.
- Если что-то не работает — смотрите логи и содержимое JSON-файлов.
- Сборка готового пакета:
    ```
    make build
    ```
  
---

## Автор

Цибиков Максим М25-555п

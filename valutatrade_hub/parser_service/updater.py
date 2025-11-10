"""Обновление курсов валют."""

import logging
from datetime import datetime
from typing import Dict, List

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.api_clients import BaseApiClient
from valutatrade_hub.parser_service.config import ParserConfig

logger = logging.getLogger("valutatrade_hub")


class RatesUpdater:
    """Координатор обновления курсов."""

    def __init__(self, clients: List[BaseApiClient], config: ParserConfig):
        self.clients = clients
        self.config = config
        self.db = DatabaseManager()

    def run_update(self) -> dict:
        """Запускает обновление курсов от всех клиентов."""
        logger.info("Starting rates update...")

        all_rates = {}
        errors = []

        for client in self.clients:
            client_name = client.__class__.__name__
            try:
                logger.info(f"Fetching from {client_name}...")
                rates = client.fetch_rates()
                all_rates.update(rates)
                logger.info(f"{client_name}: OK ({len(rates)} rates)")
            except ApiRequestError as e:
                errors.append(f"{client_name}: {e.reason}")
                logger.error(f"Failed to fetch from {client_name}: {e.reason}")

        if not all_rates:
            raise ApiRequestError("Не удалось получить ни одного курса")

        # Формирование итогового JSON
        timestamp = datetime.utcnow().isoformat() + "Z"
        rates_data = {
            "pairs": {
                pair: {
                    "rate": rate,
                    "updated_at": timestamp,
                    "source": "ParserService",
                }
                for pair, rate in all_rates.items()
            },
            "last_refresh": timestamp,
        }

        # Сохранение
        self.db.write_json(self.config.RATES_FILE_PATH, rates_data)
        logger.info(
            f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}..."
        )

        return {
            "total_rates": len(all_rates),
            "last_refresh": timestamp,
            "errors": errors,
        }

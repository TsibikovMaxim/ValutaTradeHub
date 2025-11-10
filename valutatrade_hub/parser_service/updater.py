"""Обновление курсов валют."""

import logging
from datetime import datetime
from typing import List

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
                if rates:
                    all_rates.update(rates)
                logger.info(f"{client_name}: OK ({len(rates)} rates)")
            except ApiRequestError as e:
                errors.append(f"{client_name}: {str(e)}")
                logger.error(f"Failed to fetch from {client_name}: {str(e)}")

        if not all_rates:
            raise ApiRequestError("Не удалось получить ни одного курса")

        timestamp = datetime.utcnow().isoformat() + "Z"
        pairs_dict = {}
        for pair, rate in all_rates.items():
            pairs_dict[pair] = {
                "rate": rate,
                "updated_at": timestamp,
                "source": "ParserService",
            }

        rates_data = {
            "pairs": pairs_dict,
            "last_refresh": timestamp,
        }

        self.db.write_json(self.config.RATES_FILE_PATH, rates_data)
        logger.info(f"Writing {len(all_rates)} rates to {self.config.RATES_FILE_PATH}...")

        return {
            "total_rates": len(all_rates),
            "last_refresh": timestamp,
            "errors": errors,
        }

"""Декораторы для логирования действий."""

import functools
import logging
from datetime import datetime

logger = logging.getLogger("valutatrade_hub")


def log_action(action_type: str):
    """Декоратор для логирования доменных операций."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.utcnow().isoformat()
            result_status = "OK"
            error_msg = None

            try:
                result = func(*args, **kwargs)
                logger.info(
                    f"{action_type} timestamp={timestamp} "
                    f"args={args} kwargs={kwargs} result={result_status}"
                )
                return result
            except Exception as e:
                result_status = "ERROR"
                error_msg = str(e)
                logger.error(
                    f"{action_type} timestamp={timestamp} "
                    f"args={args} kwargs={kwargs} result={result_status} "
                    f"error={error_msg}"
                )
                raise

        return wrapper

    return decorator

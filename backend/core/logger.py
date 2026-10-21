"""Módulo de configuração de observabilidade e logs da aplicação."""

import logging
import sys
from backend.core.config import settings


def setup_logger() -> logging.Logger:
    """Configura e retorna o logger padronizado do sistema."""
    logger = logging.getLogger("conversor_moedas")

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(settings.LOG_LEVEL.upper())
    return logger


logger = setup_logger()

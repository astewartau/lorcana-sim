"""Lorcana simulation package."""

__version__ = "0.1.0"

# Set up logging configuration on import
import os
from .utils.logging_config import setup_logging

# Default to INFO level, but allow override via environment variable
log_level = os.getenv('LORCANA_LOG_LEVEL', 'INFO')
setup_logging(level=log_level)

from . import models
from . import loaders
from . import utils
from . import engine

__all__ = ["models", "loaders", "utils", "engine"]
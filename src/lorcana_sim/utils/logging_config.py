"""Logging configuration for Lorcana Sim."""

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", format_style: str = "simple") -> None:
    """
    Set up logging configuration for the entire application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Format style - "simple", "detailed", or "json"
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Define format styles
    formats = {
        "simple": "%(name)s - %(levelname)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        "json": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"  # Could be enhanced for actual JSON
    }
    
    # Get the appropriate format
    log_format = formats.get(format_style, formats["simple"])
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Optionally reduce noise from other libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


# Convenience function for getting loggers with shortened names
def get_game_logger(module_name: str) -> logging.Logger:
    """
    Get a logger with a shortened name for game modules.
    
    Args:
        module_name: Full module name (e.g., 'lorcana_sim.engine.event_system')
        
    Returns:
        Logger with shortened name (e.g., 'engine.event_system')
    """
    # Remove the 'lorcana_sim.' prefix for cleaner log output
    if module_name.startswith('lorcana_sim.'):
        short_name = module_name[len('lorcana_sim.'):]
    else:
        short_name = module_name
    
    return logging.getLogger(short_name)
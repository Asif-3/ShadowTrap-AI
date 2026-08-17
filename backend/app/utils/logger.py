"""
ShadowTrap AI - Logging Utility
================================
Configurable colored logging for the application.
"""

import logging
import sys
from datetime import datetime

# Ensure UTF-8 output encoding for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class ShadowTrapFormatter(logging.Formatter):
    """Custom formatter with color support and structured output."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        
        formatted = (
            f"{self.BOLD}[{timestamp}]{self.RESET} "
            f"{color}{record.levelname:8s}{self.RESET} "
            f"\033[90m{record.name}\033[0m -> "
            f"{record.getMessage()}"
        )
        
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        
        return formatted



def setup_logger(name="shadowtrap", level=logging.DEBUG):
    """
    Create and configure a logger instance.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler with color formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ShadowTrapFormatter())
    logger.addHandler(console_handler)
    
    return logger


# Pre-configured loggers for common modules
def get_logger(module_name):
    """Get a logger for a specific module."""
    return setup_logger(f"shadowtrap.{module_name}")

"""
Structured Logging Utilities
"""
import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """
    Configure structured logging.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

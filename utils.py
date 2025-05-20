'''Utility functions for the PDF anonymization application.'''
import logging
import sys

DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DEFAULT_LOG_LEVEL = logging.INFO

def setup_logging(log_level: int = DEFAULT_LOG_LEVEL, log_format: str = DEFAULT_LOG_FORMAT) -> None:
    """
    Configures basic logging for the application.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG).
        log_format: The format string for log messages.
    """
    logging.basicConfig(level=log_level, format=log_format, stream=sys.stdout)
    # You can also configure logging to a file here if needed:
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setFormatter(logging.Formatter(log_format))
    # logging.getLogger().addHandler(file_handler)

# Example of how to get a logger in other modules:
# import logging
# logger = logging.getLogger(__name__)
# logger.info("This is an info message.")

if __name__ == '__main__':
    setup_logging(logging.DEBUG) # Setup with DEBUG level for testing this module
    logger = logging.getLogger(__name__) # Get a logger for the current module

    logger.debug("This is a debug message from utils.")
    logger.info("This is an info message from utils.")
    logger.warning("This is a warning message from utils.")
    logger.error("This is an error message from utils.")
    logger.critical("This is a critical message from utils.")

    print("Logging setup complete. Check console for messages.")

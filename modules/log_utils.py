import logging
import functools

# Custom log filter to suppress specific non-critical log messages
class SuppressNonCriticalErrors(logging.Filter):
    def filter(self, record):
        # Suppress logs that contain specific non-critical errors
        non_critical_phrases = [
            "conflicting titles",
            "Task status check failed with status code: 404",
            "Response status code: 202",
            "Failed to copy page",
            "Attempt",
            "Response content",
            "Response status code: 400",
            "Error: []"
        ]
        return not any(phrase in record.getMessage() for phrase in non_critical_phrases)

# Function to set up a logger
def setup_logger(name="app_logger", level=logging.DEBUG):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)

    # Add custom filter to suppress non-critical errors
    logger.addFilter(SuppressNonCriticalErrors())

    return logger

# Create a logger instance
logger = setup_logger()

# Decorator for logging function call details and exceptions
def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering {func.__name__}() with args: {args}, kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__}() returned {result}")
            return result
        except Exception as e:
            logger.error(f"Exception occurred in {func.__name__}(): {str(e)}", exc_info=True)
            raise
    return wrapper

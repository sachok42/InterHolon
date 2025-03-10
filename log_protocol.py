import logging

def create_file_logger(log_file, logger_name='file_logger', log_level=logging.INFO, log_format='%(asctime)s - %(levelname)s - %(message)s'):
    """
    Creates and configures a logger that logs messages into a specified file.

    :param log_file: Path to the log file where logs will be written.
    :param logger_name: Name of the logger (default is 'file_logger').
    :param log_level: Logging level (default is logging.INFO).
    :param log_format: Format of the log messages (default is '%(asctime)s - %(levelname)s - %(message)s').
    :return: Configured logger object.
    """
    # Create a logger with the specified name
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Create a file handler to write logs to the specified file
    file_handler = logging.FileHandler(log_file, mode='a')  # 'a' for append mode
    file_handler.setLevel(log_level)

    # Create a formatter and set it for the file handler
    formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger

# Example usage:
if __name__ == "__main__":
    # Create a logger that logs to 'my_log_file.log'
    my_logger = create_file_logger(log_file='my_log_file.log')

    # Log some messages
    my_logger.info("This is an info message.")
    my_logger.warning("This is a warning message.")
    my_logger.error("This is an error message.")
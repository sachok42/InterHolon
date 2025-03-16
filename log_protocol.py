import logging
import datetime

# logger = logging.getLogger(__name__)
# logging.basicConfig(filename='chatting_log.log', encoding='utf-8', level=logging.DEBUG)
# logging.basicConfig(filename='error_log.log', encoding='utf-8', level=logging.DEBUG)

standard_font = ("Arial", 14)

def setup_logger(logger_name, log_file, level=logging.DEBUG):
    l = logging.getLogger(logger_name)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(log_file, mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)

    l.setLevel(level)
    l.addHandler(fileHandler)
    # l.addHandler(streamHandler)    


# setup_logger('chatting_log', 'chatting_log.log')
# setup_logger('error_log', 'error_log.log')
logger = logging.getLogger('chatting_log.log')
error_logger = logging.getLogger('error_log.log')
formatter = logging.Formatter('%(asctime)s : %(message)s')
fileHandler = logging.FileHandler('chatting_log.log', mode='w')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
basic_buffer_size = 1024

def custom_log(text, used_logger=None):
    if used_logger is None:
        used_logger = logger
    message = f"{datetime.datetime.now()} {text}"
    logger.info(message)
    print(message)

custom_log("LOG STARTED", logger)
custom_log("LOG_STARTED", error_logger)

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
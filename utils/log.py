import logging
import os

LOGGING_DIR = os.path.join(os.path.expanduser('~'), 'opendss_powerflow_service', 'logs')

if not os.path.exists(LOGGING_DIR):
    os.makedirs(LOGGING_DIR)

def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(os.path.join(LOGGING_DIR, 'app.log'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)

    return logger
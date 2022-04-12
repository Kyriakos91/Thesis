import logging
import sys,os
from logging.handlers import RotatingFileHandler

def initialize_logger(log_to_file=False, loginfo=logging.INFO):
    """
    initialize_logger initializes python logger with a unified format and the ability to persist to a file.

    Input 
    - log_to_file:  boolean indicating whether to persist logs to a file (and not console)
    - loginfo:      log info to use (default is logging.INFO)
    """
    log_format = '%(asctime)-15s %(threadName)-10s %(lineno)-3s %(name)-8s %(levelname)-8s %(message)s'
    logger = logging.getLogger()
    logger.setLevel(loginfo)

    if log_to_file:
        handler = RotatingFileHandler('{}.log'.format(
            os.path.basename(sys.argv[0])), maxBytes=20000000, backupCount=10)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)    
    
    return logger

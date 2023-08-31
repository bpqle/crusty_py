import logging
import sys
from .config import *
logger = logging.getLogger('main')

def lincoln(log, level='DEBUG'):
    # Courtesy of https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output
    class CustomFormatter(logging.Formatter):

        white = "\x1b[37m"  # debug
        green = "\x1b[32m"  # proto
        blue = "\x1b[34m"  # dispatch
        magenta = "\x1b[35m"  # state
        cyan = "\x1b[36m"  # info
        yellow = "\x1b[33m"  # warning
        red = "\x1b[31m"  # error
        bold_red = "\x1b[31;1m"
        reset = "\x1b[0m"
        begin = "%(asctime)s - %(name)s - %(levelname)s:"
        end = " - %(message)s (%(filename)s:%(lineno)d)"

        FORMATS = {
            logging.DEBUG: magenta + begin + reset + end,
            logging.PROTO: blue + begin + reset + end,
            logging.DISPATCH: cyan + begin + reset + end,
            logging.STATE: green + begin + reset + end,
            logging.INFO: white + begin + reset + end,
            logging.WARNING: yellow + begin + reset + end,
            logging.ERROR: red + begin + reset + end,
            logging.CRITICAL: bold_red + begin + reset + end
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)

    streamer = logging.StreamHandler(sys.stdout)
    streamer.setFormatter(CustomFormatter())
    logger.addHandler(streamer)
    if LOCAL_LOG:
        filer = logging.FileHandler(f"/root/py_crust/log/{log}", mode='w')
        filer.setFormatter(logging.Formatter())
        logger.addHandler(filer)

    logger.info(f"Logging to file {log}. Connecting to DecideAPI")
    logger.setLevel(level)

# The following function is taken from https://stackoverflow.com/questions/2183233
# Checkout module haggis for more information
def add_log_lvl(name, num, method_name):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.
    """
    if not method_name:
        method_name = name.lower()

    if hasattr(logging, name):
        raise AttributeError('{} already defined in logging module'.format(name))
    if hasattr(logging, method_name):
        raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError('{} already defined in logger class'.format(method_name))

    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(num):
            self._log(num, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(num, message, *args, **kwargs)

    logging.addLevelName(num, name)
    setattr(logging, name, num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)


# Proto is reserved for basic communication protocols of protobuf found in decrypt.py
# Dispatch is reserved for zmq operations found in dispatch.py
# State is reserved for state-machine operations found in process.py
add_log_lvl('PROTO', 11, 'proto')
add_log_lvl('DISPATCH', 12, 'dispatch')
add_log_lvl('STATE', 13, 'state')
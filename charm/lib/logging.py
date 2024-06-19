import logging

COMMENT = logging.DEBUG - 2
COMMAND = logging.DEBUG - 1
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
FATAL = logging.FATAL

logging.addLevelName(COMMENT, "COMMENT")
logging.addLevelName(COMMAND, "COMMAND")

import logging
from digiformatter import logger as digilogger
from charm.lib.debug_menu import ImGuiHandler

# https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
# TODO: There's got to be a better way to do this
def add_logging_level(level_name, level_num, method_name=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> add_logging_level('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    """
    if not method_name:
        method_name = level_name.lower()

    if hasattr(logging, level_name):
        raise AttributeError('{} already defined in logging module'.format(level_name))
    if hasattr(logging, method_name):
        raise AttributeError('{} already defined in logging module'.format(method_name))
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError('{} already defined in logger class'.format(method_name))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(level_num):
            self._log(level_num, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(level_num, message, *args, **kwargs)

    logging.addLevelName(level_num, level_name)
    setattr(logging, level_name, level_num)
    setattr(logging.getLoggerClass(), method_name, logForLevel)
    setattr(logging, method_name, logToRoot)

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    dfhandler = digilogger.DigiFormatterHandler()
    dfhandlersource = digilogger.DigiFormatterHandler(showsource=True)
    ihandler = ImGuiHandler()
    ihandlersource = ImGuiHandler(showsource=True)

    add_logging_level("COMMENT", logging.DEBUG - 2)
    add_logging_level("COMMAND", logging.DEBUG - 1)

    logger = logging.getLogger("charm")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(dfhandler)
    logger.addHandler(ihandler)

    arcadelogger = logging.getLogger("arcade")
    arcadelogger.setLevel(logging.WARN)
    arcadelogger.handlers = []
    arcadelogger.propagate = False
    arcadelogger.addHandler(dfhandlersource)
    arcadelogger.addHandler(ihandlersource)

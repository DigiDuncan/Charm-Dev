import logging

from digiformatter import logger as digilogger
from charm.lib.debug import ImGuiLogger

def setup() -> None:
    logging.basicConfig(level=logging.INFO)
    dfhandler = digilogger.DigiFormatterHandler()
    dfhandlersource = digilogger.DigiFormatterHandler(showsource=True)
    ihandler = ImGuiLogger()
    ihandlersource = ImGuiLogger(showsource=True)

    logger = logging.getLogger("charm")
    logger.setLevel(logging.DEBUG)
    logger.handlers = []
    logger.propagate = False
    logger.addHandler(dfhandler)
    logger.addHandler(ihandler)

    arcadelogger = logging.getLogger("arcade")
    arcadelogger.setLevel(logging.WARNING)
    arcadelogger.handlers = []
    arcadelogger.propagate = False
    arcadelogger.addHandler(dfhandlersource)
    arcadelogger.addHandler(ihandlersource)

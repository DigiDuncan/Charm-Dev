from logging import Logger
from time import time


class LogSection:
    def __init__(self, logger: Logger, name: str):
        self.logger = logger
        self.name = name
        logger.debug(f"Starting {name}")
        self.start_time = time()

    def done(self) -> None:
        duration = int((time() - self.start_time) * 1000)
        self.logger.debug(f"Done {self.name} ({duration}ms)")

    def __enter__(self) -> None:
        pass

    def __exit__(self, type, value, traceback) -> None:
        if type is None:
            self.done()

import os
from loguru import logger


class LoggerService:
    def __init__(self):
        self.logger = logger

    def setup(self):
        mode = os.getenv("APP_MODE", "development")
        logger.remove()
        if mode == "production":
            logger.add(
                "logs/islamic_api.log",
                rotation="10 MB",
                retention="30 days",
                level="INFO",
                format="{time} | {level} | {message}"
            )
        else:
            logger.add(
                lambda msg: print(msg, end=""),
                level="DEBUG",
                colorize=True,
                format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | {message}"
            )
        logger.info("Logger initialized")

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)

from kernel.services.database import DatabaseService
from kernel.services.cache import CacheService
from kernel.services.logger import LoggerService
from kernel.services.config_reader import ConfigReader
from kernel.services.translator import TranslatorService


class ServiceContainer:
    def __init__(self):
        self.config = ConfigReader()
        self.logger = LoggerService()
        self.db = DatabaseService()
        self.cache = CacheService()
        self.translator = TranslatorService()

    async def init(self):
        self.config.load()
        self.logger.setup()
        await self.db.connect(self.config.config)
        await self.cache.connect()
        self.logger.info("All services initialized")

    async def dispose(self):
        await self.db.disconnect()
        await self.cache.disconnect()
        self.logger.info("All services disposed")

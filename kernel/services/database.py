import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()


class DatabaseService:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def connect(self):
        database_url = os.getenv("DATABASE_URL")
        self.engine = create_async_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            echo=os.getenv("APP_MODE") == "development"
        )
        self.session_factory = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        print("Database connected")

    async def disconnect(self):
        if self.engine:
            await self.engine.dispose()
            print("Database disconnected")

    def get_session(self) -> AsyncSession:
        return self.session_factory()

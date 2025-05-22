# File: app/core/database_manager.py
# (Content as previously generated, verified)
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator # Added AsyncGenerator

import asyncpg # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config_manager import ConfigManager

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_database_config()
        self.engine = None # type: ignore 
        self.session_factory: Optional[sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        if self.engine: 
            return

        connection_string = (
            f"postgresql+asyncpg://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
        
        self.engine = create_async_engine(
            connection_string,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_min_size,
            max_overflow=self.config.pool_max_size - self.config.pool_min_size,
            pool_recycle=self.config.pool_recycle_seconds
        )
        
        self.session_factory = sessionmaker(
            self.engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        await self._create_pool()
    
    async def _create_pool(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=self.config.username,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size
            )
        except Exception as e:
            print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]: 
        if not self.pool:
            if not self.engine: 
                 raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            await self._create_pool() 
            if not self.pool: 
                raise RuntimeError("Failed to acquire asyncpg pool.")
            
        async with self.pool.acquire() as connection:
            yield connection # type: ignore # asyncpg.Connection
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback):
        async with self.connection() as conn:
            async with conn.transaction():
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose()
            self.engine = None 

# File: app/core/database_manager.py
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, TYPE_CHECKING, Any 
import logging # Import standard logging

import asyncpg 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text 

from app.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager, app_core: Optional["ApplicationCore"] = None):
        self.config = config_manager.get_database_config()
        self.app_core = app_core 
        self.engine: Optional[Any] = None 
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None
        self.logger: Optional[logging.Logger] = None # Initialize logger attribute

    async def initialize(self):
        if self.engine: 
            return
        
        # Set up logger if not already done by app_core injecting it
        if self.app_core and hasattr(self.app_core, 'logger'):
            self.logger = self.app_core.logger
        elif not self.logger: # Basic fallback logger if app_core didn't set one
            self.logger = logging.getLogger("DatabaseManager")
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)


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
        
        self.session_factory = async_sessionmaker(
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
            if self.logger: self.logger.error(f"Failed to create asyncpg pool: {e}", exc_info=True)
            else: print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            # This log might happen before logger is fully set if initialize isn't called first.
            log_msg = "DatabaseManager not initialized. Call initialize() first."
            if self.logger: self.logger.error(log_msg)
            else: print(f"ERROR: {log_msg}")
            raise RuntimeError(log_msg)
            
        session: AsyncSession = self.session_factory()
        try:
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id_str}';"))
            # If no app_core.current_user, we DO NOT set app.current_user_id.
            # The audit trigger's fallback logic (EXCEPTION WHEN OTHERS -> v_user_id := NULL; IF v_user_id IS NULL THEN NEW.id for users table)
            # will handle attributing self-updates to core.users or logging NULL for other system actions.
            
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
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await connection.execute(f"SET LOCAL app.current_user_id = '{user_id_str}';") # type: ignore
            # Again, do not set if no current_user, let trigger handle it.
            yield connection # type: ignore 
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback): 
        async with self.connection() as conn:
            async with conn.transaction(): # type: ignore 
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose() # type: ignore
            self.engine = None

# File: app/services/tax_service.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select
from app.models.accounting.tax_code import TaxCode 
from app.models.accounting.gst_return import GSTReturn 
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context
from app.services import ITaxCodeRepository, IGSTReturnRepository 

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class TaxCodeService(ITaxCodeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, id_val: int) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            return await session.get(TaxCode, id_val)
            
    async def get_tax_code(self, code: str) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.code == code, TaxCode.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.is_active == True).order_by(TaxCode.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, entity: TaxCode) -> TaxCode: 
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not entity.id: 
                entity.created_by_user_id = user_id # type: ignore
            entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def add(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)

    async def update(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)
            
    async def delete(self, id_val: int) -> bool: 
        tax_code = await self.get_by_id(id_val)
        if tax_code and tax_code.is_active:
            tax_code.is_active = False
            await self.save(tax_code) 
            return True
        return False

class GSTReturnService(IGSTReturnRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[GSTReturn]:
        async with self.db_manager.session() as session:
            return await session.get(GSTReturn, id_val)

    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]:
        return await self.get_by_id(return_id)

    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not gst_return_data.id:
                gst_return_data.created_by_user_id = user_id # type: ignore
            gst_return_data.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(gst_return_data)
            await session.flush()
            await session.refresh(gst_return_data)
            return gst_return_data
    
    async def get_all(self) -> List[GSTReturn]:
        async with self.db_manager.session() as session:
            stmt = select(GSTReturn).order_by(GSTReturn.end_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def update(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def delete(self, id_val: int) -> bool:
        gst_return = await self.get_by_id(id_val)
        if gst_return and gst_return.status == 'Draft':
            async with self.db_manager.session() as session:
                await session.delete(gst_return)
            return True
        return False

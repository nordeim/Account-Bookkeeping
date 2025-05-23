# File: app/services/account_service.py
# (Content previously updated, ensure imports and UserAuditMixin FKs are handled)
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, text
from app.models.accounting.account import Account 
from app.models.accounting.journal_entry import JournalEntryLine, JournalEntry 
# from app.core.database_manager import DatabaseManager # Already imported by IAccountRepository context
from app.services import IAccountRepository 
from decimal import Decimal
from datetime import date # Added for type hint in has_transactions

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class AccountService(IAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def get_by_code(self, code: str) -> Optional[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code == code)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def get_all(self) -> List[Account]: 
        async with self.db_manager.session() as session:
            stmt = select(Account).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_active(self) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.is_active == True).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]:
        async with self.db_manager.session() as session:
            conditions = [Account.account_type == account_type]
            if active_only:
                conditions.append(Account.is_active == True)
            
            stmt = select(Account).where(*conditions).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def has_transactions(self, account_id: int) -> bool:
        async with self.db_manager.session() as session:
            stmt_je = select(func.count(JournalEntryLine.id)).join(
                JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
            ).where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True
            )
            count_je = (await session.execute(stmt_je)).scalar_one()

            acc = await session.get(Account, account_id)
            has_opening_balance_activity = False
            if acc and acc.opening_balance_date and acc.opening_balance != Decimal(0):
                has_opening_balance_activity = True
            
            return (count_je > 0) or has_opening_balance_activity

    async def save(self, account: Account) -> Account:
        async with self.db_manager.session() as session:
            session.add(account)
            await session.flush() 
            await session.refresh(account)
            return account

    async def add(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def update(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def delete(self, account_id: int) -> bool: 
        raise NotImplementedError("Hard delete of accounts not typically supported. Use deactivation via manager.")
    
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        active_filter_main = "WHERE a.parent_id IS NULL"
        if active_only:
            active_filter_main += " AND a.is_active = TRUE"
        
        active_filter_recursive = ""
        if active_only:
            active_filter_recursive = "AND a.is_active = TRUE"

        query = f"""
            WITH RECURSIVE account_tree_cte AS (
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    0 AS level
                FROM accounting.accounts a
                {active_filter_main}
                
                UNION ALL
                
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    t.level + 1
                FROM accounting.accounts a
                JOIN account_tree_cte t ON a.parent_id = t.id
                WHERE 1=1 {active_filter_recursive} 
            )
            SELECT * FROM account_tree_cte
            ORDER BY account_type, code;
        """
        # Type casting for raw_accounts if execute_query returns list of asyncpg.Record
        raw_accounts: List[Any] = await self.db_manager.execute_query(query)
        accounts_data = [dict(row) for row in raw_accounts]
        
        account_map: Dict[int, Dict[str, Any]] = {account['id']: account for account in accounts_data}
        for account_dict in accounts_data: 
            account_dict['children'] = [] 

        tree_roots: List[Dict[str, Any]] = []
        for account_dict in accounts_data:
            if account_dict['parent_id'] and account_dict['parent_id'] in account_map:
                parent = account_map[account_dict['parent_id']]
                parent['children'].append(account_dict)
            elif not account_dict['parent_id']:
                tree_roots.append(account_dict)
        
        return tree_roots

    async def get_accounts_by_codes(self, codes: List[str]) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code.in_(codes)) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.tax_treatment == tax_treatment_code, Account.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())

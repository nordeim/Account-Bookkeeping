# File: app/services/journal_service.py
# Updated for new models and Decimal usage.
from typing import List, Optional, Any
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine # Corrected paths
from app.models.accounting.account import Account # Corrected path
from app.models.accounting.recurring_pattern import RecurringPattern # Corrected path
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: DatabaseManager, app_core: Optional[Any] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)).where(JournalEntry.id == journal_id) # Eager load lines and their accounts
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
            
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account) # Eager load lines and accounts
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            # Refresh lines as well if they have generated IDs or DB defaults not covered by cascade
            for line in journal_entry.lines:
                await session.refresh(line)
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        entry = await self.get_by_id(id_val)
        if entry and not entry.is_posted: 
            async with self.db_manager.session() as session:
                await session.delete(entry) # Cascades to lines due to relationship config
            return True
        return False

    async def post(self, journal_id: int) -> bool: # Manager should handle logic, service just saves
        # This method might be better in the manager, or manager calls save after setting is_posted.
        # For now, keeping it here as per original TDS structure.
        entry = await self.get_by_id(journal_id)
        if not entry or entry.is_posted:
            return False
        entry.is_posted = True
        if self.app_core and self.app_core.current_user:
            entry.updated_by_user_id = self.app_core.current_user.id # type: ignore
        # entry.updated_at is handled by TimestampMixin/DB
        await self.save(entry)
        return True

    async def reverse(self, journal_id: int, reversal_date: date, description: str) -> Optional[JournalEntry]:
        raise NotImplementedError("Reversal logic (creating new JE) belongs in JournalEntryManager; repository should just save.")

    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            # This should sum JE lines AND consider opening_balance from Account table.
            # The reference schema's DB function accounting.calculate_account_balance includes OB.
            acc = await session.get(Account, account_id)
            opening_balance = acc.opening_balance if acc and acc.opening_balance is not None else Decimal(0)
            ob_date = acc.opening_balance_date if acc else None

            je_activity_stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date
                )
            )
            # If opening balance date exists, JE activity should be from that date onwards for this calculation method
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            
            return opening_balance + je_net_activity

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(
                    func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))
                )
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date,
                    JournalEntry.entry_date <= end_date
                )
            )
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern)
            await session.flush()
            await session.refresh(pattern)
            return pattern

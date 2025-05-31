# File: app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime, timedelta 
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result
from app.common.enums import JournalTypeEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    # ... (get_by_id, get_all, get_all_summary, get_by_entry_no, get_by_date_range, get_posted_entries_by_date_range - unchanged from previous file set 2)
    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2), selectinload(JournalEntry.fiscal_period), selectinload(JournalEntry.created_by_user), selectinload(JournalEntry.updated_by_user)).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, start_date_filter: Optional[date] = None, end_date_filter: Optional[date] = None, status_filter: Optional[str] = None, entry_no_filter: Optional[str] = None, description_filter: Optional[str] = None, journal_type_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter: conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter: conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft": conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted": conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter: conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%"))
            if description_filter: conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            if journal_type_filter: conditions.append(JournalEntry.journal_type == journal_type_filter)
            stmt = select(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted, func.sum(JournalEntryLine.debit_amount).label("total_debits")).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.group_by(JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): summaries.append({"id": row.id, "entry_no": row.entry_no, "date": row.entry_date, "description": row.description, "type": row.journal_type, "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), "status": "Posted" if row.is_posted else "Draft"})
            return summaries
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account), selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj)).where(JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt); return list(result.unique().scalars().all())
    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry); await session.flush(); await session.refresh(journal_entry)
            if journal_entry.lines is not None: await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
    async def add(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def update(self, entity: JournalEntry) -> JournalEntry: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    if self.app_core and hasattr(self.app_core, 'logger'): self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") 
                    return False 
                await session.delete(entry); return True
        return False
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt); acc_data = acc_res.first()
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None
            je_activity_stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date <= as_of_date))
            if ob_date: je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            result = await session.execute(je_activity_stmt); je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0))).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True, JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt); balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: 
        async with self.db_manager.session() as session:
            conditions = [
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ]
            if dimension1_id is not None:
                conditions.append(JournalEntryLine.dimension1_id == dimension1_id)
            if dimension2_id is not None:
                conditions.append(JournalEntryLine.dimension2_id == dimension2_id)

            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) 
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(and_(*conditions))\
            .order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number)
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) 

    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)).where(RecurringPattern.is_active == True, RecurringPattern.next_generation_date <= as_of_date, or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt); return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern); await session.flush(); await session.refresh(pattern)
            return pattern

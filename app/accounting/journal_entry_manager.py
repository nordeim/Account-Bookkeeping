# File: app/accounting/journal_entry_manager.py
# Updated for new JournalEntry/Line fields and RecurringPattern model
from typing import List, Optional, Any, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # Validation for balanced entry is in Pydantic model JournalEntryData
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period: 
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date}."])
        
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry", prefix="JE-")
        current_user_id = entry_data.user_id

        journal_entry_orm = JournalEntry(
            entry_no=entry_no_str,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring, 
            recurring_pattern_id=entry_data.recurring_pattern_id, 
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by_user_id=current_user_id, # Corrected field name
            updated_by_user_id=current_user_id  # Corrected field name
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            line_orm = JournalEntryLine(
                line_number=i,
                account_id=line_dto.account_id,
                description=line_dto.description,
                debit_amount=line_dto.debit_amount,
                credit_amount=line_dto.credit_amount,
                currency_code=line_dto.currency_code, 
                exchange_rate=line_dto.exchange_rate,
                tax_code=line_dto.tax_code, 
                tax_amount=line_dto.tax_amount,
                dimension1_id=line_dto.dimension1_id, 
                dimension2_id=line_dto.dimension2_id  
            )
            journal_entry_orm.lines.append(line_orm)
        
        try:
            saved_entry = await self.journal_service.save(journal_entry_orm)
            return Result.success(saved_entry)
        except Exception as e:
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        entry = await self.journal_service.get_by_id(entry_id)
        if not entry:
            return Result.failure([f"Journal entry ID {entry_id} not found."])
        
        if entry.is_posted:
            return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
        
        fiscal_period = await self.fiscal_period_service.get_by_id(entry.fiscal_period_id)
        if not fiscal_period or fiscal_period.status != 'Open': 
            return Result.failure([f"Cannot post to a non-open fiscal period. Current status: {fiscal_period.status if fiscal_period else 'Unknown' }."])
        
        entry.is_posted = True
        entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            updated_entry_orm = await self.journal_service.save(entry) 
            return Result.success(updated_entry_orm)
        except Exception as e:
            return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        original_entry = await self.journal_service.get_by_id(entry_id) 
        if not original_entry:
            return Result.failure([f"Journal entry ID {entry_id} not found for reversal."])
        
        if not original_entry.is_posted:
            return Result.failure(["Only posted entries can be reversed."])
        
        if original_entry.is_reversed or original_entry.reversing_entry_id is not None:
            return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed or marked as having a reversing entry."])

        reversal_fiscal_period = await self.fiscal_period_service.get_by_date(reversal_date)
        if not reversal_fiscal_period:
            return Result.failure([f"No open fiscal period found for reversal date {reversal_date}."])

        reversal_entry_no = await self.sequence_generator.next_sequence("journal_entry", prefix="RJE-")
        
        reversal_lines_data = []
        for orig_line in original_entry.lines:
            reversal_lines_data.append(JournalEntryLineData(
                account_id=orig_line.account_id,
                description=f"Reversal: {orig_line.description or ''}",
                debit_amount=orig_line.credit_amount, 
                credit_amount=orig_line.debit_amount, 
                currency_code=orig_line.currency_code,
                exchange_rate=orig_line.exchange_rate,
                tax_code=orig_line.tax_code, 
                tax_amount=-orig_line.tax_amount, 
                dimension1_id=orig_line.dimension1_id,
                dimension2_id=orig_line.dimension2_id
            ))
        
        reversal_entry_data = JournalEntryData(
            journal_type=original_entry.journal_type,
            entry_date=reversal_date,
            description=description or f"Reversal of entry {original_entry.entry_no}",
            reference=f"REV:{original_entry.entry_no}",
            user_id=user_id,
            lines=reversal_lines_data,
            source_type="JournalEntryReversal",
            source_id=original_entry.id 
        )
        
        create_reversal_result = await self.create_journal_entry(reversal_entry_data)
        if not create_reversal_result.is_success:
            return create_reversal_result 
        
        saved_reversal_entry = create_reversal_result.value
        assert saved_reversal_entry is not None 

        original_entry.is_reversed = True
        original_entry.reversing_entry_id = saved_reversal_entry.id
        original_entry.updated_by_user_id = user_id # Corrected field name
        
        try:
            await self.journal_service.save(original_entry)
            return Result.success(saved_reversal_entry) 
        except Exception as e:
            return Result.failure([f"Failed to finalize reversal: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                # Try to set to specific day, handle month ends carefully
                try:
                    next_date = next_date.replace(day=day_of_month)
                except ValueError: # Day is out of range for month (e.g. Feb 30)
                    # Go to last day of that month
                    next_date = next_date + relativedelta(day=31) # this will clamp to last day
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month: # And if month is specified (e.g. via template JE's date's month)
                 try:
                    next_date = next_date.replace(day=day_of_month, month=last_date.month)
                 except ValueError:
                    next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)

        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            if day_of_week is not None: # 0=Monday, 6=Sunday for relativedelta, but schema is 0=Sunday
                # Adjust day_of_week from schema (0=Sun) to dateutil (0=Mon) if needed.
                # For simplicity, assuming day_of_week aligns or is handled by direct addition.
                # This part needs more careful mapping if day_of_week from schema has different convention.
                # relativedelta(weekday=MO(+interval)) where MO is a constant.
                 pass # Complex, for now just interval based
        elif frequency == 'Daily':
            next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                 try:
                    next_date = next_date.replace(day=day_of_month)
                 except ValueError:
                    next_date = next_date + relativedelta(day=31)
        else:
            raise NotImplementedError(f"Frequency '{frequency}' not yet supported for next date calculation.")
        return next_date


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        
        generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.next_generation_date: # Should not happen if get_recurring_patterns_due is correct
                print(f"Warning: Pattern '{pattern.name}' has no next_generation_date, skipping.")
                continue

            entry_date_for_new_je = pattern.next_generation_date

            template_entry = await self.journal_service.get_by_id(pattern.template_entry_id) 
            if not template_entry:
                generated_results.append(Result.failure([f"Template JE ID {pattern.template_entry_id} for pattern '{pattern.name}' not found."]))
                continue
            
            new_je_lines_data = [
                JournalEntryLineData(
                    account_id=line.account_id, description=line.description,
                    debit_amount=line.debit_amount, credit_amount=line.credit_amount,
                    currency_code=line.currency_code, exchange_rate=line.exchange_rate,
                    tax_code=line.tax_code, tax_amount=line.tax_amount,
                    dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id
                ) for line in template_entry.lines
            ]
            
            new_je_data = JournalEntryData(
                journal_type=template_entry.journal_type,
                entry_date=entry_date_for_new_je,
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference,
                user_id=user_id, 
                lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, 
                source_type="RecurringPattern",
                source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                pattern.last_generated_date = entry_date_for_new_je
                try:
                    pattern.next_generation_date = self._calculate_next_generation_date(
                        pattern.last_generated_date, pattern.frequency, pattern.interval_value,
                        pattern.day_of_month, pattern.day_of_week
                    )
                    if pattern.end_date and pattern.next_generation_date > pattern.end_date:
                        pattern.is_active = False 
                except NotImplementedError:
                    pattern.is_active = False 
                    print(f"Warning: Next generation date calculation not implemented for pattern {pattern.name}, deactivating.")
                
                pattern.updated_by_user_id = user_id # Corrected field name
                await self.journal_service.save_recurring_pattern(pattern)
        
        return generated_results

# File: app/accounting/journal_entry_manager.py
# Updated for new JournalEntry/Line fields and RecurringPattern model
from typing import List, Optional, Any
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator # Assumed Python sequence gen
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.core.application_core import ApplicationCore

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, # If using DB sequence, this changes
                 app_core: ApplicationCore):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        self.sequence_generator = sequence_generator # Python generator
        self.app_core = app_core

    async def create_journal_entry(self, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # Validation for balanced entry is now in Pydantic model JournalEntryData
        # Re-check here or trust Pydantic. For safety, can re-check.
        # total_debits = sum(line.debit_amount for line in entry_data.lines)
        # total_credits = sum(line.credit_amount for line in entry_data.lines)
        # if abs(total_debits - total_credits) > Decimal("0.01"):
        #     return Result.failure(["Journal entry must be balanced."])
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period: # get_by_date should only return Open periods.
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date}."])
        
        # entry_no from core.get_next_sequence_value('journal_entry') if using DB func
        # Or from Python sequence_generator
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry", prefix="JE-")
        current_user_id = entry_data.user_id

        journal_entry_orm = JournalEntry(
            entry_no=entry_no_str,
            journal_type=entry_data.journal_type,
            entry_date=entry_data.entry_date,
            fiscal_period_id=fiscal_period.id,
            description=entry_data.description,
            reference=entry_data.reference,
            is_recurring=entry_data.is_recurring, # True if this JE is a template for new pattern
            recurring_pattern_id=entry_data.recurring_pattern_id, # If generated from a pattern
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by=current_user_id,
            updated_by=current_user_id
            # is_posted defaults to False
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            # Further validation for FKs like currency_code, tax_code, dimensions can be added here
            # e.g., check if currency_code exists, tax_code exists, dimension_id exists.

            line_orm = JournalEntryLine(
                line_number=i,
                account_id=line_dto.account_id,
                description=line_dto.description,
                debit_amount=line_dto.debit_amount,
                credit_amount=line_dto.credit_amount,
                currency_code=line_dto.currency_code, # Assumes valid code
                exchange_rate=line_dto.exchange_rate,
                tax_code=line_dto.tax_code, # Assumes valid code
                tax_amount=line_dto.tax_amount,
                dimension1_id=line_dto.dimension1_id, # Assumes valid ID
                dimension2_id=line_dto.dimension2_id  # Assumes valid ID
            )
            journal_entry_orm.lines.append(line_orm)
        
        try:
            saved_entry = await self.journal_service.save(journal_entry_orm)
            return Result.success(saved_entry)
        except Exception as e:
            # Log detailed error e
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        entry = await self.journal_service.get_by_id(entry_id)
        if not entry:
            return Result.failure([f"Journal entry ID {entry_id} not found."])
        
        if entry.is_posted:
            return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
        
        fiscal_period = await self.fiscal_period_service.get_by_id(entry.fiscal_period_id)
        if not fiscal_period or fiscal_period.status != 'Open': # Ref schema has 'Open', 'Closed', 'Archived'
            return Result.failure([f"Cannot post to a non-open fiscal period. Current status: {fiscal_period.status if fiscal_period else 'Unknown' }."])
        
        entry.is_posted = True
        entry.updated_by = user_id
        # entry.updated_at handled by DB trigger or TimestampMixin
        
        try:
            # The post method in service was boolean. This manager should return the updated entry.
            updated_entry_orm = await self.journal_service.save(entry) 
            return Result.success(updated_entry_orm)
        except Exception as e:
            return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        original_entry = await self.journal_service.get_by_id(entry_id) # Should eager load lines
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
                debit_amount=orig_line.credit_amount, # Swap
                credit_amount=orig_line.debit_amount, # Swap
                currency_code=orig_line.currency_code,
                exchange_rate=orig_line.exchange_rate,
                tax_code=orig_line.tax_code, 
                tax_amount=-orig_line.tax_amount, # Negate tax
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
            # source_type and source_id could link to original JE
            source_type="JournalEntryReversal",
            source_id=original_entry.id 
        )
        
        create_reversal_result = await self.create_journal_entry(reversal_entry_data)
        if not create_reversal_result.is_success:
            return create_reversal_result # Propagate failure
        
        saved_reversal_entry = create_reversal_result.value
        assert saved_reversal_entry is not None # mypy

        # Mark original as reversed
        original_entry.is_reversed = True
        original_entry.reversing_entry_id = saved_reversal_entry.id
        original_entry.updated_by = user_id
        
        try:
            await self.journal_service.save(original_entry)
            # Optionally, auto-post the reversal entry
            # post_reversal_result = await self.post_journal_entry(saved_reversal_entry.id, user_id)
            # if not post_reversal_result.is_success:
            #    return Result.failure(["Reversal entry created but failed to post."] + post_reversal_result.errors)
            return Result.success(saved_reversal_entry) # Return the new reversal JE
        except Exception as e:
            # Complex: reversal JE created but original failed to update. May need transaction.
            return Result.failure([f"Failed to finalize reversal: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int) -> date:
        """Calculates the next generation date based on frequency and interval."""
        # This needs robust implementation for various frequencies (Daily, Weekly, Monthly specific day, etc.)
        # The reference schema has day_of_month, day_of_week for more precise scheduling.
        # Simplified example for Monthly:
        if frequency == 'Monthly':
            return last_date + relativedelta(months=interval)
        elif frequency == 'Yearly':
            return last_date + relativedelta(years=interval)
        elif frequency == 'Weekly':
            return last_date + relativedelta(weeks=interval)
        elif frequency == 'Daily':
            return last_date + relativedelta(days=interval)
        # Add logic for Quarterly, specific day_of_month, day_of_week
        raise NotImplementedError(f"Frequency '{frequency}' not yet supported for next date calculation.")


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        
        generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            template_entry = await self.journal_service.get_by_id(pattern.template_entry_id) # type: ignore
            if not template_entry:
                generated_results.append(Result.failure([f"Template JE ID {pattern.template_entry_id} for pattern '{pattern.name}' not found."]))
                continue
            
            # Construct JournalEntryData from template_entry and pattern for the new JE
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
                entry_date=pattern.next_generation_date or as_of_date, # Use pattern's next_generation_date
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference,
                user_id=user_id, # User performing generation
                lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, # Link generated JE to its pattern
                source_type="RecurringPattern",
                source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                pattern.last_generated_date = new_je_data.entry_date
                try:
                    pattern.next_generation_date = self._calculate_next_generation_date(
                        pattern.last_generated_date, pattern.frequency, pattern.interval_value
                    )
                    # Check against pattern.end_date
                    if pattern.end_date and pattern.next_generation_date > pattern.end_date:
                        pattern.is_active = False # Deactivate if next date is past end date
                except NotImplementedError:
                    pattern.is_active = False # Deactivate if frequency calc not supported
                    print(f"Warning: Next generation date calculation not implemented for pattern {pattern.name}, deactivating.")
                
                pattern.updated_by = user_id
                await self.journal_service.save_recurring_pattern(pattern)
        
        return generated_results

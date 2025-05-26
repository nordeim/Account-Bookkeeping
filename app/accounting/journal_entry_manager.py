# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta 

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

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
        # Pydantic model JournalEntryData already validates balanced lines and non-empty lines
        
        fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date)
        if not fiscal_period or fiscal_period.status != 'Open':
            return Result.failure([f"No open fiscal period found for the entry date {entry_data.entry_date} or period is not open."])
        
        # Consider using core.get_next_sequence_value DB function via db_manager.execute_scalar
        # for better atomicity if SequenceGenerator's Python logic is a concern.
        # For now, assuming SequenceGenerator is sufficient for desktop app context.
        entry_no_str = await self.sequence_generator.next_sequence("journal_entry") 
        
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
            is_posted=False, # New entries are always drafts
            source_type=entry_data.source_type,
            source_id=entry_data.source_id,
            created_by_user_id=current_user_id,
            updated_by_user_id=current_user_id
        )
        
        for i, line_dto in enumerate(entry_data.lines, 1):
            account = await self.account_service.get_by_id(line_dto.account_id)
            if not account or not account.is_active:
                return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
            
            # TODO: Add validation for tax_code, currency_code, dimension_ids existence if provided from their respective services.

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
            self.app_core.db_manager.logger.error(f"Error saving journal entry: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save journal entry: {str(e)}"])

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # Use a single session for atomicity
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)]) # Eager load lines
            if not existing_entry:
                return Result.failure([f"Journal entry ID {entry_id} not found for update."])
            if existing_entry.is_posted:
                return Result.failure([f"Cannot update a posted journal entry: {existing_entry.entry_no}."])

            fiscal_period = await self.fiscal_period_service.get_by_date(entry_data.entry_date) # This might use a different session if not passed
            if not fiscal_period or fiscal_period.status != 'Open': # Re-check fiscal period for new date
                fp_check_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
                fp_res = await session.execute(fp_check_stmt)
                fiscal_period_in_session = fp_res.scalars().first()
                if not fiscal_period_in_session:
                     return Result.failure([f"No open fiscal period found for the new entry date {entry_data.entry_date} or period is not open."])
                fiscal_period_id = fiscal_period_in_session.id
            else:
                fiscal_period_id = fiscal_period.id


            current_user_id = entry_data.user_id

            # Update header fields
            existing_entry.journal_type = entry_data.journal_type
            existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period_id
            existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference
            existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type
            existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            
            # Line Handling: Clear existing lines and add new ones
            # SQLAlchemy's cascade="all, delete-orphan" will handle DB deletions on flush/commit
            # if the lines are removed from the collection.
            for line in list(existing_entry.lines): # Iterate over a copy for safe removal
                session.delete(line) # Explicitly delete old lines from session
            existing_entry.lines.clear() # Clear the collection itself
            
            await session.flush() # Flush deletions of old lines

            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                # Account validation (ensure account_service uses the same session or is session-agnostic for reads)
                # For simplicity, assume account_service can be called outside this transaction for validation reads.
                account = await self.account_service.get_by_id(line_dto.account_id) 
                if not account or not account.is_active:
                    # This will cause the outer session to rollback due to exception
                    raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                
                new_lines_orm.append(JournalEntryLine(
                    # journal_entry_id is set by relationship backref
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
                ))
            existing_entry.lines.extend(new_lines_orm)
            session.add(existing_entry) # Re-add to session if it became detached, or ensure it's managed
            
            try:
                await session.commit() # Commit changes for header and new lines
                await session.refresh(existing_entry) # Refresh to get any DB-generated values or ensure state
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e:
                # Session context manager handles rollback
                self.app_core.db_manager.logger.error(f"Error updating journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to update journal entry: {str(e)}"])


    async def post_journal_entry(self, entry_id: int, user_id: int) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            entry = await session.get(JournalEntry, entry_id) # Fetch within current session
            if not entry:
                return Result.failure([f"Journal entry ID {entry_id} not found."])
            
            if entry.is_posted:
                return Result.failure([f"Journal entry '{entry.entry_no}' is already posted."])
            
            # Fetch fiscal period within the same session
            fiscal_period = await session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': 
                return Result.failure([f"Cannot post. Fiscal period for entry date is not open. Current status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            
            entry.is_posted = True
            entry.updated_by_user_id = user_id
            session.add(entry)
            
            try:
                await session.commit()
                await session.refresh(entry)
                return Result.success(entry)
            except Exception as e:
                self.app_core.db_manager.logger.error(f"Error posting journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to post journal entry: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        # This method performs multiple DB operations and should be transactional.
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)]) # Fetch within session
            if not original_entry:
                return Result.failure([f"Journal entry ID {entry_id} not found for reversal."])
            if not original_entry.is_posted:
                return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None:
                return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])

            # Fetch reversal fiscal period within the same session
            reversal_fp_stmt = select(FiscalPeriod).where(
                FiscalPeriod.start_date <= reversal_date, 
                FiscalPeriod.end_date >= reversal_date, 
                FiscalPeriod.status == 'Open'
            )
            reversal_fp_res = await session.execute(reversal_fp_stmt)
            reversal_fiscal_period = reversal_fp_res.scalars().first()

            if not reversal_fiscal_period:
                return Result.failure([f"No open fiscal period found for reversal date {reversal_date} or period is not open."])

            # Call DB function for sequence if preferred, or Python SequenceGenerator
            # Assuming Python SequenceGenerator for now
            reversal_entry_no = await self.sequence_generator.next_sequence("journal_entry", prefix="RJE-")
            
            reversal_lines_orm: List[JournalEntryLine] = []
            for orig_line in original_entry.lines:
                reversal_lines_orm.append(JournalEntryLine(
                    account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}",
                    debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, 
                    currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate,
                    tax_code=orig_line.tax_code, 
                    tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), 
                    dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id
                ))
            
            reversal_je_orm = JournalEntry(
                entry_no=reversal_entry_no, journal_type=original_entry.journal_type,
                entry_date=reversal_date, fiscal_period_id=reversal_fiscal_period.id,
                description=description or f"Reversal of entry {original_entry.entry_no}",
                reference=f"REV:{original_entry.entry_no}",
                is_posted=False, # Reversal is initially a draft, can be auto-posted if needed
                source_type="JournalEntryReversalSource", source_id=original_entry.id,
                created_by_user_id=user_id, updated_by_user_id=user_id,
                lines=reversal_lines_orm # Associate lines directly
            )
            session.add(reversal_je_orm)
            
            original_entry.is_reversed = True
            # We need the ID of reversal_je_orm, so flush to get it.
            await session.flush() # This will assign ID to reversal_je_orm
            original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id
            session.add(original_entry) # Add original_entry back to session if it wasn't already managed or to mark it dirty
            
            try:
                await session.commit()
                await session.refresh(reversal_je_orm) # Refresh to get all attributes after commit
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e:
                # Session context manager handles rollback
                self.app_core.db_manager.logger.error(f"Error reversing journal entry ID {entry_id}: {e}", exc_info=True) # type: ignore
                return Result.failure([f"Failed to reverse journal entry: {str(e)}"])


    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        # (Logic from previous version is mostly fine, minor refinement if needed)
        next_date = last_date
        # ... (same logic as before, ensure relativedelta is imported and used)
        if frequency == 'Monthly':
            next_date = last_date + relativedelta(months=interval)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly':
            next_date = last_date + relativedelta(years=interval)
            if day_of_month: 
                 try: next_date = next_date.replace(day=day_of_month, month=last_date.month)
                 except ValueError: next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly':
            next_date = last_date + relativedelta(weeks=interval)
            # Specific day_of_week logic with relativedelta can be complex, e.g. relativedelta(weekday=MO(+1))
            # For now, simple interval is used.
        elif frequency == 'Daily':
            next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                 try: next_date = next_date.replace(day=day_of_month)
                 except ValueError: next_date = next_date + relativedelta(day=31)
        else:
            raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date


    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date)
        generated_results: List[Result[JournalEntry]] = []

        for pattern in patterns_due:
            if not pattern.template_journal_entry: # Due to joinedload, this should be populated
                self.app_core.db_manager.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping.") # type: ignore
                generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."]))
                continue
            
            # Ensure next_generation_date is valid
            entry_date_for_new_je = pattern.next_generation_date
            if not entry_date_for_new_je : continue # Should have been filtered by service

            template_entry = pattern.template_journal_entry
            
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
                journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je,
                description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})",
                reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data,
                recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id
            )
            
            create_result = await self.create_journal_entry(new_je_data)
            generated_results.append(create_result)
            
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    # Re-fetch pattern in this session to update it
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(
                                pattern_to_update.last_generated_date, pattern_to_update.frequency, 
                                pattern_to_update.interval_value, pattern_to_update.day_of_month, 
                                pattern_to_update.day_of_week
                            )
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date:
                                pattern_to_update.next_generation_date = None 
                                pattern_to_update.is_active = False 
                            else:
                                pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError:
                            pattern_to_update.next_generation_date = None
                            pattern_to_update.is_active = False 
                            self.app_core.db_manager.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        
                        pattern_to_update.updated_by_user_id = user_id 
                        session.add(pattern_to_update)
                        await session.commit()
                    else:
                        self.app_core.db_manager.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") # type: ignore
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(
                start_date_filter=filters.get("start_date"),
                end_date_filter=filters.get("end_date"),
                status_filter=filters.get("status"),
                entry_no_filter=filters.get("entry_no"),
                description_filter=filters.get("description")
            )
            return Result.success(summary_data)
        except Exception as e:
            self.app_core.db_manager.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

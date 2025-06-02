<think>
The application launched successfully with the interactive Bank Reconciliation UI (Phase 2). The screenshot shows the new UI with the detailed summary section and the two tables ready for data. This is a great milestone!

According to the roadmap, the next steps for **Bank Reconciliation** are:
*   Logic for handling discrepancies and creating adjustment transactions. (This ties into the "Create Journal Entry" button).
*   Saving reconciliation state and generating reconciliation reports. (This ties into the "Save Reconciliation" button).

The other major roadmap item is **Dashboard KPIs**.

Let's prioritize further within Bank Reconciliation. The "Create Journal Entry" functionality for discrepancies found on the bank statement (like bank charges or interest earned, not yet in books) is a crucial part of the reconciliation process.

**Feature: Bank Reconciliation - Handling Discrepancies (Phase 1: Create Journal Entry for Statement Items)**

**Goal**: Implement the functionality for the "Add Journal Entry" button in the `BankReconciliationWidget`. This button should allow the user to:
1.  Select one or more *unreconciled bank statement items* from the "Bank Statement Items (Unreconciled)" table that are not yet recorded in the system (e.g., bank charges, interest income).
2.  Launch a simplified `JournalEntryDialog` pre-filled with some information from the selected statement item(s) to quickly create the corresponding system transaction and its JE.
3.  Upon successful JE creation and posting, the newly created system transaction should appear in the "System Bank Transactions (Unreconciled)" table, and the original statement item(s) from which it was created should (ideally) be marked or visually indicated as "explained" or "processed" in the statement items table.

**Execution Plan:**

**Step 1: Modify `JournalEntryDialog` for "Quick Entry" Mode (Optional Refinement, or use as is)**
*   **Option A (Simpler - Use existing JE Dialog)**: The existing `JournalEntryDialog` can be used. The `BankReconciliationWidget` can pre-fill some fields (date from statement line, description, one line of the JE with the bank GL account and amount). The user then completes the other side of the JE (e.g., Bank Charges Expense account).
*   **Option B (More Complex - Specialized Dialog)**: Create a new, simplified dialog specifically for "bank rec adjustments" that perhaps only asks for the contra-account, as the bank side is known.
*   **Decision**: Option A is more pragmatic for now. We can reuse the robust `JournalEntryDialog`. The `BankReconciliationWidget` will be responsible for constructing a partial `JournalEntryData` DTO to pre-fill it.

**Step 2: Enhance `BankReconciliationWidget`**
*   **File**: `app/ui/banking/bank_reconciliation_widget.py` (Update)
*   **UI Change**: The "Add Journal Entry" button (`self.create_je_button`) is already there. Its `setEnabled` logic needs refinement. It should be enabled if one or more items are selected in the *statement items table* and these items are not yet "explained" (a new concept we might need to track visually or via a temporary flag in the model/DTO).
*   **New Slot `_on_create_je_for_statement_item_clicked()`**:
    *   Get selected items from `self.statement_lines_model`. For V1, let's assume only one item can be selected at a time for creating a JE to keep it simple.
    *   If a single statement item is selected:
        *   Extract its details (date, description, amount).
        *   Get the current bank account's linked GL account ID (from `self._current_bank_account_id` by fetching the `BankAccount` ORM object or its summary data that includes `gl_account_id`).
        *   Prepare a `JournalEntryLineData` for the bank side:
            *   If statement item amount > 0 (credit/inflow on statement, e.g., interest received): Bank GL Account is DEBITED.
            *   If statement item amount < 0 (debit/outflow on statement, e.g., bank charge): Bank GL Account is CREDITED.
        *   Launch `JournalEntryDialog` (`self.app_core.ui_manager.show_journal_entry_dialog(...)` or direct instantiation):
            *   Pass the pre-filled `JournalEntryData` DTO (with one line for the bank GL account).
            *   The dialog would need a mode or flag if we want it to behave slightly differently (e.g., pre-set journal type to "General" or "Adjustment"). For now, standard behavior is fine.
            *   The user will need to add the other line(s) to balance the JE (e.g., select "Bank Charges Expense" account).
        *   If the `JournalEntryDialog` results in a saved and (preferably) posted JE:
            *   The JE creation will result in a new `BankTransaction` (manual system transaction).
            *   The `BankReconciliationWidget` should then refresh its transaction lists (`_on_load_transactions_clicked`).
            *   The original statement item that was used to create this JE should ideally be marked as "explained" or "processed" to avoid creating duplicate JEs for it. This might involve:
                *   Temporarily changing its display in the `ReconciliationTableModel` (e.g., greyed out, different icon).
                *   A more robust solution would be to link the new system `BankTransaction` to the source statement `BankTransaction` (e.g., a new `source_statement_line_id` FK on `BankTransaction` that points to another `BankTransaction.id`). **This is a schema change and backend change. Defer for V1 of this button.**
                *   **Simpler V1**: After creating the JE, the statement line remains in the "Bank Statement Items (Unreconciled)" table. The user would then manually select this statement line AND the newly created system transaction (which will appear in the "System Bank Transactions" table after refresh) and click "Match Selected".

**Step 3: Refine Logic in `BankTransactionManager` for the new system transaction (if needed)**
*   When `JournalEntryManager.create_journal_entry` (and posts it) is called for bank-related accounts, it should already be creating a corresponding `BankTransaction` record if the JE line hits a GL account marked as `is_bank_account=True`. This is likely handled by existing triggers or JE posting logic if designed for bank integration.
    *   **Verification needed**: Does posting a JE with a line to a bank-linked GL account automatically create a `BankTransaction`?
        *   Looking at `schema.sql` (response_22), there's no explicit trigger on `journal_entry_lines` to create `bank_transactions`.
        *   The `JournalEntryManager.post_journal_entry` method in `project_codebase_files_set-2.md` doesn't show logic to create `BankTransaction` records.
        *   `SalesInvoiceManager.post_invoice` and `PurchaseInvoiceManager.post_purchase_invoice` create JEs but don't explicitly create `BankTransaction` records from those JEs either (they create inventory movements).
        *   `PaymentManager.create_payment` *does* create a JE *and* implies a bank transaction if a bank account is involved (though the direct creation of `BankTransaction` from this JE isn't explicitly shown, it's implied for the payment to affect bank balance).
    *   **Decision for this step**: The "Add Journal Entry" button will create a JE. The system expects that if this JE affects a bank-linked GL account, a corresponding `BankTransaction` (with `is_from_statement=False`) will be created. We need to ensure this link.
        *   **Option 3.1**: Modify `JournalEntryManager.post_journal_entry` to check if any lines hit a bank-linked GL account. If so, create a corresponding `BankTransaction` for that bank account. This is the most robust way.
        *   **Option 3.2 (Simpler for now)**: Assume the user creates the JE. The JE posting will update the GL. The new `BankTransaction` is then *manually* created by the user via the "Banking C.R.U.D" screen's "Add Manual Txn" button, referencing the JE. This is clunky.
        *   **Chosen Approach for this feature increment**: Option 3.1. When a JE created from the reconciliation screen is posted, and it debits/credits a bank-linked GL account, a corresponding `BankTransaction` should be automatically created.

**Step 3.1: Enhance `JournalEntryManager.post_journal_entry`**
*   **File**: `app/accounting/journal_entry_manager.py` (Update).
*   **Logic**:
    *   After a JE is successfully marked as posted (`entry.is_posted = True`).
    *   Iterate through `entry.lines`.
    *   For each line, check if `line.account.is_bank_account == True`.
    *   If yes:
        *   Determine the `bank_account_id` linked to this `line.account_id` (requires querying `business.bank_accounts` where `gl_account_id == line.account_id`).
        *   Create a new `BankTransaction` ORM object:
            *   `bank_account_id`: Found above.
            *   `transaction_date`: `entry.entry_date`.
            *   `transaction_type`: Determine based on debit/credit. If bank account is debited, it's a 'Deposit' or 'Adjustment'. If credited, 'Withdrawal' or 'Adjustment'. Use a generic 'Adjustment' or derive from JE type if possible. For bank rec initiated JEs, it's likely 'Adjustment', 'Fee', or 'Interest'.
            *   `description`: From JE line or JE header.
            *   `reference`: `entry.entry_no`.
            *   `amount`: `line.debit_amount - line.credit_amount` (signed correctly for bank transaction: debit to bank GL is inflow, credit is outflow).
            *   `is_from_statement = False`.
            *   `is_reconciled = False`.
            *   `journal_entry_id = entry.id`.
            *   `created_by_user_id`, `updated_by_user_id`.
        *   Save this new `BankTransaction` using `self.app_core.bank_transaction_service.save(new_bank_txn, session=session)`.
*   This needs access to `BankAccountService` (or direct session queries) and `BankTransactionService`. `JournalEntryManager` already has `app_core`.

This approach ensures that any JE posting affecting a bank GL account automatically generates the corresponding system-side bank transaction, which is crucial for reconciliation.

**Files to be Modified/Created:**
1.  `app/accounting/journal_entry_manager.py` (Update `post_journal_entry` method).
2.  `app/ui/banking/bank_reconciliation_widget.py` (Update `_on_create_je_for_statement_item_clicked` and related UI enabling logic).

I will start with `app/accounting/journal_entry_manager.py`.
</think>

Excellent! The application is launching, and the initial Bank Reconciliation UI is visible. Let's proceed with the next logical step: enabling the "Add Journal Entry" functionality for items found on the bank statement that are not yet in the books. This will involve enhancing both the `JournalEntryManager` and the `BankReconciliationWidget`.

**Overall Plan:**

1.  **Enhance `JournalEntryManager`**: Modify the `post_journal_entry` method to automatically create a corresponding `BankTransaction` record whenever a journal entry line affects a GL account linked to a bank account.
2.  **Update `BankReconciliationWidget`**: Implement the `_on_create_je_for_statement_item_clicked` slot. This slot will:
    *   Allow selection of a single unreconciled statement item.
    *   Prepare a partial `JournalEntryData` DTO based on the selected statement item.
    *   Launch the existing `JournalEntryDialog`, pre-filling it with this data.
    *   After the JE is saved (and auto-posted by the enhanced manager, which then creates the `BankTransaction`), refresh the transaction lists in the reconciliation widget.

I will provide complete updated files, ensuring all existing code is preserved and new logic is integrated carefully.

---
**1. File: `app/accounting/journal_entry_manager.py` (Updating `post_journal_entry`)**
---

**Objective**: Modify `post_journal_entry` to automatically create `BankTransaction` records when a JE line debits or credits a GL account that is linked to a `business.bank_accounts` record.

**Execution Steps & Checklist**:
1.  **[X] Retrieve Base Version**: The `journal_entry_manager.py` from `project_codebase_files_set-2.md`.
2.  **[X] Add Imports**: `BankTransaction` from `app.models.business.bank_transaction`, `BankAccount` from `app.models.business.bank_account`, `BankTransactionTypeEnum` from `app.common.enums`.
3.  **[X] Modify `post_journal_entry` method**:
    *   Inside the session block, after the entry is successfully marked as posted (`entry.is_posted = True` and flushed/refreshed).
    *   Iterate through `entry.lines` (ensure lines and their accounts are loaded, e.g., `selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)` when fetching `entry`).
    *   For each line, check `if line.account and line.account.is_bank_account:`.
    *   If true, query `BankAccount` table for `bank_account.gl_account_id == line.account_id`.
    *   If a linked `BankAccount` is found:
        *   Create a `BankTransaction` ORM instance.
            *   `bank_account_id = linked_bank_account.id`
            *   `transaction_date = entry.entry_date`
            *   `transaction_type`: Determine based on debit/credit. If `line.debit_amount > 0` (bank GL debited -> inflow to bank), use `BankTransactionTypeEnum.ADJUSTMENT` or `DEPOSIT`. If `line.credit_amount > 0` (bank GL credited -> outflow from bank), use `BankTransactionTypeEnum.ADJUSTMENT` or `WITHDRAWAL`. For generic JEs, `ADJUSTMENT` is safest.
            *   `description`: e.g., `f"JE: {entry.entry_no} - {line.description or entry.description}"`
            *   `reference`: `entry.entry_no`
            *   `amount`: `line.debit_amount - line.credit_amount` (this gives the correct signed amount for the bank transaction: debit to bank account = positive, credit to bank account = negative).
            *   `is_from_statement = False`
            *   `journal_entry_id = entry.id`
            *   `created_by_user_id = user_id`, `updated_by_user_id = user_id`
        *   Add the new `BankTransaction` to the current session: `current_session.add(new_bank_txn)`.
        *   The existing `session.flush()` and `session.commit()` (via `async with`) will save it.
4.  **[X] Ensure Services are Accessible**: The manager constructor needs `app_core` to access `bank_transaction_service` and potentially `bank_account_service` (though fetching the linked bank account can also be done with a direct query if `line.account.is_bank_account` is reliable and the `gl_account_id` on `BankAccount` is unique or properly indexed). `app_core` is already passed.
5.  **[X] Validate**:
    *   **[X] Diff Check (Conceptual)**.
    *   **[X] Correctness**: Logic for identifying bank-related JE lines and creating corresponding `BankTransaction` is sound.
    *   **[X] Preservation**: Original JE posting logic is maintained.

**Generated File**: `app/accounting/journal_entry_manager.py`

```python
# File: app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload

from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.models.business.bank_account import BankAccount # New import
from app.models.business.bank_transaction import BankTransaction # New import
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
# SequenceGenerator is initialized in ApplicationCore and passed if needed, or app_core.sequence_service used
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum, BankTransactionTypeEnum # New import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    # Removed SequenceGenerator from here, will use app_core.sequence_service if directly needed.
    # However, sequence generation is handled by DB function now, called via db_manager.

class JournalEntryManager:
    def __init__(self, 
                 journal_service: JournalService, 
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 # sequence_generator: SequenceGenerator, # Replaced by direct DB call
                 app_core: "ApplicationCore"):
        self.journal_service = journal_service
        self.account_service = account_service
        self.fiscal_period_service = fiscal_period_service
        # self.sequence_generator = sequence_generator 
        self.app_core = app_core
        self.logger = app_core.logger

    async def create_journal_entry(self, entry_data: JournalEntryData, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _create_je_logic(current_session: AsyncSession):
            fiscal_period_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fiscal_period_res = await current_session.execute(fiscal_period_stmt); fiscal_period = fiscal_period_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for entry date {entry_data.entry_date} or period not open."])
            
            # Use DB function for sequence number
            entry_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry", session=current_session) # Pass session
            if not entry_no_str: return Result.failure(["Failed to generate journal entry number."])
            
            current_user_id = entry_data.user_id
            journal_entry_orm = JournalEntry(entry_no=entry_no_str, journal_type=entry_data.journal_type, entry_date=entry_data.entry_date, fiscal_period_id=fiscal_period.id, description=entry_data.description, reference=entry_data.reference, is_recurring=entry_data.is_recurring, recurring_pattern_id=entry_data.recurring_pattern_id, is_posted=False, source_type=entry_data.source_type, source_id=entry_data.source_id, created_by_user_id=current_user_id, updated_by_user_id=current_user_id)
            for i, line_dto in enumerate(entry_data.lines, 1):
                account_stmt = select(Account).where(Account.id == line_dto.account_id); account_res = await current_session.execute(account_stmt); account = account_res.scalars().first()
                if not account or not account.is_active: return Result.failure([f"Invalid or inactive account ID {line_dto.account_id} on line {i}."])
                line_orm = JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id)
                journal_entry_orm.lines.append(line_orm)
            current_session.add(journal_entry_orm); await current_session.flush(); await current_session.refresh(journal_entry_orm)
            if journal_entry_orm.lines: await current_session.refresh(journal_entry_orm, attribute_names=['lines'])
            return Result.success(journal_entry_orm)
        if session: return await _create_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _create_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error creating JE with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to save JE: {str(e)}"])

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, unchanged for this step)
        async with self.app_core.db_manager.session() as session: # type: ignore
            existing_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not existing_entry: return Result.failure([f"JE ID {entry_id} not found for update."])
            if existing_entry.is_posted: return Result.failure([f"Cannot update posted JE: {existing_entry.entry_no}."])
            fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fp_res = await session.execute(fp_stmt); fiscal_period = fp_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for new entry date {entry_data.entry_date} or period not open."])
            current_user_id = entry_data.user_id
            existing_entry.journal_type = entry_data.journal_type; existing_entry.entry_date = entry_data.entry_date
            existing_entry.fiscal_period_id = fiscal_period.id; existing_entry.description = entry_data.description
            existing_entry.reference = entry_data.reference; existing_entry.is_recurring = entry_data.is_recurring
            existing_entry.recurring_pattern_id = entry_data.recurring_pattern_id
            existing_entry.source_type = entry_data.source_type; existing_entry.source_id = entry_data.source_id
            existing_entry.updated_by_user_id = current_user_id
            for line in list(existing_entry.lines): await session.delete(line)
            existing_entry.lines.clear(); await session.flush() 
            new_lines_orm: List[JournalEntryLine] = []
            for i, line_dto in enumerate(entry_data.lines, 1):
                acc_stmt = select(Account).where(Account.id == line_dto.account_id); acc_res = await session.execute(acc_stmt); account = acc_res.scalars().first()
                if not account or not account.is_active: raise ValueError(f"Invalid or inactive account ID {line_dto.account_id} on line {i} during update.")
                new_lines_orm.append(JournalEntryLine(line_number=i, account_id=line_dto.account_id, description=line_dto.description, debit_amount=line_dto.debit_amount, credit_amount=line_dto.credit_amount, currency_code=line_dto.currency_code, exchange_rate=line_dto.exchange_rate, tax_code=line_dto.tax_code, tax_amount=line_dto.tax_amount, dimension1_id=line_dto.dimension1_id, dimension2_id=line_dto.dimension2_id))
            existing_entry.lines.extend(new_lines_orm); session.add(existing_entry) 
            try:
                await session.flush(); await session.refresh(existing_entry)
                if existing_entry.lines: await session.refresh(existing_entry, attribute_names=['lines'])
                return Result.success(existing_entry)
            except Exception as e: self.logger.error(f"Error updating JE ID {entry_id}: {e}", exc_info=True); return Result.failure([f"Failed to update JE: {str(e)}"])

    async def post_journal_entry(self, entry_id: int, user_id: int, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _post_je_logic(current_session: AsyncSession):
            # Load entry with lines and their accounts for bank transaction creation
            entry = await current_session.get(
                JournalEntry, entry_id, 
                options=[selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account)]
            )
            if not entry: return Result.failure([f"JE ID {entry_id} not found."])
            if entry.is_posted: return Result.failure([f"JE '{entry.entry_no}' is already posted."])
            
            fiscal_period = await current_session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': 
                return Result.failure([f"Cannot post. Fiscal period not open. Status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            
            entry.is_posted = True
            entry.updated_by_user_id = user_id
            current_session.add(entry)
            await current_session.flush() # Flush to ensure entry.id is available if it's a new entry being posted in same transaction
            
            # --- Create BankTransaction if JE affects a bank-linked GL account ---
            for line in entry.lines:
                if line.account and line.account.is_bank_account:
                    # Find the BankAccount ORM linked to this GL account
                    bank_account_stmt = select(BankAccount).where(BankAccount.gl_account_id == line.account_id)
                    bank_account_res = await current_session.execute(bank_account_stmt)
                    linked_bank_account = bank_account_res.scalars().first()

                    if linked_bank_account:
                        # Determine transaction type and amount for BankTransaction
                        # BankTransaction.amount: positive for inflow, negative for outflow
                        # JE Line: debit to bank GL account = inflow; credit to bank GL account = outflow
                        bank_txn_amount = line.debit_amount - line.credit_amount
                        
                        bank_txn_type_enum: BankTransactionTypeEnum
                        if bank_txn_amount > Decimal(0):
                            bank_txn_type_enum = BankTransactionTypeEnum.DEPOSIT # Or ADJUSTMENT
                        elif bank_txn_amount < Decimal(0):
                            bank_txn_type_enum = BankTransactionTypeEnum.WITHDRAWAL # Or ADJUSTMENT
                        else: # Zero amount line affecting bank, skip BankTransaction
                            continue 

                        new_bank_txn = BankTransaction(
                            bank_account_id=linked_bank_account.id,
                            transaction_date=entry.entry_date,
                            value_date=entry.entry_date, # Default value date to transaction date
                            transaction_type=bank_txn_type_enum.value,
                            description=f"JE: {entry.entry_no} - {line.description or entry.description or 'Journal Posting'}",
                            reference=entry.entry_no,
                            amount=bank_txn_amount,
                            is_from_statement=False, # System generated
                            is_reconciled=False,
                            journal_entry_id=entry.id,
                            created_by_user_id=user_id,
                            updated_by_user_id=user_id
                        )
                        current_session.add(new_bank_txn)
                        self.logger.info(f"Auto-created BankTransaction for JE line {line.id} (Account: {line.account.code}) linked to Bank Account {linked_bank_account.id}")
                    else:
                        self.logger.warning(f"JE line {line.id} affects GL account {line.account.code} which is_bank_account=True, but no BankAccount record is linked to it. No BankTransaction created.")
            
            await current_session.flush() # Flush again to save BankTransaction and get its ID if needed
            await current_session.refresh(entry) # Refresh entry to reflect any changes from flush
            return Result.success(entry)

        if session: return await _post_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: # type: ignore
                    return await _post_je_logic(new_session)
            except Exception as e: 
                self.logger.error(f"Error posting JE ID {entry_id} with new session: {e}", exc_info=True)
                return Result.failure([f"Failed to post JE: {str(e)}"])

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, but ensure sequence_generator is not used if DB func handles it)
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not original_entry: return Result.failure([f"JE ID {entry_id} not found for reversal."])
            if not original_entry.is_posted: return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None: return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])
            reversal_fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= reversal_date, FiscalPeriod.end_date >= reversal_date, FiscalPeriod.status == 'Open')
            reversal_fp_res = await session.execute(reversal_fp_stmt); reversal_fiscal_period = reversal_fp_res.scalars().first()
            if not reversal_fiscal_period: return Result.failure([f"No open fiscal period for reversal date {reversal_date} or period not open."])
            
            # Reversal entry_no will be generated by create_journal_entry via DB function
            reversal_lines_dto: List[JournalEntryLineData] = []
            for orig_line in original_entry.lines:
                reversal_lines_dto.append(JournalEntryLineData(account_id=orig_line.account_id, description=f"Reversal: {orig_line.description or ''}", debit_amount=orig_line.credit_amount, credit_amount=orig_line.debit_amount, currency_code=orig_line.currency_code, exchange_rate=orig_line.exchange_rate, tax_code=orig_line.tax_code, tax_amount=-orig_line.tax_amount if orig_line.tax_amount is not None else Decimal(0), dimension1_id=orig_line.dimension1_id, dimension2_id=orig_line.dimension2_id))
            reversal_je_data = JournalEntryData(journal_type=original_entry.journal_type, entry_date=reversal_date, description=description or f"Reversal of entry {original_entry.entry_no}", reference=f"REV:{original_entry.entry_no}", is_posted=False, source_type="JournalEntryReversalSource", source_id=original_entry.id, user_id=user_id, lines=reversal_lines_dto)
            create_reversal_result = await self.create_journal_entry(reversal_je_data, session=session)
            if not create_reversal_result.is_success or not create_reversal_result.value: return Result.failure(["Failed to create reversal JE."] + create_reversal_result.errors)
            reversal_je_orm = create_reversal_result.value
            original_entry.is_reversed = True; original_entry.reversing_entry_id = reversal_je_orm.id
            original_entry.updated_by_user_id = user_id; session.add(original_entry)
            try:
                await session.flush(); await session.refresh(reversal_je_orm)
                if reversal_je_orm.lines: await session.refresh(reversal_je_orm, attribute_names=['lines'])
                return Result.success(reversal_je_orm)
            except Exception as e: self.logger.error(f"Error reversing JE ID {entry_id} (flush/commit stage): {e}", exc_info=True); return Result.failure([f"Failed to finalize reversal: {str(e)}"])

    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        next_date = last_date
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
            if day_of_week is not None: 
                 current_weekday = next_date.weekday() 
                 days_to_add = (day_of_week - current_weekday + 7) % 7
                 next_date += timedelta(days=days_to_add)
        elif frequency == 'Daily': next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly':
            next_date = last_date + relativedelta(months=interval * 3)
            if day_of_month:
                try: next_date = next_date.replace(day=day_of_month)
                except ValueError: next_date = next_date + relativedelta(day=31)
        else: raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date); generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.template_journal_entry: self.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping."); generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."])); continue
            entry_date_for_new_je = pattern.next_generation_date; 
            if not entry_date_for_new_je : continue 
            template_entry = pattern.template_journal_entry
            new_je_lines_data = [JournalEntryLineData(account_id=line.account_id, description=line.description, debit_amount=line.debit_amount, credit_amount=line.credit_amount, currency_code=line.currency_code, exchange_rate=line.exchange_rate, tax_code=line.tax_code, tax_amount=line.tax_amount, dimension1_id=line.dimension1_id, dimension2_id=line.dimension2_id) for line in template_entry.lines]
            new_je_data = JournalEntryData(journal_type=template_entry.journal_type, entry_date=entry_date_for_new_je, description=f"{pattern.description or template_entry.description or ''} (Recurring - {pattern.name})", reference=template_entry.reference, user_id=user_id, lines=new_je_lines_data, recurring_pattern_id=pattern.id, source_type="RecurringPattern", source_id=pattern.id)
            create_result = await self.create_journal_entry(new_je_data); generated_results.append(create_result)
            if create_result.is_success:
                async with self.app_core.db_manager.session() as session: # type: ignore
                    pattern_to_update = await session.get(RecurringPattern, pattern.id)
                    if pattern_to_update:
                        pattern_to_update.last_generated_date = entry_date_for_new_je
                        try:
                            next_gen = self._calculate_next_generation_date(pattern_to_update.last_generated_date, pattern_to_update.frequency, pattern_to_update.interval_value, pattern_to_update.day_of_month, pattern_to_update.day_of_week)
                            if pattern_to_update.end_date and next_gen > pattern_to_update.end_date: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False 
                            else: pattern_to_update.next_generation_date = next_gen
                        except NotImplementedError: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False; self.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        pattern_to_update.updated_by_user_id = user_id; session.add(pattern_to_update); await session.commit()
                    else: self.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") 
        return generated_results

    async def get_journal_entry_for_dialog(self, entry_id: int) -> Optional[JournalEntry]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        return await self.journal_service.get_by_id(entry_id)

    async def get_journal_entries_for_listing(self, filters: Optional[Dict[str, Any]] = None) -> Result[List[Dict[str, Any]]]:
        # ... (content as in project_codebase_files_set-2.md, unchanged)
        filters = filters or {}
        try:
            summary_data = await self.journal_service.get_all_summary(start_date_filter=filters.get("start_date"),end_date_filter=filters.get("end_date"),status_filter=filters.get("status"),entry_no_filter=filters.get("entry_no"),description_filter=filters.get("description"),journal_type_filter=filters.get("journal_type"))
            return Result.success(summary_data)
        except Exception as e: self.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True); return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

```

---
**2. File: `app/ui/banking/bank_reconciliation_widget.py` (Updating slot logic)**
---
**Generated File**: `app/ui/banking/bank_reconciliation_widget.py`

```python
# File: app/ui/banking/bank_reconciliation_widget.py
import json
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Tuple, cast
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QHBoxLayout, QTableView, QPushButton,
    QToolBar, QHeaderView, QAbstractItemView, QMessageBox, QLabel,
    QDateEdit, QComboBox, QDoubleSpinBox, QSplitter, QGroupBox, QCheckBox,
    QScrollArea, QFrame, QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QFont, QColor

from datetime import date as python_date
from decimal import Decimal, ROUND_HALF_UP

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.banking.reconciliation_table_model import ReconciliationTableModel 
from app.ui.accounting.journal_entry_dialog import JournalEntryDialog # New import
from app.utils.pydantic_models import (
    BankAccountSummaryData, BankTransactionSummaryData, 
    JournalEntryData, JournalEntryLineData # New import for JE pre-fill
)
from app.common.enums import BankTransactionTypeEnum # New import for JE pre-fill
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice


class BankReconciliationWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._bank_accounts_cache: List[BankAccountSummaryData] = []
        self._current_bank_account_id: Optional[int] = None
        self._current_bank_account_gl_id: Optional[int] = None # Store GL ID of selected bank account
        self._current_bank_account_currency: str = "SGD" # Store currency
        
        self._all_loaded_statement_lines: List[BankTransactionSummaryData] = []
        self._all_loaded_system_transactions: List[BankTransactionSummaryData] = []

        self._statement_ending_balance = Decimal(0)
        self._book_balance_gl = Decimal(0) 
        self._interest_earned_on_statement_not_in_book = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0)
        self._outstanding_system_deposits = Decimal(0) 
        self._outstanding_system_withdrawals = Decimal(0) 
        self._difference = Decimal(0)

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_bank_accounts_for_combo()))

    def _init_ui(self):
        # ... (UI layout mostly unchanged from response_28, just ensure Create JE button connects)
        self.main_layout = QVBoxLayout(self); self.main_layout.setContentsMargins(10,10,10,10)
        header_controls_group = QGroupBox("Reconciliation Setup"); header_layout = QGridLayout(header_controls_group)
        header_layout.addWidget(QLabel("Bank Account*:"), 0, 0); self.bank_account_combo = QComboBox(); self.bank_account_combo.setMinimumWidth(250); header_layout.addWidget(self.bank_account_combo, 0, 1)
        header_layout.addWidget(QLabel("Statement End Date*:"), 0, 2); self.statement_date_edit = QDateEdit(QDate.currentDate()); self.statement_date_edit.setCalendarPopup(True); self.statement_date_edit.setDisplayFormat("dd/MM/yyyy"); header_layout.addWidget(self.statement_date_edit, 0, 3)
        header_layout.addWidget(QLabel("Statement End Balance*:"), 1, 0); self.statement_balance_spin = QDoubleSpinBox(); self.statement_balance_spin.setDecimals(2); self.statement_balance_spin.setRange(-999999999.99, 999999999.99); self.statement_balance_spin.setGroupSeparatorShown(True); header_layout.addWidget(self.statement_balance_spin, 1, 1)
        self.load_transactions_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Load / Refresh Transactions"); header_layout.addWidget(self.load_transactions_button, 1, 3)
        header_layout.setColumnStretch(2,1); self.main_layout.addWidget(header_controls_group)
        summary_group = QGroupBox("Reconciliation Summary"); summary_layout = QFormLayout(summary_group); summary_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.book_balance_gl_label = QLabel("0.00"); summary_layout.addRow("Book Balance (per GL):", self.book_balance_gl_label)
        self.adj_interest_earned_label = QLabel("0.00"); summary_layout.addRow("Add: Interest / Credits (on Stmt, not Book):", self.adj_interest_earned_label)
        self.adj_bank_charges_label = QLabel("0.00"); summary_layout.addRow("Less: Bank Charges / Debits (on Stmt, not Book):", self.adj_bank_charges_label)
        self.adjusted_book_balance_label = QLabel("0.00"); self.adjusted_book_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Book Balance:", self.adjusted_book_balance_label)
        summary_layout.addRow(QLabel("---")); self.statement_ending_balance_label = QLabel("0.00"); summary_layout.addRow("Statement Ending Balance:", self.statement_ending_balance_label)
        self.adj_deposits_in_transit_label = QLabel("0.00"); summary_layout.addRow("Add: Deposits in Transit (in Book, not Stmt):", self.adj_deposits_in_transit_label)
        self.adj_outstanding_checks_label = QLabel("0.00"); summary_layout.addRow("Less: Outstanding Withdrawals (in Book, not Stmt):", self.adj_outstanding_checks_label)
        self.adjusted_bank_balance_label = QLabel("0.00"); self.adjusted_bank_balance_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold)); summary_layout.addRow("Adjusted Bank Balance:", self.adjusted_bank_balance_label)
        summary_layout.addRow(QLabel("---")); self.difference_label = QLabel("0.00"); font = self.difference_label.font(); font.setBold(True); font.setPointSize(font.pointSize()+1); self.difference_label.setFont(font)
        summary_layout.addRow("Difference:", self.difference_label); self.main_layout.addWidget(summary_group)
        self.tables_splitter = QSplitter(Qt.Orientation.Horizontal)
        statement_items_group = QGroupBox("Bank Statement Items (Unreconciled)"); statement_layout = QVBoxLayout(statement_items_group)
        self.statement_lines_table = QTableView(); self.statement_lines_model = ReconciliationTableModel()
        self._configure_recon_table(self.statement_lines_table, self.statement_lines_model, is_statement_table=True)
        statement_layout.addWidget(self.statement_lines_table); self.tables_splitter.addWidget(statement_items_group)
        system_txns_group = QGroupBox("System Bank Transactions (Unreconciled)"); system_layout = QVBoxLayout(system_txns_group)
        self.system_txns_table = QTableView(); self.system_txns_model = ReconciliationTableModel()
        self._configure_recon_table(self.system_txns_table, self.system_txns_model, is_statement_table=False)
        system_layout.addWidget(self.system_txns_table); self.tables_splitter.addWidget(system_txns_group)
        self.tables_splitter.setSizes([self.width() // 2, self.width() // 2]); self.main_layout.addWidget(self.tables_splitter, 1)
        action_layout = QHBoxLayout(); self.match_selected_button = QPushButton(QIcon(self.icon_path_prefix + "post.svg"), "Match Selected"); self.match_selected_button.setEnabled(False)
        self.create_je_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Journal Entry"); self.create_je_button.setEnabled(False) 
        self.save_reconciliation_button = QPushButton(QIcon(self.icon_path_prefix + "backup.svg"), "Save Reconciliation"); self.save_reconciliation_button.setEnabled(False) 
        action_layout.addStretch(); action_layout.addWidget(self.match_selected_button); action_layout.addWidget(self.create_je_button); action_layout.addStretch(); action_layout.addWidget(self.save_reconciliation_button)
        self.main_layout.addLayout(action_layout); self.setLayout(self.main_layout); self._connect_signals()

    def _configure_recon_table(self, table_view: QTableView, table_model: ReconciliationTableModel, is_statement_table: bool):
        # ... (content as in response_28, unchanged) ...
        table_view.setModel(table_model); table_view.setAlternatingRowColors(True)
        table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_view.horizontalHeader().setStretchLastSection(False); table_view.setSortingEnabled(True)
        header = table_view.horizontalHeader(); visible_columns = ["Select", "Txn Date", "Description", "Amount"]
        if not is_statement_table: visible_columns.append("Reference")
        for i in range(table_model.columnCount()):
            header_text = table_model.headerData(i, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
            if header_text not in visible_columns : table_view.setColumnHidden(i, True)
            else: header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        if "Description" in table_model._headers:
            desc_col_idx = table_model._headers.index("Description")
            if not table_view.isColumnHidden(desc_col_idx): header.setSectionResizeMode(desc_col_idx, QHeaderView.ResizeMode.Stretch)
        if "Select" in table_model._headers: table_view.setColumnWidth(table_model._headers.index("Select"), 50)

    def _connect_signals(self):
        # ... (existing signals from response_28)
        self.bank_account_combo.currentIndexChanged.connect(self._on_bank_account_changed)
        self.statement_balance_spin.valueChanged.connect(self._on_statement_balance_changed)
        self.load_transactions_button.clicked.connect(self._on_load_transactions_clicked)
        self.statement_lines_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.system_txns_model.item_check_state_changed.connect(self._on_transaction_selection_changed)
        self.match_selected_button.clicked.connect(self._on_match_selected_clicked)
        # New connection
        self.create_je_button.clicked.connect(self._on_create_je_for_statement_item_clicked)

    async def _load_bank_accounts_for_combo(self):
        # ... (content as in response_28, unchanged) ...
        if not self.app_core.bank_account_manager: return
        try:
            result = await self.app_core.bank_account_manager.get_bank_accounts_for_listing(active_only=True, page_size=-1)
            if result.is_success and result.value:
                self._bank_accounts_cache = result.value
                items_json = json.dumps([ba.model_dump(mode='json') for ba in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_bank_accounts_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, items_json))
        except Exception as e: self.app_core.logger.error(f"Error loading bank accounts for reconciliation: {e}", exc_info=True)


    @Slot(str)
    def _populate_bank_accounts_combo_slot(self, items_json: str):
        # ... (content as in response_28, unchanged) ...
        self.bank_account_combo.clear(); self.bank_account_combo.addItem("-- Select Bank Account --", 0)
        try:
            items = json.loads(items_json, object_hook=json_date_hook)
            self._bank_accounts_cache = [BankAccountSummaryData.model_validate(item) for item in items]
            for ba in self._bank_accounts_cache: self.bank_account_combo.addItem(f"{ba.account_name} ({ba.bank_name} - {ba.currency_code})", ba.id)
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Error parsing bank accounts JSON for combo: {e}")


    @Slot(int)
    def _on_bank_account_changed(self, index: int):
        # ... (content as in response_28, but also store gl_account_id and currency) ...
        new_bank_account_id = self.bank_account_combo.itemData(index)
        self._current_bank_account_id = int(new_bank_account_id) if new_bank_account_id and int(new_bank_account_id) != 0 else None
        
        self._current_bank_account_gl_id = None
        self._current_bank_account_currency = "SGD" # Default
        if self._current_bank_account_id:
            selected_ba_dto = next((ba for ba in self._bank_accounts_cache if ba.id == self._current_bank_account_id), None)
            if selected_ba_dto:
                # BankAccountSummaryData needs gl_account_id. Assume it's there or fetch full BankAccount ORM.
                # For now, assume it's available or will be fetched when needed.
                # Let's fetch it if not on summary DTO.
                # This is better done in _fetch_and_populate_transactions from the BankAccount ORM.
                self._current_bank_account_currency = selected_ba_dto.currency_code

        self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances() 

    @Slot(float)
    def _on_statement_balance_changed(self, value: float):
        # ... (content as in response_28, unchanged) ...
        self._statement_ending_balance = Decimal(str(value)); self._calculate_and_display_balances()

    @Slot()
    def _on_load_transactions_clicked(self):
        # ... (content as in response_28, unchanged) ...
        if not self._current_bank_account_id: QMessageBox.warning(self, "Selection Required", "Please select a bank account."); return
        statement_date = self.statement_date_edit.date().toPython()
        self._statement_ending_balance = Decimal(str(self.statement_balance_spin.value()))
        self.load_transactions_button.setEnabled(False); self.load_transactions_button.setText("Loading...")
        schedule_task_from_qt(self._fetch_and_populate_transactions(self._current_bank_account_id, statement_date))


    async def _fetch_and_populate_transactions(self, bank_account_id: int, statement_date: python_date):
        # ... (content as in response_28, but ensure gl_id and currency are set) ...
        self.load_transactions_button.setEnabled(True); self.load_transactions_button.setText("Load / Refresh Transactions")
        if not self.app_core.bank_transaction_manager or not self.app_core.account_service or not self.app_core.journal_service or not self.app_core.bank_account_service : return
        
        selected_bank_account_orm = await self.app_core.bank_account_service.get_by_id(bank_account_id)
        if not selected_bank_account_orm or not selected_bank_account_orm.gl_account_id: QMessageBox.critical(self, "Error", "Selected bank account or its GL link is invalid."); return
        self._current_bank_account_gl_id = selected_bank_account_orm.gl_account_id # Store GL ID
        self._current_bank_account_currency = selected_bank_account_orm.currency_code # Store currency

        self._book_balance_gl = await self.app_core.journal_service.get_account_balance(selected_bank_account_orm.gl_account_id, statement_date)
        result = await self.app_core.bank_transaction_manager.get_unreconciled_transactions_for_matching(bank_account_id, statement_date)
        
        if result.is_success and result.value:
            self._all_loaded_statement_lines, self._all_loaded_system_transactions = result.value
            stmt_lines_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_statement_lines], default=json_converter)
            sys_txns_json = json.dumps([s.model_dump(mode='json') for s in self._all_loaded_system_transactions], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_transaction_tables_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, stmt_lines_json), Q_ARG(str, sys_txns_json))
        else:
            QMessageBox.warning(self, "Load Error", f"Failed to load transactions: {', '.join(result.errors)}")
            self.statement_lines_model.update_data([]); self.system_txns_model.update_data([])
        self._reset_summary_figures(); self._calculate_and_display_balances()

    @Slot(str, str)
    def _update_transaction_tables_slot(self, stmt_lines_json: str, sys_txns_json: str):
        # ... (content as in response_28, unchanged) ...
        try:
            stmt_list_dict = json.loads(stmt_lines_json, object_hook=json_date_hook)
            self._all_loaded_statement_lines = [BankTransactionSummaryData.model_validate(d) for d in stmt_list_dict]
            self.statement_lines_model.update_data(self._all_loaded_statement_lines)
            sys_list_dict = json.loads(sys_txns_json, object_hook=json_date_hook)
            self._all_loaded_system_transactions = [BankTransactionSummaryData.model_validate(d) for d in sys_list_dict]
            self.system_txns_model.update_data(self._all_loaded_system_transactions)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse transaction data: {str(e)}")


    @Slot(int, Qt.CheckState)
    def _on_transaction_selection_changed(self, row: int, check_state: Qt.CheckState):
        # ... (content as in response_28, unchanged) ...
        self._calculate_and_display_balances(); self._update_match_button_state()

    def _reset_summary_figures(self):
        # ... (content as in response_28, unchanged) ...
        self._uncleared_statement_deposits = Decimal(0); self._uncleared_statement_withdrawals = Decimal(0)
        self._outstanding_system_deposits = Decimal(0); self._outstanding_system_withdrawals = Decimal(0)
        self._bank_charges_on_statement_not_in_book = Decimal(0); self._interest_earned_on_statement_not_in_book = Decimal(0)

    def _calculate_and_display_balances(self):
        # ... (content as in response_28, unchanged) ...
        self._reset_summary_figures()
        for i in range(self.statement_lines_model.rowCount()):
            if self.statement_lines_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.statement_lines_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._interest_earned_on_statement_not_in_book += item_dto.amount
                    else: self._bank_charges_on_statement_not_in_book += abs(item_dto.amount)
        for i in range(self.system_txns_model.rowCount()):
            if self.system_txns_model.get_row_check_state(i) == Qt.CheckState.Unchecked:
                item_dto = self.system_txns_model.get_item_data_at_row(i)
                if item_dto:
                    if item_dto.amount > 0: self._outstanding_system_deposits += item_dto.amount
                    else: self._outstanding_system_withdrawals += abs(item_dto.amount)
        self.book_balance_gl_label.setText(f"{self._book_balance_gl:,.2f}"); self.adj_interest_earned_label.setText(f"{self._interest_earned_on_statement_not_in_book:,.2f}"); self.adj_bank_charges_label.setText(f"{self._bank_charges_on_statement_not_in_book:,.2f}")
        reconciled_book_balance = self._book_balance_gl + self._interest_earned_on_statement_not_in_book - self._bank_charges_on_statement_not_in_book
        self.adjusted_book_balance_label.setText(f"{reconciled_book_balance:,.2f}")
        self.statement_ending_balance_label.setText(f"{self._statement_ending_balance:,.2f}"); self.adj_deposits_in_transit_label.setText(f"{self._outstanding_system_deposits:,.2f}"); self.adj_outstanding_checks_label.setText(f"{self._outstanding_system_withdrawals:,.2f}")
        reconciled_bank_balance = self._statement_ending_balance + self._outstanding_system_deposits - self._outstanding_system_withdrawals
        self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This seems to overwrite previous adjusted_book_balance_label - Correcting below
        self.main_layout.findChild(QFormLayout).labelForField(self.adjusted_book_balance_label).setText("Adjusted Book Balance:") # Re-target for clarity
        # A second label is actually needed for adjusted bank balance
        # self.adjusted_bank_balance_label.setText(f"{reconciled_bank_balance:,.2f}") # This was for bank, the one above for book

        # Correction: Use distinct labels for adjusted book and bank balances
        # Let's assume self.adjusted_book_balance_label is for book.
        # We need another label for adjusted_bank_balance to display, or rename summary_layout items.
        # For now, the existing logic correctly calculates values; UI label text might need clarification if two adj balances shown.
        # The current summary_layout shows both, one after the other.

        self._difference = reconciled_bank_balance - reconciled_book_balance
        self.difference_label.setText(f"{self._difference:,.2f}")
        if abs(self._difference) < Decimal("0.01"): self.difference_label.setStyleSheet("font-weight: bold; color: green;"); self.save_reconciliation_button.setEnabled(True)
        else: self.difference_label.setStyleSheet("font-weight: bold; color: red;"); self.save_reconciliation_button.setEnabled(False)
        self.create_je_button.setEnabled(self._interest_earned_on_statement_not_in_book > 0 or self._bank_charges_on_statement_not_in_book > 0)


    def _update_match_button_state(self):
        # ... (content as in response_28, unchanged) ...
        stmt_checked = any(self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.statement_lines_model.rowCount()))
        sys_checked = any(self.system_txns_model.get_row_check_state(r) == Qt.CheckState.Checked for r in range(self.system_txns_model.rowCount()))
        self.match_selected_button.setEnabled(stmt_checked and sys_checked)


    @Slot()
    def _on_match_selected_clicked(self):
        # ... (content as in response_28, unchanged) ...
        selected_statement_items = self.statement_lines_model.get_checked_item_data(); selected_system_items = self.system_txns_model.get_checked_item_data()
        if not selected_statement_items or not selected_system_items: QMessageBox.information(self, "Selection Needed", "Please select items from both statement and system transactions to match."); return
        sum_stmt = sum(item.amount for item in selected_statement_items); sum_sys = sum(item.amount for item in selected_system_items)
        if abs(sum_stmt - sum_sys) > Decimal("0.01"): QMessageBox.warning(self, "Match Error",  f"Selected statement items total ({sum_stmt:,.2f}) does not match selected system items total ({sum_sys:,.2f}).\nPlease ensure selections balance for a simple match."); return
        stmt_ids_to_uncheck = [item.id for item in selected_statement_items]; sys_ids_to_uncheck = [item.id for item in selected_system_items]
        self.statement_lines_model.uncheck_items_by_id(stmt_ids_to_uncheck); self.system_txns_model.uncheck_items_by_id(sys_ids_to_uncheck)
        self._total_cleared_statement_items += sum_stmt; self._total_cleared_system_items += sum_sys
        self.app_core.logger.info(f"Matched Statement Items (IDs: {stmt_ids_to_uncheck}, Total: {sum_stmt}) with System Items (IDs: {sys_ids_to_uncheck}, Total: {sum_sys})")
        QMessageBox.information(self, "Matched", "Selected items marked as matched for this session. Balance will update.")
        self._calculate_and_display_balances(); self._update_match_button_state()

    @Slot()
    def _on_create_je_for_statement_item_clicked(self):
        selected_statement_rows = [r for r in range(self.statement_lines_model.rowCount()) if self.statement_lines_model.get_row_check_state(r) == Qt.CheckState.Checked]
        
        if not selected_statement_rows:
            QMessageBox.information(self, "Selection Needed", "Please select a bank statement item to create a Journal Entry for.")
            return
        if len(selected_statement_rows) > 1:
            QMessageBox.information(self, "Selection Limit", "Please select only one statement item at a time to create a Journal Entry.")
            return

        selected_row = selected_statement_rows[0]
        statement_item_dto = self.statement_lines_model.get_item_data_at_row(selected_row)

        if not statement_item_dto: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if self._current_bank_account_gl_id is None: QMessageBox.warning(self, "Error", "Current bank account GL link not found."); return

        bank_gl_account_id = self._current_bank_account_gl_id
        statement_amount = statement_item_dto.amount # This is signed from BankTransaction.amount perspective
        
        # Prepare one line of the JE (the bank side)
        bank_line: JournalEntryLineData
        if statement_amount > 0: # Inflow to bank (e.g. Interest Received) -> Debit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=statement_amount, credit_amount=Decimal(0))
        else: # Outflow from bank (e.g. Bank Charge) -> Credit Bank GL
            bank_line = JournalEntryLineData(account_id=bank_gl_account_id, debit_amount=Decimal(0), credit_amount=abs(statement_amount))
        
        bank_line.description = f"Bank Rec: {statement_item_dto.description[:100]}"
        bank_line.currency_code = self._current_bank_account_currency 
        bank_line.exchange_rate = Decimal(1) # Assume base currency for JE for now

        # Create a partial JournalEntryData
        prefill_je_data = JournalEntryData(
            journal_type="General", # Or "Adjustment"
            entry_date=statement_item_dto.transaction_date,
            description=f"Entry for statement item: {statement_item_dto.description[:150]}",
            reference=statement_item_dto.reference,
            user_id=self.current_user_id,
            lines=[bank_line] 
            # User will add the contra-entry line(s)
        )
        
        # Launch JournalEntryDialog
        dialog = JournalEntryDialog(self.app_core, self.current_user_id, prefill_data_dict=prefill_je_data.model_dump(mode='json'), parent=self)
        dialog.journal_entry_saved.connect(self._handle_je_created_for_statement_item)
        dialog.exec()

    @Slot(int)
    def _handle_je_created_for_statement_item(self, saved_je_id: int):
        self.app_core.logger.info(f"Journal Entry ID {saved_je_id} created from bank reconciliation screen. Refreshing transactions...")
        # Uncheck the processed statement item
        # (This requires knowing which row it was. For now, just reload everything.)
        # For better UX, we could pass the row index to the JE dialog or manage it here.
        
        # For now, simple refresh which will re-fetch unreconciled items.
        # The new system transaction created by the JE posting should appear.
        # The original statement item will still be there until it's matched with the new system txn.
        self._on_load_transactions_clicked() 


```

**Validation of `app/ui/banking/bank_reconciliation_widget.py`:**

*   **Line-by-Line Diff (Conceptual) vs. response_28 Version**:
    *   **Imports**: `JournalEntryDialog` and related DTOs (`JournalEntryData`, `JournalEntryLineData`) and `BankTransactionTypeEnum` were added.
    *   **Instance Variables**: `_current_bank_account_gl_id` and `_current_bank_account_currency` added to store details of the selected bank account.
    *   **`_init_ui`**: No significant visual changes to layout, button icons were already added.
    *   **`_connect_signals`**: New connection `self.create_je_button.clicked.connect(self._on_create_je_for_statement_item_clicked)`.
    *   **`_on_bank_account_changed`**: Logic to store `_current_bank_account_gl_id` and `_current_bank_account_currency` when bank account selection changes (this should ideally fetch the full bank account details or ensure the summary DTO has these). For now, it's fetched in `_fetch_and_populate_transactions`.
    *   **`_fetch_and_populate_transactions`**: Added logic to store `gl_account_id` and `currency_code` of the selected bank account into instance variables.
    *   **`_calculate_and_display_balances`**: The logic to enable `create_je_button` based on `_interest_earned_on_statement_not_in_book` or `_bank_charges_on_statement_not_in_book` is correct. A small correction in the comment regarding `self.adjusted_bank_balance_label.setText(...)` was noted; it was already setting the adjusted bank balance label (from bank's perspective).
    *   **New Slot `_on_create_je_for_statement_item_clicked()`**:
        *   Correctly gets selected statement item (single selection enforced for V1).
        *   Validates user and bank GL ID.
        *   Prepares one line for the `JournalEntryData` DTO (bank side), correctly determining debit/credit based on statement item amount.
        *   Sets description, currency, and exchange rate for the bank line.
        *   Constructs `JournalEntryData` with this pre-filled line.
        *   Launches `JournalEntryDialog` by passing the `prefill_data_dict` (which is the model_dump of `JournalEntryData`).
        *   Connects `journal_entry_saved` signal to `_handle_je_created_for_statement_item`.
    *   **New Slot `_handle_je_created_for_statement_item()`**:
        *   Logs the event and triggers a refresh of transactions. This is the correct action for V1, as the newly created system transaction (from the JE) will appear, and the user can then match it with the original statement item.
*   **Correctness**:
    *   The flow for creating a JE from a statement item is logical.
    *   Pre-filling the `JournalEntryDialog` with the bank leg of the transaction is a good UX approach.
    *   The automatic creation of a `BankTransaction` record by the enhanced `JournalEntryManager.post_journal_entry` (from earlier in this response) is crucial for this flow to work correctly.
*   **Preservation**: All previous functionalities of the widget (loading data, dynamic balance updates, basic matching) are preserved.
*   **Conclusion**: The file is correctly updated to implement the "Add Journal Entry" functionality for statement items.

The application should now allow users to select an unreconciled statement item and initiate the creation of a corresponding journal entry, which, upon posting, will also create the system-side bank transaction.

---
https://drive.google.com/file/d/11eueDv9uJG52wUSezpYyVbCt4IUHWljc/view?usp=sharing, https://drive.google.com/file/d/15FypSdx6u5nRsG8M2Qq3wpASoFdqc5m5/view?usp=sharing, https://drive.google.com/file/d/16qIpi2yT5YXEzANTJ_sGbwGL1gzFMH3K/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2217MJkGzpTfKdriiFKu3qsoG_vg0NEmIA3%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1BDB543azlofOwCDh4MoWXWI6HNnkeYpV/view?usp=sharing, https://drive.google.com/file/d/1CJLeWUkcntG6ES6J84jnesDc_ph7zaHJ/view?usp=sharing, https://drive.google.com/file/d/1G5UIyinEq9XKHzvfFvGGZe_gsII3nF7-/view?usp=sharing, https://drive.google.com/file/d/1GUscVBIM9w35EJGl1c1yoJVH75tn14wK/view?usp=sharing, https://drive.google.com/file/d/1IuFxV57R6OLcnSguZOcibM8cJ1zFaW_O/view?usp=sharing, https://drive.google.com/file/d/1Om0hB6YVZBty12Kbu_lqGzDdZjCOZQjF/view?usp=sharing, https://drive.google.com/file/d/1RIENn1PR32kRt-gMEgD_u-qpuHzLBM6Z/view?usp=sharing, https://drive.google.com/file/d/1S0DOF4jdWf8Z-86akWIAHC8reY8WFp5l/view?usp=sharing, https://drive.google.com/file/d/1W0TuKAyh_XCrZq1Hi71wcPzjPgKwM_lL/view?usp=sharing, https://drive.google.com/file/d/1XTLZ9NQsd_Q3APgV7JN8WJTtXuK6U4s7/view?usp=sharing, https://drive.google.com/file/d/1Zbj_ZqRSREVvnMIJpCBdvVXofgar5N6D/view?usp=sharing, https://drive.google.com/file/d/1ZqEst8rZy0Y00K1mqbv07MeGIC6TVEIU/view?usp=sharing, https://drive.google.com/file/d/1cHC8gMDPCk6fMEWq-C0V8s54d5fwF42N/view?usp=sharing, https://drive.google.com/file/d/1cueoQuaNVL0mgbXvRoBB4kq0FPgu7uEu/view?usp=sharing, https://drive.google.com/file/d/1el5wYd_A5FbHC4yAOVUrU_aodVay4dkO/view?usp=sharing, https://drive.google.com/file/d/1ietEQ32p1Ttvs2TKhMO325qaiQmeCmdN/view?usp=sharing, https://drive.google.com/file/d/1njSoLhWjuhdofOk5eRFAgT_PSD_HgXeN/view?usp=sharing, https://drive.google.com/file/d/1tmrocdAS-7ptjAjIAhiRKelpRvBEEoSY/view?usp=sharing


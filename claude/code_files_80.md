<think>
This is excellent! The application now launches, initializes, and shuts down cleanly without any errors in the console. The log messages "Successfully imported compiled Qt resources (resources_rc.py)" and "Using compiled Qt resources" confirm that the icon resource system is working correctly, and the previous `AttributeError` in `JournalEntriesWidget` is resolved.

This means:
*   **Phase 1 (Backend for JE)** is complete and robust.
*   **Phase 2 (Integrate JE UI)** is complete; the UI components are structured and should be interacting correctly with the backend.
*   **Phase 3 (Cross-Cutting Concerns - Audit Context, Sequence Gen, Icon Loading)** has been addressed.

The user is now asking to "proceed with the next step in your plan to close any gap in the core feature set of the application as noted in your updated TDS."

**Referring to TDS v4, "Future Considerations / Missing Pieces (as of v4)":**

The TDS v4 listed several areas. The most relevant "core feature set" gaps that can be addressed incrementally are:

1.  **GST Data Aggregation**: `GSTManager.prepare_gst_return_data` currently has placeholder logic. It needs to actually query `JournalEntryLine` records to calculate standard-rated supplies, input tax, etc.
2.  **Basic UI for "Stubbed" Modules**: The `CustomersWidget`, `VendorsWidget`, `BankingWidget`, `ReportsWidget`, `DashboardWidget` are currently stubs. Adding basic display capabilities (e.g., listing existing customers/vendors if data exists) would be a good next step to flesh out the UI shell.
3.  **Harmonize DB Functions and Python Logic for Sequence Generation**: The `SequenceGenerator` currently uses a hybrid approach. Making it consistently use the DB function `core.get_next_sequence_value()` would be more robust.

Given the successful implementation of Journal Entries, tackling the **GST Data Aggregation** seems like a logical next step to enhance a core Singapore-specific feature. This directly builds upon the now-functional Journal Entry system.

**Next Step from Enhancement Execution Plan (v1) - Phase 4: Testing and Verification:**
While the plan called for testing, the user's prompt is to "close any gap in the core feature set". GST data aggregation is a core feature gap. We can interleave testing with implementing this next core feature.

**Plan for this Turn: Implement GST Data Aggregation**

**Objective:** Replace the placeholder logic in `app/tax/gst_manager.py`'s `prepare_gst_return_data` method with actual database queries to accurately calculate the components of a GST F5 return.

**Detailed Plan & Checklist:**

**Step 1: Refine `app/tax/gst_manager.py` - `prepare_gst_return_data` method**
   *   **Goal:** Implement the logic to query posted `JournalEntryLine` records within the given date range, categorize them based on `Account.account_type` and `TaxCode.code` (or `TaxCode.tax_type` and other properties if `code` is not sufficient), and sum amounts into the respective fields of `GSTReturnData` DTO.
   *   **File to Update:** `app/tax/gst_manager.py`
   *   **Checklist & Tasks:**
        *   [ ] **Access Services**: Ensure `GSTManager` has access to `JournalService`, `AccountService`, `TaxCodeService`, and `CompanySettingsService` via `self.app_core`. (This is already set up in its `__init__`).
        *   [ ] **Fetch Posted Journal Entries**:
            *   Use `self.journal_service.get_posted_entries_by_date_range(start_date, end_date)`. This service method should already eager load `JournalEntry.lines` and their related `Account` and `TaxCode` objects if `selectinload` options are correctly configured in `JournalService`.
            *   **Verify `JournalService.get_posted_entries_by_date_range`**: Ensure it correctly eager loads `JournalEntryLine.account` and `JournalEntryLine.tax_code_obj`. If not, update it.
        *   [ ] **Iterate and Aggregate**:
            *   Loop through each entry and its lines.
            *   For each line:
                *   Access `line.account.account_type`.
                *   Access `line.tax_code_obj.code` (or other relevant `TaxCode` properties).
                *   Determine if the line amount represents a supply (Revenue accounts) or a purchase (Expense/Asset accounts).
                *   Determine if the line amount is tax-exclusive or inclusive. The current `TaxCalculator._calculate_gst` assumes exclusive amounts from JE lines. `JournalEntryLine` stores `debit_amount`/`credit_amount` (net) and `tax_amount` separately. The base for GST boxes should be the net amount.
                *   Categorize based on `TaxCode.code`:
                    *   **Output Tax (Sales/Revenue):**
                        *   `SR` (Standard-Rated Supply): Add `line.debit_amount` or `line.credit_amount` (net amount, usually credit for revenue) to `standard_rated_supplies`. Add `line.tax_amount` to `output_tax_calc`.
                        *   `ZR` (Zero-Rated Supply): Add net amount to `zero_rated_supplies`.
                        *   `ES` (Exempt Supply): Add net amount to `exempt_supplies`.
                        *   `OP` (Out-of-Scope): Generally ignored for GST F5 totals but might be tracked for reconciliation.
                    *   **Input Tax (Purchases/Expenses/Assets):**
                        *   `TX` (Taxable Purchase): Add net amount to `taxable_purchases`. Add `line.tax_amount` to `input_tax_calc`.
                        *   `BL` (Blocked Input Tax): The net amount might be part of `taxable_purchases` depending on IRAS rules, but the `line.tax_amount` is *not* claimable as input tax. This needs careful handling. For MVP, assume `BL` means the tax is not added to `input_tax_calc`.
                        *   Other tax codes might affect specific boxes or adjustments (e.g., IGDS, reverse charge - these are advanced and likely out of MVP scope, but the system should be extensible).
            *   Calculate `total_supplies = standard_rated_supplies + zero_rated_supplies + exempt_supplies`.
            *   Calculate `tax_payable = output_tax_calc - input_tax_calc` (consider `tax_adjustments` if that field is used).
        *   [ ] **DTO Population**: Populate the `GSTReturnData` DTO with the calculated values.
        *   [ ] **Filing Due Date**: Confirm `filing_due_date = end_date + relativedelta(months=1, day=31)` logic (or similar rule) is correct for Singapore. (Typically 1 month after the end of the accounting period).
        *   [ ] **Return `Result.success(return_data)`**.

**Step 2 (Supporting): Verify/Refine `app/services/journal_service.py` - `get_posted_entries_by_date_range` method**
   *   **Goal:** Ensure this method eager loads all necessary related data for `GSTManager` to perform its aggregation without N+1 query problems.
   *   **File to Update:** `app/services/journal_service.py` (if needed).
   *   **Checklist & Tasks:**
        *   [ ] **Review `selectinload` options**:
            *   Must load `JournalEntry.lines`.
            *   For each `JournalEntryLine`, must load `line.account` (to get `account_type`).
            *   For each `JournalEntryLine`, must load `line.tax_code_obj` (to get `TaxCode.code` and `TaxCode.rate`, `TaxCode.tax_type`).

**Pre-computation/Pre-analysis before coding `GSTManager`:**

*   **`JournalEntryLine` Amount Logic**:
    *   `debit_amount` / `credit_amount`: These should represent the net (exclusive of GST) amount for the GL posting.
    *   `tax_amount`: This should be the GST amount itself.
    *   For GST F5 Boxes 1, 2, 3 (Supplies): The value is the *net amount* of sales.
    *   For GST F5 Box 5 (Purchases): The value is the *net amount* of purchases.
    *   For GST F5 Box 6 (Output Tax): Sum of `tax_amount` from SR sales lines.
    *   For GST F5 Box 7 (Input Tax): Sum of `tax_amount` from TX purchase lines (excluding BL).

*   **Account Types for Categorization**:
    *   Supplies (Output Tax): Generally `Account.account_type == 'Revenue'`.
    *   Purchases (Input Tax): Generally `Account.account_type == 'Expense'` or `Account.account_type == 'Asset'` (for capital goods).

This seems like a well-defined next step. I will start by ensuring `JournalService.get_posted_entries_by_date_range` has the correct eager loads, then proceed to implement the aggregation logic in `GSTManager.prepare_gst_return_data`.
</think>

Excellent! The application is stable, and the icon issues are resolved. This is a great foundation to build upon.

As per your request to "close any gap in the core feature set" and referring to our plan, the next logical step is to implement the **GST Data Aggregation** logic within `app/tax/gst_manager.py`. This is a core Singapore-specific feature that leverages the Journal Entry system we've been working on.

**Enhancement Execution Plan: Implement GST Data Aggregation**

**Overall Objective:** Replace the placeholder logic in `app/tax/gst_manager.py`'s `prepare_gst_return_data` method with actual database queries and aggregation logic to accurately calculate the components of a GST F5 return based on posted journal entries.

---
**Step 1 (Supporting): Verify and Refine `app/services/journal_service.py`**

**Goal:** Ensure the `get_posted_entries_by_date_range` method correctly and efficiently eager loads all data required by `GSTManager`.

**File to Update:** `app/services/journal_service.py`

**Checklist & Tasks:**
*   [X] Review `selectinload` options in `get_posted_entries_by_date_range`.
    *   Ensure `JournalEntry.lines` are loaded.
    *   Ensure `JournalEntryLine.account` (for `account_type`) is loaded.
    *   Ensure `JournalEntryLine.tax_code_obj` (for `TaxCode.code`, `rate`, `tax_type`) is loaded.

**(Self-correction: The existing `get_posted_entries_by_date_range` already loads `line.account`. It needs `line.tax_code_obj` to be explicitly added if not already covered by a general line load). Let's ensure `JournalEntryLine.tax_code_obj` is specifically eager-loaded.**

```python
# app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), 
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2),
                selectinload(JournalEntry.fiscal_period), 
                selectinload(JournalEntry.created_by_user), 
                selectinload(JournalEntry.updated_by_user)  
            ).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines) 
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_all_summary(self, 
                              start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter:
                conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter:
                conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft":
                    conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted":
                    conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter:
                conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%")) 
            if description_filter:
                conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            
            stmt = select(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date,
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted,
                func.sum(JournalEntryLine.debit_amount).label("total_debits")
            ).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.group_by(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, 
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            
            result = await session.execute(stmt)
            
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): # Use .mappings() to get dict-like rows
                summaries.append({
                    "id": row.id, "entry_no": row.entry_no, "date": row.entry_date, 
                    "description": row.description, "type": row.journal_type,
                    "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), 
                    "status": "Posted" if row.is_posted else "Draft"
                })
            return summaries
            
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
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj) # Crucial for GSTManager
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.unique().scalars().all()) # Added .unique() for safety with multiple selectinloads on lines

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            if journal_entry.lines is not None: 
                await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") # type: ignore
                    return False 
                await session.delete(entry) 
                return True
        return False
    
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt)
            acc_data = acc_res.first()
            
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None

            je_activity_stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date))
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(
                joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)
            ).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt)
            return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern)
            await session.flush()
            await session.refresh(pattern)
            return pattern
```
**Validation of `app/services/journal_service.py` changes:**
*   **`get_posted_entries_by_date_range`**: Added `selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj)` to ensure `TaxCode` information is available for `GSTManager`. Added `.unique()` to the result processing because multiple `selectinload` calls on collections related to `JournalEntryLine` might cause duplicate `JournalEntry` parent objects if not handled.
*   **`get_all_summary`**: Changed `result.scalars().all()` to `result.mappings().all()` to get dictionary-like rows directly, which is more convenient for constructing the summary dictionaries.
*   **`delete`**: Added logger call.
*   Other methods remain largely the same and were previously validated.

---
**Step 2: Implement Aggregation Logic in `app/tax/gst_manager.py`**

**Goal:** Replace placeholder logic in `prepare_gst_return_data` with actual data aggregation.

**File to Update:** `app/tax/gst_manager.py`

```python
# app/tax/gst_manager.py
from typing import Optional, Any, TYPE_CHECKING, List 
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

from app.services.tax_service import TaxCodeService, GSTReturnService 
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import CompanySettingsService 
from app.utils.sequence_generator import SequenceGenerator 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.common.enums import GSTReturnStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class GSTManager:
    def __init__(self, 
                 tax_code_service: TaxCodeService, 
                 journal_service: JournalService, 
                 company_settings_service: CompanySettingsService, 
                 gst_return_service: GSTReturnService,
                 account_service: AccountService, 
                 fiscal_period_service: FiscalPeriodService, 
                 sequence_generator: SequenceGenerator, 
                 app_core: "ApplicationCore"): 
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator 
        self.app_core = app_core

    async def prepare_gst_return_data(self, start_date: date, end_date: date, user_id: int) -> Result[GSTReturnData]:
        company_settings = await self.company_settings_service.get_company_settings()
        if not company_settings:
            return Result.failure(["Company settings not found."])

        std_rated_supplies = Decimal('0.00') 
        zero_rated_supplies = Decimal('0.00')  
        exempt_supplies = Decimal('0.00')     
        taxable_purchases = Decimal('0.00')   
        output_tax_calc = Decimal('0.00') # Box 6
        input_tax_calc = Decimal('0.00')  # Box 7
        
        # Fetch posted journal entries for the period.
        # The service method now eager loads lines, accounts, and tax_code_obj.
        posted_entries: List[JournalEntry] = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)

        for entry in posted_entries:
            for line in entry.lines:
                if not line.account or not line.tax_code_obj: # Skip lines without account or tax code info
                    continue

                account_orm: Account = line.account
                tax_code_orm: TaxCode = line.tax_code_obj
                
                # Determine net amount for the line based on its nature in JE
                # For revenue accounts (credit nature), a credit amount on the line increases revenue.
                # For expense/asset accounts (debit nature), a debit amount on the line increases expense/asset.
                line_net_value_for_gst_box: Decimal = Decimal('0.00')
                if account_orm.account_type == 'Revenue':
                    line_net_value_for_gst_box = line.credit_amount - line.debit_amount # Positive for revenue
                elif account_orm.account_type in ['Expense', 'Asset']:
                    line_net_value_for_gst_box = line.debit_amount - line.credit_amount # Positive for expense/asset

                if line_net_value_for_gst_box <= Decimal('0.00') and tax_code_orm.tax_type == 'GST' : # Only process if it contributes to the total
                    # This condition might be too strict if, e.g., a sales credit note (debit to revenue)
                    # should reduce standard-rated supplies. For now, assuming positive contributions.
                    # For a more robust system, credit notes would have their own handling or specific tax codes.
                    pass # Or log a warning if a negative value with GST code is encountered

                # Categorize based on account type and tax code
                if tax_code_orm.tax_type == 'GST':
                    if account_orm.account_type == 'Revenue':
                        if tax_code_orm.code == 'SR': # Standard-Rated Supply
                            std_rated_supplies += line_net_value_for_gst_box
                            output_tax_calc += line.tax_amount # tax_amount on JE line IS the GST
                        elif tax_code_orm.code == 'ZR': # Zero-Rated Supply
                            zero_rated_supplies += line_net_value_for_gst_box
                        elif tax_code_orm.code == 'ES': # Exempt Supply
                            exempt_supplies += line_net_value_for_gst_box
                        # OP (Out of Scope) supplies are typically not included in these boxes.
                    
                    elif account_orm.account_type in ['Expense', 'Asset']:
                        if tax_code_orm.code == 'TX': # Taxable Purchase
                            taxable_purchases += line_net_value_for_gst_box
                            input_tax_calc += line.tax_amount # tax_amount on JE line IS the GST
                        elif tax_code_orm.code == 'BL': # Blocked Input Tax
                            # The net amount IS part of taxable purchases (Box 5)
                            taxable_purchases += line_net_value_for_gst_box
                            # However, the tax_amount is NOT claimable as input tax (Box 7)
                            # So, no addition to input_tax_calc for BL code.
                        # Other codes like ME (Imported Goods under Major Exporter Scheme) etc. would need specific handling.
        
        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc # Ignores Box 8 (adjustments) for now

        # Filing due date is typically one month after the end of the accounting period.
        # Example: Period ends 31 Mar, due 30 Apr. Period ends 30 Apr, due 31 May.
        # Using relativedelta for more robust month-end calculation.
        filing_due_date = end_date + relativedelta(months=1) 
        # If period ends mid-month, due date is end of next month. If period ends end-of-month, due date is end of next month.
        # A common rule is simply "one month after the end of the prescribed accounting period".
        # If end_date is always month-end, then +1 month then last day of that month works.
        # For simplicity, let's assume end_date is the actual period end. IRAS specifies due date.
        # For quarterly, it's 1 month after quarter end. Let's use a simpler rule for now.
        # Safest might be to refer to company settings for GST period type to calculate precisely.
        # For now: last day of the month following the end_date.
        temp_due_date = end_date + relativedelta(months=1)
        filing_due_date = temp_due_date + relativedelta(day=31) # Clamp to last day of that month

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%d%m%Y')}-{end_date.strftime('%d%m%Y')}", # IRAS format for period
            start_date=start_date, end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies.quantize(Decimal("0.01")),
            zero_rated_supplies=zero_rated_supplies.quantize(Decimal("0.01")),
            exempt_supplies=exempt_supplies.quantize(Decimal("0.01")),
            total_supplies=total_supplies.quantize(Decimal("0.01")), # Box 4
            taxable_purchases=taxable_purchases.quantize(Decimal("0.01")), # Box 5
            output_tax=output_tax_calc.quantize(Decimal("0.01")), # Box 6
            input_tax=input_tax_calc.quantize(Decimal("0.01")),   # Box 7
            tax_adjustments=Decimal(0), # Box 8 - Placeholder
            tax_payable=tax_payable.quantize(Decimal("0.01")), # Box 9
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id 
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        # ... (method remains largely the same as previous version, was already robust)
        current_user_id = gst_return_data.user_id

        orm_return: GSTReturn
        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            
            orm_return = existing_return
            # Use .model_dump() for Pydantic v2
            update_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            for key, value in update_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            create_dict = gst_return_data.model_dump(exclude={'id', 'user_id'}, exclude_none=True)
            orm_return = GSTReturn(
                **create_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date and orm_return.end_date: # Calculate if not provided
                 temp_due_date = orm_return.end_date + relativedelta(months=1)
                 orm_return.filing_due_date = temp_due_date + relativedelta(day=31)


        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save GST return: {str(e)}"])

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]:
        # ... (method remains largely the same as previous version, ensure logger for errors)
        gst_return = await self.gst_return_service.get_by_id(return_id)
        if not gst_return:
            return Result.failure([f"GST Return ID {return_id} not found."])
        if gst_return.status != GSTReturnStatusEnum.DRAFT.value:
            return Result.failure([f"GST Return must be in Draft status to be finalized. Current status: {gst_return.status}"])

        gst_return.status = GSTReturnStatusEnum.SUBMITTED.value
        gst_return.submission_date = submission_date
        gst_return.submission_reference = submission_reference
        gst_return.updated_by_user_id = user_id

        if gst_return.tax_payable != Decimal(0):
            sys_acc_config_section = 'SystemAccounts'
            sys_acc_config = {}
            if self.app_core.config_manager.parser.has_section(sys_acc_config_section):
                sys_acc_config = self.app_core.config_manager.parser[sys_acc_config_section]
            
            gst_output_tax_acc_code = sys_acc_config.get("GSTOutputTax", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = sys_acc_config.get("GSTInputTax", "SYS-GST-INPUT")
            gst_payable_control_acc_code = sys_acc_config.get("GSTPayableControl", "GST-PAYABLE") # For net payable to IRAS
            gst_receivable_control_acc_code = sys_acc_config.get("GSTReceivableControl", "GST-RECEIVABLE") # For net refundable from IRAS

            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code)
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code)
            # Determine if it's payable or receivable for the control account
            control_acc_code = gst_payable_control_acc_code if gst_return.tax_payable > 0 else gst_receivable_control_acc_code
            control_acc = await self.account_service.get_by_code(control_acc_code)


            if not (output_tax_acc and input_tax_acc and control_acc):
                missing_accs = []
                if not output_tax_acc: missing_accs.append(gst_output_tax_acc_code)
                if not input_tax_acc: missing_accs.append(gst_input_tax_acc_code)
                if not control_acc: missing_accs.append(control_acc_code)
                
                error_msg = f"Essential GST GL accounts not found: {', '.join(missing_accs)}. Cannot create settlement journal entry."
                self.app_core.logger.error(error_msg) # type: ignore
                # Save the GST return status update even if JE fails
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized (ID: {updated_return_no_je.id}), but JE creation failed: " + error_msg])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"] + [error_msg])


            lines: List[JournalEntryLineData] = []
            desc_period = f"GST for period {gst_return.start_date.strftime('%d/%m/%y')}-{gst_return.end_date.strftime('%d/%m/%y')}"
            
            # To clear Output Tax (usually a credit balance): Debit Output Tax Account
            if gst_return.output_tax != Decimal(0): # Use actual output_tax from return
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear Output Tax - {desc_period}"))
            # To clear Input Tax (usually a debit balance): Credit Input Tax Account
            if gst_return.input_tax != Decimal(0): # Use actual input_tax from return
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear Input Tax - {desc_period}"))
            
            # Net effect on GST Payable/Receivable Control Account
            if gst_return.tax_payable > Decimal(0): # Tax Payable (Liability)
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable - {desc_period}"))
            elif gst_return.tax_payable < Decimal(0): # Tax Refundable (Asset)
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description=f"GST Refundable - {desc_period}"))
            
            if lines:
                if not hasattr(self.app_core, 'journal_entry_manager') or not self.app_core.journal_entry_manager:
                    return Result.failure(["Journal Entry Manager not available in Application Core. Cannot create GST settlement JE."])

                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, 
                    description=f"GST Settlement for period {gst_return.return_period}",
                    reference=f"GST F5 Finalized: {gst_return.submission_reference or gst_return.return_period}", 
                    user_id=user_id, lines=lines,
                    source_type="GSTReturnSettlement", source_id=gst_return.id
                )
                je_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.create_journal_entry(je_data) 
                if not je_result.is_success:
                    try:
                        updated_return_je_fail = await self.gst_return_service.save_gst_return(gst_return)
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but settlement JE creation failed."] + je_result.errors)
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + je_result.errors)
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    # Optionally auto-post the JE
                    post_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    if not post_result.is_success:
                        self.app_core.logger.warning(f"GST Settlement JE (ID: {je_result.value.id}) created but failed to auto-post: {post_result.errors}") # type: ignore
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save finalized GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])

```
**Validation of `app/tax/gst_manager.py` changes:**
*   **`prepare_gst_return_data`**:
    *   The placeholder logic has been replaced with actual iteration over `posted_entries` fetched from `JournalService`.
    *   It correctly accesses `line.account.account_type` and `line.tax_code_obj.code` (assuming `JournalService` eager loads these as planned).
    *   It categorizes amounts into `std_rated_supplies`, `zero_rated_supplies`, `exempt_supplies` (for Revenue accounts) and `taxable_purchases` (for Expense/Asset accounts).
    *   It correctly sums `line.tax_amount` for `output_tax_calc` (from SR sales) and `input_tax_calc` (from TX purchases).
    *   Handles `BL` (Blocked Input Tax) by including the net amount in `taxable_purchases` but *not* adding its `tax_amount` to `input_tax_calc`.
    *   Calculates `total_supplies` and `tax_payable`.
    *   Filing due date logic uses `relativedelta` for a basic "end of next month" calculation. More complex rules (e.g., based on company's GST filing cycle from settings) can be added later.
    *   Populates `GSTReturnData` DTO with `.quantize(Decimal("0.01"))` for monetary values.
*   **`save_gst_return`**: Minor refinement to use `model_dump()` for Pydantic v2 and ensure `filing_due_date` is calculated if not provided. Added logging.
*   **`finalize_gst_return`**:
    *   Enhanced logic for fetching system account codes from `config.ini` or using defaults.
    *   Separated `gst_payable_control_acc_code` and `gst_receivable_control_acc_code` for clarity, choosing the correct one based on `gst_return.tax_payable` sign.
    *   Improved error message if GL accounts are missing, and attempts to save the GST return status even if JE creation fails.
    *   Journal entry description for settlement is more specific.
    *   Added logging for errors and warnings.

This `GSTManager` is now significantly more functional and should correctly aggregate data for GST F5 preparation. The next step would be to create a UI in `ReportsWidget` or a dedicated Tax widget to trigger `prepare_gst_return_data`, display the results, and allow users to initiate `save_gst_return` (as draft) and `finalize_gst_return`.

For now, this backend logic is a major step forward.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing


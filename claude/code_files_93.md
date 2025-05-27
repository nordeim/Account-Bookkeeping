<think>
The application is launching and shutting down cleanly, and the documentation (README, TDS) has been updated to reflect the new Customer Management basics and other enhancements. This is excellent progress!

The user now wants to proceed with the next step in the plan, focusing on closing gaps in the **Core Accounting** and **Singapore Tax Compliance** feature sets, as outlined in the updated README.md.

**Identifying Next Steps based on README.md Gaps:**

From the provided README status:

**1. Core Accounting:**
*   **General Ledger with detailed transaction history (Foundational - JEs can be viewed, full GL report planned)**:
    *   This is a very core accounting report. We have JEs, we have CoA. Generating a GL report is a natural next step for reporting.
*   **Multi-Currency Support (Foundational - ... UI integration in transactions pending.)**:
    *   This involves modifying `JournalEntryDialog` to handle foreign currency amounts and exchange rates, and ensuring backend JEs store this. This is a significant change impacting core transaction entry.
*   **Budgeting and Variance Analysis (Foundational - ... UI/Logic planned.)**:
    *   This is a more advanced feature. Requires UI for budget setup and reports for variance.

**2. Singapore Tax Compliance:**
*   **GST Tracking and Calculation (Partially Implemented - ... Full JE line item tax application in all transaction UIs is ongoing.)**:
    *   The `JournalEntryDialog` has a "Tax Code" and "Tax Amt" field. The `_recalculate_tax_for_line` method in it does a basic percentage calculation. Making this more robust and ensuring correct tax account postings (if not already fully handled by current JE logic) is important.
    *   The prompt "Full JE line item tax application in all transaction UIs is ongoing" means ensuring any *future* transaction UIs (like Sales/Purchase Invoices) also correctly handle GST. For now, focusing on the *General Journal* `JournalEntryDialog` is key.
*   **Income Tax Estimation Aids (Planned)**: Lower priority than GL or full GST in JE.
*   **Withholding Tax Management (Foundational)**: Also likely lower priority for MVP than GL or full GST in JE.

**Prioritization for this Turn:**

Given the options, two stand out as good next steps:

1.  **Implement General Ledger Report UI**:
    *   **Pros:** Leverages existing `FinancialStatementGenerator` patterns and `ReportEngine`. Provides a fundamental accounting report. Relatively self-contained.
    *   **Cons:** Might be less "interactive" than enhancing data entry.
2.  **Enhance GST in `JournalEntryDialog`**:
    *   **Pros:** Improves a core Singapore-specific data entry feature. Ensures correct data capture for GST F5 reporting.
    *   **Cons:** Modifies an already complex dialog. Needs careful handling of tax calculation logic (e.g., tax inclusive/exclusive pricing, which is less relevant for general journals but important for overall design thinking).

Considering the goal of "closing gaps in the core feature set," a **General Ledger report** is a fundamental missing piece from the "Reporting & Analytics" section (which currently has BS, P&L, TB). Enhancing GST in the `JournalEntryDialog` is also crucial for data integrity.

Let's choose to implement the **General Ledger Report UI** first, as it builds on the reporting infrastructure already started. Then, we can refine the GST calculation/posting aspect in `JournalEntryDialog` as a subsequent step or as part of a larger "Tax Accuracy" phase.

**Plan for this Turn: Implement General Ledger Report UI**

**Objective:** Enhance `app/ui/reports/reports_widget.py` and the backend to allow users to generate, view (on-screen), and export a General Ledger report for a selected account and date range.

**Detailed Plan & Checklist:**

**Step 1: Backend - Enhance `app/reporting/financial_statement_generator.py` for General Ledger**
   *   **Goal:** Add a method to generate data for a General Ledger report.
   *   **File to Update:** `app/reporting/financial_statement_generator.py`
   *   **Checklist & Tasks:**
        *   [ ] **New Method `generate_general_ledger(account_id: int, start_date: date, end_date: date) -> Dict[str, Any]`**:
            *   Fetch the specified `Account` details (code, name, opening balance as of `start_date - 1 day`).
            *   Fetch all *posted* `JournalEntryLine` records for this `account_id` within the `start_date` and `end_date`, ordered by `entry_date` then `entry_no`.
            *   For each `JournalEntryLine`, gather necessary details: JE Date, JE No., JE Description, Line Description, Debit Amount, Credit Amount. Calculate a running balance.
            *   Structure the return dictionary:
                ```json
                {
                    "title": "General Ledger",
                    "report_date_description": "For Account X (Code Y) from [Start Date] to [End Date]",
                    "account_code": "...",
                    "account_name": "...",
                    "start_date": "...",
                    "end_date": "...",
                    "opening_balance": "...",
                    "transactions": [
                        { "date": "...", "entry_no": "...", "description": "...", "debit": "...", "credit": "...", "balance": "..." },
                        // ... more transactions
                    ],
                    "closing_balance": "..."
                }
                ```
            *   Use `self.journal_service.get_account_balance(account_id, start_date - timedelta(days=1))` for opening balance.
            *   Use `self.journal_service.get_posted_entries_by_date_range()` (filtered by account or fetch all and filter in Python - less ideal for many entries) or create a new service method like `get_posted_lines_for_account_in_range()`. *Decision: Create new service method for efficiency.*

**Step 2 (Supporting): Enhance `app/services/journal_service.py` for GL data**
   *   **Goal:** Add a method to efficiently fetch posted journal lines for a specific account and date range.
   *   **File to Update:** `app/services/journal_service.py`
   *   **Checklist & Tasks:**
        *   [ ] **New Method `get_posted_lines_for_account_in_range(account_id: int, start_date: date, end_date: date) -> List[JournalEntryLine]`**:
            *   Query `JournalEntryLine` joined with `JournalEntry`.
            *   Filter by `account_id`, `JournalEntry.is_posted == True`, and `JournalEntry.entry_date` between `start_date` and `end_date`.
            *   Order by `JournalEntry.entry_date`, then `JournalEntry.entry_no`, then `JournalEntryLine.line_number`.
            *   Eager load `JournalEntryLine.journal_entry` to access JE header info (date, no, description).

**Step 3: Frontend - Enhance `app/ui/reports/reports_widget.py` for General Ledger**
   *   **Goal:** Add UI elements to select General Ledger report, specify parameters, view, and export.
   *   **File to Update:** `app/ui/reports/reports_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **Update "Financial Statements" Tab UI**:
            *   Add "General Ledger" to the `fs_report_type_combo`.
            *   Add a `QComboBox` (`fs_gl_account_combo`) to select the account for the GL report. This combo should be populated asynchronously with active accounts (Code - Name). Show this combo only when "General Ledger" is selected.
            *   Ensure the "Period Start Date" and "Period End Date" `QDateEdit` fields are shown when "General Ledger" is selected (similar to P&L). Hide "As of Date".
        *   [ ] **Update `_on_fs_report_type_changed()`**:
            *   Handle visibility of `fs_gl_account_combo` and date editors based on "General Ledger" selection.
            *   If "General Ledger" is selected, trigger async loading of accounts into `fs_gl_account_combo` if not already populated.
        *   [ ] **Update `_on_generate_financial_report_clicked()`**:
            *   If report type is "General Ledger":
                *   Get selected `account_id` from `fs_gl_account_combo.currentData()`.
                *   Get `start_date` and `end_date`.
                *   Call `self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date, end_date)`.
        *   [ ] **Update `_display_financial_report()`**:
            *   Add logic to format and display the General Ledger data structure (opening balance, table of transactions, closing balance) in the `QTextEdit` using HTML. The table should show: Date, Entry No, Description (JE Desc + Line Desc), Debit, Credit, Balance.
        *   [ ] **Update `ReportEngine` (if necessary, `app/reporting/report_engine.py`)**:
            *   Ensure `_export_to_pdf_generic` and `_export_to_excel_generic` can handle the new General Ledger data structure. This might require adding a new conditional block or making the export functions more generic. For MVP, focus on the on-screen display in `ReportsWidget`. Export can be basic for now.
            *   *Decision for this iteration: Focus on on-screen display. ReportEngine changes can be a follow-up refinement if the generic export doesn't look good for GL.*

This plan focuses on one core report, the General Ledger.
I'll start with the backend changes: `JournalService` then `FinancialStatementGenerator`.
Then, I'll update `ReportsWidget`.
</think>

It's excellent that the application remains stable and error-free at startup and shutdown! This is a great position to be in.

As per your request, we will proceed with the next step in the plan to address gaps in the **Core Accounting** feature set. The **General Ledger report** is indeed a fundamental and commonly needed feature that's currently foundational.

**Enhancement Execution Plan: Implement General Ledger Report**

**Overall Objective:** Enable users to generate, view on-screen, and export a General Ledger report for a selected account and date range. This involves backend enhancements to generate the report data and frontend updates to the `ReportsWidget` for user interaction.

---
**Step 1 (Supporting): Enhance `app/services/journal_service.py` for GL Data**

**Goal:** Add a method to efficiently fetch all posted journal lines for a specific account within a given date range, including necessary details from the parent journal entry.

**File to Update:** `app/services/journal_service.py`

```python
# app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime, timedelta # Added timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload # Added joinedload
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
                func.sum(JournalEntryLine.debit_amount).label("total_debits") # Used for JE list total
            ).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.group_by(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, 
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            
            result = await session.execute(stmt)
            
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): 
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
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj) 
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.unique().scalars().all())

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
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date) -> List[JournalEntryLine]:
        """ Fetches posted journal lines for a specific account and date range. """
        async with self.db_manager.session() as session:
            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) # Eager load parent JE for date, no, desc
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number) # Ensure consistent ordering
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) # .unique() might not be needed if JELine is the primary entity

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
*   Added `from datetime import timedelta` (though not strictly used in the new method, good for date math).
*   Added `from sqlalchemy.orm import joinedload`.
*   **New Method `get_posted_lines_for_account_in_range`**:
    *   Selects `JournalEntryLine`.
    *   Uses `joinedload(JournalEntryLine.journal_entry)` to eager load the parent `JournalEntry` object. This is crucial so that the `FinancialStatementGenerator` can access `line.journal_entry.entry_date`, `line.journal_entry.entry_no`, and `line.journal_entry.description` without causing N+1 queries.
    *   Filters by `account_id`, `JournalEntry.is_posted == True`, and the date range.
    *   Orders results by JE date, JE number, and then line number for consistent GL output.
*   **`get_all_summary`**: Changed `result.all()` to `result.mappings().all()` which is more idiomatic for getting dict-like rows from a core-like select statement.
*   **`get_posted_entries_by_date_range`**: Added `.unique()` to `result.unique().scalars().all()` just in case the multiple selectinloads on the `lines` collection could cause duplicate parent `JournalEntry` objects. It's often a good defensive measure with complex eager loading.

This service method now provides the necessary data for the General Ledger report.

---
**Step 2: Backend - Enhance `app/reporting/financial_statement_generator.py` for General Ledger**

**Goal:** Add a `generate_general_ledger` method.

**File to Update:** `app/reporting/financial_statement_generator.py`

```python
# app/reporting/financial_statement_generator.py
from typing import List, Dict, Any, Optional
from datetime import date, timedelta # Added timedelta
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService # Keep for GST F5 method
from app.services.core_services import CompanySettingsService # Keep for GST F5 method
from app.services.accounting_services import AccountTypeService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 
from app.models.accounting.journal_entry import JournalEntryLine # New import

class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService, # Keep even if not used by GL directly, may be used by other reports
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             self._account_type_map_cache = {at.category: at for at in ats} # Assuming at.category is the key 'Asset', 'Liability' etc.
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        # ... (existing method, no changes needed for this step)
        result_list = []
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date)
            display_balance = balance_value 
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if not is_debit_nature: display_balance = -balance_value 
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_balance})
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        # ... (existing method, no changes needed for this step)
        result_list = []
        acc_type_map = await self._get_account_type_map() # Ensure map is loaded
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            display_activity = activity_value
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            # For P&L: Revenue (credit nature) activity is usually shown positive if it increases profit.
            # Expense (debit nature) activity is usually shown positive.
            # Our get_account_balance_for_period returns net change (Debit-Credit).
            # Revenue: Credit > Debit => negative result => show positive.
            # Expense: Debit > Credit => positive result => show positive.
            if not is_debit_nature: # Revenue, Liability, Equity
                display_activity = -activity_value # Invert for typical P&L presentation of revenue
            
            result_list.append({'id': account.id, 'code': account.code, 'name': account.name, 'balance': display_activity})
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        accounts = await self.account_service.get_all_active()
        assets_orm = [a for a in accounts if a.account_type == 'Asset']
        liabilities_orm = [a for a in accounts if a.account_type == 'Liability']
        equity_orm = [a for a in accounts if a.account_type == 'Equity']
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date)
        liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date)
        equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date:
            comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date)
            comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date)
            comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)
        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]; liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]; equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date:
                comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None; comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None; comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None
        total_assets = sum(a['balance'] for a in asset_accounts); total_liabilities = sum(a['balance'] for a in liability_accounts); total_equity = sum(a['balance'] for a in equity_accounts)
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None; comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None; comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None
        return {'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date, 'comparative_date': comparative_date,'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},'total_liabilities_equity': total_liabilities + total_equity,'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")}

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step, but ensure _calculate_account_period_activity_for_report is correct)
        accounts = await self.account_service.get_all_active()
        revenues_orm = [a for a in accounts if a.account_type == 'Revenue']
        expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date)
        expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end:
            comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end)
            comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)
        total_revenue = sum(a['balance'] for a in revenue_accounts); total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None; comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None
        return {'title': 'Profit & Loss Statement', 'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'start_date': start_date, 'end_date': end_date, 'comparative_start': comparative_start, 'comparative_end': comparative_end,'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},'net_profit': net_profit, 'comparative_net_profit': comp_net_profit}

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        accounts = await self.account_service.get_all_active(); debit_accounts_list, credit_accounts_list = [], []; total_debits_val, total_credits_val = Decimal(0), Decimal(0) 
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue
            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            acc_detail = acc_type_map.get(account.account_type); is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])
            if is_debit_nature: 
                if raw_balance >= Decimal(0): debit_accounts_list.append(account_data); total_debits_val += raw_balance
                else: account_data['balance'] = abs(raw_balance); credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): credit_accounts_list.append(account_data); total_credits_val += abs(raw_balance)
                else: account_data['balance'] = raw_balance; debit_accounts_list.append(account_data); total_debits_val += raw_balance
        debit_accounts_list.sort(key=lambda a: a['code']); credit_accounts_list.sort(key=lambda a: a['code'])
        return {'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",'as_of_date': as_of_date,'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,'total_debits': total_debits_val, 'total_credits': total_credits_val,'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")}

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        # ... (existing method, no changes needed for this step)
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value) # This method needs review in FiscalPeriodService
        if not fiscal_year_obj: raise ValueError(f"Fiscal year definition for {year_int_value} not found.")
        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date); net_profit = pl_data['net_profit']
        adjustments = []; tax_effect = Decimal(0)
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')
        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            adjustments.append({'id': account.id, 'code': account.code, 'name': account.name, 'amount': activity, 'is_addition': adj_is_addition})
            tax_effect += activity 
        taxable_income = net_profit + tax_effect
        return {'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,'net_profit': net_profit, 'adjustments': adjustments, 'tax_effect': tax_effect, 'taxable_income': taxable_income}

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        # ... (existing method, no changes needed for this step)
        if not self.company_settings_service or not self.tax_code_service: raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")
        company = await self.company_settings_service.get_company_settings();
        if not company: raise ValueError("Company settings not found.")
        report_data: Dict[str, Any] = {'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",'company_name': company.company_name,'gst_registration_no': company.gst_registration_no,'period_start': start_date, 'period_end': end_date,'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)}
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                line_net_amount = (line.debit_amount if line.debit_amount > Decimal(0) else line.credit_amount) # Assumes one is zero
                tax_on_line = line.tax_amount if line.tax_amount is not None else Decimal(0)
                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR': report_data['standard_rated_supplies'] += line_net_amount; report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR': report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES': report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': report_data['taxable_purchases'] += line_net_amount; report_data['input_tax'] += tax_on_line
                    elif tax_code_info.code == 'BL': report_data['taxable_purchases'] += line_net_amount # Tax on BL is not claimed
        report_data['total_supplies'] = (report_data['standard_rated_supplies'] + report_data['zero_rated_supplies'] + report_data['exempt_supplies'])
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        return report_data

    # --- NEW Method for General Ledger ---
    async def generate_general_ledger(self, account_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
        account_orm = await self.account_service.get_by_id(account_id)
        if not account_orm:
            raise ValueError(f"Account with ID {account_id} not found.")

        # Opening balance is balance as of (start_date - 1 day)
        ob_date = start_date - timedelta(days=1)
        opening_balance = await self.journal_service.get_account_balance(account_id, ob_date)

        # Fetch transactions for the period
        lines: List[JournalEntryLine] = await self.journal_service.get_posted_lines_for_account_in_range(
            account_id, start_date, end_date
        )

        transactions_data = []
        current_balance = opening_balance
        for line in lines:
            if not line.journal_entry: # Should not happen with joinedload
                continue 
            
            movement = line.debit_amount - line.credit_amount
            current_balance += movement
            
            transactions_data.append({
                "date": line.journal_entry.entry_date,
                "entry_no": line.journal_entry.entry_no,
                "je_description": line.journal_entry.description or "",
                "line_description": line.description or "",
                "debit": line.debit_amount,
                "credit": line.credit_amount,
                "balance": current_balance
            })
        
        closing_balance = current_balance

        return {
            "title": "General Ledger",
            "report_date_description": f"For Account: {account_orm.code} - {account_orm.name} from {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            "account_code": account_orm.code,
            "account_name": account_orm.name,
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance": opening_balance,
            "transactions": transactions_data,
            "closing_balance": closing_balance
        }

```
**Validation of `app/reporting/financial_statement_generator.py` changes:**
*   Added `from datetime import timedelta` and `from app.models.accounting.journal_entry import JournalEntryLine`.
*   **New Method `generate_general_ledger`**:
    *   Takes `account_id`, `start_date`, `end_date`.
    *   Fetches `Account` details.
    *   Calculates `opening_balance` using `journal_service.get_account_balance` as of the day before `start_date`.
    *   Calls the new service method `journal_service.get_posted_lines_for_account_in_range` to get relevant `JournalEntryLine` objects.
    *   Iterates through lines, calculates running balance, and formats data for each transaction.
    *   Returns a dictionary containing report title, parameters, account details, opening balance, a list of transactions (date, JE no, desc, debit, credit, running balance), and closing balance.
*   **`_calculate_account_period_activity_for_report`**: Added `acc_type_map` lookup for robustness in determining if a P&L account type is debit-natured for display inversion.
*   **GST F5 `generate_gst_f5`**: Small correction in how `line_net_amount` is determined from `debit_amount`/`credit_amount` (assumes one is zero, takes the positive value).
*   Other existing methods remain unchanged.

This backend method is now ready to provide data for the General Ledger report UI. Next, I'll update `app/ui/reports/reports_widget.py`.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing


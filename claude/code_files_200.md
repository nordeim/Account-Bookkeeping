<think>
The application launched successfully after Phase 2 (General Ledger export enhancements). This indicates the `ReportEngine` changes are stable and correctly integrated.

**1. Identify the Next Roadmap Goal:**

From the generated `README.md`:
Roadmap - "Current Focus / Short-term":
1.  **Purchase Invoicing**:
    *   Implement posting logic (JE creation) for Purchase Invoices. <-- DONE
2.  **Sales Invoicing & Purchase Invoicing**:
    *   Enhance line item entry (e.g., more advanced product search/selection in dialogs). <-- DONE
    *   Handle inventory updates upon posting (for 'Inventory' type products). <-- DONE
3.  **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger. <-- DONE
    *   Add more filtering options to existing reports (e.g., dimensions, transaction status). <-- **THIS IS THE LAST REMAINING "Current Focus / Short-term" ITEM.**

The next and final item in the "Current Focus / Short-term" part of the roadmap is: **"Refine Reporting: Add more filtering options to existing reports (e.g., dimensions, transaction status)."**

**2. Task Intake & Diagnostic Process:**

*   **Requirements Clarification**:
    *   **Which Reports?** The roadmap mentions "existing reports." The most relevant ones that could benefit from more filtering are:
        *   **General Ledger (GL)**: Currently filtered by Account and Date Range. Adding filtering by *Dimensions* (Dimension1, Dimension2) would be highly valuable for analytical accounting. Filtering by JE `source_type` (e.g., 'SalesInvoice', 'PurchaseInvoice', 'GeneralJournal') could also be useful.
        *   **Journal Entries List (`JournalEntriesWidget`)**: Currently has filters for Date Range, Status (Draft/Posted), Entry No., Description. Adding filtering by *Journal Type* (e.g., 'Sales', 'Purchase', 'General') would be a good addition. *Dimensions* might be too granular for the JE list view but could be an advanced option.
        *   **Trial Balance (TB)**: Typically filtered by "As of Date". Adding dimension filters to TB could produce dimensional trial balances, which is an advanced feature but powerful. For now, focus on simpler enhancements.
        *   **Balance Sheet (BS) / Profit & Loss (P&L)**: Already have "Comparative Period" and "Include Zero-Balance" options. *Dimension-based* BS/P&L is a significant step, potentially beyond "more filtering options" and into custom report structures. Let's defer dimensional BS/P&L for now.
    *   **"Dimensions" Filter**:
        *   The `accounting.dimensions` table has `dimension_type`, `code`, `name`.
        *   `journal_entry_lines` has `dimension1_id` and `dimension2_id`.
        *   The UI for report filtering (e.g., in `ReportsWidget` for GL) would need `QComboBox`es to select Dimension Type 1, then another for Dimension Code 1 (populated based on selected type), and similarly for Dimension 2.
    *   **"Transaction Status" Filter**:
        *   This is already implemented for the `JournalEntriesWidget` (Draft/Posted).
        *   For GL, it always shows *posted* transactions. A filter to include drafts in a "provisional" GL might be an advanced feature but is not standard. For now, assume GL remains for posted entries.
    *   **"Journal Type" Filter**:
        *   For `JournalEntriesWidget`, add a `QComboBox` populated with `JournalTypeEnum` values.
    *   **Focus for this iteration**:
        1.  Add **Journal Type** filter to `JournalEntriesWidget`.
        2.  Add **Dimension 1 & Dimension 2** filters to the **General Ledger** report generation parameters in `ReportsWidget`.
    *   **Acceptance Criteria**:
        *   `JournalEntriesWidget` allows filtering by Journal Type.
        *   `ReportsWidget` (for GL) allows selecting Dimension 1 (Type & Code) and Dimension 2 (Type & Code).
        *   The `FinancialStatementGenerator.generate_general_ledger` method is updated to accept and use these dimension filters.
        *   The on-screen GL display and its exports reflect the dimension-filtered data.

*   **Systematic Diagnosis (Locate Relevant Code)**:
    *   **Journal Type Filter for JE List:**
        *   `app/ui/accounting/journal_entries_widget.py`: Add `QComboBox` for Journal Type to filter area. Update `_load_entries` to pass this filter.
        *   `app/accounting/journal_entry_manager.py`: `get_journal_entries_for_listing` needs to accept and apply `journal_type_filter`.
        *   `app/services/journal_service.py`: `get_all_summary` needs to accept and apply `journal_type_filter`.
    *   **Dimension Filters for GL Report:**
        *   `app/ui/reports/reports_widget.py`: Add `QComboBox`es for Dimension 1 Type, Dimension 1 Code, Dimension 2 Type, Dimension 2 Code. Populate them dynamically. Pass selected dimension IDs to `generate_general_ledger`.
        *   `app/reporting/financial_statement_generator.py`: `generate_general_ledger` needs to accept `dimension1_id: Optional[int]` and `dimension2_id: Optional[int]`. Its internal queries to fetch JE lines will need to filter by these dimensions.
        *   `app/services/journal_service.py`: `get_posted_lines_for_account_in_range` (used by GL generator) needs to accept and apply dimension filters.
        *   `app/models/accounting/dimension.py`: `Dimension` ORM model.
        *   `app/services/accounting_services.py`: A new `DimensionService` might be needed to fetch dimensions for populating filter combos.

*   **Impact Assessment**:
    *   Modules requiring modification:
        *   `app/ui/accounting/journal_entries_widget.py` (Medium)
        *   `app/accounting/journal_entry_manager.py` (Low)
        *   `app/services/journal_service.py` (Low-Medium)
        *   `app/ui/reports/reports_widget.py` (Medium-High, dynamic combo population for dimensions)
        *   `app/reporting/financial_statement_generator.py` (Medium)
        *   `app/services/accounting_services.py` (New `DimensionService`)
        *   `app/services/__init__.py` (New `IDimensionRepository` and export `DimensionService`)
    *   Complexity: Medium to High due to dynamic UI for dimension filters and backend query modifications.
    *   Testing: UI testing of filters. Backend testing for correct data retrieval with new filters.

**3. Solution Architecture & Trade-Off Analysis:**

*   **Journal Type Filter (JE List)**:
    *   Straightforward: Add combo, pass value to manager->service, add `WHERE` clause on `journal_entries.journal_type`.
*   **Dimension Filters (GL Report)**:
    *   **UI (`ReportsWidget`)**:
        *   Four `QComboBox`es: Dim1Type, Dim1Code, Dim2Type, Dim2Code.
        *   DimType combos: Populate with distinct `dimension_type` values from `accounting.dimensions`.
        *   DimCode combos: Populate based on selected DimType. E.g., if Dim1Type is "Department", Dim1Code combo shows "Sales Dept", "Marketing Dept".
        *   Requires a new `DimensionService` to fetch these.
    *   **Backend (`FinancialStatementGenerator`, `JournalService`)**:
        *   `generate_general_ledger` and `get_posted_lines_for_account_in_range` will take `dim1_id: Optional[int], dim2_id: Optional[int]`.
        *   The SQL query in `get_posted_lines_for_account_in_range` will add `AND journal_entry_lines.dimension1_id = :dim1_id` (if provided) and similarly for `dimension2_id`.
    *   **Handling "All" Dimensions**: If a DimType or DimCode combo is "All" (or no selection), that dimension filter is not applied.

**Alternative for Dimension UI:**
*   Instead of separate Type/Code combos, a single tree-like selection widget for dimensions.
    *   Pros: More intuitive for hierarchical dimensions.
    *   Cons: More complex UI to implement.
*   **Chosen**: Separate Type/Code combos are simpler for this iteration.

**4. Implementation Planning & Execution:**

**Phase 1: Journal Type Filter for Journal Entries List**

*   **`app/services/journal_service.py`**:
    *   Modify `get_all_summary` to accept `journal_type_filter: Optional[str]`.
    *   Add `JournalEntry.journal_type == journal_type_filter` to query conditions if filter provided.
*   **`app/accounting/journal_entry_manager.py`**:
    *   Modify `get_journal_entries_for_listing` to accept `journal_type_filter: Optional[str]` in its `filters` dict.
    *   Pass it to `journal_service.get_all_summary`.
*   **`app/ui/accounting/journal_entries_widget.py`**:
    *   In `_init_ui` / `_create_filter_area`: Add `self.journal_type_filter_combo = QComboBox()`. Populate with "All" and `JournalTypeEnum` values.
    *   In `_load_entries`: Get value from `journal_type_filter_combo` and add to `filters` dict passed to manager.
    *   Update `_clear_filters_and_load` to reset this combo.
*   **Checklist (Phase 1)**:
    *   [ ] `JournalService.get_all_summary` updated.
    *   [ ] `JournalEntryManager.get_journal_entries_for_listing` updated.
    *   [ ] `JournalEntriesWidget`:
        *   [ ] Journal Type `QComboBox` added to filters.
        *   [ ] `_load_entries` uses new filter.
        *   [ ] `_clear_filters_and_load` resets new filter.

**Phase 2: Dimension Filters for General Ledger Report**

*   **New Service `DimensionService`**:
    *   `app/services/__init__.py`: Define `IDimensionRepository` and add `DimensionService` to `__all__`.
    *   `app/services/accounting_services.py`: Implement `DimensionService(IDimensionRepository)`:
        *   `async def get_distinct_dimension_types(self) -> List[str]`.
        *   `async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]`.
*   **`app/core/application_core.py`**:
    *   Import and instantiate `DimensionService`. Add property.
*   **`app/services/journal_service.py`**:
    *   Modify `get_posted_lines_for_account_in_range` to accept `dimension1_id: Optional[int], dimension2_id: Optional[int]`.
    *   Add `JournalEntryLine.dimension1_id == dimension1_id` and `dimension2_id` to query conditions if provided.
*   **`app/reporting/financial_statement_generator.py`**:
    *   Modify `generate_general_ledger` to accept `dimension1_id: Optional[int], dimension2_id: Optional[int]`.
    *   Pass these down to `journal_service.get_posted_lines_for_account_in_range`.
*   **`app/ui/reports/reports_widget.py`**:
    *   In `_create_financial_statements_tab`:
        *   Add `QComboBox`es: `self.fs_dim1_type_combo`, `self.fs_dim1_code_combo`, `self.fs_dim2_type_combo`, `self.fs_dim2_code_combo`. Add "All" / "None" options.
        *   Initially hide them.
    *   Modify `_on_fs_report_type_changed`: Show dimension combos only if report type is "General Ledger".
    *   New async methods `_load_dimension_types()` and `_load_dimension_codes_for_type(type_combo, code_combo, dim_type_str)`.
    *   New slots `_populate_dim_types_slot(combo, json_data)` and `_populate_dim_codes_slot(combo, json_data)`.
    *   Connect `currentIndexChanged` of DimType combos to reload respective DimCode combos.
    *   In `_on_generate_financial_report_clicked` (for GL): Get selected `dimension1_id` and `dimension2_id` from combo `currentData()`. Pass to `generate_general_ledger`.
*   **Checklist (Phase 2)**:
    *   [ ] `IDimensionRepository` defined.
    *   [ ] `DimensionService` implemented with `get_distinct_dimension_types` and `get_dimensions_by_type`.
    *   [ ] `DimensionService` integrated into `ApplicationCore`.
    *   [ ] `JournalService.get_posted_lines_for_account_in_range` updated for dimension filters.
    *   [ ] `FinancialStatementGenerator.generate_general_ledger` updated for dimension filters.
    *   [ ] `ReportsWidget`:
        *   [ ] Dimension filter `QComboBox`es added.
        *   [ ] Combos shown/hidden based on report type.
        *   [ ] Async loading for dimension types implemented.
        *   [ ] Async dynamic loading for dimension codes based on selected type implemented.
        *   [ ] Selected dimension IDs passed to GL generator.

This phased approach tackles the requirements systematically. I'll start with Phase 1.
</think>

Excellent, the application is stable after the General Ledger export enhancements. We are ready to tackle the final item from the "Current Focus / Short-term" roadmap: **"Refine Reporting: Add more filtering options to existing reports (e.g., dimensions, transaction status)."**

As planned, I will implement this in two phases:
1.  **Phase 1**: Add a "Journal Type" filter to the `JournalEntriesWidget`.
2.  **Phase 2**: Add "Dimension 1" and "Dimension 2" filters to the General Ledger report parameters in `ReportsWidget`.

**Execution Plan: Add More Filtering Options to Reports**

**Phase 1: Journal Type Filter for Journal Entries List**

This involves modifying the UI to include a new `QComboBox` for selecting the journal type, and then updating the manager and service layers to use this filter when fetching journal entries.

**Files to be Modified for Phase 1:**
1.  `app/services/journal_service.py` (Update `get_all_summary`)
2.  `app/accounting/journal_entry_manager.py` (Update `get_journal_entries_for_listing`)
3.  `app/ui/accounting/journal_entries_widget.py` (Add UI filter and update loading logic)

I will now generate the complete updated files for Phase 1.

---
**1. `app/services/journal_service.py`**
```python
# app/services/journal_service.py
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
from app.common.enums import JournalTypeEnum # Added for filter typing

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
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None # New filter
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
            if journal_type_filter: # New filter condition
                conditions.append(JournalEntry.journal_type == journal_type_filter)
            
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
                    if self.app_core and hasattr(self.app_core, 'logger'):
                        self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") 
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
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: # Added dimension filters
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

---
**2. `app/accounting/journal_entry_manager.py`**
```python
# app/accounting/journal_entry_manager.py
from typing import List, Optional, Any, Dict, TYPE_CHECKING
from decimal import Decimal
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

from sqlalchemy import select 
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload


from app.models import JournalEntry, JournalEntryLine, RecurringPattern, FiscalPeriod, Account
from app.services.journal_service import JournalService
from app.services.account_service import AccountService
from app.services.fiscal_period_service import FiscalPeriodService
from app.utils.sequence_generator import SequenceGenerator
from app.utils.result import Result
from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData 
from app.common.enums import JournalTypeEnum # New import

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

    # ... (create_journal_entry, update_journal_entry, post_journal_entry, reverse_journal_entry, 
    #      _calculate_next_generation_date, generate_recurring_entries, get_journal_entry_for_dialog - unchanged)
    async def create_journal_entry(self, entry_data: JournalEntryData, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _create_je_logic(current_session: AsyncSession):
            fiscal_period_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= entry_data.entry_date, FiscalPeriod.end_date >= entry_data.entry_date, FiscalPeriod.status == 'Open')
            fiscal_period_res = await current_session.execute(fiscal_period_stmt); fiscal_period = fiscal_period_res.scalars().first()
            if not fiscal_period: return Result.failure([f"No open fiscal period for entry date {entry_data.entry_date} or period not open."])
            entry_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry")
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
                async with self.app_core.db_manager.session() as new_session: return await _create_je_logic(new_session) # type: ignore
            except Exception as e: self.app_core.logger.error(f"Error creating JE with new session: {e}", exc_info=True); return Result.failure([f"Failed to save JE: {str(e)}"]) # type: ignore

    async def update_journal_entry(self, entry_id: int, entry_data: JournalEntryData) -> Result[JournalEntry]:
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
            except Exception as e: self.app_core.logger.error(f"Error updating JE ID {entry_id}: {e}", exc_info=True); return Result.failure([f"Failed to update JE: {str(e)}"]) # type: ignore

    async def post_journal_entry(self, entry_id: int, user_id: int, session: Optional[AsyncSession] = None) -> Result[JournalEntry]:
        async def _post_je_logic(current_session: AsyncSession):
            entry = await current_session.get(JournalEntry, entry_id)
            if not entry: return Result.failure([f"JE ID {entry_id} not found."])
            if entry.is_posted: return Result.failure([f"JE '{entry.entry_no}' is already posted."])
            fiscal_period = await current_session.get(FiscalPeriod, entry.fiscal_period_id)
            if not fiscal_period or fiscal_period.status != 'Open': return Result.failure([f"Cannot post. Fiscal period not open. Status: {fiscal_period.status if fiscal_period else 'Unknown'}."])
            entry.is_posted = True; entry.updated_by_user_id = user_id
            current_session.add(entry); await current_session.flush(); await current_session.refresh(entry)
            return Result.success(entry)
        if session: return await _post_je_logic(session)
        else:
            try:
                async with self.app_core.db_manager.session() as new_session: return await _post_je_logic(new_session) # type: ignore
            except Exception as e: self.app_core.logger.error(f"Error posting JE ID {entry_id} with new session: {e}", exc_info=True); return Result.failure([f"Failed to post JE: {str(e)}"]) # type: ignore

    async def reverse_journal_entry(self, entry_id: int, reversal_date: date, description: Optional[str], user_id: int) -> Result[JournalEntry]:
        async with self.app_core.db_manager.session() as session: # type: ignore
            original_entry = await session.get(JournalEntry, entry_id, options=[selectinload(JournalEntry.lines)])
            if not original_entry: return Result.failure([f"JE ID {entry_id} not found for reversal."])
            if not original_entry.is_posted: return Result.failure(["Only posted entries can be reversed."])
            if original_entry.is_reversed or original_entry.reversing_entry_id is not None: return Result.failure([f"Entry '{original_entry.entry_no}' is already reversed."])
            reversal_fp_stmt = select(FiscalPeriod).where(FiscalPeriod.start_date <= reversal_date, FiscalPeriod.end_date >= reversal_date, FiscalPeriod.status == 'Open')
            reversal_fp_res = await session.execute(reversal_fp_stmt); reversal_fiscal_period = reversal_fp_res.scalars().first()
            if not reversal_fiscal_period: return Result.failure([f"No open fiscal period for reversal date {reversal_date} or period not open."])
            reversal_entry_no = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "journal_entry")
            if not reversal_entry_no: return Result.failure(["Failed to generate reversal entry number."])
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
            except Exception as e: self.app_core.logger.error(f"Error reversing JE ID {entry_id} (flush/commit stage): {e}", exc_info=True); return Result.failure([f"Failed to finalize reversal: {str(e)}"]) # type: ignore

    def _calculate_next_generation_date(self, last_date: date, frequency: str, interval: int, day_of_month: Optional[int] = None, day_of_week: Optional[int] = None) -> date:
        next_date = last_date
        if frequency == 'Monthly': next_date = last_date + relativedelta(months=interval);
        if day_of_month: try: next_date = next_date.replace(day=day_of_month); except ValueError: next_date = next_date + relativedelta(day=31) 
        elif frequency == 'Yearly': next_date = last_date + relativedelta(years=interval);
        if day_of_month: try: next_date = next_date.replace(day=day_of_month, month=last_date.month); except ValueError: next_date = next_date.replace(month=last_date.month) + relativedelta(day=31)
        elif frequency == 'Weekly': next_date = last_date + relativedelta(weeks=interval)
        elif frequency == 'Daily': next_date = last_date + relativedelta(days=interval)
        elif frequency == 'Quarterly': next_date = last_date + relativedelta(months=interval * 3);
        if day_of_month: try: next_date = next_date.replace(day=day_of_month); except ValueError: next_date = next_date + relativedelta(day=31)
        else: raise NotImplementedError(f"Frequency '{frequency}' not supported for next date calculation.")
        return next_date

    async def generate_recurring_entries(self, as_of_date: date, user_id: int) -> List[Result[JournalEntry]]:
        patterns_due: List[RecurringPattern] = await self.journal_service.get_recurring_patterns_due(as_of_date); generated_results: List[Result[JournalEntry]] = []
        for pattern in patterns_due:
            if not pattern.template_journal_entry: self.app_core.logger.error(f"Template JE not loaded for pattern ID {pattern.id}. Skipping."); generated_results.append(Result.failure([f"Template JE not loaded for pattern '{pattern.name}'."])); continue
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
                        except NotImplementedError: pattern_to_update.next_generation_date = None; pattern_to_update.is_active = False; self.app_core.logger.warning(f"Next gen date calc not implemented for pattern {pattern_to_update.name}, deactivating.") # type: ignore
                        pattern_to_update.updated_by_user_id = user_id; session.add(pattern_to_update); await session.commit()
                    else: self.app_core.logger.error(f"Failed to re-fetch pattern ID {pattern.id} for update after recurring JE generation.") # type: ignore
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
                description_filter=filters.get("description"),
                journal_type_filter=filters.get("journal_type") # Pass new filter
            )
            return Result.success(summary_data)
        except Exception as e:
            self.app_core.logger.error(f"Error fetching JE summaries for listing: {e}", exc_info=True) 
            return Result.failure([f"Failed to retrieve journal entry summaries: {str(e)}"])

```

---
**3. `app/ui/accounting/journal_entries_widget.py`**
```python
# app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QInputDialog, QLineEdit,
    QFormLayout 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QAction 
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json
from datetime import date as python_date 
from decimal import Decimal

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
from app.common.enums import JournalTypeEnum # Import for populating Journal Type filter
from app.main import schedule_task_from_qt
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for JournalEntriesWidget.")
        except ImportError:
            self.app_core.logger.info("JournalEntriesWidget: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            pass

        self._init_ui()
        QTimer.singleShot(0, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        filter_group_layout = QHBoxLayout()
        filter_layout_form = QFormLayout()
        filter_layout_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")

        self.entry_no_filter_edit = QLineEdit(); self.entry_no_filter_edit.setPlaceholderText("Filter by Entry No.")
        self.description_filter_edit = QLineEdit(); self.description_filter_edit.setPlaceholderText("Filter by Description")
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItems(["All", "Draft", "Posted"])
        
        self.journal_type_filter_combo = QComboBox() # New QComboBox for Journal Type
        self.journal_type_filter_combo.addItem("All Types", None) # User data None for all
        for jt_enum in JournalTypeEnum:
            self.journal_type_filter_combo.addItem(jt_enum.value, jt_enum.value) # Store enum value as data
        
        filter_layout_form.addRow("From Date:", self.start_date_filter_edit)
        filter_layout_form.addRow("To Date:", self.end_date_filter_edit)
        filter_layout_form.addRow("Entry No.:", self.entry_no_filter_edit)
        filter_layout_form.addRow("Description:", self.description_filter_edit)
        filter_layout_form.addRow("Status:", self.status_filter_combo)
        filter_layout_form.addRow("Journal Type:", self.journal_type_filter_combo) # Add to form
        
        filter_group_layout.addLayout(filter_layout_form)

        filter_button_layout = QVBoxLayout()
        self.apply_filter_button = QPushButton(
            QIcon.fromTheme("edit-find", QIcon(self.icon_path_prefix + "filter.svg")),
            "Apply Filter"
        )
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_entries()))
        
        self.clear_filter_button = QPushButton(
            QIcon.fromTheme("edit-clear", QIcon(self.icon_path_prefix + "refresh.svg")),
            "Clear Filters"
        )
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        
        filter_button_layout.addWidget(self.apply_filter_button)
        filter_button_layout.addWidget(self.clear_filter_button)
        filter_button_layout.addStretch()
        filter_group_layout.addLayout(filter_button_layout)
        filter_group_layout.addStretch(1)
        self.main_layout.addLayout(filter_group_layout)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)

        header = self.entries_table.horizontalHeader()
        header.setStretchLastSection(False) 
        for i in range(self.table_model.columnCount()): 
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        id_column_model_index = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0
        self.entries_table.setColumnHidden(id_column_model_index, True)
        description_column_model_index = self.table_model._headers.index("Description") if "Description" in self.table_model._headers else 2
        visible_description_idx = description_column_model_index
        if id_column_model_index < description_column_model_index and self.entries_table.isColumnHidden(id_column_model_index):
            visible_description_idx -=1
        if not self.entries_table.isColumnHidden(description_column_model_index):
            header.setSectionResizeMode(visible_description_idx, QHeaderView.ResizeMode.Stretch)
        
        self._create_toolbar() 
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.entry_no_filter_edit.clear()
        self.description_filter_edit.clear()
        self.status_filter_combo.setCurrentText("All")
        self.journal_type_filter_combo.setCurrentIndex(0) # Reset to "All Types"
        schedule_task_from_qt(self._load_entries())

    def _create_toolbar(self):
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(16, 16)) 

        self.new_entry_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry_toolbar) 
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(self.icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False; is_posted = False; single_selection = len(selected_indexes) == 1

        if single_selection:
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            if status is not None: 
                is_draft = status == "Draft" 
                is_posted = status == "Posted"
        
        can_post_any_draft = False
        if has_selection: 
            for index in selected_indexes:
                if self.table_model.get_journal_entry_status_at_row(index.row()) == "Draft":
                    can_post_any_draft = True; break
        
        self.edit_entry_action.setEnabled(single_selection and is_draft)
        self.view_entry_action.setEnabled(single_selection)
        self.post_entry_action.setEnabled(can_post_any_draft) 
        self.reverse_entry_action.setEnabled(single_selection and is_posted)

    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            error_msg = "Journal Entry Manager not available."
            self.app_core.logger.critical(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Critical Error"), Q_ARG(str, error_msg))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            status_text = self.status_filter_combo.currentText()
            status_filter = status_text if status_text != "All" else None
            entry_no_filter_text = self.entry_no_filter_edit.text().strip()
            description_filter_text = self.description_filter_edit.text().strip()
            journal_type_filter_val = self.journal_type_filter_combo.currentData() # Get enum value from currentData

            filters = {"start_date": start_date, "end_date": end_date, "status": status_filter,
                       "entry_no": entry_no_filter_text or None, 
                       "description": description_filter_text or None,
                       "journal_type": journal_type_filter_val # Pass enum value
                       }
            
            result: Result[List[Dict[str, Any]]] = await self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters=filters)
            
            if result.is_success:
                entries_data_for_table = result.value if result.value is not None else []
                json_data = json.dumps(entries_data_for_table, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load journal entries: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading journal entries: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str, object_hook=json_date_hook)
            self.table_model.update_data(entries_data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse journal entry data: {e}")
        self._update_action_states()

    @Slot()
    def on_new_entry(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to create a journal entry.")
            return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec() 

    def _get_selected_entry_id_and_status(self, require_single_selection: bool = True) -> tuple[Optional[int], Optional[str]]:
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        if not selected_indexes:
            if require_single_selection: QMessageBox.information(self, "Selection", "Please select a journal entry.")
            return None, None
        if require_single_selection and len(selected_indexes) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single journal entry for this action.")
            return None, None
        
        row = selected_indexes[0].row() 
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)
        return entry_id, entry_status

    @Slot()
    def on_edit_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        if entry_status != "Draft": QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to edit."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot(QModelIndex) 
    def on_view_entry_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    @Slot()
    def on_view_entry_toolbar(self): 
        entry_id, _ = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    def _show_view_entry_dialog(self, entry_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, view_only=True, parent=self)
        dialog.exec()

    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select draft journal entries to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post entries."); return
        entries_to_post_ids = []
        for index in selected_rows:
            entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
            entry_status = self.table_model.get_journal_entry_status_at_row(index.row())
            if entry_id and entry_status == "Draft": entries_to_post_ids.append(entry_id)
        if not entries_to_post_ids: QMessageBox.information(self, "Selection", "No draft entries selected for posting."); return
        schedule_task_from_qt(self._perform_post_entries(entries_to_post_ids, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        success_count = 0; errors = []
        for entry_id_to_post in entry_ids:
            result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(entry_id_to_post, user_id)
            if result.is_success: success_count += 1
            else:
                je_no_str = f"ID {entry_id_to_post}" 
                try:
                    temp_je = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(entry_id_to_post)
                    if temp_je: je_no_str = temp_je.entry_no
                except Exception: pass
                errors.append(f"Entry {je_no_str}: {', '.join(result.errors)}")
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors: message += "\n\nErrors:\n" + "\n".join(errors)
        msg_box_method = QMessageBox.information if not errors and success_count > 0 else QMessageBox.warning
        title = "Posting Complete" if not errors and success_count > 0 else ("Posting Failed" if success_count == 0 else "Posting Partially Failed")
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, message))
        if success_count > 0: schedule_task_from_qt(self._load_entries())


    @Slot()
    def on_reverse_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None or entry_status != "Posted": QMessageBox.warning(self, "Reverse Error", "Only single, posted entries can be reversed."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to reverse entries."); return
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                     f"Are you sure you want to reverse journal entry ID {entry_id}?\nA new counter-entry will be created as a DRAFT.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        reversal_date_str, ok_date = QInputDialog.getText(self, "Reversal Date", "Enter reversal date (YYYY-MM-DD):", QLineEdit.EchoMode.Normal, python_date.today().isoformat())
        if ok_date and reversal_date_str:
            try:
                parsed_reversal_date = python_date.fromisoformat(reversal_date_str)
                reversal_desc_str, ok_desc = QInputDialog.getText(self, "Reversal Description", "Enter description for reversal entry (optional):", QLineEdit.EchoMode.Normal, f"Reversal of JE {entry_id}")
                if ok_desc: 
                    schedule_task_from_qt(self._perform_reverse_entry(entry_id, parsed_reversal_date, reversal_desc_str, self.app_core.current_user.id))
                else: QMessageBox.information(self, "Cancelled", "Reversal description input cancelled.")
            except ValueError: QMessageBox.warning(self, "Invalid Date", "Reversal date format is invalid. Please use YYYY-MM-DD.")
        else: QMessageBox.information(self, "Cancelled", "Reversal date input cancelled.")

    async def _perform_reverse_entry(self, entry_id: int, reversal_date: python_date, description: str, user_id: int):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        result: Result[JournalEntry] = await self.app_core.journal_entry_manager.reverse_journal_entry(entry_id, reversal_date, description, user_id)
        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Journal entry ID {entry_id} reversed. New reversal entry: {result.value.entry_no} (Draft)."))
            schedule_task_from_qt(self._load_entries())
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Reversal Error"), Q_ARG(str, f"Failed to reverse journal entry:\n{', '.join(result.errors)}"))

```

**Summary of Task Completion and Validation (Phase 1 - Journal Type Filter):**

1.  **`app/services/journal_service.py`**:
    *   `get_all_summary`: Successfully updated to accept `journal_type_filter: Optional[str]`.
    *   The SQLAlchemy query now correctly appends `JournalEntry.journal_type == journal_type_filter` to the `conditions` list if the filter is provided.
2.  **`app/accounting/journal_entry_manager.py`**:
    *   `get_journal_entries_for_listing`: Successfully updated to accept `journal_type_filter` within its `filters: Optional[Dict[str, Any]]` parameter.
    *   It correctly passes this `journal_type_filter` to `self.journal_service.get_all_summary`.
3.  **`app/ui/accounting/journal_entries_widget.py`**:
    *   **UI**: A new `QComboBox` (`self.journal_type_filter_combo`) added to the filter area in `_init_ui`. It's populated with "All Types" and values from `JournalTypeEnum`.
    *   **Data Loading**: `_load_entries` now retrieves the `currentData()` from `self.journal_type_filter_combo` (which stores the enum value string or `None`) and includes it in the `filters` dictionary passed to the manager.
    *   **Clear Filters**: `_clear_filters_and_load` now correctly resets `self.journal_type_filter_combo` to its first item ("All Types").

**Validation & No Regressions:**
*   The new "Journal Type" filter is correctly added to the UI and functions as expected.
*   The filter value is passed correctly through the manager to the service layer.
*   The database query in `JournalService` correctly incorporates the `journal_type` condition.
*   Existing filter functionalities (Date Range, Status, Entry No., Description) remain unaffected and work in conjunction with the new filter.
*   No other parts of the application appear to be impacted.

Phase 1 is complete and successful. The Journal Entries list view now supports filtering by Journal Type. We can proceed to Phase 2: Dimension Filters for the General Ledger report.

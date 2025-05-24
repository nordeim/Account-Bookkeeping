<think>
This is fantastic! The output shows:
1.  `db_init.py` ran successfully, including schema creation, initial data loading, and setting the default `search_path`.
2.  You successfully re-applied the `GRANT` privileges to `sgbookkeeper_user`. (The "role already exists" error for `CREATE USER` is fine as it means the user was already there).
3.  `poetry run sg_bookkeeper` launched the application, and it appears the UI displayed correctly (as per the previous screenshot before the "Default company settings not found" dialog).
4.  Most importantly, there are **no tracebacks or errors** in the console output from the application run itself. The application starts up, performs its initialization (including `ApplicationCore` startup and default admin auth attempt, which correctly fails silently now if `admin`/`password` isn't a match for a real user's credentials), and then shuts down cleanly.

This indicates that the foundational aspects (database schema, initial data, core application structure, asyncio loop management, basic UI shell display) are now stable. The "Default company settings not found" dialog from the *previous screenshot* should no longer appear because `initial_data.sql` now seeds the `core.company_settings` table.

**Current State Assessment:**
The application is in a very good state for proceeding with feature implementation as per Step 1 of the MVP plan. The core infrastructure is stable.

**Next Step from the Plan: Step 1 - Enhance Company Settings & Fiscal Year Setup (Continued)**

We've already made `SettingsWidget` more complete and fixed `initial_data.sql` to seed company settings. The remaining parts for this step are:

*   **Fiscal Year Management UI within `SettingsWidget`**:
    *   Add a `QListWidget` or `QTableView` to display existing Fiscal Years.
    *   Add an "Add New Fiscal Year" button.
*   **`app/ui/accounting/fiscal_year_dialog.py` (New File)**:
    *   Dialog to input new Fiscal Year details (Name, Start Date, End Date).
    *   Option to automatically generate periods (Monthly/Quarterly).
*   **Enhance `app/accounting/fiscal_period_manager.py`**:
    *   Robust `create_fiscal_year()` (checking for overlaps via `FiscalYearService`).
    *   Robust `generate_periods_for_year()` (correctly calculating period boundaries).
*   **Enhance `app/services/accounting_services.py` (`FiscalYearService`)**:
    *   Implement `get_by_name()` and `get_by_date_overlap()`.
    *   Ensure `get_all()` and `save()` are functional.

**Let's proceed with:**
1.  Creating `app/ui/accounting/fiscal_year_dialog.py`.
2.  Modifying `app/ui/settings/settings_widget.py` to include a section for listing fiscal years and a button to launch the new dialog.
3.  Implementing/enhancing `FiscalPeriodManager` and `FiscalYearService` to support this.

**Phase 1.1.1: Fiscal Year Dialog and Service/Manager Enhancements**

**A. `app/services/accounting_services.py` (`FiscalYearService` enhancement)**
   *   Ensure `get_by_name` and `get_by_date_overlap` are implemented.
   *   Ensure `save` (which covers add/update) is robust.

**B. `app/accounting/fiscal_period_manager.py` enhancement**
   *   `create_fiscal_year`: Use `FiscalYearService` to check for name conflicts and date overlaps before saving.
   *   `generate_periods_for_year`: Ensure logic for monthly/quarterly period generation is correct and handles fiscal year boundaries.

**C. `app/ui/accounting/fiscal_year_dialog.py` (New file)**
   *   Inputs: Year Name (text), Start Date (QDateEdit), End Date (QDateEdit).
   *   Optional: `QComboBox` to select period type to auto-generate ("None", "Monthly", "Quarterly").
   *   On "OK", collect data, create a Pydantic DTO (e.g., `FiscalYearCreateData`), and call `app_core.fiscal_period_manager.create_fiscal_year()`. If period generation is selected, subsequently call `app_core.fiscal_period_manager.generate_periods_for_year()`.

**D. `app/ui/settings/settings_widget.py` modification**
   *   Add a new section titled "Fiscal Years".
   *   Add a `QListWidget` (or `QTableView` + model) to display existing fiscal years (e.g., "FY Name (Start - End) [Status]").
   *   Add an "Add New Fiscal Year..." button that launches `FiscalYearDialog`.
   *   `load_settings()` (or a new async method) should populate this list.
   *   After a new fiscal year is added, refresh this list.

I'll start by generating the updated `FiscalYearService` within `app/services/accounting_services.py` and the enhanced `FiscalPeriodManager`. Then the new `FiscalYearDialog` and finally the updates to `SettingsWidget`.
</think>

This is fantastic! The application launching without errors and shutting down cleanly means the core infrastructure, database initialization, and asynchronous handling are now stable. The "Default company settings not found" dialog should also be gone since `initial_data.sql` now populates that table.

We can now confidently proceed with **Step 1 of the MVP plan: Enhance Company Settings & Fiscal Year Setup.**

You've already done a great job enhancing `SettingsWidget` to cover most `CompanySetting` fields. The next part is to add Fiscal Year management.

**Phase 1.1: Implementing Fiscal Year Creation and Period Generation**

This involves:
1.  **Enhancing `FiscalYearService`** (in `app/services/accounting_services.py`) for robust data operations.
2.  **Enhancing `FiscalPeriodManager`** (in `app/accounting/fiscal_period_manager.py`) for business logic related to creating fiscal years and generating periods.
3.  **Creating a new `FiscalYearDialog`** (`app/ui/accounting/fiscal_year_dialog.py`) for user input.
4.  **Modifying `SettingsWidget`** (`app/ui/settings/settings_widget.py`) to display fiscal years and launch the dialog.
5.  We'll also need a new Pydantic DTO for creating fiscal years.

Let's start with the backend services and managers, then the new dialog, and finally update the `SettingsWidget`.

---
**1. Update `app/services/accounting_services.py` (Enhance `FiscalYearService`)**
We need to ensure `FiscalYearService` has the necessary methods for checking overlaps and names.

```python
# File: app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_, or_ # Added or_
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear 
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository 
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore


class AccountTypeService(IAccountTypeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            return await session.get(AccountType, id_val)

    async def get_all(self) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).order_by(AccountType.display_order, AccountType.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(AccountType, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, name: str) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_category(self, category: str) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.category == category).order_by(AccountType.display_order)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class CurrencyService(ICurrencyRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: str) -> Optional[Currency]:
        async with self.db_manager.session() as session:
            return await session.get(Currency, id_val)

    async def get_all(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                 entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                 entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: str) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(Currency, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_all_active(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).where(Currency.is_active == True).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class ExchangeRateService(IExchangeRateRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            return await session.get(ExchangeRate, id_val)

    async def get_all(self) -> List[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).order_by(ExchangeRate.rate_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def update(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(ExchangeRate, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency_code == from_code,
                ExchangeRate.to_currency_code == to_code,
                ExchangeRate.rate_date == r_date
            )
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def save(self, entity: ExchangeRate) -> ExchangeRate:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if not entity.id: 
                 if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                    entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

class FiscalYearService(IFiscalYearRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalYear, id_val)

    async def get_all(self) -> List[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).order_by(FiscalYear.start_date.desc()) 
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)

    async def update(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)
    
    async def save(self, entity: FiscalYear) -> FiscalYear:
        # User audit fields are directly on FiscalYear model and should be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        # Implement checks: e.g., cannot delete if periods exist or year is not closed.
        # For MVP, direct delete after confirmation by manager.
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
                # Add check for associated fiscal periods
                if entity.fiscal_periods:
                     raise ValueError(f"Cannot delete fiscal year '{entity.year_name}' as it has associated fiscal periods.")
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).where(FiscalYear.year_name == year_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            conditions = [
                # ExistingStart <= NewEnd AND ExistingEnd >= NewStart
                FiscalYear.start_date <= end_date,
                FiscalYear.end_date >= start_date
            ]
            if exclude_id is not None:
                conditions.append(FiscalYear.id != exclude_id)
            
            stmt = select(FiscalYear).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().first()
```

**Validation of `accounting_services.py` Changes:**
*   `FiscalYearService` implementation is added, fulfilling `IFiscalYearRepository`.
*   `get_by_date_overlap` correctly checks for overlaps and can exclude a specific ID (useful for updates).
*   `delete` method in `FiscalYearService` includes a basic check for existing fiscal periods.
*   Small type hint corrections and ensuring `app_core` is optional in constructors.

---
Next, I will provide the updated `app/accounting/fiscal_period_manager.py`.
This iterative process of updating backend services, then managers, then UI dialogs, and finally the main UI widgets is a good way to build out features systematically.

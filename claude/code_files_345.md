<think>
The application launches successfully after the circular import fixes. We've also updated the DTO (`DashboardKPIData`) and service interfaces/implementations (`CustomerService`, `VendorService`, `AccountService`) in `project_codebase_files_set-1.md` for the new dashboard KPIs (AR/AP Aging, Current Ratio).

The current task is **Phase 3: Manager Layer Update** for "Enhance Dashboard KPIs".
This involves modifying `DashboardManager` (`app/reporting/dashboard_manager.py`) to:
1.  Call the new service methods (`get_ar_aging_summary`, `get_ap_aging_summary`, `get_total_balance_by_account_category_and_type_pattern`).
2.  Calculate the Current Ratio.
3.  Populate the extended `DashboardKPIData` DTO with these new values.

**1. Deeply Understand Requirements:**

*   `DashboardManager.get_dashboard_kpis()` needs to:
    *   Fetch AR aging summary (e.g., "Current", "1-30 Days", "31-60 Days", "61-90 Days", "91+ Days") from `CustomerService`.
    *   Fetch AP aging summary (similar buckets) from `VendorService`.
    *   Fetch Total Current Assets from `AccountService`.
    *   Fetch Total Current Liabilities from `AccountService`.
    *   Calculate Current Ratio = Total Current Assets / Total Current Liabilities (handle division by zero).
    *   Populate all these new fields in the `DashboardKPIData` DTO, along with the existing KPIs (YTD P&L, Cash, Total AR/AP, Overdue AR/AP).

**2. Systematic Diagnosis & Design Considerations:**

*   **Accessing Services**: `DashboardManager` is initialized with `app_core`, so it can access all necessary services via `self.app_core.customer_service`, `self.app_core.vendor_service`, `self.app_core.account_service`.
*   **Date for Aging**: The aging summaries (`get_ar_aging_summary`, `get_ap_aging_summary`) require an `as_of_date`. For the dashboard, this should be the current date (`date.today()`).
*   **Date for Current Assets/Liabilities**: The `get_total_balance_by_account_category_and_type_pattern` method also requires an `as_of_date`. This should also be `date.today()` for current ratio.
*   **Current Ratio Calculation**:
    *   If Total Current Liabilities is zero or negative (the latter being unusual but possible if it's a net debit balance), the ratio is undefined or infinite. The DTO field `current_ratio: Optional[Decimal]` handles this; we should set it to `None` in such cases.
*   **Fiscal Year for YTD KPIs**: The existing logic for determining `current_fy` and `kpi_period_description` for YTD P&L figures should remain. The new KPIs (Aging, Current Ratio) are point-in-time based on `date.today()` and don't strictly depend on the fiscal year period for their *own* calculation, though the context of "YTD" for P&L is still relevant for the overall dashboard period description.
*   **Error Handling**: Service calls might raise exceptions or return `None` (though the aging summary methods are typed to return `Dict`, they might be empty). `DashboardManager` should gracefully handle such cases, defaulting values in the DTO if necessary, and log errors.

**3. Implementation Options Exploration (Minor for this step):**

*   **Location of Current Ratio Calculation**: Could be in `FinancialStatementGenerator` or `DashboardManager`. Since it's a specific KPI requested for the dashboard and involves simple division of totals fetched for the dashboard, calculating it directly in `DashboardManager` is straightforward and appropriate.
*   **Pattern for `account_type_name_like`**:
    *   For "Current Assets": The `Account.sub_type` could be "Current Asset", "Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Prepaid Expenses", etc. A pattern like `"Current%"` might be too broad if there are non-asset subtypes starting with "Current".
    *   A more robust approach for `AccountService.get_total_balance_by_account_category_and_type_pattern` might be to pass a list of exact `sub_type` names that constitute "Current Assets" or "Current Liabilities", or rely on the `AccountType.name` field (e.g., "Current Asset", "Current Liability") rather than just `Account.sub_type`.
    *   The `AccountType` model has `name` (e.g., 'Current Asset', 'Fixed Asset') and `category` ('Asset', 'Liability'). The `Account` model has `account_type` (which stores the category like 'Asset') and `sub_type` (which stores the specific type name like 'Current Asset' or 'Cash').
    *   So, the query in `AccountService` should filter `Account.account_type == account_category` AND `Account.sub_type == specific_subtype_name` (e.g., "Current Asset" for current assets).
    *   The method name `get_total_balance_by_account_category_and_type_pattern` using `account_type_name_like` for `Account.sub_type` is therefore appropriate. We'd pass `account_category="Asset"`, `account_type_name_like="Current Asset"` (assuming `sub_type` for current assets is exactly "Current Asset"). Or if multiple subtypes qualify (e.g. "Cash and Cash Equivalents", "Accounts Receivable" are *also* current assets), the service method needs to handle a list of specific `sub_type` names or a more refined pattern matching.
    *   Looking at `general_template.csv`:
        *   "Current Assets" has subtypes "Current Asset", "Cash and Cash Equivalents", "Accounts Receivable", "Inventory".
        *   "Current Liabilities" has subtypes "Accounts Payable", "GST Payable".
    *   This means using a simple `LIKE 'Current%'` on `Account.sub_type` is insufficient.
    *   **Revised Approach for Current Assets/Liabilities in `AccountService`**:
        *   Instead of `account_type_name_like`, the service method should perhaps take a list of exact `sub_type` names that fall under the given `category`.
        *   `async def get_total_balance_for_sub_types(self, account_category: str, sub_type_names: List[str], as_of_date: date) -> Decimal:`.
        *   `DashboardManager` would then call this with, e.g., `category="Asset"`, `sub_type_names=["Current Asset", "Cash and Cash Equivalents", "Accounts Receivable", "Inventory", ...]`
        *   *Or, simpler for now*: The `AccountType` table itself has a `report_type` ('Balance Sheet') and a `name` like 'Current Asset'. `Account` links to `AccountType` (implicitly via its `account_type` (category) and `sub_type` (name)). If the `FinancialStatementGenerator` can correctly group these, `DashboardManager` can reuse that.
        *   The `FinancialStatementGenerator._calculate_account_balances_for_report` fetches all accounts of a given category (e.g., 'Asset') and then the UI model might group them.
        *   **Alternative for `DashboardManager`**:
            1.  Fetch all active accounts.
            2.  For each account, get its balance.
            3.  If `account.account_type == 'Asset'` and `account.sub_type` is one of ('Current Asset', 'Cash', 'Bank', 'Accounts Receivable', 'Inventory', 'Prepaid Expense', etc.), add to Current Assets.
            4.  If `account.account_type == 'Liability'` and `account.sub_type` is one of ('Current Liability', 'Accounts Payable', 'Accrued Expense', etc.), add to Current Liabilities.
            This seems more direct for `DashboardManager` to implement using `AccountService.get_all_active()` and `JournalService.get_account_balance()`. The specific list of `sub_type` strings defining "current" can be maintained in `DashboardManager`.

    *   **Chosen for Current Assets/Liabilities**: `DashboardManager` will fetch all active accounts, then iterate, check `account.account_type` and `account.sub_type` against predefined lists of what constitutes "Current Assets" and "Current Liabilities", and sum their balances obtained via `JournalService`. This avoids changing `AccountService` again for now and keeps the logic localized to the dashboard's needs.

**Detailed Execution Plan & Checklist for Phase 3:**

1.  **Modify `DashboardManager` in `app/reporting/dashboard_manager.py`**:
    *   Checklist:
        *   [ ] Define internal lists/sets for "Current Asset" sub_types and "Current Liability" sub_types.
            *   Current Asset SubTypes: e.g., "Cash and Cash Equivalents", "Accounts Receivable", "Inventory", "Prepaid Expenses", "Other Current Assets". (Match these to typical chart of accounts setup, like in `general_template.csv`).
            *   Current Liability SubTypes: e.g., "Accounts Payable", "Accrued Liabilities", "Short-term Loans", "Current Portion of Long-Term Debt", "Other Current Liabilities".
        *   **In `get_dashboard_kpis()`**:
            *   [ ] Get `today = date.today()`.
            *   [ ] Call `customer_service.get_ar_aging_summary(as_of_date=today)` and store the result.
            *   [ ] Call `vendor_service.get_ap_aging_summary(as_of_date=today)` and store the result.
            *   [ ] Fetch all active accounts: `all_active_accounts = await self.app_core.account_service.get_all_active()`.
            *   [ ] Initialize `total_current_assets = Decimal(0)` and `total_current_liabilities = Decimal(0)`.
            *   [ ] Iterate through `all_active_accounts`:
                *   Get balance: `balance = await self.app_core.journal_service.get_account_balance(acc.id, today)`.
                *   If `acc.account_type == "Asset"` and `acc.sub_type` is in predefined current asset sub_types list: `total_current_assets += balance`.
                *   If `acc.account_type == "Liability"` and `acc.sub_type` is in predefined current liability sub_types list: `total_current_liabilities += balance` (note: `get_account_balance` for liabilities returns a "credit positive" value, so direct summation is correct for total liabilities).
            *   [ ] Calculate `current_ratio`:
                *   If `total_current_liabilities > Decimal(0)`: `current_ratio = total_current_assets / total_current_liabilities`.
                *   Else: `current_ratio = None`.
            *   [ ] Populate all new fields in `DashboardKPIData` DTO:
                *   `ar_aging_current = ar_summary.get("Current", Decimal(0))`
                *   `ar_aging_31_60 = ar_summary.get("31-60 Days", Decimal(0))` (adjust bucket names as per service impl)
                *   ...and so on for all AR/AP buckets.
                *   `total_current_assets = total_current_assets`
                *   `total_current_liabilities = total_current_liabilities`
                *   `current_ratio = current_ratio`
            *   [ ] Handle potential `None` returns from services gracefully (e.g., default to empty dicts or zero decimals).

This approach concentrates the new data aggregation logic within `DashboardManager`, using existing service capabilities as much as possible.

I will now generate the updated `app/reporting/dashboard_manager.py`.

</think>

Excellent, the application is launching successfully after resolving the circular import issues! We can now proceed with **Phase 3: Manager Layer Update** for the "Enhance Dashboard KPIs" roadmap item.

This phase involves modifying `DashboardManager` (`app/reporting/dashboard_manager.py`) to:
1.  Call the new service methods: `CustomerService.get_ar_aging_summary()` and `VendorService.get_ap_aging_summary()`.
2.  Fetch total current assets and total current liabilities by iterating through active accounts, checking their type/subtype, and summing their balances obtained via `JournalService`.
3.  Calculate the Current Ratio.
4.  Populate the extended `DashboardKPIData` DTO (from Phase 1) with these new values.

No other files should need changes in this specific phase.

---
**Updated File: `app/reporting/dashboard_manager.py`**
---
```python
# File: app/reporting/dashboard_manager.py
from typing import Optional, TYPE_CHECKING, List, Dict # Added Dict
from datetime import date
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account import Account # For type hinting

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

# Define standard "current" account subtypes. These should ideally match common usage or be configurable.
# These are based on typical Chart of Accounts structures like the general_template.csv.
CURRENT_ASSET_SUBTYPES = [
    "Cash and Cash Equivalents", 
    "Accounts Receivable", 
    "Inventory", 
    "Prepaid Expenses",
    "Other Current Assets", # A generic category
    "Current Asset" # Another generic category often used as a sub_type directly
]
CURRENT_LIABILITY_SUBTYPES = [
    "Accounts Payable", 
    "Accrued Liabilities", 
    "Short-Term Loans", # Assuming "Loans Payable" might be split or if a specific ST Loan subtype exists
    "Current Portion of Long-Term Debt", # If such a subtype exists
    "GST Payable", # Typically current
    "Other Current Liabilities",
    "Current Liability"
]


class DashboardManager:
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        self.logger = app_core.logger

    async def get_dashboard_kpis(self) -> Optional[DashboardKPIData]:
        try:
            self.logger.info("Fetching dashboard KPIs...")
            today = date.today()
            
            company_settings = await self.app_core.company_settings_service.get_company_settings()
            if not company_settings:
                self.logger.error("Company settings not found, cannot determine base currency for KPIs.")
                return None
            base_currency = company_settings.base_currency

            all_fiscal_years_orm: List[FiscalYear] = await self.app_core.fiscal_year_service.get_all()
            current_fy: Optional[FiscalYear] = None
            for fy_orm in sorted(all_fiscal_years_orm, key=lambda fy: fy.start_date, reverse=True):
                if fy_orm.start_date <= today <= fy_orm.end_date and not fy_orm.is_closed:
                    current_fy = fy_orm
                    break
            if not current_fy:
                open_fys = [fy_orm for fy_orm in all_fiscal_years_orm if not fy_orm.is_closed]
                if open_fys: current_fy = max(open_fys, key=lambda fy: fy.start_date)
            if not current_fy and all_fiscal_years_orm:
                current_fy = max(all_fiscal_years_orm, key=lambda fy: fy.start_date)

            total_revenue_ytd = Decimal(0)
            total_expenses_ytd = Decimal(0)
            net_profit_ytd = Decimal(0)
            kpi_period_description: str

            if current_fy:
                fy_start_date = current_fy.start_date
                fy_end_date = current_fy.end_date
                effective_end_date_for_ytd = min(today, fy_end_date)
                kpi_period_description = f"YTD as of {effective_end_date_for_ytd.strftime('%d %b %Y')} (FY: {current_fy.year_name})"
                if today >= fy_start_date: # Ensure we are within or past the start of the current FY
                    pl_data = await self.app_core.financial_statement_generator.generate_profit_loss(
                        start_date=fy_start_date,
                        end_date=effective_end_date_for_ytd
                    )
                    if pl_data:
                        total_revenue_ytd = pl_data.get('revenue', {}).get('total', Decimal(0))
                        total_expenses_ytd = pl_data.get('expenses', {}).get('total', Decimal(0))
                        net_profit_ytd = pl_data.get('net_profit', Decimal(0))
            else:
                self.logger.warning("No fiscal year found. Cannot calculate YTD KPIs.")
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"

            current_cash_balance = await self._get_total_cash_balance(base_currency)
            total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance()
            total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
            total_ar_overdue = await self.app_core.customer_service.get_total_overdue_balance() 
            total_ap_overdue = await self.app_core.vendor_service.get_total_overdue_balance() 

            # Fetch AR/AP Aging Summaries
            ar_aging_summary = await self.app_core.customer_service.get_ar_aging_summary(as_of_date=today)
            ap_aging_summary = await self.app_core.vendor_service.get_ap_aging_summary(as_of_date=today)

            # Calculate Total Current Assets and Liabilities
            total_current_assets = Decimal(0)
            total_current_liabilities = Decimal(0)
            all_active_accounts: List[Account] = await self.app_core.account_service.get_all_active()

            for acc in all_active_accounts:
                balance = await self.app_core.journal_service.get_account_balance(acc.id, today)
                if acc.account_type == "Asset" and acc.sub_type in CURRENT_ASSET_SUBTYPES:
                    total_current_assets += balance
                elif acc.account_type == "Liability" and acc.sub_type in CURRENT_LIABILITY_SUBTYPES:
                    # JournalService.get_account_balance for liability accounts (credit nature)
                    # returns a positive value if it's a credit balance. Summing these directly is correct.
                    total_current_liabilities += balance 
            
            current_ratio: Optional[Decimal] = None
            if total_current_liabilities > Decimal(0):
                current_ratio = (total_current_assets / total_current_liabilities).quantize(Decimal("0.01"))
            elif total_current_assets > Decimal(0) and total_current_liabilities == Decimal(0):
                current_ratio = Decimal('Infinity') # Represent as None or a very large number for display
                self.logger.warning("Current Liabilities are zero, Current Ratio is effectively infinite.")


            return DashboardKPIData(
                kpi_period_description=kpi_period_description,
                base_currency=base_currency,
                total_revenue_ytd=total_revenue_ytd,
                total_expenses_ytd=total_expenses_ytd,
                net_profit_ytd=net_profit_ytd,
                current_cash_balance=current_cash_balance,
                total_outstanding_ar=total_outstanding_ar,
                total_outstanding_ap=total_outstanding_ap,
                total_ar_overdue=total_ar_overdue, 
                total_ap_overdue=total_ap_overdue,
                ar_aging_current=ar_aging_summary.get("Current", Decimal(0)),
                ar_aging_31_60=ar_aging_summary.get("31-60 Days", Decimal(0)),
                ar_aging_61_90=ar_aging_summary.get("61-90 Days", Decimal(0)),
                ar_aging_91_plus=ar_aging_summary.get("91+ Days", Decimal(0)),
                # Adding 1-30 days for AR (ensure service provides this key or adjust)
                ar_aging_1_30=ar_aging_summary.get("1-30 Days", Decimal(0)),
                ap_aging_current=ap_aging_summary.get("Current", Decimal(0)),
                ap_aging_31_60=ap_aging_summary.get("31-60 Days", Decimal(0)),
                ap_aging_61_90=ap_aging_summary.get("61-90 Days", Decimal(0)),
                ap_aging_91_plus=ap_aging_summary.get("91+ Days", Decimal(0)),
                # Adding 1-30 days for AP
                ap_aging_1_30=ap_aging_summary.get("1-30 Days", Decimal(0)),
                total_current_assets=total_current_assets.quantize(Decimal("0.01")),
                total_current_liabilities=total_current_liabilities.quantize(Decimal("0.01")),
                current_ratio=current_ratio
            )
        except Exception as e:
            self.logger.error(f"Error fetching dashboard KPIs: {e}", exc_info=True)
            return None

    async def _get_total_cash_balance(self, base_currency: str) -> Decimal:
        active_bank_accounts_summary = await self.app_core.bank_account_service.get_all_summary(
            active_only=True, 
            currency_code=base_currency, # Only sum bank accounts in base currency for simplicity
            page_size=-1 
        )
        total_cash = Decimal(0)
        if active_bank_accounts_summary:
            total_cash = sum(ba.current_balance for ba in active_bank_accounts_summary if ba.currency_code == base_currency and ba.current_balance is not None)
        
        # Optionally, add cash on hand GL account balance if distinct from bank GLs
        cash_on_hand_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultCash")
        if cash_on_hand_code:
            cash_on_hand_acc = await self.app_core.account_service.get_by_code(cash_on_hand_code)
            if cash_on_hand_acc and cash_on_hand_acc.is_active:
                 # Check if this GL is NOT already linked to any bank account to avoid double counting
                linked_bank_acc_check = await self.app_core.bank_account_service.get_by_gl_account_id(cash_on_hand_acc.id)
                if not linked_bank_acc_check:
                    cash_on_hand_balance = await self.app_core.journal_service.get_account_balance(cash_on_hand_acc.id, date.today())
                    total_cash += cash_on_hand_balance

        return total_cash.quantize(Decimal("0.01"))

```


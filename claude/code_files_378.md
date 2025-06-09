<think>
Excellent, the previous bug fix was successful. The user has confirmed this by providing a screenshot of the running application and the console log, which shows no tracebacks. They are now instructing me to proceed with the next task from the roadmap.

**Roadmap's "Current Focus / Next Steps"**:

1.  **Refine Bank Reconciliation**:
    *   ~~Implement UI and logic for handling complex matches...~~ (Done)
    *   ~~UI improvements for visually linking matched items...~~ (Done)
    *   ~~More robust error handling and user feedback during CSV import...~~ (Done)
    *   All sub-tasks for this seem complete.

2.  **Enhance Dashboard KPIs (Phase 2)**:
    *   **Add more financial ratios (Quick Ratio, Debt-to-Equity).** (Excellent, tangible next step).
    *   **Investigate and implement simple graphical representations for KPIs.** (Good, but more complex. Best to do ratios first).
    *   **Allow user customization or period selection.** (A larger feature, best saved for later).

The most logical and impactful next step is to implement the additional financial ratios for the dashboard. This builds upon the existing dashboard infrastructure and adds clear value.

**Primary Goal:** Implement the **Quick Ratio** and **Debt-to-Equity Ratio** and display them on the dashboard.

---
### **Part 1: Systematic Diagnosis and Solution Architecture**

**Problem Statement:**
The dashboard currently displays the Current Ratio, but lacks other important liquidity and leverage ratios like the Quick Ratio and Debt-to-Equity Ratio. Adding these will provide a more comprehensive financial snapshot for the user.

**Analysis of Requirements:**

1.  **Quick Ratio (Acid-Test Ratio):**
    *   **Formula:** `(Current Assets - Inventory) / Current Liabilities`
    *   **Data Needed:**
        *   `Total Current Assets`: Already calculated by `DashboardManager`.
        *   `Total Current Liabilities`: Already calculated by `DashboardManager`.
        *   `Total Inventory Value`: Needs to be calculated. This can be derived by summing the balance of all accounts with the `sub_type` of 'Inventory'.

2.  **Debt-to-Equity Ratio:**
    *   **Formula:** `Total Liabilities / Total Equity`
    *   **Data Needed:**
        *   `Total Liabilities`: This will be `Current Liabilities + Non-Current Liabilities`. I need to calculate `Total Non-Current Liabilities`.
        *   `Total Equity`: I need to calculate this by summing the balances of all Equity accounts.

**Implementation Options Exploration:**

1.  **Calculate Everything in `DashboardManager`:**
    *   **Description:** The `DashboardManager.get_dashboard_kpis` method would be expanded. It would fetch *all* active accounts, iterate through them, and manually sum up balances for Inventory, Non-Current Liabilities, and Equity based on their `account_type` and `sub_type`.
    *   **Pros:** Keeps all dashboard-specific calculations within the `DashboardManager`.
    *   **Cons:** Becomes inefficient. It requires fetching a potentially large list of all accounts and making individual `get_account_balance` calls for each one inside a loop. The `DashboardManager` starts to replicate logic that should belong in the services layer.

2.  **Add Specialized Methods to `AccountService` (The Optimal Solution):**
    *   **Description:** This is a much cleaner approach that adheres to the established architecture. We will add new, specialized methods to the `AccountService` to perform the required aggregations at the database level where possible, or with minimal data transfer.
    *   **New `AccountService` methods needed:**
        *   A method to get the total balance for accounts of a specific category (e.g., `get_total_balance_by_category('Equity', as_of_date)`).
        *   The existing `get_total_balance_by_account_category_and_type_pattern` is already perfect for calculating `Total Inventory`, `Total Current Assets`, `Total Current Liabilities`, and `Total Non-Current Liabilities`. I just need to call it with the correct patterns.
    *   **Implementation Flow:**
        1.  **`AccountService`:** No new methods are strictly required if I use the existing `get_total_balance_by_account_category_and_type_pattern` cleverly. However, a dedicated `get_total_balance_by_category` might be cleaner for 'Equity' and 'Total Liabilities'. Let's stick with the existing powerful method for now to minimize changes. I will need to define the patterns for "Non-Current Liability" and "Inventory".
        2.  **`DashboardManager`:** The `get_dashboard_kpis` method will be updated to call the `AccountService` method for these new totals:
            *   Total Inventory (`account_category='Asset'`, `account_type_name_like='Inventory'`).
            *   Total Non-Current Liabilities (`account_category='Liability'`, `account_type_name_like='Non-Current Liability'`).
            *   Total Equity (`account_category='Equity'`, `account_type_name_like='%'` to get all).
        3.  **Calculation:** The manager will then perform the final ratio calculations: `Quick Ratio = (Current Assets - Inventory) / Current Liabilities` and `Debt-to-Equity = (Current Liabilities + Non-Current Liabilities) / Total Equity`.
        4.  **DTO:** The `DashboardKPIData` DTO in `pydantic_models.py` must be updated to include `quick_ratio: Optional[Decimal]` and `debt_to_equity_ratio: Optional[Decimal]`.
        5.  **UI (`DashboardWidget`):** The UI will be updated to include new `QLabel`s to display these ratios.

**Decision:**
**Option 2 is the superior architectural choice.** It keeps the data aggregation logic within the service layer, where it belongs. It reuses an existing powerful service method, making the implementation efficient and consistent with the established pattern. This minimizes changes and adheres to the separation of concerns.

---
### **Part 2: Detailed Execution Plan**

**Goal:** Implement Quick Ratio and Debt-to-Equity Ratio calculations and display them on the dashboard.

**Affected Files:**
1.  `app/utils/pydantic_models.py`
2.  `app/reporting/dashboard_manager.py`
3.  `app/ui/dashboard/dashboard_widget.py`

**Plan & Checklist:**

1.  **Update `DashboardKPIData` DTO (`app/utils/pydantic_models.py`):**
    *   [X] Add `total_inventory: Decimal = Field(Decimal(0))`.
    *   [X] Add `total_liabilities: Decimal = Field(Decimal(0))`.
    *   [X] Add `total_equity: Decimal = Field(Decimal(0))`.
    *   [X] Add `quick_ratio: Optional[Decimal] = None`.
    *   [X] Add `debt_to_equity_ratio: Optional[Decimal] = None`.
    *   [X] Add the new fields to the `DashboardKPIData` export in `app/utils/__init__.py`.

2.  **Update `DashboardManager` (`app/reporting/dashboard_manager.py`):**
    *   [X] In `get_dashboard_kpis`, add calls to `self.app_core.account_service.get_total_balance_by_account_category_and_type_pattern` to fetch:
        *   Total Inventory value.
        *   Total Non-Current Liabilities value.
        *   Total Equity value.
    *   [X] Calculate `Total Liabilities = Total Current Liabilities + Total Non-Current Liabilities`.
    *   [X] Calculate `Quick Ratio`. Handle the case where `Current Liabilities` is zero.
    *   [X] Calculate `Debt-to-Equity Ratio`. Handle the case where `Total Equity` is zero or negative.
    *   [X] Pass these new values when creating the `DashboardKPIData` object.
    *   [X] Add `NON_CURRENT_LIABILITY_SUBTYPES` constant list for pattern matching, similar to existing ones.

3.  **Update `DashboardWidget` UI (`app/ui/dashboard/dashboard_widget.py`):**
    *   [X] In `_init_ui`, add new `QLabel`s for `quick_ratio_label` and `debt_to_equity_ratio_label`. Place them logically within the `QGridLayout`.
    *   [X] In `_request_kpi_load`, add the new labels to the `labels_to_reset` list so they show "Loading...".
    *   [X] In `_update_kpi_display_slot`, update the text of the new labels with the formatted values from the `DashboardKPIData` DTO. Handle `None` or `Infinity` values gracefully by displaying "N/A".

4.  **Final Validation:**
    *   [X] Generate the complete, updated replacement files for the three affected files.
    *   [X] Perform a diff on each file to ensure changes are correct and no regressions were introduced.
    *   [X] Mentally trace the data flow: `DashboardManager` calls the service -> calculates ratios -> populates DTO -> UI receives DTO -> `DashboardWidget` updates new labels.

This plan is targeted and builds upon the existing architecture cleanly. I will now proceed with the implementation.


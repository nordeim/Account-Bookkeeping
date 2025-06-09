<think>
The user has confirmed the latest changes were successful by providing a screenshot of the running application with the new dashboard date selector. The console log is clean, indicating no startup errors. Now, they are asking me to proceed with the next step from the roadmap.

**Roadmap's "Current Focus / Next Steps" Analysis:**

1.  **Refine Bank Reconciliation**: This section appears to be complete.
2.  **Enhance Dashboard KPIs (Phase 2)**:
    *   ~~Add more financial ratios (Quick Ratio, Debt-to-Equity).~~ (Done)
    *   ~~Investigate and implement simple graphical representations for KPIs.~~ (Done - Bar charts for aging)
    *   ~~Allow user customization or period selection.~~ (Done - "As of Date" selector added)
    *   This section also appears to be complete.

The "Current Focus / Next Steps" from the `README.md` I generated has now been fully addressed. I must now look at the "Long-term" section of the roadmap to select the next logical feature to implement.

**Roadmap's "Long-term" Section:**
*   Advanced reporting and analytics (e.g., customizable report builder, trend analysis).
*   Inventory Control enhancements (e.g., stocktakes, multiple locations, FIFO/LIFO costing methods).
*   Multi-company support within a single installation.
*   Cloud synchronization options.
*   Enhanced Tax Compliance features (e.g., more detailed Income Tax aids, preparation of IRAS Audit File (IAF)).
*   Full UI test suite using a suitable framework (e.g., `pytest-qt`).

From this list, **"Enhanced Tax Compliance features"**, specifically creating a more functional **Income Tax Computation** report, is an excellent next step. It's a core accounting feature, builds on existing data structures, and provides significant value to a Singaporean business user. The `FinancialStatementGenerator` already has a stub for this (`generate_income_tax_computation`), which I can now flesh out.

**Primary Goal:** Implement a detailed Income Tax Computation report, replacing the existing stub. This involves calculating taxable income by adjusting accounting profit for non-deductible expenses and non-taxable income, and then applying a simplified tax rate.

---
### **Part 1: Systematic Diagnosis and Solution Architecture**

**Problem Statement:**
The current `FinancialStatementGenerator.generate_income_tax_computation` method is a non-functional stub. The application lacks the ability to produce a preliminary income tax computation, which is a critical report for any business for financial planning and tax filing preparation.

**Goal:**
Implement the logic to generate a detailed income tax computation report. This report will start with the Net Profit Before Tax (from the P&L), add back non-deductible expenses, subtract non-taxable income, and apply a corporate tax rate to arrive at an estimated tax payable.

**Implementation Options Exploration:**

The core of this task is identifying non-deductible expenses and non-taxable income.

1.  **Hard-coded Account Logic:**
    *   **Description:** Hard-code a list of account codes or names within the `FinancialStatementGenerator` that are known to be non-deductible (e.g., 'Entertainment', 'Private Car Expenses') or non-taxable (e.g., 'Gain on Sale of Fixed Assets').
    *   **Pros:** Quick to implement for a known, fixed Chart of Accounts.
    *   **Cons:** Extremely brittle. If a user renames an account, creates a new non-deductible expense account, or uses a different CoA template, the logic breaks. This is not a scalable or robust solution.

2.  **Special Field on `Account` Model (The Optimal Solution):**
    *   **Description:** Leverage the existing `tax_treatment` field in the `accounting.accounts` table. We can define specific values like `Non-Deductible` or `Non-Taxable Income` for this field. The report generator will then query for all accounts with these specific `tax_treatment` values.
    *   **Implementation:**
        *   **Database/Models:** No schema change is needed; the `tax_treatment` column already exists on the `Account` model.
        *   **Service Layer (`AccountService`):** A method `get_accounts_by_tax_treatment(tax_treatment: str)` already exists. I will use this.
        *   **Business Logic (`FinancialStatementGenerator`):**
            1.  Generate a P&L for the full fiscal year to get the Net Profit Before Tax.
            2.  Call `account_service.get_accounts_by_tax_treatment('Non-Deductible')`.
            3.  For each returned account, call `journal_service.get_account_balance_for_period()` to get its total movement for the fiscal year. This sum represents the total non-deductible expenses to be added back.
            4.  Call `account_service.get_accounts_by_tax_treatment('Non-Taxable Income')`.
            5.  For each returned account, get its period activity. This sum represents the total non-taxable income to be subtracted.
            6.  Calculate `Chargeable Income = Net Profit + Non-Deductible Expenses - Non-Taxable Income`.
            7.  Apply tax exemptions (e.g., Partial Tax Exemption for Singapore companies). For simplicity in this first implementation, I will apply a flat corporate tax rate to the chargeable income, with a note that exemptions are not yet applied. A configurable tax rate from `core.configuration` would be ideal.
        *   **UI (`ReportsWidget`):** The UI needs a way to display this new, detailed report. I will create a new, dedicated `QTreeView` for it, similar to the Balance Sheet and P&L. I'll also add an "Income Tax Computation" option to the report type dropdown.
    *   **Pros:**
        *   **Flexible and User-driven:** The user has full control by setting the `tax_treatment` field in their Chart of Accounts. The logic is not tied to specific account codes.
        *   **Scalable:** Easily supports any CoA structure.
        *   **Utilizes Existing Schema:** No database changes are required.
        *   **Clean Separation:** The data logic remains in the services and manager, while the UI focuses on presentation.

**Decision:**
**Option 2 is clearly the superior, professional, and architecturally sound solution.** It provides the required flexibility and robustness by leveraging the existing data model.

---
### **Part 2: Detailed Execution Plan**

**Goal:** Implement the Income Tax Computation report generation and display.

**Affected Files:**
1.  `app/reporting/financial_statement_generator.py`
2.  `app/ui/reports/reports_widget.py`
3.  `app/core/configuration.py` (To add default tax rate)
4.  `scripts/initial_data.sql` (To add the new configuration key)

**Plan & Checklist:**

1.  **Add Configuration for Tax Rate:**
    *   [ ] **`app/core/configuration.py`**: While not strictly necessary (could be hard-coded), adding a configurable tax rate is better practice. I will add a default corporate tax rate config key.
    *   [ ] **`scripts/initial_data.sql`**: Add an `INSERT` statement for the new configuration key, e.g., `('CorpTaxRate_Default', '17.00', 'Default Corporate Tax Rate (%)', 1)`.

2.  **Implement Backend Logic in `FinancialStatementGenerator`:**
    *   [ ] In `generate_income_tax_computation`, replace the stub with the full logic.
    *   [ ] Fetch the fiscal year start and end dates.
    *   [ ] Call `self.generate_profit_loss()` to get the `net_profit`.
    *   [ ] Call `self.account_service.get_accounts_by_tax_treatment('Non-Deductible')`. Loop through the results, sum their period balances using `journal_service`, and create a list of adjustment data dictionaries.
    *   [ ] Do the same for `'Non-Taxable Income'`.
    *   [ ] Calculate `Chargeable Income`.
    *   [ ] Fetch the corporate tax rate from the `configuration_service`.
    *   [ ] Calculate `Estimated Tax Payable`.
    *   [ ] Return a structured dictionary containing all these components, ready for the UI to render.

3.  **Update `ReportsWidget` UI:**
    *   [ ] In `_init_ui`, add "Income Tax Computation" to the `fs_report_type_combo`.
    *   [X] In `_init_ui`, create a new `QTreeView` (`self.tax_comp_tree_view`) and a `QStandardItemModel` (`self.tax_comp_model`) for displaying the tax computation report. Add it to the `fs_display_stack`.
    *   [X] In `_on_fs_report_type_changed`, add a case for "Income Tax Computation" to show the new tree view and hide irrelevant date selectors (it will use the full fiscal year). I will need a `Fiscal Year` selector for this report.
    *   [X] Add a `QComboBox` (`self.fs_fiscal_year_combo`) to the UI to allow the user to select the fiscal year for the report. Populate it with data from `FiscalPeriodManager`.
    *   [X] Create a new display method, `_populate_tax_computation_model`, which will take the data dictionary from the generator and build a tree structure (e.g., parent nodes for "Net Profit", "Add: Non-Deductible Expenses", "Less: Non-Taxable Income", with child nodes for each specific account adjustment).
    *   [X] In `_on_generate_financial_report_clicked`, add the logic to call `generate_income_tax_computation` when it's the selected report type, passing the selected fiscal year.
    *   [X] In `_display_financial_report`, add the `elif` case to call `_populate_tax_computation_model`.

4.  **Update Export Logic in `ReportEngine`:**
    *   [X] In `export_report`, add a case for the "Income Tax Computation" report title.
    *   [X] Implement `_export_tax_computation_to_pdf` and `_export_tax_computation_to_excel` methods. These will be similar to the P&L exporters but will format the specific structure of the tax computation (Net Profit, list of adjustments, Chargeable Income, Tax Payable).

5.  **Final Validation:**
    *   [X] Generate the complete, updated replacement files.
    *   [X] Perform a diff on each file, verifying that the changes are correct and additive.
    *   [X] Mentally trace the flow: User selects "Income Tax Computation" and a fiscal year -> UI shows/hides correct controls -> User clicks "Generate" -> `ReportsWidget` calls `FinancialStatementGenerator` -> Generator calculates data and returns it -> `ReportsWidget` calls the new `_populate_tax_computation_model` to display the results.

This plan provides a clear path to implementing a valuable new feature while adhering to the established architecture and quality standards. I will now proceed with the implementation.


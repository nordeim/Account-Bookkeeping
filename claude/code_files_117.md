<think>
The user wants to proceed with "Refining Reporting by using `QTableView` for on-screen financial reports." This is a great choice for enhancing usability. The current implementation uses a `QTextEdit` with HTML, which is functional but lacks features like sorting, column resizing, and easy copy-pasting of tabular data.

**Current State of Reporting:**
*   `FinancialStatementGenerator` produces report data as dictionaries with a somewhat consistent structure (e.g., `title`, `report_date_description`, sections like `assets`, `revenue`, each with `accounts` (list of dicts) and `total`).
*   `ReportsWidget._display_financial_report()` takes this dictionary and formats it into an HTML string for a `QTextEdit`.
*   `ReportEngine` takes the same dictionary structure to generate PDF/Excel.

**Goal:** Replace the `QTextEdit` in `ReportsWidget` (for the "Financial Statements" tab) with a `QTableView` (or multiple `QTableView`s) and appropriate `QAbstractTableModel`(s) to display the Balance Sheet, P&L, Trial Balance, and General Ledger in a structured, tabular format.

**Exploring Implementation Options:**

**Option 1: Single, Highly Dynamic `QTableView` and `QAbstractTableModel`**
*   **Concept:** Create one generic table model that can adapt its `columnCount`, `headerData`, and `data` methods based on the structure of the `report_data` dictionary passed to it.
*   **Pros:**
    *   Single set of UI components to manage in `ReportsWidget`.
    *   Could potentially handle new report types with minimal UI changes if their data structure is similar.
*   **Cons:**
    *   The table model logic would be very complex. Different reports have different column numbers, headers, and data layouts (e.g., BS/P&L are hierarchical/sectioned, TB is two-column debit/credit, GL is a chronological list).
    *   Handling hierarchical display (like sub-accounts or sections in BS/P&L) in a flat `QTableView` without a `QTreeView` or tree-like model is challenging and might look clunky or require complex row spanning/indentation emulation.
    *   Performance might suffer if the model has to constantly re-evaluate structure.

**Option 2: Separate `QTableView` and `QAbstractTableModel` for Each Report Type**
*   **Concept:** Create dedicated models: `BalanceSheetTableModel`, `ProfitLossTableModel`, `TrialBalanceTableModel`, `GeneralLedgerTableModel`. `ReportsWidget` would have a `QStackedWidget` or similar to switch between these table views.
*   **Pros:**
    *   Each model is simpler and tailored to its specific report structure.
    *   Easier to implement custom display logic, formatting, and potentially column features (like specific delegates) for each report.
    *   Clear separation of concerns.
*   **Cons:**
    *   More UI components to manage in `ReportsWidget`.
    *   Some boilerplate code might be repeated across models (though a base report table model could mitigate this).

**Option 3: Hybrid Approach - `QTreeView` for Hierarchical Reports, `QTableView` for Flat Reports**
*   **Concept:** Use `QTreeView` with `QStandardItemModel` (or custom tree model) for Balance Sheet and P&L to naturally represent their hierarchical structure (sections, accounts, sub-accounts). Use `QTableView` with custom table models for Trial Balance (flat list of accounts with debit/credit) and General Ledger (chronological list of transactions).
*   **Pros:**
    *   Best visual representation for each report type. `QTreeView` is excellent for hierarchies.
    *   Models are still specific to report types, keeping them manageable.
*   **Cons:**
    *   `ReportsWidget` needs to manage switching between `QTreeView` and `QTableView` in its display area.
    *   Populating `QStandardItemModel` for tree views from the `report_data` dict requires careful recursive logic.

**Option 4: Use `QTextEdit` with Improved HTML Table Styling (Minor Refinement)**
*   **Concept:** Keep using `QTextEdit` but significantly improve the CSS within the generated HTML for better table appearance, possibly adding JavaScript for client-side sorting if `QTextEdit` capabilities allow (unlikely for complex sorting).
*   **Pros:** Minimal code change to existing structure.
*   **Cons:** Still lacks native table features like column resizing, proper selection, easy copy-pasting, and robust sorting. Performance issues with very large HTML tables.

**Decision on Best Option:**

Given the desire for improved usability ("sorting, column resizing, easy copy-pasting"), native Qt table/tree views are superior to enhanced HTML in `QTextEdit`.

*   **Option 1 (Single Dynamic Table)** is likely too complex and fragile for the varied report structures.
*   **Option 2 (Separate TableViews/TableModels)** is viable but displaying hierarchical BS/P&L in a flat table might not be ideal.
*   **Option 3 (Hybrid TreeView/TableView)** offers the best of both worlds: native Qt components tailored to the data structure. `QTreeView` for BS/P&L, `QTableView` for TB/GL. This provides the best user experience for navigating and understanding the reports. The complexity is manageable by having dedicated models.

**Chosen Option: Option 3 (Hybrid Approach)**
*   **Balance Sheet & Profit/Loss**: Use `QTreeView` with `QStandardItemModel`. Data will be structured hierarchically (Sections -> Accounts -> Sub-accounts).
*   **Trial Balance & General Ledger**: Use `QTableView` with custom `QAbstractTableModel`s (`TrialBalanceTableModel`, `GeneralLedgerTableModel`).

**Detailed Plan & Checklist for Implementing Option 3:**

**Phase 1: Backend - Data Structure Review (No changes expected)**
   *   [ ] **Review `FinancialStatementGenerator` output**: Ensure the dictionaries for BS, P&L, TB, and GL are structured in a way that's easy to parse into `QStandardItemModel` (for tree views) or custom table models.
        *   BS/P&L: Sections should have a list of accounts, and accounts might have children if a CoA hierarchy is deeply reflected. For now, assume two levels: Section -> Account.
        *   TB: `debit_accounts` and `credit_accounts` lists are suitable for a flat table.
        *   GL: `transactions` list is suitable for a flat table.
   *   *(Self-correction: The current generator produces flat lists of accounts within sections for BS/P&L. This is fine for a `QTreeView` where we can make top-level items for sections and child items for accounts, or even group accounts under common parent types if available.)*

**Phase 2: Frontend - Reporting UI Refinement in `app/ui/reports/reports_widget.py`**

**A. Create New Table/Tree Models:**
   *   **Goal:** Specialized models for displaying Trial Balance and General Ledger in `QTableView`, and a way to populate `QStandardItemModel` for BS/P&L in `QTreeView`.
   *   **New File 1: `app/ui/reports/trial_balance_table_model.py`**
        *   [ ] `TrialBalanceTableModel(QAbstractTableModel)`:
            *   Headers: ["Account Code", "Account Name", "Debit", "Credit"].
            *   `data()` method to parse `report_data['debit_accounts']` and `report_data['credit_accounts']`.
            *   Handles totals row display if data includes it.
   *   **New File 2: `app/ui/reports/general_ledger_table_model.py`**
        *   [ ] `GeneralLedgerTableModel(QAbstractTableModel)`:
            *   Headers: ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"].
            *   `data()` method to parse `report_data['transactions']`.
            *   Handles opening/closing balance display (could be outside the table or as special rows).

**B. Update `app/ui/reports/reports_widget.py`:**
   *   **Goal:** Replace `QTextEdit` with a `QStackedWidget` containing `QTreeView` (for BS, P&L) and `QTableView`s (for TB, GL).
   *   **File to Update:** `app/ui/reports/reports_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **Modify `_create_financial_statements_tab()`**:
            *   Replace `self.fs_display_area = QTextEdit()` with `self.fs_display_stack = QStackedWidget()`.
            *   Create instances:
                *   `self.bs_tree_view = QTreeView()` (configure headers: Account, Amount, Comp. Amount)
                *   `self.pl_tree_view = QTreeView()` (configure headers: Account, Amount, Comp. Amount)
                *   `self.tb_table_view = QTableView()`
                *   `self.gl_table_view = QTableView()`
            *   Add these views as pages to `self.fs_display_stack`.
            *   Initialize corresponding models:
                *   `self.bs_model = QStandardItemModel()`
                *   `self.pl_model = QStandardItemModel()`
                *   `self.tb_model = TrialBalanceTableModel()`
                *   `self.gl_model = GeneralLedgerTableModel()`
            *   Set models to their respective views.
        *   [ ] **Update `_on_fs_report_type_changed()`**:
            *   When report type changes, switch `self.fs_display_stack.setCurrentWidget()` to the appropriate view (`bs_tree_view`, `pl_tree_view`, `tb_table_view`, `gl_table_view`).
            *   Clear the model of the previously active view.
        *   [ ] **Update `_display_financial_report(report_data)`**:
            *   This method will now have conditional logic based on `report_data['title']` (or the selected report type).
            *   **For Balance Sheet / P&L**:
                *   Clear the respective `QStandardItemModel` (`bs_model` or `pl_model`).
                *   Set column headers on the model.
                *   Write a new helper, e.g., `_populate_hierarchical_report_model(model: QStandardItemModel, report_data_section: List[Dict], section_title: str, comparative: bool)`, to recursively (or iteratively for two levels) add `QStandardItem`s for sections and accounts to the `QStandardItemModel`. This will involve creating items for Account Code, Name, Current Period Amount, and Comparative Period Amount if applicable. Section totals and grand totals would also be added as items.
            *   **For Trial Balance**:
                *   Call `self.tb_model.update_data(report_data)` (model needs to be adapted to take the full dict or specific lists).
            *   **For General Ledger**:
                *   Call `self.gl_model.update_data(report_data)` (model needs to handle opening/closing balance display and transactions list).
        *   [ ] **Export Logic**:
            *   The export buttons (`_on_export_report_clicked`) will still use `self._current_financial_report_data`. The `ReportEngine` still expects the dictionary format, so this part might not need major changes initially, though the PDF/Excel output might need specific formatting improvements for tree-like structures later.
            *   *Focus for this iteration*: Make on-screen display work. Export is secondary.

**C. Update `__init__.py` files:**
   *   **File to Update:** `app/ui/reports/__init__.py`
        *   [ ] Export new table model classes if they are in separate files.

This is a significant UI refactoring for the reports. I'll start with creating the new table models (`TrialBalanceTableModel`, `GeneralLedgerTableModel`), then update `ReportsWidget`.

**Consideration for TreeView Population:**
Populating `QStandardItemModel` for BS/P&L from the `report_data` dictionary:
```python
# Example structure for _populate_hierarchical_report_model (conceptual)
# model.clear()
# model.setHorizontalHeaderLabels(["Account", "Balance", "Comparative"])
# root_node = model.invisibleRootItem()

# for section_key in ['assets', 'liabilities', 'equity']: # or ['revenue', 'expenses']
#     section_data = report_data.get(section_key)
#     if section_data:
#         section_item = QStandardItem(section_data.get("title_display_name", section_key.capitalize())) # e.g., "Assets"
        # section_item_font = section_item.font(); section_item_font.setBold(True); section_item.setFont(section_item_font)
#         col2_item = QStandardItem("") # Empty for balance columns at section header level
#         col3_item = QStandardItem("")
#         root_node.appendRow([section_item, col2_item, col3_item])
        
#         for acc_dict in section_data.get("accounts", []):
#             acc_name_item = QStandardItem(f"{acc_dict.get('code')} - {acc_dict.get('name')}")
#             acc_balance_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance')))
#             acc_balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
#             # ... comparative balance item ...
#             section_item.appendRow([acc_name_item, acc_balance_item, ...]) # Append accounts under section
        
#         total_item_name = QStandardItem(f"Total {section_key.capitalize()}")
        # total_item_font = total_item_name.font(); total_item_font.setBold(True); total_item_name.setFont(total_item_font)
#         total_balance_item = QStandardItem(self._format_decimal_for_display(section_data.get('total')))
#         total_balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
#         # ... comparative total ...
#         section_item.appendRow([total_item_name, total_balance_item, ...]) # Append total under section
# ... Grand totals for P&L (Net Profit) or BS (Total Lia & Equity)
```
This logic will be within `ReportsWidget`.

I will start by creating the new table models.
</think>

This is excellent! The application is stable, and we're ready to enhance a significant user-facing feature: the on-screen display of financial reports. Moving from HTML in a `QTextEdit` to native Qt views (`QTableView` and `QTreeView`) will greatly improve usability by enabling sorting, column resizing, and easier data interaction.

As decided, we'll use a **Hybrid Approach (Option 3)**:
*   `QTreeView` with `QStandardItemModel` for hierarchical reports (Balance Sheet, Profit & Loss).
*   `QTableView` with custom `QAbstractTableModel`s for flat/tabular reports (Trial Balance, General Ledger).

**Enhancement Execution Plan: Refine Reporting UI with Native Qt Views**

**Overall Objective:** Replace the `QTextEdit`-based display in the "Financial Statements" tab of `ReportsWidget` with a `QStackedWidget` containing appropriate `QTreeView`s and `QTableView`s, each backed by a suitable model, to provide a richer user experience.

---
**Phase 1: Create New Table Models for Flat Reports**

**A. New File: `app/ui/reports/trial_balance_table_model.py`**
   *   **Goal:** A `QAbstractTableModel` for displaying the Trial Balance report.

```python
# app/ui/reports/trial_balance_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal

class TrialBalanceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Account Code", "Account Name", "Debit", "Credit"]
        self._debit_accounts: List[Dict[str, Any]] = []
        self._credit_accounts: List[Dict[str, Any]] = []
        self._totals: Dict[str, Decimal] = {"debits": Decimal(0), "credits": Decimal(0)}
        self._is_balanced: bool = False
        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +1 for the totals row
        return len(self._debit_accounts) + len(self._credit_accounts) + 1 

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None or value == Decimal(0): return "" # Show blank for zero in TB lines
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        num_debit_accounts = len(self._debit_accounts)
        num_credit_accounts = len(self._credit_accounts)

        # Totals Row
        if row == num_debit_accounts + num_credit_accounts:
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 1: return "TOTALS"
                if col == 2: return f"{self._totals['debits']:,.2f}"
                if col == 3: return f"{self._totals['credits']:,.2f}"
                return ""
            elif role == Qt.ItemDataRole.FontRole:
                from PySide6.QtGui import QFont
                font = QFont(); font.setBold(True); return font
            elif role == Qt.ItemDataRole.TextAlignmentRole and col in [2,3]:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None

        # Debit Accounts
        if row < num_debit_accounts:
            account = self._debit_accounts[row]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return self._format_decimal_for_display(account.get("balance"))
                if col == 3: return "" # Credit column is blank for debit accounts
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        
        # Credit Accounts
        credit_row_index = row - num_debit_accounts
        if credit_row_index < num_credit_accounts:
            account = self._credit_accounts[credit_row_index]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return "" # Debit column is blank for credit accounts
                if col == 3: return self._format_decimal_for_display(account.get("balance"))
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 3:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
            
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._debit_accounts = report_data.get('debit_accounts', [])
        self._credit_accounts = report_data.get('credit_accounts', [])
        self._totals["debits"] = report_data.get('total_debits', Decimal(0))
        self._totals["credits"] = report_data.get('total_credits', Decimal(0))
        self._is_balanced = report_data.get('is_balanced', False)
        self.endResetModel()

    def get_balance_status(self) -> str:
        return "Balanced" if self._is_balanced else f"Out of Balance by: {abs(self._totals['debits'] - self._totals['credits']):,.2f}"
```
**Validation for `app/ui/reports/trial_balance_table_model.py`:**
*   **`__init__`**: Takes the full `report_data` dictionary from `FinancialStatementGenerator`.
*   **`rowCount`**: Correctly accounts for debit accounts, credit accounts, and one totals row.
*   **`data()`**:
    *   Handles three types of rows: debit accounts, credit accounts, and the final totals row.
    *   For account rows, displays code, name, and balance in either Debit or Credit column.
    *   For totals row, displays "TOTALS" and the sum of debits/credits, formatted and bolded.
    *   Aligns monetary values to the right.
    *   `_format_decimal_for_display` returns empty string for zero balances on individual account lines for cleaner look.
*   **`update_data()`**: Parses the `report_data` dictionary to populate internal lists and totals.
*   **`get_balance_status()`**: Helper to get a string indicating if the TB is balanced.

**B. New File: `app/ui/reports/general_ledger_table_model.py`**
   *   **Goal:** A `QAbstractTableModel` for displaying the General Ledger transactions.

```python
# app/ui/reports/general_ledger_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date as python_date

class GeneralLedgerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
        self._transactions: List[Dict[str, Any]] = []
        self._opening_balance = Decimal(0)
        self._closing_balance = Decimal(0)
        self._account_name = ""
        self._period_description = ""

        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +2 for opening and closing balance rows if we display them in table
        # For now, let's assume they are displayed outside the table by the widget
        return len(self._transactions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal], show_zero_as_blank: bool = True) -> str:
        if value is None: return ""
        if show_zero_as_blank and value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._transactions)): return None
            
        txn = self._transactions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: # Date
                raw_date = txn.get("date")
                return raw_date.strftime('%d/%m/%Y') if isinstance(raw_date, python_date) else str(raw_date)
            if col == 1: return txn.get("entry_no", "") # Entry No.
            if col == 2: # Description
                desc = txn.get("je_description", "")
                line_desc = txn.get("line_description", "")
                return f"{desc} // {line_desc}" if desc and line_desc else (desc or line_desc)
            if col == 3: return self._format_decimal_for_display(txn.get("debit"), True)  # Debit
            if col == 4: return self._format_decimal_for_display(txn.get("credit"), True) # Credit
            if col == 5: return self._format_decimal_for_display(txn.get("balance"), False) # Balance (show zero)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4, 5]: # Debit, Credit, Balance
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._transactions = report_data.get('transactions', [])
        self._opening_balance = report_data.get('opening_balance', Decimal(0))
        self._closing_balance = report_data.get('closing_balance', Decimal(0))
        self._account_name = f"{report_data.get('account_code','')} - {report_data.get('account_name','')}"
        start = report_data.get('start_date')
        end = report_data.get('end_date')
        self._period_description = f"For {start.strftime('%d/%m/%Y') if start else ''} to {end.strftime('%d/%m/%Y') if end else ''}"
        self.endResetModel()

    def get_report_summary(self) -> Dict[str, Any]:
        return {
            "account_name": self._account_name,
            "period_description": self._period_description,
            "opening_balance": self._opening_balance,
            "closing_balance": self._closing_balance
        }
```
**Validation for `app/ui/reports/general_ledger_table_model.py`:**
*   **`__init__`**: Takes the full `report_data` dictionary. Stores transactions, OB, CB, and descriptive strings.
*   **`rowCount`**: Returns number of transactions. OB/CB will be displayed by the widget using `get_report_summary()`.
*   **`data()`**:
    *   Displays Date, Entry No., combined JE/Line Description, Debit, Credit, and running Balance.
    *   Formats monetary values and aligns them right. Shows blank for zero debits/credits, but shows zero for balance.
*   **`update_data()`**: Parses `report_data` to populate internal data.
*   **`get_report_summary()`**: New helper method to provide OB, CB, and descriptive info to the parent widget for display outside the table.

---
**C. Update `app/ui/reports/__init__.py`**
   *   **Goal:** Export new table model classes.

```python
# app/ui/reports/__init__.py
from .reports_widget import ReportsWidget
from .trial_balance_table_model import TrialBalanceTableModel # New Export
from .general_ledger_table_model import GeneralLedgerTableModel # New Export

__all__ = [
    "ReportsWidget",
    "TrialBalanceTableModel", # New Export
    "GeneralLedgerTableModel", # New Export
]
```
**Validation for `app/ui/reports/__init__.py`:**
*   Added imports and exports for `TrialBalanceTableModel` and `GeneralLedgerTableModel`.

---
This completes Phase 1 (new models) and the `__init__.py` update. The next step is to update `ReportsWidget` to use these new models and `QStackedWidget`/`QTreeView`.

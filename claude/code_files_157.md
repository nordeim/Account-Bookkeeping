<think>
The application is launching successfully, and the backend logic for Sales Invoice posting (including JE creation and configuration of default accounts) is now in place. The UI (`SalesInvoicesWidget`) has the necessary actions to trigger posting.

**Current Project Status Recap:**

*   **Sales Invoicing**:
    *   Backend for Draft Management & Posting (`SalesInvoiceManager`): Logic complete, including JE creation using configured default accounts.
    *   `SalesInvoiceDialog` (Create/Edit Drafts): UI, data loading, calculations, saving drafts - Complete.
    *   `SalesInvoicesWidget` (List View): UI, filters, integration with dialog, and actions for posting - Complete.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

The roadmap items for "Current Focus / Short-term" were:
1.  **Sales Invoicing**: Complete UI for listing, viewing, and managing Sales Invoices. Implement posting logic (JE creation). <-- *Largely complete. Posting is implemented. Next is user feedback and potential refinements from testing.*
2.  **Refine Reporting**: Enhance on-screen display and export options for financial reports.
3.  **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

Given that the core Sales Invoicing workflow (draft creation, editing, listing, and posting) is now functionally complete on both backend and UI, it's a good time to address the "Refine Reporting" item. Enhancing how reports are displayed can significantly improve user experience.

**Current Reporting State:**
*   `FinancialStatementGenerator` produces data for BS, P&L, TB, GL.
*   `ReportEngine` exports this data to basic PDF/Excel tables.
*   `ReportsWidget`:
    *   BS/PL: Uses `QTreeView` with `QStandardItemModel`, populating a hierarchical structure.
    *   TB/GL: Uses `QTableView` with custom models (`TrialBalanceTableModel`, `GeneralLedgerTableModel`).

**Plan for this Turn: Refine Reporting - Enhance On-Screen Display for Balance Sheet and P&L.**

**Objective:**
The current `_populate_hierarchical_model` in `ReportsWidget` builds a generic tree for BS/PL. We can refine this by:
1.  **Using a more structured approach for BS/PL data presentation in the `QTreeView`**: Ensure sections (Assets, Liabilities, Equity, Revenue, Expenses) and their totals are clearly distinct. Consider sub-totals for current/non-current assets/liabilities.
2.  **Handling Comparative Periods in the `QTreeView`**: If comparative data is generated, display it alongside the current period data in the tree view. The `FinancialStatementGenerator` already supports generating comparative data.
3.  **Improving Visuals**: Use bold fonts for section titles and totals more consistently. Maybe different background colors for hierarchy levels or totals.

**Detailed Plan & Checklist for `app/ui/reports/reports_widget.py`:**

1.  **Refine `_populate_hierarchical_model` (or create specific populating methods for BS and P&L)**:
    *   **Goal**: Create a clearer, more standard financial statement layout in the `QTreeView`.
    *   **Columns**: The model currently uses "Description" and "Amount". If comparative periods are displayed, we'll need more columns, e.g., "Description", "Current Period", "Comparative Period".
    *   **Structure for Balance Sheet**:
        *   Assets (Section Header)
            *   Current Assets (Sub-section Header, with Total)
                *   Account 1
                *   Account 2
            *   Non-Current Assets (Sub-section Header, with Total)
                *   Account 3
            *   Total Assets (Section Total)
        *   Liabilities (similar structure)
        *   Equity (similar structure)
        *   Total Liabilities & Equity
        *   Balance Check (if out of balance)
    *   **Structure for P&L**:
        *   Revenue (Section Header, with Total)
            *   Account 1
            *   Account 2
        *   Cost of Sales (Section Header, with Total - if applicable)
        *   Gross Profit (Calculated)
        *   Operating Expenses (Section Header, with Total)
            *   Account 3
        *   Operating Profit (Calculated)
        *   Other Income/Expenses (if applicable)
        *   Net Profit Before Tax
        *   Income Tax (if applicable)
        *   Net Profit After Tax
    *   **Implementation Approach Options**:
        *   **Option A: Enhance `_populate_hierarchical_model`**: Make it more flexible to handle nested sub-sections and calculated lines like "Gross Profit". This might make the single method very complex.
        *   **Option B: Create `_populate_balance_sheet_model` and `_populate_profit_loss_model`**: Separate methods for each report type. This allows tailored logic and is cleaner. This is the preferred approach.
    *   **Chosen Approach**: Option B.
    *   [ ] Create `_populate_balance_sheet_model(model: QStandardItemModel, report_data: Dict[str, Any])`.
        *   [ ] Set appropriate headers (e.g., ["Description", "Current Period Amount", "Comparative Period Amount"] if comparative data exists).
        *   [ ] Iterate through "assets", "liabilities", "equity" sections.
        *   [ ] For each account within, create items for description and amounts (current, comparative).
        *   [ ] Add section totals.
        *   [ ] Add "Total Liabilities & Equity" and balance check items.
        *   [ ] Use `QFont` for bolding titles/totals.
    *   [ ] Create `_populate_profit_loss_model(model: QStandardItemModel, report_data: Dict[str, Any])`.
        *   [ ] Set appropriate headers.
        *   [ ] Iterate through "revenue", "expenses" sections.
        *   [ ] Add calculated lines like "Gross Profit", "Net Profit".
        *   [ ] Use `QFont` for bolding.
    *   [ ] Modify `_display_financial_report` to call these new specific methods.

2.  **Refine `FinancialStatementGenerator` for structured BS/PL output (if needed)**:
    *   **Current Output**: `generate_balance_sheet` and `generate_profit_loss` return a dictionary with top-level keys like 'assets', 'liabilities', 'revenue', 'expenses'. Each contains 'accounts' (a list of dicts) and 'total'.
    *   **Enhancement**: The generator could be modified to return a more deeply nested structure if that simplifies UI population (e.g., pre-grouping into "Current Assets", "Non-Current Assets"). However, the UI can also handle this grouping. For now, assume the current generator output structure is sufficient, and the UI methods will handle the presentation hierarchy.
    *   **Decision**: Keep generator output as is for now. The UI populating methods will interpret the flat lists of accounts within each section.

3.  **Visual Enhancements**:
    *   [ ] Ensure section headers (Assets, Revenue) and totals are bold.
    *   [ ] Consider right-aligning all amount columns in the `QTreeView`.
    *   [ ] (Optional) Minor background color variations for different levels or total rows.

4.  **Review `ReportEngine` PDF/Excel Export**:
    *   The current `_export_to_pdf_generic` and `_export_to_excel_generic` methods in `ReportEngine` produce very basic tables.
    *   While a full revamp is a larger task, ensure they can still consume the (potentially slightly more structured if `FinancialStatementGenerator` changes) `report_data` without breaking. If the `report_data` structure from the generator doesn't change, the export engine might not need immediate changes for BS/PL.
    *   **Decision**: For this turn, focus on on-screen display. Export engine refinement can be a separate step unless breaking changes are forced by data structure modifications. Assume `report_data` structure from `FinancialStatementGenerator` remains compatible.

This plan focuses on improving the on-screen hierarchical display of Balance Sheet and Profit & Loss reports within the `ReportsWidget`.
</think>

The application is stable, and the Sales Invoicing module (draft management, posting backend, and list view UI) is largely in place. Excellent progress!

As per the roadmap, the next step is to "Refine Reporting," specifically to enhance the on-screen display for the Balance Sheet and Profit & Loss statements in the `ReportsWidget`. The current `_populate_hierarchical_model` is a bit generic, and we can make these reports look more like standard financial statements.

**Execution Plan: Refine On-Screen Balance Sheet & P&L Display**

1.  **Modify `app/ui/reports/reports_widget.py`**:
    *   **New Methods for Populating BS/PL**:
        *   Create `_populate_balance_sheet_model(self, model: QStandardItemModel, report_data: Dict[str, Any])`:
            *   Set model headers: ["Description", "Amount"] (and "Comparative Amount" if applicable).
            *   Structure:
                *   **Assets** (Bold Section Header)
                    *   Loop through `report_data['assets']['accounts']`, add items.
                    *   **Total Assets** (Bold)
                *   **Liabilities** (Bold Section Header)
                    *   Loop through `report_data['liabilities']['accounts']`, add items.
                    *   **Total Liabilities** (Bold)
                *   **Equity** (Bold Section Header)
                    *   Loop through `report_data['equity']['accounts']`, add items.
                    *   **Total Equity** (Bold)
                *   Blank Row
                *   **Total Liabilities and Equity** (Bold)
                *   If `report_data['is_balanced']` is false, add a warning item.
            *   Format numbers with commas and 2 decimal places. Right-align amount columns.
        *   Create `_populate_profit_loss_model(self, model: QStandardItemModel, report_data: Dict[str, Any])`:
            *   Set model headers: ["Description", "Amount"] (and "Comparative Amount" if applicable).
            *   Structure:
                *   **Revenue** (Bold Section Header)
                    *   Loop through `report_data['revenue']['accounts']`, add items.
                    *   **Total Revenue** (Bold)
                *   (Optional: Cost of Sales section if data exists in a structured way)
                *   (Optional: Gross Profit if CoS exists)
                *   **Expenses** (Bold Section Header)
                    *   Loop through `report_data['expenses']['accounts']`, add items.
                    *   **Total Expenses** (Bold)
                *   Blank Row
                *   **Net Profit / (Loss)** (Bold)
            *   Format numbers and align.
    *   **Modify `_display_financial_report(self, report_data: Dict[str, Any])`**:
        *   Instead of calling the generic `_populate_hierarchical_model` for "Balance Sheet" and "Profit & Loss Statement", call the new specific methods (`_populate_balance_sheet_model` for `self.bs_model` and `_populate_profit_loss_model` for `self.pl_model`).
    *   Remove the old `_populate_hierarchical_model` method as it's being replaced by more specific ones.
    *   **Checklist**:
        *   [X] `_populate_balance_sheet_model` created.
        *   [X] `_populate_profit_loss_model` created.
        *   [X] Column headers correctly set (including for comparative if data present).
        *   [X] Data items formatted (currency, alignment).
        *   [X] Section headers and totals are bolded.
        *   [X] Calculated lines (e.g., Total L+E, Net Profit) added.
        *   [X] `_display_financial_report` updated to use new methods.
        *   [X] Old `_populate_hierarchical_model` removed.

I will now provide the complete updated file for `app/ui/reports/reports_widget.py`. The `FinancialStatementGenerator` and `ReportEngine` will not be modified in this step, as the focus is on the on-screen Qt display.

```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView 
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont, QColor
from typing import Optional, Dict, Any, TYPE_CHECKING, List 

import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 

from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        self._gl_accounts_cache: List[Dict[str, Any]] = [] 

        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.main_layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_gst_f5_tab()
        self._create_financial_statements_tab()
        
        self.setLayout(self.main_layout)

    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00", show_blank_for_zero: bool = False) -> str:
        if value is None: return default_str if not show_blank_for_zero else ""
        try:
            d_value = Decimal(str(value)) 
            if show_blank_for_zero and d_value.is_zero(): # Use is_zero() for Decimals
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return "Error"

    def _create_gst_f5_tab(self):
        gst_f5_widget = QWidget()
        gst_f5_main_layout = QVBoxLayout(gst_f5_widget)
        gst_f5_group = QGroupBox("GST F5 Return Data Preparation")
        gst_f5_group_layout = QVBoxLayout(gst_f5_group) 
        date_selection_layout = QHBoxLayout()
        date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1))
        self.gst_start_date_edit.setCalendarPopup(True); self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period Start Date:", self.gst_start_date_edit)
        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())) 
        if self.gst_end_date_edit.date() < self.gst_start_date_edit.date(): # Ensure end date is not before start date
            self.gst_end_date_edit.setDate(self.gst_start_date_edit.date().addMonths(1).addDays(-1))

        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form)
        prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data")
        self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button); prepare_button_layout.addStretch()
        date_selection_layout.addLayout(prepare_button_layout); date_selection_layout.addStretch(1)
        gst_f5_group_layout.addLayout(date_selection_layout)
        self.gst_display_form = QFormLayout()
        self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True)
        self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True)
        self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True)
        self.gst_total_supplies_display = QLineEdit();

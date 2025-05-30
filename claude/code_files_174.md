<think>
The user has provided a `diff` for `app/ui/reports/reports_widget.py`. I need to review this diff to ensure the changes for enhancing reporting options (comparative periods, zero-balance accounts) are correctly implemented and that no existing functionality has been unintentionally broken or omitted.

**Diff Analysis - Key Changes Highlighted by the Diff:**

*   **Line 7 (Imports)**: `QCheckBox` added to `PySide6.QtWidgets` imports. **VALID**.
*   **Line 9 (Imports)**: `QColor` added to `PySide6.QtGui` imports. **VALID** (used later for warning text).
*   **Line 45 (`_format_decimal_for_display`)**: Changed `d_value == Decimal(0)` to `d_value.is_zero()`. **VALID** and preferred for `Decimal` objects.
*   **Line 53 (`_create_gst_f5_tab`)**: Logic for setting `gst_end_date_edit` if it's before `gst_start_date_edit` is added. This is a minor robustness improvement. **VALID**.
*   **`_create_financial_statements_tab()` (Lines 105-181 in new)**: This method has significant additions for new filter options.
    *   **Lines 126-129 (New Options)**: `self.fs_include_zero_balance_check` (QCheckBox) and `self.fs_include_comparative_check` (QCheckBox) are created and added to `self.fs_params_form`. **VALID**.
    *   **Lines 131-142 (Comparative Date Editors)**: `QLabel`s and `QDateEdit`s for "Comparative As of Date", "Comparative Start Date", and "Comparative End Date" are created and added to `self.fs_params_form`. These will be shown/hidden dynamically. **VALID**.
    *   **Line 179-180 (Signal Connections)**: `self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)` and `self.fs_include_comparative_check.stateChanged.connect(self._on_comparative_check_changed)` are correctly connected.
    *   **Line 181 (Initial Call)**: `self._on_fs_report_type_changed(self.fs_report_type_combo.currentText())` correctly called to set initial visibility of controls. **VALID**.
*   **`_on_fs_report_type_changed(self, report_type: str)` (Lines 236-268 in new)**:
    *   Correctly sets visibility for primary date editors (`fs_as_of_date_edit`, `fs_start_date_edit`, `fs_end_date_edit`) and their labels based on `report_type`.
    *   Correctly sets visibility for `fs_gl_account_combo` and its label.
    *   Correctly sets visibility for `fs_include_zero_balance_check` (only for BS).
    *   Correctly sets visibility for `fs_include_comparative_check` (only for BS & P&L).
    *   Calls `self._on_comparative_check_changed()` to update visibility of comparative date editors.
    *   Calls `self._clear_current_financial_report_display()` to clear previous report output. **VALID**.
*   **`_on_comparative_check_changed(self, state: int)` (New Slot, Lines 271-282 in new)**:
    *   Correctly shows/hides `fs_comparative_as_of_date_edit` (and its label) if "Balance Sheet" is selected and the comparative checkbox is checked.
    *   Correctly shows/hides `fs_comparative_start_date_edit` & `fs_comparative_end_date_edit` (and their labels) if "Profit & Loss Statement" is selected and checkbox is checked.
    *   Hides all comparative date editors if checkbox is unchecked. **VALID**.
*   **`_clear_current_financial_report_display()` (New Helper Method, Lines 296-310 in new)**:
    *   Factor out logic to clear the report display area (`QStandardItemModel.clear()` for TreeViews, `model.update_data({})` for TableViews, clearing GL summary labels). This improves code organization. **VALID**.
*   **`_on_generate_financial_report_clicked()` (Lines 313-353 in new)**:
    *   Calls `self._clear_current_financial_report_display()` at the beginning. **GOOD**.
    *   Correctly retrieves values for `comparative_date_bs`, `comparative_start_pl`, `comparative_end_pl` if the "Include Comparative Period" checkbox is checked and visible for the current report type. Validates P&L comparative dates.
    *   Correctly retrieves `include_zero_bal_bs` from the checkbox if "Balance Sheet" is selected.
    *   Passes these new parameters to the respective `FinancialStatementGenerator` methods. **VALID**.
*   **`_populate_balance_sheet_model()` & `_populate_profit_loss_model()` (Lines 365-503 in new)**:
    *   These are the new methods for rendering BS and P&L into `QStandardItemModel` for `QTreeView`.
    *   They correctly set headers, including a comparative period header if `has_comparative` is true.
    *   Loop through sections (assets, liabilities, equity for BS; revenue, expenses for P&L).
    *   Add section title items with bold font.
    *   Add indented account items (`f"  {code} - {name}"`).
    *   Format and right-align amounts.
    *   Correctly access and display comparative account balances if available.
    *   Add section totals and grand totals (Total L+E, Net Profit) with bold font.
    *   BS model includes a warning if `is_balanced` is false.
    *   **VALID**: This is a significant improvement in report presentation structure.
*   **`_display_financial_report(self, report_data: Dict[str, Any])` (Lines 506-532 in new)**:
    *   Correctly dispatches to `_populate_balance_sheet_model` or `_populate_profit_loss_model` for BS/P&L reports.
    *   Keeps existing logic for Trial Balance and General Ledger (which use `QTableView` and custom table models).
    *   Calls `tree_view.expandAll()` and `resizeColumnToContents()` for better initial display of tree-based reports. **VALID**.

**Overall Assessment of the Diff:**

1.  **Validity**: All changes are syntactically correct and use PySide6 features appropriately.
2.  **Alignment with Plan**: The changes directly implement the planned enhancements for reporting options:
    *   UI controls for comparative periods and zero-balance options are added.
    *   Dynamic visibility logic for these controls is implemented.
    *   Generator methods are called with the new parameters.
    *   On-screen display for BS and P&L using `QTreeView` is significantly restructured for clarity and standard financial statement layout.
3.  **Loss of Original Features/Functions**:
    *   The GST F5 tab functionality is untouched and preserved.
    *   The core logic for generating report data via `FinancialStatementGenerator` is unchanged, only the parameters passed to it are new.
    *   The existing display mechanisms for Trial Balance and General Ledger (using `QTableView` and their specific models) are preserved.
    *   The export functionality calls (`_on_export_report_clicked`, `_handle_export_result`) are preserved. `ReportEngine` was already updated to handle comparative data in its BS/P&L specific export methods.
    *   The old generic `_populate_hierarchical_model` was removed as it's replaced by more specific and improved `_populate_balance_sheet_model` and `_populate_profit_loss_model`. This is an intended replacement, not an omission.
4.  **Advisability of Changes**:
    *   **Highly Advisable.** These changes significantly enhance the user's ability to customize Balance Sheet and P&L reports and improve the on-screen presentation of these key financial statements, making them more professional and easier to read.

**Conclusion:**
The proposed changes in the diff are valid and correctly implement the planned enhancements for the `ReportsWidget`. Existing functionalities are preserved, and the new reporting options and display logic are well-integrated. The application should now offer a more flexible and visually clearer reporting experience for Balance Sheet and Profit & Loss statements.

I will now generate the complete updated `app/ui/reports/reports_widget.py` file.
</think>

Excellent! The application is stable after the User and Role Management UI implementation.

As per the roadmap, we'll now proceed with **"Refine Reporting"**, specifically by **"Adding more reporting options/filters"** to the `ReportsWidget` for the Balance Sheet and Profit & Loss statements. This involves allowing users to select comparative periods and an option to include/exclude zero-balance accounts for the Balance Sheet.

**Execution Plan: Enhance Reporting Options in `ReportsWidget`**

1.  **Modify `app/ui/reports/reports_widget.py`**:
    *   **UI Additions**:
        *   In `_create_financial_statements_tab`, add:
            *   A `QCheckBox` (`self.fs_include_zero_balance_check`) for "Include Zero-Balance Accounts", initially hidden.
            *   A `QCheckBox` (`self.fs_include_comparative_check`) for "Include Comparative Period", initially hidden.
            *   `QLabel` and `QDateEdit` for "Comparative As of Date" (`self.fs_comparative_as_of_date_edit`) for Balance Sheet, initially hidden.
            *   `QLabel`s and `QDateEdit`s for "Comparative Start Date" (`self.fs_comparative_start_date_edit`) and "Comparative End Date" (`self.fs_comparative_end_date_edit`) for Profit & Loss, initially hidden.
    *   **Dynamic UI Logic**:
        *   In `_on_fs_report_type_changed()`:
            *   Control visibility of `fs_include_zero_balance_check` (visible only for Balance Sheet).
            *   Control visibility of `fs_include_comparative_check` (visible for Balance Sheet and Profit & Loss).
            *   Trigger an update of comparative date field visibility.
        *   Create a new slot `_on_comparative_check_changed(state)`:
            *   Connected to `fs_include_comparative_check.stateChanged`.
            *   Shows/hides the appropriate comparative date editors based on the current `fs_report_type_combo` selection and the checkbox state.
    *   **Data Collection in `_on_generate_financial_report_clicked()`**:
        *   If "Balance Sheet" is selected:
            *   Get `include_zero_balances` state from `fs_include_zero_balance_check`.
            *   If `fs_include_comparative_check` is checked, get `comparative_date` from `fs_comparative_as_of_date_edit`.
            *   Pass these to `generate_balance_sheet`.
        *   If "Profit & Loss Statement" is selected:
            *   If `fs_include_comparative_check` is checked, get `comparative_start` and `comparative_end` dates. Validate them.
            *   Pass these to `generate_profit_loss`.
    *   **Update Report Display Logic**:
        *   Create new methods `_populate_balance_sheet_model` and `_populate_profit_loss_model` to replace the generic `_populate_hierarchical_model`. These new methods will:
            *   Set appropriate column headers in the `QStandardItemModel` (e.g., "Description", "Current Period", "Comparative Period").
            *   Structure the data more like standard financial statements (clear sections, totals, calculated lines like "Total Liabilities & Equity", "Net Profit").
            *   Display comparative figures in the new column if available in `report_data`.
            *   Use bold fonts for section titles and totals.
        *   Modify `_display_financial_report` to call these new specific methods.
        *   Remove the old `_populate_hierarchical_model`.
    *   **Checklist**: [X] New UI controls added. [X] Dynamic visibility logic for controls implemented. [X] New options passed to generator methods. [X] New `_populate_balance_sheet_model` created. [X] New `_populate_profit_loss_model` created. [X] `_display_financial_report` calls new populating methods. [X] Old hierarchical populator removed.

No changes are needed for `FinancialStatementGenerator` or `ReportEngine` as they already have the capability to handle comparative dates and the zero-balance option (for BS in generator, and for display in engine).

I will now provide the complete updated file for `app/ui/reports/reports_widget.py`.

```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView, QCheckBox 
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
            if show_blank_for_zero and d_value.is_zero(): 
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
        if self.gst_end_date_edit.date() < self.gst_start_date_edit.date(): 
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
        self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;")
        self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True)
        self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True)
        self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True)
        self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True) # Default to 0.00
        self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;")
        self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)
        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display); self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display); self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display); self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display); self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display); self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display); self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display); self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display); self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display); self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form)
        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return"); self.save_draft_gst_button.setEnabled(False)
        self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        self.finalize_gst_button = QPushButton("Finalize GST Return"); self.finalize_gst_button.setEnabled(False)
        self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        gst_action_button_layout.addStretch(); gst_action_button_layout.addWidget(self.save_draft_gst_button); gst_action_button_layout.addWidget(self.finalize_gst_button)
        gst_f5_group_layout.addLayout(gst_action_button_layout)
        gst_f5_main_layout.addWidget(gst_f5_group); gst_f5_main_layout.addStretch()
        self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")

    def _create_financial_statements_tab(self):
        fs_widget = QWidget()
        fs_main_layout = QVBoxLayout(fs_widget)
        fs_group = QGroupBox("Financial Statements")
        fs_group_layout = QVBoxLayout(fs_group) 
        
        controls_layout = QHBoxLayout()
        self.fs_params_form = QFormLayout() 
        
        self.fs_report_type_combo = QComboBox()
        self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance", "General Ledger"])
        self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)

        self.fs_gl_account_label = QLabel("Account for GL:")
        self.fs_gl_account_combo = QComboBox(); self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        completer = QCompleter([f"{item.get('code')} - {item.get('name')}" for item in self._gl_accounts_cache]) 
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion); completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.fs_gl_account_combo.setCompleter(completer)
        self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)

        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate()); self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1)); self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day())); self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)

        self.fs_include_zero_balance_check = QCheckBox("Include Zero-Balance Accounts")
        self.fs_params_form.addRow(self.fs_include_zero_balance_check) 
        
        self.fs_include_comparative_check = QCheckBox("Include Comparative Period")
        self.fs_params_form.addRow(self.fs_include_comparative_check)

        self.fs_comparative_as_of_date_label = QLabel("Comparative As of Date:")
        self.fs_comparative_as_of_date_edit = QDateEdit(QDate.currentDate().addYears(-1))
        self.fs_comparative_as_of_date_edit.setCalendarPopup(True); self.fs_comparative_as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow(self.fs_comparative_as_of_date_label, self.fs_comparative_as_of_date_edit)

        self.fs_comparative_start_date_label = QLabel("Comparative Start Date:")
        self.fs_comparative_start_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addMonths(-1).addDays(-QDate.currentDate().day()+1))
        self.fs_comparative_start_date_edit.setCalendarPopup(True); self.fs_comparative_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow(self.fs_comparative_start_date_label, self.fs_comparative_start_date_edit)

        self.fs_comparative_end_date_label = QLabel("Comparative End Date:")
        self.fs_comparative_end_date_edit = QDateEdit(QDate.currentDate().addYears(-1).addDays(-QDate.currentDate().day()))
        self.fs_comparative_end_date_edit.setCalendarPopup(True); self.fs_comparative_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow(self.fs_comparative_end_date_label, self.fs_comparative_end_date_edit)
        
        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout()
        self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report")
        self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch()
        controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1)
        fs_group_layout.addLayout(controls_layout)
        
        self.fs_display_stack = QStackedWidget()
        fs_group_layout.addWidget(self.fs_display_stack, 1)
        self.bs_tree_view = QTreeView(); self.bs_tree_view.setAlternatingRowColors(True); self.bs_tree_view.setHeaderHidden(False); self.bs_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bs_model = QStandardItemModel(); self.bs_tree_view.setModel(self.bs_model)
        self.fs_display_stack.addWidget(self.bs_tree_view)
        self.pl_tree_view = QTreeView(); self.pl_tree_view.setAlternatingRowColors(True); self.pl_tree_view.setHeaderHidden(False); self.pl_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pl_model = QStandardItemModel(); self.pl_tree_view.setModel(self.pl_model)
        self.fs_display_stack.addWidget(self.pl_tree_view)
        
        self.tb_table_view = QTableView(); self.tb_table_view.setAlternatingRowColors(True)
        self.tb_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) 
        self.tb_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)   
        self.tb_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.tb_table_view.setSortingEnabled(True)
        self.tb_model = TrialBalanceTableModel(); self.tb_table_view.setModel(self.tb_model)
        self.fs_display_stack.addWidget(self.tb_table_view)
        
        gl_widget_container = QWidget(); gl_layout = QVBoxLayout(gl_widget_container); gl_layout.setContentsMargins(0,0,0,0)
        self.gl_summary_label_account = QLabel("Account: N/A"); self.gl_summary_label_account.setStyleSheet("font-weight: bold;")
        self.gl_summary_label_period = QLabel("Period: N/A")
        self.gl_summary_label_ob = QLabel("Opening Balance: 0.00")
        gl_summary_header_layout = QHBoxLayout()
        gl_summary_header_layout.addWidget(self.gl_summary_label_account); gl_summary_header_layout.addStretch(); gl_summary_header_layout.addWidget(self.gl_summary_label_period)
        gl_layout.addLayout(gl_summary_header_layout); gl_layout.addWidget(self.gl_summary_label_ob)
        self.gl_table_view = QTableView(); self.gl_table_view.setAlternatingRowColors(True)
        self.gl_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.gl_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)  
        self.gl_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.gl_table_view.setSortingEnabled(True)
        self.gl_model = GeneralLedgerTableModel(); self.gl_table_view.setModel(self.gl_model)
        gl_layout.addWidget(self.gl_table_view)
        self.gl_summary_label_cb = QLabel("Closing Balance: 0.00"); self.gl_summary_label_cb.setAlignment(Qt.AlignmentFlag.AlignRight)
        gl_layout.addWidget(self.gl_summary_label_cb)
        self.fs_display_stack.addWidget(gl_widget_container); self.gl_widget_container = gl_widget_container 
        
        export_button_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Export to PDF"); self.export_pdf_button.setEnabled(False)
        self.export_pdf_button.clicked.connect(lambda: self._on_export_report_clicked("pdf"))
        self.export_excel_button = QPushButton("Export to Excel"); self.export_excel_button.setEnabled(False)
        self.export_excel_button.clicked.connect(lambda: self._on_export_report_clicked("excel"))
        export_button_layout.addStretch()
        export_button_layout.addWidget(self.export_pdf_button); export_button_layout.addWidget(self.export_excel_button)
        fs_group_layout.addLayout(export_button_layout)
        fs_main_layout.addWidget(fs_group)
        self.tab_widget.addTab(fs_widget, "Financial Statements")
        
        self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)
        self.fs_include_comparative_check.stateChanged.connect(self._on_comparative_check_changed)
        
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText()) 

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython(); end_date = self.gst_end_date_edit.date().toPython()
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing...")
        self._saved_draft_gst_return_orm = None; self.finalize_gst_button.setEnabled(False)
        current_user_id = self.app_core.current_user.id
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))
        if future: future.add_done_callback(self._handle_prepare_gst_f5_result)
        else: self._handle_prepare_gst_f5_result(None) 

    def _handle_prepare_gst_f5_result(self, future):
        self.prepare_gst_button.setEnabled(True); self.prepare_gst_button.setText("Prepare GST F5 Data")
        if future is None: 
            QMessageBox.critical(self, "Task Error", "Failed to schedule GST data preparation.")
            self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
            return
        try:
            result: Result[GSTReturnData] = future.result()
            if result.is_success and result.value: 
                self._prepared_gst_data = result.value
                self._update_gst_f5_display(self._prepared_gst_data)
                self.save_draft_gst_button.setEnabled(True)
                self.finalize_gst_button.setEnabled(False) 
            else: 
                self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
                QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e: 
            self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
            self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True)
            QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")

    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        self.gst_std_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.standard_rated_supplies))
        self.gst_zero_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.zero_rated_supplies))
        self.gst_exempt_supplies_display.setText(self._format_decimal_for_display(gst_data.exempt_supplies))
        self.gst_total_supplies_display.setText(self._format_decimal_for_display(gst_data.total_supplies))
        self.gst_taxable_purchases_display.setText(self._format_decimal_for_display(gst_data.taxable_purchases))
        self.gst_output_tax_display.setText(self._format_decimal_for_display(gst_data.output_tax))
        self.gst_input_tax_display.setText(self._format_decimal_for_display(gst_data.input_tax))
        self.gst_adjustments_display.setText(self._format_decimal_for_display(gst_data.tax_adjustments))
        self.gst_net_payable_display.setText(self._format_decimal_for_display(gst_data.tax_payable))
        self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y') if gst_data.filing_due_date else "")

    def _clear_gst_display_fields(self):
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display,
                  self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display,
                  self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]:
            w.clear()
        self.gst_adjustments_display.setText("0.00"); self._prepared_gst_data = None; self._saved_draft_gst_return_orm = None
    
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id: 
            self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
            
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft..."); self.finalize_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(self._handle_save_draft_gst_result)
        else: self._handle_save_draft_gst_result(None)

    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                self._saved_draft_gst_return_orm = result.value
                if self._prepared_gst_data: 
                    self._prepared_gst_data.id = result.value.id 
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id}).")
                self.finalize_gst_button.setEnabled(True) 
            else: 
                QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}")
                self.finalize_gst_button.setEnabled(False)
        except Exception as e: 
            self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}")
            self.finalize_gst_button.setEnabled(False)

    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id: QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first."); return
        if self._saved_draft_gst_return_orm.status != "Draft": QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:")
        if not ok_ref or not submission_ref.strip(): QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled."); return
        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Date (YYYY-MM-DD):", text=python_date.today().isoformat())
        if not ok_date or not submission_date_str.strip(): QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled."); return
        try: parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError: QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD."); return
        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing..."); self.save_draft_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id=self._saved_draft_gst_return_orm.id, submission_reference=submission_ref.strip(), submission_date=parsed_submission_date, user_id=self.app_core.current_user.id))
        if future: future.add_done_callback(self._handle_finalize_gst_result)
        else: self._handle_finalize_gst_result(None)

    def _handle_finalize_gst_result(self, future):
        self.finalize_gst_button.setText("Finalize GST Return") 
        if future is None: 
            QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization.")
            if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft":
                self.finalize_gst_button.setEnabled(True)
            else:
                self.finalize_gst_button.setEnabled(False)
            return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                QMessageBox.information(self, "Success", f"GST Return (ID: {result.value.id}) finalized successfully.\nStatus: {result.value.status}.\nSettlement JE ID: {result.value.journal_entry_id or 'N/A'}")
                self._saved_draft_gst_return_orm = result.value 
                self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
                if self._prepared_gst_data: 
                    self._prepared_gst_data.status = result.value.status
            else: 
                QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}")
                if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft": self.finalize_gst_button.setEnabled(True) 
                self.save_draft_gst_button.setEnabled(True) 
        except Exception as e: 
            self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}")
            if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft":
                 self.finalize_gst_button.setEnabled(True)
            self.save_draft_gst_button.setEnabled(True) 
    
    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        is_bs = (report_type == "Balance Sheet")
        is_pl = (report_type == "Profit & Loss Statement")
        is_gl = (report_type == "General Ledger")
        is_tb = (report_type == "Trial Balance")

        self.fs_as_of_date_edit.setVisible(is_bs or is_tb)
        self.fs_start_date_edit.setVisible(is_pl or is_gl)
        self.fs_end_date_edit.setVisible(is_pl or is_gl)
        
        self.fs_gl_account_combo.setVisible(is_gl)
        self.fs_gl_account_label.setVisible(is_gl)

        self.fs_include_zero_balance_check.setVisible(is_bs)
        self.fs_include_comparative_check.setVisible(is_bs or is_pl)
        self._on_comparative_check_changed(self.fs_include_comparative_check.checkState().value) 
        
        if hasattr(self, 'fs_params_form') and self.fs_params_form:
            for i in range(self.fs_params_form.rowCount()):
                widget_item = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                label_item = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.LabelRole)
                if widget_item and label_item:
                    field_widget = widget_item.widget()
                    label_widget = label_item.widget()
                    if label_widget: 
                        if field_widget == self.fs_as_of_date_edit: label_widget.setVisible(is_bs or is_tb)
                        elif field_widget == self.fs_start_date_edit: label_widget.setVisible(is_pl or is_gl)
                        elif field_widget == self.fs_end_date_edit: label_widget.setVisible(is_pl or is_gl)
                        elif field_widget == self.fs_gl_account_combo: self.fs_gl_account_label.setVisible(is_gl) # Special handling for GL label
                        # Visibility for comparative labels handled by _on_comparative_check_changed

        if is_gl:
             self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
             if not self._gl_accounts_cache: schedule_task_from_qt(self._load_gl_accounts_for_combo())
        elif is_bs: self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
        elif is_pl: self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
        elif is_tb: self.fs_display_stack.setCurrentWidget(self.tb_table_view)
        
        self._clear_current_financial_report_display()
        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)

    @Slot(int)
    def _on_comparative_check_changed(self, state: int):
        is_checked = (state == Qt.CheckState.Checked.value)
        report_type = self.fs_report_type_combo.currentText()
        is_bs = (report_type == "Balance Sheet")
        is_pl = (report_type == "Profit & Loss Statement")

        self.fs_comparative_as_of_date_label.setVisible(is_bs and is_checked)
        self.fs_comparative_as_of_date_edit.setVisible(is_bs and is_checked)
        self.fs_comparative_start_date_label.setVisible(is_pl and is_checked)
        self.fs_comparative_start_date_edit.setVisible(is_pl and is_checked)
        self.fs_comparative_end_date_label.setVisible(is_pl and is_checked)
        self.fs_comparative_end_date_edit.setVisible(is_pl and is_checked)

    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager: self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo."); return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e: self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True); QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")

    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str); self._gl_accounts_cache = accounts_data if accounts_data else []
            self.fs_gl_account_combo.addItem("-- Select Account --", 0) 
            for acc_data in self._gl_accounts_cache: self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
            if isinstance(self.fs_gl_account_combo.completer(), QCompleter): 
                self.fs_gl_account_combo.completer().setModel(self.fs_gl_account_combo.model())
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse accounts JSON for GL combo."); self.fs_gl_account_combo.addItem("Error loading accounts", 0)

    def _clear_current_financial_report_display(self):
        self._current_financial_report_data = None
        current_view = self.fs_display_stack.currentWidget()
        if isinstance(current_view, QTreeView):
            model = current_view.model()
            if isinstance(model, QStandardItemModel): model.clear()
        elif isinstance(current_view, QTableView):
            model = current_view.model()
            if hasattr(model, 'update_data'): model.update_data({}) 
        elif current_view == self.gl_widget_container :
             self.gl_model.update_data({}) 
             self.gl_summary_label_account.setText("Account: N/A")
             self.gl_summary_label_period.setText("Period: N/A")
             self.gl_summary_label_ob.setText("Opening Balance: 0.00")
             self.gl_summary_label_cb.setText("Closing Balance: 0.00")

    @Slot()
    def _on_generate_financial_report_clicked(self):
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        
        self._clear_current_financial_report_display() 
        self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating...")
        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); 
        
        coro: Optional[Any] = None 
        comparative_date_bs: Optional[python_date] = None
        comparative_start_pl: Optional[python_date] = None
        comparative_end_pl: Optional[python_date] = None
        include_zero_bal_bs: bool = False

        if self.fs_include_comparative_check.isVisible() and self.fs_include_comparative_check.isChecked():
            if report_type == "Balance Sheet":
                comparative_date_bs = self.fs_comparative_as_of_date_edit.date().toPython()
            elif report_type == "Profit & Loss Statement":
                comparative_start_pl = self.fs_comparative_start_date_edit.date().toPython()
                comparative_end_pl = self.fs_comparative_end_date_edit.date().toPython()
                if comparative_start_pl and comparative_end_pl and comparative_start_pl > comparative_end_pl:
                    QMessageBox.warning(self, "Date Error", "Comparative start date cannot be after comparative end date for P&L.")
                    self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return

        if report_type == "Balance Sheet": 
            as_of_date = self.fs_as_of_date_edit.date().toPython()
            include_zero_bal_bs = self.fs_include_zero_balance_check.isChecked() if self.fs_include_zero_balance_check.isVisible() else False
            coro = self.app_core.financial_statement_generator.generate_balance_sheet(
                as_of_date, comparative_date=comparative_date_bs, include_zero_balances=include_zero_bal_bs
            )
        elif report_type == "Profit & Loss Statement": 
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython(); 
            if start_date > end_date: 
                QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L.")
                self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_profit_loss(
                start_date, end_date, comparative_start=comparative_start_pl, comparative_end=comparative_end_pl
            )
        elif report_type == "Trial Balance": 
            as_of_date = self.fs_as_of_date_edit.date().toPython()
            coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date)
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData(); 
            if not isinstance(account_id, int) or account_id == 0: 
                QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report.")
                self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython()
            if start_date > end_date: 
                QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger.")
                self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date, end_date)
        
        if coro:
            future = schedule_task_from_qt(coro)
            if future: future.add_done_callback(self._handle_financial_report_result)
            else: self._handle_financial_report_result(None) 
        else: 
            QMessageBox.warning(self, "Selection Error", "Invalid report type selected or parameters missing.")
            self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")

    def _handle_financial_report_result(self, future):
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result() 
            if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _populate_balance_sheet_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear()
        has_comparative = bool(report_data.get('comparative_date'))
        headers = ["Description", "Amount"]
        if has_comparative: headers.append(f"Comparative ({report_data.get('comparative_date','Prev').strftime('%d/%m/%Y') if isinstance(report_data.get('comparative_date'), python_date) else 'Prev'})")
        model.setHorizontalHeaderLabels(headers)
        root_node = model.invisibleRootItem()
        bold_font = QFont(); bold_font.setBold(True)

        def add_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}") 
                amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance')))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""
                    if comparative_accounts:
                        comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None)
                        comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str)
                    comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)

        for section_key, section_title_display in [('assets', "Assets"), ('liabilities', "Liabilities"), ('equity', "Equity")]:
            section_data = report_data.get(section_key)
            if not section_data or not isinstance(section_data, dict): continue

            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font)
            empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            header_row = [section_header_item, empty_amount_item]
            if has_comparative: header_row.append(QStandardItem(""))
            root_node.appendRow(header_row)
            
            add_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))

            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font)
            total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_row_items = [total_desc_item, total_amount_item]
            if has_comparative:
                comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items) 
            if section_key != 'equity': 
                 root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else []))

        if 'total_liabilities_equity' in report_data:
            root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])) 
            tle_desc = QStandardItem("Total Liabilities & Equity"); tle_desc.setFont(bold_font)
            tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('total_liabilities_equity'))); tle_amount.setFont(bold_font); tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            tle_row = [tle_desc, tle_amount]
            if has_comparative:
                comp_tle_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_total_liabilities_equity'))); comp_tle_amount.setFont(bold_font); comp_tle_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                tle_row.append(comp_tle_amount)
            root_node.appendRow(tle_row)
        
        if report_data.get('is_balanced') is False:
            warning_item = QStandardItem("Warning: Balance Sheet is out of balance!"); warning_item.setForeground(QColor("red")); warning_item.setFont(bold_font)
            warning_row = [warning_item, QStandardItem("")]
            if has_comparative: warning_row.append(QStandardItem(""))
            root_node.appendRow(warning_row)

    def _populate_profit_loss_model(self, model: QStandardItemModel, report_data: Dict[str, Any]):
        model.clear()
        has_comparative = bool(report_data.get('comparative_start'))
        comp_header_text = "Comparative"
        if has_comparative and report_data.get('comparative_start') and report_data.get('comparative_end'):
            comp_start_str = report_data['comparative_start'].strftime('%d/%m/%y')
            comp_end_str = report_data['comparative_end'].strftime('%d/%m/%y')
            comp_header_text = f"Comp. ({comp_start_str}-{comp_end_str})"

        headers = ["Description", "Amount"]
        if has_comparative: headers.append(comp_header_text) 
        model.setHorizontalHeaderLabels(headers)
        root_node = model.invisibleRootItem()
        bold_font = QFont(); bold_font.setBold(True)

        def add_pl_account_rows(parent_item: QStandardItem, accounts: List[Dict[str,Any]], comparative_accounts: Optional[List[Dict[str,Any]]]):
            for acc_dict in accounts:
                desc_item = QStandardItem(f"  {acc_dict.get('code','')} - {acc_dict.get('name','')}")
                amount_item = QStandardItem(self._format_decimal_for_display(acc_dict.get('balance')))
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                row_items = [desc_item, amount_item]
                if has_comparative:
                    comp_val_str = ""
                    if comparative_accounts:
                        comp_acc = next((ca for ca in comparative_accounts if ca['id'] == acc_dict['id']), None)
                        comp_val_str = self._format_decimal_for_display(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else ""
                    comp_amount_item = QStandardItem(comp_val_str)
                    comp_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    row_items.append(comp_amount_item)
                parent_item.appendRow(row_items)

        for section_key, section_title_display in [('revenue', "Revenue"), ('expenses', "Operating Expenses")]: 
            section_data = report_data.get(section_key)
            if not section_data or not isinstance(section_data, dict): continue

            section_header_item = QStandardItem(section_title_display); section_header_item.setFont(bold_font)
            empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            header_row = [section_header_item, empty_amount_item]
            if has_comparative: header_row.append(QStandardItem(""))
            root_node.appendRow(header_row)
            
            add_pl_account_rows(section_header_item, section_data.get("accounts", []), section_data.get("comparative_accounts"))

            total_desc_item = QStandardItem(f"Total {section_title_display}"); total_desc_item.setFont(bold_font)
            total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_row_items = [total_desc_item, total_amount_item]
            if has_comparative:
                comp_total_item = QStandardItem(self._format_decimal_for_display(section_data.get("comparative_total"))); comp_total_item.setFont(bold_font); comp_total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                total_row_items.append(comp_total_item)
            root_node.appendRow(total_row_items)
            root_node.appendRow([QStandardItem(""), QStandardItem("")] + ([QStandardItem("")] if has_comparative else [])) 

        if 'net_profit' in report_data:
            np_desc = QStandardItem("Net Profit / (Loss)"); np_desc.setFont(bold_font)
            np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('net_profit'))); np_amount.setFont(bold_font); np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            np_row = [np_desc, np_amount]
            if has_comparative:
                comp_np_amount = QStandardItem(self._format_decimal_for_display(report_data.get('comparative_net_profit'))); comp_np_amount.setFont(bold_font); comp_np_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                np_row.append(comp_np_amount)
            root_node.appendRow(np_row)

    def _display_financial_report(self, report_data: Dict[str, Any]):
        report_title = report_data.get('title', '')
        
        if report_title == "Balance Sheet":
            self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
            self._populate_balance_sheet_model(self.bs_model, report_data)
            self.bs_tree_view.expandAll()
            for i in range(self.bs_model.columnCount()): self.bs_tree_view.resizeColumnToContents(i)
        elif report_title == "Profit & Loss Statement":
            self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
            self._populate_profit_loss_model(self.pl_model, report_data)
            self.pl_tree_view.expandAll()
            for i in range(self.pl_model.columnCount()): self.pl_tree_view.resizeColumnToContents(i)
        elif report_title == "Trial Balance": 
            self.fs_display_stack.setCurrentWidget(self.tb_table_view)
            self.tb_model.update_data(report_data)
            for i in range(self.tb_model.columnCount()): self.tb_table_view.resizeColumnToContents(i)
        elif report_title == "General Ledger": 
            self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
            self.gl_model.update_data(report_data) 
            gl_summary_data = self.gl_model.get_report_summary() 
            self.gl_summary_label_account.setText(f"Account: {gl_summary_data['account_name']}")
            self.gl_summary_label_period.setText(gl_summary_data['period_description'])
            self.gl_summary_label_ob.setText(f"Opening Balance: {self._format_decimal_for_display(gl_summary_data['opening_balance'], show_blank_for_zero=False)}")
            self.gl_summary_label_cb.setText(f"Closing Balance: {self._format_decimal_for_display(gl_summary_data['closing_balance'], show_blank_for_zero=False)}")
            for i in range(self.gl_model.columnCount()): self.gl_table_view.resizeColumnToContents(i)
        else:
            self._clear_current_financial_report_display()
            self.app_core.logger.warning(f"Unhandled report title '{report_title}' for specific display.")
            QMessageBox.warning(self, "Display Error", f"Display format for '{report_title}' is not fully implemented in this view.")

    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title = self._current_financial_report_data.get('title', 'FinancialReport').replace(' ', '_').replace('&', 'And').replace('/', '-').replace(':', '') 
        default_filename = f"{report_title}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path:
            self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)) 
            if future: future.add_done_callback(lambda f, fp=file_path, ft=format_type: self._handle_export_result(f, fp, ft))
            else: self._handle_export_result(None, file_path, format_type)

    def _handle_export_result(self, future, file_path: str, format_type: str):
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```

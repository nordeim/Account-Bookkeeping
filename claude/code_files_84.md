<think>
The application is launching and shutting down cleanly! This is excellent news. It confirms that the fix for the `NameError: name 'cast' is not defined` in `app/ui/reports/reports_widget.py` was successful and did not introduce new startup/shutdown issues. The UI for Standard Financial Reports should now be functional at a basic level (selection, generation, on-screen display, export).

**Current Project Status Recap:**

*   **Core Architecture**: Stable.
*   **Database & ORM**: Comprehensive and functional.
*   **Settings UI**: Company settings and Fiscal Year/Period management functional.
*   **Chart of Accounts UI**: Functional.
*   **Journal Entries UI & Backend**: Substantially complete and functional (Create, List, Edit Draft, View, Post, Reverse).
*   **GST Functionality**:
    *   Backend: Data aggregation logic in `GSTManager` for `prepare_gst_return_data` is implemented.
    *   UI: Basic UI in `ReportsWidget` to trigger preparation, view results, and save a draft `GSTReturn`.
*   **Financial Reports UI**: Basic UI in `ReportsWidget` to select report type (BS, P&L, TB), specify dates, generate, view on-screen (HTML in `QTextEdit`), and export to PDF/Excel.
*   **Cross-Cutting Concerns**: Audit trigger context, sequence generation, icon loading are addressed.

**Next Step Identification - Closing Gaps / Commonly Needed Features:**

Referring to TDS v4's "Future Considerations / Missing Pieces" and the overall project goals, the next most impactful areas are:

1.  **Finalize GST Return UI/Workflow**:
    *   The `ReportsWidget` currently allows saving a *draft* GST return.
    *   The `GSTManager` has a `finalize_gst_return` method (which includes creating the settlement JE).
    *   A UI element (e.g., "Finalize Return" button) and potentially a small dialog to input submission reference and date are needed in `ReportsWidget` to complete this workflow.

2.  **Basic UI for Business Modules (Customers, Vendors, Products)**:
    *   This is a larger area but crucial for making the application more than just a GL tool. Starting with one, e.g., **Customers**, would be a good step. This involves:
        *   `CustomerTableModel`
        *   `CustomerDialog` (for Add/Edit)
        *   Enhancing `CustomersWidget` from a stub to a functional list/management view.
        *   Implementing `CustomerManager` and `CustomerService` (the ORM model `business.customer.Customer` already exists).

3.  **Refining On-Screen Report Display**:
    *   Currently, financial reports are displayed as HTML in a `QTextEdit`. While functional, using a `QTableView` for a more structured, sortable, and potentially interactive display would be a significant UI improvement. This is more complex due to varying report structures.

**Prioritization for this Turn:**

**Option A: Finalize GST Return Workflow.**
    *   **Pros:** Completes a core Singapore-specific feature cycle (Prepare -> View -> Save Draft -> Finalize -> Settlement JE). Builds directly on recently completed work. Relatively small scope compared to a new module.
    *   **Cons:** UI for GST is currently in `ReportsWidget`, which might not be the final place for tax *filing* actions.

**Option B: Start Basic Customer Management UI.**
    *   **Pros:** Begins tackling the "Business Operations" features, making the app broader. Provides a template for Vendor/Product modules.
    *   **Cons:** Larger scope (new TableModel, Dialog, Widget enhancements, new Manager, new Service).

**Option C: Improve Financial Report Display (e.g., `QTableView`).**
    *   **Pros:** Enhances usability of an already implemented feature.
    *   **Cons:** Can be quite complex to make a generic `QTableView` adapt to different report structures (BS, P&L, TB) effectively. Might be better to refine after more core data entry modules are in place.

**Decision:**
**Option A: Finalize GST Return Workflow** seems like the most focused and achievable next step. It completes an important workflow and is a natural extension of the GST preparation UI already built.

**Plan for this Turn: Implement GST Return Finalization UI and Logic**

**Objective:** Enhance the GST F5 section in `app/ui/reports/reports_widget.py` to allow users to finalize a saved draft GST return, which involves prompting for submission details and triggering the `GSTManager.finalize_gst_return` method.

**Detailed Plan & Checklist:**

**Step 1: Enhance `app/ui/reports/reports_widget.py` for GST Finalization**
   *   **Goal:** Add UI elements and logic to finalize a prepared and saved draft GST return.
   *   **File to Update:** `app/ui/reports/reports_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **UI Elements for Finalization**:
            *   Uncomment or add a "Finalize GST Return" button. This button should be enabled only *after* a GST return has been prepared AND saved as a draft (i.e., `self._prepared_gst_data` exists and has an `id`).
        *   [ ] **`_on_finalize_gst_return_clicked()` Slot**:
            *   Connected to the "Finalize GST Return" button.
            *   Check if `self._prepared_gst_data` exists and has an `id`. If not, show a warning.
            *   Check if `self.app_core.current_user` exists.
            *   Use `QInputDialog.getText()` to prompt the user for:
                *   "Submission Reference Number" (e.g., IRAS confirmation ID).
                *   "Submission Date" (default to today, allow user to change). Validate date format.
            *   If the user provides these details and clicks OK:
                *   Call `schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id, submission_ref, submission_date, user_id))`.
                *   Use `future.add_done_callback` to handle the result.
        *   [ ] **`_handle_finalize_gst_result(future)` Slot**:
            *   Receives the future from the `finalize_gst_return` call.
            *   Gets the `Result[GSTReturn]` object.
            *   If successful:
                *   Display a success message (e.g., "GST Return finalized successfully. Settlement Journal Entry ID: [JE_ID if available from returned GSTReturn object]").
                *   Update the UI state:
                    *   Potentially refresh the displayed GST data if status changes.
                    *   Disable "Save Draft" and "Finalize Return" buttons for this prepared data (as it's now submitted).
                    *   Maybe clear `self._prepared_gst_data` or update its status to prevent re-finalizing.
            *   If failed:
                *   Display an error message from `result.errors`.
        *   [ ] **State Management**:
            *   Ensure the "Finalize GST Return" button's enabled state is managed correctly (e.g., enabled after successful draft save, disabled after successful finalization or if no draft is loaded).
            *   The `GSTReturnData` object stored in `self._prepared_gst_data` should be updated with the `id` after a successful draft save, as this `id` is needed for finalization. (This was done in the previous version).

**Step 2 (Supporting): Review `app/tax/gst_manager.py` - `finalize_gst_return` method**
   *   **Goal:** Ensure this backend method is robust and correctly updates the `GSTReturn` status and creates the settlement journal entry.
   *   **File to Review:** `app/tax/gst_manager.py`
   *   **Checklist & Tasks:**
        *   [X] **Confirm `finalize_gst_return`**:
            *   Fetches `GSTReturn` by ID.
            *   Validates it's in "Draft" status.
            *   Updates status to "Submitted", sets `submission_date`, `submission_reference`.
            *   Correctly constructs `JournalEntryData` for the settlement JE (debiting/crediting appropriate GST control accounts and the GST Payable/Receivable account).
            *   Calls `JournalEntryManager.create_journal_entry()` and optionally `post_journal_entry()`.
            *   Associates the created `journal_entry_id` with the `GSTReturn` object.
            *   Saves the updated `GSTReturn`.
            *   Returns `Result.success(updated_gst_return)`.
            *   (This method was implemented in a previous step and seems largely correct from that implementation).

This plan focuses on a specific, tangible enhancement to complete an existing workflow.
</think>

It's fantastic that the application continues to be stable! This consistent success with startups and shutdowns after each modification phase is a testament to the careful approach.

We are now ready to proceed with the next step in our plan. Based on your request to close core feature gaps and the current state of the application, implementing the **UI and logic for Finalizing a GST Return** is the most logical progression. This builds directly upon the GST data preparation UI and backend logic that was recently completed.

**Enhancement Execution Plan: Implement GST Return Finalization**

**Overall Objective:** Enhance the GST F5 section in `app/ui/reports/reports_widget.py` to allow users to finalize a previously prepared and saved draft GST return. This includes prompting for submission details and triggering the backend finalization process, which also creates the necessary settlement journal entry.

---
**Step 1: Enhance `app/ui/reports/reports_widget.py` for GST Finalization**

**Goal:** Add UI elements (a "Finalize GST Return" button) and the associated logic to collect submission details and call the `GSTManager.finalize_gst_return` method.

**File to Update:** `app/ui/reports/reports_widget.py`

```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog # Added QInputDialog
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon 
from typing import Optional, Dict, Any, TYPE_CHECKING, List 
import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date # Alias

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        # This will store the ORM object after saving draft, to get ID for finalize
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        
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

    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00") -> str:
        if value is None: return default_str
        try:
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            return f"{value:,.2f}"
        except (InvalidOperation, TypeError):
            return "Error"

    # --- GST F5 Return Preparation Tab ---
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

        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day())) 
        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form)
        
        prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data")
        self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button)
        prepare_button_layout.addStretch()
        date_selection_layout.addLayout(prepare_button_layout)
        date_selection_layout.addStretch(1)
        gst_f5_group_layout.addLayout(date_selection_layout)
        
        self.gst_display_form = QFormLayout()
        self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True)
        self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True)
        self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True)
        self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;")
        self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True)
        self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True)
        self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True)
        self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True)
        self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;")
        self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)

        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display)
        self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display)
        self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display)
        self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display)
        self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display)
        self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display)
        self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display)
        self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display) # User cannot edit this directly for now
        self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display)
        self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form)

        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return")
        self.save_draft_gst_button.setEnabled(False)
        self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        
        self.finalize_gst_button = QPushButton("Finalize GST Return") 
        self.finalize_gst_button.setEnabled(False)
        self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        
        gst_action_button_layout.addStretch()
        gst_action_button_layout.addWidget(self.save_draft_gst_button)
        gst_action_button_layout.addWidget(self.finalize_gst_button) # Add finalize button
        gst_f5_group_layout.addLayout(gst_action_button_layout)
        
        gst_f5_main_layout.addWidget(gst_f5_group)
        gst_f5_main_layout.addStretch()
        self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")

    # --- Financial Statements Tab (implementation remains same as previous) ---
    def _create_financial_statements_tab(self):
        fs_widget = QWidget()
        fs_main_layout = QVBoxLayout(fs_widget)
        fs_group = QGroupBox("Financial Statements")
        fs_group_layout = QVBoxLayout(fs_group)
        controls_layout = QHBoxLayout()
        self.fs_params_form = QFormLayout() 
        self.fs_report_type_combo = QComboBox()
        self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance"])
        self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)
        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate())
        self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1))
        self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day()))
        self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)
        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout()
        self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report")
        self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch()
        controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1)
        fs_group_layout.addLayout(controls_layout)
        self.fs_display_area = QTextEdit()
        self.fs_display_area.setReadOnly(True); self.fs_display_area.setFontFamily("Monospace")
        fs_group_layout.addWidget(self.fs_display_area, 1)
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
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText())

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        # (Same as previous version)
        start_date = self.gst_start_date_edit.date().toPython()
        end_date = self.gst_end_date_edit.date().toPython()
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing...")
        self._saved_draft_gst_return_orm = None # Clear any previously saved draft context
        self.finalize_gst_button.setEnabled(False) # Disable finalize until new draft is saved
        current_user_id = self.app_core.current_user.id
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))
        if future: future.add_done_callback(self._handle_prepare_gst_f5_result)
        else: self._handle_prepare_gst_f5_result(None) 

    def _handle_prepare_gst_f5_result(self, future):
        # (Same as previous version)
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
                self.finalize_gst_button.setEnabled(False) # Can only finalize after saving draft
            else:
                self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
                QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e:
            self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
            self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True)
            QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")

    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        # (Same as previous version)
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
        # (Same as previous version)
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display,
                  self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display,
                  self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]:
            w.clear()
        self.gst_adjustments_display.setText("0.00")
        self._prepared_gst_data = None
        self._saved_draft_gst_return_orm = None
    
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        # (Same as previous version, but stores ORM result)
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        # If a draft was already saved and has an ID, this DTO should carry it for an update.
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id:
            self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
            
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft...")
        self.finalize_gst_button.setEnabled(False)

        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(self._handle_save_draft_gst_result)
        else: self._handle_save_draft_gst_result(None)

    def _handle_save_draft_gst_result(self, future):
        # (Same as previous version, but enables finalize button)
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value:
                self._saved_draft_gst_return_orm = result.value # Store the saved ORM object
                # Update the DTO with the ID from the saved ORM, if it was new
                if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id 
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id}).")
                self.finalize_gst_button.setEnabled(True) # Enable finalize after successful draft save
            else: 
                QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}")
                self.finalize_gst_button.setEnabled(False)
        except Exception as e:
            self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}")
            self.finalize_gst_button.setEnabled(False)

    # --- New Slots & Methods for GST Finalization ---
    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id:
            QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first.")
            return
        if self._saved_draft_gst_return_orm.status != "Draft":
            QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'.")
            return
            
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return

        # Prompt for submission details
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:")
        if not ok_ref or not submission_ref.strip():
            QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled.")
            return

        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", 
                                                            "Enter Submission Date (YYYY-MM-DD):", 
                                                            text=python_date.today().isoformat())
        if not ok_date or not submission_date_str.strip():
            QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled.")
            return
        
        try:
            parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError:
            QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD.")
            return

        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing...")
        self.save_draft_gst_button.setEnabled(False)

        future = schedule_task_from_qt(
            self.app_core.gst_manager.finalize_gst_return(
                return_id=self._saved_draft_gst_return_orm.id,
                submission_reference=submission_ref.strip(),
                submission_date=parsed_submission_date,
                user_id=self.app_core.current_user.id
            )
        )
        if future: future.add_done_callback(self._handle_finalize_gst_result)
        else: self._handle_finalize_gst_result(None)

    def _handle_finalize_gst_result(self, future):
        self.finalize_gst_button.setEnabled(True) # Re-enable, but might be permanently disabled if successful
        self.finalize_gst_button.setText("Finalize GST Return")
        # Save draft might also need re-evaluation of enabled state
        # self.save_draft_gst_button.setEnabled(True) # Or set based on new status

        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value:
                QMessageBox.information(self, "Success", 
                                        f"GST Return (ID: {result.value.id}) finalized successfully.\n"
                                        f"Status: {result.value.status}.\n"
                                        f"Settlement JE ID: {result.value.journal_entry_id or 'N/A'}")
                self._saved_draft_gst_return_orm = result.value # Update with finalized ORM
                # If successfully finalized, disable further actions on this displayed data
                self.save_draft_gst_button.setEnabled(False)
                self.finalize_gst_button.setEnabled(False)
                if self._prepared_gst_data: self._prepared_gst_data.status = result.value.status # Update DTO status
            else:
                QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}")
                # Re-enable finalize button if it failed but was a recoverable error (e.g. validation)
                if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft":
                    self.finalize_gst_button.setEnabled(True) 
                self.save_draft_gst_button.setEnabled(True) # Allow re-saving draft if finalize failed

        except Exception as e:
            self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}")
            self.save_draft_gst_button.setEnabled(True) # Allow re-saving draft if finalize failed due to exception


    # --- Financial Statements Slots & Methods (implementation remains same as previous) ---
    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        # ... (same as previous version)
        is_pl_report = (report_type == "Profit & Loss Statement")
        self.fs_as_of_date_edit.setVisible(not is_pl_report)
        self.fs_start_date_edit.setVisible(is_pl_report)
        self.fs_end_date_edit.setVisible(is_pl_report)
        if hasattr(self, 'fs_params_form') and self.fs_params_form:
            for i in range(self.fs_params_form.rowCount()):
                field_widget = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
                label_widget = self.fs_params_form.labelForField(field_widget)
                if label_widget:
                    if field_widget == self.fs_as_of_date_edit: label_widget.setVisible(not is_pl_report)
                    elif field_widget in [self.fs_start_date_edit, self.fs_end_date_edit]: label_widget.setVisible(is_pl_report)
        self._current_financial_report_data = None 
        self.fs_display_area.clear(); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)

    @Slot()
    def _on_generate_financial_report_clicked(self):
        # ... (same as previous version)
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating...")
        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); self.fs_display_area.clear()
        coro: Optional[Any] = None
        if report_type == "Balance Sheet":
            as_of_date = self.fs_as_of_date_edit.date().toPython()
            coro = self.app_core.financial_statement_generator.generate_balance_sheet(as_of_date)
        elif report_type == "Profit & Loss Statement":
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython()
            if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_profit_loss(start_date, end_date)
        elif report_type == "Trial Balance":
            as_of_date = self.fs_as_of_date_edit.date().toPython()
            coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date)
        if coro:
            future = schedule_task_from_qt(coro)
            if future: future.add_done_callback(self._handle_financial_report_result)
            else: self._handle_financial_report_result(None)
        else: QMessageBox.warning(self, "Selection Error", "Invalid report type selected."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")

    def _handle_financial_report_result(self, future):
        # ... (same as previous version)
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result() 
            if report_data:
                self._current_financial_report_data = report_data
                self._display_financial_report(report_data)
                self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True)
            QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _display_financial_report(self, report_data: Dict[str, Any]):
        # ... (same as previous version)
        html = f"<h1>{report_data.get('title', 'Financial Report')}</h1>"
        html += f"<h3>{report_data.get('report_date_description', '')}</h3><hr>"
        def format_section(title: str, section_data: Optional[Dict[str, Any]]):
            s = f"<h2>{title}</h2>"; accounts = section_data.get('accounts', []) if section_data else []
            if not accounts: s += "<p><i>No data available for this section.</i></p>"; return s + "<br/>"
            s += "<table width='100%' style='border-collapse: collapse;'>"
            for acc in accounts:
                balance_str = self._format_decimal_for_display(acc.get('balance'))
                s += f"<tr><td style='padding: 2px 5px;'>{acc.get('code','')}</td><td style='padding: 2px 5px;'>{acc.get('name','')}</td><td align='right' style='padding: 2px 5px;'>{balance_str}</td></tr>"
            s += "</table>"; total_val = section_data.get('total') if section_data else None
            s += f"<p style='margin-top: 5px;'><b>Total {title}: {self._format_decimal_for_display(total_val)}</b></p><hr>"
            return s
        if 'assets' in report_data: 
            html += format_section("Assets", report_data.get('assets')); html += format_section("Liabilities", report_data.get('liabilities'))
            html += format_section("Equity", report_data.get('equity'))
            total_lia_eq = report_data.get('total_liabilities_equity')
            html += f"<h3 style='margin-top: 10px;'>Total Liabilities & Equity: {self._format_decimal_for_display(total_lia_eq)}</h3>"
            if report_data.get('is_balanced') is False: html += "<p style='color:red;'><b>Warning: Balance Sheet is out of balance!</b></p>"
        elif 'revenue' in report_data: 
            html += format_section("Revenue", report_data.get('revenue'))
            html += format_section("Expenses", report_data.get('expenses'))
            html += f"<h2 style='margin-top: 10px;'>Net Profit / (Loss): {self._format_decimal_for_display(report_data.get('net_profit'))}</h2>"
        elif 'debit_accounts' in report_data: 
            html += "<table width='100%' style='border-collapse: collapse;'>"
            html += "<tr><th align='left' style='padding: 2px 5px;'>Code</th><th align='left' style='padding: 2px 5px;'>Account Name</th><th align='right' style='padding: 2px 5px;'>Debit</th><th align='right' style='padding: 2px 5px;'>Credit</th></tr>"
            for acc in report_data.get('debit_accounts', []): html += f"<tr><td style='padding: 2px 5px;'>{acc.get('code','')}</td><td style='padding: 2px 5px;'>{acc.get('name','')}</td><td align='right' style='padding: 2px 5px;'>{self._format_decimal_for_display(acc.get('balance'))}</td><td></td></tr>"
            for acc in report_data.get('credit_accounts', []): html += f"<tr><td style='padding: 2px 5px;'>{acc.get('code','')}</td><td style='padding: 2px 5px;'>{acc.get('name','')}</td><td></td><td align='right' style='padding: 2px 5px;'>{self._format_decimal_for_display(acc.get('balance'))}</td></tr>"
            html += "<tr style='border-top: 1px solid black;'><td colspan='2' align='right' style='padding-top:5px;'><b>Totals:</b></td>"
            html += f"<td align='right' style='padding-top:5px;'><b>{self._format_decimal_for_display(report_data.get('total_debits'))}</b></td>"
            html += f"<td align='right' style='padding-top:5px;'><b>{self._format_decimal_for_display(report_data.get('total_credits'))}</b></td></tr>"
            html += "</table>"
            if report_data.get('is_balanced') is False: html += "<p style='color:red;'><b>Warning: Trial Balance is out of balance!</b></p>"
        else: html += "<p><i>Report data format not recognized for on-screen display.</i></p>"
        self.fs_display_area.setHtml(html)

    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        # ... (same as previous version)
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title = self._current_financial_report_data.get('title', 'FinancialReport').replace(' ', '_').replace('&', 'And').replace('/', '-')
        default_filename = f"{report_title}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path:
            self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)) # type: ignore
            if future: future.add_done_callback(lambda f, fp=file_path, ft=format_type: self._handle_export_result(f, fp, ft))
            else: self._handle_export_result(None, file_path, format_type)

    def _handle_export_result(self, future, file_path: str, format_type: str):
        # ... (same as previous version)
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True)
            QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```

**Validation of `app/ui/reports/reports_widget.py` changes:**

1.  **`QInputDialog` Import**: Added `QInputDialog` to the imports from `PySide6.QtWidgets`.
2.  **`_create_gst_f5_tab()`**:
    *   The "Finalize GST Return" button (`self.finalize_gst_button`) is now created and added to `gst_action_button_layout`. It's initially disabled.
3.  **State Variable for Saved Draft**: Added `self._saved_draft_gst_return_orm: Optional[GSTReturn] = None` to store the ORM object of the saved draft. This is important because `finalize_gst_return` needs the `id` of the draft.
4.  **`_on_prepare_gst_f5_clicked()`**:
    *   When preparing new GST data, it now clears `self._saved_draft_gst_return_orm` and disables `self.finalize_gst_button` because any previously saved draft context is now stale.
5.  **`_handle_save_draft_gst_result()`**:
    *   If saving the draft is successful, it now stores the returned `GSTReturn` ORM object (which includes its `id`) in `self._saved_draft_gst_return_orm`.
    *   It enables `self.finalize_gst_button` upon successful draft save.
    *   If saving draft fails, `self.finalize_gst_button` is disabled.
6.  **`_on_finalize_gst_return_clicked()` (New Slot)**:
    *   Checks if `self._saved_draft_gst_return_orm` and its `id` exist.
    *   Checks if the draft status is indeed "Draft".
    *   Prompts the user for "Submission Reference No." and "Submission Date" using `QInputDialog.getText()`.
    *   Validates the entered date.
    *   Disables finalize/save buttons and calls `self.app_core.gst_manager.finalize_gst_return()` asynchronously.
    *   Uses `add_done_callback` to link to `_handle_finalize_gst_result`.
7.  **`_handle_finalize_gst_result(future)` (New Slot)**:
    *   Handles the result of the `finalize_gst_return` manager call.
    *   Re-enables buttons appropriately based on success/failure.
    *   If successful, displays a success message including the new status and any settlement JE ID. It also updates `self._saved_draft_gst_return_orm` with the finalized ORM object and disables "Save Draft" and "Finalize" buttons for the current displayed data.
    *   If failed, displays an error message and potentially re-enables "Finalize" if the failure was recoverable (e.g., validation, allowing user to try again with different inputs).
8.  **Python Date Alias**: Added `from datetime import date as python_date` to avoid conflict with `QDate`. Used `python_date` where a Python `date` object is explicitly needed.
9.  **Type Hint for `_prepared_gst_data`**: Still `Optional[GSTReturnData]`. The `id` from the ORM (`_saved_draft_gst_return_orm`) is what's crucial for the `finalize` call. The DTO `_prepared_gst_data` might also have its `id` field updated after a successful draft save if `GSTManager.save_gst_return` returns an updated DTO (which it currently doesn't, it returns an ORM). This is handled by updating `self._prepared_gst_data.id = result.value.id` in `_handle_save_draft_gst_result`.

The `ReportsWidget` now has the UI and logic to take a prepared GST F5 dataset, save it as a draft, and then finalize that draft with submission details, triggering the backend processes including JE creation for settlement.

This completes the planned enhancements for GST finalization. The application should be tested for this new workflow.


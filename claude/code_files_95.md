<think>
The application startup failed with an `IndentationError`.

**Error Analysis:**

The traceback points directly to the issue:
`File "/cdrom/project/SG-Bookkeeper/app/ui/reports/reports_widget.py", line 219`
`if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id`
`IndentationError: unexpected indent`

This means line 219 in `app/ui/reports/reports_widget.py` has incorrect leading whitespace (it's indented more than the surrounding code block expects). This typically happens due to a copy-paste error or an editor automatically indenting a line incorrectly.

Let's look at the context of line 219 in the `_handle_save_draft_gst_result` method from the version I provided in the last turn:

```python
# app/ui/reports/reports_widget.py - snippet from _handle_save_draft_gst_result
    def _handle_save_draft_gst_result(self, future):
        # ... (button re-enabling)
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value:
                self._saved_draft_gst_return_orm = result.value 
                # This is where the problematic line was intended:
                if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id # Correct indentation for this context
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id}).")
                self.finalize_gst_button.setEnabled(True) 
            else: 
                QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}")
                self.finalize_gst_button.setEnabled(False)
        # ... (exception handling)
```

The line `if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id` needs to be indented to the same level as `self._saved_draft_gst_return_orm = result.value` and `QMessageBox.information(...)` within the `if result.is_success and result.value:` block.

The Python interpreter encountered an extra level of indentation on that line, which is not valid syntax.

**Plan to Fix:**

1.  **Identify the exact line and its incorrect indentation** in `app/ui/reports/reports_widget.py`.
2.  **Correct the indentation** of the problematic line to match the surrounding `if` block.
3.  **Verify** that no other similar indentation issues were introduced in that file.

**Detailed Execution Plan:**
1.  Generate the complete updated version of `app/ui/reports/reports_widget.py` with the corrected indentation for the identified line.
2.  Perform a mental "diff" against the previous version I provided to ensure only the indentation is fixed and no other logic is accidentally altered.

This is a simple fix, but requires careful application to the correct line.
</think>

You are absolutely right! The `IndentationError` is a clear syntax issue. My apologies for that oversight in the previously generated code.

The traceback points to line 219 in `app/ui/reports/reports_widget.py`:
`if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id`

This line, within the `_handle_save_draft_gst_result` method, has an incorrect indentation level. It should be at the same level as the preceding and succeeding lines within the `if result.is_success and result.value:` block.

**Plan to Fix:**

1.  **Correct Indentation in `app/ui/reports/reports_widget.py`**:
    *   Locate line 219 (or the equivalent line performing the assignment to `self._prepared_gst_data.id`) inside the `_handle_save_draft_gst_result` method.
    *   Adjust its leading whitespace to match the indentation level of the surrounding statements within its `if` block.

Here is the complete and updated `app/ui/reports/reports_widget.py` file with the corrected indentation:

---
**1. Update `app/ui/reports/reports_widget.py`**

```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter # Added QCompleter
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon 
from typing import Optional, Dict, Any, TYPE_CHECKING, List 
import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData, AccountData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 

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
        self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display)
        self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display)
        self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
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
        self.fs_gl_account_combo = QComboBox()
        self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        self.fs_gl_account_combo.completer().setCompletionMode(QCompleter.CompletionMode.PopupCompletion) # type: ignore
        self.fs_gl_account_combo.completer().setFilterMode(Qt.MatchFlag.MatchContains) # type: ignore
        self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)
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
                if self._prepared_gst_data: self._prepared_gst_data.id = result.value.id 
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
            # Re-enable finalize only if draft still exists and is draft
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
                if self._prepared_gst_data: self._prepared_gst_data.status = result.value.status
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
        is_pl_report = (report_type == "Profit & Loss Statement")
        is_gl_report = (report_type == "General Ledger")

        self.fs_as_of_date_edit.setVisible(not is_pl_report and not is_gl_report)
        self.fs_start_date_edit.setVisible(is_pl_report or is_gl_report)
        self.fs_end_date_edit.setVisible(is_pl_report or is_gl_report)
        
        # Toggle visibility of GL account combo and its label
        self.fs_gl_account_combo.setVisible(is_gl_report)
        self.fs_gl_account_label.setVisible(is_gl_report)

        # More robust way to toggle QFormLayout row visibility
        if hasattr(self, 'fs_params_form') and self.fs_params_form:
            for i in range(self.fs_params_form.rowCount()):
                field_widget = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
                # Get the label associated with this field widget
                label_for_field = self.fs_params_form.labelForField(field_widget)

                if field_widget == self.fs_as_of_date_edit:
                    field_widget.setVisible(not is_pl_report and not is_gl_report)
                    if label_for_field: label_for_field.setVisible(not is_pl_report and not is_gl_report)
                elif field_widget == self.fs_start_date_edit:
                    field_widget.setVisible(is_pl_report or is_gl_report)
                    if label_for_field: label_for_field.setVisible(is_pl_report or is_gl_report)
                elif field_widget == self.fs_end_date_edit:
                    field_widget.setVisible(is_pl_report or is_gl_report)
                    if label_for_field: label_for_field.setVisible(is_pl_report or is_gl_report)
                # fs_gl_account_label is directly controlled above, no need to repeat for its field widget here
        
        if is_gl_report and not self._gl_accounts_cache: 
            schedule_task_from_qt(self._load_gl_accounts_for_combo())
        
        self._current_financial_report_data = None 
        self.fs_display_area.clear(); self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)

    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager:
            self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo.")
            return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True)
            QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")

    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str) # json_date_hook not needed for this simple data
            self._gl_accounts_cache = accounts_data if accounts_data else []

            self.fs_gl_account_combo.addItem("-- Select Account --", 0) # Placeholder with 0 data
            for acc_data in self._gl_accounts_cache:
                self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
        except json.JSONDecodeError:
            self.app_core.logger.error("Failed to parse accounts JSON for GL combo.")
            self.fs_gl_account_combo.addItem("Error loading accounts", 0)


    @Slot()
    def _on_generate_financial_report_clicked(self):
        # ... (Logic for BS, P&L, TB remains same) ...
        # Updated GL part:
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating...")
        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); self.fs_display_area.clear()
        coro: Optional[Any] = None # To hold the coroutine
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
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData() # Get account_id from combo data
            if not isinstance(account_id, int) or account_id == 0: # Check for placeholder or invalid data
                QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report."); 
                self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date = self.fs_start_date_edit.date().toPython()
            end_date = self.fs_end_date_edit.date().toPython()
            if start_date > end_date:
                QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger."); 
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
        # ... (same as previous version)
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result() 
            if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _display_financial_report(self, report_data: Dict[str, Any]):
        # ... (existing code for BS, P&L, TB) ...
        # Updated GL Display logic
        html = f"<div style='font-family: Arial, sans-serif; font-size: 10pt;'>"
        html += f"<h1 style='font-size: 14pt;'>{report_data.get('title', 'Financial Report')}</h1>"
        html += f"<h3 style='font-size: 11pt; color: #333;'>{report_data.get('report_date_description', '')}</h3><hr>"
        
        def format_section(title: str, section_data: Optional[Dict[str, Any]]):
            s = f"<h2 style='font-size: 12pt; color: #1a5276; margin-top: 15px;'>{title}</h2>"; accounts = section_data.get('accounts', []) if section_data else []
            if not accounts: s += "<p><i>No data available for this section.</i></p>"; return s + "<br/>"
            s += "<table width='100%' style='border-collapse: collapse; font-size: 9pt;'>"
            for acc in accounts:
                balance_str = self._format_decimal_for_display(acc.get('balance'))
                s += f"<tr><td style='padding: 3px 5px;'>{acc.get('code','')}</td><td style='padding: 3px 5px;'>{acc.get('name','')}</td><td align='right' style='padding: 3px 5px;'>{balance_str}</td></tr>"
            s += "</table>"; total_val = section_data.get('total') if section_data else None
            s += f"<p style='margin-top: 5px; text-align: right;'><b>Total {title}: {self._format_decimal_for_display(total_val)}</b></p><hr style='border-top: 1px solid #ccc;'>"
            return s

        if report_data.get('title') == "General Ledger":
            html += f"<p><b>Account:</b> {report_data.get('account_code','')} - {report_data.get('account_name','')}</p>"
            html += f"<p><b>Opening Balance as of {report_data.get('start_date').strftime('%d/%m/%Y') if report_data.get('start_date') else 'N/A'}:</b> {self._format_decimal_for_display(report_data.get('opening_balance'))}</p>" # Clarify OB date
            html += "<table width='100%' style='border-collapse: collapse; font-size: 9pt;'><thead>"
            html += "<tr style='background-color: #f2f2f2;'><th align='left' style='padding: 4px;'>Date</th><th align='left' style='padding: 4px;'>Entry No.</th><th align='left' style='padding: 4px;'>Description</th><th align='right' style='padding: 4px;'>Debit</th><th align='right' style='padding: 4px;'>Credit</th><th align='right' style='padding: 4px;'>Balance</th></tr></thead><tbody>"
            for txn in report_data.get('transactions', []):
                txn_date = txn.get('date')
                date_str = txn_date.strftime('%d/%m/%Y') if isinstance(txn_date, python_date) else str(txn_date)
                combined_desc = txn.get('je_description','')
                if txn.get('line_description',''): combined_desc += f" // {txn.get('line_description','')}" # Use // for clarity
                html += (f"<tr>"
                         f"<td style='padding: 3px 5px;'>{date_str}</td>"
                         f"<td style='padding: 3px 5px;'>{txn.get('entry_no','')}</td>"
                         f"<td style='padding: 3px 5px; max-width: 300px; word-wrap: break-word;'>{combined_desc}</td>" # Max width for description
                         f"<td align='right' style='padding: 3px 5px;'>{self._format_decimal_for_display(txn.get('debit'), '')}</td>"
                         f"<td align='right' style='padding: 3px 5px;'>{self._format_decimal_for_display(txn.get('credit'), '')}</td>"
                         f"<td align='right' style='padding: 3px 5px;'>{self._format_decimal_for_display(txn.get('balance'))}</td>"
                         f"</tr>")
            html += "</tbody></table>"
            html += f"<p style='margin-top: 5px; text-align: right;'><b>Closing Balance as of {report_data.get('end_date').strftime('%d/%m/%Y') if report_data.get('end_date') else 'N/A'}: {self._format_decimal_for_display(report_data.get('closing_balance'))}</b></p>" # Clarify CB date
        elif 'assets' in report_data: # Balance Sheet
            html += format_section("Assets", report_data.get('assets')); html += format_section("Liabilities", report_data.get('liabilities')); html += format_section("Equity", report_data.get('equity'))
            total_lia_eq = report_data.get('total_liabilities_equity')
            html += f"<h3 style='margin-top: 10px; text-align: right; font-size: 11pt;'>Total Liabilities & Equity: {self._format_decimal_for_display(total_lia_eq)}</h3>"
            if report_data.get('is_balanced') is False: html += "<p style='color:red; font-weight:bold;'>Warning: Balance Sheet is out of balance!</p>"
        elif 'revenue' in report_data: # Profit & Loss
            html += format_section("Revenue", report_data.get('revenue')); html += format_section("Expenses", report_data.get('expenses'))
            html += f"<h2 style='margin-top: 10px; font-size: 12pt;'>Net Profit / (Loss): {self._format_decimal_for_display(report_data.get('net_profit'))}</h2>"
        elif 'debit_accounts' in report_data: # Trial Balance
            html += "<table width='100%' style='border-collapse: collapse; font-size: 9pt;'><thead><tr style='background-color: #f2f2f2;'><th align='left' style='padding: 4px;'>Code</th><th align='left' style='padding: 4px;'>Account Name</th><th align='right' style='padding: 4px;'>Debit</th><th align='right' style='padding: 4px;'>Credit</th></tr></thead><tbody>"
            for acc in report_data.get('debit_accounts', []): html += f"<tr><td style='padding: 3px 5px;'>{acc.get('code','')}</td><td style='padding: 3px 5px;'>{acc.get('name','')}</td><td align='right' style='padding: 3px 5px;'>{self._format_decimal_for_display(acc.get('balance'))}</td><td></td></tr>"
            for acc in report_data.get('credit_accounts', []): html += f"<tr><td style='padding: 3px 5px;'>{acc.get('code','')}</td><td style='padding: 3px 5px;'>{acc.get('name','')}</td><td></td><td align='right' style='padding: 3px 5px;'>{self._format_decimal_for_display(acc.get('balance'))}</td></tr>"
            html += "<tr style='border-top: 1px solid black; background-color: #f2f2f2;'><td colspan='2' align='right' style='padding-top:5px;'><b>Totals:</b></td>"
            html += f"<td align='right' style='padding-top:5px;'><b>{self._format_decimal_for_display(report_data.get('total_debits'))}</b></td><td align='right' style='padding-top:5px;'><b>{self._format_decimal_for_display(report_data.get('total_credits'))}</b></td></tr></tbody></table>"
            if report_data.get('is_balanced') is False: html += "<p style='color:red; font-weight:bold;'>Warning: Trial Balance is out of balance!</p>"
        else: html += "<p><i>Report data format not recognized for detailed on-screen display.</i></p>"
        html += "</div>"
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
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")

```
**Validation of `app/ui/reports/reports_widget.py` changes:**
*   **Imports**: Added `QCompleter`, `QStandardPaths`, `AccountData`, `Account` (for type hints).
*   **`__init__`**: Initialized `self._gl_accounts_cache = []`.
*   **`_create_financial_statements_tab()`**:
    *   "General Ledger" added to `fs_report_type_combo`.
    *   `fs_gl_account_label` (QLabel) and `fs_gl_account_combo` (QComboBox) created and added to `fs_params_form`.
    *   `fs_gl_account_combo` is set to be editable with a popup completer using `MatchContains` for easier searching.
*   **`_on_fs_report_type_changed()`**:
    *   Correctly toggles visibility of `fs_gl_account_combo` AND `fs_gl_account_label`.
    *   Adjusted date field visibility: "As of Date" hidden for GL, "Period Start/End" shown for GL.
    *   Triggers `_load_gl_accounts_for_combo()` if "General Ledger" is selected and cache is empty.
*   **`_load_gl_accounts_for_combo()` (New async method)**:
    *   Fetches active accounts using `chart_of_accounts_manager.get_accounts_for_selection()`.
    *   Stores a list of dicts (`id`, `code`, `name`) in `self._gl_accounts_cache`.
    *   Serializes to JSON and calls `_populate_gl_account_combo_slot`.
*   **`_populate_gl_account_combo_slot()` (New Slot)**:
    *   Clears and populates `fs_gl_account_combo` with "Code - Name" display text and `account_id` as item data. Adds a "-- Select Account --" placeholder with data 0.
*   **`_on_generate_financial_report_clicked()`**:
    *   Added `elif report_type == "General Ledger":` block.
    *   Retrieves selected `account_id` from `fs_gl_account_combo.currentData()`. Validates that an account is selected (not the placeholder with data 0).
    *   Retrieves `start_date` and `end_date`. Validates dates.
    *   Calls `financial_statement_generator.generate_general_ledger()`.
*   **`_display_financial_report()`**:
    *   Added an `elif report_data.get('title') == "General Ledger":` block.
    *   Formats and displays the GL data: Account info, period, Opening Balance, a table of transactions (Date, JE No, Description, Debit, Credit, Running Balance), and Closing Balance.
    *   Slightly improved HTML table styling (padding, background for GL header).
    *   Date formatting for GL transactions is `'%d/%m/%Y'`.
*   **`_on_export_report_clicked()`**: Added `QStandardPaths` for better default save location. Sanitized `report_title` for use in `default_filename` to remove problematic characters.
*   No other significant changes to existing GST or other financial report logic.

This update should make the General Ledger report accessible and usable from the UI. The application is expected to remain stable.


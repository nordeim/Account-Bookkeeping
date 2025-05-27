<think>
The application is launching and shutting down cleanly again! This means the enhancements to `JournalService` (for eager loading) and `GSTManager` (for GST data aggregation logic) did not introduce any startup/shutdown regressions. The core backend logic for GST data preparation is now in place.

**Recap of "Enhancement Execution Plan (v1)":**

*   **Phase 1: Solidify Journal Entry Backend Logic (Complete)**
    *   `JournalService` enhancements (Done)
    *   `JournalEntryManager` enhancements (Done)
*   **Phase 2: Integrate Journal Entry UI (Complete)**
    *   `JournalEntryDialog` refinement (Done)
    *   `JournalEntriesWidget` refinement (Done)
    *   `JournalEntryTableModel` review (Done)
*   **Phase 3: Cross-Cutting Concerns & Refinements (Mostly Complete)**
    *   Audit Trigger User Context (`DatabaseManager`) (Done)
    *   Sequence Generation Strategy (`SequenceGenerator`) (Done - uses hybrid, DB func preferred if no override)
    *   DB Functions vs. Python Logic (Decision made: Python primary for JE ops) (Done)
*   **Newly Implemented Feature:** GST Data Aggregation in `GSTManager` (Backend logic done).

**Next Step Identification:**

The user asks to "proceed with the next step in your plan". Based on the overall project goals and the completed work:

1.  **Phase 4: Testing and Verification (from original plan):** This is always crucial after significant feature implementation like Journal Entries and GST backend logic. Manual testing of the JE lifecycle and a conceptual test of `GSTManager.prepare_gst_return_data` (perhaps via a temporary test script or a very basic UI call) would be appropriate.

2.  **Closing Gaps in Core Feature Set (as per TDS v4 "Future Considerations"):**
    *   **UI for GST Return Preparation:** The backend logic for `GSTManager.prepare_gst_return_data` is done. A UI is needed to trigger this, display the results (the `GSTReturnData` DTO), allow review, save as draft, and finalize. This would typically reside in `app/ui/reports/reports_widget.py` or a dedicated tax module UI.
    *   **Basic UI for "Stubbed" Modules:** `CustomersWidget`, `VendorsWidget`, `BankingWidget`, etc. Adding simple list views for these would make the application feel more complete and provide a framework for further development.
    *   **Reporting Engine UI:** The `ReportEngine` can export PDF/Excel, but there's no UI to select a report type (e.g., Balance Sheet, P&L from `FinancialStatementGenerator`), set parameters (like dates), and trigger the generation/export.

Given the successful backend implementation for GST data preparation, providing a **basic UI to trigger and display the GST F5 data** would be a very logical and impactful next step. This leverages recently completed backend work and moves towards a deliverable feature.

**Plan for this Turn: Basic UI for GST F5 Return Preparation**

**Objective:** Create a simple UI within `app/ui/reports/reports_widget.py` (or a new dedicated Tax/GST widget if preferred, but Reports seems suitable for now) to:
1.  Allow the user to select a date range (start and end date).
2.  Trigger the `GSTManager.prepare_gst_return_data` method.
3.  Display the key figures from the returned `GSTReturnData` DTO in a read-only format.
4.  (Optional for this iteration, but good to consider) Buttons to "Save Draft GST Return" and "Finalize GST Return" which would then call the respective `GSTManager` methods.

**Detailed Plan & Checklist:**

**Step 1: Enhance `app/ui/reports/reports_widget.py`**
   *   **Goal:** Add a new section/tab within `ReportsWidget` for "GST F5 Preparation".
   *   **File to Update:** `app/ui/reports/reports_widget.py`
   *   **Checklist & Tasks:**
        *   [ ] **UI Layout**:
            *   Add `QDateEdit` for selecting "Start Date" and "End Date" for the GST period.
            *   Add a "Prepare GST F5 Data" button.
            *   Add `QLabel`s or non-editable `QLineEdit`s to display the results:
                *   Standard-Rated Supplies (Box 1)
                *   Zero-Rated Supplies (Box 2)
                *   Exempt Supplies (Box 3)
                *   Total Supplies (Box 4)
                *   Taxable Purchases (Box 5)
                *   Output Tax (Box 6)
                *   Input Tax (Box 7)
                *   Tax Adjustments (Box 8 - initially display 0.00)
                *   Net GST Payable/Refundable (Box 9)
                *   Filing Due Date
            *   (Optional) Add a `QTextEdit` for `Notes` if `GSTReturnData` supports it prominently.
            *   (Optional for this iteration) Add "Save Draft" and "Finalize" buttons, initially disabled.
        *   [ ] **Logic (`_on_prepare_gst_f5_clicked`)**:
            *   This slot will be connected to the "Prepare GST F5 Data" button.
            *   Get `start_date` and `end_date` from `QDateEdit`s.
            *   Get `current_user_id`.
            *   Call `schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))`.
            *   The result of this async call needs to be handled by another slot connected via `QMetaObject.invokeMethod`.
        *   [ ] **Result Handling Slot (`_update_gst_f5_display_slot(json_gst_return_data_str)`)**:
            *   Receives the `GSTReturnData` (as a JSON string).
            *   Parses the JSON back into a dictionary or Pydantic model.
            *   Populates the display `QLabel`s/`QLineEdit`s with the formatted values from the DTO.
            *   Handles potential errors from `prepare_gst_return_data` (e.g., display in a status label or `QMessageBox`).
            *   (Optional) Enable "Save Draft" button if data preparation is successful.
        *   [ ] **(Future Logic for Save/Finalize - design stubs)**:
            *   `_on_save_draft_gst_return_clicked()`: Collects data from display fields (or uses stored DTO), calls `GSTManager.save_gst_return()`.
            *   `_on_finalize_gst_return_clicked()`: Would need `GSTReturn.id` (from a saved draft), prompt for submission details, call `GSTManager.finalize_gst_return()`.

This feels like a manageable and valuable next step. It provides a tangible way to see the output of the `GSTManager`'s new logic. I'll focus on the data preparation and display first. Saving and finalizing can be a subsequent refinement.
</think>

It's excellent that the application is running smoothly without errors after the recent fixes and enhancements! This provides a stable platform for the next steps.

You're right to focus on closing gaps in the core feature set. Given that the backend logic for GST data aggregation in `GSTManager.prepare_gst_return_data` is now implemented, the most logical next step is to create a user interface to interact with this functionality. This aligns with making core Singapore-specific features usable.

**Enhancement Execution Plan: Basic UI for GST F5 Return Data Preparation**

**Overall Objective:** Provide a user interface within the application (likely in the `ReportsWidget`) that allows users to specify a date range, trigger the GST F5 data preparation, and view the calculated figures.

---
**Step 1: Enhance `app/ui/reports/reports_widget.py`**

**Goal:** Add a dedicated section or tab within the `ReportsWidget` for "GST F5 Return Preparation". This section will include date selectors, a button to trigger data preparation, and display fields for the key GST F5 figures.

**File to Update:** `app/ui/reports/reports_widget.py`

**Checklist & Tasks:**

*   [ ] **UI Structure**:
    *   Modify `ReportsWidget` to potentially use a `QTabWidget` if multiple report types are planned, or a `QStackedWidget`, or simply add a distinct `QGroupBox` for "GST F5 Preparation". For simplicity now, a `QGroupBox` will suffice.
    *   Add `QDateEdit` widgets for "GST Period Start Date" and "GST Period End Date".
    *   Add a `QPushButton` labeled "Prepare GST F5 Data".
    *   Add non-editable `QLineEdit`s (or `QLabel`s) to display the following fields from the `GSTReturnData` DTO:
        *   Standard-Rated Supplies (Box 1)
        *   Zero-Rated Supplies (Box 2)
        *   Exempt Supplies (Box 3)
        *   Total Supplies (Box 4)
        *   Taxable Purchases (Box 5)
        *   Output Tax (Box 6)
        *   Input Tax (Box 7)
        *   Tax Adjustments (Box 8 - display as 0.00 initially, as this logic isn't implemented yet in `GSTManager`)
        *   Net GST Payable / (Refundable) (Box 9)
        *   Filing Due Date
    *   (Optional for this iteration, but consider placeholders) Buttons for "Save Draft" and "Finalize Return", initially disabled.
*   [ ] **Signal/Slot Connections**:
    *   Connect the "Prepare GST F5 Data" button's `clicked` signal to a new slot, e.g., `_on_prepare_gst_f5_clicked()`.
*   [ ] **Logic for Data Preparation (`_on_prepare_gst_f5_clicked`)**:
    *   This slot will be responsible for:
        *   Retrieving `start_date` and `end_date` from the `QDateEdit` widgets.
        *   Validating that `start_date` is not after `end_date`.
        *   Getting the `current_user_id` from `self.app_core.current_user`.
        *   Calling `schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))` to execute the backend logic asynchronously.
*   [ ] **Logic for Displaying Results (`_update_gst_f5_display_slot(json_gst_return_data_str)`)**:
    *   This new slot will be invoked via `QMetaObject.invokeMethod` from the completion of the `prepare_gst_return_data` coroutine.
    *   It will receive the `GSTReturnData` object (serialized as a JSON string).
    *   Parse the JSON string back into a Python dictionary or Pydantic `GSTReturnData` object using `json_date_hook`.
    *   Populate the display `QLineEdit`s/`QLabel`s with the values, formatted appropriately (e.g., currency format for monetary values, date format for dates).
    *   Handle potential errors returned from `GSTManager` (e.g., if `Result.is_success` is false) by displaying an error message in a `QMessageBox` or a status label.
    *   If successful, store the prepared `GSTReturnData` (perhaps as `self._prepared_gst_data: Optional[GSTReturnData] = None`) so it can be used by "Save Draft" later.
    *   (Optional) Enable a "Save Draft" button if data preparation was successful.
*   [ ] **Initial State**:
    *   Display fields should be empty or show "0.00" initially.
    *   "Save Draft" and "Finalize Return" buttons (if added) should be disabled until data is prepared.

Let's proceed with updating `app/ui/reports/reports_widget.py`.

```python
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon # For button icons
from typing import Optional, Dict, Any, TYPE_CHECKING
import json
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData # To type hint prepared data
from app.utils.result import Result # For type hinting manager results

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice # For QWidget type hint

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.layout = QVBoxLayout(self)
        
        # --- GST F5 Return Preparation Group ---
        gst_f5_group = QGroupBox("GST F5 Return Data Preparation")
        gst_f5_main_layout = QVBoxLayout(gst_f5_group)

        # Date Selection Layout
        date_selection_layout = QHBoxLayout()
        date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1)) # Start of 3 months ago
        self.gst_start_date_edit.setCalendarPopup(True)
        self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period Start Date:", self.gst_start_date_edit)

        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day())) # End of last month
        self.gst_end_date_edit.setCalendarPopup(True)
        self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form)
        
        prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data")
        self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button)
        prepare_button_layout.addStretch()
        date_selection_layout.addLayout(prepare_button_layout)
        date_selection_layout.addStretch(1)

        gst_f5_main_layout.addLayout(date_selection_layout)
        
        # Display Fields Layout
        self.gst_display_form = QFormLayout()
        self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True)
        self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True)
        self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True)
        self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;")
        self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True)
        self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True)
        self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True)
        self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True) # Box 8
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
        
        gst_f5_main_layout.addLayout(self.gst_display_form)

        # Action Buttons (initially disabled)
        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return")
        self.save_draft_gst_button.setEnabled(False)
        self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        # self.finalize_gst_button = QPushButton("Finalize GST Return") # For later
        # self.finalize_gst_button.setEnabled(False)
        # self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        gst_action_button_layout.addStretch()
        gst_action_button_layout.addWidget(self.save_draft_gst_button)
        # gst_action_button_layout.addWidget(self.finalize_gst_button)
        gst_f5_main_layout.addLayout(gst_action_button_layout)

        self.layout.addWidget(gst_f5_group)
        self.layout.addStretch() # Push everything to the top
        self.setLayout(self.layout)

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None: return "0.00"
        try:
            return f"{Decimal(str(value)):,.2f}"
        except InvalidOperation:
            return "Error"

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython()
        end_date = self.gst_end_date_edit.date().toPython()

        if start_date > end_date:
            QMessageBox.warning(self, "Date Error", "Start date cannot be after end date.")
            return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        if not self.app_core.gst_manager:
            QMessageBox.critical(self, "Error", "GST Manager not available.")
            return

        # Disable button during preparation
        self.prepare_gst_button.setEnabled(False)
        self.prepare_gst_button.setText("Preparing...")
        
        current_user_id = self.app_core.current_user.id
        schedule_task_from_qt(
            self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id)
        ).add_done_callback(self._handle_prepare_gst_f5_result) # Use add_done_callback

    def _handle_prepare_gst_f5_result(self, future):
        # This runs in the Qt main thread because future.add_done_callback ensures it
        self.prepare_gst_button.setEnabled(True)
        self.prepare_gst_button.setText("Prepare GST F5 Data")
        try:
            result: Result[GSTReturnData] = future.result() # Get result from future
            if result.is_success and result.value:
                self._prepared_gst_data = result.value
                # Pass data as dict for JSON compatibility if using Q_ARG with QMetaObject
                # For direct call from future callback, can pass DTO or dict directly
                self._update_gst_f5_display(self._prepared_gst_data)
                self.save_draft_gst_button.setEnabled(True)
            else:
                self._clear_gst_display_fields()
                self.save_draft_gst_button.setEnabled(False)
                QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e:
            self._clear_gst_display_fields()
            self.save_draft_gst_button.setEnabled(False)
            self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True) # type: ignore
            QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")


    # This method is now called directly from _handle_prepare_gst_f5_result
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
        if gst_data.filing_due_date:
            self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y'))
        else:
            self.gst_filing_due_date_display.clear()

    def _clear_gst_display_fields(self):
        self.gst_std_rated_supplies_display.clear()
        self.gst_zero_rated_supplies_display.clear()
        self.gst_exempt_supplies_display.clear()
        self.gst_total_supplies_display.clear()
        self.gst_taxable_purchases_display.clear()
        self.gst_output_tax_display.clear()
        self.gst_input_tax_display.clear()
        self.gst_adjustments_display.setText("0.00")
        self.gst_net_payable_display.clear()
        self.gst_filing_due_date_display.clear()
        self._prepared_gst_data = None

    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data:
            QMessageBox.warning(self, "No Data", "Please prepare GST data first.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        # User ID is already in self._prepared_gst_data from prepare_gst_return_data
        # Update with current user if different, though typically should be same session.
        self._prepared_gst_data.user_id = self.app_core.current_user.id

        self.save_draft_gst_button.setEnabled(False)
        self.save_draft_gst_button.setText("Saving Draft...")
        schedule_task_from_qt(
            self.app_core.gst_manager.save_gst_return(self._prepared_gst_data)
        ).add_done_callback(self._handle_save_draft_gst_result)

    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True) # Re-enable based on state later if needed
        self.save_draft_gst_button.setText("Save Draft GST Return")
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value:
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id}).")
                # Update self._prepared_gst_data with the ID from the saved ORM object if it was new
                self._prepared_gst_data.id = result.value.id # type: ignore
                # Potentially enable "Finalize" button here
            else:
                QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True) # type: ignore
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}")

    # Placeholder for finalize - to be implemented later
    # def _on_finalize_gst_return_clicked(self):
    #     if not self._prepared_gst_data or not self._prepared_gst_data.id:
    #         QMessageBox.warning(self, "No Draft", "Please save a draft GST return first or ensure it has an ID.")
    #         return
    #     # ... (Prompt for submission reference, date, then call manager.finalize_gst_return)
    #     QMessageBox.information(self, "Finalize GST", "Finalize GST Return functionality to be implemented.")

```

**Validation of `app/ui/reports/reports_widget.py` changes:**
*   **UI Structure**:
    *   A `QGroupBox` "GST F5 Return Data Preparation" is added.
    *   `QDateEdit` for start/end dates, "Prepare GST F5 Data" button.
    *   `QFormLayout` (`self.gst_display_form`) used for neatly displaying the GST figures with `QLineEdit` (read-only). Box numbers are included in labels.
    *   "Save Draft GST Return" button added, initially disabled. "Finalize" button commented out for now.
*   **Icon Handling**: `self.icon_path_prefix` initialized and used for the "Prepare" button icon.
*   **`_on_prepare_gst_f5_clicked`**:
    *   Gets dates, validates start <= end.
    *   Checks for `current_user` and `gst_manager`.
    *   Calls `gst_manager.prepare_gst_return_data` asynchronously.
    *   Uses `future.add_done_callback(self._handle_prepare_gst_f5_result)` to handle the result in the Qt thread. This is a cleaner way than `QMetaObject.invokeMethod` if the slot only needs the future object.
*   **`_handle_prepare_gst_f5_result` (New Slot)**:
    *   Called when `prepare_gst_return_data` completes.
    *   Re-enables the "Prepare" button.
    *   Gets `Result[GSTReturnData]` from `future.result()`.
    *   If successful, stores the DTO in `self._prepared_gst_data`, calls `_update_gst_f5_display`, and enables the "Save Draft" button.
    *   Shows error messages on failure.
*   **`_update_gst_f5_display(gst_data: GSTReturnData)` (New Method)**:
    *   Takes `GSTReturnData` DTO directly.
    *   Populates the display fields using `_format_decimal_for_display`.
*   **`_clear_gst_display_fields` (New Method)**: Clears all display fields and `self._prepared_gst_data`.
*   **`_on_save_draft_gst_return_clicked` and `_handle_save_draft_gst_result`**:
    *   Logic to call `gst_manager.save_gst_return` with `self._prepared_gst_data`.
    *   Handles the result, shows messages. Updates `self._prepared_gst_data.id` if a new draft was created and saved.

This provides a functional UI for preparing and viewing GST F5 data, and saving it as a draft. The finalization step can be added later. The application should launch, and this new UI section within the "Reports" tab should be interactive.


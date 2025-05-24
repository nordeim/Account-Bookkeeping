<think>
The application startup and shutdown are consistently clean. The backend `FiscalPeriodManager` has been enhanced. Now, we move to the UI part of fiscal year management.

**Current Step: Phase 1.1.3 - Create `FiscalYearDialog` and Integrate into `SettingsWidget`**

The immediate next step according to the plan is to create the new UI dialog file `app/ui/accounting/fiscal_year_dialog.py`.
Then, I will update `app/ui/settings/settings_widget.py` to use this dialog and display fiscal years. I'll also need to ensure `app/ui/accounting/__init__.py` exports the new dialog.

**Plan for `app/ui/accounting/fiscal_year_dialog.py` (New File):**
(This was already planned in the previous response, I'm re-confirming the details)
1.  **File Path**: `app/ui/accounting/fiscal_year_dialog.py`
2.  **Class**: `FiscalYearDialog(QDialog)`
3.  **Imports**:
    *   `PySide6.QtWidgets`: `QDialog`, `QVBoxLayout`, `QFormLayout`, `QLineEdit`, `QDateEdit`, `QComboBox`, `QPushButton`, `QDialogButtonBox`, `QMessageBox`.
    *   `PySide6.QtCore`: `Qt`, `QDate`, `Slot`.
    *   `typing`: `Optional`, `Dict`, `Any`.
    *   `app.core.application_core`: `ApplicationCore` (using forward reference `if TYPE_CHECKING:`).
    *   `app.utils.pydantic_models`: `FiscalYearCreateData`.
    *   `datetime`: `date`.
4.  **`__init__(self, app_core: "ApplicationCore", current_user_id: int, parent=None)`**:
    *   Store `app_core` and `current_user_id`.
    *   Initialize `self._fiscal_year_data: Optional[FiscalYearCreateData] = None`.
    *   Set window title: "Add New Fiscal Year".
    *   Set modality and minimum width.
    *   Call `_init_ui()`.
5.  **`_init_ui()`**:
    *   Create layout (`QVBoxLayout`, `QFormLayout`).
    *   **Year Name**: `QLineEdit` (`self.year_name_edit`).
    *   **Start Date**: `QDateEdit` (`self.start_date_edit`), calendar popup, display format "dd/MM/yyyy". Default to e.g., first day of current year or next year.
    *   **End Date**: `QDateEdit` (`self.end_date_edit`), calendar popup, display format "dd/MM/yyyy". Default to one year after start date minus one day.
    *   Connect `start_date_edit.dateChanged` to a slot `_update_default_end_date` to suggest an end date.
    *   **Auto-generate Periods**: `QComboBox` (`self.auto_generate_periods_combo`) with options: "Monthly", "Quarterly", "None". Default to "Monthly".
    *   **Buttons**: `QDialogButtonBox` with OK and Cancel buttons. Connect `accepted` to `self.accept_data` and `rejected` to `self.reject`.
6.  **`_update_default_end_date(self, new_start_date: QDate)` Slot**:
    *   Calculates a suggested end date (e.g., `new_start_date.addYears(1).addDays(-1)`).
    *   Updates `self.end_date_edit` if the user hasn't manually deviated too far from a typical year-long period.
    *   Stores `self._previous_start_date` for this heuristic.
7.  **`accept_data()` Slot (connected to OK button)**:
    *   Get values from UI fields.
    *   Perform client-side validation (name not empty, start < end, reasonable duration).
    *   Show `QMessageBox.warning` if validation fails.
    *   If valid, create `FiscalYearCreateData` instance (populating `user_id` from `self.current_user_id`).
    *   Store the DTO in `self._fiscal_year_data`.
    *   Call `super().accept()` (from `QDialog`).
    *   Handle Pydantic validation errors during DTO creation.
8.  **`get_fiscal_year_data(self) -> Optional[FiscalYearCreateData]` Method**:
    *   Returns `self._fiscal_year_data`.
9.  **`open()` Method (override)**:
    *   Reset `self._fiscal_year_data = None`.
    *   Reset UI fields to sensible defaults for a new entry.

After creating this dialog, the next sub-step will be to modify `SettingsWidget`.
</think>

Continuing with our plan, the next step is to create the new UI dialog file for adding Fiscal Years.

**1. Create `app/ui/accounting/fiscal_year_dialog.py`**

This dialog will allow users to input the necessary details for a new fiscal year.

```python
# File: app/ui/accounting/fiscal_year_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import date as python_date # Alias to avoid conflict with QDate

from app.utils.pydantic_models import FiscalYearCreateData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class FiscalYearDialog(QDialog):
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self._fiscal_year_data: Optional[FiscalYearCreateData] = None
        self._previous_start_date: Optional[QDate] = None # For default end date logic

        self.setWindowTitle("Add New Fiscal Year")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._set_initial_dates() # Set initial default dates

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.year_name_edit = QLineEdit()
        self.year_name_edit.setPlaceholderText("e.g., FY2024 or Y/E 31 Dec 2024")
        form_layout.addRow("Fiscal Year Name*:", self.year_name_edit)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Start Date*:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("End Date*:", self.end_date_edit)
        
        self.start_date_edit.dateChanged.connect(self._update_default_end_date)

        self.auto_generate_periods_combo = QComboBox()
        self.auto_generate_periods_combo.addItems(["Monthly", "Quarterly", "None"])
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        form_layout.addRow("Auto-generate Periods:", self.auto_generate_periods_combo)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _set_initial_dates(self):
        today = QDate.currentDate()
        # Default start: first day of current month, or Jan 1st if typical
        default_start = QDate(today.year(), 1, 1) # Default to Jan 1st of current year
        # If current date is past June, suggest starting next year's FY
        if today.month() > 6:
            default_start = QDate(today.year() + 1, 1, 1)
        
        default_end = default_start.addYears(1).addDays(-1)
        
        self.start_date_edit.setDate(default_start)
        self.end_date_edit.setDate(default_end) 
        self._previous_start_date = default_start


    @Slot(QDate)
    def _update_default_end_date(self, new_start_date: QDate):
        # Only update if the end date seems to be following the start date automatically
        # or if it's the initial setup.
        if self._previous_start_date is None: # Initial setup
            self._previous_start_date = self.start_date_edit.date() # Could be different from new_start_date if called by setDate initially
        
        # Calculate expected end based on previous start
        expected_end_from_prev_start = self._previous_start_date.addYears(1).addDays(-1)
        
        # If current end date matches the old default, then update it based on new start date
        if self.end_date_edit.date() == expected_end_from_prev_start:
            self.end_date_edit.setDate(new_start_date.addYears(1).addDays(-1))
        
        self._previous_start_date = new_start_date


    @Slot()
    def accept_data(self):
        """Validate and store data before accepting the dialog."""
        year_name = self.year_name_edit.text().strip()
        start_date_py: python_date = self.start_date_edit.date().toPython() 
        end_date_py: python_date = self.end_date_edit.date().toPython()
        auto_generate_str = self.auto_generate_periods_combo.currentText()
        auto_generate_periods = auto_generate_str if auto_generate_str != "None" else None

        errors = []
        if not year_name:
            errors.append("Fiscal Year Name is required.")
        if start_date_py >= end_date_py:
            errors.append("End Date must be after Start Date.")
        
        days_in_year = (end_date_py - start_date_py).days + 1
        if not (300 < days_in_year < 400): # Heuristic for typical year length
             errors.append("Fiscal year duration seems unusual (typically around 365 days). Please verify dates.")

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return # Do not accept

        try:
            self._fiscal_year_data = FiscalYearCreateData(
                year_name=year_name,
                start_date=start_date_py,
                end_date=end_date_py,
                auto_generate_periods=auto_generate_periods,
                user_id=self.current_user_id # Passed in from calling widget
            )
            super().accept() 
        except Exception as e: 
            QMessageBox.warning(self, "Data Error", f"Invalid data: {str(e)}")


    def get_fiscal_year_data(self) -> Optional[FiscalYearCreateData]:
        return self._fiscal_year_data

    def open(self) -> int: 
        self._fiscal_year_data = None
        self.year_name_edit.clear()
        self._set_initial_dates() # Reset dates to default for a new entry
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        self.year_name_edit.setFocus()
        return super().open()
```

**Validation of `app/ui/accounting/fiscal_year_dialog.py`:**
*   **Imports**: Correctly imports necessary PySide6 modules, `FiscalYearCreateData` DTO, and `ApplicationCore` (via `TYPE_CHECKING`). `python_date` alias for `datetime.date` is used to avoid conflict with `QDate`.
*   **UI Elements**: Standard widgets are used. `QDateEdit` includes calendar popups and a display format.
*   **Default Dates**: `_set_initial_dates` provides sensible defaults. `_update_default_end_date` slot attempts to smartly update the end date when the start date changes.
*   **Validation (`accept_data`)**: Performs client-side checks for name, date order, and a heuristic for year duration. Creates `FiscalYearCreateData` DTO, which will also trigger Pydantic validation.
*   **Data Retrieval**: `get_fiscal_year_data()` allows the caller to get the DTO.
*   **`open()` override**: Resets the dialog for a new entry.

---
**2. Update `app/ui/accounting/__init__.py` to export the new dialog**

```python
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog
from .fiscal_year_dialog import FiscalYearDialog # Added export

__all__ = [
    "AccountingWidget", 
    "ChartOfAccountsWidget", 
    "AccountDialog",
    "FiscalYearDialog", # Added to __all__
]
```
**Validation:** Added `FiscalYearDialog` to imports and `__all__`.

---
Now, I will proceed to update `app/ui/settings/settings_widget.py` to integrate this new dialog and display fiscal years.

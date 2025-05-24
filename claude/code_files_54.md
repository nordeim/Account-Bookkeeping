<think>
The application continues to launch and shut down cleanly after the `FiscalPeriodManager` and `FiscalYearService` enhancements. This is excellent.

The next step in **Phase 1.1: Implementing Fiscal Year Creation and Period Generation** is to create the UI dialog for adding a new Fiscal Year.

**Plan for `app/ui/accounting/fiscal_year_dialog.py` (New File):**

1.  **Create the file `app/ui/accounting/fiscal_year_dialog.py`.**
2.  **Define `FiscalYearDialog(QDialog)` class.**
3.  **UI Elements:**
    *   `QLineEdit` for "Fiscal Year Name" (e.g., "FY2024", "Year Ended 31 Dec 2024").
    *   `QDateEdit` for "Start Date".
    *   `QDateEdit` for "End Date".
    *   `QComboBox` for "Auto-generate Periods": Options ["None", "Monthly", "Quarterly"]. Default to "Monthly".
    *   Standard "OK" and "Cancel" buttons (`QDialogButtonBox` or separate `QPushButton`s).
4.  **Initialization (`__init__`)**:
    *   Accept `ApplicationCore` instance and `current_user_id`.
    *   Set window title.
    *   Layout UI elements using `QFormLayout` and `QVBoxLayout`/`QHBoxLayout`.
5.  **Data Collection and Validation (on "OK" click / `accept()`):**
    *   Retrieve values from UI fields.
    *   Perform basic client-side validation (e.g., name not empty, start date < end date).
    *   Create `FiscalYearCreateData` Pydantic DTO.
6.  **Interaction with `FiscalPeriodManager`**:
    *   Call `self.app_core.fiscal_period_manager.create_fiscal_year(dto)`.
    *   This call needs to be asynchronous. The dialog's `accept()` method is synchronous.
    *   **Strategy for async call from sync dialog:**
        *   The dialog's `accept()` method will prepare the DTO.
        *   Instead of directly calling the async manager method and awaiting it (which `accept()` cannot do), the dialog will store the DTO.
        *   The calling code (e.g., `SettingsWidget`) will retrieve this DTO after `dialog.exec() == QDialog.Accepted` and then schedule the async task itself.
        *   So, `FiscalYearDialog` will have a method like `get_fiscal_year_data()` that returns the `FiscalYearCreateData` if validation passes.
7.  **Error Handling**: Display error messages from client-side validation or if the manager call (done by the caller) fails.

**Pydantic DTO `FiscalYearCreateData` (already defined in `app/utils/pydantic_models.py`):**
```python
class FiscalYearCreateData(AppBaseModel, UserAuditData):
    year_name: str = Field(..., max_length=20)
    start_date: date
    end_date: date
    auto_generate_periods: Optional[str] = None # "Monthly", "Quarterly", or None/""
    # user_id is inherited from UserAuditData

    @root_validator(skip_on_failure=True)
    def check_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        start = values.get('start_date')
        end = values.get('end_date')
        if start and end and start >= end:
            raise ValueError("End date must be after start date.")
        return values
```

This DTO structure is suitable. The dialog will primarily focus on collecting these fields.
I will now generate the content for `app/ui/accounting/fiscal_year_dialog.py`.
</think>

Excellent, the application remains stable! Now we'll create the user interface component for adding a new fiscal year.

This involves:
1.  Creating the new file `app/ui/accounting/fiscal_year_dialog.py`.
2.  Designing the dialog with input fields for fiscal year details.
3.  Handling data collection and basic validation within the dialog.
4.  Providing a way for the calling widget (`SettingsWidget`) to retrieve the entered data.

Here's the content for the new file:

```python
# File: app/ui/accounting/fiscal_year_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from typing import Optional, Dict, Any

from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import FiscalYearCreateData # Assuming this DTO is defined

class FiscalYearDialog(QDialog):
    def __init__(self, app_core: ApplicationCore, current_user_id: int, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self._fiscal_year_data: Optional[FiscalYearCreateData] = None

        self.setWindowTitle("Add New Fiscal Year")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.year_name_edit = QLineEdit()
        self.year_name_edit.setPlaceholderText("e.g., FY2024 or Year Ended 31 Dec 2024")
        form_layout.addRow("Fiscal Year Name:", self.year_name_edit)

        self.start_date_edit = QDateEdit(QDate.currentDate())
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Start Date:", self.start_date_edit)

        self.end_date_edit = QDateEdit(QDate.currentDate().addYears(1).addDays(-1))
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("End Date:", self.end_date_edit)
        
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

    @Slot(QDate)
    def _update_default_end_date(self, new_start_date: QDate):
        # Set default end date to one year minus one day from start date
        # Only update if the end date hasn't been manually changed much from the initial default
        current_end_date = self.end_date_edit.date()
        initial_default_end_for_current_start = new_start_date.addYears(1).addDays(-1)
        
        # Heuristic: if current end date is still near a typical 1-year-minus-day from some start date, auto-update it.
        # This allows manual override but helps if user primarily changes start date.
        if abs(current_end_date.daysTo(self._previous_start_date.addYears(1).addDays(-1) if hasattr(self, '_previous_start_date') else new_start_date)) < 350 : # approx
             self.end_date_edit.setDate(initial_default_end_for_current_start)
        self._previous_start_date = new_start_date


    def accept_data(self):
        """Validate and store data before accepting the dialog."""
        year_name = self.year_name_edit.text().strip()
        start_date = self.start_date_edit.date().toPython() # Convert QDate to datetime.date
        end_date = self.end_date_edit.date().toPython()
        auto_generate_str = self.auto_generate_periods_combo.currentText()
        auto_generate_periods = auto_generate_str if auto_generate_str != "None" else None

        errors = []
        if not year_name:
            errors.append("Fiscal Year Name is required.")
        if start_date >= end_date:
            errors.append("End Date must be after Start Date.")
        
        # Basic validation for typical fiscal year length (e.g., not too short, not excessively long)
        # This is a heuristic, actual business rules might vary.
        days_in_year = (end_date - start_date).days + 1
        if not (300 < days_in_year < 400): # Roughly between 10 months and 13 months
             errors.append("Fiscal year duration seems unusual. Please verify dates (typically around 365 days).")


        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return

        try:
            self._fiscal_year_data = FiscalYearCreateData(
                year_name=year_name,
                start_date=start_date,
                end_date=end_date,
                auto_generate_periods=auto_generate_periods,
                user_id=self.current_user_id
            )
            super().accept() # Call QDialog.accept()
        except Exception as e: # Catch Pydantic validation errors
            QMessageBox.warning(self, "Data Error", f"Invalid data: {str(e)}")


    def get_fiscal_year_data(self) -> Optional[FiscalYearCreateData]:
        return self._fiscal_year_data

    def open(self) -> int: # Overload open to clear data on reopen
        self._fiscal_year_data = None
        # Reset fields to sensible defaults when dialog is reopened
        self.year_name_edit.clear()
        today = QDate.currentDate()
        # Default to a typical fiscal year, e.g., starting current month, ending next year
        default_start = QDate(today.year(), today.month(), 1)
        default_end = default_start.addYears(1).addDays(-1)
        self.start_date_edit.setDate(default_start)
        self.end_date_edit.setDate(default_end) # This will trigger _update_default_end_date
        self._previous_start_date = default_start # Initialize for _update_default_end_date logic
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        return super().open()

```

**Validation of `app/ui/accounting/fiscal_year_dialog.py`:**
*   **Imports**: Necessary PySide6 components and the `FiscalYearCreateData` DTO are imported.
*   **UI Elements**: Standard input fields (`QLineEdit`, `QDateEdit`, `QComboBox`) are used.
*   **Layout**: `QFormLayout` for labeled inputs, within a `QVBoxLayout`. Standard OK/Cancel buttons.
*   **Default Dates**: Start date defaults to current date, end date defaults to approximately one year later. A slot `_update_default_end_date` provides some dynamic adjustment if the start date is changed.
*   **Data Collection & Validation (`accept_data`)**:
    *   Retrieves values from UI elements.
    *   Performs basic client-side validation (name presence, date order, rough duration check).
    *   Creates a `FiscalYearCreateData` DTO if client-side validation passes. Pydantic validation will also occur here.
    *   If valid, stores the DTO in `self._fiscal_year_data` and calls `super().accept()`.
*   **`get_fiscal_year_data()`**: Public method for the caller to retrieve the DTO after the dialog is accepted.
*   **`open()` override**: Clears previous data and resets fields to defaults when the dialog is reopened for a new entry.

This dialog provides the necessary UI for capturing new fiscal year information. The next steps will involve integrating this dialog into `SettingsWidget` and then ensuring the `FiscalPeriodManager` and `FiscalYearService` correctly process this data.

Next, I will provide the updated `app/ui/settings/settings_widget.py` to incorporate the Fiscal Year management section and this new dialog.

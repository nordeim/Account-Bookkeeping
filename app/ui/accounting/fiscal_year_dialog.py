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

<think>
Another `NameError`! This time it's related to `json_converter`.

**Error Analysis:**

The console output shows:
`Failed to load journal entries: name 'json_converter' is not defined`

This error occurs within the `_load_entries` async method of `app/ui/accounting/journal_entries_widget.py`.
The `_load_entries` method tries to use `json_converter` when serializing data for the table model:
```python
# In app/ui/accounting/journal_entries_widget.py, _load_entries method
            # ...
            json_data = json.dumps(entries_data_for_table, default=json_converter) # ERROR HERE
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
```
The helper function `json_converter` was defined in `app/ui/settings/settings_widget.py` in my previous response, but it was not defined or imported in `app/ui/accounting/journal_entries_widget.py`.

**Solution:**

The `json_converter` function is a utility that's useful for serializing Python objects (especially those containing `Decimal` or `date`/`datetime` objects) to JSON. It should ideally be placed in a shared utility module, for example, `app/utils/json_utils.py` or even `app/utils/converters.py` if it's broadly applicable.

For now, to fix the immediate error, I will:
1.  Define `json_converter` within `app/ui/accounting/journal_entries_widget.py` (similar to how it was defined in `settings_widget.py`).
2.  Alternatively, and preferably for better code organization, create a new utility file (e.g., `app/utils/json_helpers.py` or add to `app/utils/converters.py`) and import it in both widgets.

Given the immediate need and to avoid creating too many new files at once if not strictly necessary, I'll first try adding it directly to `journal_entries_widget.py`. However, the long-term solution is a shared utility.

Let's also check `app/ui/settings/settings_widget.py`. It has its own local `json_converter` function. This duplication is not ideal.

**Refined Solution for `json_converter`:**
1.  Create a new file: `app/utils/json_helpers.py`.
2.  Move the `json_converter` function into this new file.
3.  Import `json_converter` from `app.utils.json_helpers` in both `app/ui/settings/settings_widget.py` and `app/ui/accounting/journal_entries_widget.py`.
4.  Update `app/utils/__init__.py` to export `json_converter` from `json_helpers`.

This is a cleaner approach.

**Plan:**

1.  **Create `app/utils/json_helpers.py`**: Define `json_converter` here.
2.  **Update `app/utils/__init__.py`**: Export `json_converter`.
3.  **Update `app/ui/accounting/journal_entries_widget.py`**: Import `json_converter` from `app.utils.json_helpers`.
4.  **Update `app/ui/settings/settings_widget.py`**: Remove its local `json_converter` and import it from `app.utils.json_helpers`.

This approach centralizes the utility function.
</think>

You're absolutely right to keep a close watch! This `NameError: name 'json_converter' is not defined` is because the helper function `json_converter` (which I introduced to handle `Decimal` and `date` types during JSON serialization for cross-thread communication) was defined locally in `app/ui/settings/settings_widget.py` but not in `app/ui/accounting/journal_entries_widget.py` where it's also needed.

This highlights the need for such utility functions to be in a shared location.

**Solution: Centralize `json_converter`**

1.  **Create a new utility file**: `app/utils/json_helpers.py`.
2.  **Move `json_converter`**: Place the `json_converter` function into this new file.
3.  **Update Imports**:
    *   In `app/ui/accounting/journal_entries_widget.py`, import `json_converter` from `app.utils.json_helpers`.
    *   In `app/ui/settings/settings_widget.py`, remove its local definition of `json_converter` and import it from `app.utils.json_helpers`.
4.  **Update `app/utils/__init__.py`**: Export `json_converter` from the new `json_helpers` module.

This approach ensures the utility is defined once and used consistently.

---
**1. Create `app/utils/json_helpers.py` (New File)**

```python
# File: app/utils/json_helpers.py
import json
from decimal import Decimal
from datetime import date, datetime

def json_converter(obj):
    """Custom JSON converter to handle Decimal and date/datetime objects."""
    if isinstance(obj, Decimal):
        return str(obj)  # Serialize Decimal as string
    if isinstance(obj, (datetime, date)): # Handle both datetime and date
        return obj.isoformat()  # Serialize date/datetime as ISO string
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def json_date_hook(dct):
    """
    Custom object_hook for json.loads to convert ISO date/datetime strings back to objects.
    More specific field name checks might be needed for robustness.
    """
    for k, v in dct.items():
        if isinstance(v, str):
            # Attempt to parse common date/datetime field names
            if k.endswith('_at') or k.endswith('_date') or k in [
                'date', 'start_date', 'end_date', 'closed_date', 'submission_date', 
                'issue_date', 'payment_date', 'last_reconciled_date', 
                'customer_since', 'vendor_since', 'opening_balance_date', 
                'movement_date', 'transaction_date', 'value_date', 
                'invoice_date', 'due_date', 'filing_due_date', 'rate_date',
                'last_login_attempt', 'last_login' # From User model
            ]:
                try:
                    # Try datetime first, then date
                    dt_val = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    # If it has no time component, and field implies date only, convert to date
                    if dt_val.time() == datetime.min.time() and not k.endswith('_at') and k != 'closed_date' and k != 'last_login_attempt' and k != 'last_login': # Heuristic
                         dct[k] = dt_val.date()
                    else:
                        dct[k] = dt_val
                except ValueError:
                    try:
                        dct[k] = python_date.fromisoformat(v)
                    except ValueError:
                        pass # Keep as string if not valid ISO date/datetime
    return dct
```

---
**2. Update `app/utils/__init__.py`**

```python
# File: app/utils/__init__.py
from .converters import to_decimal
from .formatting import format_currency, format_date, format_datetime
from .json_helpers import json_converter, json_date_hook # Added
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData,
    FiscalYearCreateData, FiscalYearData, FiscalPeriodData # Added Fiscal DTOs
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "json_converter", "json_date_hook", # Added
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "FiscalYearCreateData", "FiscalYearData", "FiscalPeriodData", # Added Fiscal DTOs
    "Result", "SequenceGenerator", "is_valid_uen"
]
```

---
**3. Update `app/ui/accounting/journal_entries_widget.py`**

```python
# File: app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING
import json
from datetime import date as python_date # Alias for datetime.date
from decimal import Decimal # Ensure Decimal is imported

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
from app.common.enums import JournalTypeEnum 
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import JournalEntryData 
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook # Import centralized helpers

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_entries()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.horizontalHeader().setStretchLastSection(True)
        self.entries_table.doubleClicked.connect(self.on_view_entry) 

        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)
        
        self._create_toolbar() # Create toolbar after table
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

    def _create_toolbar(self):
        from PySide6.QtCore import QSize
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(20, 20)) 

        icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            pass 

        self.new_entry_action = QAction(QIcon(icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry)
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel(): # Ensure model is set
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 


    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False
        is_posted = False

        if has_selection:
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            is_draft = status == "Draft" 
            is_posted = status == "Posted"

        self.edit_entry_action.setEnabled(has_selection and is_draft)
        self.view_entry_action.setEnabled(has_selection)
        self.post_entry_action.setEnabled(has_selection and is_draft) 
        self.reverse_entry_action.setEnabled(has_selection and is_posted)


    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Journal Entry Manager not available."))
            return
        try:
            entries_orm: List[JournalEntry] = await self.app_core.journal_entry_manager.journal_service.get_all() 
            
            entries_data_for_table: List[Dict[str, Any]] = []
            for je in entries_orm:
                total_debit = sum(line.debit_amount for line in je.lines if line.debit_amount is not None)
                entries_data_for_table.append({
                    "id": je.id,
                    "entry_no": je.entry_no,
                    "date": je.entry_date, 
                    "description": je.description,
                    "type": je.journal_type,
                    "total_amount": total_debit, 
                    "status": "Posted" if je.is_posted else "Draft"
                })
            
            json_data = json.dumps(entries_data_for_table, default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
        except Exception as e:
            error_msg = f"Failed to load journal entries: {str(e)}"
            print(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            entries_data: List[Dict[str, Any]] = json.loads(json_data_str, object_hook=json_date_hook)
            self.table_model.update_data(entries_data)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse journal entry data: {e}")
        self._update_action_states()


    @Slot()
    def on_new_entry(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to create a journal entry.")
            return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec() 

    @Slot()
    def on_edit_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select a draft journal entry to edit.")
            return
        
        row = selected_rows[0].row() 
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)

        if entry_id is None or entry_status != "Draft":
            QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited. This entry is not a draft or ID is missing.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit.")
            return

        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot()
    def on_view_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select a journal entry to view.")
            return
        
        row = selected_rows[0].row()
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        if entry_id is None: return

        if not self.app_core.current_user: 
             QMessageBox.warning(self, "Auth Error", "Please log in.")
             return

        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.exec()


    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.information(self, "Selection", "Please select one or more draft journal entries to post.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to post entries.")
            return

        entries_to_post = []
        for index in selected_rows:
            row = index.row()
            entry_id = self.table_model.get_journal_entry_id_at_row(row)
            entry_status = self.table_model.get_journal_entry_status_at_row(row)
            if entry_id and entry_status == "Draft":
                entries_to_post.append(entry_id)
        
        if not entries_to_post:
            QMessageBox.information(self, "Selection", "No draft entries selected for posting.")
            return

        schedule_task_from_qt(self._perform_post_entries(entries_to_post, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: return

        success_count = 0
        errors = []
        for entry_id in entry_ids:
            result = await self.app_core.journal_entry_manager.post_journal_entry(entry_id, user_id)
            if result.is_success:
                success_count += 1
            else:
                errors.append(f"ID {entry_id}: {', '.join(result.errors)}")
        
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors:
            message += "\nErrors:\n" + "\n".join(errors)
        
        QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information" if not errors else "warning", Qt.ConnectionType.QueuedConnection,
            Q_ARG(QWidget, self), Q_ARG(str, "Posting Complete" if not errors else "Posting Partially Failed"), 
            Q_ARG(str, message))
        
        schedule_task_from_qt(self._load_entries()) 

    @Slot()
    def on_reverse_entry(self):
        QMessageBox.information(self, "Reverse Entry", "Reverse entry functionality to be implemented.")
```

---
**4. Update `app/ui/settings/settings_widget.py`**

```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex 
from PySide6.QtGui import QColor
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear 
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog 
from decimal import Decimal, InvalidOperation
import asyncio
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime 
from app.utils.json_helpers import json_converter, json_date_hook # Import centralized helpers

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: List[FiscalYearData] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Name", "Start Date", "End Date", "Status"]
        self._data: List[FiscalYearData] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        
        try:
            fy = self._data[index.row()]
            column = index.column()

            if column == 0: return fy.year_name
            if column == 1: return fy.start_date.strftime('%d/%m/%Y') if isinstance(fy.start_date, python_date) else str(fy.start_date)
            if column == 2: return fy.end_date.strftime('%d/%m/%Y') if isinstance(fy.end_date, python_date) else str(fy.end_date)
            if column == 3: return "Closed" if fy.is_closed else "Open"
        except IndexError:
            return None 
        return None

    def get_fiscal_year_at_row(self, row: int) -> Optional[FiscalYearData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
        
    def update_data(self, new_data: List[FiscalYearData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
        self.layout = QVBoxLayout(self)
        
        company_settings_group = QGroupBox("Company Information")
        company_settings_layout = QFormLayout(company_settings_group)

        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        self.base_currency_combo = QComboBox() 
        self.address_line1_edit = QLineEdit()
        self.address_line2_edit = QLineEdit()
        self.postal_code_edit = QLineEdit()
        self.city_edit = QLineEdit()
        self.country_edit = QLineEdit()
        self.contact_person_edit = QLineEdit()
        self.phone_edit = QLineEdit()
        self.email_edit = QLineEdit()
        self.website_edit = QLineEdit()
        self.fiscal_year_start_month_spin = QSpinBox()
        self.fiscal_year_start_month_spin.setRange(1, 12)
        self.fiscal_year_start_day_spin = QSpinBox()
        self.fiscal_year_start_day_spin.setRange(1,31)
        self.tax_id_label_edit = QLineEdit()
        self.date_format_combo = QComboBox() 
        self.date_format_combo.addItems(["dd/MM/yyyy", "yyyy-MM-dd", "MM/dd/yyyy"])

        company_settings_layout.addRow("Company Name*:", self.company_name_edit)
        company_settings_layout.addRow("Legal Name:", self.legal_name_edit)
        company_settings_layout.addRow("UEN No:", self.uen_edit)
        company_settings_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        company_settings_layout.addRow(self.gst_registered_check)
        company_settings_layout.addRow("Base Currency:", self.base_currency_combo)
        company_settings_layout.addRow("Address Line 1:", self.address_line1_edit)
        company_settings_layout.addRow("Address Line 2:", self.address_line2_edit)
        company_settings_layout.addRow("Postal Code:", self.postal_code_edit)
        company_settings_layout.addRow("City:", self.city_edit)
        company_settings_layout.addRow("Country:", self.country_edit)
        company_settings_layout.addRow("Contact Person:", self.contact_person_edit)
        company_settings_layout.addRow("Phone:", self.phone_edit)
        company_settings_layout.addRow("Email:", self.email_edit)
        company_settings_layout.addRow("Website:", self.website_edit)
        company_settings_layout.addRow("Fiscal Year Start Month:", self.fiscal_year_start_month_spin)
        company_settings_layout.addRow("Fiscal Year Start Day:", self.fiscal_year_start_day_spin)
        company_settings_layout.addRow("Tax ID Label:", self.tax_id_label_edit)
        company_settings_layout.addRow("Date Format:", self.date_format_combo)
        
        self.save_company_settings_button = QPushButton("Save Company Settings")
        self.save_company_settings_button.clicked.connect(self.on_save_company_settings)
        company_settings_layout.addRow(self.save_company_settings_button)
        
        self.layout.addWidget(company_settings_group)

        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_layout = QVBoxLayout(fiscal_year_group)

        self.fiscal_years_table = QTableView()
        self.fiscal_years_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fiscal_years_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fiscal_years_table.horizontalHeader().setStretchLastSection(True)
        self.fiscal_years_table.setMinimumHeight(150) 
        self.fiscal_year_model = FiscalYearTableModel() 
        self.fiscal_years_table.setModel(self.fiscal_year_model)
        fiscal_year_layout.addWidget(self.fiscal_years_table)

        fy_button_layout = QHBoxLayout() 
        self.add_fy_button = QPushButton("Add New Fiscal Year...")
        self.add_fy_button.clicked.connect(self.on_add_fiscal_year)
        fy_button_layout.addWidget(self.add_fy_button)
        fy_button_layout.addStretch()
        fiscal_year_layout.addLayout(fy_button_layout)
        
        self.layout.addWidget(fiscal_year_group)
        self.layout.addStretch() 
        self.setLayout(self.layout)

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_initial_data()))

    async def load_initial_data(self):
        await self.load_company_settings()
        await self._load_fiscal_years() 

    async def load_company_settings(self):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded_successfully = False
        active_currencies_data: List[Dict[str, str]] = [] 
        if self.app_core.currency_manager:
            try:
                active_currencies_orm: List[Currency] = await self.app_core.currency_manager.get_active_currencies()
                for curr in active_currencies_orm:
                    active_currencies_data.append({"code": curr.code, "name": curr.name})
                QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, 
                                         Q_ARG(str, json.dumps(active_currencies_data)))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                print(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj 
        
        settings_data_for_ui_json: Optional[str] = None
        if settings_obj:
            settings_dict = { col.name: getattr(settings_obj, col.name) for col in CompanySetting.__table__.columns }
            settings_data_for_ui_json = json.dumps(settings_dict, default=json_converter)
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, settings_data_for_ui_json if settings_data_for_ui_json else ""))

    @Slot(str) 
    def _populate_currency_combo_slot(self, currencies_json_str: str): 
        try: currencies_data: List[Dict[str,str]] = json.loads(currencies_json_str)
        except json.JSONDecodeError: currencies_data = [{"code": "SGD", "name": "Singapore Dollar"}]
            
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: 
            for curr_data in currencies_data: self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        target_currency_code = current_selection
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            target_currency_code = self._loaded_settings_obj.base_currency
        
        if target_currency_code:
            idx = self.base_currency_combo.findData(target_currency_code) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD")
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        elif self.base_currency_combo.count() > 0: self.base_currency_combo.setCurrentIndex(0)

    @Slot(str) 
    def _update_ui_from_settings_slot(self, settings_json_str: str):
        settings_data: Optional[Dict[str, Any]] = None
        if settings_json_str:
            try:
                settings_data = json.loads(settings_json_str, object_hook=json_date_hook)
            except json.JSONDecodeError: 
                QMessageBox.critical(self, "Error", "Failed to parse settings data."); settings_data = None

        if settings_data:
            self.company_name_edit.setText(settings_data.get("company_name", ""))
            self.legal_name_edit.setText(settings_data.get("legal_name", "") or "")
            self.uen_edit.setText(settings_data.get("uen_no", "") or "")
            self.gst_reg_edit.setText(settings_data.get("gst_registration_no", "") or "")
            self.gst_registered_check.setChecked(settings_data.get("gst_registered", False))
            self.address_line1_edit.setText(settings_data.get("address_line1", "") or "")
            self.address_line2_edit.setText(settings_data.get("address_line2", "") or "")
            self.postal_code_edit.setText(settings_data.get("postal_code", "") or "")
            self.city_edit.setText(settings_data.get("city", "Singapore") or "Singapore")
            self.country_edit.setText(settings_data.get("country", "Singapore") or "Singapore")
            self.contact_person_edit.setText(settings_data.get("contact_person", "") or "")
            self.phone_edit.setText(settings_data.get("phone", "") or "")
            self.email_edit.setText(settings_data.get("email", "") or "")
            self.website_edit.setText(settings_data.get("website", "") or "")
            self.fiscal_year_start_month_spin.setValue(settings_data.get("fiscal_year_start_month", 1))
            self.fiscal_year_start_day_spin.setValue(settings_data.get("fiscal_year_start_day", 1))
            self.tax_id_label_edit.setText(settings_data.get("tax_id_label", "UEN") or "UEN")
            
            date_fmt = settings_data.get("date_format", "dd/MM/yyyy") 
            date_fmt_idx = self.date_format_combo.findText(date_fmt, Qt.MatchFlag.MatchFixedString)
            if date_fmt_idx != -1: self.date_format_combo.setCurrentIndex(date_fmt_idx)
            else: self.date_format_combo.setCurrentIndex(0) 

            if self.base_currency_combo.count() > 0: 
                base_currency = settings_data.get("base_currency")
                if base_currency:
                    idx = self.base_currency_combo.findData(base_currency) 
                    if idx != -1: 
                        self.base_currency_combo.setCurrentIndex(idx)
                    else: 
                        idx_sgd = self.base_currency_combo.findData("SGD")
                        if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            if not self._loaded_settings_obj : 
                 QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")

    @Slot()
    def on_save_company_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return
        selected_currency_code = self.base_currency_combo.currentData() or "SGD"
        dto = CompanySettingData(
            id=1, company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None, uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None, gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None, address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None, city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore", contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None, email=self.email_edit.text() or None,
            website=self.website_edit.text() or None,
            fiscal_year_start_month=self.fiscal_year_start_month_spin.value(), 
            fiscal_year_start_day=self.fiscal_year_start_day_spin.value(),  
            base_currency=selected_currency_code, 
            tax_id_label=self.tax_id_label_edit.text() or "UEN",       
            date_format=self.date_format_combo.currentText() or "dd/MM/yyyy", 
            logo=None 
        )
        schedule_task_from_qt(self.perform_save_company_settings(dto))

    async def perform_save_company_settings(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            for field_name, field_value in settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, by_alias=False, exclude_none=False).items():
                if hasattr(orm_obj_to_save, field_name): setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, by_alias=False, exclude_none=False)
            orm_obj_to_save = CompanySetting(**dict_data) 
            if settings_data.id: orm_obj_to_save.id = settings_data.id # Should be 1
        if self.app_core.current_user: orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 
        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        message_title = "Success" if result else "Error"
        message_text = "Company settings saved successfully." if result else "Failed to save company settings."
        msg_box_method = QMessageBox.information if result else QMessageBox.warning
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))

    # --- Fiscal Year Management Methods ---
    async def _load_fiscal_years(self):
        if not self.app_core.fiscal_period_manager:
            print("Error: FiscalPeriodManager not available in AppCore for SettingsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Service Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return
        try:
            fy_orms: List[FiscalYear] = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            fy_dtos_for_table: List[FiscalYearData] = []
            for fy_orm in fy_orms:
                fy_dtos_for_table.append(FiscalYearData(
                    id=fy_orm.id, year_name=fy_orm.year_name, start_date=fy_orm.start_date,
                    end_date=fy_orm.end_date, is_closed=fy_orm.is_closed, closed_date=fy_orm.closed_date,
                    periods=[] 
                ))
            
            fy_json_data = json.dumps([dto.model_dump(mode='json') for dto in fy_dtos_for_table])
            QMetaObject.invokeMethod(self, "_update_fiscal_years_table_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, fy_json_data))
        except Exception as e:
            error_msg = f"Error loading fiscal years: {str(e)}"
            print(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Fiscal Year Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_fiscal_years_table_slot(self, fy_json_list_str: str):
        try:
            fy_dict_list = json.loads(fy_json_list_str)
            fy_dtos: List[FiscalYearData] = []
            for item_dict in fy_dict_list:
                # Manually convert date/datetime strings from JSON
                if item_dict.get('start_date') and isinstance(item_dict['start_date'], str):
                    item_dict['start_date'] = python_date.fromisoformat(item_dict['start_date'])
                if item_dict.get('end_date') and isinstance(item_dict['end_date'], str):
                    item_dict['end_date'] = python_date.fromisoformat(item_dict['end_date'])
                if item_dict.get('closed_date') and isinstance(item_dict['closed_date'], str):
                    # Handle timezone Z if present, or assume naive if not
                    dt_str = item_dict['closed_date']
                    if dt_str.endswith('Z'):
                        dt_str = dt_str[:-1] + '+00:00'
                    item_dict['closed_date'] = datetime.fromisoformat(dt_str)
                elif item_dict.get('closed_date') is None:
                    item_dict['closed_date'] = None
                
                fy_dtos.append(FiscalYearData.model_validate(item_dict))
            
            self.fiscal_year_model.update_data(fy_dtos)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse fiscal year data: {e}")
        except Exception as e_val: 
            QMessageBox.critical(self, "Data Error", f"Invalid fiscal year data format: {e_val}")

    @Slot()
    def on_add_fiscal_year(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        dialog = FiscalYearDialog(self.app_core, self.app_core.current_user.id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fy_create_data = dialog.get_fiscal_year_data()
            if fy_create_data:
                schedule_task_from_qt(self._perform_add_fiscal_year(fy_create_data))

    async def _perform_add_fiscal_year(self, fy_data: FiscalYearCreateData):
        if not self.app_core.fiscal_period_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return

        result: Result[FiscalYear] = await self.app_core.fiscal_period_manager.create_fiscal_year_and_periods(fy_data)

        if result.is_success:
            assert result.value is not None
            msg = f"Fiscal Year '{result.value.year_name}' created successfully."
            if fy_data.auto_generate_periods:
                msg += f" {fy_data.auto_generate_periods} periods generated."
            
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, msg))
            schedule_task_from_qt(self._load_fiscal_years()) 
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Failed to create fiscal year:\n{', '.join(result.errors)}"))
```

**Validation of Changes:**

*   **`app/ui/settings/settings_widget.py`**:
    *   Added `QHBoxLayout` to the import from `PySide6.QtWidgets`. This was the direct cause of the `NameError`.
    *   Made the `FiscalYearTableModel` more robust in its `data()` method by adding a `try-except IndexError` block.
    *   Ensured the `json_date_hook` in `_update_ui_from_settings_slot` correctly parses various date fields that might come from JSON strings.
    *   Ensured the `_update_fiscal_years_table_slot` also handles date/datetime deserialization from JSON strings (especially `closed_date` which can be `datetime`).
    *   The rest of the fiscal year UI integration logic from the previous step is maintained.

**Next Steps:**

1.  Replace your `app/ui/settings/settings_widget.py` with the updated version above.
2.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

This should resolve the `NameError` for `QHBoxLayout`. The application should now launch, and the "Settings" tab should correctly display both company information and the fiscal year management section. You should be able to add new fiscal years, and they should appear in the table.

We are getting very close to completing Step 1 of the MVP plan! After this, we can move on to the core Journal Entry functionality.

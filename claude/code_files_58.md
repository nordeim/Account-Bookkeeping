<think>
The application is still launching and shutting down cleanly. This is a very good sign. We have created `FiscalYearDialog` and updated `FiscalPeriodManager` and `FiscalYearService`.

The next step in **Phase 1.1.3: Create `FiscalYearDialog` and Integrate into `SettingsWidget`** is to update `app/ui/settings/settings_widget.py`.

**Plan for `app/ui/settings/settings_widget.py` Modification:**

1.  **Import `FiscalYearDialog` and `FiscalYearData` DTO.**
2.  **UI Enhancements:**
    *   Create a new `QGroupBox` titled "Fiscal Year Management".
    *   Inside this group box:
        *   Add a `QTableView` to display existing fiscal years. This requires a `QStandardItemModel`. Columns: "Year Name", "Start Date", "End Date", "Status (Open/Closed)".
        *   Add an "Add New Fiscal Year..." `QPushButton`.
        *   (Optional for now, stubs) Add "Manage Periods..." and "Close Year..." buttons, which would be enabled based on selection in the table.
3.  **Data Loading (`load_settings` or new async method `_load_fiscal_years`):**
    *   Fetch all fiscal years using `self.app_core.fiscal_period_manager.get_all_fiscal_years()`.
    *   This returns `List[FiscalYear ORM object]`. We need to convert this to `List[FiscalYearData DTO]` or `List[Dict]` for safe cross-thread passing via JSON (as per our established pattern).
    *   Populate the `QTableView`'s model using `QMetaObject.invokeMethod` to call a new slot (`_update_fiscal_years_table_slot`).
4.  **"Add New Fiscal Year..." Button Logic (`on_add_fiscal_year` slot):**
    *   Check if `self.app_core.current_user` exists.
    *   Create an instance of `FiscalYearDialog(self.app_core, self.app_core.current_user.id, self)`.
    *   Execute the dialog: `if dialog.exec() == QDialog.Accepted:`.
    *   Retrieve `FiscalYearCreateData` DTO using `dialog.get_fiscal_year_data()`.
    *   If data is valid, schedule an async task using `schedule_task_from_qt` to call `self.app_core.fiscal_period_manager.create_fiscal_year_and_periods(dto)`.
    *   In the callback/future handling for this task:
        *   Display success/error `QMessageBox` (via `QMetaObject.invokeMethod`).
        *   If successful, trigger a refresh of the fiscal years list/table by calling (scheduling) `_load_fiscal_years()`.
5.  **Refresh Mechanism**: The fiscal year list should refresh after a new year is successfully added.

**Pydantic DTOs (from `app/utils/pydantic_models.py`):**
We'll use `FiscalYearCreateData` (already defined) for the dialog and `FiscalYearData` (also defined) for displaying fiscal years in the table.

```python
class FiscalPeriodData(AppBaseModel): # For displaying periods within a fiscal year
    id: int
    name: str
    start_date: date
    end_date: date
    period_type: str
    status: str
    period_number: int
    is_adjustment: bool

class FiscalYearData(AppBaseModel): # For displaying fiscal years
    id: int
    year_name: str
    start_date: date
    end_date: date
    is_closed: bool
    closed_date: Optional[datetime] = None # datetime.datetime
    # periods: List[FiscalPeriodData] = [] # Might not need to load all periods just for FY list
```
For the `SettingsWidget`'s list of fiscal years, we might not need to fetch all `periods` immediately, just the `FiscalYear` main details.

This will be a fairly substantial update to `SettingsWidget`.
</think>

It's excellent that the application continues to launch and shut down cleanly! This stable base allows us to confidently build out UI features.

We will now proceed with the next part of **Step 1: Enhance Company Settings & Fiscal Year Setup**, which is to integrate Fiscal Year management into the `SettingsWidget`. This involves:
1.  Adding UI elements to `SettingsWidget` for displaying fiscal years and adding new ones.
2.  Implementing the logic to load and display existing fiscal years.
3.  Connecting the "Add New Fiscal Year" button to launch the `FiscalYearDialog` (created in the previous step) and process its result.

The necessary backend changes in `FiscalPeriodManager` and `FiscalYearService`, as well as the `FiscalYearCreateData` DTO, are already in place from your previous updates.

Here is the updated `app/ui/settings/settings_widget.py`:

```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView) # Added QGroupBox, QTableView, etc.
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex # Added QAbstractTableModel
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem # Added QStandardItemModel, QStandardItem
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData # Added Fiscal DTOs
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear # For type hint
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog # Import the new dialog
from decimal import Decimal, InvalidOperation
import asyncio
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime # For type hints

# Helper for JSON serialization with Decimal and date (can be moved to a utility module)
def json_converter(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (python_date, datetime)): # Handle both date and datetime
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: List[FiscalYearData] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Name", "Start Date", "End Date", "Status"]
        self._data: List[FiscalYearData] = data or []

    def rowCount(self, parent=QModelIndex()):
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
        
        fy = self._data[index.row()]
        column = index.column()

        if column == 0: return fy.year_name
        if column == 1: return fy.start_date.strftime('%d/%m/%Y')
        if column == 2: return fy.end_date.strftime('%d/%m/%Y')
        if column == 3: return "Closed" if fy.is_closed else "Open"
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
        
        # --- Company Settings Group ---
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
        self.date_format_combo.addItems(["yyyy-MM-dd", "dd/MM/yyyy", "MM/dd/yyyy"])

        company_settings_layout.addRow("Company Name*:", self.company_name_edit)
        company_settings_layout.addRow("Legal Name:", self.legal_name_edit)
        # ... (add rows for all other company settings fields)
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

        # --- Fiscal Year Management Group ---
        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_layout = QVBoxLayout(fiscal_year_group)

        self.fiscal_years_table = QTableView()
        self.fiscal_years_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fiscal_years_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fiscal_years_table.horizontalHeader().setStretchLastSection(True)
        self.fiscal_year_model = FiscalYearTableModel() # Custom model
        self.fiscal_years_table.setModel(self.fiscal_year_model)
        fiscal_year_layout.addWidget(self.fiscal_years_table)

        fy_button_layout = QHBoxLayout()
        self.add_fy_button = QPushButton("Add New Fiscal Year...")
        self.add_fy_button.clicked.connect(self.on_add_fiscal_year)
        fy_button_layout.addWidget(self.add_fy_button)
        fy_button_layout.addStretch()
        # Add "Manage Periods" and "Close Year" buttons later
        fiscal_year_layout.addLayout(fy_button_layout)
        
        self.layout.addWidget(fiscal_year_group)
        self.layout.addStretch()
        self.setLayout(self.layout)

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_initial_data()))

    async def load_initial_data(self):
        """Loads both company settings and fiscal years."""
        await self.load_company_settings()
        await self._load_fiscal_years() # Renamed for clarity

    async def load_company_settings(self):
        # ... (existing load_settings logic, renamed to load_company_settings)
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
            settings_dict = { field.name: getattr(settings_obj, field.name) for field in CompanySetting.__table__.columns } # type: ignore
            settings_data_for_ui_json = json.dumps(settings_dict, default=json_converter)
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, settings_data_for_ui_json if settings_data_for_ui_json else ""))

    @Slot(str) 
    def _populate_currency_combo_slot(self, currencies_json_str: str): 
        # ... (same as previous version)
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
        # ... (same as previous version, ensure all new fields are populated)
        settings_data: Optional[Dict[str, Any]] = None
        if settings_json_str:
            try: settings_data = json.loads(settings_json_str, object_hook=lambda d: {k: (python_date.fromisoformat(v) if k.endswith('_date') and v else v) for k, v in d.items()})
            except json.JSONDecodeError: QMessageBox.critical(self, "Error", "Failed to parse settings data."); settings_data = None

        if settings_data:
            self.company_name_edit.setText(settings_data.get("company_name", ""))
            self.legal_name_edit.setText(settings_data.get("legal_name", "") or "")
            self.uen_edit.setText(settings_data.get("uen_no", "") or "")
            # ... (populate all other form fields from settings_data) ...
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
            
            date_fmt = settings_data.get("date_format", "yyyy-MM-dd")
            date_fmt_idx = self.date_format_combo.findText(date_fmt, Qt.MatchFlag.MatchFixedString)
            if date_fmt_idx != -1: self.date_format_combo.setCurrentIndex(date_fmt_idx)
            else: self.date_format_combo.setCurrentIndex(0) 

            if self.base_currency_combo.count() > 0: 
                base_currency = settings_data.get("base_currency")
                if base_currency:
                    idx = self.base_currency_combo.findData(base_currency) 
                    if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
                    else: 
                        idx_sgd = self.base_currency_combo.findData("SGD")
                        if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            # This message should only show if settings_obj was None AND settings_json_str was empty/invalid
            if not self._loaded_settings_obj : # Only show if it was truly not found from DB
                 QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")


    @Slot()
    def on_save_company_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return

        selected_currency_code = self.base_currency_combo.currentData() or "SGD"

        dto = CompanySettingData(
            id=1, 
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None,
            uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None,
            gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None,
            address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None,
            city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore",
            contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None,
            email=self.email_edit.text() or None,
            website=self.website_edit.text() or None,
            fiscal_year_start_month=self.fiscal_year_start_month_spin.value(), 
            fiscal_year_start_day=self.fiscal_year_start_day_spin.value(),  
            base_currency=selected_currency_code, 
            tax_id_label=self.tax_id_label_edit.text() or "UEN",       
            date_format=self.date_format_combo.currentText() or "yyyy-MM-dd", 
            logo=None 
        )
        schedule_task_from_qt(self.perform_save_company_settings(dto))

    async def perform_save_company_settings(self, settings_data: CompanySettingData):
        # ... (same as previous perform_save logic, renamed for clarity)
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
                if hasattr(orm_obj_to_save, field_name):
                    setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, by_alias=False, exclude_none=False)
            orm_obj_to_save = CompanySetting(**dict_data) 
            if settings_data.id:
                 orm_obj_to_save.id = settings_data.id

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 

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
            return
        try:
            fy_orms: List[FiscalYear] = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            fy_dtos: List[FiscalYearData] = []
            for fy_orm in fy_orms:
                # Simplified DTO for display, add periods if needed later
                fy_dtos.append(FiscalYearData(
                    id=fy_orm.id,
                    year_name=fy_orm.year_name,
                    start_date=fy_orm.start_date,
                    end_date=fy_orm.end_date,
                    is_closed=fy_orm.is_closed,
                    closed_date=fy_orm.closed_date
                    # periods=[] # Not populating periods list for brevity in this table
                ))
            
            # Pass data as JSON string for thread safety with QMetaObject
            fy_json_data = json.dumps([dto.model_dump_json() for dto in fy_dtos]) # Serialize list of DTO jsons
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
            fy_dto_json_list = json.loads(fy_json_list_str)
            fy_dtos = [FiscalYearData.model_validate_json(fy_json) for fy_json in fy_dto_json_list]
            self.fiscal_year_model.update_data(fy_dtos)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse fiscal year data: {e}")
        except Exception as e_val: # Catch Pydantic validation errors too
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
            await self._load_fiscal_years() # Refresh the list
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Failed to create fiscal year:\n{', '.join(result.errors)}"))
```

**Validation of `app/ui/settings/settings_widget.py` Changes:**
*   Imported `FiscalYearDialog`, `FiscalYearData`, `QGroupBox`, `QTableView`, `QHeaderView`, `QAbstractItemView`, `QStandardItemModel`, `QStandardItem`.
*   Added `FiscalYearTableModel` as a custom table model for displaying `FiscalYearData`.
*   A "Fiscal Year Management" `QGroupBox` is added to the layout.
*   Inside the group box, a `QTableView` (`self.fiscal_years_table`) using `FiscalYearTableModel` is added to display fiscal years.
*   An "Add New Fiscal Year..." button (`self.add_fy_button`) is added.
*   `load_initial_data()` now also calls `_load_fiscal_years()`.
*   `_load_fiscal_years()`: Fetches `FiscalYear` ORM objects, converts them to `FiscalYearData` DTOs, serializes the list of DTOs to JSON, and invokes `_update_fiscal_years_table_slot` via `QMetaObject`.
*   `_update_fiscal_years_table_slot(json_str)`: Deserializes the JSON list of fiscal year DTOs and updates `self.fiscal_year_model`.
*   `on_add_fiscal_year()`: Creates and shows `FiscalYearDialog`. If accepted, it gets `FiscalYearCreateData` and schedules `_perform_add_fiscal_year`.
*   `_perform_add_fiscal_year(dto)`: Calls `self.app_core.fiscal_period_manager.create_fiscal_year_and_periods()`. Displays success/error messages and refreshes the fiscal year list.
*   The company settings fields from the previous step are retained and their save/load logic is now part of `on_save_company_settings` and `perform_save_company_settings`.

---
**3. Update `app/ui/accounting/__init__.py`** (This was done in the previous step, ensuring it's correct)
```python
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog
from .fiscal_year_dialog import FiscalYearDialog 

__all__ = [
    "AccountingWidget", 
    "ChartOfAccountsWidget", 
    "AccountDialog",
    "FiscalYearDialog", 
]
```
This looks correct.

**Next Steps:**

1.  **Create the new file `app/ui/accounting/fiscal_year_dialog.py`** (You provided this in the previous step, ensure it's in place).
2.  **Replace `app/accounting/fiscal_period_manager.py`** with the enhanced version from the previous step.
3.  **Replace `app/services/accounting_services.py`** with the enhanced `FiscalYearService` from the previous step.
4.  **Replace `app/utils/pydantic_models.py`** with the version that includes `FiscalYearCreateData`, `FiscalPeriodData`, and `FiscalYearData`.
5.  **Replace `app/ui/settings/settings_widget.py`** with the new version provided above.
6.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

After these changes, the "Settings" tab should display a new section for "Fiscal Year Management". The "Add New Fiscal Year..." button should launch the dialog, and upon successful submission, a new fiscal year (and its periods, if selected) should be created and appear in the list.

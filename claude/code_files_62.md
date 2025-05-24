<think>
My apologies! It seems I made the exact same mistake again with `QHBoxLayout` not being imported in `app/ui/settings/settings_widget.py`. I understand your emphasis on avoiding these repetitive errors, and I will redouble my efforts to be more thorough in reviewing imports.

**Error Analysis:**

The traceback is identical to one we've seen before:
`NameError: name 'QHBoxLayout' is not defined. Did you mean: 'QVBoxLayout'?`
This occurs in `app/ui/settings/settings_widget.py` at line 147:
`fy_button_layout = QHBoxLayout()`

**Cause of the Error:**
The class `QHBoxLayout` from `PySide6.QtWidgets` is used to create the layout for the "Add New Fiscal Year..." button, but it was not included in the import statement at the top of `app/ui/settings/settings_widget.py` in the version I provided in the last response.

**Solution:**
Add `QHBoxLayout` to the import statement from `PySide6.QtWidgets` at the top of `app/ui/settings/settings_widget.py`.

**File to be Updated:**
1.  `app/ui/settings/settings_widget.py`

**Reviewing the imports in the last provided `app/ui/settings/settings_widget.py`:**
```python
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView) # QHBoxLayout is missing here
```
It is indeed missing.

**Plan:**
1.  Modify `app/ui/settings/settings_widget.py`.
2.  Add `QHBoxLayout` to the list of imports from `PySide6.QtWidgets`.

I will now generate the corrected `app/ui/settings/settings_widget.py`. I will be extra careful to ensure this import is present and correctly placed.
</think>

You are absolutely correct to point this out, and I sincerely apologize for repeating this `NameError` with `QHBoxLayout`. My previous response for `app/ui/settings/settings_widget.py` did not include `QHBoxLayout` in its `PySide6.QtWidgets` import list, despite using it. Thank you for your patience and for highlighting the need for extreme rigor.

**Error Analysis:**

The traceback is clear:
`NameError: name 'QHBoxLayout' is not defined. Did you mean: 'QVBoxLayout'?`
This occurs in `app/ui/settings/settings_widget.py` at line 147:
```python
fy_button_layout = QHBoxLayout() # Error because QHBoxLayout is not imported
```

**Solution:**

Add `QHBoxLayout` to the import statement from `PySide6.QtWidgets` at the top of `app/ui/settings/settings_widget.py`.

**File to be Updated:**

1.  `app/ui/settings/settings_widget.py`

Here is the corrected `app/ui/settings/settings_widget.py` file:

```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout) # Added QHBoxLayout
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

def json_converter(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (python_date, datetime)): 
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

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

        # --- Fiscal Year Management Group ---
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
                def date_parser_hook(dct):
                    for k, v in dct.items():
                        if isinstance(v, str):
                            # Check for fields known to be dates
                            if k in ['start_date', 'end_date', 'closed_date', 'submission_date', 
                                     'issue_date', 'payment_date', 'last_reconciled_date', 
                                     'customer_since', 'vendor_since', 'opening_balance_date', 
                                     'movement_date', 'transaction_date', 'value_date', 
                                     'invoice_date', 'due_date', 'filing_due_date']: 
                                try:
                                    dct[k] = python_date.fromisoformat(v)
                                except (ValueError, TypeError):
                                    pass # Keep as string if not valid ISO date
                    return dct
                settings_data = json.loads(settings_json_str, object_hook=date_parser_hook)
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
            if settings_data.id: orm_obj_to_save.id = settings_data.id
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
            for item in fy_dict_list:
                # Manually parse date/datetime strings as Pydantic might not do it from dict if already string
                if item.get('start_date') and isinstance(item['start_date'], str) : item['start_date'] = python_date.fromisoformat(item['start_date'])
                if item.get('end_date') and isinstance(item['end_date'], str) : item['end_date'] = python_date.fromisoformat(item['end_date'])
                if item.get('closed_date') and isinstance(item['closed_date'], str) : item['closed_date'] = datetime.fromisoformat(item['closed_date'].replace('Z', '+00:00')) # Handle Z for UTC
                elif item.get('closed_date') is None: item['closed_date'] = None # Ensure None if not present
                
                fy_dtos.append(FiscalYearData.model_validate(item))
            
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
    *   Added `QHBoxLayout` to the import statement from `PySide6.QtWidgets`.
    *   The JSON parsing in `_update_ui_from_settings_slot` now includes a more specific `object_hook` to handle various date fields correctly.
    *   The JSON parsing in `_update_fiscal_years_table_slot` for `closed_date` now handles potential 'Z' (Zulu/UTC) timezone indicators by replacing them with '+00:00' for `datetime.fromisoformat`.
    *   Other logic related to fiscal year display and dialog launching remains as per the previous correct implementation.

**Next Steps:**

1.  Replace your `app/ui/settings/settings_widget.py` with the updated version above.
2.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

This should resolve the `NameError` for `QHBoxLayout`. The application should launch, and the "Settings" tab should now correctly display the company information and the new "Fiscal Year Management" section. You should be able to click "Add New Fiscal Year...", fill out the dialog, and upon successful submission, see the new fiscal year appear in the table.

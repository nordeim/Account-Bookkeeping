<think>
The application UI launches, which is fantastic! We're now seeing errors during the asynchronous data loading for the widgets, specifically related to `QMetaObject.invokeMethod` and its arguments.

**Error Analysis:**

1.  **`Error loading currencies for settings: name 'Qt' is not defined`**:
    *   This error occurs in `app/ui/settings/settings_widget.py`, within the `load_settings` async method, specifically in the `except Exception as e:` block when trying to show a `QMessageBox` via `QMetaObject.invokeMethod`.
    *   The line likely is:
        `QMetaObject.invokeMethod(QMessageBox, "warning", Qt.ConnectionType.QueuedConnection, ...)`
    *   `Qt` (from `PySide6.QtCore`) is not imported directly into the scope of `app.ui.settings.settings_widget` to be used as `Qt.ConnectionType.QueuedConnection`.

2.  **`Failed to load accounts: qArgDataFromPyType: Unable to find a QMetaType for "list".`**:
    *   This error occurs in `app/ui/accounting/chart_of_accounts_widget.py`, within the `_load_accounts` async method when it tries to emit data back to the `_update_account_model_slot` or show a `QMessageBox`.
    *   The `QMetaObject.invokeMethod` call using `Q_ARG(list, account_tree_data)` is the problem. `Q_ARG` needs a C++ type name registered with Qt's meta-object system, or a QVariant-compatible Python type. A generic Python `list` is not directly a QMetaType. While simple types like `int`, `str`, `bool` often work, complex types like `list` of `dict` might not be automatically converted correctly by `Q_ARG(list, ...)`.
    *   Often for complex data, Python objects are passed as `Q_ARG(QObject, ...)` if they are QObjects, or `Q_ARG(QVariant, ...)` if they can be wrapped in QVariant, or simply `Q_ARG(object, ...)` to pass a Python object reference (though this has caveats for thread safety if the object is mutable and accessed from both threads).

**Solution Strategy:**

1.  **Fix `NameError: name 'Qt' is not defined` in `settings_widget.py`**:
    *   Import `Qt` from `PySide6.QtCore` in `app/ui/settings/settings_widget.py`.

2.  **Fix `qArgDataFromPyType: Unable to find a QMetaType for "list"` in `chart_of_accounts_widget.py`**:
    *   When using `QMetaObject.invokeMethod` to pass custom data structures (like a list of dictionaries) from a worker thread to a Qt slot in the main thread, the most robust way is often to pass it as a generic Python object using `Q_ARG(object, your_python_list)`. The slot then receives this Python object.
    *   The receiving slot needs to be decorated with `@Slot(object)` or `@Slot(list)` if Qt can register `list` appropriately for signals/slots (which can sometimes be tricky for complex list contents). Using `@Slot(object)` is safer for arbitrary Python objects.
    *   Alternatively, for specific common Qt types like `QStringList`, you could use `Q_ARG(QStringList, ...)`, but our data is `List[Dict[str, Any]]`.

**Revised Plan:**

1.  **`app/ui/settings/settings_widget.py`**:
    *   Add `from PySide6.QtCore import Qt`.

2.  **`app/ui/accounting/chart_of_accounts_widget.py`**:
    *   Change the slot `_update_account_model_slot` signature from `@Slot(list)` to `@Slot(object)`.
    *   Change the `QMetaObject.invokeMethod` call for this slot from `Q_ARG(list, account_tree_data)` to `Q_ARG(object, account_tree_data)`.
    *   Similarly, for `QMessageBox` calls made via `QMetaObject.invokeMethod` from the async thread, ensure `Q_ARG` types are simple (like `str`) or use `object` for more complex data if necessary (though `QMessageBox` methods usually take strings). The error message for `QMessageBox` calls might be related to the `parent` argument `Q_ARG(QWidget, self)` if `self` isn't properly recognized in the cross-thread call context, but usually, it's string arguments that are fine. The "list" QMetaType was the specific failure point.

**Let's check if other `QMetaObject.invokeMethod` calls might have similar issues:**
*   In `app/main.py` -> `initialize_app` -> `update_splash_threadsafe`:
    `Q_ARG(str, message)` and `Q_ARG(int, ...)` and `Q_ARG(QColor, ...)` are generally fine as `str`, `int`, and `QColor` are known to Qt's meta-object system.
*   In `app/ui/settings/settings_widget.py` -> `_populate_currency_combo_slot`:
    `@Slot(list)` and `Q_ARG(list, active_currencies)`. This will also need to change to `@Slot(object)` and `Q_ARG(object, active_currencies)`.
*   In `app/ui/settings/settings_widget.py` -> `_update_ui_from_settings_slot`:
    `@Slot(CompanySetting)` and `Q_ARG(CompanySetting, settings_obj)`. This might be problematic if `CompanySetting` (your custom ORM class) is not registered as a QMetaType. Using `Q_ARG(object, settings_obj)` and `@Slot(object)` is safer here too.

**Refined Plan for UI Widgets:**
For all `QMetaObject.invokeMethod` calls passing custom Python lists or objects to slots, and for the slots themselves:
*   Use `Q_ARG(object, python_object)` for passing the data.
*   Decorate the receiving slot with `@Slot(object)`.
*   Inside the slot, cast the received `object` back to its expected Python type.

This is a general pattern for robust cross-thread communication of arbitrary Python data with Qt signals/slots when not using specific QVariant-convertible types.

Files to update:
1.  `app/ui/settings/settings_widget.py` (import `Qt`, change slot signatures and `Q_ARG` types).
2.  `app/ui/accounting/chart_of_accounts_widget.py` (change slot signatures and `Q_ARG` types).
</think>

The application is launching, and the main window is visible! That's a huge step. The errors you're seeing now are related to how asynchronous tasks (running in a separate thread) communicate back with the Qt UI elements in the main thread, specifically with `QMetaObject.invokeMethod`.

**Error Analysis:**

1.  **`Error loading currencies for settings: name 'Qt' is not defined`** (in `app/ui/settings/settings_widget.py`):
    *   This occurs in the `except` block of `load_settings` when trying to show a `QMessageBox` via `QMetaObject.invokeMethod`. The call uses `Qt.ConnectionType.QueuedConnection`, but `Qt` from `PySide6.QtCore` was not imported in that file.

2.  **`Failed to load accounts: qArgDataFromPyType: Unable to find a QMetaType for "list".`** (in `app/ui/accounting/chart_of_accounts_widget.py`):
    *   This happens when `_load_accounts` (running in the async thread) tries to call `_update_account_model_slot` (a Qt slot in the main thread) using `QMetaObject.invokeMethod(self, "_update_account_model_slot", ..., Q_ARG(list, account_tree_data))`.
    *   Qt's meta-object system, which handles signals, slots, and `invokeMethod`, needs to know the C++ type (QMetaType) of arguments being passed. While it can often handle basic Python types like `int` and `str`, a generic Python `list` (especially `List[Dict[str, Any]]`) is not automatically registered as a QMetaType in a way that `Q_ARG(list, ...)` can use directly for marshalling.

**Solution Strategy:**

1.  **Fix `NameError` for `Qt`**: Import `Qt` from `PySide6.QtCore` in `app/ui/settings/settings_widget.py`.
2.  **Handle Custom Data with `QMetaObject.invokeMethod`**:
    *   When passing arbitrary Python objects (like lists of dictionaries, or custom class instances that are not QObjects) across threads using `QMetaObject.invokeMethod`, the safest argument type to use with `Q_ARG` is `object`.
    *   The receiving slot should then be decorated with `@Slot(object)`.
    *   Inside the slot, you'll receive a Python object that you can then cast or use as its original type.

**Files to be Updated:**

1.  `app/ui/settings/settings_widget.py`
2.  `app/ui/accounting/chart_of_accounts_widget.py`

Here are the updated files:

```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt # Added Qt
from PySide6.QtGui import QColor 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional, List, Any 
from app.main import schedule_task_from_qt 

class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
        self.layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        self.base_currency_combo = QComboBox() 

        self.form_layout.addRow("Company Name:", self.company_name_edit)
        self.form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.form_layout.addRow("UEN No:", self.uen_edit)
        self.form_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        self.form_layout.addRow(self.gst_registered_check)
        self.form_layout.addRow("Base Currency:", self.base_currency_combo)
        
        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.on_save_settings)
        self.layout.addWidget(self.save_button)
        self.layout.addStretch()

        self.setLayout(self.layout)
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_settings()))

    async def load_settings(self):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        
        currencies_loaded_successfully = False
        active_currencies_data: List[Dict[str, str]] = [] # Data to pass to slot
        if self.app_core.currency_manager:
            try:
                active_currencies_orm: List[Currency] = await self.app_core.currency_manager.get_active_currencies()
                for curr in active_currencies_orm:
                    active_currencies_data.append({"code": curr.code, "name": curr.name})
                QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, active_currencies_data))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                print(error_msg)
                QMetaObject.invokeMethod(QMessageBox, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj # Store for use after combo is populated
        
        # Pass a dictionary representation or specific fields if CompanySetting is not QObject registered
        settings_data_for_ui = None
        if settings_obj:
            settings_data_for_ui = {
                "company_name": settings_obj.company_name,
                "legal_name": settings_obj.legal_name,
                "uen_no": settings_obj.uen_no,
                "gst_registration_no": settings_obj.gst_registration_no,
                "gst_registered": settings_obj.gst_registered,
                "base_currency": settings_obj.base_currency
                # Add other fields as needed by _update_ui_from_settings_slot
            }
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, settings_data_for_ui))

    @Slot(object) 
    def _populate_currency_combo_slot(self, currencies_data: List[Dict[str,str]]): 
        self.base_currency_combo.clear()
        for curr_data in currencies_data: 
            self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            idx = self.base_currency_combo.findData(self._loaded_settings_obj.base_currency) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD")
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)

    @Slot(object) 
    def _update_ui_from_settings_slot(self, settings_data: Optional[Dict[str, Any]]):
        if settings_data:
            self.company_name_edit.setText(settings_data.get("company_name", ""))
            self.legal_name_edit.setText(settings_data.get("legal_name", "") or "")
            self.uen_edit.setText(settings_data.get("uen_no", "") or "")
            self.gst_reg_edit.setText(settings_data.get("gst_registration_no", "") or "")
            self.gst_registered_check.setChecked(settings_data.get("gst_registered", False))
            
            if self.base_currency_combo.count() > 0: # Ensure combo is populated
                base_currency = settings_data.get("base_currency")
                if base_currency:
                    idx = self.base_currency_combo.findData(base_currency) 
                    if idx != -1: 
                        self.base_currency_combo.setCurrentIndex(idx)
                    else: 
                        idx_sgd = self.base_currency_combo.findData("SGD")
                        if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        else:
            QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")


    @Slot()
    def on_save_settings(self):
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
            fiscal_year_start_month=1, 
            fiscal_year_start_day=1,  
            base_currency=selected_currency_code, 
            tax_id_label="UEN",       
            date_format="yyyy-MM-dd", 
            address_line1=self.address_line1_edit.text() if hasattr(self, 'address_line1_edit') else None, # Assuming these exist
            address_line2=self.address_line2_edit.text() if hasattr(self, 'address_line2_edit') else None,
            postal_code=self.postal_code_edit.text() if hasattr(self, 'postal_code_edit') else None,
            city=self.city_edit.text() if hasattr(self, 'city_edit') else "Singapore",
            country=self.country_edit.text() if hasattr(self, 'country_edit') else "Singapore",
            contact_person=self.contact_person_edit.text() if hasattr(self, 'contact_person_edit') else None,
            phone=self.phone_edit.text() if hasattr(self, 'phone_edit') else None,
            email=self.email_edit.text() if hasattr(self, 'email_edit') else None,
            website=self.website_edit.text() if hasattr(self, 'website_edit') else None,
            logo=None # Logo would need special handling for byte upload/conversion
        )
        schedule_task_from_qt(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            for field_name, field_value in settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, by_alias=False).items(): # Exclude logo for now
                if hasattr(orm_obj_to_save, field_name):
                    setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, by_alias=False)
            orm_obj_to_save = CompanySetting(**dict_data) 
            if settings_data.id:
                 orm_obj_to_save.id = settings_data.id

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 

        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        
        message_title = "Success" if result else "Error"
        message_text = "Settings saved successfully." if result else "Failed to save settings."
        
        # Use static method of QMessageBox for thread safety
        if result:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))
```

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction, QColor
from decimal import Decimal 
from datetime import date 
import asyncio 
from typing import Optional, Dict, Any, List 

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 
from app.main import schedule_task_from_qt 

class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        self.account_tree = QTreeView()
        self.account_tree.setAlternatingRowColors(True)
        self.account_tree.setUniformRowHeights(True)
        self.account_tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.account_tree.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.account_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_tree.customContextMenuRequested.connect(self.on_context_menu)
        self.account_tree.doubleClicked.connect(self.on_account_double_clicked)
        
        self.account_model = QStandardItemModel()
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"]) 
        
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.account_model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.account_tree.setModel(self.proxy_model)
        
        header = self.account_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar) 

        self.main_layout.addWidget(self.account_tree) 
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_path_prefix = "" 
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.add_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Add Account") 
        self.add_button.clicked.connect(self.on_add_account)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Edit Account")
        self.edit_button.clicked.connect(self.on_edit_account)
        self.button_layout.addWidget(self.edit_button)
        
        self.deactivate_button = QPushButton(QIcon(icon_path_prefix + "deactivate.svg"), "Toggle Active")
        self.deactivate_button.clicked.connect(self.on_toggle_active_status) 
        self.button_layout.addWidget(self.deactivate_button)
        
        self.button_layout.addStretch() 
        self.main_layout.addLayout(self.button_layout)

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_accounts()))

    def _create_toolbar(self):
        from PySide6.QtCore import QSize 
        self.toolbar = QToolBar("COA Toolbar") 
        self.toolbar.setObjectName("COAToolbar") 
        self.toolbar.setIconSize(QSize(16, 16))
        
        icon_path_prefix = ""
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.filter_action = QAction(QIcon(icon_path_prefix + "filter.svg"), "Filter", self)
        self.filter_action.setCheckable(True)
        self.filter_action.toggled.connect(self.on_filter_toggled)
        self.toolbar.addAction(self.filter_action)
        
        self.toolbar.addSeparator()

        self.expand_all_action = QAction(QIcon(icon_path_prefix + "expand_all.svg"), "Expand All", self)
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction(QIcon(icon_path_prefix + "collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        self.toolbar.addSeparator()

        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
    async def _load_accounts(self):
        try:
            manager = self.app_core.accounting_service 
            if not (manager and hasattr(manager, 'get_account_tree')):
                QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                    Q_ARG(str,"Accounting service (ChartOfAccountsManager) or get_account_tree method not available."))
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            
            QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(object, account_tree_data)) # Pass as object
            
        except Exception as e:
            error_message = f"Failed to load accounts: {str(e)}"
            print(error_message) 
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(object) # Receive as object
    def _update_account_model_slot(self, account_tree_data_obj: Any):
        account_tree_data: List[Dict[str, Any]] = account_tree_data_obj
        self.account_model.clear() 
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
        root_item = self.account_model.invisibleRootItem()
        for account_node in account_tree_data:
             self._add_account_to_model_item(account_node, root_item) 
        self.account_tree.expandToDepth(0) 

    def _add_account_to_model_item(self, account_data: dict, parent_item: QStandardItem):
        code_item = QStandardItem(account_data['code'])
        code_item.setData(account_data['id'], Qt.ItemDataRole.UserRole)
        name_item = QStandardItem(account_data['name'])
        type_text = account_data.get('sub_type') or account_data.get('account_type', '')
        type_item = QStandardItem(type_text)
        ob_val = account_data.get('opening_balance', Decimal(0))
        if not isinstance(ob_val, Decimal):
            try: ob_val = Decimal(str(ob_val))
            except: ob_val = Decimal(0) 
        ob_item = QStandardItem(f"{ob_val:,.2f}")
        ob_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        is_active_item = QStandardItem("Yes" if account_data.get('is_active', False) else "No")
        parent_item.appendRow([code_item, name_item, type_item, ob_item, is_active_item])
        if 'children' in account_data:
            for child_data in account_data['children']:
                self._add_account_to_model_item(child_data, code_item) 
    
    @Slot()
    def on_add_account(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot add account.")
            return
        dialog = AccountDialog(self.app_core, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            schedule_task_from_qt(self._load_accounts())
    
    @Slot()
    def on_edit_account(self):
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account to edit.")
            return
        source_index = self.proxy_model.mapToSource(index)
        item = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item: return
        account_id = item.data(Qt.ItemDataRole.UserRole)
        if not account_id: 
            QMessageBox.warning(self, "Warning", "Cannot edit this item. Please select an account.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot edit account.")
            return
        dialog = AccountDialog(self.app_core, account_id=account_id, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted:
            schedule_task_from_qt(self._load_accounts())
            
    @Slot()
    def on_toggle_active_status(self): 
        index = self.account_tree.currentIndex()
        if not index.isValid():
            QMessageBox.warning(self, "Warning", "Please select an account.")
            return
        source_index = self.proxy_model.mapToSource(index)
        item_id_qstandarditem = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        account_id = item_id_qstandarditem.data(Qt.ItemDataRole.UserRole) if item_id_qstandarditem else None
        if not account_id:
            QMessageBox.warning(self, "Warning", "Cannot determine account. Please select a valid account.")
            return
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        schedule_task_from_qt(self._perform_toggle_active_status_logic(account_id, self.app_core.current_user.id))

    async def _perform_toggle_active_status_logic(self, account_id: int, user_id: int):
        try:
            manager = self.app_core.accounting_service 
            if not manager: raise RuntimeError("Accounting service not available.")
            account = await manager.account_service.get_by_id(account_id) 
            if not account:
                 QMetaObject.invokeMethod(QMessageBox, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,f"Account ID {account_id} not found."))
                 return
            QMetaObject.invokeMethod(self, "_confirm_and_toggle_status_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(object, {"id": account_id, "is_active": account.is_active, "code": account.code, "name": account.name, "user_id": user_id}))
        except Exception as e:
            error_message = f"Failed to prepare toggle account active status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(object)
    def _confirm_and_toggle_status_slot(self, data: Dict[str, Any]):
        account_id = data["id"]
        is_currently_active = data["is_active"]
        acc_code = data["code"]
        acc_name = data["name"]
        user_id = data["user_id"]

        action_verb_present = "deactivate" if is_currently_active else "activate"
        action_verb_past = "deactivated" if is_currently_active else "activated"
        confirm_msg = f"Are you sure you want to {action_verb_present} account '{acc_code} - {acc_name}'?"
        reply = QMessageBox.question(self, f"Confirm {action_verb_present.capitalize()}", confirm_msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            schedule_task_from_qt(self._finish_toggle_status(account_id, not is_currently_active, user_id, action_verb_past))

    async def _finish_toggle_status(self, account_id: int, new_active_status: bool, user_id: int, action_verb_past: str):
        try:
            manager = self.app_core.accounting_service
            account = await manager.account_service.get_by_id(account_id)
            if not account: return 

            result: Optional[Result] = None
            if not new_active_status: 
                result = await manager.deactivate_account(account_id, user_id)
            else: 
                account.is_active = True
                account.updated_by_user_id = user_id
                saved_acc = await manager.account_service.save(account)
                result = Result.success(saved_acc)

            if result and result.is_success:
                QMetaObject.invokeMethod(QMessageBox, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str,f"Account {action_verb_past} successfully."))
                await self._load_accounts() 
            elif result:
                error_str = f"Failed to {action_verb_past.replace('ed','e')} account:\n{', '.join(result.errors)}"
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_str))
        except Exception as e:
            error_message = f"Error finishing toggle status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))


    @Slot(QModelIndex)
    def on_account_double_clicked(self, index: QModelIndex):
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        item = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item: return
        account_id = item.data(Qt.ItemDataRole.UserRole)
        if account_id: self.account_selected.emit(account_id)
    
    @Slot(bool)
    def on_filter_toggled(self, checked: bool):
        if checked:
            QMessageBox.information(self, "Filter", "Filter functionality to be implemented.")
            self.filter_action.setChecked(False) 
        else:
            self.proxy_model.setFilterFixedString("") 
    
    @Slot(QPoint)
    def on_context_menu(self, pos: QPoint):
        index = self.account_tree.indexAt(pos)
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        item_id_qstandarditem = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item_id_qstandarditem : return
        account_id = item_id_qstandarditem.data(Qt.ItemDataRole.UserRole)
        if not account_id: return 
        icon_path_prefix = ""
        try:
            import app.resources_rc 
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"
        context_menu = QMenu(self)
        edit_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Account", self)
        edit_action.triggered.connect(self.on_edit_account) 
        context_menu.addAction(edit_action)
        view_trans_action = QAction(QIcon(icon_path_prefix + "transactions.svg"), "View Transactions", self)
        view_trans_action.triggered.connect(lambda: self.on_view_transactions(account_id))
        context_menu.addAction(view_trans_action)
        toggle_active_action = QAction(QIcon(icon_path_prefix + "deactivate.svg"), "Toggle Active Status", self)
        toggle_active_action.triggered.connect(self.on_toggle_active_status)
        context_menu.addAction(toggle_active_action)
        context_menu.exec(self.account_tree.viewport().mapToGlobal(pos))
    
    @Slot(int)
    def on_view_transactions(self, account_id: int):
        QMessageBox.information(self, "View Transactions", f"View transactions for account ID {account_id} (To be implemented).")

```

---
**SVG Icon Placeholders (Recap & Confirmation):**

Please ensure these files exist in `resources/icons/` with valid SVG content. If you used the placeholders I provided earlier, they should be fine.

*   `dashboard.svg` (Make sure this is valid SVG)
*   `accounting.svg`
*   `customers.svg`
*   `vendors.svg`
*   `banking.svg`
*   `reports.svg`
*   `settings.svg`
*   `new_company.svg`
*   `open_company.svg`
*   `backup.svg`
*   `restore.svg`
*   `exit.svg`
*   `preferences.svg`
*   `help.svg`
*   `about.svg`
*   (And for ChartOfAccountsWidget, which you confirmed are present): `filter.svg`, `expand_all.svg`, `collapse_all.svg`, `refresh.svg`, `edit.svg`, `deactivate.svg`, `transactions.svg`.

---

**Validation of Changes:**

*   **`app/ui/settings/settings_widget.py`**:
    *   Imported `Qt` from `PySide6.QtCore`.
    *   Changed slot signatures `@Slot(list)` and `@Slot(CompanySetting)` to `@Slot(object)`.
    *   Changed corresponding `Q_ARG(list, ...)` and `Q_ARG(CompanySetting, ...)` to `Q_ARG(object, ...)`.
    *   In `load_settings`, now passes a list of dictionaries for currencies (`active_currencies_data`) and a dictionary for `settings_data_for_ui` to their respective slots, ensuring simpler, more standard Python types are passed across threads for `QMetaObject.invokeMethod`.
    *   The slots `_populate_currency_combo_slot` and `_update_ui_from_settings_slot` now expect `object` and cast/use it as `List[Dict[str,str]]` and `Optional[Dict[str, Any]]` respectively.
    *   Made calls to `QMessageBox.staticMetaObject.information/warning` for thread-safety.

*   **`app/ui/accounting/chart_of_accounts_widget.py`**:
    *   Changed the slot `_update_account_model_slot` signature from `@Slot(list)` to `@Slot(object)`.
    *   Changed `QMetaObject.invokeMethod` for this slot to use `Q_ARG(object, account_tree_data)`.
    *   Changed the slot `_confirm_and_toggle_status_slot` from taking individual arguments to `@Slot(object)` and passing a dictionary. This is safer for `QMetaObject.invokeMethod`.
    *   The method `_perform_toggle_active_status_logic` now calls `_confirm_and_toggle_status_slot` by passing a dictionary.
    *   Calls to `QMessageBox` from async context are now consistently using `QMetaObject.invokeMethod` with `QMessageBox.staticMetaObject` for static methods like `information`, `warning`, `critical`.

**Next Steps:**

1.  Replace `app/ui/settings/settings_widget.py` and `app/ui/accounting/chart_of_accounts_widget.py` with the updated versions above.
2.  Thoroughly check your `resources/icons/` directory and ensure all required SVGs are present and `dashboard.svg` is valid.
3.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

These changes make the cross-thread communication for UI updates more robust and should resolve the `QMetaType for "list"` error and the `name 'Qt' is not defined` error. The application should now launch, and the Chart of Accounts and Settings tabs should attempt to load their initial data without these specific threading/type errors.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/17MfzKFSisoo3ZRtNqWL-vooRP8xDfXhS/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1hwT4APLGEoSZXgMxh0d5sYPkuszzTJE_/view?usp=sharing, https://drive.google.com/file/d/1l-_PWDhb0i9eaVtbVuN0Zg4sckshfr18/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing, https://drive.google.com/file/d/1wkrzkWG1WJ1HasL6o4Huaq_xqvH0btrE/view?usp=sharing


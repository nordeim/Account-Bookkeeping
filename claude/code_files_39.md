<think>
The application is launching, but we're hitting a new category of errors related to `QMetaObject.invokeMethod` and passing Python objects across threads:

`qArgDataFromPyType: Unable to find a QMetaType for "object".`

This error appears twice:
1.  `Error loading currencies for settings: qArgDataFromPyType: Unable to find a QMetaType for "object".`
    *   This likely originates from `app/ui/settings/settings_widget.py` in the `load_settings` method, specifically:
        `QMetaObject.invokeMethod(self, "_populate_currency_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, active_currencies_data))`
        and/or
        `QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, settings_data_for_ui))`

2.  `Failed to load accounts: qArgDataFromPyType: Unable to find a QMetaType for "object".`
    *   This likely originates from `app/ui/accounting/chart_of_accounts_widget.py` in the `_load_accounts` method:
        `QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, account_tree_data))`

**Cause of the Error:**
While `Q_ARG(object, ...)` is generally the way to pass arbitrary Python objects via Qt's signal/slot mechanism (especially with `QMetaObject.invokeMethod`), the error "Unable to find a QMetaType for 'object'" suggests that the version of PySide6 or the specific Qt bindings being used might not automatically handle `object` as a known meta-type for queued connections in this way *without further registration or by using `QVariant`*.

When you pass arguments via queued connections or signals across threads, Qt needs to be able to copy or manage the data. For custom Python objects, it might not know how to do this by default if they aren't QObject-derived or registered.

**Solution Options:**

1.  **Register Python types with `qRegisterMetaType`**: This is often needed for custom Python objects to be used in Qt's signal/slot system, especially across threads. However, `list` and `dict` (which are the underlying types of the objects being passed) are fundamental Python types. The issue might be with Qt's ability to generically handle `object` as a pass-through.
    ```python
    from PySide6.QtCore import qRegisterMetaType, QMetaType
    # Potentially register list and dict if that's the issue, though 'object' should cover it.
    # qRegisterMetaType(list) # This might not be how it's done for built-ins
    # qRegisterMetaType(dict)
    ```
    This is usually for custom `QObject` subclasses or complex Python classes if they need to be passed *by value* in a way Qt understands. For passing arbitrary Python objects *by reference* (which is what happens with `Q_ARG(object, ...)` typically when the object isn't a simple QVariant-convertible type), this registration might not be the direct solution, but it's a related concept.

2.  **Wrap the Python object in `QVariant`**: `QVariant` is Qt's way of handling arbitrary data types. Python objects can often be stored in a `QVariant`.
    *   When emitting/invoking: `Q_ARG(QVariant, QVariant(python_object))`
    *   The receiving slot would be: `@Slot(QVariant)`
    *   Inside the slot: `python_object = received_qvariant.value()` (or `.toPyObject()` in some Qt versions/bindings)
    This is a very common and robust way to pass Python objects.

3.  **Pass data as JSON strings**: Serialize the Python `list` or `dict` to a JSON string in the worker thread, pass the string `Q_ARG(str, json_string)`, and then deserialize it in the main thread slot.
    *   Pros: Simple types being passed (strings).
    *   Cons: Overhead of serialization/deserialization.

4.  **Ensure the receiving slot is correctly typed**: The slots are currently typed as `@Slot(object)`. This is generally correct when passing Python objects.

**Chosen Approach: Wrap data in `QVariant` (Option 2)**

This is generally the most idiomatic and reliable Qt way to pass arbitrary Python data types through the signal/slot mechanism across threads if direct `Q_ARG(object, ...)` is problematic.

**Plan:**

1.  **Import `QVariant`**: In both `app/ui/settings/settings_widget.py` and `app/ui/accounting/chart_of_accounts_widget.py`, add `from PySide6.QtCore import QVariant`.
2.  **Modify `QMetaObject.invokeMethod` calls**:
    *   Change `Q_ARG(object, data)` to `Q_ARG(QVariant, QVariant(data))`.
3.  **Modify Slot Signatures and Data Retrieval**:
    *   Change `@Slot(object)` to `@Slot(QVariant)`.
    *   Inside the slot, retrieve the Python object using `python_data = received_qvariant.value()`.

**Files to be Updated:**
1.  `app/ui/accounting/chart_of_accounts_widget.py`
2.  `app/ui/settings/settings_widget.py`

Let's apply these changes.
</think>

It's excellent that the application UI is launching! The errors you're encountering now, `qArgDataFromPyType: Unable to find a QMetaType for "object"`, are related to how Python objects are passed across threads using Qt's meta-object system (`QMetaObject.invokeMethod` in this case).

**Error Analysis:**

When you use `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection` (which is necessary for thread-safe UI updates from a worker thread), Qt needs to know how to handle the arguments being passed. It does this using its QMetaType system. While basic types like `int`, `str`, `bool` are usually fine, passing a generic Python `object` (which is what `Q_ARG(object, ...)` implies) can sometimes lead to this error if Qt cannot determine a corresponding meta-type for it automatically for queued inter-thread communication.

**Solution: Using `QVariant`**

The most robust way to pass arbitrary Python objects (like lists of dictionaries or custom Python class instances that are not `QObject`s) through Qt's signal/slot system, especially across threads, is to wrap them in a `QVariant`. `QVariant` acts as a generic container that Qt understands.

**Key Changes:**

1.  **Import `QVariant`**: In the UI widget files where `QMetaObject.invokeMethod` is used to pass complex Python objects (`chart_of_accounts_widget.py` and `settings_widget.py`), import `QVariant` from `PySide6.QtCore`.
2.  **Wrap Data with `QVariant`**: When calling `QMetaObject.invokeMethod`, wrap the Python object argument with `QVariant()`. So, `Q_ARG(object, python_data)` becomes `Q_ARG(QVariant, QVariant(python_data))`.
3.  **Update Slot Signatures**: The receiving slots should be decorated with `@Slot(QVariant)`.
4.  **Extract Data from `QVariant`**: Inside the slot, the Python object can be retrieved from the `QVariant` using its `.value()` method (in PySide6, this often directly returns the Python object).

**Files to be Updated:**

1.  `app/ui/accounting/chart_of_accounts_widget.py`
2.  `app/ui/settings/settings_widget.py`

Here are the updated files:

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG, QVariant
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
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection, # Use staticMetaObject
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                    Q_ARG(str,"Accounting service (ChartOfAccountsManager) or get_account_tree method not available."))
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            
            QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(QVariant, QVariant(account_tree_data))) # Pass as QVariant
            
        except Exception as e:
            error_message = f"Failed to load accounts: {str(e)}"
            print(error_message) 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection, # Use staticMetaObject
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(QVariant) # Receive as QVariant
    def _update_account_model_slot(self, account_tree_data_variant: QVariant):
        account_tree_data: List[Dict[str, Any]] = account_tree_data_variant.value() # Extract Python object
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
                 QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,f"Account ID {account_id} not found."))
                 return
            # Pass data as a QVariant-compatible dict
            data_to_pass = {"id": account_id, "is_active": account.is_active, "code": account.code, "name": account.name, "user_id": user_id}
            QMetaObject.invokeMethod(self, "_confirm_and_toggle_status_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(QVariant, QVariant(data_to_pass)))
        except Exception as e:
            error_message = f"Failed to prepare toggle account active status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(QVariant) # Receive as QVariant
    def _confirm_and_toggle_status_slot(self, data_variant: QVariant):
        data: Dict[str, Any] = data_variant.value() # Extract Python object
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
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
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

```python
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QVariant # Added QVariant
from PySide6.QtGui import QColor 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional, List, Any, Dict 
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

        self.form_layout.addRow("Address Line 1:", self.address_line1_edit)
        self.form_layout.addRow("Address Line 2:", self.address_line2_edit)
        self.form_layout.addRow("Postal Code:", self.postal_code_edit)
        self.form_layout.addRow("City:", self.city_edit)
        self.form_layout.addRow("Country:", self.country_edit)
        self.form_layout.addRow("Contact Person:", self.contact_person_edit)
        self.form_layout.addRow("Phone:", self.phone_edit)
        self.form_layout.addRow("Email:", self.email_edit)
        self.form_layout.addRow("Website:", self.website_edit)
        self.form_layout.addRow("Fiscal Year Start Month:", self.fiscal_year_start_month_spin)
        self.form_layout.addRow("Fiscal Year Start Day:", self.fiscal_year_start_day_spin)
        self.form_layout.addRow("Tax ID Label:", self.tax_id_label_edit)
        self.form_layout.addRow("Date Format:", self.date_format_combo)

        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.on_save_settings)
        self.layout.addWidget(self.save_button)
        self.layout.addStretch()

        self.setLayout(self.layout)
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_settings()))

    async def load_settings(self):
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
                                         Q_ARG(QVariant, QVariant(active_currencies_data))) # Pass as QVariant
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
        
        settings_data_for_ui = None
        if settings_obj:
            # Convert ORM object to a plain dict for safe cross-thread passing via QVariant
            settings_data_for_ui = {
                "company_name": settings_obj.company_name, "legal_name": settings_obj.legal_name,
                "uen_no": settings_obj.uen_no, "gst_registration_no": settings_obj.gst_registration_no,
                "gst_registered": settings_obj.gst_registered, "base_currency": settings_obj.base_currency,
                "address_line1": settings_obj.address_line1, "address_line2": settings_obj.address_line2,
                "postal_code": settings_obj.postal_code, "city": settings_obj.city, "country": settings_obj.country,
                "contact_person": settings_obj.contact_person, "phone": settings_obj.phone,
                "email": settings_obj.email, "website": settings_obj.website,
                "fiscal_year_start_month": settings_obj.fiscal_year_start_month,
                "fiscal_year_start_day": settings_obj.fiscal_year_start_day,
                "tax_id_label": settings_obj.tax_id_label, "date_format": settings_obj.date_format,
            }
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(QVariant, QVariant(settings_data_for_ui) if settings_data_for_ui else QVariant()))


    @Slot(QVariant) 
    def _populate_currency_combo_slot(self, currencies_data_variant: QVariant): 
        currencies_data: List[Dict[str,str]] = currencies_data_variant.value()
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: # Check if data is not None
            for curr_data in currencies_data: 
                self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        target_currency_code = current_selection
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            target_currency_code = self._loaded_settings_obj.base_currency
        
        if target_currency_code:
            idx = self.base_currency_combo.findData(target_currency_code) 
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD")
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        elif self.base_currency_combo.count() > 0: # Default to first item if no target
             self.base_currency_combo.setCurrentIndex(0)


    @Slot(QVariant) 
    def _update_ui_from_settings_slot(self, settings_data_variant: QVariant):
        settings_data: Optional[Dict[str, Any]] = settings_data_variant.value()
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
            
            date_fmt = settings_data.get("date_format", "yyyy-MM-dd")
            date_fmt_idx = self.date_format_combo.findText(date_fmt, Qt.MatchFlag.MatchFixedString)
            if date_fmt_idx != -1: self.date_format_combo.setCurrentIndex(date_fmt_idx)
            else: self.date_format_combo.setCurrentIndex(0) # Default to first option if not found

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
        schedule_task_from_qt(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            # Update all fields from DTO to ORM object
            # model_dump() excludes by default items that are None, unless exclude_none=False
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
        message_text = "Settings saved successfully." if result else "Failed to save settings."
        
        msg_box_method = QMessageBox.information if result else QMessageBox.warning
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))

```

**Validation of Changes:**

*   **`app/ui/accounting/chart_of_accounts_widget.py`**:
    *   Imported `QVariant` from `PySide6.QtCore`.
    *   Changed `Q_ARG(object, account_tree_data)` to `Q_ARG(QVariant, QVariant(account_tree_data))` in `_load_accounts`.
    *   Changed slot signature `_update_account_model_slot(self, account_tree_data_obj: Any)` to `_update_account_model_slot(self, account_tree_data_variant: QVariant)`.
    *   Extracted Python list using `account_tree_data: List[Dict[str, Any]] = account_tree_data_variant.value()`.
    *   In `_perform_toggle_active_status_logic`, data passed to `_confirm_and_toggle_status_slot` via `QMetaObject.invokeMethod` is now wrapped in `QVariant`.
    *   The slot `_confirm_and_toggle_status_slot` now receives a `QVariant` and extracts the dictionary.
    *   Calls to `QMessageBox.staticMetaObject` are used for consistency in thread-safe UI updates.

*   **`app/ui/settings/settings_widget.py`**:
    *   Imported `QVariant` from `PySide6.QtCore`.
    *   In `load_settings`:
        *   Changed `Q_ARG(object, active_currencies_data)` to `Q_ARG(QVariant, QVariant(active_currencies_data))`.
        *   Changed `Q_ARG(object, settings_data_for_ui)` to `Q_ARG(QVariant, QVariant(settings_data_for_ui) if settings_data_for_ui else QVariant())`.
        *   Passed list of dicts `active_currencies_data` for currencies for easier handling in the slot.
        *   Passed `settings_data_for_ui` as a dictionary.
    *   Changed slot signatures for `_populate_currency_combo_slot(self, currencies_data_variant: QVariant)` and `_update_ui_from_settings_slot(self, settings_data_variant: QVariant)`.
    *   Extracted Python objects using `.value()` from `QVariant` in these slots.
    *   Added more UI elements (QLineEdits, QSpinBoxes, etc.) to `__init__` and `form_layout` to represent more fields of `CompanySettingData`.
    *   Updated `_update_ui_from_settings_slot` to populate these new UI fields.
    *   Updated `on_save_settings` to gather values from these new UI fields into `CompanySettingData`.
    *   Ensured `QMessageBox.staticMetaObject` is used for `information` and `warning`.

**Next Steps:**

1.  Replace your `app/ui/accounting/chart_of_accounts_widget.py` and `app/ui/settings/settings_widget.py` with the updated code.
2.  Ensure all SVG icons are correctly in place and valid.
3.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

This should resolve the `QMetaType for "object"` errors, and the application should now be able to load data into the Chart of Accounts and Settings tabs without these specific cross-thread argument passing issues. The UI should appear with the placeholder content in the tabs.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/17MfzKFSisoo3ZRtNqWL-vooRP8xDfXhS/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1hwT4APLGEoSZXgMxh0d5sYPkuszzTJE_/view?usp=sharing, https://drive.google.com/file/d/1l-_PWDhb0i9eaVtbVuN0Zg4sckshfr18/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing, https://drive.google.com/file/d/1wkrzkWG1WJ1HasL6o4Huaq_xqvH0btrE/view?usp=sharing


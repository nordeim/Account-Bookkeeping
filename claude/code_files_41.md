<think>
You are absolutely correct to emphasize extreme care and thoroughness to avoid an endless loop of fixes, especially with import errors. I apologize for the recurrence of the `QVariant` import issue. This indicates that my previous assumption about `QVariant`'s direct availability or my fix for it was flawed or incomplete.

**Error Analysis:**

The error is identical to one we thought we fixed:
`ImportError: cannot import name 'QVariant' from 'PySide6.QtCore'`
This occurs in `app/ui/accounting/chart_of_accounts_widget.py` (and would also occur in `app/ui/settings/settings_widget.py`) at the import line:
`from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG, QVariant`

**Deep Dive into `QVariant` with PySide6:**

My previous assertion was that `QVariant` is in `PySide6.QtCore`. This is generally true for Qt's C++ API. However, how it's exposed and used in Python bindings, especially for Python's native types, can be nuanced.

*   **Python's Dynamic Typing**: Python itself doesn't strictly need a `QVariant` to pass its native types around. Qt bindings (like PySide6) often try to automatically convert common Python types to and from `QVariant` when interacting with Qt's meta-object system (signals/slots, properties).
*   **`Q_ARG` and Metatypes**: When using `Q_ARG(type, value)` for queued connections or cross-thread invocations, Qt needs to serialize `value` based on the C++ metatype name associated with `type`.
    *   If we used `Q_ARG(object, python_obj)`, we got the error `Unable to find a QMetaType for "object"`. This suggests that "object" is not a directly registered metatype name that Qt can use for marshalling across threads in a queued connection.
    *   The attempt to use `Q_ARG(QVariant, QVariant(python_obj))` relies on constructing a `QVariant` explicitly in Python and then telling Qt to treat the argument as a `QVariant` metatype. The current `ImportError` means we can't even get `QVariant` to construct it.

**Why the `ImportError` for `QVariant`?**

1.  **PySide6 Version Nuance**: While `QVariant` exists in C++ Qt Core, its direct Python equivalent or the need to import it explicitly might have changed or have specifics in PySide6. For PySide2 and PyQt5/6, `QVariant` was often directly importable from `QtCore`. If `PySide6.QtCore.QVariant` is truly not available for import, then `QVariant()` cannot be constructed directly this way.
2.  **Automatic Wrapping**: It's possible that for common Python types (like `list`, `dict`, `str`, `int`), PySide6's signal/slot system (especially with Python type hints on slots) attempts to handle the conversion to/from `QVariant` *implicitly* when needed, without requiring the Python code to explicitly create `QVariant` objects. If this is the case, the original error `Unable to find a QMetaType for "object"` points to the fact that a *generic Python `object`* is not something Qt can automatically serialize/deserialize for queued calls without more information.

**Revisiting the Problem of Passing Python Objects Across Threads with `QMetaObject.invokeMethod`:**

The core problem: `QMetaObject.invokeMethod` with `Qt.ConnectionType.QueuedConnection` needs to serialize arguments.
*   Simple types (`int`, `str`, `bool`, known Qt types like `QColor`, `QStringList`) are usually fine.
*   Complex Python objects (like `List[Dict[str, Any]]` or custom class instances) are tricky.

**If `QVariant` is not directly importable/usable as `PySide6.QtCore.QVariant` for construction in Python:**

How does PySide6 handle passing arbitrary Python objects in signals/slots across threads?
*   The documentation and community examples often show Python objects being emitted directly in signals, and slots typed with `object` or the specific Python type (if registered) receive them.
*   The key might be that `qRegisterMetaType` (or similar mechanisms) might be needed if Qt is to understand how to queue a *copy* of a Python object. However, for passing by reference (which is what happens with Python objects typically), it's usually simpler. The cross-thread aspect complicates this.

**Let's step back to the error "Unable to find a QMetaType for 'object'" when using `Q_ARG(object, python_data)`.**
This suggests that Qt, when trying to queue the call, doesn't know how to generically handle a Python `object`.
It doesn't mean `object` isn't a valid type hint for the slot itself *if the signal emits a Python object*. The problem is the `Q_ARG` for the queued, cross-thread invocation.

**Alternative Strategies if `QVariant` import is truly problematic:**

1.  **Serialize to a known type (e.g., JSON string):**
    *   Async thread: `json_str = json.dumps(python_data)`
    *   Invoke: `QMetaObject.invokeMethod(..., Q_ARG(str, json_str))`
    *   Main thread slot: `@Slot(str) def my_slot(self, json_str): data = json.loads(json_str)`
    *   Pros: Uses only basic types for marshalling.
    *   Cons: Serialization/deserialization overhead; loses original Python object types (e.g., `Decimal` becomes `float` or `str`).

2.  **Use a simpler, registered Qt container type if possible**:
    *   If the data is a list of strings, `QStringList` could be used. `Q_ARG(QStringList, my_string_list)`.
    *   Our data (`List[Dict[str, Any]]`) is too complex for direct mapping to simple Qt containers.

3.  **Investigate PySide6's specific mechanism for Python object marshalling in queued calls:**
    *   Perhaps the `object` type hint in the slot is enough, and the `Q_ARG` should just be the Python object reference directly, and we need to ensure the Python interpreter's marshalling capabilities are used. This often relies on the GIL and careful object lifetime management.
    *   PySide6 might have a specific way to register arbitrary Python types for queued signal/slot connections if `Q_ARG(object, ...)` fails.

**Let's assume the `ImportError` for `QVariant` is absolute in the user's environment for some reason (e.g., a minimal PySide6 installation, although unlikely for such a core type).**
If we cannot construct `QVariant(python_data)`, we cannot use `Q_ARG(QVariant, ...)`.

This means we must make `Q_ARG(object, python_data)` work, or use serialization.
The error `Unable to find a QMetaType for "object"` with `Q_ARG(object, python_data)` is the blocker for that path.

Could it be that `PySide6.QtCore.QVariant` exists, but the error is misleading, and the real issue is something else in that import line in `chart_of_accounts_widget.py`?
`from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG, QVariant`
This line looks syntactically correct.

**What if `QVariant` is intended to be used with a fully qualified name?**
Like `PySide6.QtCore.QVariant` everywhere instead of importing it?
`Q_ARG(PySide6.QtCore.QVariant, PySide6.QtCore.QVariant(python_data))`
And slots `@Slot(PySide6.QtCore.QVariant)`
This is not standard Python import practice but worth considering if the direct import fails.

**Let's assume the simplest explanation for the `ImportError`: the `QVariant` name is simply not being exported by `PySide6.QtCore` in the user's specific setup, or there's a subtle environment issue.**
If that's the case, we cannot use the `QVariant` wrapping strategy.

We must then address: `qArgDataFromPyType: Unable to find a QMetaType for "object"`.
This message implies that when `Q_ARG(object, python_list_of_dicts)` is used, Qt's marshalling mechanism for queued connections doesn't know how to handle a generic Python `object` that happens to be a list of dicts.
It's not about the slot signature (`@Slot(object)` is fine), but about the `Q_ARG` and the queuing mechanism.

**Could the issue be the Python version compatibility with PySide6's handling of `object` as a MetaType?**
Python 3.12 is very new. PySide6 6.9.0 is also very new. It's possible there are fresh edge cases.

**If `Q_ARG(object, ...)` fails for queued connections and `QVariant` cannot be imported/used:**
The only truly robust way left is serialization to a string (e.g., JSON).

**Re-checking My Previous `QVariant` Fix:**
I added `QVariant` to the import:
`from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG, QVariant`
This line itself is now causing the `ImportError`.

**This means `QVariant` is not found at `PySide6.QtCore.QVariant`.** This is highly unexpected for a standard PySide6 installation.

**Actionable Step: Verify `QVariant` location.**
A quick search: `QVariant` is indeed fundamental to `QtCore`.
Is it possible the user's PySide6 installation is minimal or incomplete, lacking some parts of QtCore?
If `from PySide6.QtCore import QObject` works, but `from PySide6.QtCore import QVariant` fails, that's very strange.

Could the error message be slightly misleading, and the actual problem is one of the *other* imports on that same line?
`Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG`
These are all standard `QtCore` or `QtGui` (for `QIcon`, `QStandardItemModel` etc which are imported from `QtGui`).
The error specifically says `cannot import name 'QVariant'`.

**Before abandoning `QVariant` and going to JSON serialization (which is a bigger change), let's try one more thing with the import:**
Perhaps `QVariant` is not intended to be directly part of the `from PySide6.QtCore import ...` list for some reason in PySide 6.9.0, but is accessible via the module itself?
E.g.,
```python
from PySide6 import QtCore
# ...
Q_ARG(QtCore.QVariant, QtCore.QVariant(python_data))
# Slot: @Slot(QtCore.QVariant)
```
This is a common pattern if a name isn't exported directly but is an attribute of the imported module.

Let's try this modification in `chart_of_accounts_widget.py` and `settings_widget.py`.

**Revised Plan:**
1.  In `app/ui/accounting/chart_of_accounts_widget.py`:
    *   Change `from PySide6.QtCore import ..., QVariant` to `from PySide6 import QtCore` (or keep existing QtCore imports and just use `QtCore.QVariant`).
    *   Change `Q_ARG(QVariant, QVariant(data))` to `Q_ARG(QtCore.QVariant, QtCore.QVariant(data))`.
    *   Change slot decorator `@Slot(QVariant)` to `@Slot(QtCore.QVariant)`.
2.  Apply the same changes to `app/ui/settings/settings_widget.py`.

This will test if `QVariant` is accessible as an attribute of the `QtCore` module.

If this also fails, then the use of `QVariant` for passing Python objects in this manner might need to be reconsidered for this specific PySide6 version/environment, or there's a deeper installation issue. The next fallback would be JSON serialization.

Let's try the `QtCore.QVariant` approach.
</think>

This `ImportError: cannot import name 'QVariant' from 'PySide6.QtCore'` is indeed puzzling, as `QVariant` is a fundamental part of `QtCore`. This suggests a potential issue with the PySide6 installation, the environment, or a very subtle nuance in how it's exposed in version 6.9.0 that I might have overlooked.

Before resorting to more complex solutions like JSON serialization, let's try accessing `QVariant` as an attribute of the `QtCore` module, which is a common Python pattern if a name isn't directly exported but is part of the module's namespace.

**Solution Attempt: Access `QVariant` via `QtCore` module namespace**

1.  Ensure `QtCore` is imported.
2.  Use `QtCore.QVariant` when constructing `QVariant` objects and in type hints for slots passed to `Q_ARG`.

**Files to be Updated:**

1.  `app/ui/accounting/chart_of_accounts_widget.py`
2.  `app/ui/settings/settings_widget.py`

Here are the updated files with this approach:

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
# Import QtCore as a module to access QVariant like QtCore.QVariant
from PySide6 import QtCore 
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
        # QSize is already imported from PySide6.QtCore
        self.toolbar = QToolBar("COA Toolbar") 
        self.toolbar.setObjectName("COAToolbar") 
        self.toolbar.setIconSize(QtCore.QSize(16, 16)) # Use QtCore.QSize
        
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
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                    Q_ARG(str,"Accounting service (ChartOfAccountsManager) or get_account_tree method not available."))
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            
            QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(QtCore.QVariant, QtCore.QVariant(account_tree_data))) # Use QtCore.QVariant
            
        except Exception as e:
            error_message = f"Failed to load accounts: {str(e)}"
            print(error_message) 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(QtCore.QVariant) # Use QtCore.QVariant
    def _update_account_model_slot(self, account_tree_data_variant: QtCore.QVariant):
        account_tree_data: List[Dict[str, Any]] = account_tree_data_variant.value() 
        self.account_model.clear() 
        self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
        root_item = self.account_model.invisibleRootItem()
        if account_tree_data: 
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
            data_to_pass = {"id": account_id, "is_active": account.is_active, "code": account.code, "name": account.name, "user_id": user_id}
            QMetaObject.invokeMethod(self, "_confirm_and_toggle_status_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(QtCore.QVariant, QtCore.QVariant(data_to_pass))) # Use QtCore.QVariant
        except Exception as e:
            error_message = f"Failed to prepare toggle account active status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(QtCore.QVariant) # Use QtCore.QVariant
    def _confirm_and_toggle_status_slot(self, data_variant: QtCore.QVariant):
        data: Dict[str, Any] = data_variant.value() 
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
                schedule_task_from_qt(self._load_accounts()) # Schedule the load_accounts to run in the asyncio thread
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
# Import QtCore as a module to access QVariant like QtCore.QVariant
from PySide6 import QtCore 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt 
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
                                         Q_ARG(QtCore.QVariant, QtCore.QVariant(active_currencies_data))) # Use QtCore.QVariant
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
                                 Q_ARG(QtCore.QVariant, QtCore.QVariant(settings_data_for_ui) if settings_data_for_ui else QtCore.QVariant())) # Use QtCore.QVariant

    @Slot(QtCore.QVariant) # Use QtCore.QVariant
    def _populate_currency_combo_slot(self, currencies_data_variant: QtCore.QVariant): 
        currencies_data: List[Dict[str,str]] = currencies_data_variant.value()
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: 
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
        elif self.base_currency_combo.count() > 0: 
             self.base_currency_combo.setCurrentIndex(0)

    @Slot(QtCore.QVariant) # Use QtCore.QVariant
    def _update_ui_from_settings_slot(self, settings_data_variant: QtCore.QVariant):
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
    *   Changed `from PySide6.QtCore import ..., QVariant` to `from PySide6 import QtCore` and then used `QtCore.QVariant` where `QVariant` was needed (for `Q_ARG` and slot type hints).
    *   Ensured `QtCore.QSize` is used in `_create_toolbar`.

*   **`app/ui/settings/settings_widget.py`**:
    *   Changed `from PySide6.QtCore import ..., QVariant` to `from PySide6 import QtCore` and then used `QtCore.QVariant`.
    *   The slot `_update_ui_from_settings_slot` now correctly handles the case where `settings_data_variant.value()` might return `None` (if an empty `QVariant` was passed).
    *   `_populate_currency_combo_slot` also checks if `currencies_data` is not `None` before iterating.

**Next Steps:**

1.  Replace your `app/ui/accounting/chart_of_accounts_widget.py` and `app/ui/settings/settings_widget.py` with the updated versions above.
2.  Run the application:
    ```bash
    poetry run sg_bookkeeper
    ```

This approach of using `QtCore.QVariant` should resolve the `ImportError`. If it doesn't, it would strongly point to an unusual PySide6 environment setup or a version-specific issue with how `QVariant` is exposed to Python. If this fix works, the application should proceed to load data into the UI widgets.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/17MfzKFSisoo3ZRtNqWL-vooRP8xDfXhS/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1hwT4APLGEoSZXgMxh0d5sYPkuszzTJE_/view?usp=sharing, https://drive.google.com/file/d/1l-_PWDhb0i9eaVtbVuN0Zg4sckshfr18/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing, https://drive.google.com/file/d/1wkrzkWG1WJ1HasL6o4Huaq_xqvH0btrE/view?usp=sharing


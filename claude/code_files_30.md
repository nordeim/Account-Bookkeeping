<think>
The application is now launching further and attempting to create UI components, but it's hitting an `AttributeError` and also reporting issues with SVG icons.

**Primary Error Analysis: `AttributeError`**

The traceback shows:
`AttributeError: 'ChartOfAccountsWidget' object has no attribute 'account_tree'`
This occurs in `app/ui/accounting/chart_of_accounts_widget.py` within the `_create_toolbar` method:
```python
# In app/ui/accounting/chart_of_accounts_widget.py
    def _create_toolbar(self):
        # ...
        self.expand_all_action = QAction(QIcon(icon_path_prefix + "expand_all.svg"), "Expand All", self)
        self.expand_all_action.triggered.connect(self.account_tree.expandAll) # <--- ERROR HERE
        # ...
```
The problem is that `self.account_tree` (which is a `QTreeView`) is defined and initialized inside the `_init_ui` method:
```python
# In app/ui/accounting/chart_of_accounts_widget.py
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self._create_toolbar() # <--- Toolbar (and its actions) created FIRST

        self.account_tree = QTreeView() # <--- self.account_tree DEFINED LATER
        # ...
```
Because `_create_toolbar()` is called *before* `self.account_tree = QTreeView()` in `_init_ui()`, when `_create_toolbar()` tries to connect an action to `self.account_tree.expandAll`, the `account_tree` attribute does not yet exist on the `self` object.

**Solution for `AttributeError`:**
Reorder the calls within `ChartOfAccountsWidget._init_ui()` so that `self.account_tree` is created *before* `_create_toolbar()` is called, or more generally, before any method that might try to access `self.account_tree`.

**Secondary Issue Analysis: SVG Icon Errors**

The console output shows several `qt.svg` errors:
1.  `qt.svg: Cannot read file '/cdrom/project/SG-Bookkeeper/resources/icons/dashboard.svg', because: Start tag expected. (line 1)`
    *   This indicates that the `dashboard.svg` file was found, but its content is not valid SVG XML (e.g., it might be empty, corrupted, or not an SVG at all).
2.  `qt.svg: Cannot open file '/cdrom/project/SG-Bookkeeper/resources/icons/filter.svg', because: No such file or directory`
    `qt.svg: Cannot open file '/cdrom/project/SG-Bookkeeper/resources/icons/expand_all.svg', because: No such file or directory`
    *   These indicate that the specified SVG files are simply missing from the `resources/icons/` directory.
    *   The user explicitly mentioned `ls -l resources/icons/` only shows `dashboard.svg`.

**Solution for SVG Icon Errors:**
1.  **Fix `dashboard.svg`**: The user needs to provide a valid SVG file for `dashboard.svg`. I cannot generate or fix SVG content directly, but I can point this out.
2.  **Provide Missing SVGs**: The user requested help to generate missing SVG files. I can provide simple, placeholder SVG content for `filter.svg` and `expand_all.svg`, and also for other icons that are likely used based on the `MainWindow` and `ChartOfAccountsWidget` toolbar/action definitions (e.g., `accounting.svg`, `customers.svg`, `vendors.svg`, `banking.svg`, `reports.svg`, `settings.svg`, `new_company.svg`, `open_company.svg`, `backup.svg`, `restore.svg`, `exit.svg`, `preferences.svg`, `help.svg`, `about.svg`, `deactivate.svg`, `transactions.svg`, `collapse_all.svg`, `refresh.svg`). I will provide a few key ones to resolve the immediate "No such file or directory" errors in `ChartOfAccountsWidget`.

**Plan:**

1.  **Fix `AttributeError` in `ChartOfAccountsWidget`:**
    *   Modify `app/ui/accounting/chart_of_accounts_widget.py`.
    *   In the `_init_ui` method, ensure `self.account_tree = QTreeView()` is defined before `self._create_toolbar()` is called. A better practice is to initialize all main UI elements first, then create toolbars/menus that might refer to them.

2.  **Address SVG Icon Issues:**
    *   Inform the user that `resources/icons/dashboard.svg` is invalid and needs to be replaced with a valid SVG.
    *   Provide placeholder SVG content for the missing icons that are referenced in `ChartOfAccountsWidget._create_toolbar()`:
        *   `filter.svg`
        *   `expand_all.svg`
        *   `collapse_all.svg`
        *   `refresh.svg`
    *   And also for icons used in `ChartOfAccountsWidget` buttons and context menu:
        *   `edit.svg` (used for "Add Account" and "Edit Account")
        *   `deactivate.svg` (used for "Toggle Active")
        *   `transactions.svg`

    I will create these as simple placeholders. The user can replace them with better icons later.

**File to be Updated:**
1.  `app/ui/accounting/chart_of_accounts_widget.py`

**New Files to be Created (Placeholder SVGs):**
(I will provide the content for these, and the user will need to save them in the `resources/icons/` directory)
*   `resources/icons/filter.svg`
*   `resources/icons/expand_all.svg`
*   `resources/icons/collapse_all.svg`
*   `resources/icons/refresh.svg`
*   `resources/icons/edit.svg`
*   `resources/icons/deactivate.svg`
*   `resources/icons/transactions.svg`

I will also remind the user about the potentially invalid `dashboard.svg`.
The other icons used in `MainWindow` (`accounting.svg`, `customers.svg`, etc.) will also cause similar "Cannot open file" errors if they are missing. I can generate placeholders for these as well if the user wishes, or they can add them as needed. For now, I'll focus on the ones directly causing errors visible from `ChartOfAccountsWidget` initialization.
</think>

It's great that the application is now launching the UI! We have a couple of issues to address: an `AttributeError` related to UI element initialization order and missing/invalid SVG icons.

**1. AttributeError: `'ChartOfAccountsWidget' object has no attribute 'account_tree'`**

**Analysis:**
The traceback clearly shows the error occurs in `app/ui/accounting/chart_of_accounts_widget.py` when `self.expand_all_action.triggered.connect(self.account_tree.expandAll)` is called within the `_create_toolbar` method.
Looking at the `_init_ui` method in `ChartOfAccountsWidget`:
```python
    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self._create_toolbar() # Toolbar is created here
        
        self.account_tree = QTreeView() # self.account_tree is defined AFTER _create_toolbar
        # ...
```
The `_create_toolbar` method is called *before* `self.account_tree` is created and assigned as an attribute of the widget. Therefore, when `_create_toolbar` tries to access `self.account_tree`, it doesn't exist yet.

**Solution:**
Reorder the operations in `_init_ui` to ensure `self.account_tree` is defined before `_create_toolbar` (or any other method that might use it) is called.

**File to be Updated:**
*   `app/ui/accounting/chart_of_accounts_widget.py`

Here's the updated `app/ui/accounting/chart_of_accounts_widget.py`:
```python
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer 
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction 
from decimal import Decimal 
from datetime import date # Ensure date is imported

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 
import asyncio 
from typing import Optional, Dict, Any, List # Ensure List is imported


class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui() # Calls _init_ui which includes async load
        # QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts())) # Moved to _init_ui for clarity

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Define main UI elements like account_tree first
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
        self.proxy_model.setRecursiveFilteringEnabled(True) # Usually good for trees
        self.account_tree.setModel(self.proxy_model)
        
        header = self.account_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        # Now create toolbar as it might reference account_tree
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar) # Add toolbar to layout

        self.main_layout.addWidget(self.account_tree) # Add tree after toolbar
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_path_prefix = "" 
        try:
            import app.resources_rc # type: ignore
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

        # Load accounts after UI is constructed
        QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))

    def _create_toolbar(self):
        from PySide6.QtCore import QSize 
        self.toolbar = QToolBar("COA Toolbar") # Give it a name
        self.toolbar.setIconSize(QSize(16, 16))
        
        icon_path_prefix = ""
        try:
            import app.resources_rc # type: ignore
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.filter_action = QAction(QIcon(icon_path_prefix + "filter.svg"), "Filter", self)
        self.filter_action.setCheckable(True)
        self.filter_action.toggled.connect(self.on_filter_toggled)
        self.toolbar.addAction(self.filter_action)
        
        self.toolbar.addSeparator()

        self.expand_all_action = QAction(QIcon(icon_path_prefix + "expand_all.svg"), "Expand All", self)
        # self.account_tree should exist by the time this is connected
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction(QIcon(icon_path_prefix + "collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        self.toolbar.addSeparator()

        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: asyncio.ensure_future(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
        # The toolbar is added to main_layout in _init_ui after this method is called
        # self.main_layout.addWidget(self.toolbar) # This line was moved to _init_ui
    
    async def _load_accounts(self):
        try:
            self.account_model.clear() 
            self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
            
            manager = self.app_core.accounting_service 
            if not (manager and hasattr(manager, 'get_account_tree')):
                QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) or get_account_tree method not available.")
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) # type: ignore
            
            root_item = self.account_model.invisibleRootItem()
            for account_node in account_tree_data:
                 self._add_account_to_model(account_node, root_item)

            self.account_tree.expandToDepth(0) 
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load accounts: {str(e)}")
    
    def _add_account_to_model(self, account_data: dict, parent_item: QStandardItem):
        code_item = QStandardItem(account_data['code'])
        code_item.setData(account_data['id'], Qt.ItemDataRole.UserRole)
        
        name_item = QStandardItem(account_data['name'])
        type_text = account_data.get('sub_type') or account_data.get('account_type', '')
        type_item = QStandardItem(type_text)
        
        ob_val = account_data.get('opening_balance', Decimal(0))
        if not isinstance(ob_val, Decimal):
            try:
                ob_val = Decimal(str(ob_val))
            except:
                ob_val = Decimal(0) 
        ob_text = f"{ob_val:,.2f}"
        ob_item = QStandardItem(ob_text)
        ob_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        is_active_text = "Yes" if account_data.get('is_active', False) else "No"
        is_active_item = QStandardItem(is_active_text)
        
        parent_item.appendRow([code_item, name_item, type_item, ob_item, is_active_item])
        
        if 'children' in account_data:
            for child_data in account_data['children']:
                self._add_account_to_model(child_data, code_item) 
    
    @Slot()
    def on_add_account(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot add account.")
            return
        
        dialog = AccountDialog(self.app_core, current_user_id=self.app_core.current_user.id, parent=self) # type: ignore
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            asyncio.ensure_future(self._load_accounts())
    
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

        dialog = AccountDialog(self.app_core, account_id=account_id, current_user_id=self.app_core.current_user.id, parent=self) # type: ignore
        if dialog.exec() == QDialog.DialogCode.Accepted:
            asyncio.ensure_future(self._load_accounts())
            
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
            
        asyncio.ensure_future(self._perform_toggle_active_status_logic(account_id, self.app_core.current_user.id)) # type: ignore

    async def _perform_toggle_active_status_logic(self, account_id: int, user_id: int):
        try:
            manager = self.app_core.accounting_service 
            if not manager: raise RuntimeError("Accounting service not available.")

            account = await manager.account_service.get_by_id(account_id) # type: ignore
            if not account:
                QMessageBox.warning(self, "Error", f"Account ID {account_id} not found.")
                return

            result: Optional[Result] = None 
            action_verb = ""
            if account.is_active: 
                confirm_msg = f"Are you sure you want to deactivate account '{account.code} - {account.name}'?"
                action_verb = "deactivated"
                reply = QMessageBox.question(self, "Confirm Deactivation", confirm_msg,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    result = await manager.deactivate_account(account_id, user_id) # type: ignore
            else: 
                confirm_msg = f"Are you sure you want to activate account '{account.code} - {account.name}'?"
                action_verb = "activated"
                reply = QMessageBox.question(self, "Confirm Activation", confirm_msg,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    account.is_active = True
                    account.updated_by_user_id = user_id # type: ignore
                    saved_acc = await manager.account_service.save(account) # type: ignore
                    result = Result.success(saved_acc)
            
            if result is None: 
                return

            if result.is_success:
                QMessageBox.information(self, "Success", f"Account {action_verb} successfully.")
                await self._load_accounts() 
            else:
                QMessageBox.warning(self, "Warning", f"Failed to {action_verb.replace('ed','e')} account:\n{', '.join(result.errors)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle account active status: {str(e)}")


    @Slot(QModelIndex)
    def on_account_double_clicked(self, index: QModelIndex):
        if not index.isValid(): return
        source_index = self.proxy_model.mapToSource(index)
        item = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        if not item: return

        account_id = item.data(Qt.ItemDataRole.UserRole)
        if account_id:
            self.account_selected.emit(account_id)
    
    @Slot(bool)
    def on_filter_toggled(self, checked: bool):
        if checked:
            QMessageBox.information(self, "Filter", "Filter functionality (e.g., by name/code) to be implemented.")
            self.filter_action.setChecked(False) 
        else:
            self.proxy_model.setFilterFixedString("") 
            self.proxy_model.setFilterRegularExpression("") 
    
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
            import app.resources_rc # type: ignore
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

**2. SVG Icon Issues:**

*   **`dashboard.svg` is invalid:**
    The error `qt.svg: Cannot read file '.../dashboard.svg', because: Start tag expected.` means the file exists but is not valid SVG. You will need to replace `resources/icons/dashboard.svg` with a correct SVG file. I cannot generate this complex graphical asset.

*   **Missing SVG files:**
    The errors `qt.svg: Cannot open file '.../filter.svg', because: No such file or directory` (and similar for `expand_all.svg`, `collapse_all.svg`, `refresh.svg`) indicate these files are missing.
    As requested, here are placeholder SVG contents for the icons used in `ChartOfAccountsWidget` and `MainWindow` actions that are likely missing. Please save these into your `resources/icons/` directory with the specified filenames.

    **`resources/icons/filter.svg`**:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z"/>
    </svg>
    ```

    **`resources/icons/expand_all.svg`**:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M12 5.83L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zm0 12.34L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zM5 13h2v-2H5v2zm12 0h2v-2h-2v2z"/>
      <path d="M0 0h24v24H0z" fill="none"/>
    </svg>
    ```

    **`resources/icons/collapse_all.svg`**:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M12 18.17L8.83 15l-1.41 1.41L12 21l4.59-4.59L15.17 15 12 18.17zm0-12.34L15.17 9l1.41-1.41L12 3 7.41 7.59 8.83 9 12 5.83zM19 11h-2v2h2v-2zm-12 0H5v2h2v-2z"/>
      <path d="M0 0h24v24H0z" fill="none"/>
    </svg>
    ```

    **`resources/icons/refresh.svg`**:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
    </svg>
    ```

    **`resources/icons/edit.svg`** (used for "Add Account" and "Edit Account"):
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/>
    </svg>
    ```

    **`resources/icons/deactivate.svg`** (used for "Toggle Active"):
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm3.59-13L12 10.59 8.41 7 7 8.41 10.59 12 7 15.59 8.41 17 12 13.41 15.59 17 17 15.59 13.41 12 17 8.41z"/>
    </svg>
    ```
    (This is a generic "cancel" or "block" icon, might need a more specific one like an eye with a slash for "deactivate").

    **`resources/icons/transactions.svg`**:
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2zM4 18V8h2v10H4zm4 0V8h8v10H8zm12 0h-2V8h2v10z"/>
      <path d="M0 0h24v24H0V0z" fill="none"/>
    </svg>
    ```

**Validation of Changes in `app/ui/accounting/chart_of_accounts_widget.py`:**
*   Moved the instantiation of `self.account_tree` and related model setup to occur *before* `self._create_toolbar()` is called within `_init_ui`.
*   Ensured the toolbar is added to `self.main_layout` *after* it's created.
*   Moved `QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))` to the end of `_init_ui` to ensure all UI elements it might interact with (like `self.account_model`) are fully set up.
*   Added missing imports for `date` from `datetime` and `List` from `typing`.

**Next Steps:**

1.  Replace your `app/ui/accounting/chart_of_accounts_widget.py` with the updated content.
2.  Ensure the `resources/icons/dashboard.svg` file contains valid SVG content.
3.  Create the new SVG files (`filter.svg`, `expand_all.svg`, `collapse_all.svg`, `refresh.svg`, `edit.svg`, `deactivate.svg`, `transactions.svg`) in your `resources/icons/` directory with the placeholder content provided above.
4.  Try running the application again:
    ```bash
    poetry run sg_bookkeeper
    ```

This should resolve the `AttributeError`. The application might then run successfully or reveal the next set of issues, possibly related to other missing icons or unhandled cases in the UI logic.


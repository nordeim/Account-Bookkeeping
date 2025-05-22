# File: app/ui/accounting/chart_of_accounts_widget.py
# (Content previously updated, ensure ApplicationCore type hint and async calls are fine)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction # Added QAction

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
import asyncio 

class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()
        # Use QTimer to schedule the async load after UI is set up
        QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self._create_toolbar()
        
        self.account_tree = QTreeView()
        self.account_tree.setAlternatingRowColors(True)
        self.account_tree.setUniformRowHeights(True)
        self.account_tree.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)
        self.account_tree.setSelectionBehavior(QTreeView.SelectionBehavior.SelectRows)
        self.account_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.account_tree.customContextMenuRequested.connect(self.on_context_menu)
        self.account_tree.doubleClicked.connect(self.on_account_double_clicked)
        
        self.account_model = QStandardItemModel()
        # Balance column might show current balance or opening balance depending on design
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
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # For Is Active
        self.main_layout.addWidget(self.account_tree)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        self.add_button = QPushButton(QIcon("resources/icons/edit.svg"), "Add Account") # Example icon
        self.add_button.clicked.connect(self.on_add_account)
        self.button_layout.addWidget(self.add_button)
        
        self.edit_button = QPushButton(QIcon("resources/icons/edit.svg"), "Edit Account")
        self.edit_button.clicked.connect(self.on_edit_account)
        self.button_layout.addWidget(self.edit_button)
        
        self.deactivate_button = QPushButton(QIcon("resources/icons/deactivate.svg"), "Toggle Active Status")
        self.deactivate_button.clicked.connect(self.on_toggle_active_status) 
        self.button_layout.addWidget(self.deactivate_button)
        
        self.main_layout.addLayout(self.button_layout)

    def _create_toolbar(self):
        from PySide6.QtCore import QSize # Ensure QSize is imported
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(16, 16))
        
        icon_path_prefix = "resources/icons/"

        self.filter_action = QAction(QIcon(icon_path_prefix + "filter.svg"), "Filter", self)
        self.filter_action.setCheckable(True)
        self.filter_action.toggled.connect(self.on_filter_toggled)
        self.toolbar.addAction(self.filter_action)
        
        self.expand_all_action = QAction(QIcon(icon_path_prefix + "expand_all.svg"), "Expand All", self)
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction(QIcon(icon_path_prefix + "collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: asyncio.ensure_future(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
        self.main_layout.addWidget(self.toolbar)
    
    async def _load_accounts(self):
        try:
            self.account_model.clear()
            self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
            
            # Accessing ChartOfAccountsManager via app_core.accounting_service (facade)
            if not (self.app_core and hasattr(self.app_core, 'accounting_service') and 
                    hasattr(self.app_core.accounting_service, 'get_account_tree')): # type: ignore
                QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) or get_account_tree method not available.")
                return

            account_tree_data = await self.app_core.accounting_service.get_account_tree(active_only=False) # Show all for management # type: ignore
            
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
        ob_text = f"{ob_val:,.2f}" if isinstance(ob_val, Decimal) else "N/A"
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
        # Pass user_id from current logged-in user
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
            QMessageBox.warning(self, "Warning", "Please select an account to toggle active status.")
            return

        source_index = self.proxy_model.mapToSource(index)
        item_id = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        item_active = self.account_model.itemFromIndex(source_index.siblingAtColumn(4)) # Assuming 'Is Active' is column 4
        
        if not item_id or not item_active: return
        
        account_id = item_id.data(Qt.ItemDataRole.UserRole)
        is_currently_active = (item_active.text() == "Yes")

        if not account_id:
            QMessageBox.warning(self, "Warning", "Cannot toggle status for this item. Please select an account.")
            return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in. Cannot change account status.")
            return
            
        action_text = "deactivate" if is_currently_active else "activate"
        reply = QMessageBox.question(
            self, f"Confirm {action_text.capitalize()}",
            f"Are you sure you want to {action_text} this account?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            asyncio.ensure_future(self._perform_toggle_active(account_id, is_currently_active, self.app_core.current_user.id)) # type: ignore

    async def _perform_toggle_active(self, account_id: int, currently_active: bool, user_id: int):
        try:
            manager = self.app_core.accounting_service # This is ChartOfAccountsManager
            if not manager: raise RuntimeError("Accounting service not available.")

            if currently_active: # Action is to deactivate
                result = await manager.deactivate_account(account_id, user_id) # type: ignore
            else: # Action is to activate
                # Need an activate_account method or update logic here
                acc_to_activate = await manager.account_service.get_by_id(account_id)
                if not acc_to_activate:
                    QMessageBox.warning(self, "Error", f"Account ID {account_id} not found.")
                    return
                acc_to_activate.is_active = True
                acc_to_activate.updated_by_user_id = user_id # type: ignore
                saved_acc = await manager.account_service.save(acc_to_activate)
                result = Result.success(saved_acc) # type: ignore
            
            if result.is_success:
                action_done = "deactivated" if currently_active else "activated"
                QMessageBox.information(self, "Success", f"Account {action_done} successfully.")
                await self._load_accounts() 
            else:
                QMessageBox.warning(self, "Warning", "\n".join(result.errors))
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
            QMessageBox.information(self, "Filter", "Filter functionality to be implemented.")
            self.filter_action.setChecked(False) 
        else:
            self.proxy_model.setFilterFixedString("")
    
    @Slot(QPoint)
    def on_context_menu(self, pos: QPoint):
        index = self.account_tree.indexAt(pos)
        if not index.isValid(): return

        source_index = self.proxy_model.mapToSource(index)
        item_id = self.account_model.itemFromIndex(source_index.siblingAtColumn(0))
        item_active_text = self.account_model.itemFromIndex(source_index.siblingAtColumn(4)).text() if source_index.siblingAtColumn(4).isValid() else "No"

        if not item_id : return
        
        account_id = item_id.data(Qt.ItemDataRole.UserRole)
        if not account_id: return 
        
        is_currently_active = (item_active_text == "Yes")
        toggle_action_text = "Deactivate Account" if is_currently_active else "Activate Account"
        
        icon_path_prefix = "resources/icons/"
        context_menu = QMenu(self)
        
        edit_action = QAction(QIcon(icon_path_prefix + "edit.svg"), "Edit Account", self)
        edit_action.triggered.connect(self.on_edit_account) 
        context_menu.addAction(edit_action)
        
        view_trans_action = QAction(QIcon(icon_path_prefix + "transactions.svg"), "View Transactions", self)
        view_trans_action.triggered.connect(lambda: self.on_view_transactions(account_id))
        context_menu.addAction(view_trans_action)
        
        toggle_active_action = QAction(QIcon(icon_path_prefix + "deactivate.svg"), toggle_action_text, self) # Icon might need to change based on action
        toggle_active_action.triggered.connect(self.on_toggle_active_status)
        context_menu.addAction(toggle_active_action)
        
        context_menu.exec(self.account_tree.viewport().mapToGlobal(pos))
    
    @Slot(int)
    def on_view_transactions(self, account_id: int):
        QMessageBox.information(self, "View Transactions", f"View transactions for account ID {account_id} (To be implemented).")

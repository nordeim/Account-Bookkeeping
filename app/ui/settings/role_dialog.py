# File: app/ui/settings/role_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel, QTextEdit, QListWidget, QListWidgetItem, QAbstractItemView,
    QGroupBox # Added QGroupBox
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import RoleCreateData, RoleUpdateData, RoleData, PermissionData
from app.models.core.user import Role # ORM for loading
from app.utils.result import Result
from app.utils.json_helpers import json_converter # For serializing if complex objects were in DTO

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleDialog(QDialog):
    role_saved = Signal(int) # Emits role ID

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int, 
                 role_id_to_edit: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.role_id_to_edit = role_id_to_edit
        self.loaded_role_orm: Optional[Role] = None
        self._all_permissions_cache: List[PermissionData] = []


        self.is_new_role = self.role_id_to_edit is None
        self.setWindowTitle("Add New Role" if self.is_new_role else "Edit Role")
        self.setMinimumWidth(500) # Increased width for permissions
        self.setMinimumHeight(450)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_data()))
        # load_existing_role_data is called within _load_initial_data if editing

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        details_group = QGroupBox("Role Details")
        form_layout = QFormLayout(details_group)
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter role name (e.g., Sales Manager)")
        form_layout.addRow("Role Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter a brief description for this role.")
        self.description_edit.setFixedHeight(60) # Reduced height slightly
        form_layout.addRow("Description:", self.description_edit)
        main_layout.addWidget(details_group)
        
        permissions_group = QGroupBox("Assign Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        self.permissions_list_widget = QListWidget()
        self.permissions_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        # Height can be adjusted or let it expand
        permissions_layout.addWidget(self.permissions_list_widget)
        main_layout.addWidget(permissions_group)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)
        
    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

    async def _load_initial_data(self):
        """Load all available permissions and role data if editing."""
        perms_loaded = False
        try:
            if self.app_core.security_manager:
                self._all_permissions_cache = await self.app_core.security_manager.get_all_permissions()
                perms_json = json.dumps([p.model_dump() for p in self._all_permissions_cache])
                QMetaObject.invokeMethod(self, "_populate_permissions_list_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, perms_json))
                perms_loaded = True
        except Exception as e:
            self.app_core.logger.error(f"Error loading permissions for RoleDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load permissions: {str(e)}")
        
        if not perms_loaded:
            self.permissions_list_widget.addItem("Error loading permissions.")
            self.permissions_list_widget.setEnabled(False)

        if self.role_id_to_edit: # If editing, load role data (which includes its permissions)
            try:
                if self.app_core.security_manager:
                    self.loaded_role_orm = await self.app_core.security_manager.get_role_by_id(self.role_id_to_edit)
                    if self.loaded_role_orm:
                        # Serialize role data (including its assigned permission IDs)
                        assigned_perm_ids = [p.id for p in self.loaded_role_orm.permissions]
                        role_dict = {
                            "id": self.loaded_role_orm.id, "name": self.loaded_role_orm.name,
                            "description": self.loaded_role_orm.description,
                            "assigned_permission_ids": assigned_perm_ids
                        }
                        role_json_str = json.dumps(role_dict, default=json_converter)
                        QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, role_json_str))
                    else:
                        QMessageBox.warning(self, "Load Error", f"Role ID {self.role_id_to_edit} not found.")
                        self.reject()
            except Exception as e:
                 self.app_core.logger.error(f"Error loading role (ID: {self.role_id_to_edit}) for edit: {e}", exc_info=True)
                 QMessageBox.warning(self, "Load Error", f"Could not load role details: {str(e)}"); self.reject()
        elif self.is_new_role : # New role
            self.name_edit.setFocus()


    @Slot(str)
    def _populate_permissions_list_slot(self, permissions_json_str: str):
        self.permissions_list_widget.clear()
        try:
            permissions_data_list = json.loads(permissions_json_str)
            self._all_permissions_cache = [PermissionData.model_validate(p_dict) for p_dict in permissions_data_list]
            for perm_dto in self._all_permissions_cache:
                item_text = f"{perm_dto.module}: {perm_dto.code}"
                if perm_dto.description: item_text += f" - {perm_dto.description}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, perm_dto.id) # Store permission ID
                self.permissions_list_widget.addItem(item)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing permissions JSON for RoleDialog: {e}")
            self.permissions_list_widget.addItem("Error parsing permissions.")
        
        # If editing and user data already loaded, re-select permissions
        if self.role_id_to_edit and self.loaded_role_orm:
            self._select_assigned_permissions([p.id for p in self.loaded_role_orm.permissions])


    @Slot(str)
    def _populate_fields_slot(self, role_json_str: str):
        try:
            role_data = json.loads(role_json_str) 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse role data for editing."); return

        self.name_edit.setText(role_data.get("name", ""))
        self.description_edit.setText(role_data.get("description", "") or "")

        if role_data.get("name") == "Administrator":
            self.name_edit.setReadOnly(True)
            self.name_edit.setToolTip("The 'Administrator' role name cannot be changed.")
            # self.permissions_list_widget.setEnabled(False) # Admin role permissions are implicit
            # For Admin role, all permissions should be selected and disabled from unchecking.
            for i in range(self.permissions_list_widget.count()):
                self.permissions_list_widget.item(i).setSelected(True)
            self.permissions_list_widget.setEnabled(False) # Prevent changing Admin permissions

        else:
            assigned_permission_ids = role_data.get("assigned_permission_ids", [])
            self._select_assigned_permissions(assigned_permission_ids)

    def _select_assigned_permissions(self, assigned_ids: List[int]):
        for i in range(self.permissions_list_widget.count()):
            item = self.permissions_list_widget.item(i)
            permission_id_in_item = item.data(Qt.ItemDataRole.UserRole)
            if permission_id_in_item in assigned_ids:
                item.setSelected(True)
            else:
                item.setSelected(False) # Explicitly deselect

    def _collect_data(self) -> Optional[Union[RoleCreateData, RoleUpdateData]]:
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip() or None
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Role Name is required.")
            return None
        
        selected_permission_ids: List[int] = []
        for item in self.permissions_list_widget.selectedItems():
            perm_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(perm_id, int):
                selected_permission_ids.append(perm_id)
        
        common_data = {"name": name, "description": description, "permission_ids": selected_permission_ids}

        try:
            if self.is_new_role:
                return RoleCreateData(**common_data) # type: ignore
            else:
                assert self.role_id_to_edit is not None
                return RoleUpdateData(id=self.role_id_to_edit, **common_data) # type: ignore
        except ValueError as pydantic_error: 
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
        # Prevent saving if editing "Administrator" role name (already handled by read-only)
        # but this is an additional safeguard.
        if self.loaded_role_orm and self.loaded_role_orm.name == "Administrator" and \
           self.name_edit.text().strip() != "Administrator":
            QMessageBox.warning(self, "Save Error", "Cannot change the name of the 'Administrator' role.")
            self.name_edit.setText("Administrator") # Reset it
            return

        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_save(dto))
            if future:
                future.add_done_callback(
                    lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
                )
            else: 
                if ok_button: ok_button.setEnabled(True)

    async def _perform_save(self, dto: Union[RoleCreateData, RoleUpdateData]):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[Role]
        action_verb_present = "update" if isinstance(dto, RoleUpdateData) else "create"
        action_verb_past = "updated" if isinstance(dto, RoleUpdateData) else "created"

        if isinstance(dto, RoleUpdateData):
            result = await self.app_core.security_manager.update_role(dto, self.current_admin_user_id)
        else: 
            result = await self.app_core.security_manager.create_role(dto, self.current_admin_user_id)

        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self.parentWidget() if self.parentWidget() else self), 
                Q_ARG(str, "Success"), 
                Q_ARG(str, f"Role '{result.value.name}' {action_verb_past} successfully."))
            self.role_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), 
                Q_ARG(str, f"Failed to {action_verb_present} role:\n{', '.join(result.errors)}"))

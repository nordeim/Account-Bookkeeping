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

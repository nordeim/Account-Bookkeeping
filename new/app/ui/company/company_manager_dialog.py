# File: app/ui/company/company_manager_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QPushButton, QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot, Signal
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CompanyManagerDialog(QDialog):
    # Custom result codes to signal specific actions back to the main window
    NewCompanyRequest = 100
    OpenCompanyRequest = 101

    def __init__(self, app_core: "ApplicationCore", parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.setWindowTitle("Company File Manager")
        self.setMinimumSize(500, 350)
        self.setModal(True)
        
        self.icon_path_prefix = "resources/icons/"
        try:
            import app.resources_rc
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._selected_company_info: Optional[Dict[str, str]] = None
        self._init_ui()
        self._connect_signals()
        self._load_company_list()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        main_layout.addWidget(QLabel("Select a company file to open, or create a new one."))
        
        self.company_list_widget = QListWidget()
        self.company_list_widget.setAlternatingRowColors(True)
        main_layout.addWidget(self.company_list_widget)

        button_layout = QHBoxLayout()
        self.new_button = QPushButton(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...")
        self.delete_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove from List")
        self.delete_button.setEnabled(False)
        button_layout.addWidget(self.new_button)
        button_layout.addStretch()
        button_layout.addWidget(self.delete_button)
        main_layout.addLayout(button_layout)
        
        self.button_box = QDialogButtonBox()
        self.open_button = self.button_box.addButton("Open Company", QDialogButtonBox.ButtonRole.AcceptRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Cancel)
        self.open_button.setEnabled(False) # Disable until a selection is made
        main_layout.addWidget(self.button_box)
        
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.new_button.clicked.connect(self._on_new_company_request)
        self.delete_button.clicked.connect(self._on_delete_company)
        self.open_button.clicked.connect(self._on_open_company)
        self.button_box.rejected.connect(self.reject)
        
        self.company_list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.company_list_widget.itemDoubleClicked.connect(self._on_open_company)

    def _load_company_list(self):
        self.company_list_widget.clear()
        try:
            companies = self.app_core.company_manager.get_company_list()
            for company_info in companies:
                display_name = company_info.get("display_name", "Unknown Company")
                db_name = company_info.get("database_name", "unknown_db")
                item_text = f"{display_name}\n({db_name})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, company_info) # Store the whole dict
                self.company_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load company list: {e}")

    @Slot()
    def _on_selection_changed(self):
        has_selection = bool(self.company_list_widget.selectedItems())
        self.open_button.setEnabled(has_selection)
        self.delete_button.setEnabled(has_selection)
        if has_selection:
            self._selected_company_info = self.company_list_widget.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        else:
            self._selected_company_info = None

    @Slot()
    def _on_new_company_request(self):
        self.done(self.NewCompanyRequest)

    @Slot()
    def _on_open_company(self):
        if self._selected_company_info:
            self.done(self.OpenCompanyRequest)
        else:
            QMessageBox.information(self, "No Selection", "Please select a company to open.")

    @Slot()
    def _on_delete_company(self):
        if not self._selected_company_info:
            return
        
        display_name = self._selected_company_info.get("display_name")
        reply = QMessageBox.question(self, "Confirm Remove",
            f"Are you sure you want to remove '{display_name}' from the list?\n\nThis will NOT delete the actual database file, only remove it from this list.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.app_core.company_manager.remove_company(self._selected_company_info)
                self._load_company_list() # Refresh the list widget
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not remove company from list: {e}")

    def get_selected_company_info(self) -> Optional[Dict[str, str]]:
        return self._selected_company_info

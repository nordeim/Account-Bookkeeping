# app/ui/main_window.py
```py
# app/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QMessageBox, QLabel 
)
from PySide6.QtGui import QIcon, QKeySequence, QAction 
from PySide6.QtCore import Qt, QSettings, Signal, Slot, QCoreApplication, QSize 

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.products.products_widget import ProductsWidget # New Import
from app.ui.banking.banking_widget import BankingWidget
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget
from app.core.application_core import ApplicationCore

class MainWindow(QMainWindow):
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        
        self.setWindowTitle(f"{QCoreApplication.applicationName()} - {QCoreApplication.applicationVersion()}")
        self.setMinimumSize(1024, 768)
        
        # Determine icon path prefix once
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            # This message is better placed in main.py or ApplicationCore for a one-time startup log
            # print("MainWindow: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            pass

        settings = QSettings() 
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry")) 
        else:
            self.resize(1280, 800)
        
        self._init_ui()
        
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state")) 
    
    def _init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self._create_toolbar()
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget)
        
        self._add_module_tabs()
        self._create_status_bar()
        self._create_actions()
        self._create_menus()
    
    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24)) # Slightly larger toolbar icons
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        # Icon path prefix is now an instance variable self.icon_path_prefix
        self.dashboard_widget = DashboardWidget(self.app_core)
        self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        
        self.accounting_widget = AccountingWidget(self.app_core)
        self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        
        self.customers_widget = CustomersWidget(self.app_core)
        self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")

        self.products_widget = ProductsWidget(self.app_core) # New Widget
        self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services") # New Tab
        
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking")
        
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        # ... (no changes from previous version)
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    
    def _create_actions(self):
        # ... (no changes from previous version, uses self.icon_path_prefix)
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New)); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open)); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        # ... (no changes from previous version)
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    # ... (other slots remain unchanged) ...
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        # Example: Navigate to Settings tab, or open a dedicated preferences dialog
        settings_tab_index = -1
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.settings_widget:
                settings_tab_index = i
                break
        if settings_tab_index != -1:
            self.tab_widget.setCurrentIndex(settings_tab_index)
        else:
            QMessageBox.information(self, "Preferences", "Preferences (Settings Tab) not found or full dialog not yet implemented.")

    @Slot()
    def on_help_contents(self): QMessageBox.information(self, "Help", "Help system not yet implemented.")
    @Slot()
    def on_about(self): QMessageBox.about(self, f"About {QCoreApplication.applicationName()}", f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}\n\nA comprehensive bookkeeping application for Singapore small businesses.\n\n© 2024 {QCoreApplication.organizationName()}"); 
    def closeEvent(self, event): 
        settings = QSettings(); settings.setValue("MainWindow/geometry", self.saveGeometry()); settings.setValue("MainWindow/state", self.saveState()); settings.sync()
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes: event.accept() 
        else: event.ignore()

```

# app/ui/reports/__init__.py
```py
# app/ui/reports/__init__.py
from .reports_widget import ReportsWidget
from .trial_balance_table_model import TrialBalanceTableModel # New Export
from .general_ledger_table_model import GeneralLedgerTableModel # New Export

__all__ = [
    "ReportsWidget",
    "TrialBalanceTableModel", # New Export
    "GeneralLedgerTableModel", # New Export
]


```

# app/ui/reports/reports_widget.py
```py
# app/ui/reports/reports_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QDateEdit, QPushButton, QFormLayout, 
    QLineEdit, QGroupBox, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy,
    QTabWidget, QTextEdit, QComboBox, QFileDialog, QInputDialog, QCompleter,
    QStackedWidget, QTreeView, QTableView, 
    QAbstractItemView 
)
from PySide6.QtCore import Qt, Slot, QDate, QTimer, QMetaObject, Q_ARG, QStandardPaths
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont 
from typing import Optional, Dict, Any, TYPE_CHECKING, List 

import json
from decimal import Decimal, InvalidOperation
import os 
from datetime import date as python_date, timedelta 

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.pydantic_models import GSTReturnData 
from app.utils.result import Result 
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.account import Account 

from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice 

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._prepared_gst_data: Optional[GSTReturnData] = None 
        self._saved_draft_gst_return_orm: Optional[GSTReturn] = None 
        self._current_financial_report_data: Optional[Dict[str, Any]] = None
        self._gl_accounts_cache: List[Dict[str, Any]] = [] 

        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self.main_layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self._create_gst_f5_tab()
        self._create_financial_statements_tab()
        
        self.setLayout(self.main_layout)

    def _format_decimal_for_display(self, value: Optional[Decimal], default_str: str = "0.00", show_blank_for_zero: bool = False) -> str:
        if value is None: return default_str if not show_blank_for_zero else ""
        try:
            d_value = Decimal(str(value)) 
            if show_blank_for_zero and d_value == Decimal(0):
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return "Error"

    def _create_gst_f5_tab(self):
        gst_f5_widget = QWidget()
        gst_f5_main_layout = QVBoxLayout(gst_f5_widget)
        gst_f5_group = QGroupBox("GST F5 Return Data Preparation")
        gst_f5_group_layout = QVBoxLayout(gst_f5_group) 
        date_selection_layout = QHBoxLayout()
        date_form = QFormLayout()
        self.gst_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-3).addDays(-QDate.currentDate().day()+1))
        self.gst_start_date_edit.setCalendarPopup(True); self.gst_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period Start Date:", self.gst_start_date_edit)
        self.gst_end_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day())) 
        self.gst_end_date_edit.setCalendarPopup(True); self.gst_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        date_form.addRow("Period End Date:", self.gst_end_date_edit)
        date_selection_layout.addLayout(date_form)
        prepare_button_layout = QVBoxLayout()
        self.prepare_gst_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Prepare GST F5 Data")
        self.prepare_gst_button.clicked.connect(self._on_prepare_gst_f5_clicked)
        prepare_button_layout.addWidget(self.prepare_gst_button); prepare_button_layout.addStretch()
        date_selection_layout.addLayout(prepare_button_layout); date_selection_layout.addStretch(1)
        gst_f5_group_layout.addLayout(date_selection_layout)
        self.gst_display_form = QFormLayout()
        self.gst_std_rated_supplies_display = QLineEdit(); self.gst_std_rated_supplies_display.setReadOnly(True)
        self.gst_zero_rated_supplies_display = QLineEdit(); self.gst_zero_rated_supplies_display.setReadOnly(True)
        self.gst_exempt_supplies_display = QLineEdit(); self.gst_exempt_supplies_display.setReadOnly(True)
        self.gst_total_supplies_display = QLineEdit(); self.gst_total_supplies_display.setReadOnly(True); self.gst_total_supplies_display.setStyleSheet("font-weight: bold;")
        self.gst_taxable_purchases_display = QLineEdit(); self.gst_taxable_purchases_display.setReadOnly(True)
        self.gst_output_tax_display = QLineEdit(); self.gst_output_tax_display.setReadOnly(True)
        self.gst_input_tax_display = QLineEdit(); self.gst_input_tax_display.setReadOnly(True)
        self.gst_adjustments_display = QLineEdit("0.00"); self.gst_adjustments_display.setReadOnly(True)
        self.gst_net_payable_display = QLineEdit(); self.gst_net_payable_display.setReadOnly(True); self.gst_net_payable_display.setStyleSheet("font-weight: bold;")
        self.gst_filing_due_date_display = QLineEdit(); self.gst_filing_due_date_display.setReadOnly(True)
        self.gst_display_form.addRow("1. Standard-Rated Supplies:", self.gst_std_rated_supplies_display); self.gst_display_form.addRow("2. Zero-Rated Supplies:", self.gst_zero_rated_supplies_display); self.gst_display_form.addRow("3. Exempt Supplies:", self.gst_exempt_supplies_display); self.gst_display_form.addRow("4. Total Supplies (1+2+3):", self.gst_total_supplies_display); self.gst_display_form.addRow("5. Taxable Purchases:", self.gst_taxable_purchases_display); self.gst_display_form.addRow("6. Output Tax Due:", self.gst_output_tax_display); self.gst_display_form.addRow("7. Input Tax and Refunds Claimed:", self.gst_input_tax_display); self.gst_display_form.addRow("8. GST Adjustments:", self.gst_adjustments_display); self.gst_display_form.addRow("9. Net GST Payable / (Claimable):", self.gst_net_payable_display); self.gst_display_form.addRow("Filing Due Date:", self.gst_filing_due_date_display)
        gst_f5_group_layout.addLayout(self.gst_display_form)
        gst_action_button_layout = QHBoxLayout()
        self.save_draft_gst_button = QPushButton("Save Draft GST Return"); self.save_draft_gst_button.setEnabled(False)
        self.save_draft_gst_button.clicked.connect(self._on_save_draft_gst_return_clicked)
        self.finalize_gst_button = QPushButton("Finalize GST Return"); self.finalize_gst_button.setEnabled(False)
        self.finalize_gst_button.clicked.connect(self._on_finalize_gst_return_clicked)
        gst_action_button_layout.addStretch(); gst_action_button_layout.addWidget(self.save_draft_gst_button); gst_action_button_layout.addWidget(self.finalize_gst_button)
        gst_f5_group_layout.addLayout(gst_action_button_layout)
        gst_f5_main_layout.addWidget(gst_f5_group); gst_f5_main_layout.addStretch()
        self.tab_widget.addTab(gst_f5_widget, "GST F5 Preparation")

    def _create_financial_statements_tab(self):
        fs_widget = QWidget()
        fs_main_layout = QVBoxLayout(fs_widget)
        fs_group = QGroupBox("Financial Statements")
        fs_group_layout = QVBoxLayout(fs_group) 
        controls_layout = QHBoxLayout()
        self.fs_params_form = QFormLayout() 
        self.fs_report_type_combo = QComboBox()
        self.fs_report_type_combo.addItems(["Balance Sheet", "Profit & Loss Statement", "Trial Balance", "General Ledger"])
        self.fs_params_form.addRow("Report Type:", self.fs_report_type_combo)
        self.fs_gl_account_label = QLabel("Account for GL:")
        self.fs_gl_account_combo = QComboBox()
        self.fs_gl_account_combo.setMinimumWidth(250); self.fs_gl_account_combo.setEditable(True)
        completer = QCompleter([f"{item.get('code')} - {item.get('name')}" for item in self._gl_accounts_cache]) 
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.fs_gl_account_combo.setCompleter(completer)
        self.fs_params_form.addRow(self.fs_gl_account_label, self.fs_gl_account_combo)
        self.fs_as_of_date_edit = QDateEdit(QDate.currentDate())
        self.fs_as_of_date_edit.setCalendarPopup(True); self.fs_as_of_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("As of Date:", self.fs_as_of_date_edit)
        self.fs_start_date_edit = QDateEdit(QDate.currentDate().addMonths(-1).addDays(-QDate.currentDate().day()+1))
        self.fs_start_date_edit.setCalendarPopup(True); self.fs_start_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period Start Date:", self.fs_start_date_edit)
        self.fs_end_date_edit = QDateEdit(QDate.currentDate().addDays(-QDate.currentDate().day()))
        self.fs_end_date_edit.setCalendarPopup(True); self.fs_end_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.fs_params_form.addRow("Period End Date:", self.fs_end_date_edit)
        controls_layout.addLayout(self.fs_params_form)
        generate_fs_button_layout = QVBoxLayout()
        self.generate_fs_button = QPushButton(QIcon(self.icon_path_prefix + "reports.svg"), "Generate Report")
        self.generate_fs_button.clicked.connect(self._on_generate_financial_report_clicked)
        generate_fs_button_layout.addWidget(self.generate_fs_button); generate_fs_button_layout.addStretch()
        controls_layout.addLayout(generate_fs_button_layout); controls_layout.addStretch(1)
        fs_group_layout.addLayout(controls_layout)
        self.fs_display_stack = QStackedWidget()
        fs_group_layout.addWidget(self.fs_display_stack, 1)
        self.bs_tree_view = QTreeView(); self.bs_tree_view.setAlternatingRowColors(True); self.bs_tree_view.setHeaderHidden(False); self.bs_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.bs_model = QStandardItemModel(); self.bs_tree_view.setModel(self.bs_model)
        self.fs_display_stack.addWidget(self.bs_tree_view)
        self.pl_tree_view = QTreeView(); self.pl_tree_view.setAlternatingRowColors(True); self.pl_tree_view.setHeaderHidden(False); self.pl_tree_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pl_model = QStandardItemModel(); self.pl_tree_view.setModel(self.pl_model)
        self.fs_display_stack.addWidget(self.pl_tree_view)
        
        self.tb_table_view = QTableView()
        self.tb_table_view.setAlternatingRowColors(True)
        self.tb_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Corrected
        self.tb_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)   # Added
        self.tb_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tb_table_view.setSortingEnabled(True)
        self.tb_model = TrialBalanceTableModel(); self.tb_table_view.setModel(self.tb_model)
        self.fs_display_stack.addWidget(self.tb_table_view)
        
        gl_widget_container = QWidget() 
        gl_layout = QVBoxLayout(gl_widget_container)
        gl_layout.setContentsMargins(0,0,0,0)
        self.gl_summary_label_account = QLabel("Account: N/A"); self.gl_summary_label_account.setStyleSheet("font-weight: bold;")
        self.gl_summary_label_period = QLabel("Period: N/A")
        self.gl_summary_label_ob = QLabel("Opening Balance: 0.00")
        gl_summary_header_layout = QHBoxLayout()
        gl_summary_header_layout.addWidget(self.gl_summary_label_account); gl_summary_header_layout.addStretch(); gl_summary_header_layout.addWidget(self.gl_summary_label_period)
        gl_layout.addLayout(gl_summary_header_layout)
        gl_layout.addWidget(self.gl_summary_label_ob)
        self.gl_table_view = QTableView()
        self.gl_table_view.setAlternatingRowColors(True)
        self.gl_table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Corrected
        self.gl_table_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)   # Added
        self.gl_table_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.gl_table_view.setSortingEnabled(True)
        self.gl_model = GeneralLedgerTableModel(); self.gl_table_view.setModel(self.gl_model)
        gl_layout.addWidget(self.gl_table_view)
        self.gl_summary_label_cb = QLabel("Closing Balance: 0.00"); self.gl_summary_label_cb.setAlignment(Qt.AlignmentFlag.AlignRight)
        gl_layout.addWidget(self.gl_summary_label_cb)
        self.fs_display_stack.addWidget(gl_widget_container)
        self.gl_widget_container = gl_widget_container 
        
        export_button_layout = QHBoxLayout()
        self.export_pdf_button = QPushButton("Export to PDF"); self.export_pdf_button.setEnabled(False)
        self.export_pdf_button.clicked.connect(lambda: self._on_export_report_clicked("pdf"))
        self.export_excel_button = QPushButton("Export to Excel"); self.export_excel_button.setEnabled(False)
        self.export_excel_button.clicked.connect(lambda: self._on_export_report_clicked("excel"))
        export_button_layout.addStretch()
        export_button_layout.addWidget(self.export_pdf_button); export_button_layout.addWidget(self.export_excel_button)
        fs_group_layout.addLayout(export_button_layout)
        fs_main_layout.addWidget(fs_group)
        self.tab_widget.addTab(fs_widget, "Financial Statements")
        self.fs_report_type_combo.currentTextChanged.connect(self._on_fs_report_type_changed)
        self._on_fs_report_type_changed(self.fs_report_type_combo.currentText())

    @Slot()
    def _on_prepare_gst_f5_clicked(self):
        start_date = self.gst_start_date_edit.date().toPython(); end_date = self.gst_end_date_edit.date().toPython()
        if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        if not self.app_core.gst_manager: QMessageBox.critical(self, "Error", "GST Manager not available."); return
        self.prepare_gst_button.setEnabled(False); self.prepare_gst_button.setText("Preparing...")
        self._saved_draft_gst_return_orm = None; self.finalize_gst_button.setEnabled(False)
        current_user_id = self.app_core.current_user.id
        future = schedule_task_from_qt(self.app_core.gst_manager.prepare_gst_return_data(start_date, end_date, current_user_id))
        if future: future.add_done_callback(self._handle_prepare_gst_f5_result)
        else: self._handle_prepare_gst_f5_result(None) 

    def _handle_prepare_gst_f5_result(self, future):
        self.prepare_gst_button.setEnabled(True); self.prepare_gst_button.setText("Prepare GST F5 Data")
        if future is None: 
            QMessageBox.critical(self, "Task Error", "Failed to schedule GST data preparation.")
            self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
            return
        try:
            result: Result[GSTReturnData] = future.result()
            if result.is_success and result.value: 
                self._prepared_gst_data = result.value
                self._update_gst_f5_display(self._prepared_gst_data)
                self.save_draft_gst_button.setEnabled(True)
                self.finalize_gst_button.setEnabled(False) 
            else: 
                self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
                QMessageBox.warning(self, "GST Data Error", f"Failed to prepare GST data:\n{', '.join(result.errors)}")
        except Exception as e: 
            self._clear_gst_display_fields(); self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
            self.app_core.logger.error(f"Exception handling GST F5 preparation result: {e}", exc_info=True)
            QMessageBox.critical(self, "GST Data Error", f"An unexpected error occurred: {str(e)}")

    def _update_gst_f5_display(self, gst_data: GSTReturnData):
        self.gst_std_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.standard_rated_supplies))
        self.gst_zero_rated_supplies_display.setText(self._format_decimal_for_display(gst_data.zero_rated_supplies))
        self.gst_exempt_supplies_display.setText(self._format_decimal_for_display(gst_data.exempt_supplies))
        self.gst_total_supplies_display.setText(self._format_decimal_for_display(gst_data.total_supplies))
        self.gst_taxable_purchases_display.setText(self._format_decimal_for_display(gst_data.taxable_purchases))
        self.gst_output_tax_display.setText(self._format_decimal_for_display(gst_data.output_tax))
        self.gst_input_tax_display.setText(self._format_decimal_for_display(gst_data.input_tax))
        self.gst_adjustments_display.setText(self._format_decimal_for_display(gst_data.tax_adjustments))
        self.gst_net_payable_display.setText(self._format_decimal_for_display(gst_data.tax_payable))
        self.gst_filing_due_date_display.setText(gst_data.filing_due_date.strftime('%d/%m/%Y') if gst_data.filing_due_date else "")

    def _clear_gst_display_fields(self):
        for w in [self.gst_std_rated_supplies_display, self.gst_zero_rated_supplies_display, self.gst_exempt_supplies_display,
                  self.gst_total_supplies_display, self.gst_taxable_purchases_display, self.gst_output_tax_display,
                  self.gst_input_tax_display, self.gst_net_payable_display, self.gst_filing_due_date_display]:
            w.clear()
        self.gst_adjustments_display.setText("0.00"); self._prepared_gst_data = None; self._saved_draft_gst_return_orm = None
    
    @Slot()
    def _on_save_draft_gst_return_clicked(self):
        if not self._prepared_gst_data: QMessageBox.warning(self, "No Data", "Please prepare GST data first."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        self._prepared_gst_data.user_id = self.app_core.current_user.id
        if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.id: 
            self._prepared_gst_data.id = self._saved_draft_gst_return_orm.id
            
        self.save_draft_gst_button.setEnabled(False); self.save_draft_gst_button.setText("Saving Draft..."); self.finalize_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.save_gst_return(self._prepared_gst_data))
        if future: future.add_done_callback(self._handle_save_draft_gst_result)
        else: self._handle_save_draft_gst_result(None)

    def _handle_save_draft_gst_result(self, future):
        self.save_draft_gst_button.setEnabled(True); self.save_draft_gst_button.setText("Save Draft GST Return")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule GST draft save."); return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                self._saved_draft_gst_return_orm = result.value
                if self._prepared_gst_data: 
                    self._prepared_gst_data.id = result.value.id 
                QMessageBox.information(self, "Success", f"GST Return draft saved successfully (ID: {result.value.id}).")
                self.finalize_gst_button.setEnabled(True) 
            else: 
                QMessageBox.warning(self, "Save Error", f"Failed to save GST Return draft:\n{', '.join(result.errors)}")
                self.finalize_gst_button.setEnabled(False)
        except Exception as e: 
            self.app_core.logger.error(f"Exception handling save draft GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"An unexpected error occurred: {str(e)}")
            self.finalize_gst_button.setEnabled(False)

    @Slot()
    def _on_finalize_gst_return_clicked(self):
        if not self._saved_draft_gst_return_orm or not self._saved_draft_gst_return_orm.id: QMessageBox.warning(self, "No Draft", "Please prepare and save a draft GST return first."); return
        if self._saved_draft_gst_return_orm.status != "Draft": QMessageBox.information(self, "Already Processed", f"This GST Return (ID: {self._saved_draft_gst_return_orm.id}) is already '{self._saved_draft_gst_return_orm.status}'."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Authentication Error", "No user logged in."); return
        submission_ref, ok_ref = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Reference No.:")
        if not ok_ref or not submission_ref.strip(): QMessageBox.information(self, "Cancelled", "Submission reference not provided. Finalization cancelled."); return
        submission_date_str, ok_date = QInputDialog.getText(self, "Finalize GST Return", "Enter Submission Date (YYYY-MM-DD):", text=python_date.today().isoformat())
        if not ok_date or not submission_date_str.strip(): QMessageBox.information(self, "Cancelled", "Submission date not provided. Finalization cancelled."); return
        try: parsed_submission_date = python_date.fromisoformat(submission_date_str)
        except ValueError: QMessageBox.warning(self, "Invalid Date", "Submission date format is invalid. Please use YYYY-MM-DD."); return
        self.finalize_gst_button.setEnabled(False); self.finalize_gst_button.setText("Finalizing..."); self.save_draft_gst_button.setEnabled(False)
        future = schedule_task_from_qt(self.app_core.gst_manager.finalize_gst_return(return_id=self._saved_draft_gst_return_orm.id, submission_reference=submission_ref.strip(), submission_date=parsed_submission_date, user_id=self.app_core.current_user.id))
        if future: future.add_done_callback(self._handle_finalize_gst_result)
        else: self._handle_finalize_gst_result(None)

    def _handle_finalize_gst_result(self, future):
        self.finalize_gst_button.setText("Finalize GST Return") 
        if future is None: 
            QMessageBox.critical(self, "Task Error", "Failed to schedule GST finalization.")
            if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft":
                self.finalize_gst_button.setEnabled(True)
            else:
                self.finalize_gst_button.setEnabled(False)
            return
        try:
            result: Result[GSTReturn] = future.result()
            if result.is_success and result.value: 
                QMessageBox.information(self, "Success", f"GST Return (ID: {result.value.id}) finalized successfully.\nStatus: {result.value.status}.\nSettlement JE ID: {result.value.journal_entry_id or 'N/A'}")
                self._saved_draft_gst_return_orm = result.value 
                self.save_draft_gst_button.setEnabled(False); self.finalize_gst_button.setEnabled(False)
                if self._prepared_gst_data: 
                    self._prepared_gst_data.status = result.value.status
            else: 
                QMessageBox.warning(self, "Finalization Error", f"Failed to finalize GST Return:\n{', '.join(result.errors)}")
                if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft": self.finalize_gst_button.setEnabled(True) 
                self.save_draft_gst_button.setEnabled(True) 
        except Exception as e: 
            self.app_core.logger.error(f"Exception handling finalize GST result: {e}", exc_info=True)
            QMessageBox.critical(self, "Finalization Error", f"An unexpected error occurred: {str(e)}")
            if self._saved_draft_gst_return_orm and self._saved_draft_gst_return_orm.status == "Draft":
                 self.finalize_gst_button.setEnabled(True)
            self.save_draft_gst_button.setEnabled(True) 

    @Slot(str)
    def _on_fs_report_type_changed(self, report_type: str):
        is_pl_report = (report_type == "Profit & Loss Statement")
        is_gl_report = (report_type == "General Ledger")

        self.fs_as_of_date_edit.setVisible(not is_pl_report and not is_gl_report)
        self.fs_start_date_edit.setVisible(is_pl_report or is_gl_report)
        self.fs_end_date_edit.setVisible(is_pl_report or is_gl_report)
        self.fs_gl_account_combo.setVisible(is_gl_report)
        self.fs_gl_account_label.setVisible(is_gl_report)

        if hasattr(self, 'fs_params_form') and self.fs_params_form:
            for i in range(self.fs_params_form.rowCount()):
                field_widget = self.fs_params_form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
                label_for_field = self.fs_params_form.labelForField(field_widget)
                if label_for_field: 
                    if field_widget == self.fs_as_of_date_edit: label_for_field.setVisible(not is_pl_report and not is_gl_report)
                    elif field_widget == self.fs_start_date_edit: label_for_field.setVisible(is_pl_report or is_gl_report)
                    elif field_widget == self.fs_end_date_edit: label_for_field.setVisible(is_pl_report or is_gl_report)
        
        if is_gl_report:
             self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
             if not self._gl_accounts_cache: schedule_task_from_qt(self._load_gl_accounts_for_combo())
        elif report_type == "Balance Sheet": self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
        elif report_type == "Profit & Loss Statement": self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
        elif report_type == "Trial Balance": self.fs_display_stack.setCurrentWidget(self.tb_table_view)
        
        self._current_financial_report_data = None 
        current_view = self.fs_display_stack.currentWidget()
        if isinstance(current_view, QTreeView):
            model = current_view.model()
            if isinstance(model, QStandardItemModel): model.clear()
        elif isinstance(current_view, QTableView):
            model = current_view.model()
            if hasattr(model, 'update_data'): model.update_data({}) 
        elif current_view == self.gl_widget_container: 
             self.gl_model.update_data({}) 
             self.gl_summary_label_account.setText("Account: N/A")
             self.gl_summary_label_period.setText("Period: N/A")
             self.gl_summary_label_ob.setText("Opening Balance: 0.00")
             self.gl_summary_label_cb.setText("Closing Balance: 0.00")
        elif hasattr(current_view, 'clear'): 
             current_view.clear()

        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)

    async def _load_gl_accounts_for_combo(self):
        if not self.app_core.chart_of_accounts_manager: self.app_core.logger.error("ChartOfAccountsManager not available for GL account combo."); return
        try:
            accounts_orm: List[Account] = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            self._gl_accounts_cache = [{"id": acc.id, "code": acc.code, "name": acc.name} for acc in accounts_orm]
            accounts_json = json.dumps(self._gl_accounts_cache, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_gl_account_combo_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, accounts_json))
        except Exception as e: self.app_core.logger.error(f"Error loading accounts for GL combo: {e}", exc_info=True); QMessageBox.warning(self, "Account Load Error", "Could not load accounts for General Ledger selection.")

    @Slot(str)
    def _populate_gl_account_combo_slot(self, accounts_json_str: str):
        self.fs_gl_account_combo.clear()
        try:
            accounts_data = json.loads(accounts_json_str); self._gl_accounts_cache = accounts_data if accounts_data else []
            self.fs_gl_account_combo.addItem("-- Select Account --", 0) 
            for acc_data in self._gl_accounts_cache: self.fs_gl_account_combo.addItem(f"{acc_data['code']} - {acc_data['name']}", acc_data['id'])
        except json.JSONDecodeError: self.app_core.logger.error("Failed to parse accounts JSON for GL combo."); self.fs_gl_account_combo.addItem("Error loading accounts", 0)

    @Slot()
    def _on_generate_financial_report_clicked(self):
        report_type = self.fs_report_type_combo.currentText()
        if not self.app_core.financial_statement_generator: QMessageBox.critical(self, "Error", "Financial Statement Generator not available."); return
        self.generate_fs_button.setEnabled(False); self.generate_fs_button.setText("Generating...")
        self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False); 
        
        current_display_widget = self.fs_display_stack.currentWidget()
        if isinstance(current_display_widget, QTreeView):
            model = current_display_widget.model()
            if isinstance(model, QStandardItemModel): model.clear()
        elif isinstance(current_display_widget, QTableView):
            model = current_display_widget.model()
            if hasattr(model, 'update_data'): model.update_data({}) 
        elif current_display_widget == self.gl_widget_container :
            self.gl_model.update_data({}) 
            self.gl_summary_label_account.setText("Account: N/A"); self.gl_summary_label_period.setText("Period: N/A")
            self.gl_summary_label_ob.setText("Opening Balance: 0.00"); self.gl_summary_label_cb.setText("Closing Balance: 0.00")

        coro: Optional[Any] = None 
        if report_type == "Balance Sheet": as_of_date = self.fs_as_of_date_edit.date().toPython(); coro = self.app_core.financial_statement_generator.generate_balance_sheet(as_of_date)
        elif report_type == "Profit & Loss Statement": 
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython(); 
            if start_date > end_date: 
                QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for P&L.")
                self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
                return
            coro = self.app_core.financial_statement_generator.generate_profit_loss(start_date, end_date)
        elif report_type == "Trial Balance": as_of_date = self.fs_as_of_date_edit.date().toPython(); coro = self.app_core.financial_statement_generator.generate_trial_balance(as_of_date)
        elif report_type == "General Ledger":
            account_id = self.fs_gl_account_combo.currentData(); 
            if not isinstance(account_id, int) or account_id == 0: QMessageBox.warning(self, "Selection Error", "Please select a valid account for the General Ledger report."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            start_date = self.fs_start_date_edit.date().toPython(); end_date = self.fs_end_date_edit.date().toPython()
            if start_date > end_date: QMessageBox.warning(self, "Date Error", "Start date cannot be after end date for General Ledger."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report"); return
            coro = self.app_core.financial_statement_generator.generate_general_ledger(account_id, start_date, end_date)
        if coro:
            future = schedule_task_from_qt(coro)
            if future: future.add_done_callback(self._handle_financial_report_result)
            else: self._handle_financial_report_result(None)
        else: QMessageBox.warning(self, "Selection Error", "Invalid report type selected or parameters missing."); self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")

    def _handle_financial_report_result(self, future):
        self.generate_fs_button.setEnabled(True); self.generate_fs_button.setText("Generate Report")
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report generation."); return
        try:
            report_data: Optional[Dict[str, Any]] = future.result() 
            if report_data: self._current_financial_report_data = report_data; self._display_financial_report(report_data); self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
            else: QMessageBox.warning(self, "Report Error", "Failed to generate report data or report data is empty.")
        except Exception as e: self.app_core.logger.error(f"Exception handling financial report result: {e}", exc_info=True); QMessageBox.critical(self, "Report Generation Error", f"An unexpected error occurred: {str(e)}")

    def _populate_hierarchical_model(self, model: QStandardItemModel, report_data: Dict[str, Any], section_keys: List[str], title_key: str = "name", balance_key: str = "balance"):
        model.clear()
        headers = ["Description", "Amount"] 
        model.setHorizontalHeaderLabels(headers)
        root_node = model.invisibleRootItem()
        bold_font = QFont(); bold_font.setBold(True)
        for section_id in section_keys: 
            section_data = report_data.get(section_id)
            if not section_data: continue
            section_title = section_data.get("title_display_name", section_id.replace('_', ' ').title()) 
            section_item = QStandardItem(section_title); section_item.setFont(bold_font)
            empty_amount_item = QStandardItem(""); empty_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root_node.appendRow([section_item, empty_amount_item])
            for acc_dict in section_data.get("accounts", []):
                desc_text = f"{acc_dict.get('code','')} - {acc_dict.get(title_key,'')}"
                acc_desc_item = QStandardItem(desc_text)
                acc_balance_item = QStandardItem(self._format_decimal_for_display(acc_dict.get(balance_key)))
                acc_balance_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                section_item.appendRow([acc_desc_item, acc_balance_item])
            total_desc_item = QStandardItem(f"Total {section_title}"); total_desc_item.setFont(bold_font)
            total_amount_item = QStandardItem(self._format_decimal_for_display(section_data.get("total"))); total_amount_item.setFont(bold_font); total_amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            section_item.appendRow([total_desc_item, total_amount_item])
        if report_data.get('title') == "Profit & Loss Statement" and 'net_profit' in report_data:
            net_profit_desc = QStandardItem("Net Profit / (Loss)"); net_profit_desc.setFont(bold_font)
            net_profit_amount = QStandardItem(self._format_decimal_for_display(report_data.get('net_profit'))); net_profit_amount.setFont(bold_font); net_profit_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root_node.appendRow([QStandardItem(""), QStandardItem("")]); root_node.appendRow([net_profit_desc, net_profit_amount])
        elif report_data.get('title') == "Balance Sheet" and 'total_liabilities_equity' in report_data:
            total_lia_eq_desc = QStandardItem("Total Liabilities & Equity"); total_lia_eq_desc.setFont(bold_font)
            total_lia_eq_amount = QStandardItem(self._format_decimal_for_display(report_data.get('total_liabilities_equity'))); total_lia_eq_amount.setFont(bold_font); total_lia_eq_amount.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root_node.appendRow([QStandardItem(""), QStandardItem("")]); root_node.appendRow([total_lia_eq_desc, total_lia_eq_amount])
            if report_data.get('is_balanced') is False: warning_item = QStandardItem("Warning: Balance Sheet is out of balance!"); warning_item.setForeground(QColor("red")); warning_item.setFont(bold_font); root_node.appendRow([warning_item,QStandardItem("")])

    def _display_financial_report(self, report_data: Dict[str, Any]):
        report_title = report_data.get('title', '')
        
        if report_title == "Balance Sheet":
            self.fs_display_stack.setCurrentWidget(self.bs_tree_view)
            self._populate_hierarchical_model(self.bs_model, report_data, ['assets', 'liabilities', 'equity'])
            self.bs_tree_view.expandAll()
            for i in range(self.bs_model.columnCount()): self.bs_tree_view.resizeColumnToContents(i)
        elif report_title == "Profit & Loss Statement":
            self.fs_display_stack.setCurrentWidget(self.pl_tree_view)
            self._populate_hierarchical_model(self.pl_model, report_data, ['revenue', 'expenses'])
            self.pl_tree_view.expandAll()
            for i in range(self.pl_model.columnCount()): self.pl_tree_view.resizeColumnToContents(i)
        elif report_title == "Trial Balance":
            self.fs_display_stack.setCurrentWidget(self.tb_table_view)
            self.tb_model.update_data(report_data)
            for i in range(self.tb_model.columnCount()): self.tb_table_view.resizeColumnToContents(i)
        elif report_title == "General Ledger":
            self.fs_display_stack.setCurrentWidget(self.gl_widget_container)
            self.gl_model.update_data(report_data) 
            gl_summary_data = self.gl_model.get_report_summary() 
            self.gl_summary_label_account.setText(f"Account: {gl_summary_data['account_name']}")
            self.gl_summary_label_period.setText(gl_summary_data['period_description'])
            self.gl_summary_label_ob.setText(f"Opening Balance: {self._format_decimal_for_display(gl_summary_data['opening_balance'], show_zero_as_blank=False)}")
            self.gl_summary_label_cb.setText(f"Closing Balance: {self._format_decimal_for_display(gl_summary_data['closing_balance'], show_zero_as_blank=False)}")
            for i in range(self.gl_model.columnCount()): self.gl_table_view.resizeColumnToContents(i)
        else:
            default_view = self.bs_tree_view 
            self.fs_display_stack.setCurrentWidget(default_view)
            current_model = default_view.model()
            if isinstance(current_model, QStandardItemModel):
                current_model.clear()
            self.app_core.logger.warning(f"Unhandled report title '{report_title}' for specific display. Showing empty default.")
            QMessageBox.warning(self, "Display Error", f"Display format for '{report_title}' is not yet implemented.")

    @Slot(str)
    def _on_export_report_clicked(self, format_type: str):
        if not self._current_financial_report_data: QMessageBox.warning(self, "No Report", "Please generate a report first before exporting."); return
        report_title = self._current_financial_report_data.get('title', 'FinancialReport').replace(' ', '_').replace('&', 'And').replace('/', '-').replace(':', '') 
        default_filename = f"{report_title}_{python_date.today().strftime('%Y%m%d')}.{format_type}"
        documents_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        if not documents_path: documents_path = os.path.expanduser("~") 
        file_path, _ = QFileDialog.getSaveFileName(self, f"Save {format_type.upper()} Report", os.path.join(documents_path, default_filename), f"{format_type.upper()} Files (*.{format_type});;All Files (*)")
        if file_path:
            self.export_pdf_button.setEnabled(False); self.export_excel_button.setEnabled(False)
            future = schedule_task_from_qt(self.app_core.report_engine.export_report(self._current_financial_report_data, format_type)) 
            if future: future.add_done_callback(lambda f, fp=file_path, ft=format_type: self._handle_export_result(f, fp, ft))
            else: self._handle_export_result(None, file_path, format_type)

    def _handle_export_result(self, future, file_path: str, format_type: str):
        self.export_pdf_button.setEnabled(True); self.export_excel_button.setEnabled(True)
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule report export."); return
        try:
            report_bytes: Optional[bytes] = future.result()
            if report_bytes:
                with open(file_path, "wb") as f: f.write(report_bytes)
                QMessageBox.information(self, "Export Successful", f"Report exported to:\n{file_path}")
            else: QMessageBox.warning(self, "Export Failed", f"Failed to generate report bytes for {format_type.upper()}.")
        except Exception as e: self.app_core.logger.error(f"Exception handling report export result: {e}", exc_info=True); QMessageBox.critical(self, "Export Error", f"An error occurred during export: {str(e)}")


```

# app/ui/reports/general_ledger_table_model.py
```py
# app/ui/reports/general_ledger_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import date as python_date

class GeneralLedgerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
        self._transactions: List[Dict[str, Any]] = []
        self._opening_balance = Decimal(0)
        self._closing_balance = Decimal(0)
        self._account_name = ""
        self._period_description = ""

        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +2 for opening and closing balance rows if we display them in table
        # For now, let's assume they are displayed outside the table by the widget
        return len(self._transactions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal], show_zero_as_blank: bool = True) -> str:
        if value is None: return ""
        if show_zero_as_blank and value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._transactions)): return None
            
        txn = self._transactions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: # Date
                raw_date = txn.get("date")
                return raw_date.strftime('%d/%m/%Y') if isinstance(raw_date, python_date) else str(raw_date)
            if col == 1: return txn.get("entry_no", "") # Entry No.
            if col == 2: # Description
                desc = txn.get("je_description", "")
                line_desc = txn.get("line_description", "")
                return f"{desc} // {line_desc}" if desc and line_desc else (desc or line_desc)
            if col == 3: return self._format_decimal_for_display(txn.get("debit"), True)  # Debit
            if col == 4: return self._format_decimal_for_display(txn.get("credit"), True) # Credit
            if col == 5: return self._format_decimal_for_display(txn.get("balance"), False) # Balance (show zero)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4, 5]: # Debit, Credit, Balance
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._transactions = report_data.get('transactions', [])
        self._opening_balance = report_data.get('opening_balance', Decimal(0))
        self._closing_balance = report_data.get('closing_balance', Decimal(0))
        self._account_name = f"{report_data.get('account_code','')} - {report_data.get('account_name','')}"
        start = report_data.get('start_date')
        end = report_data.get('end_date')
        self._period_description = f"For {start.strftime('%d/%m/%Y') if start else ''} to {end.strftime('%d/%m/%Y') if end else ''}"
        self.endResetModel()

    def get_report_summary(self) -> Dict[str, Any]:
        return {
            "account_name": self._account_name,
            "period_description": self._period_description,
            "opening_balance": self._opening_balance,
            "closing_balance": self._closing_balance
        }

```

# app/ui/reports/trial_balance_table_model.py
```py
# app/ui/reports/trial_balance_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal

class TrialBalanceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[Dict[str, Any]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["Account Code", "Account Name", "Debit", "Credit"]
        self._debit_accounts: List[Dict[str, Any]] = []
        self._credit_accounts: List[Dict[str, Any]] = []
        self._totals: Dict[str, Decimal] = {"debits": Decimal(0), "credits": Decimal(0)}
        self._is_balanced: bool = False
        if data:
            self.update_data(data)

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        # +1 for the totals row
        return len(self._debit_accounts) + len(self._credit_accounts) + 1 

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None or value == Decimal(0): return "" # Show blank for zero in TB lines
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row = index.row()
        col = index.column()

        num_debit_accounts = len(self._debit_accounts)
        num_credit_accounts = len(self._credit_accounts)

        # Totals Row
        if row == num_debit_accounts + num_credit_accounts:
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 1: return "TOTALS"
                if col == 2: return f"{self._totals['debits']:,.2f}"
                if col == 3: return f"{self._totals['credits']:,.2f}"
                return ""
            elif role == Qt.ItemDataRole.FontRole:
                from PySide6.QtGui import QFont
                font = QFont(); font.setBold(True); return font
            elif role == Qt.ItemDataRole.TextAlignmentRole and col in [2,3]:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None

        # Debit Accounts
        if row < num_debit_accounts:
            account = self._debit_accounts[row]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return self._format_decimal_for_display(account.get("balance"))
                if col == 3: return "" # Credit column is blank for debit accounts
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        
        # Credit Accounts
        credit_row_index = row - num_debit_accounts
        if credit_row_index < num_credit_accounts:
            account = self._credit_accounts[credit_row_index]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return "" # Debit column is blank for credit accounts
                if col == 3: return self._format_decimal_for_display(account.get("balance"))
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 3:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
            
        return None

    def update_data(self, report_data: Dict[str, Any]):
        self.beginResetModel()
        self._debit_accounts = report_data.get('debit_accounts', [])
        self._credit_accounts = report_data.get('credit_accounts', [])
        self._totals["debits"] = report_data.get('total_debits', Decimal(0))
        self._totals["credits"] = report_data.get('total_credits', Decimal(0))
        self._is_balanced = report_data.get('is_balanced', False)
        self.endResetModel()

    def get_balance_status(self) -> str:
        return "Balanced" if self._is_balanced else f"Out of Balance by: {abs(self._totals['debits'] - self._totals['credits']):,.2f}"

```

# app/ui/accounting/journal_entry_table_model.py
```py
# app/ui/accounting/journal_entry_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date # Alias to avoid conflict with Qt's QDate

class JournalEntryTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None, parent=None):
        super().__init__(parent)
        # Headers match the expected dictionary keys from JournalEntryManager.get_journal_entries_for_listing
        self._headers = ["ID", "Entry No.", "Date", "Description", "Type", "Total", "Status"]
        self._data: List[Dict[str, Any]] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): # This model is flat, no children
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        entry_summary = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace('.', '').replace(' ', '_') # "Entry No." -> "entry_no"
            
            if header_key == "id": return str(entry_summary.get("id", "")) # Display ID as string
            if header_key == "entry_no": return entry_summary.get("entry_no", "")
            if header_key == "date": 
                raw_date = entry_summary.get("date")
                if isinstance(raw_date, python_date): return raw_date.strftime('%d/%m/%Y')
                # Assuming date might come as string from JSON, ensure it's parsed if needed by json_date_hook earlier
                if isinstance(raw_date, str): # Should have been converted by json_date_hook
                     try: return python_date.fromisoformat(raw_date).strftime('%d/%m/%Y')
                     except ValueError: return raw_date # Fallback
                return ""
            if header_key == "description": return entry_summary.get("description", "")
            if header_key == "type": return entry_summary.get("type", "")
            if header_key == "total": # Corresponds to "total_amount" key in data dict
                val = entry_summary.get("total_amount")
                try: return f"{Decimal(str(val) if val is not None else '0'):,.2f}"
                except (InvalidOperation, TypeError): return str(val) if val is not None else "0.00"
            if header_key == "status": return entry_summary.get("status", "")
            
            # Fallback for any unhandled column, though all should be covered
            return entry_summary.get(header_key, "")

        elif role == Qt.ItemDataRole.UserRole: # Store complex data if needed, e.g., full object or just ID
            # Typically, for quick access to the ID without parsing display text
            if col == 0: # Store ID with the first column for convenience
                 return entry_summary.get("id")
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Total": # Align "Total" amount to the right
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        
        return None

    def get_journal_entry_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Prefer UserRole if ID is stored there, otherwise parse from display data (less ideal)
            index = self.index(row, 0) # Assuming ID is in/associated with the first column
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole not used or ID not stored there, try from dict directly
            return self._data[row].get("id")
        return None
        
    def get_journal_entry_status_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].get("status")
        return None

    def update_data(self, new_data: List[Dict[str, Any]]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


```

# app/ui/accounting/__init__.py
```py
# File: app/ui/accounting/__init__.py
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog
from .fiscal_year_dialog import FiscalYearDialog 
from .journal_entry_dialog import JournalEntryDialog # Added
from .journal_entries_widget import JournalEntriesWidget # Added
from .journal_entry_table_model import JournalEntryTableModel # Added

__all__ = [
    "AccountingWidget", 
    "ChartOfAccountsWidget", 
    "AccountDialog",
    "FiscalYearDialog", 
    "JournalEntryDialog",
    "JournalEntriesWidget",
    "JournalEntryTableModel",
]

```

# app/ui/accounting/chart_of_accounts_widget.py
```py
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction, QColor
from decimal import Decimal, InvalidOperation
from datetime import date 
import asyncio 
import json # For JSON serialization
from typing import Optional, Dict, Any, List 

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 
from app.main import schedule_task_from_qt 

# Helper for JSON serialization with Decimal and date
def json_converter(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

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
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                    Q_ARG(str,"Accounting service (ChartOfAccountsManager) or get_account_tree method not available."))
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            json_data = json.dumps(account_tree_data, default=json_converter)
            
            QMetaObject.invokeMethod(self, "_update_account_model_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data))
            
        except Exception as e:
            error_message = f"Failed to load accounts: {str(e)}"
            print(error_message) 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(str) 
    def _update_account_model_slot(self, account_tree_json_str: str):
        try:
            account_tree_data: List[Dict[str, Any]] = json.loads(account_tree_json_str)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Failed to parse account data: {e}")
            return

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
        
        ob_str = account_data.get('opening_balance', "0.00")
        try:
            ob_val = Decimal(str(ob_str))
        except InvalidOperation:
            ob_val = Decimal(0)
        ob_item = QStandardItem(f"{ob_val:,.2f}")
        ob_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Handle opening_balance_date if it's in ISO format string
        ob_date_str = account_data.get('opening_balance_date')
        if ob_date_str:
            try:
                # Potentially store/display QDate.fromString(ob_date_str, Qt.DateFormat.ISODate)
                pass # For now, just displaying balance
            except Exception:
                pass


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
            json_data_to_pass = json.dumps(data_to_pass, default=json_converter)
            QMetaObject.invokeMethod(self, "_confirm_and_toggle_status_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data_to_pass))
        except Exception as e:
            error_message = f"Failed to prepare toggle account active status: {str(e)}"
            print(error_message)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, error_message))

    @Slot(str) 
    def _confirm_and_toggle_status_slot(self, data_json_str: str):
        try:
            data: Dict[str, Any] = json.loads(data_json_str)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Error", f"Failed to parse toggle status data: {e}")
            return

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
                schedule_task_from_qt(self._load_accounts()) 
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

# app/ui/accounting/journal_entries_widget.py
```py
# app/ui/accounting/journal_entries_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QDateEdit, QComboBox, QInputDialog, QLineEdit,
    QFormLayout 
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QDate, QSize
from PySide6.QtGui import QIcon, QAction 
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json
from datetime import date as python_date 
from decimal import Decimal

from app.ui.accounting.journal_entry_dialog import JournalEntryDialog
from app.ui.accounting.journal_entry_table_model import JournalEntryTableModel
# from app.common.enums import JournalTypeEnum # Not directly used in this file's logic
from app.main import schedule_task_from_qt
# from app.utils.pydantic_models import JournalEntryData # Not directly used by widget
from app.models.accounting.journal_entry import JournalEntry 
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalEntriesWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for JournalEntriesWidget.")
        except ImportError:
            self.app_core.logger.info("JournalEntriesWidget: Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            pass

        self._init_ui()
        QTimer.singleShot(0, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        filter_group_layout = QHBoxLayout()
        filter_layout_form = QFormLayout()
        filter_layout_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-1))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")

        self.entry_no_filter_edit = QLineEdit(); self.entry_no_filter_edit.setPlaceholderText("Filter by Entry No.")
        self.description_filter_edit = QLineEdit(); self.description_filter_edit.setPlaceholderText("Filter by Description")
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItems(["All", "Draft", "Posted"])
        
        filter_layout_form.addRow("From Date:", self.start_date_filter_edit)
        filter_layout_form.addRow("To Date:", self.end_date_filter_edit)
        filter_layout_form.addRow("Entry No.:", self.entry_no_filter_edit)
        filter_layout_form.addRow("Description:", self.description_filter_edit)
        filter_layout_form.addRow("Status:", self.status_filter_combo)
        filter_group_layout.addLayout(filter_layout_form)

        filter_button_layout = QVBoxLayout()
        self.apply_filter_button = QPushButton(
            QIcon.fromTheme("edit-find", QIcon(self.icon_path_prefix + "filter.svg")),
            "Apply Filter"
        )
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_entries()))
        
        self.clear_filter_button = QPushButton(
            QIcon.fromTheme("edit-clear", QIcon(self.icon_path_prefix + "refresh.svg")),
            "Clear Filters"
        )
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        
        filter_button_layout.addWidget(self.apply_filter_button)
        filter_button_layout.addWidget(self.clear_filter_button)
        filter_button_layout.addStretch()
        filter_group_layout.addLayout(filter_button_layout)
        filter_group_layout.addStretch(1)
        self.main_layout.addLayout(filter_group_layout)

        self.entries_table = QTableView()
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.entries_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_view_entry_double_click) 
        self.entries_table.setSortingEnabled(True)

        # Create and set the model FIRST
        self.table_model = JournalEntryTableModel()
        self.entries_table.setModel(self.table_model)

        # Now configure header and columns using self.table_model
        header = self.entries_table.horizontalHeader()
        header.setStretchLastSection(False) 
        
        # Set default resize mode for all columns first
        for i in range(self.table_model.columnCount()): # Use model's column count
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        # Hide ID column (model index 0, assuming headers are ["ID", "Entry No.", ...])
        id_column_model_index = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else 0
        self.entries_table.setColumnHidden(id_column_model_index, True)
        
        # Specifically set stretch for "Description" column
        # "Description" is model index 3. If "ID" (model index 0) is hidden,
        # visible indices are: Entry No (0), Date (1), Description (2), Type (3), Total (4), Status (5)
        # So, visible index for "Description" is 2.
        description_column_visible_index = 2 
        header.setSectionResizeMode(description_column_visible_index, QHeaderView.ResizeMode.Stretch)
        
        self._create_toolbar() 
        self.main_layout.addWidget(self.toolbar) 
        self.main_layout.addWidget(self.entries_table) 
        self.setLayout(self.main_layout)

    @Slot()
    def _clear_filters_and_load(self):
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-1))
        self.end_date_filter_edit.setDate(QDate.currentDate())
        self.entry_no_filter_edit.clear()
        self.description_filter_edit.clear()
        self.status_filter_combo.setCurrentText("All")
        schedule_task_from_qt(self._load_entries())

    def _create_toolbar(self):
        self.toolbar = QToolBar("Journal Entries Toolbar")
        self.toolbar.setObjectName("JournalEntriesToolbar")
        self.toolbar.setIconSize(QSize(16, 16)) 

        self.new_entry_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New Entry", self) 
        self.new_entry_action.triggered.connect(self.on_new_entry)
        self.toolbar.addAction(self.new_entry_action)

        self.edit_entry_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.edit_entry_action.triggered.connect(self.on_edit_entry)
        self.toolbar.addAction(self.edit_entry_action)
        
        self.view_entry_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View Entry", self) 
        self.view_entry_action.triggered.connect(self.on_view_entry_toolbar) 
        self.toolbar.addAction(self.view_entry_action)

        self.toolbar.addSeparator()

        self.post_entry_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post Selected", self) 
        self.post_entry_action.triggered.connect(self.on_post_entry)
        self.toolbar.addAction(self.post_entry_action)
        
        self.reverse_entry_action = QAction(QIcon(self.icon_path_prefix + "reverse.svg"), "Reverse Selected", self) 
        self.reverse_entry_action.triggered.connect(self.on_reverse_entry)
        self.toolbar.addAction(self.reverse_entry_action)

        self.toolbar.addSeparator()
        self.refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_entries()))
        self.toolbar.addAction(self.refresh_action)

        if self.entries_table.selectionModel():
            self.entries_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states() 

    @Slot()
    def _update_action_states(self):
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        has_selection = bool(selected_indexes)
        is_draft = False; is_posted = False; single_selection = len(selected_indexes) == 1

        if single_selection:
            first_selected_row = selected_indexes[0].row()
            status = self.table_model.get_journal_entry_status_at_row(first_selected_row)
            if status is not None: 
                is_draft = status == "Draft" 
                is_posted = status == "Posted"
        
        can_post_any_draft = False
        if has_selection: 
            for index in selected_indexes:
                if self.table_model.get_journal_entry_status_at_row(index.row()) == "Draft":
                    can_post_any_draft = True; break
        
        self.edit_entry_action.setEnabled(single_selection and is_draft)
        self.view_entry_action.setEnabled(single_selection)
        self.post_entry_action.setEnabled(can_post_any_draft) 
        self.reverse_entry_action.setEnabled(single_selection and is_posted)

    async def _load_entries(self):
        if not self.app_core.journal_entry_manager:
            error_msg = "Journal Entry Manager not available."
            self.app_core.logger.critical(error_msg)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Critical Error"), Q_ARG(str, error_msg))
            return
        try:
            start_date = self.start_date_filter_edit.date().toPython()
            end_date = self.end_date_filter_edit.date().toPython()
            status_text = self.status_filter_combo.currentText()
            status_filter = status_text if status_text != "All" else None
            entry_no_filter_text = self.entry_no_filter_edit.text().strip()
            description_filter_text = self.description_filter_edit.text().strip()

            filters = {"start_date": start_date, "end_date": end_date, "status": status_filter,
                       "entry_no": entry_no_filter_text or None, 
                       "description": description_filter_text or None}
            
            result: Result[List[Dict[str, Any]]] = await self.app_core.journal_entry_manager.get_journal_entries_for_listing(filters=filters)
            
            if result.is_success:
                entries_data_for_table = result.value if result.value is not None else []
                json_data = json.dumps(entries_data_for_table, default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load journal entries: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading journal entries: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
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

    def _get_selected_entry_id_and_status(self, require_single_selection: bool = True) -> tuple[Optional[int], Optional[str]]:
        selected_indexes = self.entries_table.selectionModel().selectedRows()
        if not selected_indexes:
            if require_single_selection: QMessageBox.information(self, "Selection", "Please select a journal entry.")
            return None, None
        if require_single_selection and len(selected_indexes) > 1:
            QMessageBox.information(self, "Selection", "Please select only a single journal entry for this action.")
            return None, None
        
        row = selected_indexes[0].row() 
        entry_id = self.table_model.get_journal_entry_id_at_row(row)
        entry_status = self.table_model.get_journal_entry_status_at_row(row)
        return entry_id, entry_status

    @Slot()
    def on_edit_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        if entry_status != "Draft": QMessageBox.warning(self, "Edit Error", "Only draft entries can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to edit."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, parent=self)
        dialog.journal_entry_saved.connect(lambda _id: schedule_task_from_qt(self._load_entries()))
        dialog.exec()

    @Slot(QModelIndex) 
    def on_view_entry_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    @Slot()
    def on_view_entry_toolbar(self): 
        entry_id, _ = self._get_selected_entry_id_and_status()
        if entry_id is None: return
        self._show_view_entry_dialog(entry_id)

    def _show_view_entry_dialog(self, entry_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = JournalEntryDialog(self.app_core, self.app_core.current_user.id, journal_entry_id=entry_id, view_only=True, parent=self)
        dialog.exec()

    @Slot()
    def on_post_entry(self):
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select draft journal entries to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post entries."); return
        entries_to_post_ids = []
        for index in selected_rows:
            entry_id = self.table_model.get_journal_entry_id_at_row(index.row())
            entry_status = self.table_model.get_journal_entry_status_at_row(index.row())
            if entry_id and entry_status == "Draft": entries_to_post_ids.append(entry_id)
        if not entries_to_post_ids: QMessageBox.information(self, "Selection", "No draft entries selected for posting."); return
        schedule_task_from_qt(self._perform_post_entries(entries_to_post_ids, self.app_core.current_user.id))

    async def _perform_post_entries(self, entry_ids: List[int], user_id: int):
        if not self.app_core.journal_entry_manager: 
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        success_count = 0; errors = []
        for entry_id_to_post in entry_ids:
            result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(entry_id_to_post, user_id)
            if result.is_success: success_count += 1
            else:
                je_no_str = f"ID {entry_id_to_post}" 
                try:
                    temp_je = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(entry_id_to_post)
                    if temp_je: je_no_str = temp_je.entry_no
                except Exception: pass
                errors.append(f"Entry {je_no_str}: {', '.join(result.errors)}")
        message = f"{success_count} of {len(entry_ids)} entries posted."
        if errors: message += "\n\nErrors:\n" + "\n".join(errors)
        msg_box_method = QMessageBox.information if not errors and success_count > 0 else QMessageBox.warning
        title = "Posting Complete" if not errors and success_count > 0 else ("Posting Failed" if success_count == 0 else "Posting Partially Failed")
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, message))
        if success_count > 0: schedule_task_from_qt(self._load_entries())


    @Slot()
    def on_reverse_entry(self):
        entry_id, entry_status = self._get_selected_entry_id_and_status()
        if entry_id is None or entry_status != "Posted": QMessageBox.warning(self, "Reverse Error", "Only single, posted entries can be reversed."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to reverse entries."); return
        reply = QMessageBox.question(self, "Confirm Reversal", 
                                     f"Are you sure you want to reverse journal entry ID {entry_id}?\nA new counter-entry will be created as a DRAFT.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
        reversal_date_str, ok_date = QInputDialog.getText(self, "Reversal Date", "Enter reversal date (YYYY-MM-DD):", QLineEdit.EchoMode.Normal, python_date.today().isoformat())
        if ok_date and reversal_date_str:
            try:
                parsed_reversal_date = python_date.fromisoformat(reversal_date_str)
                reversal_desc_str, ok_desc = QInputDialog.getText(self, "Reversal Description", "Enter description for reversal entry (optional):", QLineEdit.EchoMode.Normal, f"Reversal of JE {entry_id}")
                if ok_desc: 
                    schedule_task_from_qt(self._perform_reverse_entry(entry_id, parsed_reversal_date, reversal_desc_str, self.app_core.current_user.id))
                else: QMessageBox.information(self, "Cancelled", "Reversal description input cancelled.")
            except ValueError: QMessageBox.warning(self, "Invalid Date", "Reversal date format is invalid. Please use YYYY-MM-DD.")
        else: QMessageBox.information(self, "Cancelled", "Reversal date input cancelled.")

    async def _perform_reverse_entry(self, entry_id: int, reversal_date: python_date, description: str, user_id: int):
        if not self.app_core.journal_entry_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
            return
        result: Result[JournalEntry] = await self.app_core.journal_entry_manager.reverse_journal_entry(entry_id, reversal_date, description, user_id)
        if result.is_success and result.value:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Journal entry ID {entry_id} reversed. New reversal entry: {result.value.entry_no} (Draft)."))
            schedule_task_from_qt(self._load_entries())
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Reversal Error"), Q_ARG(str, f"Failed to reverse journal entry:\n{', '.join(result.errors)}"))


```

# app/ui/accounting/fiscal_year_dialog.py
```py
# File: app/ui/accounting/fiscal_year_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, 
    QComboBox, QPushButton, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt, QDate, Slot
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import date as python_date # Alias to avoid conflict with QDate

from app.utils.pydantic_models import FiscalYearCreateData

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class FiscalYearDialog(QDialog):
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self._fiscal_year_data: Optional[FiscalYearCreateData] = None
        self._previous_start_date: Optional[QDate] = None # For default end date logic

        self.setWindowTitle("Add New Fiscal Year")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._set_initial_dates() # Set initial default dates

    def _init_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.year_name_edit = QLineEdit()
        self.year_name_edit.setPlaceholderText("e.g., FY2024 or Y/E 31 Dec 2024")
        form_layout.addRow("Fiscal Year Name*:", self.year_name_edit)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("Start Date*:", self.start_date_edit)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat("dd/MM/yyyy")
        form_layout.addRow("End Date*:", self.end_date_edit)
        
        self.start_date_edit.dateChanged.connect(self._update_default_end_date)

        self.auto_generate_periods_combo = QComboBox()
        self.auto_generate_periods_combo.addItems(["Monthly", "Quarterly", "None"])
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        form_layout.addRow("Auto-generate Periods:", self.auto_generate_periods_combo)

        layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept_data)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def _set_initial_dates(self):
        today = QDate.currentDate()
        # Default start: first day of current month, or Jan 1st if typical
        default_start = QDate(today.year(), 1, 1) # Default to Jan 1st of current year
        # If current date is past June, suggest starting next year's FY
        if today.month() > 6:
            default_start = QDate(today.year() + 1, 1, 1)
        
        default_end = default_start.addYears(1).addDays(-1)
        
        self.start_date_edit.setDate(default_start)
        self.end_date_edit.setDate(default_end) 
        self._previous_start_date = default_start


    @Slot(QDate)
    def _update_default_end_date(self, new_start_date: QDate):
        # Only update if the end date seems to be following the start date automatically
        # or if it's the initial setup.
        if self._previous_start_date is None: # Initial setup
            self._previous_start_date = self.start_date_edit.date() # Could be different from new_start_date if called by setDate initially
        
        # Calculate expected end based on previous start
        expected_end_from_prev_start = self._previous_start_date.addYears(1).addDays(-1)
        
        # If current end date matches the old default, then update it based on new start date
        if self.end_date_edit.date() == expected_end_from_prev_start:
            self.end_date_edit.setDate(new_start_date.addYears(1).addDays(-1))
        
        self._previous_start_date = new_start_date


    @Slot()
    def accept_data(self):
        """Validate and store data before accepting the dialog."""
        year_name = self.year_name_edit.text().strip()
        start_date_py: python_date = self.start_date_edit.date().toPython() 
        end_date_py: python_date = self.end_date_edit.date().toPython()
        auto_generate_str = self.auto_generate_periods_combo.currentText()
        auto_generate_periods = auto_generate_str if auto_generate_str != "None" else None

        errors = []
        if not year_name:
            errors.append("Fiscal Year Name is required.")
        if start_date_py >= end_date_py:
            errors.append("End Date must be after Start Date.")
        
        days_in_year = (end_date_py - start_date_py).days + 1
        if not (300 < days_in_year < 400): # Heuristic for typical year length
             errors.append("Fiscal year duration seems unusual (typically around 365 days). Please verify dates.")

        if errors:
            QMessageBox.warning(self, "Validation Error", "\n".join(errors))
            return # Do not accept

        try:
            self._fiscal_year_data = FiscalYearCreateData(
                year_name=year_name,
                start_date=start_date_py,
                end_date=end_date_py,
                auto_generate_periods=auto_generate_periods,
                user_id=self.current_user_id # Passed in from calling widget
            )
            super().accept() 
        except Exception as e: 
            QMessageBox.warning(self, "Data Error", f"Invalid data: {str(e)}")


    def get_fiscal_year_data(self) -> Optional[FiscalYearCreateData]:
        return self._fiscal_year_data

    def open(self) -> int: 
        self._fiscal_year_data = None
        self.year_name_edit.clear()
        self._set_initial_dates() # Reset dates to default for a new entry
        self.auto_generate_periods_combo.setCurrentText("Monthly")
        self.year_name_edit.setFocus()
        return super().open()

```

# app/ui/accounting/accounting_widget.py
```py
# File: app/ui/accounting/accounting_widget.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from app.ui.accounting.chart_of_accounts_widget import ChartOfAccountsWidget
from app.ui.accounting.journal_entries_widget import JournalEntriesWidget # Import new widget
from app.core.application_core import ApplicationCore 

class AccountingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): 
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        
        self.coa_widget = ChartOfAccountsWidget(self.app_core)
        self.tab_widget.addTab(self.coa_widget, "Chart of Accounts")
        
        self.journal_entries_widget = JournalEntriesWidget(self.app_core) # Create instance
        self.tab_widget.addTab(self.journal_entries_widget, "Journal Entries") # Add as tab
        
        other_label = QLabel("Other Accounting Features (e.g., Fiscal Periods, Budgets)")
        self.tab_widget.addTab(other_label, "More...")

        self.setLayout(self.layout)

```

# app/ui/accounting/journal_entry_dialog.py
```py
# File: app/ui/accounting/journal_entry_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDateEdit, QComboBox,
    QPushButton, QDialogButtonBox, QMessageBox, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QDoubleSpinBox, QApplication, QStyledItemDelegate,
    QAbstractSpinBox # For QDoubleSpinBox.NoButtons
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon, QKeySequence, QColor, QPalette # QKeySequence not used here, but kept from original for consistency
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast

from decimal import Decimal, InvalidOperation
import json
from datetime import date as python_date

from app.utils.pydantic_models import JournalEntryData, JournalEntryLineData
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
# from app.models.accounting.currency import Currency # Not directly used for line combos
from app.models.accounting.journal_entry import JournalEntry 
from app.common.enums import JournalTypeEnum 
from app.main import schedule_task_from_qt
from app.utils.json_helpers import json_converter, json_date_hook 
from app.utils.result import Result 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from PySide6.QtGui import QPaintDevice # For QWidget type hint

class JournalEntryDialog(QDialog):
    journal_entry_saved = Signal(int) # Emits the ID of the saved/updated JE

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 journal_entry_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional["QWidget"] = None): # QWidget type hint
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.journal_entry_id = journal_entry_id
        self.view_only_mode = view_only 
        self.loaded_journal_entry_orm: Optional[JournalEntry] = None 
        self.existing_journal_entry_data_dict: Optional[Dict[str, Any]] = None

        self._accounts_cache: List[Account] = []
        self._tax_codes_cache: List[TaxCode] = []
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(900, 700)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.journal_entry_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_journal_entry()))
        elif not self.view_only_mode: 
            self._add_new_line() 
            self._add_new_line() 

    def _get_window_title(self) -> str:
        if self.view_only_mode: return "View Journal Entry"
        if self.journal_entry_id: return "Edit Journal Entry"
        return "New Journal Entry"

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        self.header_form = QFormLayout() # Made it an instance variable for disabling fields
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.entry_date_edit = QDateEdit(QDate.currentDate())
        self.entry_date_edit.setCalendarPopup(True)
        self.entry_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.header_form.addRow("Entry Date*:", self.entry_date_edit)

        self.journal_type_combo = QComboBox()
        for jt_enum_member in JournalTypeEnum: self.journal_type_combo.addItem(jt_enum_member.value, jt_enum_member.value)
        self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value)
        self.header_form.addRow("Journal Type:", self.journal_type_combo)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Overall description for the journal entry")
        self.header_form.addRow("Description:", self.description_edit)

        self.reference_edit = QLineEdit()
        self.reference_edit.setPlaceholderText("e.g., Invoice #, Check #, Source Document ID")
        self.header_form.addRow("Reference:", self.reference_edit)
        
        main_layout.addLayout(self.header_form)

        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(7) 
        self.lines_table.setHorizontalHeaderLabels([
            "Account*", "Description", "Debit*", "Credit*", 
            "Tax Code", "Tax Amt", "" 
        ])
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) 
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) 
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed) 
        self.lines_table.setColumnWidth(2, 130); self.lines_table.setColumnWidth(3, 130)
        self.lines_table.setColumnWidth(4, 160); self.lines_table.setColumnWidth(5, 110)
        self.lines_table.setColumnWidth(6, 30) 
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        
        main_layout.addWidget(self.lines_table)

        lines_button_layout = QHBoxLayout()
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.add_line_button = QPushButton(QIcon(icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"), "Remove Selected Line")
        lines_button_layout.addWidget(self.add_line_button)
        lines_button_layout.addWidget(self.remove_line_button)
        lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        totals_layout = QHBoxLayout()
        totals_layout.addStretch()
        self.debits_label = QLabel("Debits: 0.00")
        self.credits_label = QLabel("Credits: 0.00")
        self.balance_label = QLabel("Balance: OK")
        self.balance_label.setStyleSheet("font-weight: bold;")
        totals_layout.addWidget(self.debits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.credits_label); totals_layout.addWidget(QLabel("  |  "));
        totals_layout.addWidget(self.balance_label)
        main_layout.addLayout(totals_layout)

        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_post_button = self.button_box.addButton("Save & Post", QDialogButtonBox.ButtonRole.ActionRole)
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_line)
        self.remove_line_button.clicked.connect(self._remove_selected_line)
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_post_button.clicked.connect(self.on_save_and_post)
        
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: # In view_only_mode
            close_button.clicked.connect(self.reject)
        if cancel_button: # In edit/new mode
            cancel_button.clicked.connect(self.reject)


    async def _load_initial_combo_data(self):
        # ... (same as previous version)
        try:
            if self.app_core.chart_of_accounts_manager:
                 self._accounts_cache = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(active_only=True)
            if self.app_core.tax_code_service:
                 self._tax_codes_cache = await self.app_core.tax_code_service.get_all()
            QMetaObject.invokeMethod(self, "_update_combos_in_all_lines_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading initial combo data for JE Dialog: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Data Load Error"), Q_ARG(str, f"Could not load all data for dropdowns: {e}"))

    @Slot()
    def _update_combos_in_all_lines_slot(self):
        # ... (same as previous version)
        for r in range(self.lines_table.rowCount()):
            line_data_to_use = None
            if self.existing_journal_entry_data_dict and r < len(self.existing_journal_entry_data_dict.get("lines",[])):
                line_data_to_use = self.existing_journal_entry_data_dict["lines"][r]
            self._populate_combos_for_row(r, line_data_to_use)

    async def _load_existing_journal_entry(self):
        # ... (same as previous version)
        if not self.journal_entry_id or not self.app_core.journal_entry_manager: return
        
        self.loaded_journal_entry_orm = await self.app_core.journal_entry_manager.get_journal_entry_for_dialog(self.journal_entry_id)
        if self.loaded_journal_entry_orm:
            json_data_str = self._serialize_je_for_ui(self.loaded_journal_entry_orm)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, json_data_str))
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Journal Entry ID {self.journal_entry_id} not found."))
            self.reject()


    def _serialize_je_for_ui(self, je: JournalEntry) -> str: # Converts ORM to JSON string for cross-thread
        # ... (same as previous version)
        data = {
            "entry_date": je.entry_date, "journal_type": je.journal_type,
            "description": je.description, "reference": je.reference,
            "is_posted": je.is_posted, "source_type": je.source_type, "source_id": je.source_id,
            "lines": [
                { "account_id": line.account_id, "description": line.description,
                  "debit_amount": line.debit_amount, "credit_amount": line.credit_amount,
                  "currency_code": line.currency_code, "exchange_rate": line.exchange_rate,
                  "tax_code": line.tax_code, "tax_amount": line.tax_amount,
                  "dimension1_id": line.dimension1_id, "dimension2_id": line.dimension2_id,
                } for line in je.lines ]}
        return json.dumps(data, default=json_converter)

    @Slot(str)
    def _populate_dialog_from_data_slot(self, json_data_str: str): # Parses JSON and populates UI
        # ... (same as previous version, including read-only logic)
        try:
            data = json.loads(json_data_str, object_hook=json_date_hook)
            self.existing_journal_entry_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing journal entry data."); return

        if data.get("entry_date"): self.entry_date_edit.setDate(QDate(data["entry_date"]))
        type_idx = self.journal_type_combo.findText(data.get("journal_type", JournalTypeEnum.GENERAL.value))
        if type_idx != -1: self.journal_type_combo.setCurrentIndex(type_idx)
        self.description_edit.setText(data.get("description", ""))
        self.reference_edit.setText(data.get("reference", ""))

        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_line(); self._add_new_line()
        self._calculate_totals()

        is_read_only = self.view_only_mode or data.get("is_posted", False)
        if is_read_only:
            self.save_draft_button.setVisible(False) 
            self.save_post_button.setVisible(False)
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            
            # Iterate through form layout items to set read-only
            for i in range(self.header_form.rowCount()):
                label_item = self.header_form.itemAt(i, QFormLayout.ItemRole.LabelRole)
                field_item = self.header_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(True)
                    elif isinstance(widget, QComboBox): widget.setEnabled(False)
            
            self.add_line_button.setEnabled(False); self.remove_line_button.setEnabled(False)
            for r in range(self.lines_table.rowCount()): 
                del_btn_widget = self.lines_table.cellWidget(r, 6)
                if del_btn_widget : del_btn_widget.setVisible(False)


    def _populate_combos_for_row(self, row: int, line_data_for_this_row: Optional[Dict[str, Any]] = None):
        # ... (same as previous version, but ensure cast is imported)
        acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
        if not acc_combo: acc_combo = QComboBox(); self.lines_table.setCellWidget(row, 0, acc_combo)
        acc_combo.clear()
        acc_combo.setEditable(True); acc_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        current_acc_id = line_data_for_this_row.get("account_id") if line_data_for_this_row else None
        selected_acc_idx = -1
        for i, acc_orm in enumerate(self._accounts_cache):
            acc_combo.addItem(f"{acc_orm.code} - {acc_orm.name}", acc_orm.id)
            if acc_orm.id == current_acc_id: selected_acc_idx = i
        
        if selected_acc_idx != -1: acc_combo.setCurrentIndex(selected_acc_idx)
        elif current_acc_id and self.loaded_journal_entry_orm: 
            orig_line_orm = next((l for l in self.loaded_journal_entry_orm.lines if l.account_id == current_acc_id), None)
            if orig_line_orm and orig_line_orm.account:
                acc_combo.addItem(f"{orig_line_orm.account.code} - {orig_line_orm.account.name} (Loaded)", current_acc_id) # Indicate it's from loaded data
                acc_combo.setCurrentIndex(acc_combo.count() -1)
            else: 
                acc_combo.addItem(f"ID: {current_acc_id} (Unknown/Not Found)", current_acc_id)
                acc_combo.setCurrentIndex(acc_combo.count() -1)
        elif current_acc_id : # If no ORM loaded but ID exists (e.g. error case)
             acc_combo.addItem(f"ID: {current_acc_id} (Not in cache)", current_acc_id)
             acc_combo.setCurrentIndex(acc_combo.count() -1)


        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
        if not tax_combo: tax_combo = QComboBox(); self.lines_table.setCellWidget(row, 4, tax_combo)
        tax_combo.clear()
        tax_combo.addItem("None", "") 
        current_tax_code_str = line_data_for_this_row.get("tax_code") if line_data_for_this_row else None
        selected_tax_idx = 0 
        for i, tc_orm in enumerate(self._tax_codes_cache):
            tax_combo.addItem(f"{tc_orm.code} ({tc_orm.rate}%)", tc_orm.code)
            if tc_orm.code == current_tax_code_str: selected_tax_idx = i + 1
        
        tax_combo.setCurrentIndex(selected_tax_idx)
        if selected_tax_idx == 0 and current_tax_code_str : # Loaded tax code not in cache
             tax_combo.addItem(f"{current_tax_code_str} (Not in cache)", current_tax_code_str)
             tax_combo.setCurrentIndex(tax_combo.count()-1)


    def _add_new_line(self, line_data: Optional[Dict[str, Any]] = None):
        # ... (same as previous, ensure icon path fallback)
        row_position = self.lines_table.rowCount()
        self.lines_table.insertRow(row_position)

        acc_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 0, acc_combo)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row_position, 1, desc_item)

        debit_spin = QDoubleSpinBox(); debit_spin.setRange(0, 999999999999.99); debit_spin.setDecimals(2); debit_spin.setGroupSeparatorShown(True); debit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        credit_spin = QDoubleSpinBox(); credit_spin.setRange(0, 999999999999.99); credit_spin.setDecimals(2); credit_spin.setGroupSeparatorShown(True); credit_spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        if line_data:
            debit_spin.setValue(float(Decimal(str(line_data.get("debit_amount", "0")))))
            credit_spin.setValue(float(Decimal(str(line_data.get("credit_amount", "0")))))
        self.lines_table.setCellWidget(row_position, 2, debit_spin)
        self.lines_table.setCellWidget(row_position, 3, credit_spin)
        
        debit_spin.valueChanged.connect(lambda val, r=row_position, cs=credit_spin: cs.setValue(0.00) if val > 0.001 else None)
        credit_spin.valueChanged.connect(lambda val, r=row_position, ds=debit_spin: ds.setValue(0.00) if val > 0.001 else None)
        debit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))
        credit_spin.valueChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position))

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row_position, 4, tax_combo)
        tax_combo.currentIndexChanged.connect(self._calculate_totals_and_tax_for_row_slot(row_position)) # Ensure it triggers recalc chain

        initial_tax_amt_str = "0.00"
        if line_data and line_data.get("tax_amount") is not None:
            initial_tax_amt_str = str(Decimal(str(line_data.get("tax_amount"))).quantize(Decimal("0.01")))
        tax_amt_item = QTableWidgetItem(initial_tax_amt_str)
        tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lines_table.setItem(row_position, 5, tax_amt_item)
        
        icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; icon_path_prefix = ":/icons/"
        except ImportError: pass
        del_button = QPushButton(QIcon(icon_path_prefix + "remove.svg"))
        del_button.setToolTip("Remove this line"); del_button.setFixedSize(24,24)
        del_button.clicked.connect(lambda _, r=row_position: self._remove_specific_line(r))
        self.lines_table.setCellWidget(row_position, 6, del_button)

        self._populate_combos_for_row(row_position, line_data) 
        self._recalculate_tax_for_line(row_position) 
        self._calculate_totals() 


    def _calculate_totals_and_tax_for_row_slot(self, row: int):
        # ... (same as previous)
        return lambda: self._chain_recalculate_tax_and_totals(row)

    def _chain_recalculate_tax_and_totals(self, row: int):
        # ... (same as previous)
        self._recalculate_tax_for_line(row)

    def _remove_selected_line(self):
        # ... (same as previous)
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_line(current_row)

    def _remove_specific_line(self, row_to_remove: int):
        # ... (same as previous)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted): return
        if self.lines_table.rowCount() > 0 : 
            self.lines_table.removeRow(row_to_remove)
            self._calculate_totals()


    @Slot() 
    def _calculate_totals_from_signal(self): 
        # ... (same as previous)
        self._calculate_totals()

    def _calculate_totals(self):
        # ... (same as previous, ensure Decimal used)
        total_debits = Decimal(0); total_credits = Decimal(0)
        for row in range(self.lines_table.rowCount()):
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            if debit_spin: total_debits += Decimal(str(debit_spin.value()))
            if credit_spin: total_credits += Decimal(str(credit_spin.value()))
        
        self.debits_label.setText(f"Debits: {total_debits:,.2f}")
        self.credits_label.setText(f"Credits: {total_credits:,.2f}")

        if abs(total_debits - total_credits) < Decimal("0.005"): 
            self.balance_label.setText("Balance: OK"); self.balance_label.setStyleSheet("font-weight: bold; color: green;")
        else:
            diff = total_debits - total_credits
            self.balance_label.setText(f"Balance: {diff:,.2f}"); self.balance_label.setStyleSheet("font-weight: bold; color: red;")

    def _recalculate_tax_for_line(self, row: int):
        # ... (same as previous, ensure Decimal used)
        try:
            debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
            credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
            tax_amt_item = self.lines_table.item(row, 5)

            if not all([debit_spin, credit_spin, tax_combo]): return 
            if not tax_amt_item: 
                tax_amt_item = QTableWidgetItem("0.00")
                tax_amt_item.setFlags(tax_amt_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                tax_amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.lines_table.setItem(row, 5, tax_amt_item)

            base_amount = Decimal(str(debit_spin.value())) if debit_spin.value() > 0 else Decimal(str(credit_spin.value()))
            tax_code_str = tax_combo.currentData() if tax_combo.currentIndex() > 0 else None # Handles "None" item
            
            calculated_tax = Decimal(0)
            if tax_code_str and base_amount != Decimal(0):
                tc_obj = next((tc for tc in self._tax_codes_cache if tc.code == tax_code_str), None)
                if tc_obj and tc_obj.tax_type == "GST" and tc_obj.rate is not None:
                    tax_rate = tc_obj.rate / Decimal(100)
                    calculated_tax = (base_amount * tax_rate).quantize(Decimal("0.01"))
            
            tax_amt_item.setText(f"{calculated_tax:,.2f}")
        except Exception as e:
            self.app_core.logger.error(f"Error recalculating tax for row {row}: {e}", exc_info=True)
            if tax_amt_item: tax_amt_item.setText("Error")
        finally:
            self._calculate_totals() 


    def _collect_data(self) -> Optional[JournalEntryData]:
        # ... (same as previous, but ensure use of self.loaded_journal_entry_orm for source_type/id)
        lines_data: List[JournalEntryLineData] = []
        total_debits = Decimal(0); total_credits = Decimal(0)

        for row in range(self.lines_table.rowCount()):
            try:
                acc_combo = cast(QComboBox, self.lines_table.cellWidget(row, 0))
                desc_item_widget = self.lines_table.item(row, 1)
                debit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 2))
                credit_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, 3))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, 4))
                tax_amt_item_widget = self.lines_table.item(row, 5)

                account_id = acc_combo.currentData() if acc_combo else None
                line_debit = Decimal(str(debit_spin.value())) if debit_spin else Decimal(0)
                line_credit = Decimal(str(credit_spin.value())) if credit_spin else Decimal(0)

                if account_id is None and (line_debit != Decimal(0) or line_credit != Decimal(0)):
                    QMessageBox.warning(self, "Validation Error", f"Account not selected for line {row + 1} which has amounts.")
                    return None
                if account_id is None: continue 

                line_dto = JournalEntryLineData(
                    account_id=int(account_id),
                    description=desc_item_widget.text() if desc_item_widget else "",
                    debit_amount=line_debit, credit_amount=line_credit,
                    tax_code=tax_combo.currentData() if tax_combo and tax_combo.currentData() else None, 
                    tax_amount=Decimal(tax_amt_item_widget.text().replace(',', '')) if tax_amt_item_widget and tax_amt_item_widget.text() else Decimal(0),
                    currency_code="SGD", exchange_rate=Decimal(1), # Defaults for now
                    dimension1_id=None, dimension2_id=None 
                )
                lines_data.append(line_dto)
                total_debits += line_debit; total_credits += line_credit
            except Exception as e:
                QMessageBox.warning(self, "Input Error", f"Error processing line {row + 1}: {e}"); return None
        
        if not lines_data:
             QMessageBox.warning(self, "Input Error", "Journal entry must have at least one valid line."); return None
        if abs(total_debits - total_credits) > Decimal("0.01"):
            QMessageBox.warning(self, "Balance Error", f"Journal entry is not balanced. Debits: {total_debits:,.2f}, Credits: {total_credits:,.2f}."); return None

        try:
            # Get source_type/id from loaded ORM if editing, otherwise None for new.
            # self.loaded_journal_entry_orm is set in _load_existing_journal_entry
            source_type = self.loaded_journal_entry_orm.source_type if self.journal_entry_id and self.loaded_journal_entry_orm else None
            source_id = self.loaded_journal_entry_orm.source_id if self.journal_entry_id and self.loaded_journal_entry_orm else None
            
            entry_data = JournalEntryData(
                journal_type=self.journal_type_combo.currentText(),
                entry_date=self.entry_date_edit.date().toPython(),
                description=self.description_edit.text().strip() or None,
                reference=self.reference_edit.text().strip() or None,
                user_id=self.current_user_id, lines=lines_data,
                source_type=source_type, source_id=source_id
                # is_recurring, recurring_pattern_id are not set by this generic dialog directly.
            )
            return entry_data
        except ValueError as e: 
            QMessageBox.warning(self, "Validation Error", str(e)); return None

    @Slot()
    def on_save_draft(self):
        # ... (same as previous version)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save. Entry is posted or in view-only mode.")
            return
        entry_data = self._collect_data()
        if entry_data: schedule_task_from_qt(self._perform_save(entry_data, post_after_save=False))

    @Slot()
    def on_save_and_post(self):
        # ... (same as previous version)
        if self.view_only_mode or (self.loaded_journal_entry_orm and self.loaded_journal_entry_orm.is_posted):
            QMessageBox.information(self, "Info", "Cannot save and post. Entry is already posted or in view-only mode.")
            return
        entry_data = self._collect_data()
        if entry_data: schedule_task_from_qt(self._perform_save(entry_data, post_after_save=True))

    async def _perform_save(self, entry_data: JournalEntryData, post_after_save: bool):
        # ... (same as previous version, ensuring Result type hint)
        manager = self.app_core.journal_entry_manager
        if not manager:
             QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Journal Entry Manager not available."))
             return

        result: Result[JournalEntry] # Explicit type hint
        if self.journal_entry_id and self.loaded_journal_entry_orm: 
            result = await manager.update_journal_entry(self.journal_entry_id, entry_data)
        else: 
            result = await manager.create_journal_entry(entry_data)

        if result.is_success:
            saved_je = result.value
            assert saved_je is not None
            if post_after_save:
                post_result: Result[JournalEntry] = await manager.post_journal_entry(saved_je.id, self.current_user_id)
                if post_result.is_success:
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved and posted successfully."))
                    self.journal_entry_saved.emit(saved_je.id)
                    QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
                else:
                    error_msg = f"Journal entry saved as draft (ID: {saved_je.id}), but failed to post:\n{', '.join(post_result.errors)}"
                    QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(QWidget, self), Q_ARG(str, "Posting Error"), Q_ARG(str, error_msg))
                    self.journal_entry_saved.emit(saved_je.id) 
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, "Journal entry saved as draft successfully."))
                self.journal_entry_saved.emit(saved_je.id)
                QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save journal entry:\n{', '.join(result.errors)}"))


    def open(self) -> int: 
        # ... (same as previous version, with more thorough reset)
        if not self.journal_entry_id and not self.view_only_mode : 
            self.setWindowTitle("New Journal Entry") # Reset title
            self.entry_date_edit.setDate(QDate.currentDate()); self.entry_date_edit.setReadOnly(False)
            self.journal_type_combo.setCurrentText(JournalTypeEnum.GENERAL.value); self.journal_type_combo.setEnabled(True)
            self.description_edit.clear(); self.description_edit.setReadOnly(False)
            self.reference_edit.clear(); self.reference_edit.setReadOnly(False)
            self.lines_table.setRowCount(0)
            self._add_new_line()
            self._add_new_line()
            self._calculate_totals()
            self.save_draft_button.setVisible(True); self.save_draft_button.setEnabled(True)
            self.save_post_button.setVisible(True); self.save_post_button.setEnabled(True)
            self.save_post_button.setText("Save & Post")
            self.lines_table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
            self.add_line_button.setEnabled(True); self.remove_line_button.setEnabled(True)
            
            # Ensure form layout fields are re-enabled
            for i in range(self.header_form.rowCount()):
                field_item = self.header_form.itemAt(i, QFormLayout.ItemRole.FieldRole)
                if field_item:
                    widget = field_item.widget()
                    if isinstance(widget, (QLineEdit, QDateEdit)): widget.setReadOnly(False)
                    elif isinstance(widget, QComboBox): widget.setEnabled(True)
            
            # Ensure line delete buttons are visible if any rows exist
            for r in range(self.lines_table.rowCount()):
                del_btn_widget = self.lines_table.cellWidget(r, 6)
                if del_btn_widget: del_btn_widget.setVisible(True)

        return super().open()

```

# app/ui/accounting/account_dialog.py
```py
# File: app/ui/accounting/account_dialog.py
# (Content as previously updated and verified)
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QFormLayout, QMessageBox, QCheckBox, QDateEdit, QComboBox, 
                               QSpinBox, QHBoxLayout) 
from PySide6.QtCore import Slot, QDate, QTimer 
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData
from app.models.accounting.account import Account 
from app.core.application_core import ApplicationCore
from decimal import Decimal, InvalidOperation 
import asyncio 
from typing import Optional, cast 

class AccountDialog(QDialog):
    def __init__(self, app_core: ApplicationCore, current_user_id: int, account_id: Optional[int] = None, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.account_id = account_id
        self.current_user_id = current_user_id 
        self.account: Optional[Account] = None 

        self.setWindowTitle("Add Account" if not account_id else "Edit Account")
        self.setMinimumWidth(450) 

        self.layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.code_edit = QLineEdit()
        self.name_edit = QLineEdit()
        
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(['Asset', 'Liability', 'Equity', 'Revenue', 'Expense'])
        
        self.sub_type_edit = QLineEdit() 
        self.description_edit = QLineEdit() 
        self.parent_id_spin = QSpinBox() 
        self.parent_id_spin.setRange(0, 999999) 
        self.parent_id_spin.setSpecialValueText("None (Root Account)")


        self.opening_balance_edit = QLineEdit("0.00") 
        self.opening_balance_date_edit = QDateEdit(QDate.currentDate())
        self.opening_balance_date_edit.setCalendarPopup(True)
        self.opening_balance_date_edit.setEnabled(False) 

        self.report_group_edit = QLineEdit()
        self.gst_applicable_check = QCheckBox()
        self.tax_treatment_edit = QLineEdit() 
        self.is_active_check = QCheckBox("Is Active")
        self.is_active_check.setChecked(True)
        self.is_control_account_check = QCheckBox("Is Control Account")
        self.is_bank_account_check = QCheckBox("Is Bank Account")
        
        self.form_layout.addRow("Code:", self.code_edit)
        self.form_layout.addRow("Name:", self.name_edit)
        self.form_layout.addRow("Account Type:", self.account_type_combo)
        self.form_layout.addRow("Sub Type:", self.sub_type_edit)
        self.form_layout.addRow("Parent Account ID:", self.parent_id_spin) 
        self.form_layout.addRow("Description:", self.description_edit)
        self.form_layout.addRow("Opening Balance:", self.opening_balance_edit)
        self.form_layout.addRow("OB Date:", self.opening_balance_date_edit)
        self.form_layout.addRow("Report Group:", self.report_group_edit)
        self.form_layout.addRow("GST Applicable:", self.gst_applicable_check)
        self.form_layout.addRow("Tax Treatment:", self.tax_treatment_edit)
        self.form_layout.addRow(self.is_active_check)
        self.form_layout.addRow(self.is_control_account_check)
        self.form_layout.addRow(self.is_bank_account_check)
        
        self.layout.addLayout(self.form_layout)

        self.save_button = QPushButton("Save")
        self.cancel_button = QPushButton("Cancel")
        
        self.button_layout_bottom = QHBoxLayout() 
        self.button_layout_bottom.addStretch()
        self.button_layout_bottom.addWidget(self.save_button)
        self.button_layout_bottom.addWidget(self.cancel_button)
        self.layout.addLayout(self.button_layout_bottom)

        self.save_button.clicked.connect(self.on_save)
        self.cancel_button.clicked.connect(self.reject)
        self.opening_balance_edit.textChanged.connect(self._on_ob_changed)

        if self.account_id:
            QTimer.singleShot(0, lambda: asyncio.ensure_future(self.load_account_data()))

    def _on_ob_changed(self, text: str):
        try:
            ob_val = Decimal(text)
            self.opening_balance_date_edit.setEnabled(ob_val != Decimal(0))
        except InvalidOperation: 
            self.opening_balance_date_edit.setEnabled(False)


    async def load_account_data(self):
        manager = self.app_core.accounting_service 
        if not manager or not hasattr(manager, 'account_service'): 
            QMessageBox.critical(self, "Error", "Accounting service or account_service attribute not available.")
            self.reject(); return

        self.account = await manager.account_service.get_by_id(self.account_id) # type: ignore
        if self.account:
            self.code_edit.setText(self.account.code)
            self.name_edit.setText(self.account.name)
            self.account_type_combo.setCurrentText(self.account.account_type)
            self.sub_type_edit.setText(self.account.sub_type or "")
            self.description_edit.setText(self.account.description or "")
            self.parent_id_spin.setValue(self.account.parent_id or 0)
            
            self.opening_balance_edit.setText(f"{self.account.opening_balance:.2f}")
            if self.account.opening_balance_date:
                self.opening_balance_date_edit.setDate(QDate.fromString(str(self.account.opening_balance_date), "yyyy-MM-dd"))
                self.opening_balance_date_edit.setEnabled(True)
            else:
                self.opening_balance_date_edit.setEnabled(False)
                self.opening_balance_date_edit.setDate(QDate.currentDate())


            self.report_group_edit.setText(self.account.report_group or "")
            self.gst_applicable_check.setChecked(self.account.gst_applicable)
            self.tax_treatment_edit.setText(self.account.tax_treatment or "")
            self.is_active_check.setChecked(self.account.is_active)
            self.is_control_account_check.setChecked(self.account.is_control_account)
            self.is_bank_account_check.setChecked(self.account.is_bank_account)
        else:
            QMessageBox.warning(self, "Error", f"Account ID {self.account_id} not found.")
            self.reject()

    @Slot()
    def on_save(self):
        try:
            ob_decimal = Decimal(self.opening_balance_edit.text())
        except InvalidOperation:
            QMessageBox.warning(self, "Input Error", "Invalid opening balance format. Please enter a valid number.")
            return

        parent_id_val = self.parent_id_spin.value()
        parent_id = parent_id_val if parent_id_val > 0 else None

        common_data = {
            "code": self.code_edit.text(),
            "name": self.name_edit.text(),
            "account_type": self.account_type_combo.currentText(),
            "sub_type": self.sub_type_edit.text() or None,
            "description": self.description_edit.text() or None,
            "parent_id": parent_id,
            "opening_balance": ob_decimal,
            "opening_balance_date": self.opening_balance_date_edit.date().toPython() if self.opening_balance_date_edit.isEnabled() else None,
            "report_group": self.report_group_edit.text() or None,
            "gst_applicable": self.gst_applicable_check.isChecked(),
            "tax_treatment": self.tax_treatment_edit.text() or None,
            "is_active": self.is_active_check.isChecked(),
            "is_control_account": self.is_control_account_check.isChecked(),
            "is_bank_account": self.is_bank_account_check.isChecked(),
            "user_id": self.current_user_id
        }

        try:
            if self.account_id:
                update_dto = AccountUpdateData(id=self.account_id, **common_data)
                asyncio.ensure_future(self._perform_update(update_dto))
            else:
                create_dto = AccountCreateData(**common_data)
                asyncio.ensure_future(self._perform_create(create_dto))
        except Exception as pydantic_error: 
             QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{pydantic_error}")


    async def _perform_create(self, data: AccountCreateData):
        manager = self.app_core.accounting_service 
        if not (manager and hasattr(manager, 'create_account')): 
            QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) not available.")
            return
        
        result = await manager.create_account(data) # type: ignore
        if result.is_success:
            QMessageBox.information(self, "Success", "Account created successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to create account:\n{', '.join(result.errors)}")

    async def _perform_update(self, data: AccountUpdateData):
        manager = self.app_core.accounting_service 
        if not (manager and hasattr(manager, 'update_account')):
            QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) not available.")
            return

        result = await manager.update_account(data) # type: ignore
        if result.is_success:
            QMessageBox.information(self, "Success", "Account updated successfully.")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", f"Failed to update account:\n{', '.join(result.errors)}")

```

# app/utils/json_helpers.py
```py
# File: app/utils/json_helpers.py
import json
from decimal import Decimal
from datetime import date, datetime

def json_converter(obj):
    """Custom JSON converter to handle Decimal and date/datetime objects."""
    if isinstance(obj, Decimal):
        return str(obj)  # Serialize Decimal as string
    if isinstance(obj, (datetime, date)): # Handle both datetime and date
        return obj.isoformat()  # Serialize date/datetime as ISO string
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

def json_date_hook(dct):
    """
    Custom object_hook for json.loads to convert ISO date/datetime strings back to objects.
    More specific field name checks might be needed for robustness.
    """
    for k, v in dct.items():
        if isinstance(v, str):
            # Attempt to parse common date/datetime field names
            if k.endswith('_at') or k.endswith('_date') or k in [
                'date', 'start_date', 'end_date', 'closed_date', 'submission_date', 
                'issue_date', 'payment_date', 'last_reconciled_date', 
                'customer_since', 'vendor_since', 'opening_balance_date', 
                'movement_date', 'transaction_date', 'value_date', 
                'invoice_date', 'due_date', 'filing_due_date', 'rate_date',
                'last_login_attempt', 'last_login' # From User model
            ]:
                try:
                    # Try datetime first, then date
                    dt_val = datetime.fromisoformat(v.replace('Z', '+00:00'))
                    # If it has no time component, and field implies date only, convert to date
                    if dt_val.time() == datetime.min.time() and not k.endswith('_at') and k != 'closed_date' and k != 'last_login_attempt' and k != 'last_login': # Heuristic
                         dct[k] = dt_val.date()
                    else:
                        dct[k] = dt_val
                except ValueError:
                    try:
                        dct[k] = python_date.fromisoformat(v)
                    except ValueError:
                        pass # Keep as string if not valid ISO date/datetime
    return dct

```

# app/utils/result.py
```py
# File: app/utils/result.py
# (Content as previously generated, verified)
from typing import TypeVar, Generic, List, Any, Optional

T = TypeVar('T')

class Result(Generic[T]):
    def __init__(self, is_success: bool, value: Optional[T] = None, errors: Optional[List[str]] = None):
        self.is_success = is_success
        self.value = value
        self.errors = errors if errors is not None else []

    @staticmethod
    def success(value: Optional[T] = None) -> 'Result[T]':
        return Result(is_success=True, value=value)

    @staticmethod
    def failure(errors: List[str]) -> 'Result[Any]': 
        return Result(is_success=False, errors=errors)

    def __repr__(self):
        if self.is_success:
            return f"<Result success={True} value='{str(self.value)[:50]}'>"
        else:
            return f"<Result success={False} errors={self.errors}>"

```

# app/utils/__init__.py
```py
# File: app/utils/__init__.py
from .converters import to_decimal
from .formatting import format_currency, format_date, format_datetime
from .json_helpers import json_converter, json_date_hook # Added
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData,
    FiscalYearCreateData, FiscalYearData, FiscalPeriodData # Added Fiscal DTOs
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "json_converter", "json_date_hook", # Added
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "FiscalYearCreateData", "FiscalYearData", "FiscalPeriodData", # Added Fiscal DTOs
    "Result", "SequenceGenerator", "is_valid_uen"
]

```

# app/utils/pydantic_models.py
```py
# app/utils/pydantic_models.py
from pydantic import BaseModel, Field, validator, root_validator, EmailStr # type: ignore
from typing import List, Optional, Union, Any, Dict 
from datetime import date, datetime
from decimal import Decimal

from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # Added InvoiceStatusEnum

class AppBaseModel(BaseModel):
    class Config:
        from_attributes = True 
        json_encoders = {
            Decimal: lambda v: float(v) if v is not None and v.is_finite() else None,
        }
        validate_assignment = True 

class UserAuditData(BaseModel):
    user_id: int

# --- Account Related DTOs (existing, condensed) ---
class AccountBaseData(AppBaseModel): # ...
    code: str = Field(..., max_length=20); name: str = Field(..., max_length=100); account_type: str 
    sub_type: Optional[str] = Field(None, max_length=30); tax_treatment: Optional[str] = Field(None, max_length=20)
    gst_applicable: bool = False; description: Optional[str] = None; parent_id: Optional[int] = None
    report_group: Optional[str] = Field(None, max_length=50); is_control_account: bool = False
    is_bank_account: bool = False; opening_balance: Decimal = Field(Decimal(0))
    opening_balance_date: Optional[date] = None; is_active: bool = True
    @validator('opening_balance', pre=True, always=True)
    def opening_balance_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)
class AccountCreateData(AccountBaseData, UserAuditData): pass
class AccountUpdateData(AccountBaseData, UserAuditData): id: int

# --- Journal Entry Related DTOs (existing, condensed) ---
class JournalEntryLineData(AppBaseModel): # ...
    account_id: int; description: Optional[str] = Field(None, max_length=200); debit_amount: Decimal = Field(Decimal(0))
    credit_amount: Decimal = Field(Decimal(0)); currency_code: str = Field("SGD", max_length=3) 
    exchange_rate: Decimal = Field(Decimal(1)); tax_code: Optional[str] = Field(None, max_length=20) 
    tax_amount: Decimal = Field(Decimal(0)); dimension1_id: Optional[int] = None; dimension2_id: Optional[int] = None 
    @validator('debit_amount', 'credit_amount', 'exchange_rate', 'tax_amount', pre=True, always=True)
    def je_line_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0) 
    @root_validator(skip_on_failure=True)
    def check_je_line_debit_credit_exclusive(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        debit = values.get('debit_amount', Decimal(0)); credit = values.get('credit_amount', Decimal(0))
        if debit > Decimal(0) and credit > Decimal(0): raise ValueError("Debit and Credit amounts cannot both be positive for a single line.")
        return values
class JournalEntryData(AppBaseModel, UserAuditData): # ...
    journal_type: str; entry_date: date; description: Optional[str] = Field(None, max_length=500)
    reference: Optional[str] = Field(None, max_length=100); is_recurring: bool = False 
    recurring_pattern_id: Optional[int] = None; source_type: Optional[str] = Field(None, max_length=50)
    source_id: Optional[int] = None; lines: List[JournalEntryLineData]
    @validator('lines')
    def check_je_lines_not_empty(cls, v: List[JournalEntryLineData]) -> List[JournalEntryLineData]: 
        if not v: raise ValueError("Journal entry must have at least one line.")
        return v
    @root_validator(skip_on_failure=True)
    def check_je_balanced_entry(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        lines = values.get('lines', []); total_debits = sum(l.debit_amount for l in lines); total_credits = sum(l.credit_amount for l in lines)
        if abs(total_debits - total_credits) > Decimal("0.01"): raise ValueError(f"Journal entry must be balanced (Debits: {total_debits}, Credits: {total_credits}).")
        return values

# --- GST Return Related DTOs (existing, condensed) ---
class GSTReturnData(AppBaseModel, UserAuditData): # ... 
    id: Optional[int] = None; return_period: str = Field(..., max_length=20); start_date: date; end_date: date; filing_due_date: Optional[date] = None 
    standard_rated_supplies: Decimal = Field(Decimal(0)); zero_rated_supplies: Decimal = Field(Decimal(0)); exempt_supplies: Decimal = Field(Decimal(0)); total_supplies: Decimal = Field(Decimal(0)) 
    taxable_purchases: Decimal = Field(Decimal(0)); output_tax: Decimal = Field(Decimal(0)); input_tax: Decimal = Field(Decimal(0)); tax_adjustments: Decimal = Field(Decimal(0)); tax_payable: Decimal = Field(Decimal(0)) 
    status: str = Field("Draft", max_length=20); submission_date: Optional[date] = None; submission_reference: Optional[str] = Field(None, max_length=50); journal_entry_id: Optional[int] = None; notes: Optional[str] = None
    @validator('standard_rated_supplies', 'zero_rated_supplies', 'exempt_supplies', 'total_supplies', 'taxable_purchases', 'output_tax', 'input_tax', 'tax_adjustments', 'tax_payable', pre=True, always=True)
    def gst_amounts_to_decimal(cls, v): return Decimal(str(v)) if v is not None else Decimal(0)

# --- Tax Calculation DTOs (existing, condensed) ---
class TaxCalculationResultData(AppBaseModel): tax_amount: Decimal; tax_account_id: Optional[int] = None; taxable_amount: Decimal
class TransactionLineTaxData(AppBaseModel): amount: Decimal; tax_code: Optional[str] = None; account_id: Optional[int] = None; index: int 
class TransactionTaxData(AppBaseModel): transaction_type: str; lines: List[TransactionLineTaxData]

# --- Validation Result DTO (existing, condensed) ---
class AccountValidationResult(AppBaseModel): is_valid: bool; errors: List[str] = []
class AccountValidator: # ... (existing logic)
    def validate_common(self, account_data: AccountBaseData) -> List[str]:
        errors = []; 
        if not account_data.code: errors.append("Account code is required.")
        if not account_data.name: errors.append("Account name is required.")
        if not account_data.account_type: errors.append("Account type is required.")
        if account_data.is_bank_account and account_data.account_type != 'Asset': errors.append("Bank accounts must be of type 'Asset'.")
        if account_data.opening_balance_date and account_data.opening_balance == Decimal(0): errors.append("Opening balance date provided but opening balance is zero.")
        if account_data.opening_balance != Decimal(0) and not account_data.opening_balance_date: errors.append("Opening balance provided but opening balance date is missing.")
        return errors
    def validate_create(self, account_data: AccountCreateData) -> AccountValidationResult:
        errors = self.validate_common(account_data); return AccountValidationResult(is_valid=not errors, errors=errors)
    def validate_update(self, account_data: AccountUpdateData) -> AccountValidationResult:
        errors = self.validate_common(account_data)
        if not account_data.id: errors.append("Account ID is required for updates.")
        return AccountValidationResult(is_valid=not errors, errors=errors)

# --- Company Setting DTO (existing, condensed) ---
class CompanySettingData(AppBaseModel, UserAuditData): # ... 
    id: Optional[int] = None; company_name: str = Field(..., max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registration_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: str = Field("Singapore", max_length=50); country: str = Field("Singapore", max_length=50); contact_person: Optional[str] = Field(None, max_length=100); phone: Optional[str] = Field(None, max_length=20); email: Optional[EmailStr] = None; website: Optional[str] = Field(None, max_length=100); logo: Optional[bytes] = None; fiscal_year_start_month: int = Field(1, ge=1, le=12); fiscal_year_start_day: int = Field(1, ge=1, le=31); base_currency: str = Field("SGD", max_length=3); tax_id_label: str = Field("UEN", max_length=50); date_format: str = Field("dd/MM/yyyy", max_length=20)

# --- Fiscal Year Related DTOs (existing, condensed) ---
class FiscalYearCreateData(AppBaseModel, UserAuditData): # ...
    year_name: str = Field(..., max_length=20); start_date: date; end_date: date; auto_generate_periods: Optional[str] = None
    @root_validator(skip_on_failure=True)
    def check_fy_dates(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        start, end = values.get('start_date'), values.get('end_date');
        if start and end and start >= end: raise ValueError("End date must be after start date.")
        return values
class FiscalPeriodData(AppBaseModel): id: int; name: str; start_date: date; end_date: date; period_type: str; status: str; period_number: int; is_adjustment: bool
class FiscalYearData(AppBaseModel): id: int; year_name: str; start_date: date; end_date: date; is_closed: bool; closed_date: Optional[datetime] = None; periods: List[FiscalPeriodData] = []

# --- Customer Related DTOs (existing, condensed) ---
class CustomerBaseData(AppBaseModel): # ... 
    customer_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); credit_terms: int = Field(30, ge=0); credit_limit: Optional[Decimal] = Field(None, ge=Decimal(0)); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; customer_since: Optional[date] = None; notes: Optional[str] = None; receivables_account_id: Optional[int] = None
    @validator('credit_limit', pre=True, always=True)
    def customer_credit_limit_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_customer(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if customer is GST registered.")
        return values
class CustomerCreateData(CustomerBaseData, UserAuditData): pass
class CustomerUpdateData(CustomerBaseData, UserAuditData): id: int
class CustomerData(CustomerBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class CustomerSummaryData(AppBaseModel): id: int; customer_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Vendor Related DTOs (existing, condensed) ---
class VendorBaseData(AppBaseModel): # ... 
    vendor_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); legal_name: Optional[str] = Field(None, max_length=200); uen_no: Optional[str] = Field(None, max_length=20); gst_registered: bool = False; gst_no: Optional[str] = Field(None, max_length=20); withholding_tax_applicable: bool = False; withholding_tax_rate: Optional[Decimal] = Field(None, ge=Decimal(0), le=Decimal(100)); contact_person: Optional[str] = Field(None, max_length=100); email: Optional[EmailStr] = None; phone: Optional[str] = Field(None, max_length=20); address_line1: Optional[str] = Field(None, max_length=100); address_line2: Optional[str] = Field(None, max_length=100); postal_code: Optional[str] = Field(None, max_length=20); city: Optional[str] = Field(None, max_length=50); country: str = Field("Singapore", max_length=50); payment_terms: int = Field(30, ge=0); currency_code: str = Field("SGD", min_length=3, max_length=3); is_active: bool = True; vendor_since: Optional[date] = None; notes: Optional[str] = None; bank_account_name: Optional[str] = Field(None, max_length=100); bank_account_number: Optional[str] = Field(None, max_length=50); bank_name: Optional[str] = Field(None, max_length=100); bank_branch: Optional[str] = Field(None, max_length=100); bank_swift_code: Optional[str] = Field(None, max_length=20); payables_account_id: Optional[int] = None
    @validator('withholding_tax_rate', pre=True, always=True)
    def vendor_wht_rate_to_decimal(cls, v): return Decimal(str(v)) if v is not None else None 
    @root_validator(skip_on_failure=True)
    def check_gst_no_if_registered_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get('gst_registered') and not values.get('gst_no'): raise ValueError("GST No. is required if vendor is GST registered.")
        return values
    @root_validator(skip_on_failure=True)
    def check_wht_rate_if_applicable_vendor(cls, values: Dict[str, Any]) -> Dict[str, Any]: 
        if values.get('withholding_tax_applicable') and values.get('withholding_tax_rate') is None: raise ValueError("Withholding Tax Rate is required if Withholding Tax is applicable.")
        return values
class VendorCreateData(VendorBaseData, UserAuditData): pass
class VendorUpdateData(VendorBaseData, UserAuditData): id: int
class VendorData(VendorBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class VendorSummaryData(AppBaseModel): id: int; vendor_code: str; name: str; email: Optional[EmailStr] = None; phone: Optional[str] = None; is_active: bool

# --- Product/Service Related DTOs (existing, condensed) ---
class ProductBaseData(AppBaseModel): # ...
    product_code: str = Field(..., min_length=1, max_length=20); name: str = Field(..., min_length=1, max_length=100); description: Optional[str] = None; product_type: ProductTypeEnum; category: Optional[str] = Field(None, max_length=50); unit_of_measure: Optional[str] = Field(None, max_length=20); barcode: Optional[str] = Field(None, max_length=50); sales_price: Optional[Decimal] = Field(None, ge=Decimal(0)); purchase_price: Optional[Decimal] = Field(None, ge=Decimal(0)); sales_account_id: Optional[int] = None; purchase_account_id: Optional[int] = None; inventory_account_id: Optional[int] = None; tax_code: Optional[str] = Field(None, max_length=20); is_active: bool = True; min_stock_level: Optional[Decimal] = Field(None, ge=Decimal(0)); reorder_point: Optional[Decimal] = Field(None, ge=Decimal(0))
    @validator('sales_price', 'purchase_price', 'min_stock_level', 'reorder_point', pre=True, always=True)
    def product_decimal_fields(cls, v): return Decimal(str(v)) if v is not None else None
    @root_validator(skip_on_failure=True)
    def check_inventory_fields_product(cls, values: Dict[str, Any]) -> Dict[str, Any]: # Renamed validator
        product_type = values.get('product_type')
        if product_type == ProductTypeEnum.INVENTORY:
            if values.get('inventory_account_id') is None: raise ValueError("Inventory Account ID is required for 'Inventory' type products.")
        else: 
            if values.get('inventory_account_id') is not None: raise ValueError("Inventory Account ID should only be set for 'Inventory' type products.")
            if values.get('min_stock_level') is not None or values.get('reorder_point') is not None: raise ValueError("Stock levels are only applicable for 'Inventory' type products.")
        return values
class ProductCreateData(ProductBaseData, UserAuditData): pass
class ProductUpdateData(ProductBaseData, UserAuditData): id: int
class ProductData(ProductBaseData): id: int; created_at: datetime; updated_at: datetime; created_by_user_id: int; updated_by_user_id: int
class ProductSummaryData(AppBaseModel): id: int; product_code: str; name: str; product_type: ProductTypeEnum; sales_price: Optional[Decimal] = None; purchase_price: Optional[Decimal] = None; is_active: bool

# --- NEW: Sales Invoice Related DTOs ---
class SalesInvoiceLineBaseData(AppBaseModel):
    product_id: Optional[int] = None # Optional if it's a service line w/o specific product item
    description: str = Field(..., min_length=1, max_length=200)
    quantity: Decimal = Field(..., gt=Decimal(0))
    unit_price: Decimal = Field(..., ge=Decimal(0))
    discount_percent: Decimal = Field(Decimal(0), ge=Decimal(0), le=Decimal(100))
    # discount_amount will be calculated
    tax_code: Optional[str] = Field(None, max_length=20) # TaxCode.code
    # line_subtotal, tax_amount, line_total will be calculated by manager/logic before saving to ORM

    @validator('quantity', 'unit_price', 'discount_percent', pre=True, always=True)
    def sales_inv_line_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(0)

class SalesInvoiceBaseData(AppBaseModel):
    customer_id: int
    invoice_date: date
    due_date: date
    currency_code: str = Field("SGD", min_length=3, max_length=3)
    exchange_rate: Decimal = Field(Decimal(1), ge=Decimal(0))
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    # subtotal, tax_amount, total_amount will be calculated by manager/logic before saving to ORM
    # status will be set by manager (e.g., Draft)
    
    @validator('exchange_rate', pre=True, always=True)
    def sales_inv_hdr_decimals(cls, v):
        return Decimal(str(v)) if v is not None else Decimal(1)

    @root_validator(skip_on_failure=True)
    def check_due_date(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        invoice_date, due_date = values.get('invoice_date'), values.get('due_date')
        if invoice_date and due_date and due_date < invoice_date:
            raise ValueError("Due date cannot be before invoice date.")
        return values

class SalesInvoiceCreateData(SalesInvoiceBaseData, UserAuditData):
    lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1) # Must have at least one line

class SalesInvoiceUpdateData(SalesInvoiceBaseData, UserAuditData):
    id: int
    lines: List[SalesInvoiceLineBaseData] = Field(..., min_length=1)

class SalesInvoiceData(SalesInvoiceBaseData): # For full representation
    id: int
    invoice_no: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatusEnum # Use Enum
    journal_entry_id: Optional[int] = None
    lines: List[SalesInvoiceLineBaseData] # Or a more detailed SalesInvoiceLineData if needed
    created_at: datetime
    updated_at: datetime
    created_by_user_id: int
    updated_by_user_id: int

class SalesInvoiceSummaryData(AppBaseModel): # For listing invoices
    id: int
    invoice_no: str
    invoice_date: date
    due_date: date
    customer_name: str # To be joined/fetched
    total_amount: Decimal
    amount_paid: Decimal
    status: InvoiceStatusEnum # Use Enum


```

# app/utils/validation.py
```py
# File: app/utils/validation.py
# (Content as previously generated, verified)
def is_valid_uen(uen: str) -> bool:
    if not uen: return True 
    return len(uen) >= 9 and len(uen) <= 10 

```

# app/utils/sequence_generator.py
```py
# File: app/utils/sequence_generator.py
import asyncio
from typing import Optional, TYPE_CHECKING
from app.models.core.sequence import Sequence # Still needed if we fallback or for other methods
from app.services.core_services import SequenceService 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For db_manager access if needed

class SequenceGenerator:
    def __init__(self, sequence_service: SequenceService, app_core_ref: Optional["ApplicationCore"] = None):
        self.sequence_service = sequence_service
        # Store app_core to access db_manager for calling the DB function
        self.app_core = app_core_ref 
        if self.app_core is None and hasattr(sequence_service, 'app_core'): # Fallback if service has it
            self.app_core = sequence_service.app_core


    async def next_sequence(self, sequence_name: str, prefix_override: Optional[str] = None) -> str:
        """
        Generates the next number in a sequence.
        Primarily tries to use the PostgreSQL function core.get_next_sequence_value().
        Falls back to Python-based logic if DB function call fails or app_core is not available for DB manager.
        """
        if self.app_core and hasattr(self.app_core, 'db_manager'):
            try:
                # The DB function `core.get_next_sequence_value(p_sequence_name VARCHAR)`
                # already handles prefix, suffix, formatting and returns the final string.
                # It does NOT take prefix_override. If prefix_override is needed,
                # this DB function strategy needs re-evaluation or the DB func needs an update.
                # For now, assume prefix_override is not used with DB function or is handled by template in DB.
                
                # If prefix_override is essential, we might need to:
                # 1. Modify DB function to accept it.
                # 2. Fetch numeric value from DB, then format in Python with override. (More complex)

                # Current DB function `core.get_next_sequence_value` uses the prefix stored in the table.
                # If prefix_override is provided, the Python fallback might be necessary.
                # Let's assume for now, if prefix_override is given, we must use Python logic.
                
                if prefix_override is None: # Only use DB function if no override, as DB func uses its stored prefix
                    db_func_call = f"SELECT core.get_next_sequence_value('{sequence_name}');"
                    generated_value = await self.app_core.db_manager.execute_scalar(db_func_call) # type: ignore
                    if generated_value:
                        return str(generated_value)
                    else:
                        # Log this failure to use DB func
                        if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                            self.app_core.db_manager.logger.warning(f"DB function core.get_next_sequence_value for '{sequence_name}' returned None. Falling back to Python logic.")
                        else:
                            print(f"Warning: DB function for sequence '{sequence_name}' failed. Falling back.")
                else:
                    if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                        self.app_core.db_manager.logger.info(f"Prefix override for '{sequence_name}' provided. Using Python sequence logic.") # type: ignore
                    else:
                        print(f"Info: Prefix override for '{sequence_name}' provided. Using Python sequence logic.")


            except Exception as e:
                # Log this failure to use DB func
                if hasattr(self.app_core.db_manager, 'logger') and self.app_core.db_manager.logger:
                     self.app_core.db_manager.logger.error(f"Error calling DB sequence function for '{sequence_name}': {e}. Falling back to Python logic.", exc_info=True) # type: ignore
                else:
                    print(f"Error calling DB sequence function for '{sequence_name}': {e}. Falling back.")
        
        # Fallback to Python-based logic (less robust for concurrency)
        sequence_obj = await self.sequence_service.get_sequence_by_name(sequence_name)

        if not sequence_obj:
            # Fallback creation if not found - ensure this is atomic or a rare case
            print(f"Sequence '{sequence_name}' not found in DB, creating with defaults via Python logic.")
            default_actual_prefix = prefix_override if prefix_override is not None else sequence_name.upper()[:3]
            sequence_obj = Sequence(
                sequence_name=sequence_name, next_value=1, increment_by=1,
                min_value=1, max_value=2147483647, prefix=default_actual_prefix,
                format_template=f"{{PREFIX}}-{{VALUE:06d}}" # Ensure d for integer formatting
            )
            # This save should happen in its own transaction managed by sequence_service.
            await self.sequence_service.save_sequence(sequence_obj) 

        current_value = sequence_obj.next_value
        sequence_obj.next_value += sequence_obj.increment_by
        
        if sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            sequence_obj.next_value = sequence_obj.min_value
        elif not sequence_obj.cycle and sequence_obj.next_value > sequence_obj.max_value:
            # This is a critical error for non-cycling sequences
            raise ValueError(f"Sequence '{sequence_name}' has reached its maximum value ({sequence_obj.max_value}) and cannot cycle.")

        await self.sequence_service.save_sequence(sequence_obj) 

        actual_prefix_for_format = prefix_override if prefix_override is not None else (sequence_obj.prefix or '')
        
        # Refined formatting logic
        template = sequence_obj.format_template
        
        # Handle common padding formats like {VALUE:06} or {VALUE:06d}
        import re
        match = re.search(r"\{VALUE:0?(\d+)[d]?\}", template)
        value_str: str
        if match:
            padding = int(match.group(1))
            value_str = str(current_value).zfill(padding)
            template = template.replace(match.group(0), value_str) # Replace the whole placeholder
        else: # Fallback for simple {VALUE}
            value_str = str(current_value)
            template = template.replace('{VALUE}', value_str)

        template = template.replace('{PREFIX}', actual_prefix_for_format)
        template = template.replace('{SUFFIX}', sequence_obj.suffix or '')
            
        return template

```

# app/utils/formatting.py
```py
# File: app/utils/formatting.py
# (Content as previously generated, verified)
from decimal import Decimal
from datetime import date, datetime

def format_currency(amount: Decimal, currency_code: str = "SGD") -> str:
    return f"{currency_code} {amount:,.2f}"

def format_date(d: date, fmt_str: str = "%d %b %Y") -> str: 
    return d.strftime(fmt_str) 

def format_datetime(dt: datetime, fmt_str: str = "%d %b %Y %H:%M:%S") -> str: 
    return dt.strftime(fmt_str)

```

# app/utils/converters.py
```py
# File: app/utils/converters.py
# (Content as previously generated, verified)
from decimal import Decimal, InvalidOperation

def to_decimal(value: any, default: Decimal = Decimal(0)) -> Decimal:
    if isinstance(value, Decimal):
        return value
    if value is None: 
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError): 
        return default

```

# app/services/journal_service.py
```py
# File: app/services/journal_service.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from datetime import date, datetime, timedelta # Added timedelta
from decimal import Decimal
from sqlalchemy import select, func, and_, or_, literal_column, case, text
from sqlalchemy.orm import aliased, selectinload, joinedload # Added joinedload
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.account import Account 
from app.models.accounting.recurring_pattern import RecurringPattern 
from app.core.database_manager import DatabaseManager
from app.services import IJournalEntryRepository
from app.utils.result import Result

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class JournalService(IJournalEntryRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, journal_id: int) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj), 
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.currency),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension1),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.dimension2),
                selectinload(JournalEntry.fiscal_period), 
                selectinload(JournalEntry.created_by_user), 
                selectinload(JournalEntry.updated_by_user)  
            ).where(JournalEntry.id == journal_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines) 
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_all_summary(self, 
                              start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]:
        async with self.db_manager.session() as session:
            conditions = []
            if start_date_filter:
                conditions.append(JournalEntry.entry_date >= start_date_filter)
            if end_date_filter:
                conditions.append(JournalEntry.entry_date <= end_date_filter)
            if status_filter:
                if status_filter.lower() == "draft":
                    conditions.append(JournalEntry.is_posted == False)
                elif status_filter.lower() == "posted":
                    conditions.append(JournalEntry.is_posted == True)
            if entry_no_filter:
                conditions.append(JournalEntry.entry_no.ilike(f"%{entry_no_filter}%")) 
            if description_filter:
                conditions.append(JournalEntry.description.ilike(f"%{description_filter}%"))
            
            stmt = select(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date,
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted,
                func.sum(JournalEntryLine.debit_amount).label("total_debits") # Used for JE list total
            ).join(JournalEntryLine, JournalEntry.id == JournalEntryLine.journal_entry_id, isouter=True)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.group_by(
                JournalEntry.id, JournalEntry.entry_no, JournalEntry.entry_date, 
                JournalEntry.description, JournalEntry.journal_type, JournalEntry.is_posted
            ).order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_no.desc())
            
            result = await session.execute(stmt)
            
            summaries: List[Dict[str, Any]] = []
            for row in result.mappings().all(): 
                summaries.append({
                    "id": row.id, "entry_no": row.entry_no, "date": row.entry_date, 
                    "description": row.description, "type": row.journal_type,
                    "total_amount": row.total_debits if row.total_debits is not None else Decimal(0), 
                    "status": "Posted" if row.is_posted else "Draft"
                })
            return summaries
            
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(JournalEntry.entry_no == entry_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(selectinload(JournalEntry.lines)).where(
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]:
        async with self.db_manager.session() as session:
            stmt = select(JournalEntry).options(
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account),
                selectinload(JournalEntry.lines).selectinload(JournalEntryLine.tax_code_obj) 
            ).where(
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no)
            result = await session.execute(stmt)
            return list(result.unique().scalars().all())

    async def save(self, journal_entry: JournalEntry) -> JournalEntry:
        async with self.db_manager.session() as session:
            session.add(journal_entry)
            await session.flush() 
            await session.refresh(journal_entry)
            if journal_entry.lines is not None: 
                await session.refresh(journal_entry, attribute_names=['lines'])
            return journal_entry
            
    async def add(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def update(self, entity: JournalEntry) -> JournalEntry:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entry = await session.get(JournalEntry, id_val)
            if entry:
                if entry.is_posted:
                    self.app_core.logger.warning(f"JournalService: Deletion of posted journal entry ID {id_val} prevented.") # type: ignore
                    return False 
                await session.delete(entry) 
                return True
        return False
    
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            acc_stmt = select(Account.opening_balance, Account.opening_balance_date).where(Account.id == account_id)
            acc_res = await session.execute(acc_stmt)
            acc_data = acc_res.first()
            
            opening_balance = acc_data.opening_balance if acc_data and acc_data.opening_balance is not None else Decimal(0)
            ob_date = acc_data.opening_balance_date if acc_data and acc_data.opening_balance_date is not None else None

            je_activity_stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id,
                    JournalEntry.is_posted == True,
                    JournalEntry.entry_date <= as_of_date))
            if ob_date:
                je_activity_stmt = je_activity_stmt.where(JournalEntry.entry_date >= ob_date)
            
            result = await session.execute(je_activity_stmt)
            je_net_activity = result.scalar_one_or_none() or Decimal(0)
            return opening_balance + je_net_activity

    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal:
        async with self.db_manager.session() as session:
            stmt = (
                select(func.coalesce(func.sum(JournalEntryLine.debit_amount - JournalEntryLine.credit_amount), Decimal(0)))
                .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
                .where(
                    JournalEntryLine.account_id == account_id, JournalEntry.is_posted == True,
                    JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date))
            result = await session.execute(stmt)
            balance_change = result.scalar_one_or_none()
            return balance_change if balance_change is not None else Decimal(0)
            
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date) -> List[JournalEntryLine]:
        """ Fetches posted journal lines for a specific account and date range. """
        async with self.db_manager.session() as session:
            stmt = select(JournalEntryLine).options(
                joinedload(JournalEntryLine.journal_entry) # Eager load parent JE for date, no, desc
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)\
            .where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True,
                JournalEntry.entry_date >= start_date,
                JournalEntry.entry_date <= end_date
            ).order_by(JournalEntry.entry_date, JournalEntry.entry_no, JournalEntryLine.line_number) # Ensure consistent ordering
            
            result = await session.execute(stmt)
            return list(result.scalars().all()) # .unique() might not be needed if JELine is the primary entity

    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]:
        async with self.db_manager.session() as session:
            stmt = select(RecurringPattern).options(
                joinedload(RecurringPattern.template_journal_entry).selectinload(JournalEntry.lines)
            ).where(
                RecurringPattern.is_active == True,
                RecurringPattern.next_generation_date <= as_of_date,
                or_(RecurringPattern.end_date == None, RecurringPattern.end_date >= as_of_date)
            ).order_by(RecurringPattern.next_generation_date)
            result = await session.execute(stmt)
            return list(result.scalars().unique().all())

    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern:
        async with self.db_manager.session() as session:
            session.add(pattern)
            await session.flush()
            await session.refresh(pattern)
            return pattern

```

# app/services/core_services.py
```py
# File: app/services/core_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select, update
from app.models.core.sequence import Sequence
from app.models.core.configuration import Configuration
from app.models.core.company_setting import CompanySetting
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class SequenceService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager

    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]:
        async with self.db_manager.session() as session:
            stmt = select(Sequence).where(Sequence.sequence_name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save_sequence(self, sequence_obj: Sequence) -> Sequence:
        async with self.db_manager.session() as session:
            session.add(sequence_obj)
            await session.flush()
            await session.refresh(sequence_obj)
            return sequence_obj

class ConfigurationService:
    def __init__(self, db_manager: "DatabaseManager"):
        self.db_manager = db_manager
    
    async def get_config_by_key(self, key: str) -> Optional[Configuration]:
        async with self.db_manager.session() as session:
            stmt = select(Configuration).where(Configuration.config_key == key)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save_config(self, config_obj: Configuration) -> Configuration:
        async with self.db_manager.session() as session:
            session.add(config_obj)
            await session.flush()
            await session.refresh(config_obj)
            return config_obj

class CompanySettingsService:
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]:
        async with self.db_manager.session() as session:
            return await session.get(CompanySetting, settings_id)

    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting:
        if self.app_core and self.app_core.current_user:
            settings_obj.updated_by_user_id = self.app_core.current_user.id # type: ignore
        async with self.db_manager.session() as session:
            session.add(settings_obj)
            await session.flush()
            await session.refresh(settings_obj)
            return settings_obj

```

# app/services/__init__.py
```py
# app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict 
from datetime import date
from decimal import Decimal 

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData, SalesInvoiceSummaryData

# --- Enum Imports (for filter types in interfaces) ---
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum


# --- Existing Interfaces (condensed for brevity) ---
class IAccountRepository(IRepository[Account, int]): # ...
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): # ...
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): # ...
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): # ...
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): # ...
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): # ... 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): # ...
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): # ...
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): # ... 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): # ...
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): # ...
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): # ...
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass

class IVendorRepository(IRepository[Vendor, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass

class IProductRepository(IRepository[Product, int]): # ... 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass

# --- Service Implementations ---
from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService
from .business_services import CustomerService, VendorService, ProductService, SalesInvoiceService # New Import for SalesInvoiceService

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", # Added SalesInvoiceService
]

```

# app/services/accounting_services.py
```py
# File: app/services/accounting_services.py
from typing import List, Optional, Any, TYPE_CHECKING
from datetime import date
from sqlalchemy import select, and_, or_ # Added or_
from app.models.accounting.account_type import AccountType
from app.models.accounting.currency import Currency
from app.models.accounting.exchange_rate import ExchangeRate
from app.models.accounting.fiscal_year import FiscalYear 
from app.core.database_manager import DatabaseManager
from app.services import (
    IAccountTypeRepository, 
    ICurrencyRepository, 
    IExchangeRateRepository,
    IFiscalYearRepository 
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore


class AccountTypeService(IAccountTypeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            return await session.get(AccountType, id_val)

    async def get_all(self) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).order_by(AccountType.display_order, AccountType.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: AccountType) -> AccountType:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(AccountType, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, name: str) -> Optional[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.name == name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_category(self, category: str) -> List[AccountType]:
        async with self.db_manager.session() as session:
            stmt = select(AccountType).where(AccountType.category == category).order_by(AccountType.display_order)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class CurrencyService(ICurrencyRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: str) -> Optional[Currency]:
        async with self.db_manager.session() as session:
            return await session.get(Currency, id_val)

    async def get_all(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                 entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                 entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: Currency) -> Currency:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: str) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(Currency, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_all_active(self) -> List[Currency]:
        async with self.db_manager.session() as session:
            stmt = select(Currency).where(Currency.is_active == True).order_by(Currency.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())


class ExchangeRateService(IExchangeRateRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            return await session.get(ExchangeRate, id_val)

    async def get_all(self) -> List[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).order_by(ExchangeRate.rate_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def update(self, entity: ExchangeRate) -> ExchangeRate:
        return await self.save(entity)

    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(ExchangeRate, id_val)
            if entity:
                await session.delete(entity)
                return True
            return False

    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]:
        async with self.db_manager.session() as session:
            stmt = select(ExchangeRate).where(
                ExchangeRate.from_currency_code == from_code,
                ExchangeRate.to_currency_code == to_code,
                ExchangeRate.rate_date == r_date
            )
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def save(self, entity: ExchangeRate) -> ExchangeRate:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id
            if not entity.id: 
                 if hasattr(entity, 'created_by_user_id') and not entity.created_by_user_id:
                    entity.created_by_user_id = user_id # type: ignore
            if hasattr(entity, 'updated_by_user_id'):
                entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

class FiscalYearService(IFiscalYearRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalYear, id_val)

    async def get_all(self) -> List[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).order_by(FiscalYear.start_date.desc()) 
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)

    async def update(self, entity: FiscalYear) -> FiscalYear:
        return await self.save(entity)
    
    async def save(self, entity: FiscalYear) -> FiscalYear:
        # User audit fields are directly on FiscalYear model and should be set by manager
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def delete(self, id_val: int) -> bool:
        # Implement checks: e.g., cannot delete if periods exist or year is not closed.
        # For MVP, direct delete after confirmation by manager.
        async with self.db_manager.session() as session:
            entity = await session.get(FiscalYear, id_val)
            if entity:
                # Add check for associated fiscal periods
                if entity.fiscal_periods:
                     raise ValueError(f"Cannot delete fiscal year '{entity.year_name}' as it has associated fiscal periods.")
                await session.delete(entity)
                return True
            return False

    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalYear).where(FiscalYear.year_name == year_name)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]:
        async with self.db_manager.session() as session:
            conditions = [
                # ExistingStart <= NewEnd AND ExistingEnd >= NewStart
                FiscalYear.start_date <= end_date,
                FiscalYear.end_date >= start_date
            ]
            if exclude_id is not None:
                conditions.append(FiscalYear.id != exclude_id)
            
            stmt = select(FiscalYear).where(and_(*conditions))
            result = await session.execute(stmt)
            return result.scalars().first()

```

# app/services/tax_service.py
```py
# File: app/services/tax_service.py
from typing import List, Optional, Any, TYPE_CHECKING
from sqlalchemy import select
from app.models.accounting.tax_code import TaxCode 
from app.models.accounting.gst_return import GSTReturn 
# from app.core.database_manager import DatabaseManager # Already imported via IRepository context
from app.services import ITaxCodeRepository, IGSTReturnRepository 

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class TaxCodeService(ITaxCodeRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, id_val: int) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            return await session.get(TaxCode, id_val)
            
    async def get_tax_code(self, code: str) -> Optional[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.code == code, TaxCode.is_active == True)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[TaxCode]:
        async with self.db_manager.session() as session:
            stmt = select(TaxCode).where(TaxCode.is_active == True).order_by(TaxCode.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def save(self, entity: TaxCode) -> TaxCode: 
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not entity.id: 
                entity.created_by_user_id = user_id # type: ignore
            entity.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def add(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)

    async def update(self, entity: TaxCode) -> TaxCode:
        return await self.save(entity)
            
    async def delete(self, id_val: int) -> bool: 
        tax_code = await self.get_by_id(id_val)
        if tax_code and tax_code.is_active:
            tax_code.is_active = False
            await self.save(tax_code) 
            return True
        return False

class GSTReturnService(IGSTReturnRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core

    async def get_by_id(self, id_val: int) -> Optional[GSTReturn]:
        async with self.db_manager.session() as session:
            return await session.get(GSTReturn, id_val)

    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]:
        return await self.get_by_id(return_id)

    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn:
        if self.app_core and self.app_core.current_user:
            user_id = self.app_core.current_user.id 
            if not gst_return_data.id:
                gst_return_data.created_by_user_id = user_id # type: ignore
            gst_return_data.updated_by_user_id = user_id # type: ignore
        
        async with self.db_manager.session() as session:
            session.add(gst_return_data)
            await session.flush()
            await session.refresh(gst_return_data)
            return gst_return_data
    
    async def get_all(self) -> List[GSTReturn]:
        async with self.db_manager.session() as session:
            stmt = select(GSTReturn).order_by(GSTReturn.end_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def update(self, entity: GSTReturn) -> GSTReturn:
        return await self.save_gst_return(entity)

    async def delete(self, id_val: int) -> bool:
        gst_return = await self.get_by_id(id_val)
        if gst_return and gst_return.status == 'Draft':
            async with self.db_manager.session() as session:
                await session.delete(gst_return)
            return True
        return False

```

# app/services/account_service.py
```py
# File: app/services/account_service.py
# (Content previously updated, ensure imports and UserAuditMixin FKs are handled)
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy import select, func, text
from app.models.accounting.account import Account 
from app.models.accounting.journal_entry import JournalEntryLine, JournalEntry 
# from app.core.database_manager import DatabaseManager # Already imported by IAccountRepository context
from app.services import IAccountRepository 
from decimal import Decimal
from datetime import date # Added for type hint in has_transactions

if TYPE_CHECKING:
    from app.core.database_manager import DatabaseManager
    from app.core.application_core import ApplicationCore


class AccountService(IAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core 

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        async with self.db_manager.session() as session:
            return await session.get(Account, account_id)
    
    async def get_by_code(self, code: str) -> Optional[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code == code)
            result = await session.execute(stmt)
            return result.scalars().first()
    
    async def get_all(self) -> List[Account]: 
        async with self.db_manager.session() as session:
            stmt = select(Account).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_all_active(self) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.is_active == True).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]:
        async with self.db_manager.session() as session:
            conditions = [Account.account_type == account_type]
            if active_only:
                conditions.append(Account.is_active == True)
            
            stmt = select(Account).where(*conditions).order_by(Account.code)
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    async def has_transactions(self, account_id: int) -> bool:
        async with self.db_manager.session() as session:
            stmt_je = select(func.count(JournalEntryLine.id)).join(
                JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
            ).where(
                JournalEntryLine.account_id == account_id,
                JournalEntry.is_posted == True
            )
            count_je = (await session.execute(stmt_je)).scalar_one()

            acc = await session.get(Account, account_id)
            has_opening_balance_activity = False
            if acc and acc.opening_balance_date and acc.opening_balance != Decimal(0):
                has_opening_balance_activity = True
            
            return (count_je > 0) or has_opening_balance_activity

    async def save(self, account: Account) -> Account:
        async with self.db_manager.session() as session:
            session.add(account)
            await session.flush() 
            await session.refresh(account)
            return account

    async def add(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def update(self, entity: Account) -> Account: 
        return await self.save(entity)

    async def delete(self, account_id: int) -> bool: 
        raise NotImplementedError("Hard delete of accounts not typically supported. Use deactivation via manager.")
    
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        active_filter_main = "WHERE a.parent_id IS NULL"
        if active_only:
            active_filter_main += " AND a.is_active = TRUE"
        
        active_filter_recursive = ""
        if active_only:
            active_filter_recursive = "AND a.is_active = TRUE"

        query = f"""
            WITH RECURSIVE account_tree_cte AS (
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    0 AS level
                FROM accounting.accounts a
                {active_filter_main}
                
                UNION ALL
                
                SELECT 
                    a.id, a.code, a.name, a.account_type, a.sub_type, 
                    a.parent_id, a.is_active, a.description, 
                    a.report_group, a.is_control_account, a.is_bank_account,
                    a.opening_balance, a.opening_balance_date,
                    t.level + 1
                FROM accounting.accounts a
                JOIN account_tree_cte t ON a.parent_id = t.id
                WHERE 1=1 {active_filter_recursive} 
            )
            SELECT * FROM account_tree_cte
            ORDER BY account_type, code;
        """
        # Type casting for raw_accounts if execute_query returns list of asyncpg.Record
        raw_accounts: List[Any] = await self.db_manager.execute_query(query)
        accounts_data = [dict(row) for row in raw_accounts]
        
        account_map: Dict[int, Dict[str, Any]] = {account['id']: account for account in accounts_data}
        for account_dict in accounts_data: 
            account_dict['children'] = [] 

        tree_roots: List[Dict[str, Any]] = []
        for account_dict in accounts_data:
            if account_dict['parent_id'] and account_dict['parent_id'] in account_map:
                parent = account_map[account_dict['parent_id']]
                parent['children'].append(account_dict)
            elif not account_dict['parent_id']:
                tree_roots.append(account_dict)
        
        return tree_roots

    async def get_accounts_by_codes(self, codes: List[str]) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.code.in_(codes)) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]:
        async with self.db_manager.session() as session:
            stmt = select(Account).where(Account.tax_treatment == tax_treatment_code, Account.is_active == True)
            result = await session.execute(stmt)
            return list(result.scalars().all())

```

# app/services/business_services.py
```py
# app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload # Added joinedload
from decimal import Decimal
import logging 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine # New Import
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import ICustomerRepository, IVendorRepository, IProductRepository, ISalesInvoiceRepository # New Import ISalesInvoiceRepository
from app.utils.pydantic_models import CustomerSummaryData, VendorSummaryData, ProductSummaryData, SalesInvoiceSummaryData # New Import SalesInvoiceSummaryData
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum # New Import InvoiceStatusEnum
from datetime import date # For date type hints

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CustomerService(ICustomerRepository):
    # ... (CustomerService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) ))
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        log_msg = f"Hard delete attempted for Customer ID {customer_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")

class VendorService(IVendorRepository):
    # ... (VendorService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern)))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        log_msg = f"Hard delete attempted for Vendor ID {vendor_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")

class ProductService(IProductRepository):
    # ... (ProductService implementation remains unchanged from previous version)
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern)))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        log_msg = f"Hard delete attempted for Product/Service ID {product_id}. Not implemented; use deactivation."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")


# --- NEW: SalesInvoiceService Implementation ---
class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),
                selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),
                selectinload(SalesInvoice.customer),
                selectinload(SalesInvoice.currency),
                selectinload(SalesInvoice.journal_entry), # For posted invoices
                selectinload(SalesInvoice.created_by_user),
                selectinload(SalesInvoice.updated_by_user)
            ).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> List[SalesInvoice]:
        """ Fetches all sales invoice ORM objects. Use with caution for large datasets. """
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt)
            # Eager load lines if this method is used broadly, otherwise expect N+1 for lines.
            # For now, no explicit line loading here for performance on `get_all`.
            return list(result.scalars().all())

    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None:
                conditions.append(SalesInvoice.customer_id == customer_id)
            if status:
                conditions.append(SalesInvoice.status == status.value)
            if start_date:
                conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date:
                conditions.append(SalesInvoice.invoice_date <= end_date)
            
            # Select specific columns for summary and join with Customer for customer_name
            stmt = select(
                SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date,
                Customer.name.label("customer_name"), # Label for DTO mapping
                SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status
            ).join(Customer, SalesInvoice.customer_id == Customer.id) # Assuming Customer model is imported
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            
            if page_size > 0: # Enable pagination
                stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            
            result = await session.execute(stmt)
            # Map SQLAlchemy result (RowMapping) to Pydantic DTO
            return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]

    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(
                selectinload(SalesInvoice.lines) # Load lines when fetching by specific number
            ).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        """ Handles both create and update for SalesInvoice ORM objects.
            Assumes lines are managed via cascade on SalesInvoice.lines relationship.
        """
        async with self.db_manager.session() as session:
            session.add(invoice)
            await session.flush() # Populates IDs, processes cascades if lines are new
            await session.refresh(invoice) # Get DB defaults like created_at
            # Eager load lines after save to ensure they are part of the returned object graph
            if invoice.id and invoice.lines: # Check if lines were part of the save graph
                await session.refresh(invoice, attribute_names=['lines'])
                # for line in invoice.lines: # Optionally refresh each line too
                #     await session.refresh(line)
            return invoice

    async def add(self, entity: SalesInvoice) -> SalesInvoice:
        return await self.save(entity)

    async def update(self, entity: SalesInvoice) -> SalesInvoice:
        return await self.save(entity)

    async def delete(self, invoice_id: int) -> bool:
        # Sales invoices are typically not hard-deleted, but voided or cancelled.
        # This logic will be in the SalesInvoiceManager.
        log_msg = f"Hard delete attempted for Sales Invoice ID {invoice_id}. Not implemented; use void/cancel."
        if self.logger: self.logger.warning(log_msg)
        else: print(f"Warning: {log_msg}")
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")


```

# app/services/fiscal_period_service.py
```py
# File: app/services/fiscal_period_service.py
# Updated to use FiscalYear model
from typing import List, Optional
from datetime import date
from sqlalchemy import select, extract # Added extract
from app.models.accounting.fiscal_period import FiscalPeriod # Corrected path
from app.models.accounting.fiscal_year import FiscalYear # New import
from app.core.database_manager import DatabaseManager
from app.services import IFiscalPeriodRepository

class FiscalPeriodService(IFiscalPeriodRepository):
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def get_by_id(self, period_id: int) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            return await session.get(FiscalPeriod, period_id)

    async def get_all(self) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).order_by(FiscalPeriod.start_date)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity)
            await session.flush()
            await session.refresh(entity)
            return entity

    async def update(self, entity: FiscalPeriod) -> FiscalPeriod:
        async with self.db_manager.session() as session:
            session.add(entity) 
            await session.flush()
            await session.refresh(entity)
            return entity
            
    async def delete(self, id_val: int) -> bool:
        period = await self.get_by_id(id_val)
        if period and period.status != 'Archived': 
             async with self.db_manager.session() as session:
                await session.delete(period)
             return True
        return False

    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]:
        async with self.db_manager.session() as session:
            stmt = select(FiscalPeriod).where(
                FiscalPeriod.start_date <= target_date,
                FiscalPeriod.end_date >= target_date,
                FiscalPeriod.status == 'Open' 
            ).order_by(FiscalPeriod.start_date.desc()) 
            result = await session.execute(stmt)
            return result.scalars().first()
            
    async def get_fiscal_year(self, year_value: int) -> Optional[FiscalYear]: # Changed return type to FiscalYear
        """Gets the FiscalYear ORM object for the specified accounting year (e.g., 2023 for FY2023)."""
        async with self.db_manager.session() as session:
            # Assumes year_name is like "FY2023" or just "2023"
            # This needs a robust way to map an integer year to a FiscalYear record.
            # For now, assuming year_name contains the year as a string.
            # Option 1: year_name is "YYYY"
            # stmt = select(FiscalYear).where(FiscalYear.year_name == str(year_value))
            # Option 2: year_value is contained in year_name
            stmt = select(FiscalYear).where(FiscalYear.year_name.like(f"%{year_value}%")) # type: ignore
            # Option 3: Check if year_value falls within start_date and end_date
            # stmt = select(FiscalYear).where(
            #    extract('year', FiscalYear.start_date) <= year_value,
            #    extract('year', FiscalYear.end_date) >= year_value
            # )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]:
        async with self.db_manager.session() as session:
            conditions = [FiscalPeriod.fiscal_year_id == fiscal_year_id]
            if period_type:
                conditions.append(FiscalPeriod.period_type == period_type)
            stmt = select(FiscalPeriod).where(*conditions).order_by(FiscalPeriod.period_number)
            result = await session.execute(stmt)
            return list(result.scalars().all())

```


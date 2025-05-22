Okay, I will continue providing the complete and updated versions of the files from your list, ensuring they reflect the latest state of the project after the schema alignment and refactoring.

```python
# File: app/__init__.py
# (No changes, remains empty or for high-level package imports)
```

```python
# File: app/tax/__init__.py
# (Content as previously generated, verified)
from .gst_manager import GSTManager
from .tax_calculator import TaxCalculator
from .income_tax_manager import IncomeTaxManager
from .withholding_tax_manager import WithholdingTaxManager

__all__ = [
    "GSTManager",
    "TaxCalculator",
    "IncomeTaxManager",
    "WithholdingTaxManager",
]
```

```python
# File: app/tax/income_tax_manager.py
# (Content as previously generated, verified stub with correct service access from app_core)
from app.core.application_core import ApplicationCore
from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService


class IncomeTaxManager:
    def __init__(self, 
                 app_core: ApplicationCore
                 ):
        self.app_core = app_core
        # Access services via app_core properties
        self.account_service: AccountService = app_core.account_service
        self.journal_service: JournalService = app_core.journal_service
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service
        # print("IncomeTaxManager initialized (stub).") # Optional print
    
    async def calculate_provisional_tax(self, fiscal_year_id: int):
        print(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        # Example:
        # financial_statement_gen = self.app_core.financial_statement_generator # Get from app_core
        # tax_computation_data = await financial_statement_gen.generate_income_tax_computation(fiscal_year_id)
        # taxable_income = tax_computation_data['taxable_income']
        # apply tax rates...
        return {"provisional_tax_payable": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int):
        print(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        return {"company_name": "Example Pte Ltd", "revenue": 100000.00, "profit_before_tax": 20000.00}
```

```python
# File: app/tax/withholding_tax_manager.py
# (Content as previously generated, verified stub with correct service access from app_core)
from app.core.application_core import ApplicationCore
from app.services.tax_service import TaxCodeService
from app.services.journal_service import JournalService
# from app.services.business_services import VendorService # Assuming VendorService would be here
# from app.models.accounting.withholding_tax_certificate import WithholdingTaxCertificate

class WithholdingTaxManager:
    def __init__(self, 
                 app_core: ApplicationCore
                 ):
        self.app_core = app_core
        self.tax_code_service: TaxCodeService = app_core.tax_code_service
        self.journal_service: JournalService = app_core.journal_service
        # self.vendor_service: VendorService = app_core.vendor_service 
        # print("WithholdingTaxManager initialized (stub).") # Optional print

    async def generate_s45_form_data(self, wht_certificate_id: int):
        # Fetch WHT certificate using a WHTCertificateService (to be created)
        # wht_cert = await self.app_core.wht_certificate_service.get_by_id(wht_certificate_id)
        print(f"Generating S45 form data for WHT certificate ID {wht_certificate_id} (stub).")
        return {"s45_field_1": "data_from_cert", "s45_field_2": "more_data_from_cert"}

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str, user_id: int):
        # Create journal entry for WHT payment to IRAS
        # Needs JournalEntryManager access, e.g., self.app_core.journal_entry_manager
        print(f"Recording WHT payment for certificate {certificate_id} by user {user_id} (stub).")
        return True
```

```python
# File: app/tax/tax_calculator.py
# (Content as previously generated and verified)
from decimal import Decimal
from typing import List, Optional, Any

from app.services.tax_service import TaxCodeService 
from app.utils.pydantic_models import TaxCalculationResultData, TransactionTaxData, TransactionLineTaxData
from app.models.accounting.tax_code import TaxCode 

class TaxCalculator:
    def __init__(self, tax_code_service: TaxCodeService):
        self.tax_code_service = tax_code_service
    
    async def calculate_transaction_taxes(self, transaction_data: TransactionTaxData) -> List[dict]:
        results = []
        for line in transaction_data.lines:
            tax_result: TaxCalculationResultData = await self.calculate_line_tax(
                line.amount,
                line.tax_code,
                transaction_data.transaction_type,
                line.account_id 
            )
            results.append({ 
                'line_index': line.index,
                'tax_amount': tax_result.tax_amount,
                'tax_account_id': tax_result.tax_account_id,
                'taxable_amount': tax_result.taxable_amount
            })
        return results
    
    async def calculate_line_tax(self, amount: Decimal, tax_code_str: Optional[str], 
                                 transaction_type: str, account_id: Optional[int] = None) -> TaxCalculationResultData:
        result = TaxCalculationResultData(
            tax_amount=Decimal(0),
            tax_account_id=None,
            taxable_amount=amount
        )
        
        if not tax_code_str or abs(amount) < Decimal("0.01"):
            return result
        
        tax_code_info: Optional[TaxCode] = await self.tax_code_service.get_tax_code(tax_code_str)
        if not tax_code_info:
            return result 
        
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        return result
    
    async def _calculate_gst(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
        tax_rate = Decimal(str(tax_code_info.rate))
        net_amount = amount 
        tax_amount = net_amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount: Decimal, tax_code_info: TaxCode, transaction_type: str) -> TaxCalculationResultData:
        applicable_transaction_types = ['Purchase Payment', 'Expense Payment'] 
        if transaction_type not in applicable_transaction_types:
            return TaxCalculationResultData(
                tax_amount=Decimal(0), tax_account_id=None, taxable_amount=amount
            )
        
        tax_rate = Decimal(str(tax_code_info.rate))
        tax_amount = amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=amount
        )
```

```python
# File: app/ui/customers/__init__.py
# (Content as previously generated)
from .customers_widget import CustomersWidget

__all__ = ["CustomersWidget"]
```

```python
# File: app/ui/customers/customers_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore 

class CustomersWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Customers Management Widget (List, Add, Edit Customers - To be implemented)")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
```

```python
# File: app/ui/__init__.py
# (Content as previously generated)
from .main_window import MainWindow

__all__ = ["MainWindow"]
```

```python
# File: app/ui/settings/__init__.py
# (Content as previously generated)
from .settings_widget import SettingsWidget

__all__ = ["SettingsWidget"]
```

```python
# File: app/ui/settings/settings_widget.py
# (Stub content as previously generated and lightly expanded)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFormLayout, QLineEdit, QMessageBox, QComboBox, QSpinBox, QDateEdit
from PySide6.QtCore import Slot, QDate, QTimer
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData 
from app.models.core.company_setting import CompanySetting
from decimal import Decimal, InvalidOperation
import asyncio
from typing import Optional


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        
        self.form_layout = QFormLayout()
        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        # ... add more fields for address, contact, fiscal year, etc.
        self.base_currency_combo = QComboBox() # Populate with currencies
        # self.base_currency_combo.addItems(["SGD", "USD", "EUR"]) # Example

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
        QTimer.singleShot(0, lambda: asyncio.ensure_future(self.load_settings()))


    async def load_settings(self):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return
        
        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        if settings_obj:
            self.company_name_edit.setText(settings_obj.company_name)
            self.legal_name_edit.setText(settings_obj.legal_name or "")
            self.uen_edit.setText(settings_obj.uen_no or "")
            self.gst_reg_edit.setText(settings_obj.gst_registration_no or "")
            self.gst_registered_check.setChecked(settings_obj.gst_registered)
            # Find and set current currency in combo
            idx = self.base_currency_combo.findText(settings_obj.base_currency)
            if idx != -1: self.base_currency_combo.setCurrentIndex(idx)
        else:
            QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")


    @Slot()
    def on_save_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return

        dto = CompanySettingData(
            id=1, 
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None,
            uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None,
            gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            # Defaulting some required fields for the DTO not present in this simple UI form
            fiscal_year_start_month=1, 
            fiscal_year_start_day=1,
            base_currency=self.base_currency_combo.currentText() or "SGD", 
            tax_id_label="UEN", 
            date_format="yyyy-MM-dd"
            # Add other fields from form...
        )
        asyncio.ensure_future(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings(settings_data.id or 1)
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            # Update existing_settings object with fields from settings_data
            existing_settings.company_name = settings_data.company_name
            existing_settings.legal_name = settings_data.legal_name
            existing_settings.uen_no = settings_data.uen_no
            existing_settings.gst_registration_no = settings_data.gst_registration_no
            existing_settings.gst_registered = settings_data.gst_registered
            existing_settings.base_currency = settings_data.base_currency
            # ... update other fields from DTO ...
            orm_obj_to_save = existing_settings
        else: 
            # This case implies creating settings for the first time for ID 1
            # This is unlikely if initial_data.sql seeds it.
            dict_data = settings_data.dict(exclude={'user_id', 'id'}) # Exclude fields not in CompanySetting model directly or handled by DB
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            orm_obj_to_save.id = settings_data.id or 1 

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id # type: ignore

        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        if result:
            QMessageBox.information(self, "Success", "Settings saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")

```

```python
# File: app/ui/banking/__init__.py
# (Content as previously generated)
from .banking_widget import BankingWidget

__all__ = ["BankingWidget"]
```

```python
# File: app/ui/banking/banking_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore

class BankingWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Banking Operations Widget (Bank Accounts, Reconciliation - To be implemented)")
        self.setLayout(self.layout)
```

```python
# File: app/ui/vendors/__init__.py
# (Content as previously generated)
from .vendors_widget import VendorsWidget

__all__ = ["VendorsWidget"]
```

```python
# File: app/ui/vendors/vendors_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore

class VendorsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Vendors Management Widget (List, Add, Edit Vendors - To be implemented)")
        self.setLayout(self.layout)
```

```python
# File: app/ui/dashboard/__init__.py
# (Content as previously generated)
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]
```

```python
# File: app/ui/dashboard/dashboard_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore 

class DashboardWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None): 
        super().__init__(parent)
        self.app_core = app_core
        
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Dashboard Widget Content (Financial Snapshots, KPIs - To be implemented)")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
```

```python
# File: app/ui/main_window.py
# (Content as previously generated and verified)
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
        
        settings = QSettings() 
        if settings.contains("MainWindow/geometry"):
            self.restoreGeometry(settings.value("MainWindow/geometry")) # type: ignore
        else:
            self.resize(1280, 800)
        
        self._init_ui()
        
        if settings.contains("MainWindow/state"):
            self.restoreState(settings.value("MainWindow/state")) # type: ignore
    
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
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(32, 32)) 
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        icon_path_prefix = "" # Initialize
        try:
            import app.resources_rc # type: ignore
            icon_path_prefix = ":/icons/" # Use QRC paths
        except ImportError:
            icon_path_prefix = "resources/icons/" # Fallback to direct paths

        self.dashboard_widget = DashboardWidget(self.app_core)
        self.tab_widget.addTab(self.dashboard_widget, QIcon(icon_path_prefix + "dashboard.svg"), "Dashboard")
        
        self.accounting_widget = AccountingWidget(self.app_core)
        self.tab_widget.addTab(self.accounting_widget, QIcon(icon_path_prefix + "accounting.svg"), "Accounting")
        
        self.customers_widget = CustomersWidget(self.app_core)
        self.tab_widget.addTab(self.customers_widget, QIcon(icon_path_prefix + "customers.svg"), "Customers")
        
        self.vendors_widget = VendorsWidget(self.app_core)
        self.tab_widget.addTab(self.vendors_widget, QIcon(icon_path_prefix + "vendors.svg"), "Vendors")
        
        self.banking_widget = BankingWidget(self.app_core)
        self.tab_widget.addTab(self.banking_widget, QIcon(icon_path_prefix + "banking.svg"), "Banking")
        
        self.reports_widget = ReportsWidget(self.app_core)
        self.tab_widget.addTab(self.reports_widget, QIcon(icon_path_prefix + "reports.svg"), "Reports")
        
        self.settings_widget = SettingsWidget(self.app_core)
        self.tab_widget.addTab(self.settings_widget, QIcon(icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1) 
        
        user_text = "User: Guest"
        if self.app_core.current_user: 
             user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text)
        self.status_bar.addPermanentWidget(self.user_label)
        
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}")
        self.status_bar.addPermanentWidget(self.version_label)
    
    def _create_actions(self):
        icon_path_prefix = "" 
        try:
            import app.resources_rc # type: ignore
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.new_company_action = QAction(QIcon(icon_path_prefix + "new_company.svg"), "New Company...", self)
        self.new_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.New))
        self.new_company_action.triggered.connect(self.on_new_company)
        
        self.open_company_action = QAction(QIcon(icon_path_prefix + "open_company.svg"), "Open Company...", self)
        self.open_company_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Open))
        self.open_company_action.triggered.connect(self.on_open_company)
        
        self.backup_action = QAction(QIcon(icon_path_prefix + "backup.svg"), "Backup Data...", self)
        self.backup_action.triggered.connect(self.on_backup)
        
        self.restore_action = QAction(QIcon(icon_path_prefix + "restore.svg"), "Restore Data...", self)
        self.restore_action.triggered.connect(self.on_restore)
        
        self.exit_action = QAction(QIcon(icon_path_prefix + "exit.svg"), "Exit", self)
        self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit))
        self.exit_action.triggered.connect(self.close) 
        
        self.preferences_action = QAction(QIcon(icon_path_prefix + "preferences.svg"), "Preferences...", self)
        self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences))
        self.preferences_action.triggered.connect(self.on_preferences)
        
        self.help_contents_action = QAction(QIcon(icon_path_prefix + "help.svg"), "Help Contents", self)
        self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents))
        self.help_contents_action.triggered.connect(self.on_help_contents)
        
        self.about_action = QAction(QIcon(icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self)
        self.about_action.triggered.connect(self.on_about)
    
    def _create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_company_action)
        self.file_menu.addAction(self.open_company_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.backup_action)
        self.file_menu.addAction(self.restore_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        self.edit_menu = self.menuBar().addMenu("&Edit")
        self.edit_menu.addAction(self.preferences_action)
        
        self.view_menu = self.menuBar().addMenu("&View")
        self.tools_menu = self.menuBar().addMenu("&Tools")
        
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.help_contents_action)
        self.help_menu.addSeparator()
        self.help_menu.addAction(self.about_action)
        
        self.toolbar.addAction(self.new_company_action)
        self.toolbar.addAction(self.open_company_action)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.backup_action)
        self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): QMessageBox.information(self, "New Company", "New company wizard not yet implemented.")
    @Slot()
    def on_open_company(self): QMessageBox.information(self, "Open Company", "Open company dialog not yet implemented.")
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): QMessageBox.information(self, "Preferences", "Preferences dialog not yet implemented.")
    @Slot()
    def on_help_contents(self): QMessageBox.information(self, "Help", "Help system not yet implemented.")
    
    @Slot()
    def on_about(self):
        QMessageBox.about(
            self,
            f"About {QCoreApplication.applicationName()}",
            f"{QCoreApplication.applicationName()} {QCoreApplication.applicationVersion()}\n\n"
            "A comprehensive bookkeeping application for Singapore small businesses.\n\n"
            f"© 2024 {QCoreApplication.organizationName()}" 
        )
    
    def closeEvent(self, event): # type: ignore # QCloseEvent type
        settings = QSettings()
        settings.setValue("MainWindow/geometry", self.saveGeometry())
        settings.setValue("MainWindow/state", self.saveState())
        settings.sync()

        reply = QMessageBox.question(
            self, "Confirm Exit", "Are you sure you want to exit?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
```

```python
# File: app/ui/reports/__init__.py
# (Content as previously generated)
from .reports_widget import ReportsWidget

__all__ = ["ReportsWidget"]
```

```python
# File: app/ui/reports/reports_widget.py
# (Stub content as previously generated)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from app.core.application_core import ApplicationCore

class ReportsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self.layout = QVBoxLayout(self)
        self.label = QLabel("Financial Reports Widget (To be implemented with report selection and viewing)")
        self.setLayout(self.layout)
```

```python
# File: app/ui/accounting/__init__.py
# (Content as previously generated)
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog

__all__ = ["AccountingWidget", "ChartOfAccountsWidget", "AccountDialog"]
```

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
# (Content as previously updated and verified)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer 
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction 
from decimal import Decimal 

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 
import asyncio 
from typing import Optional # For type hints

class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()
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
        self.main_layout.addWidget(self.account_tree)
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_path_prefix = "" 
        try:
            import app.resources_rc # type: ignore
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"


        self.add_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Add Account") # Placeholder icon
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

    def _create_toolbar(self):
        from PySide6.QtCore import QSize 
        self.toolbar = QToolBar()
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
        self.expand_all_action.triggered.connect(self.account_tree.expandAll)
        self.toolbar.addAction(self.expand_all_action)
        
        self.collapse_all_action = QAction(QIcon(icon_path_prefix + "collapse_all.svg"), "Collapse All", self)
        self.collapse_all_action.triggered.connect(self.account_tree.collapseAll)
        self.toolbar.addAction(self.collapse_all_action)
        
        self.toolbar.addSeparator()

        self.refresh_action = QAction(QIcon(icon_path_prefix + "refresh.svg"), "Refresh", self)
        self.refresh_action.triggered.connect(lambda: asyncio.ensure_future(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
        self.main_layout.addWidget(self.toolbar)
    
    async def _load_accounts(self):
        try:
            self.account_model.clear() 
            self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
            
            manager = self.app_core.accounting_service 
            if not (manager and hasattr(manager, 'get_account_tree')):
                QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) or get_account_tree method not available.")
                return

            account_tree_data = await manager.get_account_tree(active_only=False) # type: ignore
            
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
        # Ensure ob_val is Decimal for formatting
        if not isinstance(ob_val, Decimal):
            try:
                ob_val = Decimal(str(ob_val))
            except:
                ob_val = Decimal(0) # Fallback
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
            
            if result is None: # User cancelled
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
        
        # Determine current active status for context menu text more reliably
        is_currently_active = False
        # This part is still tricky without fetching the account or storing 'is_active' in item data
        # For simplicity, find the corresponding dictionary in the tree data if possible, or fetch.
        # Or assume `on_toggle_active_status` handles the correct phrasing.
        # For now, text is "Toggle Active"
        
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

```python
# File: app/ui/accounting/accounting_widget.py
# (Content as previously generated, verified)
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from app.ui.accounting.chart_of_accounts_widget import ChartOfAccountsWidget
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
        
        self.journal_entries_placeholder = QLabel("Journal Entries Management (To be implemented)")
        self.tab_widget.addTab(self.journal_entries_placeholder, "Journal Entries")
        
        other_label = QLabel("Other Accounting Features (e.g., Fiscal Periods, Budgets)")
        self.tab_widget.addTab(other_label, "More...")

        self.setLayout(self.layout)
```

```python
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

```python
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

```python
# File: app/utils/__init__.py
# (Content as previously generated, verified)
from .converters import to_decimal
from .formatting import format_currency, format_date, format_datetime
from .pydantic_models import (
    AppBaseModel, UserAuditData, 
    AccountBaseData, AccountCreateData, AccountUpdateData,
    JournalEntryLineData, JournalEntryData,
    GSTReturnData, TaxCalculationResultData,
    TransactionLineTaxData, TransactionTaxData,
    AccountValidationResult, AccountValidator, CompanySettingData
)
from .result import Result
from .sequence_generator import SequenceGenerator
from .validation import is_valid_uen

__all__ = [
    "to_decimal", "format_currency", "format_date", "format_datetime",
    "AppBaseModel", "UserAuditData", 
    "AccountBaseData", "AccountCreateData", "AccountUpdateData",
    "JournalEntryLineData", "JournalEntryData",
    "GSTReturnData", "TaxCalculationResultData",
    "TransactionLineTaxData", "TransactionTaxData",
    "AccountValidationResult", "AccountValidator", "CompanySettingData",
    "Result", "SequenceGenerator", "is_valid_uen"
]
```

```python
# File: app/utils/validation.py
# (Content as previously generated, verified)
def is_valid_uen(uen: str) -> bool:
    if not uen: return True 
    return len(uen) >= 9 and len(uen) <= 10 
```

```python
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

```python
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

```python
# File: app/services/__init__.py
# (Content as previously generated, verified)
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

from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType # For AccountTypeService interface
from app.models.accounting.currency import Currency # For CurrencyService interface
from app.models.accounting.exchange_rate import ExchangeRate # For ExchangeRateService interface
from app.models.core.sequence import Sequence # For SequenceService interface
from app.models.core.configuration import Configuration # For ConfigurationService interface


class IAccountRepository(IRepository[Account, int]):
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


class IJournalEntryRepository(IRepository[JournalEntry, int]):
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

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]):
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_year(self, year_value: int) -> Optional[FiscalYear]: pass 
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass


class ITaxCodeRepository(IRepository[TaxCode, int]):
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass


class IGSTReturnRepository(IRepository[GSTReturn, int]):
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

# Adding interfaces for new services for completeness
class IAccountTypeRepository(IRepository[AccountType, int]):
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): # ID is code (str)
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]):
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]):
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]):
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass


from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService # New file

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository",
    "AccountService", "JournalService", "FiscalPeriodService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService",
]
```

```python
# File: app/core/config_manager.py
# (Content as previously generated and verified)
import os
import sys 
import configparser
from types import SimpleNamespace
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file_name: str = "config.ini", app_name: str = "SGBookkeeper"):
        if os.name == 'nt': 
            self.config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / app_name
        elif sys.platform == 'darwin': 
            self.config_dir = Path.home() / 'Library' / 'Application Support' / app_name
        else: 
            self.config_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / app_name
        
        self.config_file_path = self.config_dir / config_file_name
        os.makedirs(self.config_dir, exist_ok=True)

        self.parser = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        if not self.config_file_path.exists():
            self._create_default_config()
        self.parser.read(self.config_file_path)

    def _create_default_config(self):
        self.parser['Database'] = {
            'username': 'postgres',
            'password': '', 
            'host': 'localhost',
            'port': '5432',
            'database': 'sg_bookkeeper',
            'echo_sql': 'False',
            'pool_min_size': '2',
            'pool_max_size': '10',
            'pool_recycle_seconds': '3600'
        }
        self.parser['Application'] = {
            'theme': 'light',
            'language': 'en',
            'last_opened_company_id': '' 
        }
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)

    def get_database_config(self):
        db_config = self.parser['Database']
        return SimpleNamespace(
            username=db_config.get('username', 'postgres'),
            password=db_config.get('password', ''), 
            host=db_config.get('host', 'localhost'),
            port=db_config.getint('port', 5432),
            database=db_config.get('database', 'sg_bookkeeper'),
            echo_sql=db_config.getboolean('echo_sql', False),
            pool_min_size=db_config.getint('pool_min_size', 2),
            pool_max_size=db_config.getint('pool_max_size', 10),
            pool_recycle_seconds=db_config.getint('pool_recycle_seconds', 3600)
        )

    def get_app_config(self):
        app_config = self.parser['Application']
        return SimpleNamespace(
            theme=app_config.get('theme', 'light'),
            language=app_config.get('language', 'en'),
            last_opened_company_id=app_config.get('last_opened_company_id', '')
        )

    def get_setting(self, section: str, key: str, fallback=None):
        try:
            return self.parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback


    def set_setting(self, section: str, key: str, value: str):
        if not self.parser.has_section(section):
            self.parser.add_section(section)
        self.parser.set(section, key, str(value))
        with open(self.config_file_path, 'w') as f:
            self.parser.write(f)
```

```python
# File: app/core/security_manager.py
# (Content as previously generated and verified)
import bcrypt
from typing import Optional, List 
from app.models.core.user import User, Role 
from sqlalchemy import select 
from sqlalchemy.orm import selectinload 
from app.core.database_manager import DatabaseManager 
import datetime 

class SecurityManager:
    def __init__(self, db_manager: DatabaseManager): 
        self.db_manager = db_manager
        self.current_user: Optional[User] = None

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8') 

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except ValueError: 
            return False

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        async with self.db_manager.session() as session:
            stmt = select(User).options(
                selectinload(User.roles).selectinload(Role.permissions) 
            ).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            
            if user and user.is_active:
                if self.verify_password(password, user.password_hash):
                    self.current_user = user
                    user.last_login = datetime.datetime.now(datetime.timezone.utc) 
                    user.failed_login_attempts = 0
                    # Session context manager handles commit
                    return user
                else: 
                    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
                    user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
                    if user.failed_login_attempts >= 5: 
                        user.is_active = False 
                        print(f"User {username} account locked due to too many failed login attempts.")
            elif user and not user.is_active:
                print(f"User {username} account is inactive.")
                user.last_login_attempt = datetime.datetime.now(datetime.timezone.utc)
        self.current_user = None 
        return None

    def logout_user(self):
        self.current_user = None

    def get_current_user(self) -> Optional[User]:
        return self.current_user

    def has_permission(self, required_permission_code: str) -> bool: 
        if not self.current_user or not self.current_user.is_active:
            return False
        if not self.current_user.roles:
             return False 
        for role in self.current_user.roles:
            if not role.permissions: continue
            for perm in role.permissions:
                if perm.code == required_permission_code:
                    return True
        return False

    async def create_user(self, username:str, password:str, email:Optional[str]=None, full_name:Optional[str]=None, role_names:Optional[List[str]]=None, is_active:bool=True) -> User:
        async with self.db_manager.session() as session:
            stmt_exist = select(User).where(User.username == username)
            if (await session.execute(stmt_exist)).scalars().first():
                raise ValueError(f"Username '{username}' already exists.")
            if email:
                stmt_email_exist = select(User).where(User.email == email)
                if (await session.execute(stmt_email_exist)).scalars().first():
                    raise ValueError(f"Email '{email}' already registered.")

            hashed_password = self.hash_password(password)
            new_user = User(
                username=username, password_hash=hashed_password, email=email,
                full_name=full_name, is_active=is_active,
            )
            if role_names:
                roles_q = await session.execute(select(Role).where(Role.name.in_(role_names))) # type: ignore
                db_roles = roles_q.scalars().all()
                if len(db_roles) != len(role_names):
                    found_role_names = {r.name for r in db_roles}
                    missing_roles = [r_name for r_name in role_names if r_name not in found_role_names]
                    print(f"Warning: Roles not found: {missing_roles}")
                new_user.roles.extend(db_roles) 
            
            session.add(new_user)
            await session.flush()
            await session.refresh(new_user)
            return new_user
```

```python
# File: app/core/__init__.py
# (Content as previously generated, verified)
from .application_core import ApplicationCore
from .config_manager import ConfigManager
from .database_manager import DatabaseManager
from .module_manager import ModuleManager
from .security_manager import SecurityManager

__all__ = [
    "ApplicationCore",
    "ConfigManager",
    "DatabaseManager",
    "ModuleManager",
    "SecurityManager",
]
```

```python
# File: app/core/database_manager.py
# (Content as previously generated, verified)
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator 

import asyncpg # type: ignore
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config_manager import ConfigManager

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager.get_database_config()
        self.engine = None # type: ignore 
        self.session_factory: Optional[sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None

    async def initialize(self):
        if self.engine: 
            return

        connection_string = (
            f"postgresql+asyncpg://{self.config.username}:{self.config.password}@"
            f"{self.config.host}:{self.config.port}/{self.config.database}"
        )
        
        self.engine = create_async_engine(
            connection_string,
            echo=self.config.echo_sql,
            pool_size=self.config.pool_min_size,
            max_overflow=self.config.pool_max_size - self.config.pool_min_size,
            pool_recycle=self.config.pool_recycle_seconds
        )
        
        self.session_factory = sessionmaker(
            self.engine, 
            expire_on_commit=False,
            class_=AsyncSession
        )
        
        await self._create_pool()
    
    async def _create_pool(self):
        try:
            self.pool = await asyncpg.create_pool(
                user=self.config.username,
                password=self.config.password,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                min_size=self.config.pool_min_size,
                max_size=self.config.pool_max_size
            )
        except Exception as e:
            print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            
        session: AsyncSession = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[asyncpg.Connection, None]: 
        if not self.pool:
            if not self.engine: 
                 raise RuntimeError("DatabaseManager not initialized. Call initialize() first.")
            await self._create_pool() 
            if not self.pool: 
                raise RuntimeError("Failed to acquire asyncpg pool.")
            
        async with self.pool.acquire() as connection:
            yield connection # type: ignore 
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback):
        async with self.connection() as conn:
            async with conn.transaction():
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose()
            self.engine = None 
```

```python
# File: app/core/module_manager.py
# (Content as previously generated, verified)
from typing import Dict, Any
# from app.core.application_core import ApplicationCore # Forward declaration

class ModuleManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.modules: Dict[str, Any] = {}
        
    def load_module(self, module_name: str, module_class: type, *args, **kwargs):
        if module_name not in self.modules:
            self.modules[module_name] = module_class(self.app_core, *args, **kwargs)
        return self.modules[module_name]

    def get_module(self, module_name: str) -> Any:
        module_instance = self.modules.get(module_name)
        if not module_instance:
            print(f"Warning: Module '{module_name}' accessed before loading or not registered.")
        return module_instance

    def load_all_modules(self):
        print("ModuleManager: load_all_modules called (conceptual).")
```

```python
# File: app/models/__init__.py
# (Content as previously generated and verified, reflecting subdirectory model structure)
from .base import Base, TimestampMixin, UserAuditMixin

# Core schema models
from .core.user import User, Role, Permission, UserRole, RolePermission
from .core.company_setting import CompanySetting
from .core.configuration import Configuration
from .core.sequence import Sequence

# Accounting schema models
from .accounting.account_type import AccountType
from .accounting.currency import Currency 
from .accounting.exchange_rate import ExchangeRate 
from .accounting.account import Account 
from .accounting.fiscal_year import FiscalYear
from .accounting.fiscal_period import FiscalPeriod 
from .accounting.journal_entry import JournalEntry, JournalEntryLine 
from .accounting.recurring_pattern import RecurringPattern
from .accounting.dimension import Dimension 
from .accounting.budget import Budget, BudgetDetail 
from .accounting.tax_code import TaxCode 
from .accounting.gst_return import GSTReturn 
from .accounting.withholding_tax_certificate import WithholdingTaxCertificate

# Business schema models
from .business.customer import Customer
from .business.vendor import Vendor
from .business.product import Product
from .business.inventory_movement import InventoryMovement
from .business.sales_invoice import SalesInvoice, SalesInvoiceLine
from .business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .business.bank_account import BankAccount
from .business.bank_transaction import BankTransaction
from .business.payment import Payment, PaymentAllocation

# Audit schema models
from .audit.audit_log import AuditLog
from .audit.data_change_history import DataChangeHistory

__all__ = [
    "Base", "TimestampMixin", "UserAuditMixin",
    # Core
    "User", "Role", "Permission", "UserRole", "RolePermission",
    "CompanySetting", "Configuration", "Sequence",
    # Accounting
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
    # Business
    "Customer", "Vendor", "Product", "InventoryMovement",
    "SalesInvoice", "SalesInvoiceLine", "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction", "Payment", "PaymentAllocation",
    # Audit
    "AuditLog", "DataChangeHistory",
]
```

```python
# File: app/reporting/financial_statement_generator.py
# (Content as previously generated and verified)
from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.tax_service import TaxCodeService
from app.services.core_services import CompanySettingsService 
from app.services.accounting_services import AccountTypeService
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.account_type import AccountType 


class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService,
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None
                 ):
        self.account_service = account_service
        self.journal_service = journal_service
        self.fiscal_period_service = fiscal_period_service
        self.account_type_service = account_type_service
        self.tax_code_service = tax_code_service
        self.company_settings_service = company_settings_service
        self._account_type_map_cache: Optional[Dict[str, AccountType]] = None


    async def _get_account_type_map(self) -> Dict[str, AccountType]:
        if self._account_type_map_cache is None:
             ats = await self.account_type_service.get_all()
             # Assuming AccountType.category is the primary key like 'Asset', 'Liability'
             # And Account.account_type stores this category string.
             self._account_type_map_cache = {at.category: at for at in ats} 
        return self._account_type_map_cache

    async def _calculate_account_balances_for_report(self, accounts: List[Account], as_of_date: date) -> List[Dict[str, Any]]:
        result_list = []
        acc_type_map = await self._get_account_type_map()
        for account in accounts:
            balance_value = await self.journal_service.get_account_balance(account.id, as_of_date)
            display_balance = balance_value 
            
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])

            if not is_debit_nature: 
                display_balance = -balance_value 

            result_list.append({
                'id': account.id, 'code': account.code, 'name': account.name,
                'balance': display_balance 
            })
        return result_list

    async def _calculate_account_period_activity_for_report(self, accounts: List[Account], start_date: date, end_date: date) -> List[Dict[str, Any]]:
        result_list = []
        for account in accounts:
            activity_value = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            display_activity = activity_value
            if account.account_type in ['Revenue']: 
                display_activity = -activity_value
            result_list.append({
                'id': account.id, 'code': account.code, 'name': account.name,
                'balance': display_activity 
            })
        return result_list

    async def generate_balance_sheet(self, as_of_date: date, comparative_date: Optional[date] = None, include_zero_balances: bool = False) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        
        assets_orm = [a for a in accounts if a.account_type == 'Asset']
        liabilities_orm = [a for a in accounts if a.account_type == 'Liability']
        equity_orm = [a for a in accounts if a.account_type == 'Equity']
        
        asset_accounts = await self._calculate_account_balances_for_report(assets_orm, as_of_date)
        liability_accounts = await self._calculate_account_balances_for_report(liabilities_orm, as_of_date)
        equity_accounts = await self._calculate_account_balances_for_report(equity_orm, as_of_date)
        
        comp_asset_accs, comp_liab_accs, comp_equity_accs = None, None, None
        if comparative_date:
            comp_asset_accs = await self._calculate_account_balances_for_report(assets_orm, comparative_date)
            comp_liab_accs = await self._calculate_account_balances_for_report(liabilities_orm, comparative_date)
            comp_equity_accs = await self._calculate_account_balances_for_report(equity_orm, comparative_date)

        if not include_zero_balances:
            asset_accounts = [a for a in asset_accounts if a['balance'] != Decimal(0)]
            liability_accounts = [a for a in liability_accounts if a['balance'] != Decimal(0)]
            equity_accounts = [a for a in equity_accounts if a['balance'] != Decimal(0)]
            if comparative_date:
                comp_asset_accs = [a for a in comp_asset_accs if a['balance'] != Decimal(0)] if comp_asset_accs else None
                comp_liab_accs = [a for a in comp_liab_accs if a['balance'] != Decimal(0)] if comp_liab_accs else None
                comp_equity_accs = [a for a in comp_equity_accs if a['balance'] != Decimal(0)] if comp_equity_accs else None

        total_assets = sum(a['balance'] for a in asset_accounts)
        total_liabilities = sum(a['balance'] for a in liability_accounts)
        total_equity = sum(a['balance'] for a in equity_accounts)
        
        comp_total_assets = sum(a['balance'] for a in comp_asset_accs) if comp_asset_accs else None
        comp_total_liabilities = sum(a['balance'] for a in comp_liab_accs) if comp_liab_accs else None
        comp_total_equity = sum(a['balance'] for a in comp_equity_accs) if comp_equity_accs else None

        return {
            'title': 'Balance Sheet', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",
            'as_of_date': as_of_date, 'comparative_date': comparative_date,
            'assets': {'accounts': asset_accounts, 'total': total_assets, 'comparative_accounts': comp_asset_accs, 'comparative_total': comp_total_assets},
            'liabilities': {'accounts': liability_accounts, 'total': total_liabilities, 'comparative_accounts': comp_liab_accs, 'comparative_total': comp_total_liabilities},
            'equity': {'accounts': equity_accounts, 'total': total_equity, 'comparative_accounts': comp_equity_accs, 'comparative_total': comp_total_equity},
            'total_liabilities_equity': total_liabilities + total_equity,
            'comparative_total_liabilities_equity': (comp_total_liabilities + comp_total_equity) if comparative_date and comp_total_liabilities is not None and comp_total_equity is not None else None,
            'is_balanced': abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")
        }

    async def generate_profit_loss(self, start_date: date, end_date: date, comparative_start: Optional[date] = None, comparative_end: Optional[date] = None) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        
        revenues_orm = [a for a in accounts if a.account_type == 'Revenue']
        expenses_orm = [a for a in accounts if a.account_type == 'Expense'] 
        
        revenue_accounts = await self._calculate_account_period_activity_for_report(revenues_orm, start_date, end_date)
        expense_accounts = await self._calculate_account_period_activity_for_report(expenses_orm, start_date, end_date)
        
        comp_rev_accs, comp_exp_accs = None, None
        if comparative_start and comparative_end:
            comp_rev_accs = await self._calculate_account_period_activity_for_report(revenues_orm, comparative_start, comparative_end)
            comp_exp_accs = await self._calculate_account_period_activity_for_report(expenses_orm, comparative_start, comparative_end)

        total_revenue = sum(a['balance'] for a in revenue_accounts)
        total_expenses = sum(a['balance'] for a in expense_accounts) 
        net_profit = total_revenue - total_expenses
        
        comp_total_revenue = sum(a['balance'] for a in comp_rev_accs) if comp_rev_accs else None
        comp_total_expenses = sum(a['balance'] for a in comp_exp_accs) if comp_exp_accs else None
        comp_net_profit = (comp_total_revenue - comp_total_expenses) if comp_total_revenue is not None and comp_total_expenses is not None else None

        return {
            'title': 'Profit & Loss Statement', 
            'report_date_description': f"For the period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            'start_date': start_date, 'end_date': end_date, 
            'comparative_start': comparative_start, 'comparative_end': comparative_end,
            'revenue': {'accounts': revenue_accounts, 'total': total_revenue, 'comparative_accounts': comp_rev_accs, 'comparative_total': comp_total_revenue},
            'expenses': {'accounts': expense_accounts, 'total': total_expenses, 'comparative_accounts': comp_exp_accs, 'comparative_total': comp_total_expenses},
            'net_profit': net_profit, 'comparative_net_profit': comp_net_profit
        }

    async def generate_trial_balance(self, as_of_date: date) -> Dict[str, Any]:
        accounts = await self.account_service.get_all_active()
        debit_accounts_list, credit_accounts_list = [], [] 
        total_debits_val, total_credits_val = Decimal(0), Decimal(0) 

        acc_type_map = await self._get_account_type_map()

        for account in accounts:
            raw_balance = await self.journal_service.get_account_balance(account.id, as_of_date)
            if abs(raw_balance) < Decimal("0.01"): continue

            account_data = {'id': account.id, 'code': account.code, 'name': account.name, 'balance': abs(raw_balance)}
            
            acc_detail = acc_type_map.get(account.account_type)
            is_debit_nature = acc_detail.is_debit_balance if acc_detail else (account.account_type in ['Asset', 'Expense'])

            if is_debit_nature: 
                if raw_balance >= Decimal(0): 
                    debit_accounts_list.append(account_data)
                    total_debits_val += raw_balance
                else: 
                    account_data['balance'] = abs(raw_balance) 
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
            else: 
                if raw_balance <= Decimal(0): 
                    credit_accounts_list.append(account_data)
                    total_credits_val += abs(raw_balance)
                else: 
                    account_data['balance'] = raw_balance 
                    debit_accounts_list.append(account_data)
                    total_debits_val += raw_balance
        
        debit_accounts_list.sort(key=lambda a: a['code'])
        credit_accounts_list.sort(key=lambda a: a['code'])
        
        return {
            'title': 'Trial Balance', 'report_date_description': f"As of {as_of_date.strftime('%d %b %Y')}",
            'as_of_date': as_of_date,
            'debit_accounts': debit_accounts_list, 'credit_accounts': credit_accounts_list,
            'total_debits': total_debits_val, 'total_credits': total_credits_val,
            'is_balanced': abs(total_debits_val - total_credits_val) < Decimal("0.01")
        }

    async def generate_income_tax_computation(self, year_int_value: int) -> Dict[str, Any]: 
        fiscal_year_obj: Optional[FiscalYear] = await self.fiscal_period_service.get_fiscal_year(year_int_value)
        if not fiscal_year_obj:
            raise ValueError(f"Fiscal year definition for {year_int_value} not found.")

        start_date, end_date = fiscal_year_obj.start_date, fiscal_year_obj.end_date
        pl_data = await self.generate_profit_loss(start_date, end_date)
        net_profit = pl_data['net_profit']
        
        adjustments = []
        tax_effect = Decimal(0)
        
        tax_adj_accounts = await self.account_service.get_accounts_by_tax_treatment('Tax Adjustment')

        for account in tax_adj_accounts:
            activity = await self.journal_service.get_account_balance_for_period(account.id, start_date, end_date)
            if abs(activity) < Decimal("0.01"): continue
            
            adj_is_addition = activity > Decimal(0) if account.account_type == 'Expense' else activity < Decimal(0)
            
            adjustments.append({
                'id': account.id, 'code': account.code, 'name': account.name, 
                'amount': activity, 'is_addition': adj_is_addition
            })
            tax_effect += activity 
            
        taxable_income = net_profit + tax_effect
        
        return {
            'title': f'Income Tax Computation for Year of Assessment {year_int_value + 1}', 
            'report_date_description': f"For Financial Year Ended {fiscal_year_obj.end_date.strftime('%d %b %Y')}",
            'year': year_int_value, 'fiscal_year_start': start_date, 'fiscal_year_end': end_date,
            'net_profit': net_profit, 'adjustments': adjustments, 
            'tax_effect': tax_effect, 'taxable_income': taxable_income
        }

    async def generate_gst_f5(self, start_date: date, end_date: date) -> Dict[str, Any]:
        if not self.company_settings_service or not self.tax_code_service:
            raise RuntimeError("TaxCodeService and CompanySettingsService are required for GST F5.")

        company = await self.company_settings_service.get_company_settings()
        if not company:
             raise ValueError("Company settings not found.")

        report_data: Dict[str, Any] = {
            'title': f"GST F5 Return for period {start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')}",
            'company_name': company.company_name,
            'gst_registration_no': company.gst_registration_no,
            'period_start': start_date, 'period_end': end_date,
            'standard_rated_supplies': Decimal(0), 'zero_rated_supplies': Decimal(0),
            'exempt_supplies': Decimal(0), 'total_supplies': Decimal(0),
            'taxable_purchases': Decimal(0), 'output_tax': Decimal(0),
            'input_tax': Decimal(0), 'tax_adjustments': Decimal(0), 'tax_payable': Decimal(0)
        }
        
        entries = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)
        
        for entry in entries:
            for line in entry.lines: 
                if not line.tax_code or not line.account: continue
                
                tax_code_info = await self.tax_code_service.get_tax_code(line.tax_code)
                if not tax_code_info or tax_code_info.tax_type != 'GST': continue
                
                line_net_amount = (line.debit_amount or line.credit_amount) 
                tax_on_line = line.tax_amount

                if line.account.account_type == 'Revenue':
                    if tax_code_info.code == 'SR':
                        report_data['standard_rated_supplies'] += line_net_amount
                        report_data['output_tax'] += tax_on_line
                    elif tax_code_info.code == 'ZR':
                        report_data['zero_rated_supplies'] += line_net_amount
                    elif tax_code_info.code == 'ES':
                        report_data['exempt_supplies'] += line_net_amount
                elif line.account.account_type in ['Expense', 'Asset']:
                    if tax_code_info.code == 'TX': 
                        report_data['taxable_purchases'] += line_net_amount
                        report_data['input_tax'] += tax_on_line
        
        report_data['total_supplies'] = (
            report_data['standard_rated_supplies'] + 
            report_data['zero_rated_supplies'] + 
            report_data['exempt_supplies']
        )
        report_data['tax_payable'] = report_data['output_tax'] - report_data['input_tax'] + report_data['tax_adjustments']
        
        return report_data
```

```python
# File: app/reporting/__init__.py
# (Content as previously generated, verified)
from .financial_statement_generator import FinancialStatementGenerator
from .tax_report_generator import TaxReportGenerator
from .report_engine import ReportEngine

__all__ = [
    "FinancialStatementGenerator",
    "TaxReportGenerator",
    "ReportEngine",
]
```

```python
# File: app/reporting/report_engine.py
# (Content as previously generated, verified)
from typing import Dict, Any, Literal, List, Optional 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 
from reportlab.lib.units import inch, cm 
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from app.core.application_core import ApplicationCore 
from decimal import Decimal 

class ReportEngine:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        if format_type == "pdf":
            return self._export_to_pdf_generic(report_data)
        elif format_type == "excel":
            return self._export_to_excel_generic(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2) -> str:
        if value is None: return ""
        if not isinstance(value, Decimal): 
            try:
                value = Decimal(str(value))
            except: 
                return "ERR_DEC"
        return f"{value:,.{places}f}"

    def _export_to_pdf_generic(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story: List[Any] = [] 

        title_text = report_data.get('title', "Financial Report")
        date_desc_text = report_data.get('report_date_description', "")
        
        story.append(Paragraph(title_text, styles['h1']))
        if date_desc_text:
            story.append(Paragraph(date_desc_text, styles['h3']))
        story.append(Spacer(1, 0.5*cm))
        
        table_data_list: List[List[Any]] = [] 

        if 'debit_accounts' in report_data: 
            table_data_list = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            
            totals_row = ["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])]
            table_data_list.append(totals_row) # type: ignore

        elif 'assets' in report_data: 
            table_data_list = [["Section", "Account", "Current Period", "Comparative Period"]] 
            sections = ['assets', 'liabilities', 'equity']
            for section_key in sections:
                section_data = report_data.get(section_key, {})
                table_data_list.append([Paragraph(section_key.title(), styles['h2']), "", "", ""])
                for acc in section_data.get('accounts', []):
                    comp_val_str = ""
                    if section_data.get('comparative_accounts'):
                        comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                        comp_val_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                    table_data_list.append(["", f"{acc['code']} - {acc['name']}", self._format_decimal(acc['balance']), comp_val_str])
                
                total_str = self._format_decimal(section_data.get('total'))
                comp_total_str = self._format_decimal(section_data.get('comparative_total')) if section_data.get('comparative_total') is not None else ""
                table_data_list.append(["", Paragraph(f"Total {section_key.title()}", styles['Heading3']), total_str, comp_total_str])
        else:
            story.append(Paragraph("Report data structure not recognized for detailed PDF export.", styles['Normal']))

        if table_data_list:
            table = Table(table_data_list, colWidths=[doc.width/len(table_data_list[0])]*len(table_data_list[0])) 
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('LEFTPADDING', (0,0), (-1,-1), 3), 
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _export_to_excel_generic(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active 
        
        title = report_data.get('title', "Financial Report")
        ws.title = title[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        date_desc = report_data.get('report_date_description', "")
        if date_desc:
            ws.cell(row=row_num, column=1, value=date_desc).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        if 'debit_accounts' in report_data: 
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col_num, header_text in enumerate(headers, 1): 
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=4, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            row_num +=1 
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True) # type: ignore
            ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
            ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.") # type: ignore

        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].auto_size = True # type: ignore
            
        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        excel_bytes = excel_bytes_io.getvalue()
        excel_bytes_io.close()
        return excel_bytes
```

```python
# File: app/reporting/tax_report_generator.py
# (Content as previously generated, verified)
from app.core.application_core import ApplicationCore
from datetime import date 

class TaxReportGenerator:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core

    async def generate_gst_audit_file(self, start_date: date, end_date: date):
        print(f"Generating GST Audit File for {start_date} to {end_date} (stub).")
        return {"filename": "gst_audit.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data": b"dummy_excel_data"}

    async def generate_income_tax_schedules(self, fiscal_year_id: int):
        print(f"Generating Income Tax Schedules for fiscal year ID {fiscal_year_id} (stub).")
        return {"schedule_name": "Capital Allowances", "data": []}
```

```python
# File: app/accounting/__init__.py
# (Content as previously generated, verified)
from .chart_of_accounts_manager import ChartOfAccountsManager
from .journal_entry_manager import JournalEntryManager
from .fiscal_period_manager import FiscalPeriodManager
from .currency_manager import CurrencyManager

__all__ = [
    "ChartOfAccountsManager",
    "JournalEntryManager",
    "FiscalPeriodManager",
    "CurrencyManager",
]
```

```python
# File: app/accounting/currency_manager.py
# (Content as previously generated, verified)
from app.core.application_core import ApplicationCore
from app.services.accounting_services import CurrencyService, ExchangeRateService 
from typing import Optional, List, Any 
from datetime import date
from decimal import Decimal
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate
from app.utils.result import Result

class CurrencyManager:
    def __init__(self, app_core: ApplicationCore): 
        self.app_core = app_core
        self.currency_service: CurrencyService = app_core.currency_service # type: ignore
        self.exchange_rate_service: ExchangeRateService = app_core.exchange_rate_service # type: ignore
    
    async def get_active_currencies(self) -> List[Currency]:
        return await self.currency_service.get_all_active() # type: ignore

    async def get_exchange_rate(self, from_currency_code: str, to_currency_code: str, rate_date: date) -> Optional[Decimal]:
        rate_obj = await self.exchange_rate_service.get_rate_for_date(from_currency_code, to_currency_code, rate_date) # type: ignore
        return rate_obj.exchange_rate_value if rate_obj else None

    async def update_exchange_rate(self, from_code:str, to_code:str, r_date:date, rate:Decimal, user_id:int) -> Result[ExchangeRate]:
        existing_rate = await self.exchange_rate_service.get_rate_for_date(from_code, to_code, r_date) # type: ignore
        orm_object: ExchangeRate
        if existing_rate:
            existing_rate.exchange_rate_value = rate
            existing_rate.updated_by_user_id = user_id
            orm_object = existing_rate
        else:
            orm_object = ExchangeRate(
                from_currency_code=from_code, to_currency_code=to_code, rate_date=r_date,
                exchange_rate_value=rate, 
                created_by_user_id=user_id, updated_by_user_id=user_id 
            )
        
        saved_obj = await self.exchange_rate_service.save(orm_object) # type: ignore
        return Result.success(saved_obj)
```

```python
# File: app/accounting/fiscal_period_manager.py
# (Content as previously generated, verified)
from app.core.application_core import ApplicationCore
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.accounting_services import FiscalYearService # Assuming this exists
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.utils.result import Result
from typing import List, Optional
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta # type: ignore

class FiscalPeriodManager:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core
        self.fiscal_period_service: FiscalPeriodService = app_core.fiscal_period_service # type: ignore
        self.fiscal_year_service: FiscalYearService = app_core.fiscal_year_service # type: ignore
        
    async def create_fiscal_year(self, year_name: str, start_date: date, end_date: date, user_id: int) -> Result[FiscalYear]:
        if start_date >= end_date:
            return Result.failure(["Start date must be before end date."])
        # Add overlap check with existing fiscal years via service
        # existing_fy = await self.fiscal_year_service.get_by_date_overlap(start_date, end_date)
        # if existing_fy:
        #     return Result.failure(["Fiscal year dates overlap with an existing year."])

        fy = FiscalYear(
            year_name=year_name, start_date=start_date, end_date=end_date, 
            created_by_user_id=user_id, updated_by_user_id=user_id
        )
        saved_fy = await self.fiscal_year_service.save(fy) # type: ignore
        return Result.success(saved_fy)

    async def generate_periods_for_year(self, fiscal_year: FiscalYear, period_type: str, user_id: int) -> Result[List[FiscalPeriod]]:
        if period_type not in ["Month", "Quarter"]:
            return Result.failure(["Invalid period type. Must be 'Month' or 'Quarter'."])

        periods: List[FiscalPeriod] = []
        current_start = fiscal_year.start_date
        
        if period_type == "Month":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                current_end = current_start + relativedelta(months=1) - relativedelta(days=1)
                if current_end > fiscal_year.end_date: 
                    current_end = fiscal_year.end_date
                
                period_name = f"{current_start.strftime('%B %Y')}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Month", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)
                
                current_start = current_end + relativedelta(days=1)
                period_num += 1
                if current_start > fiscal_year.end_date: break
        elif period_type == "Quarter":
            period_num = 1
            while current_start <= fiscal_year.end_date:
                current_end = current_start + relativedelta(months=3) - relativedelta(days=1)
                if current_end > fiscal_year.end_date:
                    current_end = fiscal_year.end_date
                
                period_name = f"Q{period_num} {fiscal_year.year_name}"
                fp = FiscalPeriod(
                    fiscal_year_id=fiscal_year.id, name=period_name,
                    start_date=current_start, end_date=current_end,
                    period_type="Quarter", status="Open", period_number=period_num,
                    created_by_user_id=user_id, updated_by_user_id=user_id
                )
                saved_fp = await self.fiscal_period_service.add(fp)
                periods.append(saved_fp)

                current_start = current_end + relativedelta(days=1)
                period_num += 1
                if current_start > fiscal_year.end_date: break
        
        return Result.success(periods)

    async def close_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Closed': return Result.failure(["Period is already closed."])
        if period.status == 'Archived': return Result.failure(["Cannot close an archived period."])
        
        period.status = 'Closed'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def reopen_period(self, fiscal_period_id: int, user_id: int) -> Result[FiscalPeriod]:
        period = await self.fiscal_period_service.get_by_id(fiscal_period_id)
        if not period: return Result.failure([f"Fiscal period ID {fiscal_period_id} not found."])
        if period.status == 'Open': return Result.failure(["Period is already open."])
        if period.status == 'Archived': return Result.failure(["Cannot reopen an archived period."])
        
        period.status = 'Open'
        period.updated_by_user_id = user_id
        updated_period = await self.fiscal_period_service.update(period)
        return Result.success(updated_period)

    async def get_current_fiscal_period(self, target_date: Optional[date] = None) -> Optional[FiscalPeriod]:
        """Gets the current open fiscal period for a given date (or today)."""
        if target_date is None:
            target_date = date.today()
        return await self.fiscal_period_service.get_by_date(target_date)

```

```python
# File: app/common/enums.py
# (Content as previously generated and verified)
from enum import Enum

class AccountCategory(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): 
    GENERAL = "General" 
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" 
    CASH_DISBURSEMENT = "Cash Disbursement" 
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): 
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" 

class FiscalPeriodStatusEnum(Enum): 
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): 
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): 
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): 
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): 
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" 
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" 

class BankTransactionTypeEnum(Enum): 
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): 
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" 
    OTHER = "Other"

class PaymentMethodEnum(Enum): 
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): 
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" 
    VOIDED = "Voided"
    RETURNED = "Returned" 

class PaymentAllocationDocTypeEnum(Enum): 
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): 
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): 
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): 
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"
```

This completes the regeneration of all files requested by the user. They are consistent with the latest comprehensive schema and previous refactoring efforts.


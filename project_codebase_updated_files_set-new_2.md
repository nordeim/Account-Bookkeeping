# pyproject.toml
```toml
# pyproject.toml
[tool.poetry]
name = "sg-bookkeeper"
version = "1.0.0"
description = "Singapore small business bookkeeping application"
authors = ["Your Name <your.email@example.com>"]
license = "MIT"
readme = "README.md"
homepage = "https://github.com/yourusername/sg_bookkeeper"
repository = "https://github.com/yourusername/sg_bookkeeper"
keywords = ["accounting", "bookkeeping", "singapore", "gst", "tax"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Financial and Insurance Industry",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12", 
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Topic :: Office/Business :: Financial :: Accounting",
]
packages = [{include = "app", from = "."}]

[tool.poetry.dependencies]
python = ">=3.9,<3.13" 
PySide6 = "^6.9.0"   # The QtCharts module from this package is used for the dashboard
SQLAlchemy = {extras = ["asyncio"], version = ">=2.0.0"}
asyncpg = ">=0.25.0"
alembic = ">=1.7.5"
pydantic = {version = "^2.0", extras = ["email"]}
reportlab = ">=3.6.6"
openpyxl = ">=3.0.9"
python-dateutil = ">=2.8.2"
bcrypt = ">=3.2.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
flake8 = "^6.0"
black = "^24.0" 
mypy = "^1.0" 
pre-commit = "^3.0"
pytest-qt = "^4.0"
pytest-asyncio = "^0.21.0" 

[tool.poetry.scripts]
sg_bookkeeper = "app.main:main"
sg_bookkeeper_db_init = "scripts.db_init:main"

[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py39', 'py310', 'py311', 'py312']

[tool.pytest.ini_options]
python_files = "test_*.py tests.py" 
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"

```

# app/main.py
```py
# File: app/main.py
import sys
import asyncio
import threading
from pathlib import Path
from typing import Optional, Any, List, Dict # Added List, Dict

from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication, QMetaObject, Signal, Slot, Q_ARG, QProcess
from PySide6.QtGui import QPixmap, QColor 

# --- Globals for asyncio loop management ---
_ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None
_ASYNC_LOOP_THREAD: Optional[threading.Thread] = None
_ASYNC_LOOP_STARTED = threading.Event() 

def start_asyncio_event_loop_thread():
    """Target function for the asyncio thread."""
    global _ASYNC_LOOP
    try:
        _ASYNC_LOOP = asyncio.new_event_loop()
        asyncio.set_event_loop(_ASYNC_LOOP)
        _ASYNC_LOOP_STARTED.set() 
        print(f"Asyncio event loop {_ASYNC_LOOP} started in thread {threading.current_thread().name} and set as current.")
        _ASYNC_LOOP.run_forever()
    except Exception as e:
        print(f"Critical error in asyncio event loop thread: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
             pass 
        if _ASYNC_LOOP: 
             _ASYNC_LOOP.close()
        print("Asyncio event loop from dedicated thread has been stopped and closed.")

def schedule_task_from_qt(coro) -> Optional[asyncio.Future]:
    global _ASYNC_LOOP
    if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
        return asyncio.run_coroutine_threadsafe(coro, _ASYNC_LOOP)
    else:
        print("Error: Global asyncio event loop is not available or not running when trying to schedule task.")
        return None
# --- End Globals for asyncio loop management ---

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager

class Application(QApplication):
    initialization_done_signal = Signal(bool, object) 

    def __init__(self, argv):
        super().__init__(argv)
        self.setApplicationName("SGBookkeeper"); self.setApplicationVersion("1.0.0"); self.setOrganizationName("SGBookkeeperOrg"); self.setOrganizationDomain("sgbookkeeper.org") 
        
        splash_pixmap = None
        try:
            import app.resources_rc 
            splash_pixmap = QPixmap(":/images/splash.png")
        except ImportError:
            base_path = Path(__file__).resolve().parent.parent 
            splash_image_path = base_path / "resources" / "images" / "splash.png"
            if splash_image_path.exists(): splash_pixmap = QPixmap(str(splash_image_path))
            else: print(f"Warning: Splash image not found at {splash_image_path}.")

        if splash_pixmap is None or splash_pixmap.isNull():
            self.splash = QSplashScreen(); pm = QPixmap(400,200); pm.fill(Qt.GlobalColor.lightGray)
            self.splash.setPixmap(pm); self.splash.showMessage("Loading SG Bookkeeper...", Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.black)
        else:
            self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint); self.splash.setObjectName("SplashScreen")

        self.splash.show(); self.processEvents() 
        
        self.main_window: Optional[MainWindow] = None 
        self.app_core: Optional[ApplicationCore] = None

        self.initialization_done_signal.connect(self._on_initialization_done)
        
        future = schedule_task_from_qt(self.initialize_app())
        if future is None: self._on_initialization_done(False, RuntimeError("Failed to schedule app initialization (async loop not ready)."))
            
    @Slot(bool, object)
    def _on_initialization_done(self, success: bool, result_or_error: Any):
        if success:
            self.app_core = result_or_error 
            if not self.app_core:
                 QMessageBox.critical(None, "Fatal Error", "App core not received on successful initialization."); self.quit(); return
            self.main_window = MainWindow(self.app_core); self.main_window.show(); self.splash.finish(self.main_window)
        else:
            self.splash.hide()
            error_message = str(result_or_error) if result_or_error else "An unknown error occurred during initialization."
            print(f"Critical error during application startup: {error_message}") 
            if isinstance(result_or_error, Exception) and result_or_error.__traceback__:
                import traceback
                traceback.print_exception(type(result_or_error), result_or_error, result_or_error.__traceback__)
            QMessageBox.critical(None, "Application Initialization Error", f"An error occurred during application startup:\n{error_message[:500]}\n\nThe application will now exit."); self.quit()

    async def initialize_app(self):
        current_app_core = None
        try:
            def update_splash_threadsafe(message):
                if hasattr(self, 'splash') and self.splash:
                    QMetaObject.invokeMethod(self.splash, "showMessage", Qt.ConnectionType.QueuedConnection, Q_ARG(str, message), Q_ARG(int, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter), Q_ARG(QColor, QColor(Qt.GlobalColor.white)))
            
            update_splash_threadsafe("Loading configuration...")
            config_manager = ConfigManager(app_name=QCoreApplication.applicationName())
            db_config = config_manager.get_database_config()
            if not db_config.database or db_config.database == "sg_bookkeeper_default":
                 # If no company DB is selected, we can't fully initialize. We'll let MainWindow handle this.
                 # For now, let's proceed with a basic core that doesn't try to initialize the DB services.
                 # Or better, we can skip DB initialization and have MainWindow prompt user.
                 # Let's pass a special error to the main thread.
                raise ValueError("No company database selected. Please select or create a company.")

            update_splash_threadsafe("Initializing database manager...")
            db_manager = DatabaseManager(config_manager)
            update_splash_threadsafe("Initializing application core...")
            current_app_core = ApplicationCore(config_manager, db_manager)
            await current_app_core.startup() 

            if not current_app_core.current_user: 
                authenticated_user = await current_app_core.security_manager.authenticate_user("admin", "password")
                if not authenticated_user:
                    print("Default admin/password authentication failed or no such user. MainWindow should handle login.")

            update_splash_threadsafe("Finalizing initialization...")
            self.initialization_done_signal.emit(True, current_app_core) 
        except Exception as e:
            self.initialization_done_signal.emit(False, e) 

    def actual_shutdown_sequence(self): 
        print("Application shutting down (actual_shutdown_sequence)...")
        global _ASYNC_LOOP, _ASYNC_LOOP_THREAD
        
        if self.app_core:
            print("Scheduling ApplicationCore shutdown...")
            future = schedule_task_from_qt(self.app_core.shutdown())
            if future:
                try: future.result(timeout=2); print("ApplicationCore shutdown completed.")
                except TimeoutError: print("Warning: ApplicationCore async shutdown timed out.")
                except Exception as e: print(f"Error during ApplicationCore async shutdown via future: {e}")
            else: print("Warning: Could not schedule ApplicationCore async shutdown task.")
        
        if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
            print("Requesting global asyncio event loop to stop..."); _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
        
        if _ASYNC_LOOP_THREAD and _ASYNC_LOOP_THREAD.is_alive():
            print("Joining asyncio event loop thread..."); _ASYNC_LOOP_THREAD.join(timeout=2)
            if _ASYNC_LOOP_THREAD.is_alive(): print("Warning: Asyncio event loop thread did not terminate cleanly.")
            else: print("Asyncio event loop thread joined.")
        
        print("Application shutdown process finalized.")

def main():
    global _ASYNC_LOOP_THREAD, _ASYNC_LOOP_STARTED, _ASYNC_LOOP
    print("Starting global asyncio event loop thread...")
    _ASYNC_LOOP_THREAD = threading.Thread(target=start_asyncio_event_loop_thread, daemon=True, name="AsyncioLoopThread")
    _ASYNC_LOOP_THREAD.start()
    if not _ASYNC_LOOP_STARTED.wait(timeout=5): 
        print("Fatal: Global asyncio event loop did not start in time. Exiting."); sys.exit(1)
    print(f"Global asyncio event loop {_ASYNC_LOOP} confirmed running in dedicated thread.")

    try: import app.resources_rc 
    except ImportError:
        print("Warning: Compiled Qt resources (resources_rc.py) not found. Direct file paths will be used for icons/images.")
        print("Consider running from project root: pyside6-rcc resources/resources.qrc -o app/resources_rc.py")

    app = Application(sys.argv)
    app.aboutToQuit.connect(app.actual_shutdown_sequence) 
    exit_code = app.exec()
    
    if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
        print("Post app.exec(): Forcing asyncio loop stop (fallback)."); _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
    if _ASYNC_LOOP_THREAD and _ASYNC_LOOP_THREAD.is_alive():
        print("Post app.exec(): Joining asyncio thread (fallback)."); _ASYNC_LOOP_THREAD.join(timeout=1)
            
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

```

# app/tax/__init__.py
```py
# File: app/tax/__init__.py
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

# app/tax/income_tax_manager.py
```py
# File: app/tax/income_tax_manager.py
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService
    from app.services.fiscal_period_service import FiscalPeriodService


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.account_service: "AccountService" = app_core.account_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.fiscal_period_service: "FiscalPeriodService" = app_core.fiscal_period_service # type: ignore
        self.logger = app_core.logger
        self.logger.info("IncomeTaxManager initialized.")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int) -> Dict[str, Any]:
        self.logger.info(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        # In a real implementation, this would fetch the financial data for the ECI period,
        # apply rules (e.g., 75% of taxable income up to a cap is exempt), calculate tax,
        # and determine the provisional tax payable.
        # This would require a call to a report generator like FinancialStatementGenerator.
        return {"provisional_tax_payable": 0.00, "estimated_chargeable_income": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int) -> Dict[str, Any]:
        self.logger.info(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        # A real implementation would call the FinancialStatementGenerator, get the P&L and BS,
        # and populate a dictionary that maps directly to the fields on Form C-S.
        fy = await self.app_core.fiscal_year_service.get_by_id(fiscal_year_id)
        if not fy:
            return {"error": "Fiscal year not found."}
        
        report = await self.app_core.financial_statement_generator.generate_income_tax_computation(fy)
        
        return {
            "company_name": (await self.app_core.company_settings_service.get_company_settings()).company_name,
            "revenue": report.get('revenue', {}).get('total', 0.00),
            "profit_before_tax": report.get('net_profit_before_tax', 0.00),
            "chargeable_income": report.get('chargeable_income', 0.00)
        }

```

# app/tax/withholding_tax_manager.py
```py
# File: app/tax/withholding_tax_manager.py
from typing import TYPE_CHECKING, Dict, Any
from app.models.business.payment import Payment # For type hint

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.tax_service import TaxCodeService

class WithholdingTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.tax_code_service: "TaxCodeService" = app_core.tax_code_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.logger = app_core.logger
        self.logger.info("WithholdingTaxManager initialized.")

    async def generate_s45_form_data(self, payment: Payment) -> Dict[str, Any]:
        """
        Generates a dictionary of data required for IRAS Form S45, based on a vendor payment.
        """
        self.logger.info(f"Generating S45 form data for Payment ID {payment.id}")
        
        if not payment or not payment.vendor:
            self.logger.error(f"Cannot generate S45 data: Payment {payment.id} or its vendor is not loaded.")
            return {}

        # The amount subject to WHT is the gross amount of the invoice(s) paid, not the net cash outflow.
        # This manager needs the gross amount before WHT was deducted. The `payment.amount` is the gross.
        gross_payment_amount = payment.amount
        
        # A full implementation would need to determine the WHT rate from the payment or related invoices/vendor.
        # For now, this is a conceptual data structure.
        vendor = payment.vendor
        wht_rate = vendor.withholding_tax_rate if vendor.withholding_tax_applicable else None
        
        if wht_rate is None:
             self.logger.warning(f"Vendor '{vendor.name}' has no WHT rate specified for Payment ID {payment.id}.")
             wht_amount = 0
        else:
             wht_amount = (gross_payment_amount * wht_rate) / 100

        # Assuming payee details come from the Vendor record
        payee_details = {
            "name": vendor.name,
            "address": f"{vendor.address_line1 or ''}, {vendor.address_line2 or ''}".strip(", "),
            "tax_ref_no": vendor.uen_no or "N/A", # UEN as tax reference
        }

        # Payer details would come from Company Settings
        company_settings = await self.app_core.company_settings_service.get_company_settings()
        payer_details = {
            "name": company_settings.company_name if company_settings else "N/A",
            "tax_ref_no": company_settings.uen_no if company_settings else "N/A",
        }

        form_data = {
            "s45_payee_name": payee_details["name"],
            "s45_payee_address": payee_details["address"],
            "s45_payee_tax_ref": payee_details["tax_ref_no"],
            "s45_payer_name": payer_details["name"],
            "s45_payer_tax_ref": payer_details["tax_ref_no"],
            "s45_payment_date": payment.payment_date,
            "s45_nature_of_payment": "Director's Remuneration or Fees", # This needs to be determined based on context
            "s45_gross_payment": gross_payment_amount,
            "s45_wht_rate_percent": wht_rate,
            "s45_wht_amount": wht_amount,
        }
        self.logger.info(f"S45 data generated for Payment ID {payment.id}: {form_data}")
        return form_data

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str):
        """
        This method would be responsible for creating the journal entry when the withheld tax
        is actually paid to IRAS. This is a separate process from the initial payment to the vendor.
        """
        self.logger.info(f"Recording WHT payment for certificate {certificate_id} (stub).")
        # Logic would involve:
        # 1. Fetching the WHT certificate/liability record.
        # 2. Creating a JE: Dr WHT Payable, Cr Bank.
        # 3. Posting the JE.
        # 4. Updating the certificate status to 'Paid'.
        return True

```

# app/ui/company/__init__.py
```py
# File: app/ui/company/__init__.py
from .company_manager_dialog import CompanyManagerDialog
from .new_company_dialog import NewCompanyDialog

__all__ = [
    "CompanyManagerDialog",
    "NewCompanyDialog",
]

```

# app/ui/company/new_company_dialog.py
```py
# File: app/ui/company/new_company_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QPushButton, QDialogButtonBox, QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot
from typing import Optional, Dict
import re

class NewCompanyDialog(QDialog):
    def __init__(self, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Company File")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._company_details: Optional[Dict[str, str]] = None
        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.company_name_edit = QLineEdit()
        self.company_name_edit.setPlaceholderText("e.g., My Awesome Bakery Pte. Ltd.")
        form_layout.addRow("Company Display Name*:", self.company_name_edit)

        self.db_name_edit = QLineEdit()
        self.db_name_edit.setPlaceholderText("e.g., my_awesome_bakery")
        form_layout.addRow("Database Name*:", self.db_name_edit)

        hint_label = QLabel("Database name must be lowercase, with no spaces or special characters (underscores are allowed).")
        hint_label.setWordWrap(True)
        form_layout.addRow("", hint_label)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self._on_accept)
        self.button_box.rejected.connect(self.reject)
        self.company_name_edit.textChanged.connect(self._auto_populate_db_name)

    @Slot(str)
    def _auto_populate_db_name(self, text: str):
        # Sanitize company name to suggest a valid DB name
        db_name_suggestion = text.lower()
        db_name_suggestion = re.sub(r'[^a-z0-9_]+', '_', db_name_suggestion) # Replace invalid chars with underscore
        db_name_suggestion = re.sub(r'__+', '_', db_name_suggestion) # Collapse multiple underscores
        db_name_suggestion = db_name_suggestion.strip('_') # Remove leading/trailing underscores
        self.db_name_edit.setText("sgb_" + db_name_suggestion[:40]) # Add prefix and limit length

    def _validate_input(self) -> bool:
        company_name = self.company_name_edit.text().strip()
        db_name = self.db_name_edit.text().strip()
        
        if not company_name:
            QMessageBox.warning(self, "Input Error", "Company Display Name cannot be empty.")
            return False
            
        if not db_name:
            QMessageBox.warning(self, "Input Error", "Database Name cannot be empty.")
            return False
            
        # PostgreSQL identifier rules (simplified): starts with letter or underscore,
        # subsequent can be letters, digits, or underscores.
        if not re.match(r'^[a-z_][a-z0-9_]*$', db_name):
            QMessageBox.warning(self, "Invalid Database Name", 
                "Database name must start with a lowercase letter or underscore, "
                "and contain only lowercase letters, numbers, and underscores.")
            return False
        
        return True

    @Slot()
    def _on_accept(self):
        if self._validate_input():
            self._company_details = {
                "display_name": self.company_name_edit.text().strip(),
                "database_name": self.db_name_edit.text().strip()
            }
            self.accept()

    def get_company_details(self) -> Optional[Dict[str, str]]:
        return self._company_details

```

# app/ui/company/company_manager_dialog.py
```py
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

```

# app/ui/dashboard/__init__.py
```py
# File: app/ui/dashboard/__init__.py
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]

```

# app/ui/dashboard/dashboard_widget.py
```py
# File: app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox,
    QScrollArea, QFrame, QFormLayout
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon
from typing import Optional, TYPE_CHECKING, List, Dict 
from decimal import Decimal, InvalidOperation 

import json 

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    # from PySide6.QtGui import QPaintDevice # QPaintDevice not directly used, can be removed

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass

        self._init_ui()
        self.app_core.logger.info("DashboardWidget: Scheduling initial KPI load.")
        QTimer.singleShot(0, self._request_kpi_load)

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        refresh_button_layout = QHBoxLayout()
        self.refresh_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh KPIs")
        self.refresh_button.clicked.connect(self._request_kpi_load)
        refresh_button_layout.addStretch()
        refresh_button_layout.addWidget(self.refresh_button)
        self.main_layout.addLayout(refresh_button_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.main_layout.addWidget(scroll_area)

        container_widget = QWidget()
        scroll_area.setWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        kpi_group = QGroupBox("Key Performance Indicators")
        container_layout.addWidget(kpi_group)
        
        self.kpi_layout = QGridLayout(kpi_group) 
        self.kpi_layout.setSpacing(10)
        self.kpi_layout.setColumnStretch(1, 1) 
        self.kpi_layout.setColumnStretch(3, 1) 
        self.kpi_layout.setColumnMinimumWidth(0, 200) 
        self.kpi_layout.setColumnMinimumWidth(2, 200) 


        def add_kpi_row(layout: QGridLayout, row: int, col_offset: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...")
            value_label.setFont(QFont(self.font().family(), 11)) 
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, col_offset)
            layout.addWidget(value_label, row, col_offset + 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter) 

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        self.kpi_layout.addWidget(self.base_currency_label, current_row, 2, 1, 2, Qt.AlignmentFlag.AlignCenter) 
        current_row += 1
        
        self.revenue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Revenue (YTD):")
        self.cash_balance_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Cash Balance:")
        current_row += 1
        self.expenses_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Expenses (YTD):")
        self.current_ratio_label = add_kpi_row(self.kpi_layout, current_row, 2, "Current Ratio:") 
        current_row += 1
        self.net_profit_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Net Profit / (Loss) (YTD):")
        current_row += 1 

        self.kpi_layout.addWidget(QLabel("---"), current_row, 0, 1, 4) 
        current_row += 1
        self.ar_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total Outstanding AR:")
        self.ap_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total Outstanding AP:")
        current_row += 1
        self.ar_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 0, "Total AR Overdue:")
        self.ap_overdue_value_label = add_kpi_row(self.kpi_layout, current_row, 2, "Total AP Overdue:")
        current_row += 1
        
        ar_aging_group = QGroupBox("AR Aging Summary")
        ar_aging_layout = QFormLayout(ar_aging_group) 
        ar_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ar_aging_current_label = QLabel("Loading..."); ar_aging_layout.addRow("Current (Not Overdue):", self.ar_aging_current_label)
        self.ar_aging_1_30_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (1-30 days):", self.ar_aging_1_30_label)
        self.ar_aging_31_60_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (31-60 days):", self.ar_aging_31_60_label)
        self.ar_aging_61_90_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (61-90 days):", self.ar_aging_61_90_label)
        self.ar_aging_91_plus_label = QLabel("Loading..."); ar_aging_layout.addRow("Overdue (91+ days):", self.ar_aging_91_plus_label)
        self.kpi_layout.addWidget(ar_aging_group, current_row, 0, 1, 2) 

        ap_aging_group = QGroupBox("AP Aging Summary")
        ap_aging_layout = QFormLayout(ap_aging_group) 
        ap_aging_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self.ap_aging_current_label = QLabel("Loading..."); ap_aging_layout.addRow("Current (Not Overdue):", self.ap_aging_current_label)
        self.ap_aging_1_30_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (1-30 days):", self.ap_aging_1_30_label)
        self.ap_aging_31_60_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (31-60 days):", self.ap_aging_31_60_label)
        self.ap_aging_61_90_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (61-90 days):", self.ap_aging_61_90_label)
        self.ap_aging_91_plus_label = QLabel("Loading..."); ap_aging_layout.addRow("Overdue (91+ days):", self.ap_aging_91_plus_label)
        self.kpi_layout.addWidget(ap_aging_group, current_row, 2, 1, 2) 
        
        container_layout.addStretch() 


    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        try:
            if not isinstance(value, Decimal) : value = Decimal(str(value))
            if not value.is_finite(): return "N/A (Infinite)" 
            return f"{prefix}{value:,.2f}"
        except (TypeError, InvalidOperation): 
            return f"{prefix}Error"


    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
            self.ar_overdue_value_label, self.ap_overdue_value_label,
            self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
            self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
            self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label, 
            self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
            self.current_ratio_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'): 
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label to 'Loading...'")
            label.setText("Loading...")
        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        future = schedule_task_from_qt(self._fetch_kpis_data())
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        else:
            self.app_core.logger.error("DashboardWidget: Failed to schedule _fetch_kpis_data task.")
            self.refresh_button.setEnabled(True) 

    async def _fetch_kpis_data(self):
        self.app_core.logger.info("DashboardWidget: _fetch_kpis_data started.")
        kpi_data_result: Optional[DashboardKPIData] = None 
        json_payload: Optional[str] = None
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis()
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                    json_payload = kpi_data_result.model_dump_json()
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with payload: {'JSON string' if json_payload else 'None'}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", 
                                 Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, json_payload if json_payload is not None else ""))

    @Slot(str)
    def _update_kpi_display_slot(self, kpi_data_json_str: str):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received JSON string length: {len(kpi_data_json_str)}")
        self.refresh_button.setEnabled(True)
        
        kpi_data_dto: Optional[DashboardKPIData] = None
        if kpi_data_json_str:
            try:
                kpi_data_dto = DashboardKPIData.model_validate_json(kpi_data_json_str)
                self.app_core.logger.info(f"DashboardWidget: Successfully deserialized KPI JSON to DTO.")
            except Exception as e:
                self.app_core.logger.error(f"DashboardWidget: Error deserializing/validating KPI JSON: '{kpi_data_json_str[:100]}...' - Error: {e}", exc_info=True)
        
        if kpi_data_dto:
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.ar_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ar_overdue, bc_symbol)) 
            self.ap_overdue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_ap_overdue, bc_symbol)) 

            # AR Aging
            self.ar_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_current, bc_symbol))
            self.ar_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_1_30, bc_symbol)) 
            self.ar_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_31_60, bc_symbol))
            self.ar_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_61_90, bc_symbol))
            self.ar_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ar_aging_91_plus, bc_symbol))

            # AP Aging
            self.ap_aging_current_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_current, bc_symbol))
            self.ap_aging_1_30_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_1_30, bc_symbol)) 
            self.ap_aging_31_60_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_31_60, bc_symbol))
            self.ap_aging_61_90_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_61_90, bc_symbol))
            self.ap_aging_91_plus_label.setText(self._format_decimal_for_display(kpi_data_dto.ap_aging_91_plus, bc_symbol))
            
            # Current Ratio
            if kpi_data_dto.current_ratio is None:
                self.current_ratio_label.setText("N/A")
            elif not kpi_data_dto.current_ratio.is_finite(): 
                self.current_ratio_label.setText("N/A (Infinite)")
            else:
                self.current_ratio_label.setText(f"{kpi_data_dto.current_ratio:.2f} : 1")

            self.app_core.logger.info("DashboardWidget: UI labels updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with no valid DTO. Setting error text.")
            error_text = "N/A - Data unavailable"
            for label in [self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
                          self.cash_balance_value_label, self.ar_value_label, self.ap_value_label,
                          self.ar_overdue_value_label, self.ap_overdue_value_label,
                          self.ar_aging_current_label, self.ar_aging_1_30_label, self.ar_aging_31_60_label, 
                          self.ar_aging_61_90_label, self.ar_aging_91_plus_label,
                          self.ap_aging_current_label, self.ap_aging_1_30_label, self.ap_aging_31_60_label,
                          self.ap_aging_61_90_label, self.ap_aging_91_plus_label,
                          self.current_ratio_label]:
                label.setText(error_text)
            if kpi_data_json_str: 
                 QMessageBox.warning(self, "Dashboard Data Error", "Could not process Key Performance Indicators data.")

```

# app/ui/main_window.py
```py
# File: app/ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QToolBar, QStatusBar, 
    QVBoxLayout, QWidget, QMessageBox, QLabel, QProgressDialog
)
from PySide6.QtGui import QIcon, QKeySequence, QAction 
from PySide6.QtCore import Qt, QSettings, Signal, Slot, QCoreApplication, QSize, QProcess, QTimer

from app.ui.dashboard.dashboard_widget import DashboardWidget
from app.ui.accounting.accounting_widget import AccountingWidget
from app.ui.sales_invoices.sales_invoices_widget import SalesInvoicesWidget
from app.ui.purchase_invoices.purchase_invoices_widget import PurchaseInvoicesWidget
from app.ui.payments.payments_widget import PaymentsWidget 
from app.ui.customers.customers_widget import CustomersWidget
from app.ui.vendors.vendors_widget import VendorsWidget
from app.ui.products.products_widget import ProductsWidget
from app.ui.banking.banking_widget import BankingWidget
from app.ui.banking.bank_reconciliation_widget import BankReconciliationWidget 
from app.ui.reports.reports_widget import ReportsWidget
from app.ui.settings.settings_widget import SettingsWidget
from app.core.application_core import ApplicationCore
from app.ui.company.company_manager_dialog import CompanyManagerDialog
from app.ui.company.new_company_dialog import NewCompanyDialog
from app.scripts.db_init import initialize_new_database, DBInitArgs
from app.main import schedule_task_from_qt
import sys
import asyncio

class MainWindow(QMainWindow):
    def __init__(self, app_core: ApplicationCore):
        super().__init__()
        self.app_core = app_core
        
        db_name = self.app_core.db_manager.config.database
        company_info = self.app_core.company_manager.get_company_by_db_name(db_name)
        company_display_name = company_info.get("display_name") if company_info else db_name

        self.setWindowTitle(f"{QCoreApplication.applicationName()} - {company_display_name}")
        self.setMinimumSize(1280, 800)
        
        self.icon_path_prefix = "resources/icons/" 
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass

        settings = QSettings(); 
        if settings.contains("MainWindow/geometry"): self.restoreGeometry(settings.value("MainWindow/geometry")) 
        else: self.resize(1366, 768)
        
        self._init_ui()
        if settings.contains("MainWindow/state"): self.restoreState(settings.value("MainWindow/state")) 
    
    def _init_ui(self):
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        self._create_toolbar(); self.tab_widget = QTabWidget(); self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setDocumentMode(True); self.tab_widget.setMovable(True)
        self.main_layout.addWidget(self.tab_widget); self._add_module_tabs()
        self._create_status_bar(); self._create_actions(); self._create_menus()
    
    def _create_toolbar(self):
        self.toolbar = QToolBar("Main Toolbar"); self.toolbar.setObjectName("MainToolbar") 
        self.toolbar.setMovable(False); self.toolbar.setIconSize(QSize(24, 24)) 
        self.toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar) 
    
    def _add_module_tabs(self):
        self.dashboard_widget = DashboardWidget(self.app_core); self.tab_widget.addTab(self.dashboard_widget, QIcon(self.icon_path_prefix + "dashboard.svg"), "Dashboard")
        self.accounting_widget = AccountingWidget(self.app_core); self.tab_widget.addTab(self.accounting_widget, QIcon(self.icon_path_prefix + "accounting.svg"), "Accounting")
        self.sales_invoices_widget = SalesInvoicesWidget(self.app_core); self.tab_widget.addTab(self.sales_invoices_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Sales") 
        self.purchase_invoices_widget = PurchaseInvoicesWidget(self.app_core); self.tab_widget.addTab(self.purchase_invoices_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Purchases") 
        self.payments_widget = PaymentsWidget(self.app_core); self.tab_widget.addTab(self.payments_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Payments") 
        self.customers_widget = CustomersWidget(self.app_core); self.tab_widget.addTab(self.customers_widget, QIcon(self.icon_path_prefix + "customers.svg"), "Customers")
        self.vendors_widget = VendorsWidget(self.app_core); self.tab_widget.addTab(self.vendors_widget, QIcon(self.icon_path_prefix + "vendors.svg"), "Vendors")
        self.products_widget = ProductsWidget(self.app_core); self.tab_widget.addTab(self.products_widget, QIcon(self.icon_path_prefix + "product.svg"), "Products & Services")
        self.banking_widget = BankingWidget(self.app_core); self.tab_widget.addTab(self.banking_widget, QIcon(self.icon_path_prefix + "banking.svg"), "Banking (Transactions)") 
        self.bank_reconciliation_widget = BankReconciliationWidget(self.app_core); self.tab_widget.addTab(self.bank_reconciliation_widget, QIcon(self.icon_path_prefix + "transactions.svg"), "Bank Reconciliation") 
        self.reports_widget = ReportsWidget(self.app_core); self.tab_widget.addTab(self.reports_widget, QIcon(self.icon_path_prefix + "reports.svg"), "Reports")
        self.settings_widget = SettingsWidget(self.app_core); self.tab_widget.addTab(self.settings_widget, QIcon(self.icon_path_prefix + "settings.svg"), "Settings")
    
    def _create_status_bar(self):
        self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready"); self.status_bar.addWidget(self.status_label, 1) 
        user_text = "User: Guest"; 
        if self.app_core.current_user: user_text = f"User: {self.app_core.current_user.username}"
        self.user_label = QLabel(user_text); self.status_bar.addPermanentWidget(self.user_label)
        self.version_label = QLabel(f"Version: {QCoreApplication.applicationVersion()}"); self.status_bar.addPermanentWidget(self.version_label)

    def _create_actions(self):
        self.new_company_action = QAction(QIcon(self.icon_path_prefix + "new_company.svg"), "New Company...", self); self.new_company_action.triggered.connect(self.on_new_company)
        self.open_company_action = QAction(QIcon(self.icon_path_prefix + "open_company.svg"), "Open Company...", self); self.open_company_action.triggered.connect(self.on_open_company)
        self.backup_action = QAction(QIcon(self.icon_path_prefix + "backup.svg"), "Backup Data...", self); self.backup_action.triggered.connect(self.on_backup)
        self.restore_action = QAction(QIcon(self.icon_path_prefix + "restore.svg"), "Restore Data...", self); self.restore_action.triggered.connect(self.on_restore)
        self.exit_action = QAction(QIcon(self.icon_path_prefix + "exit.svg"), "Exit", self); self.exit_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Quit)); self.exit_action.triggered.connect(self.close) 
        self.preferences_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Preferences...", self); self.preferences_action.setShortcut(QKeySequence(QKeySequence.StandardKey.Preferences)); self.preferences_action.triggered.connect(self.on_preferences)
        self.help_contents_action = QAction(QIcon(self.icon_path_prefix + "help.svg"), "Help Contents", self); self.help_contents_action.setShortcut(QKeySequence(QKeySequence.StandardKey.HelpContents)); self.help_contents_action.triggered.connect(self.on_help_contents)
        self.about_action = QAction(QIcon(self.icon_path_prefix + "about.svg"), "About " + QCoreApplication.applicationName(), self); self.about_action.triggered.connect(self.on_about)

    def _create_menus(self):
        self.file_menu = self.menuBar().addMenu("&File"); self.file_menu.addAction(self.new_company_action); self.file_menu.addAction(self.open_company_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.backup_action); self.file_menu.addAction(self.restore_action); self.file_menu.addSeparator(); self.file_menu.addAction(self.exit_action)
        self.edit_menu = self.menuBar().addMenu("&Edit"); self.edit_menu.addAction(self.preferences_action)
        self.view_menu = self.menuBar().addMenu("&View"); self.tools_menu = self.menuBar().addMenu("&Tools")
        self.help_menu = self.menuBar().addMenu("&Help"); self.help_menu.addAction(self.help_contents_action); self.help_menu.addSeparator(); self.help_menu.addAction(self.about_action)
        self.toolbar.addAction(self.new_company_action); self.toolbar.addAction(self.open_company_action); self.toolbar.addSeparator(); self.toolbar.addAction(self.backup_action); self.toolbar.addAction(self.preferences_action)
    
    @Slot()
    def on_new_company(self): self._open_company_manager(request_new=True)
    @Slot()
    def on_open_company(self): self._open_company_manager()
    
    def _open_company_manager(self, request_new=False):
        dialog = CompanyManagerDialog(self.app_core, self)
        result = dialog.exec()
        if request_new: result = CompanyManagerDialog.NewCompanyRequest # Force new company dialog

        if result == CompanyManagerDialog.NewCompanyRequest:
            new_company_dialog = NewCompanyDialog(self)
            if new_company_dialog.exec():
                new_company_details = new_company_dialog.get_company_details()
                if new_company_details: self._create_new_company_db(new_company_details)
        elif result == CompanyManagerDialog.OpenCompanyRequest:
            selected_info = dialog.get_selected_company_info()
            if selected_info: self.switch_company_database(selected_info['database_name'])
    
    def _create_new_company_db(self, company_details: Dict[str, str]):
        progress = QProgressDialog("Creating new company database...", "Cancel", 0, 0, self)
        progress.setWindowModality(Qt.WindowModality.WindowModal); progress.setCancelButton(None)
        progress.show(); QApplication.processEvents()

        admin_user = self.app_core.config_manager.config.username
        admin_pass = self.app_core.config_manager.config.password
        db_args = DBInitArgs(user=admin_user, password=admin_pass, host=self.app_core.config_manager.config.host, port=self.app_core.config_manager.config.port, dbname=company_details['database_name'], drop_existing=False)
        future = schedule_task_from_qt(initialize_new_database(db_args))
        if future: future.add_done_callback(lambda res: self._handle_db_creation_result(res, company_details))
        else: QMessageBox.critical(self, "Error", "Failed to schedule database creation task."); progress.close()

    def _handle_db_creation_result(self, future, company_details: Dict[str, str]):
        progress = self.findChild(QProgressDialog)
        if progress: progress.close()
        try:
            success = future.result()
            if success:
                self.app_core.company_manager.add_company(company_details)
                QMessageBox.information(self, "Success", f"Company '{company_details['display_name']}' created successfully.\nThe application will now restart to open it.")
                self.switch_company_database(company_details['database_name'])
            else: QMessageBox.critical(self, "Database Creation Failed", "Could not create the new company database. Please check the logs.")
        except Exception as e: QMessageBox.critical(self, "Error", f"An unexpected error occurred during database creation: {e}")

    def switch_company_database(self, db_name: str):
        self.app_core.config_manager.set_setting("Database", "database", db_name)
        QTimer.singleShot(100, self._restart_application) # Delay restart slightly

    def _restart_application(self):
        QCoreApplication.instance().quit() # type: ignore
        QProcess.startDetached(sys.executable, sys.argv)
    
    @Slot()
    def on_backup(self): QMessageBox.information(self, "Backup Data", "Backup functionality not yet implemented.")
    @Slot()
    def on_restore(self): QMessageBox.information(self, "Restore Data", "Restore functionality not yet implemented.")
    @Slot()
    def on_preferences(self): 
        settings_tab_index = -1;
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == self.settings_widget: settings_tab_index = i; break
        if settings_tab_index != -1: self.tab_widget.setCurrentIndex(settings_tab_index)
        else: QMessageBox.information(self, "Preferences", "Settings tab not found.")
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
# File: app/ui/reports/__init__.py
from .reports_widget import ReportsWidget
from .trial_balance_table_model import TrialBalanceTableModel
from .general_ledger_table_model import GeneralLedgerTableModel

__all__ = [
    "ReportsWidget",
    "TrialBalanceTableModel",
    "GeneralLedgerTableModel",
]

```

# app/ui/reports/general_ledger_table_model.py
```py
# File: app/ui/reports/general_ledger_table_model.py
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
        return len(self._transactions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal], show_blank_for_zero: bool = True) -> str:
        if value is None: return ""
        if show_blank_for_zero and value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row, col = index.row(), index.column()

        if not (0 <= row < len(self._transactions)): return None
            
        txn = self._transactions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                raw_date = txn.get("date")
                return raw_date.strftime('%d/%m/%Y') if isinstance(raw_date, python_date) else str(raw_date)
            if col == 1: return txn.get("entry_no", "")
            if col == 2: 
                desc = txn.get("je_description", "")
                line_desc = txn.get("line_description", "")
                return f"{desc} // {line_desc}" if desc and line_desc else (desc or line_desc)
            if col == 3: return self._format_decimal_for_display(txn.get("debit"), True)
            if col == 4: return self._format_decimal_for_display(txn.get("credit"), True)
            if col == 5: return self._format_decimal_for_display(txn.get("balance"), False)
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [3, 4, 5]:
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
# File: app/ui/reports/trial_balance_table_model.py
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
        return len(self._debit_accounts) + len(self._credit_accounts) + 1 

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_display(self, value: Optional[Decimal]) -> str:
        if value is None or value == Decimal(0): return ""
        return f"{value:,.2f}"

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid(): return None
        
        row, col = index.row(), index.column()
        num_debit_accounts = len(self._debit_accounts)
        num_credit_accounts = len(self._credit_accounts)

        if row == num_debit_accounts + num_credit_accounts: # Totals Row
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

        if row < num_debit_accounts: # Debit Accounts
            account = self._debit_accounts[row]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return self._format_decimal_for_display(account.get("balance"))
                if col == 3: return ""
            elif role == Qt.ItemDataRole.TextAlignmentRole and col == 2:
                 return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return None
        
        credit_row_index = row - num_debit_accounts # Credit Accounts
        if credit_row_index < num_credit_accounts:
            account = self._credit_accounts[credit_row_index]
            if role == Qt.ItemDataRole.DisplayRole:
                if col == 0: return account.get("code", "")
                if col == 1: return account.get("name", "")
                if col == 2: return ""
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

# app/ui/accounting/account_dialog.py
```py
# File: app/ui/accounting/account_dialog.py
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
        
        self.cash_flow_category_combo = QComboBox() # NEW
        self.cash_flow_category_combo.addItems(["(None)", "Operating", "Investing", "Financing"])

        self.gst_applicable_check = QCheckBox()
        self.tax_treatment_edit = QLineEdit() 
        self.is_active_check = QCheckBox("Is Active")
        self.is_active_check.setChecked(True)
        self.is_control_account_check = QCheckBox("Is Control Account")
        self.is_bank_account_check = QCheckBox("Is Bank Account")
        
        self.form_layout.addRow("Code*:", self.code_edit)
        self.form_layout.addRow("Name*:", self.name_edit)
        self.form_layout.addRow("Account Type*:", self.account_type_combo)
        self.form_layout.addRow("Sub Type:", self.sub_type_edit)
        self.form_layout.addRow("Parent Account ID:", self.parent_id_spin) 
        self.form_layout.addRow("Description:", self.description_edit)
        self.form_layout.addRow("Opening Balance:", self.opening_balance_edit)
        self.form_layout.addRow("OB Date:", self.opening_balance_date_edit)
        self.form_layout.addRow("Report Group:", self.report_group_edit)
        self.form_layout.addRow("Cash Flow Category:", self.cash_flow_category_combo) # NEW
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
        if not (manager and hasattr(manager, 'account_service')): 
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
            if self.account.cash_flow_category:
                self.cash_flow_category_combo.setCurrentText(self.account.cash_flow_category)
            else:
                self.cash_flow_category_combo.setCurrentIndex(0) # (None)
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
        
        cash_flow_category_text = self.cash_flow_category_combo.currentText()
        cash_flow_category = cash_flow_category_text if cash_flow_category_text != "(None)" else None

        common_data = {
            "code": self.code_edit.text(), "name": self.name_edit.text(),
            "account_type": self.account_type_combo.currentText(), "sub_type": self.sub_type_edit.text() or None,
            "description": self.description_edit.text() or None, "parent_id": parent_id,
            "opening_balance": ob_decimal, "opening_balance_date": self.opening_balance_date_edit.date().toPython() if self.opening_balance_date_edit.isEnabled() else None,
            "report_group": self.report_group_edit.text() or None, "cash_flow_category": cash_flow_category,
            "gst_applicable": self.gst_applicable_check.isChecked(), "tax_treatment": self.tax_treatment_edit.text() or None,
            "is_active": self.is_active_check.isChecked(), "is_control_account": self.is_control_account_check.isChecked(),
            "is_bank_account": self.is_bank_account_check.isChecked(), "user_id": self.current_user_id
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

# app/core/company_manager.py
```py
# File: app/core/company_manager.py
import json
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING
import os
import sys

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

class CompanyManager:
    """Manages the central registry of company database files."""
    def __init__(self, app_core: "ApplicationCore"):
        self.app_core = app_core
        if os.name == 'nt':
            config_dir = Path(os.getenv('APPDATA', Path.home() / 'AppData' / 'Roaming')) / "SGBookkeeper"
        elif sys.platform == 'darwin':
            config_dir = Path.home() / 'Library' / 'Application Support' / "SGBookkeeper"
        else:
            config_dir = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / '.config')) / "SGBookkeeper"
        
        os.makedirs(config_dir, exist_ok=True)
        self.registry_file = config_dir / "companies.json"
        
        self._companies: List[Dict[str, str]] = self._load_registry()

    def _load_registry(self) -> List[Dict[str, str]]:
        if not self.registry_file.exists():
            return []
        try:
            with open(self.registry_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                return []
        except (json.JSONDecodeError, IOError):
            return []

    def _save_registry(self):
        try:
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(self._companies, f, indent=2)
        except IOError as e:
            self.app_core.logger.error(f"Failed to save company registry to {self.registry_file}: {e}")
            # In a real UI app, we'd show an error dialog here.
            # For now, logging is sufficient.

    def get_company_list(self) -> List[Dict[str, str]]:
        """Returns a copy of the company list."""
        return list(self._companies)

    def add_company(self, company_info: Dict[str, str]):
        """Adds a new company to the registry if it doesn't already exist."""
        if not all(k in company_info for k in ['display_name', 'database_name']):
            raise ValueError("Company info must contain 'display_name' and 'database_name'.")
        
        # Check for duplicates based on database_name
        if any(c['database_name'] == company_info['database_name'] for c in self._companies):
            self.app_core.logger.warning(f"Attempted to add duplicate company database '{company_info['database_name']}'. Ignoring.")
            return

        self._companies.append(company_info)
        self._save_registry()

    def remove_company(self, company_info: Dict[str, str]):
        """Removes a company from the registry based on its database_name."""
        db_name_to_remove = company_info.get("database_name")
        if not db_name_to_remove:
            return

        original_count = len(self._companies)
        self._companies = [c for c in self._companies if c.get("database_name") != db_name_to_remove]
        
        if len(self._companies) < original_count:
            self._save_registry()
            
    def get_company_by_db_name(self, db_name: str) -> Optional[Dict[str, str]]:
        """Finds a company by its database name."""
        return next((c for c in self._companies if c.get("database_name") == db_name), None)

```

# app/models/business/vendor.py
```py
# File: app/models/business/vendor.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from decimal import Decimal
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.models.core.user import User

if TYPE_CHECKING:
    from app.models.business.purchase_invoice import PurchaseInvoice
    from app.models.accounting.withholding_tax_certificate import WithholdingTaxCertificate

class Vendor(Base, TimestampMixin):
    __tablename__ = 'vendors'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    vendor_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    withholding_tax_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    withholding_tax_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5,2), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    payment_terms: Mapped[int] = mapped_column(Integer, default=30) 
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    vendor_since: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_account_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True) 
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payables_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by",Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by",Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code])
    payables_account: Mapped[Optional["Account"]] = relationship("Account", back_populates="vendor_payables_links", foreign_keys=[payables_account_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    purchase_invoices: Mapped[List["PurchaseInvoice"]] = relationship("PurchaseInvoice", back_populates="vendor")
    wht_certificates: Mapped[List["WithholdingTaxCertificate"]] = relationship("WithholdingTaxCertificate", back_populates="vendor")

```

# app/models/business/purchase_invoice.py
```py
# File: app/models/business/purchase_invoice.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional, TYPE_CHECKING
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.currency import Currency
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension

if TYPE_CHECKING:
    from app.models.business.vendor import Vendor

class PurchaseInvoice(Base, TimestampMixin):
    __tablename__ = 'purchase_invoices'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Approved', 'Partially Paid', 'Paid', 'Overdue', 'Disputed', 'Voided')", name='ck_purchase_invoices_status'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.vendors.id'), nullable=False)
    vendor_invoice_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    invoice_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15,6), default=Decimal(1))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_invoices")
    currency: Mapped["Currency"] = relationship("Currency")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry")
    lines: Mapped[List["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class PurchaseInvoiceLine(Base, TimestampMixin):
    __tablename__ = 'purchase_invoice_lines'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.purchase_invoices.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.products.id'), nullable=True)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(Numeric(5,2), default=Decimal(0))
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    line_subtotal: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    line_total: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)

    invoice: Mapped["PurchaseInvoice"] = relationship("PurchaseInvoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="purchase_invoice_lines")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])

```

# app/models/accounting/__init__.py
```py
# File: app/models/accounting/__init__.py
from .account_type import AccountType
from .currency import Currency
from .exchange_rate import ExchangeRate
from .account import Account
from .fiscal_year import FiscalYear
from .fiscal_period import FiscalPeriod
from .journal_entry import JournalEntry, JournalEntryLine
from .recurring_pattern import RecurringPattern
from .dimension import Dimension
from .budget import Budget, BudgetDetail
from .tax_code import TaxCode
from .gst_return import GSTReturn
from .withholding_tax_certificate import WithholdingTaxCertificate

__all__ = [
    "AccountType", "Currency", "ExchangeRate", "Account",
    "FiscalYear", "FiscalPeriod", "JournalEntry", "JournalEntryLine",
    "RecurringPattern", "Dimension", "Budget", "BudgetDetail",
    "TaxCode", "GSTReturn", "WithholdingTaxCertificate",
]

```

# app/models/accounting/withholding_tax_certificate.py
```py
# File: app/models/accounting/withholding_tax_certificate.py
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin
from app.models.business.vendor import Vendor 
from app.models.core.user import User
import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.accounting.journal_entry import JournalEntry

class WithholdingTaxCertificate(Base, TimestampMixin):
    __tablename__ = 'withholding_tax_certificates'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Issued', 'Voided')", name='ck_wht_certs_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    certificate_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.vendors.id'), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(50), nullable=False) 
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    amount_before_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False)
    issue_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    vendor: Mapped["Vendor"] = relationship(back_populates="wht_certificates")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship()
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

Vendor.wht_certificates = relationship("WithholdingTaxCertificate", back_populates="vendor") # type: ignore

```

# app/models/accounting/account.py
```py
# File: app/models/accounting/account.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, Optional 
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin 
from app.models.core.user import User 

class Account(Base, TimestampMixin):
    __tablename__ = 'accounts'
    __table_args__ = (
         CheckConstraint("account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_accounts_account_type_category'),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    sub_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    tax_treatment: Mapped[Optional[str]] = mapped_column(String(20), nullable=True) 
    gst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    
    report_group: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cash_flow_category: Mapped[Optional[str]] = mapped_column(String(20), CheckConstraint("cash_flow_category IN ('Operating', 'Investing', 'Financing')"), nullable=True)
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bank_account: Mapped[bool] = mapped_column(Boolean, default=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    opening_balance_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
        
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    journal_lines: Mapped[List["JournalEntryLine"]] = relationship(back_populates="account") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="account") # type: ignore
    tax_code_applications: Mapped[List["TaxCode"]] = relationship(back_populates="affects_account") # type: ignore
    customer_receivables_links: Mapped[List["Customer"]] = relationship(back_populates="receivables_account") # type: ignore
    vendor_payables_links: Mapped[List["Vendor"]] = relationship(back_populates="payables_account") # type: ignore
    product_sales_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.sales_account_id", back_populates="sales_account") # type: ignore
    product_purchase_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.purchase_account_id", back_populates="purchase_account") # type: ignore
    product_inventory_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.inventory_account_id", back_populates="inventory_account") # type: ignore
    bank_account_links: Mapped[List["BankAccount"]] = relationship(back_populates="gl_account") # type: ignore

    def to_dict(self):
        return {
            'id': self.id, 'code': self.code, 'name': self.name, 'account_type': self.account_type,
            'sub_type': self.sub_type, 'parent_id': self.parent_id, 'is_active': self.is_active,
            'description': self.description, 'report_group': self.report_group,
            'is_control_account': self.is_control_account, 'is_bank_account': self.is_bank_account,
            'opening_balance': self.opening_balance, 'opening_balance_date': self.opening_balance_date,
            'cash_flow_category': self.cash_flow_category
        }

```

# app/models/accounting/tax_code.py
```py
# File: app/models/accounting/tax_code.py
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.core.user import User

class TaxCode(Base, TimestampMixin):
    __tablename__ = 'tax_codes'
    __table_args__ = (
        CheckConstraint("tax_type IN ('GST', 'Income Tax', 'Withholding Tax')", name='ck_tax_codes_tax_type'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(100), nullable=False)
    tax_type: Mapped[str] = mapped_column(String(20), nullable=False)
    rate: Mapped[Decimal] = mapped_column(Numeric(5,2), nullable=False) 
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    affects_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    affects_account: Mapped[Optional["Account"]] = relationship("Account", back_populates="tax_code_applications", foreign_keys=[affects_account_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

Account.tax_code_applications = relationship("TaxCode", back_populates="affects_account", foreign_keys=[TaxCode.affects_account_id]) # type: ignore

```

# app/models/accounting/account_type.py
```py
# File: app/models/accounting/account_type.py
from sqlalchemy import Column, Integer, String, Boolean, CheckConstraint, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
from typing import Optional

class AccountType(Base, TimestampMixin): 
    __tablename__ = 'account_types'
    __table_args__ = (
        CheckConstraint("category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')", name='ck_account_types_category'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False) 
    is_debit_balance: Mapped[bool] = mapped_column(Boolean, nullable=False)
    report_type: Mapped[str] = mapped_column(String(30), nullable=False) 
    display_order: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

```

# app/accounting/chart_of_accounts_manager.py
```py
# File: app/accounting/chart_of_accounts_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
from app.utils.result import Result
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
from decimal import Decimal
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.account_service import AccountService

class ChartOfAccountsManager:
    def __init__(self, account_service: "AccountService", app_core: "ApplicationCore"): 
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 

    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        account = Account(
            code=account_data.code, name=account_data.name,
            account_type=account_data.account_type, sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment, gst_applicable=account_data.gst_applicable,
            description=account_data.description, parent_id=account_data.parent_id,
            report_group=account_data.report_group, cash_flow_category=account_data.cash_flow_category,
            is_control_account=account_data.is_control_account, is_bank_account=account_data.is_bank_account, 
            opening_balance=account_data.opening_balance, opening_balance_date=account_data.opening_balance_date, 
            is_active=account_data.is_active, created_by_user_id=current_user_id, 
            updated_by_user_id=current_user_id 
        )
        
        try:
            saved_account = await self.account_service.save(account)
            return Result.success(saved_account)
        except Exception as e:
            return Result.failure([f"Failed to save account: {str(e)}"])
    
    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        existing_account = await self.account_service.get_by_id(account_data.id)
        if not existing_account:
            return Result.failure([f"Account with ID {account_data.id} not found."])
        
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        if account_data.code != existing_account.code:
            code_exists = await self.account_service.get_by_code(account_data.code)
            if code_exists and code_exists.id != existing_account.id:
                return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        existing_account.code = account_data.code; existing_account.name = account_data.name
        existing_account.account_type = account_data.account_type; existing_account.sub_type = account_data.sub_type
        existing_account.tax_treatment = account_data.tax_treatment; existing_account.gst_applicable = account_data.gst_applicable
        existing_account.description = account_data.description; existing_account.parent_id = account_data.parent_id
        existing_account.report_group = account_data.report_group; existing_account.cash_flow_category = account_data.cash_flow_category
        existing_account.is_control_account = account_data.is_control_account; existing_account.is_bank_account = account_data.is_bank_account
        existing_account.opening_balance = account_data.opening_balance; existing_account.opening_balance_date = account_data.opening_balance_date 
        existing_account.is_active = account_data.is_active; existing_account.updated_by_user_id = current_user_id
        
        try:
            updated_account = await self.account_service.save(existing_account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to update account: {str(e)}"])
            
    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        account = await self.account_service.get_by_id(account_id)
        if not account: return Result.failure([f"Account with ID {account_id} not found."])
        if not account.is_active: return Result.failure([f"Account '{account.code}' is already inactive."])
        if not self.app_core or not hasattr(self.app_core, 'journal_service'): return Result.failure(["Journal service not available for balance check."])

        total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today()) 
        if total_current_balance != Decimal(0): return Result.failure([f"Cannot deactivate account '{account.code}' as it has a non-zero balance ({total_current_balance:.2f})."])

        account.is_active = False; account.updated_by_user_id = user_id 
        try:
            updated_account = await self.account_service.save(account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to deactivate account: {str(e)}"])

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            tree = await self.account_service.get_account_tree(active_only=active_only)
            return tree 
        except Exception as e:
            print(f"Error getting account tree: {e}") 
            return []

    async def get_accounts_for_selection(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Account]:
        if account_type:
            return await self.account_service.get_by_type(account_type, active_only=active_only)
        elif active_only:
            return await self.account_service.get_all_active()
        else:
            if hasattr(self.account_service, 'get_all'):
                 return await self.account_service.get_all()
            else: 
                 return await self.account_service.get_all_active()

```

# scripts/db_init.py
```py
# File: scripts/db_init.py
import asyncio
import asyncpg # type: ignore
import argparse
import getpass
import os
import sys
from pathlib import Path
from typing import NamedTuple, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMA_SQL_PATH = SCRIPT_DIR / 'schema.sql'
INITIAL_DATA_SQL_PATH = SCRIPT_DIR / 'initial_data.sql'

class DBInitArgs(NamedTuple):
    """A simple data class to hold arguments for programmatic calls."""
    user: Optional[str]
    password: Optional[str]
    host: str
    port: int
    dbname: str
    drop_existing: bool = False

async def initialize_new_database(args: DBInitArgs) -> bool:
    """Create PostgreSQL database and initialize schema using reference SQL files."""
    conn_admin = None 
    db_conn = None 
    
    # Use environment variables or provided args for admin connection
    admin_user = args.user or os.getenv('PGUSER', 'postgres')
    admin_password = args.password or os.getenv('PGPASSWORD')

    if not admin_password:
        print(f"Error: Admin password for user '{admin_user}' is required for database creation but was not provided.", file=sys.stderr)
        # In a real app, this would be handled more gracefully, maybe by re-prompting if interactive.
        # For programmatic use, failing fast is better.
        return False

    try:
        conn_params_admin = { 
            "user": admin_user,
            "password": admin_password,
            "host": args.host,
            "port": args.port,
        }
        conn_admin = await asyncpg.connect(**conn_params_admin, database='postgres') 
    except Exception as e:
        print(f"Error connecting to PostgreSQL server (postgres DB): {type(e).__name__} - {str(e)}", file=sys.stderr)
        return False
    
    try:
        exists = await conn_admin.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname = $1)",
            args.dbname
        )
        
        if exists:
            if args.drop_existing:
                print(f"Terminating connections to '{args.dbname}'...")
                await conn_admin.execute(f"""
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = '{args.dbname}' AND pid <> pg_backend_pid();
                """)
                print(f"Dropping existing database '{args.dbname}'...")
                await conn_admin.execute(f"DROP DATABASE IF EXISTS \"{args.dbname}\"") 
            else:
                print(f"Database '{args.dbname}' already exists. Use --drop-existing to recreate.")
                await conn_admin.close()
                return False 
        
        print(f"Creating database '{args.dbname}'...")
        await conn_admin.execute(f"CREATE DATABASE \"{args.dbname}\"") 
        
        await conn_admin.close() 
        conn_admin = None 
        
        # Connect to the newly created database to run schema and data scripts
        conn_params_db = {**conn_params_admin, "database": args.dbname}
        db_conn = await asyncpg.connect(**conn_params_db) 
        
        if not SCHEMA_SQL_PATH.exists():
            print(f"Error: schema.sql not found at {SCHEMA_SQL_PATH}", file=sys.stderr)
            return False
            
        print(f"Initializing database schema from {SCHEMA_SQL_PATH}...")
        with open(SCHEMA_SQL_PATH, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        await db_conn.execute(schema_sql)
        print("Schema execution completed.")
        
        if not INITIAL_DATA_SQL_PATH.exists():
            print(f"Warning: initial_data.sql not found at {INITIAL_DATA_SQL_PATH}. Skipping initial data.", file=sys.stderr)
        else:
            print(f"Loading initial data from {INITIAL_DATA_SQL_PATH}...")
            with open(INITIAL_DATA_SQL_PATH, 'r', encoding='utf-8') as f:
                data_sql = f.read()
            await db_conn.execute(data_sql)
            print("Initial data loading completed.")

        print(f"Setting default search_path for database '{args.dbname}'...")
        await db_conn.execute(f"""
            ALTER DATABASE "{args.dbname}" 
            SET search_path TO core, accounting, business, audit, public;
        """)
        print("Default search_path set.")
        
        print(f"Database '{args.dbname}' created and initialized successfully.")
        return True
    
    except Exception as e:
        print(f"Error during database creation/initialization: {type(e).__name__} - {str(e)}", file=sys.stderr)
        # Provide more detail for debugging asyncpg errors
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
            print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr)
        if hasattr(e, 'detail') and e.detail: # type: ignore
             print(f"  DETAIL: {e.detail}", file=sys.stderr)
        if hasattr(e, 'query') and e.query: # type: ignore
            print(f"  Query context: {e.query[:200]}...", file=sys.stderr)
        return False
    
    finally:
        if conn_admin and not conn_admin.is_closed():
            await conn_admin.close()
        if db_conn and not db_conn.is_closed():
            await db_conn.close()

def parse_args():
    parser = argparse.ArgumentParser(description='Initialize SG Bookkeeper database from reference SQL files.')
    parser.add_argument('--host', default=os.getenv('PGHOST', 'localhost'), help='PostgreSQL server host (Env: PGHOST)')
    parser.add_argument('--port', type=int, default=os.getenv('PGPORT', 5432), help='PostgreSQL server port (Env: PGPORT)')
    parser.add_argument('--user', default=os.getenv('PGUSER', 'postgres'), help='PostgreSQL admin/superuser (Env: PGUSER)')
    parser.add_argument('--password', help='PostgreSQL admin/superuser password (Env: PGPASSWORD, or prompts if empty)')
    parser.add_argument('--dbname', default=os.getenv('PGDATABASE', 'sg_bookkeeper'), help='Database name to create (Env: PGDATABASE)')
    parser.add_argument('--drop-existing', action='store_true', help='Drop database if it already exists')
    return parser.parse_args()

def main():
    args = parse_args()
    
    password = args.password
    if not password:
        pgpassword_env = os.getenv('PGPASSWORD')
        if pgpassword_env:
            password = pgpassword_env
        else:
            try:
                password = getpass.getpass(f"Password for PostgreSQL user '{args.user}' on host '{args.host}': ")
            except (EOFError, KeyboardInterrupt): 
                print("\nPassword prompt cancelled or non-interactive environment. Exiting.", file=sys.stderr)
                sys.exit(1)
            except Exception as e: 
                print(f"Could not read password securely: {e}. Try setting PGPASSWORD environment variable or using --password.", file=sys.stderr)
                sys.exit(1)
    
    init_args = DBInitArgs(
        user=args.user,
        password=password,
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        drop_existing=args.drop_existing
    )

    try:
        success = asyncio.run(initialize_new_database(init_args))
    except KeyboardInterrupt:
        print("\nDatabase initialization cancelled by user.", file=sys.stderr)
        sys.exit(1)
    except Exception as e: 
        print(f"An unexpected error occurred in main: {type(e).__name__} - {str(e)}", file=sys.stderr)
        if hasattr(e, 'sqlstate') and e.sqlstate: # type: ignore
             print(f"  SQLSTATE: {e.sqlstate}", file=sys.stderr) 
        success = False
        
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

```

# data/chart_of_accounts/general_template.csv
```csv
Code,Name,AccountType,SubType,TaxTreatment,GSTApplicable,CashFlowCategory,ParentCode,ReportGroup,IsControlAccount,IsBankAccount,OpeningBalance,OpeningBalanceDate
1000,ASSETS,Asset,,,,,,,,,,
1100,Current Assets,Asset,,,,1000,CURRENT_ASSETS,FALSE,FALSE,,
1110,Cash and Bank,Asset,"Cash and Cash Equivalents",,FALSE,Operating,1100,CASH_BANK,FALSE,TRUE,,
1111,Main Bank Account SGD,Asset,"Cash and Cash Equivalents",Non-Taxable,FALSE,Operating,1110,CASH_BANK,FALSE,TRUE,1000.00,2023-01-01
1112,Petty Cash,Asset,"Cash and Cash Equivalents",Non-Taxable,FALSE,Operating,1110,CASH_BANK,FALSE,FALSE,100.00,2023-01-01
1120,Accounts Receivable,Asset,"Accounts Receivable",,TRUE,Operating,1100,ACCOUNTS_RECEIVABLE,TRUE,FALSE,500.00,2023-01-01
1130,Inventory,Asset,Inventory,,TRUE,Operating,1100,INVENTORY,TRUE,FALSE,0.00,
1200,Non-Current Assets,Asset,,,,1000,NON_CURRENT_ASSETS,FALSE,FALSE,,
1210,Property, Plant & Equipment,Asset,"Fixed Asset",,Investing,1200,PPE,FALSE,FALSE,,
1211,Office Equipment,Asset,"Fixed Asset",,TRUE,Investing,1210,PPE,FALSE,FALSE,5000.00,2023-01-01
1212,Accumulated Depreciation - Office Equipment,Asset,"Accumulated Depreciation",,FALSE,Operating,1210,PPE_ACCUM_DEPR,FALSE,FALSE,-500.00,2023-01-01
2000,LIABILITIES,Liability,,,,,,,,,,
2100,Current Liabilities,Liability,,,,2000,CURRENT_LIABILITIES,FALSE,FALSE,,
2110,Accounts Payable,Liability,"Accounts Payable",,TRUE,Operating,2100,ACCOUNTS_PAYABLE,TRUE,FALSE,,
2120,GST Payable,Liability,"GST Payable",,TRUE,Operating,2100,TAX_LIABILITIES,FALSE,FALSE,,
2130,Withholding Tax Payable,Liability,"Current Liability",,FALSE,Operating,2100,TAX_LIABILITIES,FALSE,FALSE,,
2200,Non-Current Liabilities,Liability,,,,2000,NON_CURRENT_LIABILITIES,FALSE,FALSE,,
2210,Bank Loan (Long Term),Liability,"Long-term Liability",,FALSE,Financing,2200,LOANS_PAYABLE,FALSE,FALSE,,
3000,EQUITY,Equity,,,,,,,,,,
3100,Owner's Capital,Equity,"Owner's Equity",,FALSE,Financing,3000,OWNERS_EQUITY,FALSE,FALSE,,
3200,Retained Earnings,Equity,"Retained Earnings",,FALSE,Financing,3000,RETAINED_EARNINGS,FALSE,FALSE,,SYS-RETAINED-EARNINGS
4000,REVENUE,Revenue,,,,,,,,,,
4100,Sales Revenue,Revenue,Sales,Taxable,TRUE,Operating,4000,OPERATING_REVENUE,FALSE,FALSE,,
4200,Service Revenue,Revenue,Services,Taxable,TRUE,Operating,4000,OPERATING_REVENUE,FALSE,FALSE,,
5000,COST OF SALES,Expense,,,,,,,,,,
5100,Cost of Goods Sold,Expense,"Cost of Sales",Taxable,TRUE,Operating,5000,COST_OF_SALES,FALSE,FALSE,,
6000,OPERATING EXPENSES,Expense,,,,,,,,,,
6100,Salaries & Wages,Expense,"Operating Expenses",Non-Taxable,FALSE,Operating,6000,SALARIES,FALSE,FALSE,,
6110,Rent Expense,Expense,"Operating Expenses",Taxable,TRUE,Operating,6000,RENT,FALSE,FALSE,,
6120,Utilities Expense,Expense,"Operating Expenses",Taxable,TRUE,Operating,6000,UTILITIES,FALSE,FALSE,,
6130,Depreciation Expense,Expense,"Depreciation",Non-Deductible,FALSE,Operating,6000,DEPRECIATION,FALSE,FALSE,,
7000,OTHER INCOME,Revenue,,,,,,,,,,
7100,Interest Income,Revenue,"Other Income",Taxable,FALSE,Investing,7000,INTEREST_INCOME,FALSE,FALSE,,
7200,Foreign Exchange Gain,Revenue,"Other Income",Taxable,FALSE,Operating,7000,FOREX,FALSE,FALSE,,
8000,OTHER EXPENSES,Expense,,,,,,,,,,
8100,Bank Charges,Expense,"Other Expenses",Non-Deductible,TRUE,Operating,8000,BANK_CHARGES,FALSE,FALSE,,
8200,Foreign Exchange Loss,Expense,"Other Expenses",Non-Deductible,FALSE,Operating,8000,FOREX,FALSE,FALSE,,

```

# Below are files `scripts/schema.sql` and `scripts/initial_data.sql` represented by their changes in "diff" command output
```diff
# diff -u scripts/schema.sql-original scripts/schema.sql
--- scripts/schema.sql-original	2025-06-04 18:50:55.248484950 +0800
+++ scripts/schema.sql	2025-06-10 13:28:36.381843159 +0800
@@ -1,31 +1,17 @@
 -- File: scripts/schema.sql
 -- ============================================================================
--- SG Bookkeeper - Complete Database Schema - Version 1.0.5
+-- SG Bookkeeper - Complete Database Schema - Version 1.0.7
 -- ============================================================================
--- This script creates the complete database schema for the SG Bookkeeper application.
--- Base version for this consolidated file was 1.0.3.
---
--- Changes from 1.0.3 to 1.0.4 (incorporated):
---  - Added business.bank_reconciliations table (for saving reconciliation state).
---  - Added last_reconciled_balance to business.bank_accounts.
---  - Added reconciled_bank_reconciliation_id to business.bank_transactions.
---  - Added relevant FK constraints for reconciliation features.
---
--- Changes from 1.0.4 to 1.0.5 (incorporated):
---  - Added status VARCHAR(20) NOT NULL DEFAULT 'Draft' with CHECK constraint to business.bank_reconciliations.
---
--- Features from 1.0.3 (base for this file):
---  - Schema version updated for bank_transactions fields (is_from_statement, raw_statement_data) & corrected trial_balance view logic.
---  - Trigger for automatic bank_account balance updates.
---  - Extended audit logging to bank_accounts and bank_transactions.
+-- Changes from 1.0.6:
+--  - Added `cash_flow_category` to `accounting.accounts` table to support the Cash Flow Statement report.
 -- ============================================================================
 
 -- ============================================================================
 -- INITIAL SETUP
 -- ============================================================================
-CREATE EXTENSION IF NOT EXISTS pgcrypto; -- For gen_random_uuid() or other crypto functions if needed
-CREATE EXTENSION IF NOT EXISTS pg_stat_statements; -- For monitoring query performance
-CREATE EXTENSION IF NOT EXISTS btree_gist; -- For EXCLUDE USING gist constraints (e.g., on date ranges)
+CREATE EXTENSION IF NOT EXISTS pgcrypto; 
+CREATE EXTENSION IF NOT EXISTS pg_stat_statements; 
+CREATE EXTENSION IF NOT EXISTS btree_gist; 
 
 CREATE SCHEMA IF NOT EXISTS core;
 CREATE SCHEMA IF NOT EXISTS accounting;
@@ -62,9 +48,9 @@
 
 CREATE TABLE core.permissions (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'manage_users', 'view_reports'
+    code VARCHAR(50) NOT NULL UNIQUE, 
     description VARCHAR(200),
-    module VARCHAR(50) NOT NULL, -- e.g., 'Core', 'Accounting', 'Sales'
+    module VARCHAR(50) NOT NULL, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
 );
 
@@ -86,7 +72,7 @@
     id SERIAL PRIMARY KEY,
     company_name VARCHAR(100) NOT NULL,
     legal_name VARCHAR(200),
-    uen_no VARCHAR(20), -- Singapore UEN
+    uen_no VARCHAR(20), 
     gst_registration_no VARCHAR(20),
     gst_registered BOOLEAN DEFAULT FALSE,
     address_line1 VARCHAR(100),
@@ -98,39 +84,39 @@
     phone VARCHAR(20),
     email VARCHAR(100),
     website VARCHAR(100),
-    logo BYTEA, -- Store logo image as bytes
+    logo BYTEA, 
     fiscal_year_start_month INTEGER DEFAULT 1 CHECK (fiscal_year_start_month BETWEEN 1 AND 12),
     fiscal_year_start_day INTEGER DEFAULT 1 CHECK (fiscal_year_start_day BETWEEN 1 AND 31),
     base_currency VARCHAR(3) DEFAULT 'SGD', 
-    tax_id_label VARCHAR(50) DEFAULT 'UEN', -- Label for primary tax ID shown on documents
-    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd', -- e.g., yyyy-MM-dd, dd/MM/yyyy
+    tax_id_label VARCHAR(50) DEFAULT 'UEN', 
+    date_format VARCHAR(20) DEFAULT 'yyyy-MM-dd', 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    updated_by INTEGER -- FK to core.users.id
+    updated_by INTEGER 
 );
 
 CREATE TABLE core.configuration (
     id SERIAL PRIMARY KEY,
-    config_key VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'DEFAULT_AR_ACCOUNT_ID'
+    config_key VARCHAR(50) NOT NULL UNIQUE, 
     config_value TEXT,
     description VARCHAR(200),
-    is_encrypted BOOLEAN DEFAULT FALSE, -- For sensitive config values
+    is_encrypted BOOLEAN DEFAULT FALSE, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    updated_by INTEGER -- FK to core.users.id
+    updated_by INTEGER 
 );
 
 CREATE TABLE core.sequences (
     id SERIAL PRIMARY KEY,
-    sequence_name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'SALES_INVOICE_NO', 'JOURNAL_ENTRY_NO'
+    sequence_name VARCHAR(50) NOT NULL UNIQUE, 
     prefix VARCHAR(10),
     suffix VARCHAR(10),
     next_value INTEGER NOT NULL DEFAULT 1,
     increment_by INTEGER NOT NULL DEFAULT 1,
     min_value INTEGER NOT NULL DEFAULT 1,
-    max_value INTEGER NOT NULL DEFAULT 2147483647, -- Max int value
-    cycle BOOLEAN DEFAULT FALSE, -- Whether to cycle back to min_value after reaching max_value
-    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}', -- e.g., 'INV-{VALUE}'
+    max_value INTEGER NOT NULL DEFAULT 2147483647, 
+    cycle BOOLEAN DEFAULT FALSE, 
+    format_template VARCHAR(50) DEFAULT '{PREFIX}{VALUE}{SUFFIX}', 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
 );
@@ -140,11 +126,11 @@
 -- ============================================================================
 CREATE TABLE accounting.account_types (
     id SERIAL PRIMARY KEY,
-    name VARCHAR(50) NOT NULL UNIQUE, -- e.g., 'Current Asset', 'Long-term Liability'
+    name VARCHAR(50) NOT NULL UNIQUE, 
     category VARCHAR(20) NOT NULL CHECK (category IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')),
-    is_debit_balance BOOLEAN NOT NULL, -- True for Asset, Expense; False for Liability, Equity, Revenue
-    report_type VARCHAR(30) NOT NULL, -- e.g., 'BalanceSheet', 'ProfitAndLoss'
-    display_order INTEGER NOT NULL, -- For ordering in reports/CoA views
+    is_debit_balance BOOLEAN NOT NULL, 
+    report_type VARCHAR(30) NOT NULL, 
+    display_order INTEGER NOT NULL, 
     description VARCHAR(200),
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
@@ -152,59 +138,62 @@
 
 CREATE TABLE accounting.accounts (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(20) NOT NULL UNIQUE, -- Account code/number
+    code VARCHAR(20) NOT NULL UNIQUE, 
     name VARCHAR(100) NOT NULL,
-    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')), -- Corresponds to account_types.category
-    sub_type VARCHAR(30), -- More specific type, e.g., 'Cash', 'Bank', 'Accounts Receivable'
-    tax_treatment VARCHAR(20), -- e.g., 'GST Input', 'GST Output', 'Non-Taxable'
+    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('Asset', 'Liability', 'Equity', 'Revenue', 'Expense')), 
+    sub_type VARCHAR(30), 
+    tax_treatment VARCHAR(20), 
     gst_applicable BOOLEAN DEFAULT FALSE,
     is_active BOOLEAN DEFAULT TRUE,
     description TEXT,
-    parent_id INTEGER, -- FK to self for hierarchical CoA
-    report_group VARCHAR(50), -- For custom grouping in financial reports
-    is_control_account BOOLEAN DEFAULT FALSE, -- True if this account is a control account (e.g., AR, AP)
-    is_bank_account BOOLEAN DEFAULT FALSE, -- True if linked to a business.bank_accounts record
+    parent_id INTEGER, 
+    report_group VARCHAR(50), 
+    cash_flow_category VARCHAR(20) CHECK (cash_flow_category IN ('Operating', 'Investing', 'Financing')), -- NEW
+    is_control_account BOOLEAN DEFAULT FALSE, 
+    is_bank_account BOOLEAN DEFAULT FALSE, 
     opening_balance NUMERIC(15,2) DEFAULT 0,
     opening_balance_date DATE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 CREATE INDEX idx_accounts_parent_id ON accounting.accounts(parent_id);
 CREATE INDEX idx_accounts_is_active ON accounting.accounts(is_active);
 CREATE INDEX idx_accounts_account_type ON accounting.accounts(account_type);
+COMMENT ON COLUMN accounting.accounts.cash_flow_category IS 'Used to classify account balance changes for the Statement of Cash Flows.';
+
 
 CREATE TABLE accounting.fiscal_years (
     id SERIAL PRIMARY KEY,
-    year_name VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'FY2023', '2023-2024'
+    year_name VARCHAR(20) NOT NULL UNIQUE, 
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     is_closed BOOLEAN DEFAULT FALSE,
     closed_date TIMESTAMP WITH TIME ZONE,
-    closed_by INTEGER, -- FK to core.users.id
+    closed_by INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL, -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL, 
     CONSTRAINT fy_date_range_check CHECK (start_date <= end_date),
     CONSTRAINT fy_unique_date_ranges EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
 );
 
 CREATE TABLE accounting.fiscal_periods (
     id SERIAL PRIMARY KEY,
-    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
-    name VARCHAR(50) NOT NULL, -- e.g., 'Jan 2023', 'Q1 2023'
+    fiscal_year_id INTEGER NOT NULL, 
+    name VARCHAR(50) NOT NULL, 
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('Month', 'Quarter', 'Year')),
     status VARCHAR(10) NOT NULL CHECK (status IN ('Open', 'Closed', 'Archived')),
-    period_number INTEGER NOT NULL, -- e.g., 1 for Jan, 1 for Q1
-    is_adjustment BOOLEAN DEFAULT FALSE, -- For year-end adjustment periods
+    period_number INTEGER NOT NULL, 
+    is_adjustment BOOLEAN DEFAULT FALSE, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL, -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL, 
     CONSTRAINT fp_date_range_check CHECK (start_date <= end_date),
     CONSTRAINT fp_unique_period_dates UNIQUE (fiscal_year_id, period_type, period_number)
 );
@@ -212,51 +201,51 @@
 CREATE INDEX idx_fiscal_periods_status ON accounting.fiscal_periods(status);
 
 CREATE TABLE accounting.currencies (
-    code CHAR(3) PRIMARY KEY, -- e.g., 'SGD', 'USD'
+    code CHAR(3) PRIMARY KEY, 
     name VARCHAR(50) NOT NULL,
     symbol VARCHAR(10) NOT NULL,
     is_active BOOLEAN DEFAULT TRUE,
     decimal_places INTEGER DEFAULT 2,
-    format_string VARCHAR(20) DEFAULT '#,##0.00', -- For display formatting
+    format_string VARCHAR(20) DEFAULT '#,##0.00', 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER, -- FK to core.users.id
-    updated_by INTEGER -- FK to core.users.id
+    created_by INTEGER, 
+    updated_by INTEGER 
 );
 
 CREATE TABLE accounting.exchange_rates (
     id SERIAL PRIMARY KEY,
-    from_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
-    to_currency CHAR(3) NOT NULL, -- FK to accounting.currencies.code
+    from_currency CHAR(3) NOT NULL, 
+    to_currency CHAR(3) NOT NULL, 
     rate_date DATE NOT NULL,
     exchange_rate NUMERIC(15,6) NOT NULL,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER, -- FK to core.users.id
-    updated_by INTEGER, -- FK to core.users.id
+    created_by INTEGER, 
+    updated_by INTEGER, 
     CONSTRAINT uq_exchange_rates_pair_date UNIQUE (from_currency, to_currency, rate_date)
 );
 CREATE INDEX idx_exchange_rates_lookup ON accounting.exchange_rates(from_currency, to_currency, rate_date);
 
 CREATE TABLE accounting.journal_entries (
     id SERIAL PRIMARY KEY,
-    entry_no VARCHAR(20) NOT NULL UNIQUE, -- System-generated
-    journal_type VARCHAR(20) NOT NULL, -- e.g., 'General', 'Sales', 'Purchase', 'Payment'
+    entry_no VARCHAR(20) NOT NULL UNIQUE, 
+    journal_type VARCHAR(20) NOT NULL, 
     entry_date DATE NOT NULL,
-    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
+    fiscal_period_id INTEGER NOT NULL, 
     description VARCHAR(500),
-    reference VARCHAR(100), -- External reference if any
+    reference VARCHAR(100), 
     is_recurring BOOLEAN DEFAULT FALSE,
-    recurring_pattern_id INTEGER, -- FK to accounting.recurring_patterns.id
+    recurring_pattern_id INTEGER, 
     is_posted BOOLEAN DEFAULT FALSE,
     is_reversed BOOLEAN DEFAULT FALSE,
-    reversing_entry_id INTEGER, -- FK to self (accounting.journal_entries.id)
-    source_type VARCHAR(50), -- e.g., 'SalesInvoice', 'PurchaseInvoice', 'Payment'
-    source_id INTEGER, -- ID of the source document
+    reversing_entry_id INTEGER, 
+    source_type VARCHAR(50), 
+    source_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 CREATE INDEX idx_journal_entries_date ON accounting.journal_entries(entry_date);
 CREATE INDEX idx_journal_entries_fiscal_period ON accounting.journal_entries(fiscal_period_id);
@@ -265,18 +254,18 @@
 
 CREATE TABLE accounting.journal_entry_lines (
     id SERIAL PRIMARY KEY,
-    journal_entry_id INTEGER NOT NULL, -- FK to accounting.journal_entries.id
+    journal_entry_id INTEGER NOT NULL, 
     line_number INTEGER NOT NULL,
-    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
+    account_id INTEGER NOT NULL, 
     description VARCHAR(200),
     debit_amount NUMERIC(15,2) DEFAULT 0,
     credit_amount NUMERIC(15,2) DEFAULT 0,
-    currency_code CHAR(3) DEFAULT 'SGD', -- FK to accounting.currencies.code
-    exchange_rate NUMERIC(15,6) DEFAULT 1, -- Rate to base currency
-    tax_code VARCHAR(20), -- FK to accounting.tax_codes.code
+    currency_code CHAR(3) DEFAULT 'SGD', 
+    exchange_rate NUMERIC(15,6) DEFAULT 1, 
+    tax_code VARCHAR(20), 
     tax_amount NUMERIC(15,2) DEFAULT 0,
-    dimension1_id INTEGER, -- FK to accounting.dimensions.id (e.g., Department)
-    dimension2_id INTEGER, -- FK to accounting.dimensions.id (e.g., Project)
+    dimension1_id INTEGER, 
+    dimension2_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     CONSTRAINT jel_check_debit_credit CHECK ((debit_amount > 0 AND credit_amount = 0) OR (credit_amount > 0 AND debit_amount = 0) OR (debit_amount = 0 AND credit_amount = 0))
@@ -288,111 +277,111 @@
     id SERIAL PRIMARY KEY,
     name VARCHAR(100) NOT NULL,
     description TEXT,
-    template_entry_id INTEGER NOT NULL, -- FK to a template journal_entries.id
+    template_entry_id INTEGER NOT NULL, 
     frequency VARCHAR(20) NOT NULL CHECK (frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')),
-    interval_value INTEGER NOT NULL DEFAULT 1, -- e.g., every 2 months
+    interval_value INTEGER NOT NULL DEFAULT 1, 
     start_date DATE NOT NULL,
-    end_date DATE, -- Optional end date for recurrence
-    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31), -- For monthly recurrence
-    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), -- For weekly recurrence (0=Sunday)
+    end_date DATE, 
+    day_of_month INTEGER CHECK (day_of_month BETWEEN 1 AND 31), 
+    day_of_week INTEGER CHECK (day_of_week BETWEEN 0 AND 6), 
     last_generated_date DATE,
     next_generation_date DATE,
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 
 CREATE TABLE accounting.dimensions (
     id SERIAL PRIMARY KEY,
-    dimension_type VARCHAR(50) NOT NULL, -- e.g., 'Department', 'Project', 'Location'
+    dimension_type VARCHAR(50) NOT NULL, 
     code VARCHAR(20) NOT NULL,
     name VARCHAR(100) NOT NULL,
     description TEXT,
     is_active BOOLEAN DEFAULT TRUE,
-    parent_id INTEGER, -- FK to self for hierarchical dimensions
+    parent_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL, -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL, 
     UNIQUE (dimension_type, code)
 );
 
 CREATE TABLE accounting.budgets (
     id SERIAL PRIMARY KEY,
     name VARCHAR(100) NOT NULL,
-    fiscal_year_id INTEGER NOT NULL, -- FK to accounting.fiscal_years.id
+    fiscal_year_id INTEGER NOT NULL, 
     description TEXT,
     is_active BOOLEAN DEFAULT TRUE,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 
 CREATE TABLE accounting.budget_details (
     id SERIAL PRIMARY KEY,
-    budget_id INTEGER NOT NULL, -- FK to accounting.budgets.id
-    account_id INTEGER NOT NULL, -- FK to accounting.accounts.id
-    fiscal_period_id INTEGER NOT NULL, -- FK to accounting.fiscal_periods.id
+    budget_id INTEGER NOT NULL, 
+    account_id INTEGER NOT NULL, 
+    fiscal_period_id INTEGER NOT NULL, 
     amount NUMERIC(15,2) NOT NULL,
-    dimension1_id INTEGER, -- FK to accounting.dimensions.id
-    dimension2_id INTEGER, -- FK to accounting.dimensions.id
+    dimension1_id INTEGER, 
+    dimension2_id INTEGER, 
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 CREATE UNIQUE INDEX uix_budget_details_key ON accounting.budget_details (budget_id, account_id, fiscal_period_id, COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0));
 
 CREATE TABLE accounting.tax_codes (
     id SERIAL PRIMARY KEY,
-    code VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'SR', 'ZR', 'ES', 'TX'
+    code VARCHAR(20) NOT NULL UNIQUE, 
     description VARCHAR(100) NOT NULL,
     tax_type VARCHAR(20) NOT NULL CHECK (tax_type IN ('GST', 'Income Tax', 'Withholding Tax')),
-    rate NUMERIC(5,2) NOT NULL, -- e.g., 9.00 for 9% GST
+    rate NUMERIC(5,2) NOT NULL, 
     is_default BOOLEAN DEFAULT FALSE,
     is_active BOOLEAN DEFAULT TRUE,
-    affects_account_id INTEGER, -- FK to accounting.accounts.id (e.g., GST Payable/Receivable account)
+    affects_account_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 
 CREATE TABLE accounting.gst_returns (
     id SERIAL PRIMARY KEY,
-    return_period VARCHAR(20) NOT NULL UNIQUE, -- e.g., 'Q1/2023'
+    return_period VARCHAR(20) NOT NULL UNIQUE, 
     start_date DATE NOT NULL,
     end_date DATE NOT NULL,
     filing_due_date DATE NOT NULL,
-    standard_rated_supplies NUMERIC(15,2) DEFAULT 0, -- Box 1
-    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,    -- Box 2
-    exempt_supplies NUMERIC(15,2) DEFAULT 0,        -- Box 3
-    total_supplies NUMERIC(15,2) DEFAULT 0,         -- Box 4 (Auto-calc: Box 1+2+3)
-    taxable_purchases NUMERIC(15,2) DEFAULT 0,      -- Box 5
-    output_tax NUMERIC(15,2) DEFAULT 0,             -- Box 6
-    input_tax NUMERIC(15,2) DEFAULT 0,              -- Box 7
-    tax_adjustments NUMERIC(15,2) DEFAULT 0,        -- Box 8 (e.g., bad debt relief)
-    tax_payable NUMERIC(15,2) DEFAULT 0,            -- Box 9 (Auto-calc: Box 6-7+8)
+    standard_rated_supplies NUMERIC(15,2) DEFAULT 0, 
+    zero_rated_supplies NUMERIC(15,2) DEFAULT 0,    
+    exempt_supplies NUMERIC(15,2) DEFAULT 0,        
+    total_supplies NUMERIC(15,2) DEFAULT 0,         
+    taxable_purchases NUMERIC(15,2) DEFAULT 0,      
+    output_tax NUMERIC(15,2) DEFAULT 0,             
+    input_tax NUMERIC(15,2) DEFAULT 0,              
+    tax_adjustments NUMERIC(15,2) DEFAULT 0,        
+    tax_payable NUMERIC(15,2) DEFAULT 0,            
     status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Submitted', 'Amended')),
     submission_date DATE,
-    submission_reference VARCHAR(50), -- IRAS submission reference
-    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id (for GST settlement JE)
+    submission_reference VARCHAR(50), 
+    journal_entry_id INTEGER, 
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 
 CREATE TABLE accounting.withholding_tax_certificates (
     id SERIAL PRIMARY KEY,
     certificate_no VARCHAR(20) NOT NULL UNIQUE,
-    vendor_id INTEGER NOT NULL, -- FK to business.vendors.id
-    tax_type VARCHAR(50) NOT NULL, -- e.g., 'Section 19', 'Section 45'
+    vendor_id INTEGER NOT NULL, 
+    tax_type VARCHAR(50) NOT NULL, 
     tax_rate NUMERIC(5,2) NOT NULL,
     payment_date DATE NOT NULL,
     amount_before_tax NUMERIC(15,2) NOT NULL,
@@ -400,12 +389,12 @@
     payment_reference VARCHAR(50),
     status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'Issued', 'Voided')),
     issue_date DATE,
-    journal_entry_id INTEGER, -- FK to accounting.journal_entries.id
+    journal_entry_id INTEGER, 
     notes TEXT,
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
-    created_by INTEGER NOT NULL, -- FK to core.users.id
-    updated_by INTEGER NOT NULL -- FK to core.users.id
+    created_by INTEGER NOT NULL, 
+    updated_by INTEGER NOT NULL 
 );
 
 -- ============================================================================
@@ -454,7 +443,7 @@
     opening_balance NUMERIC(15,2) DEFAULT 0, 
     current_balance NUMERIC(15,2) DEFAULT 0, 
     last_reconciled_date DATE, 
-    last_reconciled_balance NUMERIC(15,2) NULL, -- Added from 1.0.4 patch
+    last_reconciled_balance NUMERIC(15,2) NULL,
     gl_account_id INTEGER NOT NULL, 
     is_active BOOLEAN DEFAULT TRUE, 
     description TEXT, 
@@ -473,14 +462,14 @@
     transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')), 
     description VARCHAR(200) NOT NULL, 
     reference VARCHAR(100), 
-    amount NUMERIC(15,2) NOT NULL, -- Signed amount: positive for inflow, negative for outflow
+    amount NUMERIC(15,2) NOT NULL,
     is_reconciled BOOLEAN DEFAULT FALSE NOT NULL, 
     reconciled_date DATE, 
     statement_date DATE, 
     statement_id VARCHAR(50), 
-    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE, -- From 1.0.2
-    raw_statement_data JSONB NULL, -- From 1.0.2
-    reconciled_bank_reconciliation_id INT NULL, -- Added from 1.0.4 patch
+    is_from_statement BOOLEAN NOT NULL DEFAULT FALSE,
+    raw_statement_data JSONB NULL,
+    reconciled_bank_reconciliation_id INT NULL,
     journal_entry_id INTEGER, 
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
@@ -501,19 +490,18 @@
     reconciled_difference NUMERIC(15,2) NOT NULL, 
     reconciliation_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
     notes TEXT NULL,
-    status VARCHAR(20) NOT NULL DEFAULT 'Draft', -- Added from 1.0.5 patch
+    status VARCHAR(20) NOT NULL DEFAULT 'Draft',
     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
     created_by_user_id INTEGER NOT NULL,
     CONSTRAINT uq_bank_reconciliation_account_statement_date UNIQUE (bank_account_id, statement_date),
-    CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized')) -- Added from 1.0.5 patch
+    CONSTRAINT ck_bank_reconciliations_status CHECK (status IN ('Draft', 'Finalized'))
 );
 COMMENT ON TABLE business.bank_reconciliations IS 'Stores summary records of completed bank reconciliations.';
 COMMENT ON COLUMN business.bank_reconciliations.statement_date IS 'The end date of the bank statement that was reconciled.';
 COMMENT ON COLUMN business.bank_reconciliations.calculated_book_balance IS 'The book balance of the bank account as of the statement_date, after all reconciling items for this reconciliation are accounted for.';
 COMMENT ON COLUMN business.bank_reconciliations.status IS 'The status of the reconciliation, e.g., Draft, Finalized. Default is Draft.';
 
-
 CREATE TABLE business.payments (
     id SERIAL PRIMARY KEY, payment_no VARCHAR(20) NOT NULL UNIQUE, payment_type VARCHAR(20) NOT NULL CHECK (payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')), payment_method VARCHAR(20) NOT NULL CHECK (payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')), payment_date DATE NOT NULL, entity_type VARCHAR(20) NOT NULL CHECK (entity_type IN ('Customer', 'Vendor', 'Other')), entity_id INTEGER NOT NULL, bank_account_id INTEGER, currency_code CHAR(3) NOT NULL, exchange_rate NUMERIC(15,6) DEFAULT 1, amount NUMERIC(15,2) NOT NULL, reference VARCHAR(100), description TEXT, cheque_no VARCHAR(50), status VARCHAR(20) NOT NULL DEFAULT 'Draft' CHECK (status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')), journal_entry_id INTEGER, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, created_by INTEGER NOT NULL, updated_by INTEGER NOT NULL);
 CREATE INDEX idx_payments_date ON business.payments(payment_date); CREATE INDEX idx_payments_entity ON business.payments(entity_type, entity_id); CREATE INDEX idx_payments_status ON business.payments(status);
@@ -536,7 +524,6 @@
 -- ============================================================================
 -- ADDING FOREIGN KEY CONSTRAINTS 
 -- ============================================================================
--- Core Schema FKs
 ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES core.roles(id) ON DELETE CASCADE;
 ALTER TABLE core.role_permissions ADD CONSTRAINT fk_rp_permission FOREIGN KEY (permission_id) REFERENCES core.permissions(id) ON DELETE CASCADE;
 ALTER TABLE core.user_roles ADD CONSTRAINT fk_ur_user FOREIGN KEY (user_id) REFERENCES core.users(id) ON DELETE CASCADE;
@@ -545,7 +532,6 @@
 ALTER TABLE core.company_settings ADD CONSTRAINT fk_cs_base_currency FOREIGN KEY (base_currency) REFERENCES accounting.currencies(code);
 ALTER TABLE core.configuration ADD CONSTRAINT fk_cfg_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
 
--- Accounting Schema FKs
 ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_parent FOREIGN KEY (parent_id) REFERENCES accounting.accounts(id);
 ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE accounting.accounts ADD CONSTRAINT fk_acc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
@@ -612,7 +598,6 @@
 ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE accounting.withholding_tax_certificates ADD CONSTRAINT fk_whtc_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
 
--- Business Schema FKs
 ALTER TABLE business.customers ADD CONSTRAINT fk_cust_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
 ALTER TABLE business.customers ADD CONSTRAINT fk_cust_receivables_acc FOREIGN KEY (receivables_account_id) REFERENCES accounting.accounts(id);
 ALTER TABLE business.customers ADD CONSTRAINT fk_cust_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
@@ -664,12 +649,12 @@
 
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_journal_entry FOREIGN KEY (journal_entry_id) REFERENCES accounting.journal_entries(id);
-ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL; -- Added from 1.0.4 patch
+ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_reconciliation FOREIGN KEY (reconciled_bank_reconciliation_id) REFERENCES business.bank_reconciliations(id) ON DELETE SET NULL;
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 ALTER TABLE business.bank_transactions ADD CONSTRAINT fk_bt_updated_by FOREIGN KEY (updated_by) REFERENCES core.users(id);
 
-ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE; -- Added from 1.0.4 patch
-ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id); -- Added from 1.0.4 patch
+ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id) ON DELETE CASCADE;
+ALTER TABLE business.bank_reconciliations ADD CONSTRAINT fk_br_created_by FOREIGN KEY (created_by_user_id) REFERENCES core.users(id);
 
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_bank_account FOREIGN KEY (bank_account_id) REFERENCES business.bank_accounts(id);
 ALTER TABLE business.payments ADD CONSTRAINT fk_pay_currency FOREIGN KEY (currency_code) REFERENCES accounting.currencies(code);
@@ -680,7 +665,6 @@
 ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_payment FOREIGN KEY (payment_id) REFERENCES business.payments(id) ON DELETE CASCADE;
 ALTER TABLE business.payment_allocations ADD CONSTRAINT fk_pa_created_by FOREIGN KEY (created_by) REFERENCES core.users(id);
 
--- Audit Schema FKs
 ALTER TABLE audit.audit_log ADD CONSTRAINT fk_al_user FOREIGN KEY (user_id) REFERENCES core.users(id);
 ALTER TABLE audit.data_change_history ADD CONSTRAINT fk_dch_changed_by FOREIGN KEY (changed_by) REFERENCES core.users(id);
 
@@ -689,46 +673,24 @@
 -- ============================================================================
 CREATE OR REPLACE VIEW accounting.account_balances AS
 SELECT 
-    a.id AS account_id,
-    a.code AS account_code,
-    a.name AS account_name,
-    a.account_type,
-    a.parent_id,
-    -- balance is calculated as: opening_balance + sum_of_debits - sum_of_credits
-    -- where debits increase balance and credits decrease balance (for Asset/Expense view)
-    -- or credits increase balance and debits decrease balance (for Liability/Equity/Revenue view)
-    -- The current logic `SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END)`
-    -- effectively sums (debits - credits), so a positive result is a net debit movement.
+    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.parent_id,
     COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) + a.opening_balance AS balance,
-    COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity, -- Sum of all debit lines
-    COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity, -- Sum of all credit lines
+    COALESCE(SUM(jel.debit_amount), 0) AS total_debits_activity,
+    COALESCE(SUM(jel.credit_amount), 0) AS total_credits_activity,
     MAX(je.entry_date) AS last_activity_date
 FROM accounting.accounts a
 LEFT JOIN accounting.journal_entry_lines jel ON a.id = jel.account_id
 LEFT JOIN accounting.journal_entries je ON jel.journal_entry_id = je.id AND je.is_posted = TRUE
 GROUP BY a.id, a.code, a.name, a.account_type, a.parent_id, a.opening_balance;
 
--- Corrected Trial Balance View
 CREATE OR REPLACE VIEW accounting.trial_balance AS
 SELECT 
-    a.id AS account_id,
-    a.code AS account_code,
-    a.name AS account_name,
-    a.account_type,
-    a.sub_type,
-    -- If ab.balance (net debit actual balance) > 0, it's a debit balance.
-    -- If ab.balance (net credit actual balance) < 0, it's a credit balance (-ab.balance).
-    CASE 
-        WHEN ab.balance > 0 THEN ab.balance 
-        ELSE 0 
-    END AS debit_balance,
-    CASE 
-        WHEN ab.balance < 0 THEN -ab.balance -- Show as positive in credit column
-        ELSE 0 
-    END AS credit_balance
+    a.id AS account_id, a.code AS account_code, a.name AS account_name, a.account_type, a.sub_type,
+    CASE WHEN ab.balance > 0 THEN ab.balance ELSE 0 END AS debit_balance,
+    CASE WHEN ab.balance < 0 THEN -ab.balance ELSE 0 END AS credit_balance
 FROM accounting.accounts a
 JOIN accounting.account_balances ab ON a.id = ab.account_id
-WHERE a.is_active = TRUE AND ab.balance != 0; -- Only show active accounts with non-zero balances
+WHERE a.is_active = TRUE AND ab.balance != 0; 
 
 CREATE OR REPLACE VIEW business.customer_balances AS
 SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name,
@@ -753,9 +715,8 @@
     p.id AS product_id, p.product_code, p.name AS product_name, p.product_type, p.category, p.unit_of_measure,
     COALESCE(SUM(im.quantity), 0) AS current_quantity,
     CASE 
-        WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN 
-            (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity)) -- Parentheses added for clarity
-        ELSE p.purchase_price -- Fallback to product's purchase price if no movements/zero quantity
+        WHEN COALESCE(SUM(im.quantity), 0) != 0 THEN (COALESCE(SUM(im.total_cost), 0) / SUM(im.quantity))
+        ELSE p.purchase_price
     END AS average_cost,
     COALESCE(SUM(im.total_cost), 0) AS inventory_value,
     p.sales_price AS current_sales_price, p.min_stock_level, p.reorder_point,
@@ -765,7 +726,6 @@
 WHERE p.product_type = 'Inventory' AND p.is_active = TRUE
 GROUP BY p.id, p.product_code, p.name, p.product_type, p.category, p.unit_of_measure, p.purchase_price, p.sales_price, p.min_stock_level, p.reorder_point;
 
-
 -- ============================================================================
 -- FUNCTIONS
 -- ============================================================================
@@ -779,7 +739,7 @@
     UPDATE core.sequences SET next_value = next_value + increment_by, updated_at = CURRENT_TIMESTAMP WHERE sequence_name = p_sequence_name;
     v_result := v_sequence.format_template;
     v_result := REPLACE(v_result, '{PREFIX}', COALESCE(v_sequence.prefix, ''));
-    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); -- Standard 6 digit padding
+    v_result := REPLACE(v_result, '{VALUE}', LPAD(v_next_value::TEXT, 6, '0')); 
     v_result := REPLACE(v_result, '{SUFFIX}', COALESCE(v_sequence.suffix, ''));
     RETURN v_result;
 END;
@@ -791,7 +751,7 @@
 BEGIN
     SELECT id INTO v_fiscal_period_id FROM accounting.fiscal_periods WHERE p_entry_date BETWEEN start_date AND end_date AND status = 'Open';
     IF v_fiscal_period_id IS NULL THEN RAISE EXCEPTION 'No open fiscal period found for date %', p_entry_date; END IF;
-    v_entry_no := core.get_next_sequence_value('journal_entry'); -- Assuming 'journal_entry' sequence exists
+    v_entry_no := core.get_next_sequence_value('journal_entry');
     INSERT INTO accounting.journal_entries (entry_no, journal_type, entry_date, fiscal_period_id, description, reference, is_posted, source_type, source_id, created_by, updated_by) VALUES (v_entry_no, p_journal_type, p_entry_date, v_fiscal_period_id, p_description, p_reference, FALSE, p_source_type, p_source_id, p_user_id, p_user_id) RETURNING id INTO v_journal_id;
     FOR v_line IN SELECT * FROM jsonb_array_elements(p_lines) LOOP
         INSERT INTO accounting.journal_entry_lines (journal_entry_id, line_number, account_id, description, debit_amount, credit_amount, currency_code, exchange_rate, tax_code, tax_amount, dimension1_id, dimension2_id) 
@@ -822,8 +782,6 @@
 BEGIN
     SELECT acc.opening_balance, acc.opening_balance_date INTO v_opening_balance, v_account_opening_balance_date FROM accounting.accounts acc WHERE acc.id = p_account_id;
     IF NOT FOUND THEN RAISE EXCEPTION 'Account with ID % not found', p_account_id; END IF;
-    -- Sum (debits - credits) from posted journal entry lines up to the specified date
-    -- and after or on the account's opening balance date (if specified)
     SELECT COALESCE(SUM(CASE WHEN jel.debit_amount > 0 THEN jel.debit_amount ELSE -jel.credit_amount END), 0) 
     INTO v_balance 
     FROM accounting.journal_entry_lines jel 
@@ -832,7 +790,6 @@
       AND je.is_posted = TRUE 
       AND je.entry_date <= p_as_of_date 
       AND (v_account_opening_balance_date IS NULL OR je.entry_date >= v_account_opening_balance_date);
-      
     v_balance := v_balance + COALESCE(v_opening_balance, 0);
     RETURN v_balance;
 END;
@@ -846,33 +803,21 @@
 DECLARE
     v_old_data JSONB; v_new_data JSONB; v_change_type VARCHAR(20); v_user_id INTEGER; v_entity_id INTEGER; v_entity_name VARCHAR(200); temp_val TEXT; current_field_name_from_json TEXT;
 BEGIN
-    -- Try to get user_id from session variable first
     BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
-    -- Fallback to created_by/updated_by if session variable not set (e.g., direct DB modification)
     IF v_user_id IS NULL THEN
         IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
         ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
-        -- For DELETE, if v_user_id is still NULL, it means we can't determine it from OLD record's updated_by
         END IF;
     END IF;
-    -- Avoid logging changes to audit tables themselves to prevent infinite loops
     IF TG_TABLE_SCHEMA = 'audit' AND TG_TABLE_NAME IN ('audit_log', 'data_change_history') THEN RETURN NULL; END IF;
-
     IF TG_OP = 'INSERT' THEN v_change_type := 'Insert'; v_old_data := NULL; v_new_data := to_jsonb(NEW);
     ELSIF TG_OP = 'UPDATE' THEN v_change_type := 'Update'; v_old_data := to_jsonb(OLD); v_new_data := to_jsonb(NEW);
     ELSIF TG_OP = 'DELETE' THEN v_change_type := 'Delete'; v_old_data := to_jsonb(OLD); v_new_data := NULL; END IF;
-
-    -- Determine entity_id (usually 'id' column)
     BEGIN IF TG_OP = 'DELETE' THEN v_entity_id := OLD.id; ELSE v_entity_id := NEW.id; END IF; EXCEPTION WHEN undefined_column THEN v_entity_id := NULL; END;
-    
-    -- Determine a representative entity_name (e.g., name, code, entry_no)
     BEGIN IF TG_OP = 'DELETE' THEN temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN OLD.name WHEN TG_TABLE_NAME = 'journal_entries' THEN OLD.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN OLD.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN OLD.payment_no WHEN TG_TABLE_NAME = 'users' THEN OLD.username WHEN TG_TABLE_NAME = 'tax_codes' THEN OLD.code WHEN TG_TABLE_NAME = 'gst_returns' THEN OLD.return_period ELSE OLD.id::TEXT END;
     ELSE temp_val := CASE WHEN TG_TABLE_NAME IN ('accounts','customers','vendors','products','roles','account_types','dimensions','fiscal_years','budgets') THEN NEW.name WHEN TG_TABLE_NAME = 'journal_entries' THEN NEW.entry_no WHEN TG_TABLE_NAME = 'sales_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'purchase_invoices' THEN NEW.invoice_no WHEN TG_TABLE_NAME = 'payments' THEN NEW.payment_no WHEN TG_TABLE_NAME = 'users' THEN NEW.username WHEN TG_TABLE_NAME = 'tax_codes' THEN NEW.code WHEN TG_TABLE_NAME = 'gst_returns' THEN NEW.return_period ELSE NEW.id::TEXT END; END IF; v_entity_name := temp_val;
     EXCEPTION WHEN undefined_column THEN BEGIN IF TG_OP = 'DELETE' THEN v_entity_name := OLD.id::TEXT; ELSE v_entity_name := NEW.id::TEXT; END IF; EXCEPTION WHEN undefined_column THEN v_entity_name := NULL; END; END;
-
     INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id,v_change_type,TG_TABLE_SCHEMA||'.'||TG_TABLE_NAME,v_entity_id,v_entity_name,jsonb_build_object('old',v_old_data,'new',v_new_data),CURRENT_TIMESTAMP);
-
-    -- Log individual field changes for UPDATE operations
     IF TG_OP = 'UPDATE' THEN
         FOR current_field_name_from_json IN SELECT key_alias FROM jsonb_object_keys(v_old_data) AS t(key_alias) LOOP
             IF (v_new_data ? current_field_name_from_json) AND ((v_old_data -> current_field_name_from_json) IS DISTINCT FROM (v_new_data -> current_field_name_from_json)) THEN
@@ -880,95 +825,47 @@
             END IF;
         END LOOP;
     END IF;
-    RETURN NULL; -- Result is ignored for AFTER trigger
+    RETURN NULL; 
 END;
 $$ LANGUAGE plpgsql;
 
--- Trigger to update bank_account.current_balance
 CREATE OR REPLACE FUNCTION business.update_bank_account_balance_trigger_func()
 RETURNS TRIGGER AS $$
 BEGIN
-    IF TG_OP = 'INSERT' THEN
-        UPDATE business.bank_accounts 
-        SET current_balance = current_balance + NEW.amount -- Assumes NEW.amount is signed
-        WHERE id = NEW.bank_account_id;
-    ELSIF TG_OP = 'DELETE' THEN
-        UPDATE business.bank_accounts 
-        SET current_balance = current_balance - OLD.amount -- Assumes OLD.amount is signed
-        WHERE id = OLD.bank_account_id;
+    IF TG_OP = 'INSERT' THEN UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id;
+    ELSIF TG_OP = 'DELETE' THEN UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id;
     ELSIF TG_OP = 'UPDATE' THEN
-        -- If bank account itself changed for the transaction
         IF NEW.bank_account_id != OLD.bank_account_id THEN
-            UPDATE business.bank_accounts 
-            SET current_balance = current_balance - OLD.amount 
-            WHERE id = OLD.bank_account_id;
-            
-            UPDATE business.bank_accounts 
-            SET current_balance = current_balance + NEW.amount 
-            WHERE id = NEW.bank_account_id;
-        ELSE -- Bank account is the same, just adjust for amount difference
-            UPDATE business.bank_accounts 
-            SET current_balance = current_balance - OLD.amount + NEW.amount 
-            WHERE id = NEW.bank_account_id;
-        END IF;
+            UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount WHERE id = OLD.bank_account_id;
+            UPDATE business.bank_accounts SET current_balance = current_balance + NEW.amount WHERE id = NEW.bank_account_id;
+        ELSE UPDATE business.bank_accounts SET current_balance = current_balance - OLD.amount + NEW.amount WHERE id = NEW.bank_account_id; END IF;
     END IF;
-    RETURN NULL; -- Result is ignored since this is an AFTER trigger
+    RETURN NULL; 
 END;
 $$ LANGUAGE plpgsql;
 
-
 -- ============================================================================
 -- APPLYING TRIGGERS
 -- ============================================================================
--- Apply update_timestamp trigger to all tables with 'updated_at'
-DO $$
-DECLARE r RECORD;
+DO $$ DECLARE r RECORD;
 BEGIN
-    FOR r IN 
-        SELECT table_schema, table_name 
-        FROM information_schema.columns 
-        WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit')
-        GROUP BY table_schema, table_name 
+    FOR r IN SELECT table_schema, table_name FROM information_schema.columns WHERE column_name = 'updated_at' AND table_schema IN ('core','accounting','business','audit') GROUP BY table_schema, table_name 
     LOOP
-        EXECUTE format(
-            'DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();',
-            r.table_schema, r.table_name, r.table_schema, r.table_name
-        );
+        EXECUTE format('DROP TRIGGER IF EXISTS trg_update_timestamp ON %I.%I; CREATE TRIGGER trg_update_timestamp BEFORE UPDATE ON %I.%I FOR EACH ROW EXECUTE FUNCTION core.update_timestamp_trigger_func();', r.table_schema, r.table_name, r.table_schema, r.table_name);
     END LOOP;
 END;
 $$;
 
--- Apply audit log trigger to specified tables
-DO $$
-DECLARE
-    tables_to_audit TEXT[] := ARRAY[
-        'accounting.accounts', 'accounting.journal_entries', 'accounting.fiscal_periods', 'accounting.fiscal_years',
-        'business.customers', 'business.vendors', 'business.products', 
-        'business.sales_invoices', 'business.purchase_invoices', 'business.payments',
-        'accounting.tax_codes', 'accounting.gst_returns',
-        'core.users', 'core.roles', 'core.company_settings', 
-        'business.bank_accounts', 'business.bank_transactions', 'business.bank_reconciliations' -- Added bank_reconciliations
-    ];
-    table_fullname TEXT;
-    schema_name TEXT;
-    table_name_var TEXT;
+DO $$ DECLARE tables_to_audit TEXT[] := ARRAY['accounting.accounts', 'accounting.journal_entries', 'accounting.fiscal_periods', 'accounting.fiscal_years', 'business.customers', 'business.vendors', 'business.products', 'business.sales_invoices', 'business.purchase_invoices', 'business.payments', 'accounting.tax_codes', 'accounting.gst_returns', 'core.users', 'core.roles', 'core.company_settings', 'business.bank_accounts', 'business.bank_transactions', 'business.bank_reconciliations'];
+    table_fullname TEXT; schema_name TEXT; table_name_var TEXT;
 BEGIN
     FOREACH table_fullname IN ARRAY tables_to_audit
     LOOP
-        SELECT split_part(table_fullname, '.', 1) INTO schema_name;
-        SELECT split_part(table_fullname, '.', 2) INTO table_name_var;
-        EXECUTE format(
-            'DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();',
-            schema_name, table_name_var, schema_name, table_name_var
-        );
+        SELECT split_part(table_fullname, '.', 1) INTO schema_name; SELECT split_part(table_fullname, '.', 2) INTO table_name_var;
+        EXECUTE format('DROP TRIGGER IF EXISTS trg_audit_log ON %I.%I; CREATE TRIGGER trg_audit_log AFTER INSERT OR UPDATE OR DELETE ON %I.%I FOR EACH ROW EXECUTE FUNCTION audit.log_data_change_trigger_func();', schema_name, table_name_var, schema_name, table_name_var);
     END LOOP;
 END;
 $$;
 
--- Apply bank balance update trigger
 DROP TRIGGER IF EXISTS trg_update_bank_balance ON business.bank_transactions;
-CREATE TRIGGER trg_update_bank_balance
-AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions
-FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();
-
--- End of script
+CREATE TRIGGER trg_update_bank_balance AFTER INSERT OR UPDATE OR DELETE ON business.bank_transactions FOR EACH ROW EXECUTE FUNCTION business.update_bank_account_balance_trigger_func();
```

```diff
# diff -u scripts/initial_data.sql-original scripts/initial_data.sql  
--- scripts/initial_data.sql-original	2025-06-09 19:09:30.414541265 +0800
+++ scripts/initial_data.sql	2025-06-10 13:28:50.694082111 +0800
@@ -1,9 +1,10 @@
 -- File: scripts/initial_data.sql
 -- ============================================================================
--- INITIAL DATA (Version 1.0.6)
+-- INITIAL DATA (Version 1.0.7)
 -- ============================================================================
--- Changes from 1.0.5:
--- - Added 'CorpTaxRate_Default' to core.configuration for use in tax computation reports.
+-- Changes from 1.0.6:
+-- - Added accounts for WHT Payable, Forex Gain/Loss.
+-- - Added configuration for WHT Payable, Forex Gain/Loss.
 -- ============================================================================
 
 BEGIN;
@@ -12,14 +13,10 @@
 -- Insert default roles
 -- ----------------------------------------------------------------------------
 INSERT INTO core.roles (name, description) VALUES
-('Administrator', 'Full system access'),
-('Accountant', 'Access to accounting functions'),
-('Bookkeeper', 'Basic transaction entry and reporting'),
-('Manager', 'Access to reports and dashboards'),
+('Administrator', 'Full system access'), ('Accountant', 'Access to accounting functions'),
+('Bookkeeper', 'Basic transaction entry and reporting'), ('Manager', 'Access to reports and dashboards'),
 ('Viewer', 'Read-only access to data')
-ON CONFLICT (name) DO UPDATE SET 
-    description = EXCLUDED.description, 
-    updated_at = CURRENT_TIMESTAMP;
+ON CONFLICT (name) DO UPDATE SET description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;
 
 -- ----------------------------------------------------------------------------
 -- Insert default permissions
@@ -60,11 +57,7 @@
 -- ----------------------------------------------------------------------------
 INSERT INTO core.users (id, username, password_hash, email, full_name, is_active, require_password_change)
 VALUES (1, 'system_init_user', crypt('system_init_secure_password_!PLACEHOLDER!', gen_salt('bf')), 'system_init@sgbookkeeper.com', 'System Initializer', FALSE, FALSE) 
-ON CONFLICT (id) DO UPDATE SET 
-    username = EXCLUDED.username, password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, 
-    full_name = EXCLUDED.full_name, is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
-    updated_at = CURRENT_TIMESTAMP;
-
+ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name, is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change, updated_at = CURRENT_TIMESTAMP;
 SELECT setval(pg_get_serial_sequence('core.users', 'id'), COALESCE((SELECT MAX(id) FROM core.users), 1), true);
 
 -- ----------------------------------------------------------------------------
@@ -117,10 +110,11 @@
 ('SysAcc_DefaultInventoryAsset', '1130', 'Default Inventory Asset account code', 1),
 ('SysAcc_DefaultCOGS', '5100', 'Default Cost of Goods Sold account code', 1),
 ('SysAcc_GSTControl', 'SYS-GST-CONTROL', 'GST Control/Clearing Account', 1),
-('CorpTaxRate_Default', '17.00', 'Default Corporate Tax Rate (%)', 1) -- NEW
-ON CONFLICT (config_key) DO UPDATE SET
-    config_value = EXCLUDED.config_value, description = EXCLUDED.description,
-    updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
+('SysAcc_WHTPayable', '2130', 'Default Withholding Tax Payable account code', 1), -- NEW
+('SysAcc_ForexGain', '7200', 'Default Foreign Exchange Gain account code', 1),    -- NEW
+('SysAcc_ForexLoss', '8200', 'Default Foreign Exchange Loss account code', 1),    -- NEW
+('CorpTaxRate_Default', '17.00', 'Default Corporate Tax Rate (%)', 1)
+ON CONFLICT (config_key) DO UPDATE SET config_value = EXCLUDED.config_value, description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
 
 -- ----------------------------------------------------------------------------
 -- Insert account types
@@ -128,6 +122,7 @@
 INSERT INTO accounting.account_types (name, category, is_debit_balance, report_type, display_order, description) VALUES
 ('Current Asset', 'Asset', TRUE, 'Balance Sheet', 10, 'Assets expected to be converted to cash within one year'),
 ('Fixed Asset', 'Asset', TRUE, 'Balance Sheet', 20, 'Long-term tangible assets'),
+('Accumulated Depreciation', 'Asset', FALSE, 'Balance Sheet', 21, 'Contra-asset account for accumulated depreciation'),
 ('Other Asset', 'Asset', TRUE, 'Balance Sheet', 30, 'Assets that don''t fit in other categories'),
 ('Current Liability', 'Liability', FALSE, 'Balance Sheet', 40, 'Obligations due within one year'),
 ('Long-term Liability', 'Liability', FALSE, 'Balance Sheet', 50, 'Obligations due beyond one year'),
@@ -137,23 +132,24 @@
 ('Expense', 'Expense', TRUE, 'Income Statement', 90, 'General business expenses'),
 ('Other Income', 'Revenue', FALSE, 'Income Statement', 100, 'Income from non-core activities'),
 ('Other Expense', 'Expense', TRUE, 'Income Statement', 110, 'Expenses from non-core activities')
-ON CONFLICT (name) DO UPDATE SET
-    category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type,
-    display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;
+ON CONFLICT (name) DO UPDATE SET category = EXCLUDED.category, is_debit_balance = EXCLUDED.is_debit_balance, report_type = EXCLUDED.report_type, display_order = EXCLUDED.display_order, description = EXCLUDED.description, updated_at = CURRENT_TIMESTAMP;
 
 -- ----------------------------------------------------------------------------
 -- Ensure key GL accounts for system configuration exist
 -- ----------------------------------------------------------------------------
-INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account) VALUES
-('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE, FALSE),
-('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE, FALSE),
-('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE, FALSE),
-('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE, FALSE),
-('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 'GST Payable', 1, 1, TRUE, FALSE, FALSE),
-('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 'GST Receivable', 1, 1, TRUE, FALSE, FALSE),
-('SYS-GST-CONTROL', 'System GST Control', 'Liability', 'GST Payable', 1, 1, TRUE, TRUE, FALSE),
-('1112', 'Cash on Hand', 'Asset', 'Cash and Cash Equivalents', 1,1, TRUE, FALSE, FALSE),
-('1130', 'Inventory Asset Control', 'Asset', 'Inventory', 1,1,TRUE, TRUE, FALSE)
+INSERT INTO accounting.accounts (code, name, account_type, sub_type, created_by, updated_by, is_active, is_control_account, is_bank_account, cash_flow_category) VALUES
+('1120', 'Accounts Receivable Control', 'Asset', 'Accounts Receivable', 1, 1, TRUE, TRUE, FALSE, 'Operating'),
+('2110', 'Accounts Payable Control', 'Liability', 'Accounts Payable', 1, 1, TRUE, TRUE, FALSE, 'Operating'),
+('4100', 'General Sales Revenue', 'Revenue', 'Sales', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
+('5100', 'General Cost of Goods Sold', 'Expense', 'Cost of Sales', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
+('SYS-GST-OUTPUT', 'System GST Output Tax', 'Liability', 'GST Payable', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
+('SYS-GST-INPUT', 'System GST Input Tax', 'Asset', 'GST Receivable', 1, 1, TRUE, FALSE, FALSE, 'Operating'),
+('SYS-GST-CONTROL', 'System GST Control', 'Liability', 'GST Payable', 1, 1, TRUE, TRUE, FALSE, 'Operating'),
+('1112', 'Cash on Hand', 'Asset', 'Cash and Cash Equivalents', 1,1, TRUE, FALSE, FALSE, 'Operating'),
+('1130', 'Inventory Asset Control', 'Asset', 'Inventory', 1,1,TRUE, TRUE, FALSE, 'Operating'),
+('2130', 'Withholding Tax Payable', 'Liability', 'Current Liability', 1, 1, TRUE, FALSE, FALSE, 'Operating'), -- NEW
+('7200', 'Foreign Exchange Gain', 'Revenue', 'Other Income', 1, 1, TRUE, FALSE, FALSE, 'Operating'),       -- NEW
+('8200', 'Foreign Exchange Loss', 'Expense', 'Other Expenses', 1, 1, TRUE, FALSE, FALSE, 'Operating')        -- NEW
 ON CONFLICT (code) DO NOTHING;
 
 -- ----------------------------------------------------------------------------
@@ -173,26 +169,17 @@
 ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate, is_default = EXCLUDED.is_default, is_active = EXCLUDED.is_active, updated_by = EXCLUDED.updated_by, affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;
 INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
 ('BL', 'Blocked Input Tax (9%)', 'GST', 9.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
-INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
-('NR', 'Non-Resident Services', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
-INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
-('ND', 'Non-Deductible', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
-INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id) VALUES
-('CA', 'Capital Allowance', 'Income Tax', 0.00, FALSE, TRUE, 1, 1, NULL) ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, updated_by = EXCLUDED.updated_by, updated_at = CURRENT_TIMESTAMP;
+INSERT INTO accounting.tax_codes (code, description, tax_type, rate, is_default, is_active, created_by, updated_by, affects_account_id)
+SELECT 'WHT15', 'WHT - Non-Resident Director Fee', 'Withholding Tax', 15.00, FALSE, TRUE, 1, 1, acc.id FROM accounting.accounts acc WHERE acc.code = '2130'
+ON CONFLICT (code) DO UPDATE SET description = EXCLUDED.description, tax_type = EXCLUDED.tax_type, rate = EXCLUDED.rate, updated_by = EXCLUDED.updated_by, affects_account_id = EXCLUDED.affects_account_id, updated_at = CURRENT_TIMESTAMP;
 
 -- ----------------------------------------------------------------------------
--- Create an active 'admin' user for application login
+-- Create 'admin' user and assign 'Administrator' role
 -- ----------------------------------------------------------------------------
 INSERT INTO core.users (username, password_hash, email, full_name, is_active, require_password_change)
 VALUES ('admin', crypt('password', gen_salt('bf')), 'admin@sgbookkeeper.com', 'Administrator', TRUE, TRUE)
-ON CONFLICT (username) DO UPDATE SET
-    password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name,
-    is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change,
-    updated_at = CURRENT_TIMESTAMP;
+ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash, email = EXCLUDED.email, full_name = EXCLUDED.full_name, is_active = EXCLUDED.is_active, require_password_change = EXCLUDED.require_password_change, updated_at = CURRENT_TIMESTAMP;
 
--- ----------------------------------------------------------------------------
--- Assign 'Administrator' role to 'admin' user
--- ----------------------------------------------------------------------------
 WITH admin_user_id_cte AS (SELECT id FROM core.users WHERE username = 'admin'),
      admin_role_id_cte AS (SELECT id FROM core.roles WHERE name = 'Administrator')
 INSERT INTO core.user_roles (user_id, role_id, created_at)
@@ -200,13 +187,8 @@
 WHERE admin_user_id_cte.id IS NOT NULL AND admin_role_id_cte.id IS NOT NULL
 ON CONFLICT (user_id, role_id) DO NOTHING;
 
--- ----------------------------------------------------------------------------
--- For all permissions, grant them to the 'Administrator' role
--- ----------------------------------------------------------------------------
 INSERT INTO core.role_permissions (role_id, permission_id, created_at)
-SELECT r.id, p.id, CURRENT_TIMESTAMP
-FROM core.roles r, core.permissions p
-WHERE r.name = 'Administrator'
+SELECT r.id, p.id, CURRENT_TIMESTAMP FROM core.roles r, core.permissions p WHERE r.name = 'Administrator'
 ON CONFLICT (role_id, permission_id) DO NOTHING;
 
 -- ----------------------------------------------------------------------------
```

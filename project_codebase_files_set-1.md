# pyvenv.cfg
```cfg
home = /usr/bin
include-system-site-packages = false
version = 3.12.3
executable = /usr/bin/python3.12
command = /usr/bin/python3 -m venv /cdrom/project/SG-Bookkeeper

```

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

# /home/pete/.config/SGBookkeeper/config.ini
```ini
[Database]
username = sgbookkeeper_user
password = SGkeeperPass123
host = localhost
port = 5432
database = sg_bookkeeper
echo_sql = False
pool_min_size = 2
pool_max_size = 10
pool_recycle_seconds = 3600

[Application]
theme = light
language = en
last_opened_company_id = 


```

# app/main.py
```py
# File: app/main.py
import sys
import asyncio
import threading
import time 
from pathlib import Path
from typing import Optional, Any # Any for the error object in signal

from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox, QCheckBox 
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication, QMetaObject, Signal, Slot, Q_ARG 
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
            # This stop might be called from another thread via call_soon_threadsafe
            # loop.stop() will make run_forever() return.
             pass # Loop stopping is handled in actual_shutdown_sequence
        if _ASYNC_LOOP: 
             _ASYNC_LOOP.close() # Close the loop after it has stopped
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
    # Signal: success (bool), result_or_error (Any - ApplicationCore on success, Exception on error)
    initialization_done_signal = Signal(bool, object) 

    def __init__(self, argv):
        super().__init__(argv)
        
        self.setApplicationName("SGBookkeeper")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("SGBookkeeperOrg") 
        self.setOrganizationDomain("sgbookkeeper.org") 
        
        splash_pixmap = None
        try:
            import app.resources_rc 
            splash_pixmap = QPixmap(":/images/splash.png")
            print("Using compiled Qt resources.")
        except ImportError:
            print("Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
            base_path = Path(__file__).resolve().parent.parent 
            splash_image_path = base_path / "resources" / "images" / "splash.png"
            if splash_image_path.exists():
                splash_pixmap = QPixmap(str(splash_image_path))
            else:
                print(f"Warning: Splash image not found at {splash_image_path}. Using fallback.")

        if splash_pixmap is None or splash_pixmap.isNull():
            print("Warning: Splash image not found or invalid. Using fallback.")
            self.splash = QSplashScreen()
            pm = QPixmap(400,200); pm.fill(Qt.GlobalColor.lightGray)
            self.splash.setPixmap(pm)
            self.splash.showMessage("Loading SG Bookkeeper...", Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, Qt.GlobalColor.black)
        else:
            self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
            self.splash.setObjectName("SplashScreen")

        self.splash.show()
        self.processEvents() 
        
        self.main_window: Optional[MainWindow] = None # Type hint
        self.app_core: Optional[ApplicationCore] = None # Type hint

        self.initialization_done_signal.connect(self._on_initialization_done)
        
        future = schedule_task_from_qt(self.initialize_app())
        if future is None:
            self._on_initialization_done(False, RuntimeError("Failed to schedule app initialization (async loop not ready)."))
            
    @Slot(bool, object)
    def _on_initialization_done(self, success: bool, result_or_error: Any):
        if success:
            self.app_core = result_or_error # result_or_error is app_core instance on success
            if not self.app_core: # Should not happen if success is True
                 QMessageBox.critical(None, "Fatal Error", "App core not received on successful initialization.")
                 self.quit()
                 return

            self.main_window = MainWindow(self.app_core) 
            self.main_window.show()
            self.splash.finish(self.main_window)
        else:
            self.splash.hide()
            # self.main_window is None here, so no need to hide it
            
            error_message = str(result_or_error) if result_or_error else "An unknown error occurred during initialization."
            print(f"Critical error during application startup: {error_message}") 
            if isinstance(result_or_error, Exception) and result_or_error.__traceback__:
                import traceback
                traceback.print_exception(type(result_or_error), result_or_error, result_or_error.__traceback__)

            QMessageBox.critical(None, "Application Initialization Error", 
                                 f"An error occurred during application startup:\n{error_message[:500]}\n\nThe application will now exit.")
            self.quit()

    async def initialize_app(self):
        # This coroutine now runs in the dedicated asyncio thread (_ASYNC_LOOP)
        current_app_core = None
        try:
            def update_splash_threadsafe(message):
                if hasattr(self, 'splash') and self.splash:
                    # QColor needs to be imported where Q_ARG is used, or passed as an object
                    QMetaObject.invokeMethod(self.splash, "showMessage", Qt.ConnectionType.QueuedConnection,
                                             Q_ARG(str, message),
                                             Q_ARG(int, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter),
                                             Q_ARG(QColor, QColor(Qt.GlobalColor.white)))
            
            update_splash_threadsafe("Loading configuration...")
            
            config_manager = ConfigManager(app_name=QCoreApplication.applicationName())

            update_splash_threadsafe("Initializing database manager...")
            db_manager = DatabaseManager(config_manager)
            
            update_splash_threadsafe("Initializing application core...")
            # Store app_core locally in this async method first
            current_app_core = ApplicationCore(config_manager, db_manager)

            await current_app_core.startup() 

            if not current_app_core.current_user: 
                authenticated_user = await current_app_core.security_manager.authenticate_user("admin", "password")
                if not authenticated_user:
                    print("Default admin/password authentication failed or no such user. MainWindow should handle login.")

            update_splash_threadsafe("Finalizing initialization...")
            
            # MainWindow creation will be done in the main thread via the signal
            self.initialization_done_signal.emit(True, current_app_core) 

        except Exception as e:
            self.initialization_done_signal.emit(False, e) 


    def actual_shutdown_sequence(self): 
        print("Application shutting down (actual_shutdown_sequence)...")
        global _ASYNC_LOOP, _ASYNC_LOOP_THREAD
        
        # app_core is now set on self by _on_initialization_done
        if self.app_core:
            print("Scheduling ApplicationCore shutdown...")
            future = schedule_task_from_qt(self.app_core.shutdown())
            if future:
                try:
                    future.result(timeout=2) # Reduced timeout slightly
                    print("ApplicationCore shutdown completed.")
                except TimeoutError: 
                    print("Warning: ApplicationCore async shutdown timed out.")
                except Exception as e: 
                    print(f"Error during ApplicationCore async shutdown via future: {e}")
            else:
                print("Warning: Could not schedule ApplicationCore async shutdown task.")
        
        if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
            print("Requesting global asyncio event loop to stop...")
            _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
        
        if _ASYNC_LOOP_THREAD and _ASYNC_LOOP_THREAD.is_alive():
            print("Joining asyncio event loop thread...")
            _ASYNC_LOOP_THREAD.join(timeout=2) # Reduced timeout
            if _ASYNC_LOOP_THREAD.is_alive():
                print("Warning: Asyncio event loop thread did not terminate cleanly.")
            else:
                print("Asyncio event loop thread joined.")
        
        print("Application shutdown process finalized.")

def main():
    global _ASYNC_LOOP_THREAD, _ASYNC_LOOP_STARTED, _ASYNC_LOOP

    print("Starting global asyncio event loop thread...")
    _ASYNC_LOOP_THREAD = threading.Thread(target=start_asyncio_event_loop_thread, daemon=True, name="AsyncioLoopThread")
    _ASYNC_LOOP_THREAD.start()
    
    if not _ASYNC_LOOP_STARTED.wait(timeout=5): 
        print("Fatal: Global asyncio event loop did not start in time. Exiting.")
        sys.exit(1)
    print(f"Global asyncio event loop {_ASYNC_LOOP} confirmed running in dedicated thread.")

    try:
        import app.resources_rc 
        print("Successfully imported compiled Qt resources (resources_rc.py).")
    except ImportError:
        print("Warning: Compiled Qt resources (resources_rc.py) not found. Direct file paths will be used for icons/images.")
        print("Consider running from project root: pyside6-rcc resources/resources.qrc -o app/resources_rc.py")

    app = Application(sys.argv)
    # Connect aboutToQuit to actual_shutdown_sequence AFTER app object is created
    app.aboutToQuit.connect(app.actual_shutdown_sequence) 
    
    exit_code = app.exec()
    
    # Ensure loop is stopped and thread joined if aboutToQuit didn't run
    # This fallback is less critical if aboutToQuit is robustly connected
    if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
        print("Post app.exec(): Forcing asyncio loop stop (fallback).")
        _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
    if _ASYNC_LOOP_THREAD and _ASYNC_LOOP_THREAD.is_alive():
        print("Post app.exec(): Joining asyncio thread (fallback).")
        _ASYNC_LOOP_THREAD.join(timeout=1)
            
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

```

# app/__init__.py
```py
# File: app/__init__.py
# (Content as previously generated, no changes needed)

```

# app/tax/__init__.py
```py
# File: app/tax/__init__.py
# (Content as previously generated, no changes needed)
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
from typing import TYPE_CHECKING 
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.account_service import AccountService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED


class IncomeTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.account_service: "AccountService" = app_core.account_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.fiscal_period_service: "FiscalPeriodService" = app_core.fiscal_period_service # type: ignore
        print("IncomeTaxManager initialized (stub).")
    
    async def calculate_provisional_tax(self, fiscal_year_id: int):
        print(f"Calculating provisional tax for fiscal year ID {fiscal_year_id} (stub).")
        return {"provisional_tax_payable": 0.00}

    async def get_form_cs_data(self, fiscal_year_id: int):
        print(f"Fetching data for Form C-S for fiscal year ID {fiscal_year_id} (stub).")
        return {"company_name": "Example Pte Ltd", "revenue": 100000.00, "profit_before_tax": 20000.00}

```

# app/tax/gst_manager.py
```py
# File: app/tax/gst_manager.py
from typing import Optional, Any, TYPE_CHECKING, List, Dict
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta 
from decimal import Decimal

# REMOVED: from app.services.tax_service import TaxCodeService, GSTReturnService 
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.services.fiscal_period_service import FiscalPeriodService
# REMOVED: from app.services.core_services import CompanySettingsService 
from app.utils.result import Result
from app.utils.pydantic_models import GSTReturnData, JournalEntryData, JournalEntryLineData, GSTTransactionLineDetail
from app.models.accounting.gst_return import GSTReturn 
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine # Keep specific model imports
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.common.enums import GSTReturnStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.utils.sequence_generator import SequenceGenerator
    from app.services.tax_service import TaxCodeService, GSTReturnService # ADDED
    from app.services.account_service import AccountService # ADDED
    from app.services.fiscal_period_service import FiscalPeriodService # ADDED
    from app.services.core_services import CompanySettingsService # ADDED


class GSTManager:
    def __init__(self, 
                 tax_code_service: "TaxCodeService", 
                 journal_service: "JournalService", 
                 company_settings_service: "CompanySettingsService", 
                 gst_return_service: "GSTReturnService",
                 account_service: "AccountService", 
                 fiscal_period_service: "FiscalPeriodService", 
                 sequence_generator: "SequenceGenerator", 
                 app_core: "ApplicationCore"): 
        self.tax_code_service = tax_code_service
        self.journal_service = journal_service
        self.company_settings_service = company_settings_service
        self.gst_return_service = gst_return_service
        self.account_service = account_service 
        self.fiscal_period_service = fiscal_period_service 
        self.sequence_generator = sequence_generator
        self.app_core = app_core

    async def prepare_gst_return_data(self, start_date: date, end_date: date, user_id: int) -> Result[GSTReturnData]:
        company_settings = await self.company_settings_service.get_company_settings()
        if not company_settings:
            return Result.failure(["Company settings not found."])

        std_rated_supplies = Decimal('0.00') 
        zero_rated_supplies = Decimal('0.00')  
        exempt_supplies = Decimal('0.00')     
        taxable_purchases = Decimal('0.00')   
        output_tax_calc = Decimal('0.00') 
        input_tax_calc = Decimal('0.00')  
        
        detailed_breakdown: Dict[str, List[GSTTransactionLineDetail]] = {
            "box1_standard_rated_supplies": [], "box2_zero_rated_supplies": [],
            "box3_exempt_supplies": [], "box5_taxable_purchases": [],
            "box6_output_tax_details": [], "box7_input_tax_details": []
        }
        
        posted_entries: List[JournalEntry] = await self.journal_service.get_posted_entries_by_date_range(start_date, end_date)

        for entry in posted_entries:
            for line in entry.lines:
                if not line.account or not line.tax_code_obj: continue

                account_orm: Account = line.account
                tax_code_orm: TaxCode = line.tax_code_obj
                
                line_net_value_for_gst_box: Decimal = Decimal('0.00')
                if account_orm.account_type == 'Revenue':
                    line_net_value_for_gst_box = line.credit_amount - line.debit_amount 
                elif account_orm.account_type in ['Expense', 'Asset']:
                    line_net_value_for_gst_box = line.debit_amount - line.credit_amount 

                if tax_code_orm.tax_type != 'GST' or abs(line_net_value_for_gst_box) < Decimal('0.01') and abs(line.tax_amount) < Decimal('0.01'):
                    continue

                transaction_detail = GSTTransactionLineDetail(
                    transaction_date=entry.entry_date,
                    document_no=entry.reference or entry.entry_no, 
                    entity_name=None, 
                    description=line.description or entry.description or "N/A",
                    account_code=account_orm.code,
                    account_name=account_orm.name,
                    net_amount=line_net_value_for_gst_box.quantize(Decimal("0.01")),
                    gst_amount=line.tax_amount.quantize(Decimal("0.01")),
                    tax_code_applied=tax_code_orm.code
                )

                if account_orm.account_type == 'Revenue':
                    if tax_code_orm.code == 'SR': 
                        std_rated_supplies += line_net_value_for_gst_box
                        output_tax_calc += line.tax_amount
                        detailed_breakdown["box1_standard_rated_supplies"].append(transaction_detail)
                        if line.tax_amount != Decimal(0):
                             detailed_breakdown["box6_output_tax_details"].append(transaction_detail)
                    elif tax_code_orm.code == 'ZR': 
                        zero_rated_supplies += line_net_value_for_gst_box
                        detailed_breakdown["box2_zero_rated_supplies"].append(transaction_detail)
                    elif tax_code_orm.code == 'ES': 
                        exempt_supplies += line_net_value_for_gst_box
                        detailed_breakdown["box3_exempt_supplies"].append(transaction_detail)
                    
                elif account_orm.account_type in ['Expense', 'Asset']:
                    if tax_code_orm.code == 'TX': 
                        taxable_purchases += line_net_value_for_gst_box
                        input_tax_calc += line.tax_amount
                        detailed_breakdown["box5_taxable_purchases"].append(transaction_detail)
                        if line.tax_amount != Decimal(0):
                            detailed_breakdown["box7_input_tax_details"].append(transaction_detail)
                    elif tax_code_orm.code == 'BL': 
                        taxable_purchases += line_net_value_for_gst_box
                        detailed_breakdown["box5_taxable_purchases"].append(transaction_detail)
        
        total_supplies = std_rated_supplies + zero_rated_supplies + exempt_supplies
        tax_payable = output_tax_calc - input_tax_calc 

        temp_due_date = end_date + relativedelta(months=1)
        filing_due_date = temp_due_date + relativedelta(day=31) 

        return_data = GSTReturnData(
            return_period=f"{start_date.strftime('%d%m%Y')}-{end_date.strftime('%d%m%Y')}",
            start_date=start_date, end_date=end_date,
            filing_due_date=filing_due_date,
            standard_rated_supplies=std_rated_supplies.quantize(Decimal("0.01")),
            zero_rated_supplies=zero_rated_supplies.quantize(Decimal("0.01")),
            exempt_supplies=exempt_supplies.quantize(Decimal("0.01")),
            total_supplies=total_supplies.quantize(Decimal("0.01")), 
            taxable_purchases=taxable_purchases.quantize(Decimal("0.01")), 
            output_tax=output_tax_calc.quantize(Decimal("0.01")), 
            input_tax=input_tax_calc.quantize(Decimal("0.01")),   
            tax_adjustments=Decimal(0),
            tax_payable=tax_payable.quantize(Decimal("0.01")), 
            status=GSTReturnStatusEnum.DRAFT.value,
            user_id=user_id,
            detailed_breakdown=detailed_breakdown
        )
        return Result.success(return_data)

    async def save_gst_return(self, gst_return_data: GSTReturnData) -> Result[GSTReturn]:
        current_user_id = gst_return_data.user_id
        orm_return: GSTReturn
        core_data_dict = gst_return_data.model_dump(exclude={'id', 'user_id', 'detailed_breakdown'}, exclude_none=True)

        if gst_return_data.id: 
            existing_return = await self.gst_return_service.get_by_id(gst_return_data.id)
            if not existing_return:
                return Result.failure([f"GST Return with ID {gst_return_data.id} not found for update."])
            orm_return = existing_return
            for key, value in core_data_dict.items():
                if hasattr(orm_return, key):
                    setattr(orm_return, key, value)
            orm_return.updated_by_user_id = current_user_id
        else: 
            orm_return = GSTReturn(
                **core_data_dict,
                created_by_user_id=current_user_id,
                updated_by_user_id=current_user_id
            )
            if not orm_return.filing_due_date and orm_return.end_date: 
                 temp_due_date = orm_return.end_date + relativedelta(months=1)
                 orm_return.filing_due_date = temp_due_date + relativedelta(day=31)
        try:
            saved_return = await self.gst_return_service.save_gst_return(orm_return)
            return Result.success(saved_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save GST return: {str(e)}"])

    async def finalize_gst_return(self, return_id: int, submission_reference: str, submission_date: date, user_id: int) -> Result[GSTReturn]:
        gst_return = await self.gst_return_service.get_by_id(return_id)
        if not gst_return:
            return Result.failure([f"GST Return ID {return_id} not found."])
        if gst_return.status != GSTReturnStatusEnum.DRAFT.value:
            return Result.failure([f"GST Return must be in Draft status to be finalized. Current status: {gst_return.status}"])

        gst_return.status = GSTReturnStatusEnum.SUBMITTED.value
        gst_return.submission_date = submission_date
        gst_return.submission_reference = submission_reference
        gst_return.updated_by_user_id = user_id

        if gst_return.tax_payable != Decimal(0):
            gst_output_tax_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultGSTOutput", "SYS-GST-OUTPUT")
            gst_input_tax_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_DefaultGSTInput", "SYS-GST-INPUT")
            gst_control_acc_code = await self.app_core.configuration_service.get_config_value("SysAcc_GSTControl", "SYS-GST-CONTROL")
            
            output_tax_acc = await self.account_service.get_by_code(gst_output_tax_acc_code) # type: ignore
            input_tax_acc = await self.account_service.get_by_code(gst_input_tax_acc_code) # type: ignore
            control_acc = await self.account_service.get_by_code(gst_control_acc_code) if gst_control_acc_code else None # type: ignore

            if not (output_tax_acc and input_tax_acc and control_acc):
                missing_accs = []
                if not output_tax_acc: missing_accs.append(str(gst_output_tax_acc_code))
                if not input_tax_acc: missing_accs.append(str(gst_input_tax_acc_code))
                if not control_acc: missing_accs.append(str(gst_control_acc_code))
                error_msg = f"Essential GST GL accounts not found: {', '.join(missing_accs)}. Cannot create settlement journal entry."
                self.app_core.logger.error(error_msg) # type: ignore
                try:
                    updated_return_no_je = await self.gst_return_service.save_gst_return(gst_return)
                    return Result.failure([f"GST Return finalized (ID: {updated_return_no_je.id}), but JE creation failed: " + error_msg])
                except Exception as e_save:
                    return Result.failure([f"Failed to finalize GST return and also failed to save it before JE creation: {str(e_save)}"] + [error_msg])

            lines: List[JournalEntryLineData] = []
            desc_period = f"GST for period {gst_return.start_date.strftime('%d/%m/%y')}-{gst_return.end_date.strftime('%d/%m/%y')}"
            
            if gst_return.output_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=output_tax_acc.id, debit_amount=gst_return.output_tax, credit_amount=Decimal(0), description=f"Clear Output Tax - {desc_period}"))
            if gst_return.input_tax != Decimal(0):
                 lines.append(JournalEntryLineData(account_id=input_tax_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.input_tax, description=f"Clear Input Tax - {desc_period}"))
            
            if gst_return.tax_payable > Decimal(0): 
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=Decimal(0), credit_amount=gst_return.tax_payable, description=f"GST Payable - {desc_period}"))
            elif gst_return.tax_payable < Decimal(0): 
                lines.append(JournalEntryLineData(account_id=control_acc.id, debit_amount=abs(gst_return.tax_payable), credit_amount=Decimal(0), description=f"GST Refundable - {desc_period}"))
            
            if lines:
                if not hasattr(self.app_core, 'journal_entry_manager') or not self.app_core.journal_entry_manager:
                    return Result.failure(["Journal Entry Manager not available in Application Core. Cannot create GST settlement JE."])

                je_data = JournalEntryData(
                    journal_type="General", entry_date=submission_date, 
                    description=f"GST Settlement for period {gst_return.return_period}",
                    reference=f"GST F5 Finalized: {gst_return.submission_reference or gst_return.return_period}", 
                    user_id=user_id, lines=lines,
                    source_type="GSTReturnSettlement", source_id=gst_return.id
                )
                je_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.create_journal_entry(je_data) 
                if not je_result.is_success:
                    try:
                        updated_return_je_fail = await self.gst_return_service.save_gst_return(gst_return)
                        return Result.failure([f"GST Return finalized and saved (ID: {updated_return_je_fail.id}) but settlement JE creation failed."] + (je_result.errors or []))
                    except Exception as e_save_2:
                         return Result.failure([f"Failed to finalize GST return and also failed during JE creation and subsequent save: {str(e_save_2)}"] + (je_result.errors or []))
                else:
                    assert je_result.value is not None
                    gst_return.journal_entry_id = je_result.value.id
                    post_result: Result[JournalEntry] = await self.app_core.journal_entry_manager.post_journal_entry(je_result.value.id, user_id)
                    if not post_result.is_success:
                        self.app_core.logger.warning(f"GST Settlement JE (ID: {je_result.value.id}) created but failed to auto-post: {post_result.errors}") # type: ignore
        try:
            updated_return = await self.gst_return_service.save_gst_return(gst_return)
            return Result.success(updated_return)
        except Exception as e:
            self.app_core.logger.error(f"Failed to save finalized GST return: {e}", exc_info=True) # type: ignore
            return Result.failure([f"Failed to save finalized GST return: {str(e)}"])

```

# app/tax/withholding_tax_manager.py
```py
# File: app/tax/withholding_tax_manager.py
from typing import TYPE_CHECKING
# REMOVED: from app.services.tax_service import TaxCodeService

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.tax_service import TaxCodeService # ADDED

class WithholdingTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.tax_code_service: "TaxCodeService" = app_core.tax_code_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        print("WithholdingTaxManager initialized (stub).")

    async def generate_s45_form_data(self, wht_certificate_id: int):
        print(f"Generating S45 form data for WHT certificate ID {wht_certificate_id} (stub).")
        return {"s45_field_1": "data", "s45_field_2": "more_data"}

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str):
        print(f"Recording WHT payment for certificate {certificate_id} (stub).")
        return True

```

# app/tax/tax_calculator.py
```py
# File: app/tax/tax_calculator.py
from decimal import Decimal
from typing import List, Optional, Any, TYPE_CHECKING

# REMOVED: from app.services.tax_service import TaxCodeService 
from app.utils.pydantic_models import TaxCalculationResultData, TransactionTaxData, TransactionLineTaxData
from app.models.accounting.tax_code import TaxCode as TaxCodeModel

if TYPE_CHECKING:
    from app.services.tax_service import TaxCodeService # ADDED

class TaxCalculator:
    def __init__(self, tax_code_service: "TaxCodeService"):
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
        
        tax_code_info: Optional[TaxCodeModel] = await self.tax_code_service.get_tax_code(tax_code_str) # Use TYPE_CHECKING for TaxCodeModel
        if not tax_code_info:
            return result 
        
        if tax_code_info.tax_type == 'GST':
            return await self._calculate_gst(amount, tax_code_info, transaction_type)
        elif tax_code_info.tax_type == 'Withholding Tax':
            return await self._calculate_withholding_tax(amount, tax_code_info, transaction_type)
        return result
    
    async def _calculate_gst(self, amount: Decimal, tax_code_info: TaxCodeModel, transaction_type: str) -> TaxCalculationResultData:
        tax_rate = Decimal(str(tax_code_info.rate))
        net_amount = amount 
        tax_amount = net_amount * tax_rate / Decimal(100)
        tax_amount = tax_amount.quantize(Decimal("0.01"))
        
        return TaxCalculationResultData(
            tax_amount=tax_amount,
            tax_account_id=tax_code_info.affects_account_id,
            taxable_amount=net_amount
        )
    
    async def _calculate_withholding_tax(self, amount: Decimal, tax_code_info: TaxCodeModel, transaction_type: str) -> TaxCalculationResultData:
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

# app/ui/customers/__init__.py
```py
# app/ui/customers/__init__.py
from .customers_widget import CustomersWidget
from .customer_dialog import CustomerDialog
from .customer_table_model import CustomerTableModel

__all__ = [
    "CustomersWidget",
    "CustomerDialog",
    "CustomerTableModel",
]

```

# app/ui/customers/customer_dialog.py
```py
# app/ui/customers/customer_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QCompleter
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QIcon
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast
from decimal import Decimal, InvalidOperation

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import CustomerCreateData, CustomerUpdateData, AppBaseModel
from app.models.business.customer import Customer
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook


if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class CustomerDialog(QDialog):
    customer_saved = Signal(int) # Emits customer ID on successful save

    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 customer_id: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_user_id = current_user_id
        self.customer_id = customer_id
        self.loaded_customer_data: Optional[Customer] = None # Store loaded ORM for pre-filling

        self._currencies_cache: List[Currency] = []
        self._receivables_accounts_cache: List[Account] = []
        
        self.setWindowTitle("Edit Customer" if self.customer_id else "Add New Customer")
        self.setMinimumWidth(550) # Adjusted width
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        # Load combo box data asynchronously
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_combo_data()))

        if self.customer_id:
            QTimer.singleShot(50, lambda: schedule_task_from_qt(self._load_existing_customer_details()))


    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        # Basic Info
        self.customer_code_edit = QLineEdit(); form_layout.addRow("Customer Code*:", self.customer_code_edit)
        self.name_edit = QLineEdit(); form_layout.addRow("Customer Name*:", self.name_edit)
        self.legal_name_edit = QLineEdit(); form_layout.addRow("Legal Name:", self.legal_name_edit)
        self.uen_no_edit = QLineEdit(); form_layout.addRow("UEN No.:", self.uen_no_edit)
        
        gst_layout = QHBoxLayout()
        self.gst_registered_check = QCheckBox("GST Registered"); gst_layout.addWidget(self.gst_registered_check)
        self.gst_no_edit = QLineEdit(); self.gst_no_edit.setPlaceholderText("GST Registration No."); gst_layout.addWidget(self.gst_no_edit)
        form_layout.addRow(gst_layout) # Add layout for GST fields

        # Contact Info
        self.contact_person_edit = QLineEdit(); form_layout.addRow("Contact Person:", self.contact_person_edit)
        self.email_edit = QLineEdit(); self.email_edit.setPlaceholderText("example@domain.com"); form_layout.addRow("Email:", self.email_edit)
        self.phone_edit = QLineEdit(); form_layout.addRow("Phone:", self.phone_edit)

        # Address Info
        self.address_line1_edit = QLineEdit(); form_layout.addRow("Address Line 1:", self.address_line1_edit)
        self.address_line2_edit = QLineEdit(); form_layout.addRow("Address Line 2:", self.address_line2_edit)
        self.postal_code_edit = QLineEdit(); form_layout.addRow("Postal Code:", self.postal_code_edit)
        self.city_edit = QLineEdit(); self.city_edit.setText("Singapore"); form_layout.addRow("City:", self.city_edit)
        self.country_edit = QLineEdit(); self.country_edit.setText("Singapore"); form_layout.addRow("Country:", self.country_edit)
        
        # Financial Info
        self.credit_terms_spin = QSpinBox(); self.credit_terms_spin.setRange(0, 365); self.credit_terms_spin.setValue(30); form_layout.addRow("Credit Terms (Days):", self.credit_terms_spin)
        self.credit_limit_edit = QLineEdit(); self.credit_limit_edit.setPlaceholderText("0.00"); form_layout.addRow("Credit Limit:", self.credit_limit_edit)
        
        self.currency_code_combo = QComboBox()
        self.currency_code_combo.setMinimumWidth(150)
        form_layout.addRow("Default Currency*:", self.currency_code_combo)
        
        self.receivables_account_combo = QComboBox()
        self.receivables_account_combo.setMinimumWidth(250)
        form_layout.addRow("A/R Account:", self.receivables_account_combo)

        # Other Info
        self.is_active_check = QCheckBox("Is Active"); self.is_active_check.setChecked(True); form_layout.addRow(self.is_active_check)
        self.customer_since_date_edit = QDateEdit(QDate.currentDate()); self.customer_since_date_edit.setCalendarPopup(True); self.customer_since_date_edit.setDisplayFormat("dd/MM/yyyy"); form_layout.addRow("Customer Since:", self.customer_since_date_edit)
        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(80); form_layout.addRow("Notes:", self.notes_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save_customer)
        self.button_box.rejected.connect(self.reject)
        self.gst_registered_check.stateChanged.connect(lambda state: self.gst_no_edit.setEnabled(state == Qt.CheckState.Checked.value))
        self.gst_no_edit.setEnabled(self.gst_registered_check.isChecked())


    async def _load_combo_data(self):
        """ Load data for Currency and Receivables Account comboboxes. """
        try:
            if self.app_core.currency_manager:
                active_currencies = await self.app_core.currency_manager.get_all_currencies() # Get all, filter active in UI if needed
                self._currencies_cache = [c for c in active_currencies if c.is_active]
            
            if self.app_core.chart_of_accounts_manager:
                # Fetch Asset accounts, ideally filtered for AR control accounts by sub_type or a flag
                ar_accounts = await self.app_core.chart_of_accounts_manager.get_accounts_for_selection(account_type="Asset", active_only=True)
                self._receivables_accounts_cache = [acc for acc in ar_accounts if acc.is_active and (acc.is_control_account or not acc.is_bank_account)] # Basic filter
            
            # Serialize data for thread-safe UI update
            currencies_json = json.dumps([{"code": c.code, "name": c.name} for c in self._currencies_cache], default=json_converter)
            accounts_json = json.dumps([{"id": acc.id, "code": acc.code, "name": acc.name} for acc in self._receivables_accounts_cache], default=json_converter)

            QMetaObject.invokeMethod(self, "_populate_combos_slot", Qt.ConnectionType.QueuedConnection, 
                                     Q_ARG(str, currencies_json), Q_ARG(str, accounts_json))
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for CustomerDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load data for dropdowns: {str(e)}")

    @Slot(str, str)
    def _populate_combos_slot(self, currencies_json: str, accounts_json: str):
        try:
            currencies_data = json.loads(currencies_json, object_hook=json_date_hook)
            accounts_data = json.loads(accounts_json, object_hook=json_date_hook)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing combo JSON data: {e}")
            QMessageBox.warning(self, "Data Error", "Error parsing dropdown data.")
            return

        # Populate Currency ComboBox
        self.currency_code_combo.clear()
        for curr in currencies_data: self.currency_code_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        
        # Populate Receivables Account ComboBox
        self.receivables_account_combo.clear()
        self.receivables_account_combo.addItem("None", 0) # Option for no specific AR account
        for acc in accounts_data: self.receivables_account_combo.addItem(f"{acc['code']} - {acc['name']}", acc['id'])
        
        # If editing, try to set current values after combos are populated
        if self.loaded_customer_data:
            self._populate_fields_from_orm(self.loaded_customer_data)


    async def _load_existing_customer_details(self):
        if not self.customer_id or not self.app_core.customer_manager: return
        self.loaded_customer_data = await self.app_core.customer_manager.get_customer_for_dialog(self.customer_id)
        if self.loaded_customer_data:
            # Data passed via QMetaObject needs to be simple types or JSON serializable
            customer_dict = {col.name: getattr(self.loaded_customer_data, col.name) for col in Customer.__table__.columns}
            # Convert Decimal and date/datetime to string for JSON
            customer_json_str = json.dumps(customer_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, customer_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Customer ID {self.customer_id} not found.")
            self.reject() # Close dialog if customer not found

    @Slot(str)
    def _populate_fields_slot(self, customer_json_str: str):
        try:
            customer_data = json.loads(customer_json_str, object_hook=json_date_hook)
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse customer data for editing."); return
        
        self._populate_fields_from_dict(customer_data)


    def _populate_fields_from_orm(self, customer_orm: Customer): # Primarily for setting combos after they are loaded
        currency_idx = self.currency_code_combo.findData(customer_orm.currency_code)
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        else: self.app_core.logger.warning(f"Loaded customer currency '{customer_orm.currency_code}' not found in active currencies combo.")

        ar_acc_idx = self.receivables_account_combo.findData(customer_orm.receivables_account_id or 0)
        if ar_acc_idx != -1: self.receivables_account_combo.setCurrentIndex(ar_acc_idx)
        elif customer_orm.receivables_account_id:
             self.app_core.logger.warning(f"Loaded customer A/R account ID '{customer_orm.receivables_account_id}' not found in combo.")


    def _populate_fields_from_dict(self, data: Dict[str, Any]):
        self.customer_code_edit.setText(data.get("customer_code", ""))
        self.name_edit.setText(data.get("name", ""))
        self.legal_name_edit.setText(data.get("legal_name", "") or "")
        self.uen_no_edit.setText(data.get("uen_no", "") or "")
        self.gst_registered_check.setChecked(data.get("gst_registered", False))
        self.gst_no_edit.setText(data.get("gst_no", "") or "")
        self.gst_no_edit.setEnabled(data.get("gst_registered", False))
        self.contact_person_edit.setText(data.get("contact_person", "") or "")
        self.email_edit.setText(data.get("email", "") or "")
        self.phone_edit.setText(data.get("phone", "") or "")
        self.address_line1_edit.setText(data.get("address_line1", "") or "")
        self.address_line2_edit.setText(data.get("address_line2", "") or "")
        self.postal_code_edit.setText(data.get("postal_code", "") or "")
        self.city_edit.setText(data.get("city", "") or "Singapore")
        self.country_edit.setText(data.get("country", "") or "Singapore")
        self.credit_terms_spin.setValue(data.get("credit_terms", 30))
        cl_val = data.get("credit_limit")
        self.credit_limit_edit.setText(f"{Decimal(str(cl_val)):.2f}" if cl_val is not None else "")
        
        # Set comboboxes - ensure they are populated first
        currency_idx = self.currency_code_combo.findData(data.get("currency_code", "SGD"))
        if currency_idx != -1: self.currency_code_combo.setCurrentIndex(currency_idx)
        
        ar_acc_id = data.get("receivables_account_id")
        ar_acc_idx = self.receivables_account_combo.findData(ar_acc_id if ar_acc_id is not None else 0)
        if ar_acc_idx != -1: self.receivables_account_combo.setCurrentIndex(ar_acc_idx)

        self.is_active_check.setChecked(data.get("is_active", True))
        cs_date = data.get("customer_since")
        self.customer_since_date_edit.setDate(QDate(cs_date) if cs_date else QDate.currentDate())
        self.notes_edit.setText(data.get("notes", "") or "")


    @Slot()
    def on_save_customer(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "No user logged in."); return

        try:
            credit_limit_val_str = self.credit_limit_edit.text().strip()
            credit_limit_decimal = Decimal(credit_limit_val_str) if credit_limit_val_str else None
        except InvalidOperation:
            QMessageBox.warning(self, "Input Error", "Invalid Credit Limit format. Please enter a valid number or leave blank."); return

        receivables_acc_id_data = self.receivables_account_combo.currentData()
        receivables_acc_id = int(receivables_acc_id_data) if receivables_acc_id_data and int(receivables_acc_id_data) != 0 else None
        
        customer_since_py_date = self.customer_since_date_edit.date().toPython()

        # Common data dictionary for DTOs
        data_dict = {
            "customer_code": self.customer_code_edit.text().strip(),
            "name": self.name_edit.text().strip(),
            "legal_name": self.legal_name_edit.text().strip() or None,
            "uen_no": self.uen_no_edit.text().strip() or None,
            "gst_registered": self.gst_registered_check.isChecked(),
            "gst_no": self.gst_no_edit.text().strip() if self.gst_registered_check.isChecked() else None,
            "contact_person": self.contact_person_edit.text().strip() or None,
            "email": self.email_edit.text().strip() or None, # Pydantic will validate EmailStr
            "phone": self.phone_edit.text().strip() or None,
            "address_line1": self.address_line1_edit.text().strip() or None,
            "address_line2": self.address_line2_edit.text().strip() or None,
            "postal_code": self.postal_code_edit.text().strip() or None,
            "city": self.city_edit.text().strip() or None,
            "country": self.country_edit.text().strip() or "Singapore",
            "credit_terms": self.credit_terms_spin.value(),
            "credit_limit": credit_limit_decimal,
            "currency_code": self.currency_code_combo.currentData() or "SGD",
            "is_active": self.is_active_check.isChecked(),
            "customer_since": customer_since_py_date,
            "notes": self.notes_edit.toPlainText().strip() or None,
            "receivables_account_id": receivables_acc_id,
            "user_id": self.current_user_id
        }

        try:
            if self.customer_id: # Update
                dto = CustomerUpdateData(id=self.customer_id, **data_dict) # type: ignore
            else: # Create
                dto = CustomerCreateData(**data_dict) # type: ignore
        except ValueError as pydantic_error: # Pydantic validation error
             QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
             return

        # Disable save button during operation
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False)

        schedule_task_from_qt(self._perform_save(dto)).add_done_callback(
            lambda _: ok_button.setEnabled(True) if ok_button else None
        )

    async def _perform_save(self, dto: CustomerCreateData | CustomerUpdateData):
        if not self.app_core.customer_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Customer Manager not available."))
            return

        result: Result[Customer]
        if isinstance(dto, CustomerUpdateData):
            result = await self.app_core.customer_manager.update_customer(dto.id, dto)
        else:
            result = await self.app_core.customer_manager.create_customer(dto)

        if result.is_success and result.value:
            action = "updated" if isinstance(dto, CustomerUpdateData) else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"Customer {action} successfully (ID: {result.value.id})."))
            self.customer_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save customer:\n{', '.join(result.errors)}"))

```

# app/ui/customers/customer_table_model.py
```py
# app/ui/customers/customer_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional

from app.utils.pydantic_models import CustomerSummaryData # Using the DTO for type safety

class CustomerTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[CustomerSummaryData]] = None, parent=None):
        super().__init__(parent)
        # Headers should match fields in CustomerSummaryData + any derived display fields
        self._headers = ["ID", "Code", "Name", "Email", "Phone", "Active"]
        self._data: List[CustomerSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
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
            
        customer_summary: CustomerSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return str(customer_summary.id)
            if col == 1: return customer_summary.customer_code
            if col == 2: return customer_summary.name
            if col == 3: return str(customer_summary.email) if customer_summary.email else ""
            if col == 4: return customer_summary.phone if customer_summary.phone else ""
            if col == 5: return "Yes" if customer_summary.is_active else "No"
            
            # Fallback for safety, though all defined headers should be covered
            header_key = self._headers[col].lower().replace(' ', '_')
            return str(getattr(customer_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            # Store the full DTO or just the ID in UserRole for easy retrieval
            # Storing ID in the first column's UserRole is common.
            if col == 0: 
                return customer_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col == 5: # Active status
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_customer_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) # Assuming ID is in/associated with the first column (model index 0)
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            # Fallback if UserRole is not used for ID or is somehow None
            return self._data[row].id 
        return None
        
    def get_customer_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None

    def update_data(self, new_data: List[CustomerSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/customers/customers_widget.py
```py
# app/ui/customers/customers_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox # Added for filtering/search
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.customers.customer_table_model import CustomerTableModel # New import
from app.ui.customers.customer_dialog import CustomerDialog # New import
from app.utils.pydantic_models import CustomerSummaryData # For type hinting
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.customer import Customer # For Result type hint from manager

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class CustomersWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for CustomersWidget.")
        except ImportError:
            self.app_core.logger.info("CustomersWidget: Compiled Qt resources not found. Using direct file paths.")
            pass
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_customers()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        # --- Toolbar ---
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        # --- Filter/Search Area ---
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter code, name, or email...")
        self.search_edit.returnPressed.connect(self.toolbar_refresh_action.trigger) # Trigger refresh on Enter
        filter_layout.addWidget(self.search_edit)

        self.show_inactive_check = QCheckBox("Show Inactive")
        self.show_inactive_check.stateChanged.connect(self.toolbar_refresh_action.trigger) # Trigger refresh on change
        filter_layout.addWidget(self.show_inactive_check)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # --- Table View ---
        self.customers_table = QTableView()
        self.customers_table.setAlternatingRowColors(True)
        self.customers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.customers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.customers_table.horizontalHeader().setStretchLastSection(True)
        self.customers_table.doubleClicked.connect(self._on_edit_customer) # Or view
        self.customers_table.setSortingEnabled(True)

        self.table_model = CustomerTableModel()
        self.customers_table.setModel(self.table_model)
        
        # Configure columns after model is set
        if "ID" in self.table_model._headers:
            self.customers_table.setColumnHidden(self.table_model._headers.index("ID"), True)
        if "Name" in self.table_model._headers:
            name_col_idx = self.table_model._headers.index("Name")
            self.customers_table.horizontalHeader().setSectionResizeMode(name_col_idx, QHeaderView.ResizeMode.Stretch)
        else: # Fallback if "Name" header changes
             self.customers_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


        self.main_layout.addWidget(self.customers_table)
        self.setLayout(self.main_layout)

        if self.customers_table.selectionModel():
            self.customers_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()


    def _create_toolbar(self):
        self.toolbar = QToolBar("Customer Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Customer", self)
        self.toolbar_add_action.triggered.connect(self._on_add_customer)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Customer", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_customer)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_customers()))
        self.toolbar.addAction(self.toolbar_refresh_action)


    @Slot()
    def _update_action_states(self):
        selected_rows = self.customers_table.selectionModel().selectedRows()
        has_selection = bool(selected_rows)
        single_selection = len(selected_rows) == 1
        
        self.toolbar_edit_action.setEnabled(single_selection)
        self.toolbar_toggle_active_action.setEnabled(single_selection)

    async def _load_customers(self):
        if not self.app_core.customer_manager:
            self.app_core.logger.error("CustomerManager not available in CustomersWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Customer Manager component not available."))
            return
        try:
            search_term = self.search_edit.text().strip() or None
            active_only = not self.show_inactive_check.isChecked()
            
            # For MVP, pagination is handled by service if params are passed. UI doesn't have page controls yet.
            result: Result[List[CustomerSummaryData]] = await self.app_core.customer_manager.get_customers_for_listing(
                active_only=active_only, 
                search_term=search_term,
                page=1, # Default to first page
                page_size=200 # Load a reasonable number for MVP table
            )
            
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                error_msg = f"Failed to load customers: {', '.join(result.errors)}"
                self.app_core.logger.error(error_msg)
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))
        except Exception as e:
            error_msg = f"Unexpected error loading customers: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            # Convert list of dicts to list of CustomerSummaryData DTOs
            customer_summaries: List[CustomerSummaryData] = [CustomerSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(customer_summaries)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse customer data: {e}")
        except Exception as p_error: # Catch Pydantic validation errors too
            QMessageBox.critical(self, "Data Error", f"Invalid customer data format: {p_error}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_customer(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to add a customer.")
            return
        
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()

    def _get_selected_customer_id(self) -> Optional[int]:
        selected_rows = self.customers_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            QMessageBox.information(self, "Selection", "Please select a single customer.")
            return None
        return self.table_model.get_customer_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_customer(self):
        customer_id = self._get_selected_customer_id()
        if customer_id is None: return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to edit a customer.")
            return
            
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, customer_id=customer_id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()
        
    @Slot(QModelIndex)
    def _on_view_customer_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        customer_id = self.table_model.get_customer_id_at_row(index.row())
        if customer_id is None: return
        # For MVP, double-click also opens for edit. Can be changed to view-only later.
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to view/edit customer.")
            return
        dialog = CustomerDialog(self.app_core, self.app_core.current_user.id, customer_id=customer_id, parent=self)
        dialog.customer_saved.connect(lambda _id: schedule_task_from_qt(self._load_customers()))
        dialog.exec()


    @Slot()
    def _on_toggle_active_status(self):
        customer_id = self._get_selected_customer_id()
        if customer_id is None: return

        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in to change customer status.")
            return
            
        # Confirm action
        customer_status_active = self.table_model.get_customer_status_at_row(self.customers_table.currentIndex().row())
        action_verb = "deactivate" if customer_status_active else "activate"
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} this customer?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        future = schedule_task_from_qt(
            self.app_core.customer_manager.toggle_customer_active_status(customer_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None)

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule customer status toggle."); return
        try:
            result: Result[Customer] = future.result()
            if result.is_success:
                action_verb_past = "activated" if result.value and result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"Customer {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_customers()) # Refresh list
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle customer status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")


```

# app/ui/purchase_invoices/__init__.py
```py
# File: app/ui/purchase_invoices/__init__.py    
from .purchase_invoice_dialog import PurchaseInvoiceDialog
from .purchase_invoice_table_model import PurchaseInvoiceTableModel # New export
from .purchase_invoices_widget import PurchaseInvoicesWidget # New export

__all__ = [
    "PurchaseInvoiceDialog",
    "PurchaseInvoiceTableModel", 
    "PurchaseInvoicesWidget",
]

```

# app/ui/purchase_invoices/purchase_invoice_dialog.py
```py
# app/ui/purchase_invoices/purchase_invoice_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QDateEdit, QComboBox, QSpinBox, QTextEdit, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QCompleter,
    QSizePolicy, QApplication, QStyledItemDelegate, QAbstractSpinBox, QLabel, QFrame,
    QGridLayout, QWidget
)
from PySide6.QtCore import Qt, QDate, Slot, Signal, QTimer, QMetaObject, Q_ARG, QModelIndex
from PySide6.QtGui import QIcon, QFont, QPalette, QColor
from typing import Optional, List, Dict, Any, TYPE_CHECKING, cast, Union
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
import json
from datetime import date as python_date

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import (
    PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData, PurchaseInvoiceLineBaseData,
    VendorSummaryData, ProductSummaryData 
)
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.models.business.product import Product 
from app.common.enums import InvoiceStatusEnum, ProductTypeEnum
from app.utils.result import Result
from app.utils.json_helpers import json_converter, json_date_hook
from app.ui.sales_invoices.sales_invoice_dialog import LineItemNumericDelegate # Re-use delegate
from app.ui.shared.product_search_dialog import ProductSearchDialog

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice, QAbstractItemModel 

class PurchaseInvoiceDialog(QDialog):
    invoice_saved = Signal(int) 

    COL_DEL = 0; COL_PROD = 1; COL_DESC = 2; COL_QTY = 3; COL_PRICE = 4
    COL_DISC_PCT = 5; COL_SUBTOTAL = 6; COL_TAX_CODE = 7; COL_TAX_AMT = 8; COL_TOTAL = 9
    
    def __init__(self, app_core: "ApplicationCore", current_user_id: int, 
                 invoice_id: Optional[int] = None, 
                 view_only: bool = False, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core; self.current_user_id = current_user_id
        self.invoice_id = invoice_id; self.view_only_mode = view_only
        self.loaded_invoice_orm: Optional[PurchaseInvoice] = None
        self.loaded_invoice_data_dict: Optional[Dict[str, Any]] = None
        self._current_search_target_row: Optional[int] = None 

        self._vendors_cache: List[Dict[str, Any]] = []
        self._products_cache: List[Dict[str, Any]] = [] 
        self._currencies_cache: List[Dict[str, Any]] = []
        self._tax_codes_cache: List[Dict[str, Any]] = []
        self._base_currency: str = "SGD" 

        self.icon_path_prefix = "resources/icons/"
        try: import app.resources_rc; self.icon_path_prefix = ":/icons/"
        except ImportError: pass
        
        self.setWindowTitle(self._get_window_title())
        self.setMinimumSize(1000, 750); self.setModal(True)
        self._init_ui(); self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_combo_data()))
        if self.invoice_id:
            QTimer.singleShot(100, lambda: schedule_task_from_qt(self._load_existing_invoice_data()))
        elif not self.view_only_mode: self._add_new_invoice_line() 

    def _get_window_title(self) -> str:
        inv_no_str = ""
        if self.loaded_invoice_orm and self.loaded_invoice_orm.invoice_no: 
            inv_no_str = f" (Ref: {self.loaded_invoice_orm.invoice_no})"
        elif self.loaded_invoice_data_dict and self.loaded_invoice_data_dict.get("invoice_no"): 
            inv_no_str = f" (Ref: {self.loaded_invoice_data_dict.get('invoice_no')})"
            
        if self.view_only_mode: return f"View Purchase Invoice{inv_no_str}"
        if self.invoice_id: return f"Edit Purchase Invoice{inv_no_str}"
        return "New Purchase Invoice"

    def _init_ui(self):
        main_layout = QVBoxLayout(self); self.header_form = QFormLayout()
        self.header_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows) 
        self.header_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vendor_combo = QComboBox(); self.vendor_combo.setEditable(True); self.vendor_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert); self.vendor_combo.setMinimumWidth(300)
        vend_completer = QCompleter(); vend_completer.setFilterMode(Qt.MatchFlag.MatchContains); vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_combo.setCompleter(vend_completer)
        
        self.our_ref_no_label = QLabel("To be generated"); self.our_ref_no_label.setStyleSheet("font-style: italic; color: grey;")
        self.vendor_invoice_no_edit = QLineEdit(); self.vendor_invoice_no_edit.setPlaceholderText("Supplier's Invoice Number")
        
        self.invoice_date_edit = QDateEdit(QDate.currentDate()); self.invoice_date_edit.setCalendarPopup(True); self.invoice_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(30)); self.due_date_edit.setCalendarPopup(True); self.due_date_edit.setDisplayFormat("dd/MM/yyyy")
        
        self.currency_combo = QComboBox()
        self.exchange_rate_spin = QDoubleSpinBox(); self.exchange_rate_spin.setDecimals(6); self.exchange_rate_spin.setRange(0.000001, 999999.0); self.exchange_rate_spin.setValue(1.0)
        
        grid_header_layout = QGridLayout()
        grid_header_layout.addWidget(QLabel("Vendor*:"), 0, 0); grid_header_layout.addWidget(self.vendor_combo, 0, 1, 1, 2) 
        grid_header_layout.addWidget(QLabel("Our Ref No.:"), 0, 3); grid_header_layout.addWidget(self.our_ref_no_label, 0, 4)
        
        grid_header_layout.addWidget(QLabel("Vendor Inv No.:"), 1,0); grid_header_layout.addWidget(self.vendor_invoice_no_edit, 1,1,1,2)
        
        grid_header_layout.addWidget(QLabel("Invoice Date*:"), 2, 0); grid_header_layout.addWidget(self.invoice_date_edit, 2, 1)
        grid_header_layout.addWidget(QLabel("Due Date*:"), 2, 3); grid_header_layout.addWidget(self.due_date_edit, 2, 4)
        
        grid_header_layout.addWidget(QLabel("Currency*:"), 3, 0); grid_header_layout.addWidget(self.currency_combo, 3, 1)
        grid_header_layout.addWidget(QLabel("Exchange Rate:"), 3, 3); grid_header_layout.addWidget(self.exchange_rate_spin, 3, 4)
        
        grid_header_layout.setColumnStretch(2,1) 
        grid_header_layout.setColumnStretch(5,1) 
        main_layout.addLayout(grid_header_layout)

        self.notes_edit = QTextEdit(); self.notes_edit.setFixedHeight(60); self.header_form.addRow("Notes:", self.notes_edit)
        main_layout.addLayout(self.header_form) 

        self.lines_table = QTableWidget(); self.lines_table.setColumnCount(self.COL_TOTAL + 1) 
        self.lines_table.setHorizontalHeaderLabels(["", "Product/Service", "Description", "Qty*", "Unit Price*", "Disc %", "Subtotal", "Tax", "Tax Amt", "Total"])
        self._configure_lines_table_columns(); main_layout.addWidget(self.lines_table)
        lines_button_layout = QHBoxLayout()
        self.add_line_button = QPushButton(QIcon(self.icon_path_prefix + "add.svg"), "Add Line")
        self.remove_line_button = QPushButton(QIcon(self.icon_path_prefix + "remove.svg"), "Remove Line")
        lines_button_layout.addWidget(self.add_line_button); lines_button_layout.addWidget(self.remove_line_button); lines_button_layout.addStretch()
        main_layout.addLayout(lines_button_layout)

        totals_form = QFormLayout(); totals_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows); totals_form.setStyleSheet("QLabel { font-weight: bold; } QLineEdit { font-weight: bold; }")
        self.subtotal_display = QLineEdit("0.00"); self.subtotal_display.setReadOnly(True); self.subtotal_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_tax_display = QLineEdit("0.00"); self.total_tax_display.setReadOnly(True); self.total_tax_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.grand_total_display = QLineEdit("0.00"); self.grand_total_display.setReadOnly(True); self.grand_total_display.setAlignment(Qt.AlignmentFlag.AlignRight); self.grand_total_display.setStyleSheet("font-weight: bold; font-size: 14pt;")
        totals_form.addRow("Subtotal:", self.subtotal_display); totals_form.addRow("Total Tax:", self.total_tax_display); totals_form.addRow("Grand Total:", self.grand_total_display)
        align_totals_layout = QHBoxLayout(); align_totals_layout.addStretch(); align_totals_layout.addLayout(totals_form)
        main_layout.addLayout(align_totals_layout)
        
        self.button_box = QDialogButtonBox()
        self.save_draft_button = self.button_box.addButton("Save Draft", QDialogButtonBox.ButtonRole.ActionRole)
        self.save_approve_button = self.button_box.addButton("Save & Approve", QDialogButtonBox.ButtonRole.ActionRole) 
        self.save_approve_button.setToolTip("Save purchase invoice and mark as Approved (posts Journal Entry).")
        self.save_approve_button.setEnabled(False) 
        self.button_box.addButton(QDialogButtonBox.StandardButton.Close if self.view_only_mode else QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box); self.setLayout(main_layout)

    def _configure_lines_table_columns(self): 
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(self.COL_DEL, QHeaderView.ResizeMode.Fixed); self.lines_table.setColumnWidth(self.COL_DEL, 30)
        header.setSectionResizeMode(self.COL_PROD, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_PROD, 250)
        header.setSectionResizeMode(self.COL_DESC, QHeaderView.ResizeMode.Stretch) 
        for col in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,100)
        for col in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]: 
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(col,120)
        header.setSectionResizeMode(self.COL_TAX_CODE, QHeaderView.ResizeMode.Interactive); self.lines_table.setColumnWidth(self.COL_TAX_CODE, 150)
        
        self.lines_table.setItemDelegateForColumn(self.COL_QTY, LineItemNumericDelegate(2, self))
        self.lines_table.setItemDelegateForColumn(self.COL_PRICE, LineItemNumericDelegate(4, self)) 
        self.lines_table.setItemDelegateForColumn(self.COL_DISC_PCT, LineItemNumericDelegate(2, False, 100.00, self))

    def _connect_signals(self):
        self.add_line_button.clicked.connect(self._add_new_invoice_line)
        self.remove_line_button.clicked.connect(self._remove_selected_invoice_line)
        self.lines_table.itemChanged.connect(self._on_line_item_changed_desc_only) 
        
        self.save_draft_button.clicked.connect(self.on_save_draft)
        self.save_approve_button.clicked.connect(self.on_save_and_approve)
        
        close_button = self.button_box.button(QDialogButtonBox.StandardButton.Close)
        cancel_button = self.button_box.button(QDialogButtonBox.StandardButton.Cancel)
        if close_button: close_button.clicked.connect(self.reject)
        if cancel_button: cancel_button.clicked.connect(self.reject)

        self.vendor_combo.currentIndexChanged.connect(self._on_vendor_changed)
        self.currency_combo.currentIndexChanged.connect(self._on_currency_changed)
        self.invoice_date_edit.dateChanged.connect(self._on_invoice_date_changed)

    async def _load_initial_combo_data(self):
        try:
            cs_svc = self.app_core.company_settings_service
            if cs_svc: settings = await cs_svc.get_company_settings(); self._base_currency = settings.base_currency if settings else "SGD"

            vend_res: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1)
            self._vendors_cache = [vs.model_dump() for vs in vend_res.value] if vend_res.is_success and vend_res.value else []
            
            prod_res: Result[List[ProductSummaryData]] = await self.app_core.product_manager.get_products_for_listing(active_only=True, page_size=-1) 
            self._products_cache = [ps.model_dump() for ps in prod_res.value] if prod_res.is_success and prod_res.value else []

            if self.app_core.currency_manager:
                curr_orms = await self.app_core.currency_manager.get_all_currencies()
                self._currencies_cache = [{"code":c.code, "name":c.name} for c in curr_orms if c.is_active]
            
            if self.app_core.tax_code_service:
                tc_orms = await self.app_core.tax_code_service.get_all() 
                self._tax_codes_cache = [{"code":tc.code, "rate":tc.rate, "description":f"{tc.code} ({tc.rate:.0f}%)"} for tc in tc_orms if tc.is_active]

            QMetaObject.invokeMethod(self, "_populate_initial_combos_slot", Qt.ConnectionType.QueuedConnection)
        except Exception as e:
            self.app_core.logger.error(f"Error loading combo data for PurchaseInvoiceDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load initial data for dropdowns: {str(e)}")

    @Slot()
    def _populate_initial_combos_slot(self):
        self.vendor_combo.clear(); self.vendor_combo.addItem("-- Select Vendor --", 0)
        for vend in self._vendors_cache: self.vendor_combo.addItem(f"{vend['vendor_code']} - {vend['name']}", vend['id'])
        if isinstance(self.vendor_combo.completer(), QCompleter): self.vendor_combo.completer().setModel(self.vendor_combo.model()) 

        self.currency_combo.clear()
        for curr in self._currencies_cache: self.currency_combo.addItem(f"{curr['code']} - {curr['name']}", curr['code'])
        base_curr_idx = self.currency_combo.findData(self._base_currency)
        if base_curr_idx != -1: self.currency_combo.setCurrentIndex(base_curr_idx)
        elif self._currencies_cache : self.currency_combo.setCurrentIndex(0) 
        self._on_currency_changed(self.currency_combo.currentIndex()) 

        if self.loaded_invoice_orm: self._populate_fields_from_orm(self.loaded_invoice_orm)
        elif self.loaded_invoice_data_dict: self._populate_fields_from_dict(self.loaded_invoice_data_dict)
        
        for r in range(self.lines_table.rowCount()): self._populate_line_combos(r)

    async def _load_existing_invoice_data(self):
        if not self.invoice_id or not self.app_core.purchase_invoice_manager: return
        self.loaded_invoice_orm = await self.app_core.purchase_invoice_manager.get_invoice_for_dialog(self.invoice_id)
        self.setWindowTitle(self._get_window_title()) 
        if self.loaded_invoice_orm:
            inv_dict = {col.name: getattr(self.loaded_invoice_orm, col.name) for col in PurchaseInvoice.__table__.columns if hasattr(self.loaded_invoice_orm, col.name)}
            inv_dict["lines"] = []
            if self.loaded_invoice_orm.lines: 
                for line_orm in self.loaded_invoice_orm.lines:
                    line_dict = {col.name: getattr(line_orm, col.name) for col in PurchaseInvoiceLine.__table__.columns if hasattr(line_orm, col.name)}
                    inv_dict["lines"].append(line_dict)
            
            invoice_json_str = json.dumps(inv_dict, default=json_converter)
            QMetaObject.invokeMethod(self, "_populate_dialog_from_data_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, invoice_json_str))
        else:
            QMessageBox.warning(self, "Load Error", f"Purchase Invoice ID {self.invoice_id} not found.")
            self.reject()

    @Slot(str)
    def _populate_dialog_from_data_slot(self, invoice_json_str: str):
        try:
            data = json.loads(invoice_json_str, object_hook=json_date_hook)
            self.loaded_invoice_data_dict = data 
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse existing purchase invoice data."); return

        self.our_ref_no_label.setText(data.get("invoice_no", "N/A")) 
        self.our_ref_no_label.setStyleSheet("font-style: normal; color: black;" if data.get("invoice_no") else "font-style: italic; color: grey;")
        self.vendor_invoice_no_edit.setText(data.get("vendor_invoice_no", "") or "")
        
        if data.get("invoice_date"): self.invoice_date_edit.setDate(QDate(data["invoice_date"]))
        if data.get("due_date"): self.due_date_edit.setDate(QDate(data["due_date"]))
        
        vend_idx = self.vendor_combo.findData(data.get("vendor_id"))
        if vend_idx != -1: self.vendor_combo.setCurrentIndex(vend_idx)
        
        curr_idx = self.currency_combo.findData(data.get("currency_code"))
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
        self.exchange_rate_spin.setValue(float(data.get("exchange_rate", 1.0) or 1.0))
        self._on_currency_changed(self.currency_combo.currentIndex()) 

        self.notes_edit.setText(data.get("notes", "") or "")
        
        self.lines_table.setRowCount(0) 
        for line_data_dict in data.get("lines", []): self._add_new_invoice_line(line_data_dict)
        if not data.get("lines") and not self.view_only_mode: self._add_new_invoice_line()
        
        self._update_invoice_totals() 
        self._set_read_only_state(self.view_only_mode or (data.get("status") != InvoiceStatusEnum.DRAFT.value))

    def _populate_fields_from_orm(self, invoice_orm: PurchaseInvoice): 
        vend_idx = self.vendor_combo.findData(invoice_orm.vendor_id)
        if vend_idx != -1: self.vendor_combo.setCurrentIndex(vend_idx)
        curr_idx = self.currency_combo.findData(invoice_orm.currency_code)
        if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
    
    def _set_read_only_state(self, read_only: bool):
        self.vendor_combo.setEnabled(not read_only)
        self.vendor_invoice_no_edit.setReadOnly(read_only)
        for w in [self.invoice_date_edit, self.due_date_edit, self.notes_edit]:
            if hasattr(w, 'setReadOnly'): w.setReadOnly(read_only) 
        self.currency_combo.setEnabled(not read_only)
        self._on_currency_changed(self.currency_combo.currentIndex()) 
        if read_only: self.exchange_rate_spin.setReadOnly(True)

        self.add_line_button.setEnabled(not read_only)
        self.remove_line_button.setEnabled(not read_only)
        
        is_draft = True 
        if self.loaded_invoice_data_dict:
            is_draft = (self.loaded_invoice_data_dict.get("status") == InvoiceStatusEnum.DRAFT.value)
        elif self.loaded_invoice_orm:
            is_draft = (self.loaded_invoice_orm.status == InvoiceStatusEnum.DRAFT.value)

        can_edit_or_create = not self.view_only_mode and (self.invoice_id is None or is_draft)

        self.save_draft_button.setVisible(can_edit_or_create)
        self.save_approve_button.setVisible(can_edit_or_create)
        self.save_approve_button.setEnabled(False) # Always false for PI for now

        edit_trigger = QAbstractItemView.EditTrigger.NoEditTriggers if read_only else QAbstractItemView.EditTrigger.AllInputs
        self.lines_table.setEditTriggers(edit_trigger)
        for r in range(self.lines_table.rowCount()):
            del_btn_widget = self.lines_table.cellWidget(r, self.COL_DEL)
            if del_btn_widget: del_btn_widget.setEnabled(not read_only)
            
            prod_cell_widget = self.lines_table.cellWidget(r, self.COL_PROD)
            if isinstance(prod_cell_widget, QWidget):
                search_button = prod_cell_widget.findChild(QPushButton)
                if search_button: search_button.setEnabled(not read_only)
                combo = prod_cell_widget.findChild(QComboBox)
                if combo: combo.setEnabled(not read_only)

    def _add_new_invoice_line(self, line_data: Optional[Dict[str, Any]] = None):
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)

        del_btn = QPushButton(QIcon(self.icon_path_prefix + "remove.svg")); del_btn.setFixedSize(24,24); del_btn.setToolTip("Remove this line")
        del_btn.clicked.connect(lambda _, r=row: self._remove_specific_invoice_line(r))
        self.lines_table.setCellWidget(row, self.COL_DEL, del_btn)

        prod_cell_widget = QWidget()
        prod_cell_layout = QHBoxLayout(prod_cell_widget)
        prod_cell_layout.setContentsMargins(0,0,0,0); prod_cell_layout.setSpacing(2)
        prod_combo = QComboBox(); prod_combo.setEditable(True); prod_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        prod_completer = QCompleter(); prod_completer.setFilterMode(Qt.MatchFlag.MatchContains); prod_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        prod_combo.setCompleter(prod_completer)
        prod_combo.setMaxVisibleItems(15) 
        prod_search_btn = QPushButton("..."); prod_search_btn.setFixedSize(24,24); prod_search_btn.setToolTip("Search Product/Service")
        prod_search_btn.clicked.connect(lambda _, r=row: self._on_open_product_search(r))
        prod_cell_layout.addWidget(prod_combo, 1); prod_cell_layout.addWidget(prod_search_btn)
        self.lines_table.setCellWidget(row, self.COL_PROD, prod_cell_widget)
        
        desc_item = QTableWidgetItem(line_data.get("description", "") if line_data else "")
        self.lines_table.setItem(row, self.COL_DESC, desc_item) 

        qty_spin = QDoubleSpinBox(); qty_spin.setDecimals(2); qty_spin.setRange(0.01, 999999.99); qty_spin.setValue(float(line_data.get("quantity", 1.0) or 1.0) if line_data else 1.0)
        self.lines_table.setCellWidget(row, self.COL_QTY, qty_spin)
        price_spin = QDoubleSpinBox(); price_spin.setDecimals(4); price_spin.setRange(0, 999999.9999); price_spin.setValue(float(line_data.get("unit_price", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_PRICE, price_spin)
        disc_spin = QDoubleSpinBox(); disc_spin.setDecimals(2); disc_spin.setRange(0, 100.00); disc_spin.setValue(float(line_data.get("discount_percent", 0.0) or 0.0) if line_data else 0.0)
        self.lines_table.setCellWidget(row, self.COL_DISC_PCT, disc_spin)

        tax_combo = QComboBox(); self.lines_table.setCellWidget(row, self.COL_TAX_CODE, tax_combo)

        for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
            item = QTableWidgetItem("0.00"); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable); self.lines_table.setItem(row, col_idx, item)

        self._populate_line_combos(row, line_data) 
        
        prod_combo.currentIndexChanged.connect(lambda idx, r=row, pc=prod_combo: self._on_line_product_changed(r, pc.itemData(idx)))
        qty_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        price_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        disc_spin.valueChanged.connect(lambda val, r=row: self._trigger_line_recalculation_slot(r))
        tax_combo.currentIndexChanged.connect(lambda idx, r=row: self._trigger_line_recalculation_slot(r))

        if line_data: self._calculate_line_item_totals(row)
        self._update_invoice_totals()

    def _populate_line_combos(self, row: int, line_data: Optional[Dict[str, Any]] = None):
        prod_cell_widget = self.lines_table.cellWidget(row, self.COL_PROD)
        prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
        if prod_combo:
            prod_combo.clear(); prod_combo.addItem("-- Select Product/Service --", 0)
            current_prod_id = line_data.get("product_id") if line_data else None
            selected_prod_idx = 0 
            for i, prod_dict in enumerate(self._products_cache):
                price_val = prod_dict.get('purchase_price') 
                price_str = f"{Decimal(str(price_val)):.2f}" if price_val is not None else "N/A"
                prod_type_val = prod_dict.get('product_type')
                type_str = prod_type_val if isinstance(prod_type_val, str) else (prod_type_val.value if isinstance(prod_type_val, ProductTypeEnum) else "Unknown")
                display_text = f"{prod_dict['product_code']} - {prod_dict['name']} (Cost: {price_str})"
                prod_combo.addItem(display_text, prod_dict['id'])
                if prod_dict['id'] == current_prod_id: selected_prod_idx = i + 1
            prod_combo.setCurrentIndex(selected_prod_idx)
            if isinstance(prod_combo.completer(), QCompleter): prod_combo.completer().setModel(prod_combo.model())
        
        tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
        if tax_combo:
            tax_combo.clear(); tax_combo.addItem("None", "") 
            current_tax_code_str = line_data.get("tax_code") if line_data else None
            selected_tax_idx = 0 
            for i, tc_dict in enumerate(self._tax_codes_cache):
                tax_combo.addItem(tc_dict['description'], tc_dict['code']) 
                if tc_dict['code'] == current_tax_code_str: selected_tax_idx = i + 1
            tax_combo.setCurrentIndex(selected_tax_idx)

    @Slot(int)
    def _on_line_product_changed(self, row:int, product_id_data: Any): 
        if not isinstance(product_id_data, int) or product_id_data == 0: 
             self._calculate_line_item_totals(row); return

        product_id = product_id_data
        product_detail = next((p for p in self._products_cache if p['id'] == product_id), None)
        
        if product_detail:
            desc_item = self.lines_table.item(row, self.COL_DESC)
            prod_cell_widget = self.lines_table.cellWidget(row, self.COL_PROD)
            prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None

            if desc_item and prod_combo and (not desc_item.text().strip() or "-- Select Product/Service --" in prod_combo.itemText(0)):
                desc_item.setText(product_detail.get('name', ''))
            
            price_widget = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            if price_widget and price_widget.value() == 0.0 and product_detail.get('purchase_price') is not None: 
                try: price_widget.setValue(float(Decimal(str(product_detail['purchase_price']))))
                except: pass 
            
            tax_combo = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
            if tax_combo and product_detail.get('tax_code'): 
                tax_idx = tax_combo.findData(product_detail['tax_code'])
                if tax_idx != -1: tax_combo.setCurrentIndex(tax_idx)
        self._calculate_line_item_totals(row)

    def _remove_selected_invoice_line(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        current_row = self.lines_table.currentRow()
        if current_row >= 0: self._remove_specific_invoice_line(current_row)

    def _remove_specific_invoice_line(self, row:int):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): return
        self.lines_table.removeRow(row); self._update_invoice_totals()

    @Slot(QTableWidgetItem)
    def _on_line_item_changed_desc_only(self, item: QTableWidgetItem): 
        if item.column() == self.COL_DESC: pass 

    @Slot() 
    def _trigger_line_recalculation_slot(self, row_for_recalc: Optional[int] = None):
        current_row = row_for_recalc
        if current_row is None: 
            sender_widget = self.sender()
            if sender_widget and isinstance(sender_widget, QWidget):
                for r in range(self.lines_table.rowCount()):
                    for c in [self.COL_QTY, self.COL_PRICE, self.COL_DISC_PCT, self.COL_TAX_CODE, self.COL_PROD]:
                        cell_w = self.lines_table.cellWidget(r,c)
                        if isinstance(cell_w, QWidget) and cell_w.isAncestorOf(sender_widget): 
                            current_row = r; break
                        elif cell_w == sender_widget:
                            current_row = r; break
                    if current_row is not None: break
        if current_row is not None: self._calculate_line_item_totals(current_row)

    def _format_decimal_for_cell(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: return "0.00" if not show_zero_as_blank else ""
        if show_zero_as_blank and value.is_zero(): return ""
        return f"{value:,.2f}"

    def _calculate_line_item_totals(self, row: int):
        try:
            qty_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_QTY))
            price_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_PRICE))
            disc_pct_w = cast(QDoubleSpinBox, self.lines_table.cellWidget(row, self.COL_DISC_PCT))
            tax_combo_w = cast(QComboBox, self.lines_table.cellWidget(row, self.COL_TAX_CODE))
            qty = Decimal(str(qty_w.value())) if qty_w else Decimal(0); price = Decimal(str(price_w.value())) if price_w else Decimal(0)
            disc_pct = Decimal(str(disc_pct_w.value())) if disc_pct_w else Decimal(0)
            discount_amount = (qty * price * (disc_pct / Decimal(100))).quantize(Decimal("0.0001"), ROUND_HALF_UP)
            line_subtotal_before_tax = (qty * price) - discount_amount
            tax_code_str = tax_combo_w.currentData() if tax_combo_w and tax_combo_w.currentIndex() > 0 else None
            line_tax_amount = Decimal(0)
            if tax_code_str and line_subtotal_before_tax != Decimal(0):
                tax_code_detail = next((tc for tc in self._tax_codes_cache if tc.get("code") == tax_code_str), None)
                if tax_code_detail and tax_code_detail.get("rate") is not None:
                    rate = Decimal(str(tax_code_detail["rate"]))
                    line_tax_amount = (line_subtotal_before_tax * (rate / Decimal(100))).quantize(Decimal("0.01"), ROUND_HALF_UP)
            line_total = line_subtotal_before_tax + line_tax_amount
            subtotal_item = self.lines_table.item(row, self.COL_SUBTOTAL); tax_amt_item = self.lines_table.item(row, self.COL_TAX_AMT); total_item = self.lines_table.item(row, self.COL_TOTAL)
            if not subtotal_item: subtotal_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_SUBTOTAL, subtotal_item)
            subtotal_item.setText(self._format_decimal_for_cell(line_subtotal_before_tax.quantize(Decimal("0.01")), False))
            if not tax_amt_item: tax_amt_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_TAX_AMT, tax_amt_item)
            tax_amt_item.setText(self._format_decimal_for_cell(line_tax_amount, True))
            if not total_item: total_item = QTableWidgetItem(); self.lines_table.setItem(row, self.COL_TOTAL, total_item)
            total_item.setText(self._format_decimal_for_cell(line_total.quantize(Decimal("0.01")), False))
        except Exception as e:
            self.app_core.logger.error(f"Error calculating PI line totals for row {row}: {e}", exc_info=True)
            for col_idx in [self.COL_SUBTOTAL, self.COL_TAX_AMT, self.COL_TOTAL]:
                item = self.lines_table.item(row, col_idx); 
                if item: item.setText("Error")
        finally: self._update_invoice_totals()

    def _update_invoice_totals(self):
        invoice_subtotal_agg = Decimal(0); total_tax_agg = Decimal(0)
        for r in range(self.lines_table.rowCount()):
            try:
                sub_item = self.lines_table.item(r, self.COL_SUBTOTAL); tax_item = self.lines_table.item(r, self.COL_TAX_AMT)
                if sub_item and sub_item.text() and sub_item.text() != "Error": invoice_subtotal_agg += Decimal(sub_item.text().replace(',',''))
                if tax_item and tax_item.text() and tax_item.text() != "Error": total_tax_agg += Decimal(tax_item.text().replace(',',''))
            except (InvalidOperation, AttributeError) as e: self.app_core.logger.warning(f"Could not parse amount from PI line {r} during total update: {e}")
        grand_total_agg = invoice_subtotal_agg + total_tax_agg
        self.subtotal_display.setText(self._format_decimal_for_cell(invoice_subtotal_agg, False))
        self.total_tax_display.setText(self._format_decimal_for_cell(total_tax_agg, False))
        self.grand_total_display.setText(self._format_decimal_for_cell(grand_total_agg, False))
        
    def _collect_data(self) -> Optional[Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData]]:
        vendor_id_data = self.vendor_combo.currentData()
        if not vendor_id_data or vendor_id_data == 0: QMessageBox.warning(self, "Validation Error", "Vendor must be selected."); return None
        vendor_id = int(vendor_id_data)
        vendor_invoice_no_str = self.vendor_invoice_no_edit.text().strip() or None
        if not vendor_invoice_no_str: QMessageBox.warning(self, "Validation Error", "Vendor Invoice No. is required."); return None
        invoice_date_py = self.invoice_date_edit.date().toPython(); due_date_py = self.due_date_edit.date().toPython()
        if due_date_py < invoice_date_py: QMessageBox.warning(self, "Validation Error", "Due date cannot be before invoice date."); return None
        line_dtos: List[PurchaseInvoiceLineBaseData] = []
        for r in range(self.lines_table.rowCount()):
            try:
                prod_cell_widget = self.lines_table.cellWidget(r, self.COL_PROD)
                prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
                desc_item = self.lines_table.item(r, self.COL_DESC); qty_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_QTY))
                price_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_PRICE)); disc_pct_spin = cast(QDoubleSpinBox, self.lines_table.cellWidget(r, self.COL_DISC_PCT))
                tax_combo = cast(QComboBox, self.lines_table.cellWidget(r, self.COL_TAX_CODE))
                product_id_data = prod_combo.currentData() if prod_combo else None
                product_id = int(product_id_data) if product_id_data and product_id_data != 0 else None
                description = desc_item.text().strip() if desc_item else ""; quantity = Decimal(str(qty_spin.value()))
                unit_price = Decimal(str(price_spin.value())); discount_percent = Decimal(str(disc_pct_spin.value()))
                tax_code_str = tax_combo.currentData() if tax_combo and tax_combo.currentData() else None
                if not description and not product_id: continue 
                if quantity <= 0: QMessageBox.warning(self, "Validation Error", f"Quantity must be positive on line {r+1}."); return None
                line_dtos.append(PurchaseInvoiceLineBaseData(product_id=product_id, description=description, quantity=quantity, unit_price=unit_price, discount_percent=discount_percent, tax_code=tax_code_str))
            except Exception as e: QMessageBox.warning(self, "Input Error", f"Error processing line {r + 1}: {str(e)}"); return None
        if not line_dtos: QMessageBox.warning(self, "Input Error", "Purchase invoice must have at least one valid line item."); return None
        common_data = { "vendor_id": vendor_id, "vendor_invoice_no": vendor_invoice_no_str, "invoice_date": invoice_date_py, "due_date": due_date_py, "currency_code": self.currency_combo.currentData() or self._base_currency, "exchange_rate": Decimal(str(self.exchange_rate_spin.value())), "notes": self.notes_edit.toPlainText().strip() or None, "user_id": self.current_user_id, "lines": line_dtos }
        try:
            if self.invoice_id: return PurchaseInvoiceUpdateData(id=self.invoice_id, **common_data) 
            else: return PurchaseInvoiceCreateData(**common_data) 
        except ValueError as ve: QMessageBox.warning(self, "Validation Error", f"Data validation failed:\n{str(ve)}"); return None

    @Slot()
    def on_save_draft(self):
        if self.view_only_mode or (self.loaded_invoice_orm and self.loaded_invoice_orm.status != InvoiceStatusEnum.DRAFT.value): QMessageBox.information(self, "Info", "Cannot save. Invoice is not a draft or in view-only mode."); return
        dto = self._collect_data()
        if dto: 
            self._set_buttons_for_async_operation(True)
            future = schedule_task_from_qt(self._perform_save(dto, post_invoice_after=False))
            if future:
                future.add_done_callback(
                    lambda res: QMetaObject.invokeMethod(
                        self, "_safe_set_buttons_for_async_operation_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, False)
                    )
                )
            else:
                self.app_core.logger.error("Failed to schedule _perform_save task in on_save_draft for Purchase Invoice.")
                self._set_buttons_for_async_operation(False) # Re-enable buttons if scheduling failed


    @Slot()
    def on_save_and_approve(self): QMessageBox.information(self, "Not Implemented", "Save & Approve for Purchase Invoices is not yet available.")

    @Slot(bool)
    def _safe_set_buttons_for_async_operation_slot(self, busy: bool):
        self._set_buttons_for_async_operation(busy)

    def _set_buttons_for_async_operation(self, busy: bool):
        self.save_draft_button.setEnabled(not busy)
        self.save_approve_button.setEnabled(False) 

    async def _perform_save(self, dto: Union[PurchaseInvoiceCreateData, PurchaseInvoiceUpdateData], post_invoice_after: bool):
        if not self.app_core.purchase_invoice_manager: QMessageBox.critical(self, "Error", "Purchase Invoice Manager not available."); return
        save_result: Result[PurchaseInvoice]; is_update = isinstance(dto, PurchaseInvoiceUpdateData); action_verb_past = "updated" if is_update else "created"
        if is_update: save_result = await self.app_core.purchase_invoice_manager.update_draft_purchase_invoice(dto.id, dto) 
        else: save_result = await self.app_core.purchase_invoice_manager.create_draft_purchase_invoice(dto) 
        if not save_result.is_success or not save_result.value: QMessageBox.warning(self, "Save Error", f"Failed to {('update' if is_update else 'create')} purchase invoice draft:\n{', '.join(save_result.errors)}"); return 
        saved_invoice = save_result.value; self.invoice_saved.emit(saved_invoice.id); self.invoice_id = saved_invoice.id; self.loaded_invoice_orm = saved_invoice; self.setWindowTitle(self._get_window_title()); self.our_ref_no_label.setText(saved_invoice.invoice_no); self.our_ref_no_label.setStyleSheet("font-style: normal; color: black;")
        if not post_invoice_after: QMessageBox.information(self, "Success", f"Purchase Invoice draft {action_verb_past} successfully (ID: {saved_invoice.id}, Our Ref: {saved_invoice.invoice_no})."); self._set_read_only_state(self.view_only_mode or (saved_invoice.status != InvoiceStatusEnum.DRAFT.value)); self.accept(); return
        # PI Posting logic here if post_invoice_after is True

    @Slot(int)
    def _on_vendor_changed(self, index: int):
        vendor_id = self.vendor_combo.itemData(index)
        if vendor_id and vendor_id != 0 and self._vendors_cache:
            vendor_data = next((v for v in self._vendors_cache if v.get("id") == vendor_id), None)
            if vendor_data and vendor_data.get("currency_code"):
                curr_idx = self.currency_combo.findData(vendor_data["currency_code"])
                if curr_idx != -1: self.currency_combo.setCurrentIndex(curr_idx)
            if vendor_data and vendor_data.get("payment_terms") is not None: self.due_date_edit.setDate(self.invoice_date_edit.date().addDays(int(vendor_data["payment_terms"])))

    @Slot(int)
    def _on_currency_changed(self, index: int):
        currency_code = self.currency_combo.currentData(); is_base = (currency_code == self._base_currency)
        self.exchange_rate_spin.setEnabled(not is_base and not self.view_only_mode); self.exchange_rate_spin.setReadOnly(is_base or self.view_only_mode); 
        if is_base: self.exchange_rate_spin.setValue(1.0)

    @Slot(QDate)
    def _on_invoice_date_changed(self, new_date: QDate):
        vendor_id = self.vendor_combo.currentData(); terms = 30 
        if vendor_id and vendor_id != 0 and self._vendors_cache:
            vendor_data = next((v for v in self._vendors_cache if v.get("id") == vendor_id), None)
            if vendor_data and vendor_data.get("payment_terms") is not None:
                try: terms = int(vendor_data["payment_terms"])
                except: pass
        self.due_date_edit.setDate(new_date.addDays(terms))

    @Slot(int)
    def _on_open_product_search(self, row: int):
        self._current_search_target_row = row
        search_dialog = ProductSearchDialog(self.app_core, self)
        search_dialog.product_selected.connect(self._handle_product_selected_from_search)
        search_dialog.exec()

    @Slot(object)
    def _handle_product_selected_from_search(self, product_summary_dict_obj: object):
        if self._current_search_target_row is None: return
        target_row = self._current_search_target_row
        try:
            product_data_dict = cast(Dict[str, Any], product_summary_dict_obj)
            product_id = product_data_dict.get("id")
            if product_id is None: return
            prod_cell_widget = self.lines_table.cellWidget(target_row, self.COL_PROD)
            prod_combo = prod_cell_widget.findChild(QComboBox) if prod_cell_widget else None
            if prod_combo:
                found_idx = prod_combo.findData(product_id)
                if found_idx != -1: prod_combo.setCurrentIndex(found_idx) 
                else: self.app_core.logger.warning(f"Product ID {product_id} from search not in line combo for PI row {target_row}. Forcing."); self._on_line_product_changed(target_row, product_id) 
            else: self.app_core.logger.error(f"Product combo not found for PI row {target_row}.")
        except Exception as e: self.app_core.logger.error(f"Error handling product selected from search for PI: {e}", exc_info=True); QMessageBox.warning(self, "Product Selection Error", f"Could not apply product: {str(e)}")
        finally: self._current_search_target_row = None


```

# app/ui/purchase_invoices/purchase_invoices_widget.py
```py
# File: app/ui/purchase_invoices/purchase_invoices_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox,
    QLabel, QLineEdit, QCheckBox, QComboBox, QDateEdit, QCompleter
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize, QDate
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.purchase_invoices.purchase_invoice_table_model import PurchaseInvoiceTableModel
from app.ui.purchase_invoices.purchase_invoice_dialog import PurchaseInvoiceDialog
from app.utils.pydantic_models import PurchaseInvoiceSummaryData, VendorSummaryData
from app.common.enums import InvoiceStatusEnum
from app.utils.json_helpers import json_converter, json_date_hook
from app.utils.result import Result
from app.models.business.purchase_invoice import PurchaseInvoice

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class PurchaseInvoicesWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self._vendors_cache_for_filter: List[VendorSummaryData] = []
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
            self.app_core.logger.info("Using compiled Qt resources for PurchaseInvoicesWidget.")
        except ImportError:
            self.app_core.logger.info("PurchaseInvoicesWidget: Compiled resources not found. Using direct file paths.")
            
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_vendors_for_filter_combo()))
        QTimer.singleShot(100, lambda: self.apply_filter_button.click())


    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self._create_filter_area()
        self.main_layout.addLayout(self.filter_layout) 

        self.invoices_table = QTableView()
        self.invoices_table.setAlternatingRowColors(True)
        self.invoices_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.invoices_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.invoices_table.horizontalHeader().setStretchLastSection(False)
        self.invoices_table.doubleClicked.connect(self._on_view_invoice_double_click) 
        self.invoices_table.setSortingEnabled(True)

        self.table_model = PurchaseInvoiceTableModel()
        self.invoices_table.setModel(self.table_model)
        
        header = self.invoices_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.invoices_table.setColumnHidden(id_col_idx, True)
        
        vendor_col_idx = self.table_model._headers.index("Vendor") if "Vendor" in self.table_model._headers else -1
        if vendor_col_idx != -1:
            visible_vendor_idx = vendor_col_idx
            if id_col_idx != -1 and id_col_idx < vendor_col_idx and self.invoices_table.isColumnHidden(id_col_idx):
                 visible_vendor_idx -=1
            if not self.invoices_table.isColumnHidden(vendor_col_idx):
                 header.setSectionResizeMode(visible_vendor_idx, QHeaderView.ResizeMode.Stretch)
        elif self.table_model.columnCount() > 4 : 
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch) 


        self.main_layout.addWidget(self.invoices_table)
        self.setLayout(self.main_layout)

        if self.invoices_table.selectionModel():
            self.invoices_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Purchase Invoice Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_new_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "New P.Invoice", self)
        self.toolbar_new_action.triggered.connect(self._on_new_invoice)
        self.toolbar.addAction(self.toolbar_new_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Draft", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_draft_invoice)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_view_action = QAction(QIcon(self.icon_path_prefix + "view.svg"), "View P.Invoice", self)
        self.toolbar_view_action.triggered.connect(self._on_view_invoice_toolbar)
        self.toolbar.addAction(self.toolbar_view_action)
        
        self.toolbar_post_action = QAction(QIcon(self.icon_path_prefix + "post.svg"), "Post P.Invoice(s)", self)
        self.toolbar_post_action.triggered.connect(self._on_post_invoice) 
        # self.toolbar_post_action.setEnabled(False) # Now managed by _update_action_states
        self.toolbar.addAction(self.toolbar_post_action)

        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    # ... (_create_filter_area, _load_vendors_for_filter_combo, _populate_vendors_filter_slot, _clear_filters_and_load - unchanged from file set 3)
    def _create_filter_area(self):
        self.filter_layout = QHBoxLayout() 
        self.filter_layout.addWidget(QLabel("Vendor:"))
        self.vendor_filter_combo = QComboBox(); self.vendor_filter_combo.setMinimumWidth(200)
        self.vendor_filter_combo.addItem("All Vendors", 0); self.vendor_filter_combo.setEditable(True) 
        self.vendor_filter_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        vend_completer = QCompleter(self); vend_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        vend_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.vendor_filter_combo.setCompleter(vend_completer); self.filter_layout.addWidget(self.vendor_filter_combo)
        self.filter_layout.addWidget(QLabel("Status:"))
        self.status_filter_combo = QComboBox(); self.status_filter_combo.addItem("All Statuses", None) 
        for status_enum in InvoiceStatusEnum: self.status_filter_combo.addItem(status_enum.value, status_enum)
        self.filter_layout.addWidget(self.status_filter_combo)
        self.filter_layout.addWidget(QLabel("From:"))
        self.start_date_filter_edit = QDateEdit(QDate.currentDate().addMonths(-3))
        self.start_date_filter_edit.setCalendarPopup(True); self.start_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.start_date_filter_edit)
        self.filter_layout.addWidget(QLabel("To:"))
        self.end_date_filter_edit = QDateEdit(QDate.currentDate())
        self.end_date_filter_edit.setCalendarPopup(True); self.end_date_filter_edit.setDisplayFormat("dd/MM/yyyy")
        self.filter_layout.addWidget(self.end_date_filter_edit)
        self.apply_filter_button = QPushButton(QIcon(self.icon_path_prefix + "filter.svg"), "Apply")
        self.apply_filter_button.clicked.connect(lambda: schedule_task_from_qt(self._load_invoices()))
        self.filter_layout.addWidget(self.apply_filter_button)
        self.clear_filter_button = QPushButton(QIcon(self.icon_path_prefix + "refresh.svg"), "Clear")
        self.clear_filter_button.clicked.connect(self._clear_filters_and_load)
        self.filter_layout.addWidget(self.clear_filter_button); self.filter_layout.addStretch()

    async def _load_vendors_for_filter_combo(self):
        if not self.app_core.vendor_manager: return
        try:
            result: Result[List[VendorSummaryData]] = await self.app_core.vendor_manager.get_vendors_for_listing(active_only=True, page_size=-1) 
            if result.is_success and result.value:
                self._vendors_cache_for_filter = result.value
                vendors_json = json.dumps([v.model_dump() for v in result.value], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_vendors_filter_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, vendors_json))
        except Exception as e: self.app_core.logger.error(f"Error loading vendors for filter: {e}", exc_info=True)

    @Slot(str)
    def _populate_vendors_filter_slot(self, vendors_json_str: str):
        current_selection_data = self.vendor_filter_combo.currentData(); self.vendor_filter_combo.clear()
        self.vendor_filter_combo.addItem("All Vendors", 0) 
        try:
            vendors_data = json.loads(vendors_json_str)
            self._vendors_cache_for_filter = [VendorSummaryData.model_validate(v) for v in vendors_data]
            for vend_summary in self._vendors_cache_for_filter: self.vendor_filter_combo.addItem(f"{vend_summary.vendor_code} - {vend_summary.name}", vend_summary.id)
            idx = self.vendor_filter_combo.findData(current_selection_data)
            if idx != -1: self.vendor_filter_combo.setCurrentIndex(idx)
            if isinstance(self.vendor_filter_combo.completer(), QCompleter): self.vendor_filter_combo.completer().setModel(self.vendor_filter_combo.model())
        except json.JSONDecodeError as e: self.app_core.logger.error(f"Failed to parse vendors JSON for filter: {e}")

    @Slot()
    def _clear_filters_and_load(self):
        self.vendor_filter_combo.setCurrentIndex(0); self.status_filter_combo.setCurrentIndex(0)   
        self.start_date_filter_edit.setDate(QDate.currentDate().addMonths(-3)); self.end_date_filter_edit.setDate(QDate.currentDate())
        schedule_task_from_qt(self._load_invoices())
        
    @Slot()
    def _update_action_states(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_edit_draft = False
        can_post_any_selected = False

        if single_selection:
            row = selected_rows[0].row()
            status = self.table_model.get_invoice_status_at_row(row)
            if status == InvoiceStatusEnum.DRAFT:
                can_edit_draft = True
        
        if selected_rows:
            can_post_any_selected = any(
                self.table_model.get_invoice_status_at_row(idx.row()) == InvoiceStatusEnum.DRAFT
                for idx in selected_rows
            )
            
        self.toolbar_edit_action.setEnabled(can_edit_draft)
        self.toolbar_view_action.setEnabled(single_selection)
        self.toolbar_post_action.setEnabled(can_post_any_selected) 

    async def _load_invoices(self):
        if not self.app_core.purchase_invoice_manager: self.app_core.logger.error("PurchaseInvoiceManager not available."); return
        try:
            vend_id_data = self.vendor_filter_combo.currentData()
            vendor_id_filter = int(vend_id_data) if vend_id_data and vend_id_data != 0 else None
            status_enum_data = self.status_filter_combo.currentData()
            status_filter_val: Optional[InvoiceStatusEnum] = status_enum_data if isinstance(status_enum_data, InvoiceStatusEnum) else None
            start_date_filter = self.start_date_filter_edit.date().toPython(); end_date_filter = self.end_date_filter_edit.date().toPython()
            result: Result[List[PurchaseInvoiceSummaryData]] = await self.app_core.purchase_invoice_manager.get_invoices_for_listing(
                vendor_id=vendor_id_filter, status=status_filter_val, start_date=start_date_filter, end_date=end_date_filter, page=1, page_size=200)
            if result.is_success:
                data_for_table = result.value if result.value is not None else []
                json_data = json.dumps([dto.model_dump() for dto in data_for_table], default=json_converter)
                QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
            else:
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Failed to load PIs: {', '.join(result.errors)}"))
        except Exception as e:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading PIs: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            invoice_summaries: List[PurchaseInvoiceSummaryData] = [PurchaseInvoiceSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(invoice_summaries)
        except Exception as e: QMessageBox.critical(self, "Data Error", f"Failed to parse/validate PI data: {e}")
        finally: self._update_action_states()

    @Slot()
    def _on_new_invoice(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_invoice_id_and_status(self) -> tuple[Optional[int], Optional[InvoiceStatusEnum]]:
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1: return None, None
        row = selected_rows[0].row()
        inv_id = self.table_model.get_invoice_id_at_row(row)
        inv_status = self.table_model.get_invoice_status_at_row(row)
        return inv_id, inv_status

    @Slot()
    def _on_edit_draft_invoice(self):
        invoice_id, status = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single PI to edit."); return
        if status != InvoiceStatusEnum.DRAFT: QMessageBox.warning(self, "Edit Error", "Only Draft PIs can be edited."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, parent=self)
        dialog.invoice_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_view_invoice_toolbar(self):
        invoice_id, _ = self._get_selected_invoice_id_and_status()
        if invoice_id is None: QMessageBox.information(self, "Selection", "Please select a single PI to view."); return
        self._show_view_invoice_dialog(invoice_id)

    @Slot(QModelIndex)
    def _on_view_invoice_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        invoice_id = self.table_model.get_invoice_id_at_row(index.row())
        if invoice_id is None: return
        self._show_view_invoice_dialog(invoice_id)

    def _show_view_invoice_dialog(self, invoice_id: int):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = PurchaseInvoiceDialog(self.app_core, self.app_core.current_user.id, invoice_id=invoice_id, view_only=True, parent=self)
        dialog.exec()
        
    @Slot()
    def _on_post_invoice(self):
        selected_rows = self.invoices_table.selectionModel().selectedRows()
        if not selected_rows: QMessageBox.information(self, "Selection", "Please select one or more Draft PIs to post."); return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in to post PIs."); return
        
        draft_invoice_ids_to_post: List[int] = []
        non_draft_selected_count = 0
        for index in selected_rows:
            inv_id = self.table_model.get_invoice_id_at_row(index.row())
            status = self.table_model.get_invoice_status_at_row(index.row())
            if inv_id and status == InvoiceStatusEnum.DRAFT: draft_invoice_ids_to_post.append(inv_id)
            elif inv_id: non_draft_selected_count += 1
        
        if not draft_invoice_ids_to_post: QMessageBox.information(self, "Selection", "No Draft PIs selected for posting."); return
        
        warning_message = f"\n\nNote: {non_draft_selected_count} selected PIs are not 'Draft' and will be ignored." if non_draft_selected_count > 0 else ""
        reply = QMessageBox.question(self, "Confirm Posting", 
                                     f"Are you sure you want to post {len(draft_invoice_ids_to_post)} selected draft PIs?\nThis will create JEs and change status to 'Approved'.{warning_message}",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return
            
        self.toolbar_post_action.setEnabled(False)
        schedule_task_from_qt(self._perform_post_invoices(draft_invoice_ids_to_post, self.app_core.current_user.id))

    async def _perform_post_invoices(self, invoice_ids: List[int], user_id: int):
        if not self.app_core.purchase_invoice_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Purchase Invoice Manager not available."))
            self._update_action_states(); return

        success_count = 0; failed_posts: List[str] = []
        for inv_id_to_post in invoice_ids:
            invoice_orm_for_no = await self.app_core.purchase_invoice_manager.get_invoice_for_dialog(inv_id_to_post)
            inv_no_str = invoice_orm_for_no.invoice_no if invoice_orm_for_no else f"ID {inv_id_to_post}"
            result: Result[PurchaseInvoice] = await self.app_core.purchase_invoice_manager.post_purchase_invoice(inv_id_to_post, user_id)
            if result.is_success: success_count += 1
            else: failed_posts.append(f"PI {inv_no_str}: {', '.join(result.errors)}")
        
        summary_message_parts = []
        if success_count > 0: summary_message_parts.append(f"{success_count} PIs posted successfully.")
        if failed_posts:
            summary_message_parts.append(f"{len(failed_posts)} PIs failed to post:")
            summary_message_parts.extend([f"  - {err}" for err in failed_posts])
        final_message = "\n".join(summary_message_parts) if summary_message_parts else "No PIs were processed."
        
        msg_box_method = QMessageBox.information
        title = "Posting Complete"
        if failed_posts and success_count == 0: msg_box_method = QMessageBox.critical; title = "Posting Failed"
        elif failed_posts: msg_box_method = QMessageBox.warning; title = "Posting Partially Successful"
        
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, title), Q_ARG(str, final_message))
        
        schedule_task_from_qt(self._load_invoices())


    @Slot(int)
    def _refresh_list_after_save(self, invoice_id: int):
        self.app_core.logger.info(f"PurchaseInvoiceDialog reported save for ID: {invoice_id}. Refreshing list.")
        schedule_task_from_qt(self._load_invoices())

```

# app/ui/purchase_invoices/purchase_invoice_table_model.py
```py
# File: app/ui/purchase_invoices/purchase_invoice_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import date as python_date

from app.utils.pydantic_models import PurchaseInvoiceSummaryData
from app.common.enums import InvoiceStatusEnum

class PurchaseInvoiceTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[PurchaseInvoiceSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = [
            "ID", "Our Ref No.", "Vendor Inv No.", "Inv Date", 
            "Vendor", "Total Amount", "Status"
        ]
        self._data: List[PurchaseInvoiceSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def _format_decimal_for_table(self, value: Optional[Decimal], show_zero_as_blank: bool = False) -> str:
        if value is None: 
            return "0.00" if not show_zero_as_blank else ""
        try:
            d_value = Decimal(str(value))
            if show_zero_as_blank and d_value.is_zero():
                return ""
            return f"{d_value:,.2f}"
        except (InvalidOperation, TypeError):
            return str(value) 

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        
        row = index.row()
        col = index.column()

        if not (0 <= row < len(self._data)):
            return None
            
        invoice_summary: PurchaseInvoiceSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            # header_key = self._headers[col].lower().replace('.', '').replace(' ', '_') # Less direct mapping
            
            if col == 0: return str(invoice_summary.id)
            if col == 1: return invoice_summary.invoice_no # Our Ref No.
            if col == 2: return invoice_summary.vendor_invoice_no or ""
            if col == 3: # Inv Date
                inv_date = invoice_summary.invoice_date
                return inv_date.strftime('%d/%m/%Y') if isinstance(inv_date, python_date) else str(inv_date)
            if col == 4: return invoice_summary.vendor_name
            if col == 5: return self._format_decimal_for_table(invoice_summary.total_amount, False) # Total Amount
            if col == 6: # Status
                status_val = invoice_summary.status
                return status_val.value if isinstance(status_val, InvoiceStatusEnum) else str(status_val)
            
            # Fallback for safety if more headers added without explicit handling
            # return str(getattr(invoice_summary, header_key, ""))
            return ""


        elif role == Qt.ItemDataRole.UserRole: # Store ID for quick retrieval
            if col == 0: 
                return invoice_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] in ["Total Amount"]:
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            if self._headers[col] == "Status":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_invoice_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None:
                return int(id_val)
            return self._data[row].id 
        return None
        
    def get_invoice_status_at_row(self, row: int) -> Optional[InvoiceStatusEnum]:
        if 0 <= row < len(self._data):
            status_val = self._data[row].status
            return status_val if isinstance(status_val, InvoiceStatusEnum) else None
        return None

    def update_data(self, new_data: List[PurchaseInvoiceSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/__init__.py
```py
# File: app/ui/__init__.py
# (Content as previously generated)
from .main_window import MainWindow

__all__ = ["MainWindow"]

```

# app/ui/settings/user_management_widget.py
```py
# File: app/ui/settings/user_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QPushButton, 
    QToolBar, QMenu, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, Dict, Any, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.user_table_model import UserTableModel
from app.ui.settings.user_dialog import UserDialog 
from app.ui.settings.user_password_dialog import UserPasswordDialog # New import
from app.utils.pydantic_models import UserSummaryData
from app.utils.json_helpers import json_converter, json_date_hook 
from app.utils.result import Result
from app.models.core.user import User 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserManagementWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass 
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_users()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.users_table = QTableView()
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.users_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.users_table.horizontalHeader().setStretchLastSection(True) 
        self.users_table.setSortingEnabled(True)
        self.users_table.doubleClicked.connect(self._on_edit_user_double_click)


        self.table_model = UserTableModel()
        self.users_table.setModel(self.table_model)
        
        header = self.users_table.horizontalHeader()
        for i in range(self.table_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.users_table.setColumnHidden(id_col_idx, True)
        
        fn_col_idx = self.table_model._headers.index("Full Name") if "Full Name" in self.table_model._headers else -1
        email_col_idx = self.table_model._headers.index("Email") if "Email" in self.table_model._headers else -1

        if fn_col_idx != -1 and not self.users_table.isColumnHidden(fn_col_idx) :
            header.setSectionResizeMode(fn_col_idx, QHeaderView.ResizeMode.Stretch)
        elif email_col_idx != -1 and not self.users_table.isColumnHidden(email_col_idx):
             header.setSectionResizeMode(email_col_idx, QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.users_table)
        self.setLayout(self.main_layout)

        if self.users_table.selectionModel():
            self.users_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("User Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add User", self)
        self.toolbar_add_action.triggered.connect(self._on_add_user)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit User", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_user)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_toggle_active_action = QAction(QIcon(self.icon_path_prefix + "deactivate.svg"), "Toggle Active", self)
        self.toolbar_toggle_active_action.triggered.connect(self._on_toggle_active_status)
        self.toolbar.addAction(self.toolbar_toggle_active_action)
        
        self.toolbar_change_password_action = QAction(QIcon(self.icon_path_prefix + "preferences.svg"), "Change Password", self)
        self.toolbar_change_password_action.triggered.connect(self._on_change_password)
        self.toolbar.addAction(self.toolbar_change_password_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_users()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.users_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_current_user_selected = False
        is_system_init_user_selected = False

        if single_selection:
            can_modify = True
            row = selected_rows[0].row()
            user_id = self.table_model.get_user_id_at_row(row)
            username = self.table_model.get_username_at_row(row)

            if self.app_core.current_user and user_id == self.app_core.current_user.id:
                is_current_user_selected = True
            if username == "system_init_user": 
                is_system_init_user_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify and not is_system_init_user_selected)
        self.toolbar_toggle_active_action.setEnabled(can_modify and not is_current_user_selected and not is_system_init_user_selected)
        self.toolbar_change_password_action.setEnabled(can_modify and not is_system_init_user_selected)

    async def _load_users(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager component not available."))
            return
        try:
            summaries: List[UserSummaryData] = await self.app_core.security_manager.get_all_users_summary()
            json_data = json.dumps([s.model_dump(mode='json') for s in summaries])
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            self.app_core.logger.error(f"Unexpected error loading users: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading users: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str, object_hook=json_date_hook)
            user_summaries: List[UserSummaryData] = [UserSummaryData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(user_summaries)
        except Exception as e: 
            self.app_core.logger.error(f"Failed to parse/validate user data for table: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate user data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_user(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_user_id_and_username(self) -> tuple[Optional[int], Optional[str]]: # Modified to return username too
        selected_rows = self.users_table.selectionModel().selectedRows()
        if not selected_rows or len(selected_rows) > 1:
            return None, None
        row_index = selected_rows[0].row()
        user_id = self.table_model.get_user_id_at_row(row_index)
        username = self.table_model.get_username_at_row(row_index)
        return user_id, username


    @Slot()
    def _on_edit_user(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single user to edit.")
            return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "The 'system_init_user' cannot be edited from the UI.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, user_id_to_edit=user_id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot(QModelIndex)
    def _on_edit_user_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        user_id = self.table_model.get_user_id_at_row(index.row())
        username = self.table_model.get_username_at_row(index.row())
        if user_id is None: return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "The 'system_init_user' cannot be edited from the UI.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = UserDialog(self.app_core, self.app_core.current_user.id, user_id_to_edit=user_id, parent=self)
        dialog.user_saved.connect(self._refresh_list_after_save)
        dialog.exec()


    @Slot()
    def _on_toggle_active_status(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: QMessageBox.information(self, "Selection", "Please select a single user to toggle status."); return
        
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        if user_id == self.app_core.current_user.id:
            QMessageBox.warning(self, "Action Denied", "You cannot change the active status of your own account.")
            return
            
        if username == "system_init_user":
             QMessageBox.warning(self, "Action Denied", "The 'system_init_user' status cannot be modified from the UI.")
             return

        current_row_idx = self.users_table.currentIndex().row()
        is_currently_active = self.table_model.get_user_active_status_at_row(current_row_idx)
        action_verb = "deactivate" if is_currently_active else "activate"
        
        reply = QMessageBox.question(self, f"Confirm {action_verb.capitalize()}",
                                     f"Are you sure you want to {action_verb} user account '{username}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.toggle_user_active_status(user_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_toggle_active_result)
        else: self._handle_toggle_active_result(None) 

    def _handle_toggle_active_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule user status toggle."); return
        try:
            result: Result[User] = future.result()
            if result.is_success and result.value:
                action_verb_past = "activated" if result.value.is_active else "deactivated"
                QMessageBox.information(self, "Success", f"User account '{result.value.username}' {action_verb_past} successfully.")
                schedule_task_from_qt(self._load_users()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to toggle user status:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling toggle active status result for user: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    @Slot()
    def _on_change_password(self):
        user_id, username = self._get_selected_user_id_and_username()
        if user_id is None: 
            QMessageBox.information(self, "Selection", "Please select a user to change password.")
            return
        
        if username == "system_init_user":
            QMessageBox.warning(self, "Action Denied", "Password for 'system_init_user' cannot be changed from the UI.")
            return
        
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Auth Error", "Please log in.")
            return

        dialog = UserPasswordDialog(
            self.app_core, 
            self.app_core.current_user.id, # User performing the change
            user_id_to_change=user_id,
            username_to_change=username if username else "Selected User", # Fallback for username
            parent=self
        )
        # password_changed signal doesn't strictly need connection if just a success msg is enough
        # If list needs refresh due to some password related field, connect it.
        # dialog.password_changed.connect(lambda changed_user_id: self.app_core.logger.info(f"Password changed for user {changed_user_id}"))
        dialog.exec()
    
    @Slot(int)
    def _refresh_list_after_save(self, user_id: int): # Renamed from on_user_saved
        self.app_core.logger.info(f"UserDialog reported save for User ID: {user_id}. Refreshing user list.")
        schedule_task_from_qt(self._load_users())

```

# app/ui/settings/__init__.py
```py
# File: app/ui/settings/__init__.py
from .settings_widget import SettingsWidget
from .user_management_widget import UserManagementWidget 
from .user_table_model import UserTableModel 
from .user_dialog import UserDialog 
from .user_password_dialog import UserPasswordDialog 
from .role_management_widget import RoleManagementWidget 
from .role_table_model import RoleTableModel 
from .role_dialog import RoleDialog 
# AuditLogWidget is used by SettingsWidget, but not necessarily exported from settings package
# It's better to import it directly in SettingsWidget from app.ui.audit

__all__ = [
    "SettingsWidget",
    "UserManagementWidget", 
    "UserTableModel",       
    "UserDialog", 
    "UserPasswordDialog",
    "RoleManagementWidget", 
    "RoleTableModel",       
    "RoleDialog",           
]

```

# app/ui/settings/role_table_model.py
```py
# File: app/ui/settings/role_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Optional, Any

from app.utils.pydantic_models import RoleData # Use RoleData DTO

class RoleTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[RoleData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Name", "Description"]
        self._data: List[RoleData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole) -> Optional[str]:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            # Allow UserRole for ID retrieval
            if role == Qt.ItemDataRole.UserRole and index.column() == 0 and 0 <= index.row() < len(self._data):
                return self._data[index.row()].id
            return None
        
        row = index.row(); col = index.column()
        if not (0 <= row < len(self._data)): return None
            
        role_data: RoleData = self._data[row]

        if col == 0: return str(role_data.id)
        if col == 1: return role_data.name
        if col == 2: return role_data.description or ""
            
        return None

    def get_role_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            # Try UserRole first for consistency if data() method is updated to store it
            idx = self.index(row, 0)
            role_id = self.data(idx, Qt.ItemDataRole.UserRole)
            if role_id is not None: return int(role_id)
            return self._data[row].id 
        return None
        
    def get_role_name_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].name
        return None

    def update_data(self, new_data: List[RoleData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/settings/user_password_dialog.py
```py
# File: app/ui/settings/user_password_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, TYPE_CHECKING

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import UserPasswordChangeData
from app.utils.result import Result

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserPasswordDialog(QDialog):
    password_changed = Signal(int) # Emits user_id_to_change

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int,
                 user_id_to_change: int,
                 username_to_change: str,
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.user_id_to_change = user_id_to_change
        self.username_to_change = username_to_change

        self.setWindowTitle(f"Change Password for {self.username_to_change}")
        self.setMinimumWidth(400)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        
        info_label = QLabel(f"Changing password for user: <b>{self.username_to_change}</b> (ID: {self.user_id_to_change})")
        main_layout.addWidget(info_label)

        form_layout = QFormLayout()
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_edit.setPlaceholderText("Enter new password (min 8 characters)")
        form_layout.addRow("New Password*:", self.new_password_edit)

        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_edit.setPlaceholderText("Confirm new password")
        form_layout.addRow("Confirm New Password*:", self.confirm_password_edit)
        
        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)
        
        self.new_password_edit.setFocus()


    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_ok_clicked)
        self.button_box.rejected.connect(self.reject)

    def _collect_data(self) -> Optional[UserPasswordChangeData]:
        new_password = self.new_password_edit.text()
        confirm_password = self.confirm_password_edit.text()

        if not new_password:
            QMessageBox.warning(self, "Validation Error", "New Password cannot be empty.")
            return None
        
        # Pydantic DTO will handle min_length and password match via its validator
        try:
            dto = UserPasswordChangeData(
                user_id_to_change=self.user_id_to_change,
                new_password=new_password,
                confirm_new_password=confirm_password,
                user_id=self.current_admin_user_id # User performing the change
            )
            return dto
        except ValueError as e: # Catches Pydantic validation errors
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(e)}")
            return None

    @Slot()
    def on_ok_clicked(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_password_change(dto))
            if future:
                future.add_done_callback(
                    # Re-enable button regardless of outcome unless dialog is closed
                    lambda _: ok_button.setEnabled(True) if ok_button and self.isVisible() else None
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)
                QMessageBox.critical(self, "Task Error", "Failed to schedule password change operation.")


    async def _perform_password_change(self, dto: UserPasswordChangeData):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[None] = await self.app_core.security_manager.change_user_password(dto)

        if result.is_success:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self.parentWidget() if self.parentWidget() else self), # Show on parent if possible
                Q_ARG(str, "Success"), 
                Q_ARG(str, f"Password for user '{self.username_to_change}' changed successfully."))
            self.password_changed.emit(self.user_id_to_change)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Password Change Error"), 
                Q_ARG(str, f"Failed to change password:\n{', '.join(result.errors)}"))
            # Button re-enabled by callback in on_ok_clicked

```

# app/ui/settings/settings_widget.py
```py
# app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox, QGroupBox,
                               QTableView, QHeaderView, QAbstractItemView,
                               QHBoxLayout, QTabWidget 
                               ) 
from PySide6.QtCore import Slot, QDate, QTimer, QMetaObject, Q_ARG, Qt, QAbstractTableModel, QModelIndex 
from PySide6.QtGui import QColor, QFont 
from app.core.application_core import ApplicationCore
from app.utils.pydantic_models import CompanySettingData, FiscalYearCreateData, FiscalYearData 
from app.models.core.company_setting import CompanySetting
from app.models.accounting.currency import Currency 
from app.models.accounting.fiscal_year import FiscalYear 
from app.ui.accounting.fiscal_year_dialog import FiscalYearDialog 
from app.ui.settings.user_management_widget import UserManagementWidget 
from app.ui.settings.role_management_widget import RoleManagementWidget 
from app.ui.audit.audit_log_widget import AuditLogWidget # New Import
from decimal import Decimal, InvalidOperation
import asyncio # Not directly used, consider removing if not needed by other parts
import json 
from typing import Optional, List, Any, Dict 
from app.main import schedule_task_from_qt 
from datetime import date as python_date, datetime 
from app.utils.json_helpers import json_converter, json_date_hook 

class FiscalYearTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[FiscalYearData]] = None, parent=None): 
        super().__init__(parent)
        self._headers = ["Name", "Start Date", "End Date", "Status"]
        self._data: List[FiscalYearData] = data or []

    def rowCount(self, parent=QModelIndex()):
        if parent.isValid(): return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid(): 
            return None
        
        try:
            fy = self._data[index.row()]
            column = index.column()

            if role == Qt.ItemDataRole.DisplayRole:
                if column == 0: return fy.year_name
                if column == 1: return fy.start_date.strftime('%d/%m/%Y') if isinstance(fy.start_date, python_date) else str(fy.start_date)
                if column == 2: return fy.end_date.strftime('%d/%m/%Y') if isinstance(fy.end_date, python_date) else str(fy.end_date)
                if column == 3: return "Closed" if fy.is_closed else "Open"
            elif role == Qt.ItemDataRole.FontRole:
                if column == 3: 
                    font = QFont()
                    if fy.is_closed:
                        pass 
                    else: 
                        font.setBold(True)
                    return font
            elif role == Qt.ItemDataRole.ForegroundRole:
                 if column == 3 and not fy.is_closed: 
                    return QColor("green")
        except IndexError:
            return None 
        return None

    def get_fiscal_year_at_row(self, row: int) -> Optional[FiscalYearData]:
        if 0 <= row < len(self._data):
            return self._data[row]
        return None
        
    def update_data(self, new_data: List[FiscalYearData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()


class SettingsWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._loaded_settings_obj: Optional[CompanySetting] = None 
        
        self.main_layout = QVBoxLayout(self) 
        self.tab_widget = QTabWidget() 
        self.main_layout.addWidget(self.tab_widget)

        # --- Company Settings Tab ---
        self.company_settings_tab = QWidget()
        company_tab_layout = QVBoxLayout(self.company_settings_tab) 

        company_settings_group = QGroupBox("Company Information")
        company_settings_form_layout = QFormLayout(company_settings_group) 

        self.company_name_edit = QLineEdit()
        self.legal_name_edit = QLineEdit()
        self.uen_edit = QLineEdit()
        self.gst_reg_edit = QLineEdit()
        self.gst_registered_check = QCheckBox("GST Registered")
        self.base_currency_combo = QComboBox() 
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
        self.date_format_combo.addItems(["dd/MM/yyyy", "yyyy-MM-dd", "MM/dd/yyyy"])

        company_settings_form_layout.addRow("Company Name*:", self.company_name_edit)
        company_settings_form_layout.addRow("Legal Name:", self.legal_name_edit)
        company_settings_form_layout.addRow("UEN No:", self.uen_edit)
        company_settings_form_layout.addRow("GST Reg. No:", self.gst_reg_edit)
        company_settings_form_layout.addRow(self.gst_registered_check)
        company_settings_form_layout.addRow("Base Currency:", self.base_currency_combo)
        company_settings_form_layout.addRow("Address Line 1:", self.address_line1_edit)
        company_settings_form_layout.addRow("Address Line 2:", self.address_line2_edit)
        company_settings_form_layout.addRow("Postal Code:", self.postal_code_edit)
        company_settings_form_layout.addRow("City:", self.city_edit)
        company_settings_form_layout.addRow("Country:", self.country_edit)
        company_settings_form_layout.addRow("Contact Person:", self.contact_person_edit)
        company_settings_form_layout.addRow("Phone:", self.phone_edit)
        company_settings_form_layout.addRow("Email:", self.email_edit)
        company_settings_form_layout.addRow("Website:", self.website_edit)
        company_settings_form_layout.addRow("Fiscal Year Start Month:", self.fiscal_year_start_month_spin)
        company_settings_form_layout.addRow("Fiscal Year Start Day:", self.fiscal_year_start_day_spin)
        company_settings_form_layout.addRow("Tax ID Label:", self.tax_id_label_edit)
        company_settings_form_layout.addRow("Date Format:", self.date_format_combo)
        
        self.save_company_settings_button = QPushButton("Save Company Settings")
        self.save_company_settings_button.clicked.connect(self.on_save_company_settings)
        company_settings_form_layout.addRow(self.save_company_settings_button)
        
        company_tab_layout.addWidget(company_settings_group)
        company_tab_layout.addStretch() 
        self.tab_widget.addTab(self.company_settings_tab, "Company")

        # --- Fiscal Year Management Tab ---
        self.fiscal_year_tab = QWidget()
        fiscal_tab_main_layout = QVBoxLayout(self.fiscal_year_tab)
        
        fiscal_year_group = QGroupBox("Fiscal Year Management")
        fiscal_year_group_layout = QVBoxLayout(fiscal_year_group) 

        self.fiscal_years_table = QTableView()
        self.fiscal_years_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.fiscal_years_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.fiscal_years_table.horizontalHeader().setStretchLastSection(True)
        self.fiscal_years_table.setMinimumHeight(150) 
        self.fiscal_year_model = FiscalYearTableModel() 
        self.fiscal_years_table.setModel(self.fiscal_year_model)
        fiscal_year_group_layout.addWidget(self.fiscal_years_table)

        fy_button_layout = QHBoxLayout() 
        self.add_fy_button = QPushButton("Add New Fiscal Year...")
        self.add_fy_button.clicked.connect(self.on_add_fiscal_year)
        fy_button_layout.addWidget(self.add_fy_button)
        fy_button_layout.addStretch()
        fiscal_year_group_layout.addLayout(fy_button_layout)
        
        fiscal_tab_main_layout.addWidget(fiscal_year_group)
        fiscal_tab_main_layout.addStretch() 
        self.tab_widget.addTab(self.fiscal_year_tab, "Fiscal Years")

        # --- User Management Tab ---
        self.user_management_widget = UserManagementWidget(self.app_core)
        self.tab_widget.addTab(self.user_management_widget, "Users")

        # --- Role Management Tab ---
        self.role_management_widget = RoleManagementWidget(self.app_core)
        self.tab_widget.addTab(self.role_management_widget, "Roles & Permissions")

        # --- Audit Log Tab (New) ---
        self.audit_log_widget = AuditLogWidget(self.app_core)
        self.tab_widget.addTab(self.audit_log_widget, "Audit Logs")
        
        self.setLayout(self.main_layout) 

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self.load_initial_data()))

    async def load_initial_data(self):
        await self.load_company_settings()
        await self._load_fiscal_years() 

    async def load_company_settings(self):
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
                                         Q_ARG(str, json.dumps(active_currencies_data)))
                currencies_loaded_successfully = True
            except Exception as e:
                error_msg = f"Error loading currencies for settings: {e}"
                self.app_core.logger.error(error_msg, exc_info=True) 
                QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(QWidget, self), Q_ARG(str, "Currency Load Error"), Q_ARG(str, error_msg))
        
        if not currencies_loaded_successfully: 
            QMetaObject.invokeMethod(self.base_currency_combo, "addItems", Qt.ConnectionType.QueuedConnection, Q_ARG(list, ["SGD", "USD"]))

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        self._loaded_settings_obj = settings_obj 
        
        settings_data_for_ui_json: Optional[str] = None
        if settings_obj:
            settings_dict = { col.name: getattr(settings_obj, col.name) for col in CompanySetting.__table__.columns }
            settings_data_for_ui_json = json.dumps(settings_dict, default=json_converter)
        
        QMetaObject.invokeMethod(self, "_update_ui_from_settings_slot", Qt.ConnectionType.QueuedConnection, 
                                 Q_ARG(str, settings_data_for_ui_json if settings_data_for_ui_json else ""))

    @Slot(str) 
    def _populate_currency_combo_slot(self, currencies_json_str: str): 
        try: currencies_data: List[Dict[str,str]] = json.loads(currencies_json_str)
        except json.JSONDecodeError: currencies_data = [{"code": "SGD", "name": "Singapore Dollar"}] 
            
        current_selection = self.base_currency_combo.currentData()
        self.base_currency_combo.clear()
        if currencies_data: 
            for curr_data in currencies_data: self.base_currency_combo.addItem(f"{curr_data['code']} - {curr_data['name']}", curr_data['code']) 
        
        target_currency_code = current_selection
        if hasattr(self, '_loaded_settings_obj') and self._loaded_settings_obj and self._loaded_settings_obj.base_currency:
            target_currency_code = self._loaded_settings_obj.base_currency
        
        if target_currency_code:
            idx = self.base_currency_combo.findData(target_currency_code) 
            if idx != -1: 
                self.base_currency_combo.setCurrentIndex(idx)
            else: 
                idx_sgd = self.base_currency_combo.findData("SGD") 
                if idx_sgd != -1: self.base_currency_combo.setCurrentIndex(idx_sgd)
        elif self.base_currency_combo.count() > 0: self.base_currency_combo.setCurrentIndex(0)

    @Slot(str) 
    def _update_ui_from_settings_slot(self, settings_json_str: str):
        settings_data: Optional[Dict[str, Any]] = None
        if settings_json_str:
            try:
                settings_data = json.loads(settings_json_str, object_hook=json_date_hook)
            except json.JSONDecodeError: 
                QMessageBox.critical(self, "Error", "Failed to parse settings data."); settings_data = None

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
            
            date_fmt = settings_data.get("date_format", "dd/MM/yyyy") 
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
            if not self._loaded_settings_obj : 
                 QMessageBox.warning(self, "Settings", "Default company settings not found. Please configure.")

    @Slot()
    def on_save_company_settings(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Error", "No user logged in. Cannot save settings.")
            return
        selected_currency_code = self.base_currency_combo.currentData() or "SGD"
        dto = CompanySettingData(
            id=1, # Assuming ID 1 for company settings
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None, uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None, gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            address_line1=self.address_line1_edit.text() or None, address_line2=self.address_line2_edit.text() or None,
            postal_code=self.postal_code_edit.text() or None, city=self.city_edit.text() or "Singapore",
            country=self.country_edit.text() or "Singapore", contact_person=self.contact_person_edit.text() or None,
            phone=self.phone_edit.text() or None, email=self.email_edit.text() or None, 
            website=self.website_edit.text() or None,
            fiscal_year_start_month=self.fiscal_year_start_month_spin.value(), 
            fiscal_year_start_day=self.fiscal_year_start_day_spin.value(),  
            base_currency=selected_currency_code, 
            tax_id_label=self.tax_id_label_edit.text() or "UEN",       
            date_format=self.date_format_combo.currentText() or "dd/MM/yyyy", 
            logo=None 
        )
        schedule_task_from_qt(self.perform_save_company_settings(dto))

    async def perform_save_company_settings(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), 
                Q_ARG(str,"Company Settings Service not available."))
            return
        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            update_dict = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            for field_name, field_value in update_dict.items():
                if hasattr(orm_obj_to_save, field_name): 
                    if field_name == 'email' and field_value is not None: 
                        setattr(orm_obj_to_save, field_name, str(field_value))
                    else:
                        setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id', 'logo'}, exclude_none=False, by_alias=False)
            if 'email' in dict_data and dict_data['email'] is not None: dict_data['email'] = str(dict_data['email'])
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            if settings_data.id: orm_obj_to_save.id = settings_data.id 
        
        if self.app_core.current_user: orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 
        result_orm = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        message_title = "Success" if result_orm else "Error"
        message_text = "Company settings saved successfully." if result_orm else "Failed to save company settings."
        msg_box_method = QMessageBox.information if result_orm else QMessageBox.warning
        QMetaObject.invokeMethod(msg_box_method, "", Qt.ConnectionType.QueuedConnection, 
            Q_ARG(QWidget, self), Q_ARG(str, message_title), Q_ARG(str, message_text))

    async def _load_fiscal_years(self):
        if not self.app_core.fiscal_period_manager:
            self.app_core.logger.error("FiscalPeriodManager not available in SettingsWidget.")
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Service Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return
        try:
            fy_orms: List[FiscalYear] = await self.app_core.fiscal_period_manager.get_all_fiscal_years()
            fy_dtos_for_table: List[FiscalYearData] = []
            for fy_orm in fy_orms:
                fy_dtos_for_table.append(FiscalYearData(
                    id=fy_orm.id, year_name=fy_orm.year_name, start_date=fy_orm.start_date,
                    end_date=fy_orm.end_date, is_closed=fy_orm.is_closed, closed_date=fy_orm.closed_date,
                    periods=[] 
                ))
            
            fy_json_data = json.dumps([dto.model_dump(mode='json') for dto in fy_dtos_for_table])
            QMetaObject.invokeMethod(self, "_update_fiscal_years_table_slot", Qt.ConnectionType.QueuedConnection,
                                     Q_ARG(str, fy_json_data))
        except Exception as e:
            error_msg = f"Error loading fiscal years: {str(e)}"
            self.app_core.logger.error(error_msg, exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Fiscal Year Load Error"), Q_ARG(str, error_msg))

    @Slot(str)
    def _update_fiscal_years_table_slot(self, fy_json_list_str: str):
        try:
            fy_dict_list = json.loads(fy_json_list_str, object_hook=json_date_hook) 
            fy_dtos: List[FiscalYearData] = [FiscalYearData.model_validate(item_dict) for item_dict in fy_dict_list]
            self.fiscal_year_model.update_data(fy_dtos)
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Data Error", f"Failed to parse fiscal year data: {e}")
        except Exception as e_val: 
            QMessageBox.critical(self, "Data Error", f"Invalid fiscal year data format: {e_val}")

    @Slot()
    def on_add_fiscal_year(self):
        if not self.app_core.current_user:
            QMessageBox.warning(self, "Authentication Error", "No user logged in.")
            return
        
        dialog = FiscalYearDialog(self.app_core, self.app_core.current_user.id, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            fy_create_data = dialog.get_fiscal_year_data()
            if fy_create_data:
                schedule_task_from_qt(self._perform_add_fiscal_year(fy_create_data))

    async def _perform_add_fiscal_year(self, fy_data: FiscalYearCreateData):
        if not self.app_core.fiscal_period_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Fiscal Period Manager not available."))
            return

        result: Result[FiscalYear] = await self.app_core.fiscal_period_manager.create_fiscal_year_and_periods(fy_data)

        if result.is_success:
            assert result.value is not None
            msg = f"Fiscal Year '{result.value.year_name}' created successfully."
            if fy_data.auto_generate_periods: 
                msg += f" Periods auto-generated as per selection."
            
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, msg))
            schedule_task_from_qt(self._load_fiscal_years()) 
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, f"Failed to create fiscal year:\n{', '.join(result.errors)}"))


```

# app/ui/settings/user_table_model.py
```py
# File: app/ui/settings/user_table_model.py
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.utils.pydantic_models import UserSummaryData

class UserTableModel(QAbstractTableModel):
    def __init__(self, data: Optional[List[UserSummaryData]] = None, parent=None):
        super().__init__(parent)
        self._headers = ["ID", "Username", "Full Name", "Email", "Roles", "Active", "Last Login"]
        self._data: List[UserSummaryData] = data or []

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
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
            
        user_summary: UserSummaryData = self._data[row]

        if role == Qt.ItemDataRole.DisplayRole:
            header_key = self._headers[col].lower().replace(' ', '_')
            
            if col == 0: return str(user_summary.id)
            if col == 1: return user_summary.username
            if col == 2: return user_summary.full_name or ""
            if col == 3: return str(user_summary.email) if user_summary.email else ""
            if col == 4: return ", ".join(user_summary.roles) if user_summary.roles else "N/A"
            if col == 5: return "Yes" if user_summary.is_active else "No"
            if col == 6: 
                # Ensure last_login is datetime before formatting
                last_login_val = user_summary.last_login
                if isinstance(last_login_val, str): # It might come as ISO string from JSON
                    try:
                        last_login_val = datetime.fromisoformat(last_login_val.replace('Z', '+00:00'))
                    except ValueError:
                        return "Invalid Date" # Or keep original string
                
                return last_login_val.strftime('%d/%m/%Y %H:%M') if isinstance(last_login_val, datetime) else "Never"
            
            return str(getattr(user_summary, header_key, ""))

        elif role == Qt.ItemDataRole.UserRole:
            if col == 0: # Store ID with the first column
                return user_summary.id
        
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if self._headers[col] == "Active":
                return Qt.AlignmentFlag.AlignCenter
        
        return None

    def get_user_id_at_row(self, row: int) -> Optional[int]:
        if 0 <= row < len(self._data):
            index = self.index(row, 0) 
            id_val = self.data(index, Qt.ItemDataRole.UserRole)
            if id_val is not None: return int(id_val)
            return self._data[row].id 
        return None
        
    def get_user_active_status_at_row(self, row: int) -> Optional[bool]:
        if 0 <= row < len(self._data):
            return self._data[row].is_active
        return None
        
    def get_username_at_row(self, row: int) -> Optional[str]:
        if 0 <= row < len(self._data):
            return self._data[row].username
        return None

    def update_data(self, new_data: List[UserSummaryData]):
        self.beginResetModel()
        self._data = new_data or []
        self.endResetModel()

```

# app/ui/settings/role_management_widget.py
```py
# File: app/ui/settings/role_management_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QPushButton, QToolBar, 
    QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG, QModelIndex, QSize
from PySide6.QtGui import QIcon, QAction
from typing import Optional, List, TYPE_CHECKING

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.ui.settings.role_table_model import RoleTableModel
from app.ui.settings.role_dialog import RoleDialog # Import RoleDialog
from app.utils.pydantic_models import RoleData
from app.utils.json_helpers import json_converter
from app.utils.result import Result
from app.models.core.user import Role 

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class RoleManagementWidget(QWidget):
    def __init__(self, app_core: ApplicationCore, parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        
        self.icon_path_prefix = "resources/icons/" 
        try:
            import app.resources_rc 
            self.icon_path_prefix = ":/icons/"
        except ImportError:
            pass 
        
        self._init_ui()
        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_roles()))

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(5)

        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar)

        self.roles_table = QTableView()
        self.roles_table.setAlternatingRowColors(True)
        self.roles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.roles_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.roles_table.horizontalHeader().setStretchLastSection(True) 
        self.roles_table.setSortingEnabled(True)
        self.roles_table.doubleClicked.connect(self._on_edit_role_double_click)

        self.table_model = RoleTableModel()
        self.roles_table.setModel(self.table_model)
        
        header = self.roles_table.horizontalHeader()
        id_col_idx = self.table_model._headers.index("ID") if "ID" in self.table_model._headers else -1
        if id_col_idx != -1: self.roles_table.setColumnHidden(id_col_idx, True)
        
        header.setSectionResizeMode(self.table_model._headers.index("Name"), QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.table_model._headers.index("Description"), QHeaderView.ResizeMode.Stretch)
        
        self.main_layout.addWidget(self.roles_table)
        self.setLayout(self.main_layout)

        if self.roles_table.selectionModel():
            self.roles_table.selectionModel().selectionChanged.connect(self._update_action_states)
        self._update_action_states()

    def _create_toolbar(self):
        self.toolbar = QToolBar("Role Management Toolbar")
        self.toolbar.setIconSize(QSize(16, 16))

        self.toolbar_add_action = QAction(QIcon(self.icon_path_prefix + "add.svg"), "Add Role", self)
        self.toolbar_add_action.triggered.connect(self._on_add_role)
        self.toolbar.addAction(self.toolbar_add_action)

        self.toolbar_edit_action = QAction(QIcon(self.icon_path_prefix + "edit.svg"), "Edit Role", self)
        self.toolbar_edit_action.triggered.connect(self._on_edit_role)
        self.toolbar.addAction(self.toolbar_edit_action)

        self.toolbar_delete_action = QAction(QIcon(self.icon_path_prefix + "remove.svg"), "Delete Role", self)
        self.toolbar_delete_action.triggered.connect(self._on_delete_role)
        self.toolbar.addAction(self.toolbar_delete_action)
        
        self.toolbar.addSeparator()
        self.toolbar_refresh_action = QAction(QIcon(self.icon_path_prefix + "refresh.svg"), "Refresh List", self)
        self.toolbar_refresh_action.triggered.connect(lambda: schedule_task_from_qt(self._load_roles()))
        self.toolbar.addAction(self.toolbar_refresh_action)

    @Slot()
    def _update_action_states(self):
        selected_rows = self.roles_table.selectionModel().selectedRows()
        single_selection = len(selected_rows) == 1
        can_modify = False
        is_admin_role_selected = False

        if single_selection:
            can_modify = True
            row_idx = selected_rows[0].row()
            role_name = self.table_model.get_role_name_at_row(row_idx)
            if role_name == "Administrator":
                is_admin_role_selected = True
        
        self.toolbar_edit_action.setEnabled(can_modify) 
        self.toolbar_delete_action.setEnabled(can_modify and not is_admin_role_selected)

    async def _load_roles(self):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str,"Security Manager component not available."))
            return
        try:
            roles_orm: List[Role] = await self.app_core.security_manager.get_all_roles()
            roles_dto: List[RoleData] = [RoleData.model_validate(r) for r in roles_orm]
            json_data = json.dumps([r.model_dump() for r in roles_dto], default=json_converter)
            QMetaObject.invokeMethod(self, "_update_table_model_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, json_data))
        except Exception as e:
            self.app_core.logger.error(f"Unexpected error loading roles: {e}", exc_info=True)
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Load Error"), Q_ARG(str, f"Unexpected error loading roles: {str(e)}"))

    @Slot(str)
    def _update_table_model_slot(self, json_data_str: str):
        try:
            list_of_dicts = json.loads(json_data_str) 
            role_dtos: List[RoleData] = [RoleData.model_validate(item) for item in list_of_dicts]
            self.table_model.update_data(role_dtos)
        except Exception as e: 
            self.app_core.logger.error(f"Failed to parse/validate role data for table: {e}", exc_info=True)
            QMessageBox.critical(self, "Data Error", f"Failed to parse/validate role data: {e}")
        finally:
            self._update_action_states()

    @Slot()
    def _on_add_role(self):
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    def _get_selected_role_id(self) -> Optional[int]:
        selected_rows = self.roles_table.selectionModel().selectedRows()
        if not selected_rows: return None
        if len(selected_rows) > 1: return None # Only operate on single selection for edit/delete
        return self.table_model.get_role_id_at_row(selected_rows[0].row())

    @Slot()
    def _on_edit_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to edit.")
            return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        role_name = self.table_model.get_role_name_at_row(self.roles_table.currentIndex().row())
        if role_name == "Administrator" and self.name_edit.text().strip() != "Administrator": # self.name_edit does not exist here. This check is in RoleDialog.
             # This check is better placed within RoleDialog or SecurityManager. For now, allow opening.
             pass

        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot(QModelIndex)
    def _on_edit_role_double_click(self, index: QModelIndex):
        if not index.isValid(): return
        role_id = self.table_model.get_role_id_at_row(index.row())
        if role_id is None: return
        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        dialog = RoleDialog(self.app_core, self.app_core.current_user.id, role_id_to_edit=role_id, parent=self)
        dialog.role_saved.connect(self._refresh_list_after_save)
        dialog.exec()

    @Slot()
    def _on_delete_role(self):
        role_id = self._get_selected_role_id()
        if role_id is None: 
            QMessageBox.information(self, "Selection", "Please select a single role to delete.")
            return
        
        role_name = self.table_model.get_role_name_at_row(self.roles_table.currentIndex().row())
        if role_name == "Administrator":
            QMessageBox.warning(self, "Action Denied", "The 'Administrator' role cannot be deleted.")
            return

        if not self.app_core.current_user: QMessageBox.warning(self, "Auth Error", "Please log in."); return
        
        reply = QMessageBox.question(self, "Confirm Deletion",
                                     f"Are you sure you want to delete the role '{role_name}' (ID: {role_id})?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No: return

        future = schedule_task_from_qt(
            self.app_core.security_manager.delete_role(role_id, self.app_core.current_user.id)
        )
        if future: future.add_done_callback(self._handle_delete_role_result)
        else: self._handle_delete_role_result(None)

    def _handle_delete_role_result(self, future):
        if future is None: QMessageBox.critical(self, "Task Error", "Failed to schedule role deletion."); return
        try:
            result: Result[None] = future.result()
            if result.is_success:
                QMessageBox.information(self, "Success", "Role deleted successfully.")
                schedule_task_from_qt(self._load_roles()) 
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete role:\n{', '.join(result.errors)}")
        except Exception as e:
            self.app_core.logger.error(f"Error handling role deletion result: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"An unexpected error occurred during role deletion: {str(e)}")
        finally:
            self._update_action_states() 

    @Slot(int)
    def _refresh_list_after_save(self, role_id: int):
        self.app_core.logger.info(f"RoleDialog reported save for Role ID: {role_id}. Refreshing role list.")
        schedule_task_from_qt(self._load_roles())

```

# app/ui/settings/role_dialog.py
```py
# app/ui/settings/role_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QLabel, QTextEdit, QListWidget, QListWidgetItem, QAbstractItemView,
    QGroupBox 
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import RoleCreateData, RoleUpdateData, RoleData, PermissionData
from app.models.core.user import Role # ORM for loading
from app.utils.result import Result
from app.utils.json_helpers import json_converter

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
        self.setMinimumWidth(500) 
        self.setMinimumHeight(450)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_data()))

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
        self.description_edit.setFixedHeight(60) 
        form_layout.addRow("Description:", self.description_edit)
        main_layout.addWidget(details_group)
        
        permissions_group = QGroupBox("Assign Permissions")
        permissions_layout = QVBoxLayout(permissions_group)
        self.permissions_list_widget = QListWidget()
        self.permissions_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
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
        perms_loaded_successfully = False
        try:
            if self.app_core.security_manager:
                # Fetch all permissions for the list widget
                self._all_permissions_cache = await self.app_core.security_manager.get_all_permissions()
                perms_json = json.dumps([p.model_dump() for p in self._all_permissions_cache]) # Use model_dump for Pydantic v2
                QMetaObject.invokeMethod(self, "_populate_permissions_list_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, perms_json))
                perms_loaded_successfully = True
        except Exception as e:
            self.app_core.logger.error(f"Error loading permissions for RoleDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load permissions: {str(e)}")
        
        if not perms_loaded_successfully:
            self.permissions_list_widget.addItem("Error loading permissions.")
            self.permissions_list_widget.setEnabled(False)

        # If editing, load the specific role's data (which includes its assigned permissions)
        if self.role_id_to_edit:
            try:
                if self.app_core.security_manager:
                    # get_role_by_id should eager load role.permissions
                    self.loaded_role_orm = await self.app_core.security_manager.get_role_by_id(self.role_id_to_edit)
                    if self.loaded_role_orm:
                        assigned_perm_ids = [p.id for p in self.loaded_role_orm.permissions]
                        role_dict = {
                            "id": self.loaded_role_orm.id, "name": self.loaded_role_orm.name,
                            "description": self.loaded_role_orm.description,
                            "assigned_permission_ids": assigned_perm_ids
                        }
                        role_json_str = json.dumps(role_dict, default=json_converter)
                        # This slot will populate fields and then call _select_assigned_permissions
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
            # Cache already updated in _load_initial_data, or update it here if preferred
            self._all_permissions_cache = [PermissionData.model_validate(p_dict) for p_dict in permissions_data_list]
            for perm_dto in self._all_permissions_cache:
                item_text = f"{perm_dto.module}: {perm_dto.code}"
                if perm_dto.description: item_text += f" - {perm_dto.description}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, perm_dto.id) 
                self.permissions_list_widget.addItem(item)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing permissions JSON for RoleDialog: {e}")
            self.permissions_list_widget.addItem("Error parsing permissions.")
        
        # If editing and role data was already loaded (which triggered field population),
        # and field population triggered _select_assigned_permissions, this re-selection might be redundant
        # or necessary if permissions list is populated after fields.
        # This is generally safe.
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

        is_admin_role = (role_data.get("name") == "Administrator")
        self.name_edit.setReadOnly(is_admin_role)
        self.name_edit.setToolTip("The 'Administrator' role name cannot be changed." if is_admin_role else "")
        
        # For Admin role, all permissions should be selected and the list disabled.
        if is_admin_role:
            for i in range(self.permissions_list_widget.count()):
                self.permissions_list_widget.item(i).setSelected(True)
            self.permissions_list_widget.setEnabled(False) 
            self.permissions_list_widget.setToolTip("Administrator role has all permissions by default and cannot be modified here.")
        else:
            self.permissions_list_widget.setEnabled(True)
            assigned_permission_ids = role_data.get("assigned_permission_ids", [])
            self._select_assigned_permissions(assigned_permission_ids)


    def _select_assigned_permissions(self, assigned_ids: List[int]):
        # Ensure this is called after permissions_list_widget is populated
        if self.permissions_list_widget.count() == 0 and self._all_permissions_cache:
             # Permissions list might not be populated yet if this is called too early from _populate_fields_slot
             # _load_initial_data should ensure permissions are populated first then calls _populate_fields_slot
             # which then calls this.
             self.app_core.logger.warning("_select_assigned_permissions called before permissions list populated.")
             return

        for i in range(self.permissions_list_widget.count()):
            item = self.permissions_list_widget.item(i)
            permission_id_in_item = item.data(Qt.ItemDataRole.UserRole)
            if permission_id_in_item in assigned_ids:
                item.setSelected(True)
            else:
                item.setSelected(False) 

    def _collect_data(self) -> Optional[Union[RoleCreateData, RoleUpdateData]]:
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip() or None
        
        if not name:
            QMessageBox.warning(self, "Validation Error", "Role Name is required.")
            return None
        
        # Cannot change name of Administrator role if editing it (already handled by read-only)
        if self.loaded_role_orm and self.loaded_role_orm.name == "Administrator" and name != "Administrator":
             QMessageBox.warning(self, "Validation Error", "Cannot change the name of 'Administrator' role.")
             self.name_edit.setText("Administrator") # Reset
             return None

        selected_permission_ids: List[int] = []
        if self.permissions_list_widget.isEnabled(): # Only collect if list is enabled (not admin role)
            for item in self.permissions_list_widget.selectedItems():
                perm_id = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(perm_id, int):
                    selected_permission_ids.append(perm_id)
        elif self.loaded_role_orm and self.loaded_role_orm.name == "Administrator":
            # For admin, all permissions are implicitly assigned if list is disabled
            selected_permission_ids = [p.id for p in self._all_permissions_cache]


        common_data = {"name": name, "description": description, "permission_ids": selected_permission_ids}

        try:
            if self.is_new_role:
                return RoleCreateData(**common_data) 
            else:
                assert self.role_id_to_edit is not None
                return RoleUpdateData(id=self.role_id_to_edit, **common_data) 
        except ValueError as pydantic_error: 
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
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


```

# app/ui/settings/user_dialog.py
```py
# File: app/ui/settings/user_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QDialogButtonBox, 
    QMessageBox, QCheckBox, QListWidget, QListWidgetItem, QAbstractItemView,
    QLabel
)
from PySide6.QtCore import Qt, Slot, Signal, QTimer, QMetaObject, Q_ARG
from typing import Optional, List, Dict, Any, TYPE_CHECKING, Union, cast

import json

from app.core.application_core import ApplicationCore
from app.main import schedule_task_from_qt
from app.utils.pydantic_models import UserCreateData, UserUpdateData, RoleData
from app.models.core.user import User, Role # For ORM type hints
from app.utils.result import Result
from app.utils.json_helpers import json_converter # For serializing roles if needed

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintDevice

class UserDialog(QDialog):
    user_saved = Signal(int) # Emits user ID

    def __init__(self, app_core: ApplicationCore, 
                 current_admin_user_id: int, 
                 user_id_to_edit: Optional[int] = None, 
                 parent: Optional["QWidget"] = None):
        super().__init__(parent)
        self.app_core = app_core
        self.current_admin_user_id = current_admin_user_id
        self.user_id_to_edit = user_id_to_edit
        self.loaded_user_orm: Optional[User] = None
        self._all_roles_cache: List[RoleData] = []

        self.is_new_user = self.user_id_to_edit is None
        self.setWindowTitle("Add New User" if self.is_new_user else "Edit User")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._init_ui()
        self._connect_signals()

        QTimer.singleShot(0, lambda: schedule_task_from_qt(self._load_initial_data()))

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)

        self.username_edit = QLineEdit()
        form_layout.addRow("Username*:", self.username_edit)

        self.full_name_edit = QLineEdit()
        form_layout.addRow("Full Name:", self.full_name_edit)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText("user@example.com")
        form_layout.addRow("Email:", self.email_edit)

        self.password_label = QLabel("Password*:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.password_label, self.password_edit)

        self.confirm_password_label = QLabel("Confirm Password*:")
        self.confirm_password_edit = QLineEdit()
        self.confirm_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow(self.confirm_password_label, self.confirm_password_edit)

        self.is_active_check = QCheckBox("User is Active")
        self.is_active_check.setChecked(True)
        form_layout.addRow(self.is_active_check)
        
        form_layout.addRow(QLabel("Assign Roles:"))
        self.roles_list_widget = QListWidget()
        self.roles_list_widget.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.roles_list_widget.setFixedHeight(120) # Adjust height as needed
        form_layout.addRow(self.roles_list_widget)

        main_layout.addLayout(form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

        if not self.is_new_user: # Editing existing user
            self.password_label.setVisible(False)
            self.password_edit.setVisible(False)
            self.confirm_password_label.setVisible(False)
            self.confirm_password_edit.setVisible(False)
            # Username might be non-editable for existing users for simplicity, or based on permissions
            # self.username_edit.setReadOnly(True) 


    def _connect_signals(self):
        self.button_box.accepted.connect(self.on_save)
        self.button_box.rejected.connect(self.reject)

    async def _load_initial_data(self):
        """Load all available roles and user data if editing."""
        roles_loaded_successfully = False
        try:
            if self.app_core.security_manager:
                roles_orm: List[Role] = await self.app_core.security_manager.get_all_roles()
                self._all_roles_cache = [RoleData.model_validate(r) for r in roles_orm]
                roles_json = json.dumps([r.model_dump() for r in self._all_roles_cache], default=json_converter)
                QMetaObject.invokeMethod(self, "_populate_roles_list_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, roles_json))
                roles_loaded_successfully = True
        except Exception as e:
            self.app_core.logger.error(f"Error loading roles for UserDialog: {e}", exc_info=True)
            QMessageBox.warning(self, "Data Load Error", f"Could not load roles: {str(e)}")

        if not roles_loaded_successfully:
            self.roles_list_widget.addItem("Error loading roles.")
            self.roles_list_widget.setEnabled(False)

        if self.user_id_to_edit:
            try:
                if self.app_core.security_manager:
                    self.loaded_user_orm = await self.app_core.security_manager.get_user_by_id_for_edit(self.user_id_to_edit)
                    if self.loaded_user_orm:
                        # Serialize user data for thread-safe UI update
                        user_dict = {
                            "id": self.loaded_user_orm.id,
                            "username": self.loaded_user_orm.username,
                            "full_name": self.loaded_user_orm.full_name,
                            "email": self.loaded_user_orm.email,
                            "is_active": self.loaded_user_orm.is_active,
                            "assigned_role_ids": [role.id for role in self.loaded_user_orm.roles]
                        }
                        user_json_str = json.dumps(user_dict, default=json_converter)
                        QMetaObject.invokeMethod(self, "_populate_fields_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, user_json_str))
                    else:
                        QMessageBox.warning(self, "Load Error", f"User ID {self.user_id_to_edit} not found.")
                        self.reject() # Close dialog if user not found
            except Exception as e:
                 self.app_core.logger.error(f"Error loading user (ID: {self.user_id_to_edit}) for edit: {e}", exc_info=True)
                 QMessageBox.warning(self, "Load Error", f"Could not load user details: {str(e)}")
                 self.reject()


    @Slot(str)
    def _populate_roles_list_slot(self, roles_json_str: str):
        self.roles_list_widget.clear()
        try:
            roles_data_list = json.loads(roles_json_str)
            self._all_roles_cache = [RoleData.model_validate(r_dict) for r_dict in roles_data_list]
            for role_dto in self._all_roles_cache:
                item = QListWidgetItem(f"{role_dto.name} ({role_dto.description or 'No description'})")
                item.setData(Qt.ItemDataRole.UserRole, role_dto.id) # Store role ID
                self.roles_list_widget.addItem(item)
        except json.JSONDecodeError as e:
            self.app_core.logger.error(f"Error parsing roles JSON for UserDialog: {e}")
            self.roles_list_widget.addItem("Error parsing roles.")
        
        # If editing, and user data already loaded, re-select roles
        if self.user_id_to_edit and self.loaded_user_orm:
            self._select_assigned_roles([role.id for role in self.loaded_user_orm.roles])


    @Slot(str)
    def _populate_fields_slot(self, user_json_str: str):
        try:
            user_data = json.loads(user_json_str) # No json_date_hook needed for UserSummaryData fields
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Failed to parse user data for editing."); return

        self.username_edit.setText(user_data.get("username", ""))
        self.full_name_edit.setText(user_data.get("full_name", "") or "")
        self.email_edit.setText(user_data.get("email", "") or "")
        self.is_active_check.setChecked(user_data.get("is_active", True))
        
        assigned_role_ids = user_data.get("assigned_role_ids", [])
        self._select_assigned_roles(assigned_role_ids)

        if self.loaded_user_orm and self.loaded_user_orm.username == "system_init_user":
            self._set_read_only_for_system_user()

    def _select_assigned_roles(self, assigned_role_ids: List[int]):
        for i in range(self.roles_list_widget.count()):
            item = self.roles_list_widget.item(i)
            role_id_in_item = item.data(Qt.ItemDataRole.UserRole)
            if role_id_in_item in assigned_role_ids:
                item.setSelected(True)
            else:
                item.setSelected(False)
    
    def _set_read_only_for_system_user(self):
        self.username_edit.setReadOnly(True)
        self.full_name_edit.setReadOnly(True)
        self.email_edit.setReadOnly(True)
        self.is_active_check.setEnabled(False) # Cannot deactivate system_init
        self.roles_list_widget.setEnabled(False) # Cannot change roles of system_init
        # Password fields are already hidden for edit mode
        ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
        if ok_button: ok_button.setEnabled(False) # Prevent saving changes


    def _collect_data(self) -> Optional[Union[UserCreateData, UserUpdateData]]:
        username = self.username_edit.text().strip()
        full_name = self.full_name_edit.text().strip() or None
        email_str = self.email_edit.text().strip() or None
        is_active = self.is_active_check.isChecked()
        
        selected_role_ids: List[int] = []
        for item in self.roles_list_widget.selectedItems():
            role_id = item.data(Qt.ItemDataRole.UserRole)
            if isinstance(role_id, int):
                selected_role_ids.append(role_id)
        
        common_data = {
            "username": username, "full_name": full_name, "email": email_str,
            "is_active": is_active, "assigned_role_ids": selected_role_ids,
            "user_id": self.current_admin_user_id # The user performing the action
        }

        try:
            if self.is_new_user:
                password = self.password_edit.text()
                confirm_password = self.confirm_password_edit.text()
                if not password: # Basic check, Pydantic handles min_length
                     QMessageBox.warning(self, "Validation Error", "Password is required for new users.")
                     return None
                return UserCreateData(password=password, confirm_password=confirm_password, **common_data) # type: ignore
            else:
                assert self.user_id_to_edit is not None
                return UserUpdateData(id=self.user_id_to_edit, **common_data) # type: ignore
        except ValueError as pydantic_error: # Catches Pydantic validation errors
            QMessageBox.warning(self, "Validation Error", f"Invalid data:\n{str(pydantic_error)}")
            return None

    @Slot()
    def on_save(self):
        dto = self._collect_data()
        if dto:
            ok_button = self.button_box.button(QDialogButtonBox.StandardButton.Ok)
            if ok_button: ok_button.setEnabled(False)
            
            future = schedule_task_from_qt(self._perform_save(dto))
            if future:
                future.add_done_callback(
                    lambda _: ok_button.setEnabled(True) if ok_button else None
                )
            else: # Handle scheduling failure
                if ok_button: ok_button.setEnabled(True)


    async def _perform_save(self, dto: Union[UserCreateData, UserUpdateData]):
        if not self.app_core.security_manager:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Security Manager not available."))
            return

        result: Result[User]
        if isinstance(dto, UserCreateData):
            result = await self.app_core.security_manager.create_user_with_roles(dto)
        elif isinstance(dto, UserUpdateData):
            result = await self.app_core.security_manager.update_user_from_dto(dto)
        else: # Should not happen
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "critical", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Error"), Q_ARG(str, "Invalid DTO type for save."))
            return

        if result.is_success and result.value:
            action = "updated" if self.user_id_to_edit else "created"
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "information", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Success"), Q_ARG(str, f"User '{result.value.username}' {action} successfully."))
            self.user_saved.emit(result.value.id)
            QMetaObject.invokeMethod(self, "accept", Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(QMessageBox.staticMetaObject, "warning", Qt.ConnectionType.QueuedConnection,
                Q_ARG(QWidget, self), Q_ARG(str, "Save Error"), Q_ARG(str, f"Failed to save user:\n{', '.join(result.errors)}"))

```


# app/main.py
```py
# File: app/main.py
# (This version incorporates the diff changes: no separate asyncio thread management in main, adjusted messages)
import sys
import asyncio
# import threading # Removed based on diff
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox 
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication 
from PySide6.QtGui import QPixmap

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager

# async_event_loop = None # Removed based on diff
# async_loop_thread = None # Removed based on diff

class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        self.setApplicationName("SG Bookkeeper")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("SGBookkeeperOrg") 
        self.setOrganizationDomain("sgbookkeeper.org")
        
        splash_pixmap = None
        try:
            import app.resources_rc # type: ignore
            splash_pixmap = QPixmap(":/images/splash.png")
            print("Using compiled Qt resources.")
        except ImportError:
            print("Compiled Qt resources (resources_rc.py) not found. Using direct file paths.") # Diff adjusted message
            splash_pixmap = QPixmap("resources/images/splash.png")

        if splash_pixmap is None or splash_pixmap.isNull():
            print("Warning: Splash image not found or invalid. Using fallback.")
            self.splash = QSplashScreen()
            pm = QPixmap(400,200)
            pm.fill(Qt.GlobalColor.lightGray)
            self.splash.setPixmap(pm)
            self.splash.showMessage("Loading SG Bookkeeper...", 
                                    Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignBottom, 
                                    Qt.GlobalColor.black)
        else:
            self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)

        self.splash.show()
        self.processEvents() 
        
        self.main_window = None
        self.app_core = None

        QTimer.singleShot(100, self.initialize_app_async_wrapper)

    def initialize_app_async_wrapper(self):
        # This version implies asyncio.run will be called directly if no external loop.
        # If an external loop (e.g. from pytest-asyncio) is already running,
        # asyncio.run() will raise a RuntimeError.
        # A robust solution for desktop apps is often a dedicated asyncio bridge for Qt.
        # For simplicity here, we try asyncio.run and catch common runtime errors.
        try:
            asyncio.run(self.initialize_app())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # This means an event loop is already running (e.g. in test environment or by another part of app)
                # We need to schedule initialize_app onto that existing loop.
                # This part is tricky without knowing the context of the existing loop.
                # For now, if this happens, we might log an error or try to get the running loop.
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.initialize_app()) # Schedule on existing loop
                except RuntimeError: # If get_running_loop also fails
                     QMessageBox.critical(None, "Asyncio Error", f"Failed to initialize application on existing event loop: {e}")
                     self.quit()
            else:
                 QMessageBox.critical(None, "Asyncio Error", f"Failed to initialize application: {e}")
                 self.quit()


    async def initialize_app(self):
        try:
            self.splash.showMessage("Loading configuration...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            
            config_manager = ConfigManager(app_name=QCoreApplication.applicationName())

            self.splash.showMessage("Initializing database manager...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            db_manager = DatabaseManager(config_manager)
            
            self.splash.showMessage("Initializing application core...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            self.app_core = ApplicationCore(config_manager, db_manager)

            await self.app_core.startup()

            if not self.app_core.current_user:
                if not await self.app_core.security_manager.authenticate_user("admin", "password"):
                    # Diff adjusted message:
                    QMessageBox.information(None, "Initial Setup", "Default admin login failed. Please ensure the database is initialized with an admin user, or proceed to user setup if available.")

            self.splash.showMessage("Loading main interface...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            self.main_window = MainWindow(self.app_core) 
            
            self.main_window.show()
            self.splash.finish(self.main_window)
        except Exception as e:
            self.splash.hide() 
            if self.main_window: self.main_window.hide()
            print(f"Critical error during application startup: {e}") 
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Application Initialization Error", 
                                 f"An error occurred during application startup:\n{str(e)[:500]}\n\nThe application will now exit.")
            self.quit()

    async def shutdown_app_async(self):
        if self.app_core:
            await self.app_core.shutdown()

    def shutdown_app(self):
        print("Application shutting down...")
        if self.app_core:
            try:
                # Try to get a running loop if one exists to run shutdown
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # This is complex if the loop is Qt's main loop or another thread's
                    # For simplicity, try to run it; may need platform-specific async-to-sync bridge
                    asyncio.run_coroutine_threadsafe(self.shutdown_app_async(), loop).result(5)
                else:
                    loop.run_until_complete(self.shutdown_app_async())
            except RuntimeError: # No event loop, or cannot run in current state
                 # Fallback: try a new loop just for this if no other is available/usable
                try:
                    asyncio.run(self.shutdown_app_async())
                except RuntimeError: # If even that fails
                    print("Warning: Could not execute async shutdown cleanly.")
                    pass 
            except Exception as e:
                 print(f"Error during async shutdown: {e}")

        print("Application shutdown process complete.")

def main():
    try:
        import app.resources_rc 
        print("Successfully imported compiled Qt resources (resources_rc.py).")
    except ImportError:
        # Diff adjusted message:
        print("Warning: Compiled Qt resources (resources_rc.py) not found. Direct file paths will be used for icons/images.")
        print("Consider running from project root: pyside6-rcc resources/resources.qrc -o app/resources_rc.py")

    app = Application(sys.argv)
    app.aboutToQuit.connect(app.shutdown_app) 
    
    exit_code = app.exec()
            
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

```

# app/__init__.py
```py
# File: app/__init__.py
# (Content as previously generated, no changes needed)

```

# app/core/config_manager.py
```py
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

# app/core/security_manager.py
```py
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

# app/core/__init__.py
```py
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

# app/core/database_manager.py
```py
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

# app/core/module_manager.py
```py
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

# app/core/application_core.py
```py
# File: app/core/application_core.py
# (This version incorporates the diff, meaning it's the more complete one from my previous generations)
from typing import Optional, Any
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager
from app.core.security_manager import SecurityManager
from app.core.module_manager import ModuleManager

from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
from app.accounting.journal_entry_manager import JournalEntryManager
from app.accounting.fiscal_period_manager import FiscalPeriodManager
from app.accounting.currency_manager import CurrencyManager

from app.services.account_service import AccountService
from app.services.journal_service import JournalService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.core_services import SequenceService, CompanySettingsService, ConfigurationService
from app.services.tax_service import TaxCodeService, GSTReturnService 
# Assuming accounting_services.py contains AccountTypeService, CurrencyRepoService, ExchangeRateService
# If they are split, import them directly. For this example, let's assume they are separate.
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService


from app.utils.sequence_generator import SequenceGenerator

from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine


class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        
        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._sequence_service_instance: Optional[SequenceService] = None
        self._company_settings_service_instance: Optional[CompanySettingsService] = None
        self._tax_code_service_instance: Optional[TaxCodeService] = None
        self._gst_return_service_instance: Optional[GSTReturnService] = None
        self._account_type_service_instance: Optional[AccountTypeService] = None
        self._currency_repo_service_instance: Optional[CurrencyRepoService] = None
        self._exchange_rate_service_instance: Optional[ExchangeRateService] = None
        self._configuration_service_instance: Optional[ConfigurationService] = None

        self._coa_manager_instance: Optional[ChartOfAccountsManager] = None
        self._je_manager_instance: Optional[JournalEntryManager] = None
        self._fp_manager_instance: Optional[FiscalPeriodManager] = None
        self._currency_manager_instance: Optional[CurrencyManager] = None
        self._gst_manager_instance: Optional[GSTManager] = None
        self._tax_calculator_instance: Optional[TaxCalculator] = None
        self._financial_statement_generator_instance: Optional[FinancialStatementGenerator] = None
        self._report_engine_instance: Optional[ReportEngine] = None

        print("ApplicationCore initialized.")

    async def startup(self):
        print("ApplicationCore starting up...")
        await self.db_manager.initialize()
        
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self.config_service_instance = ConfigurationService(self.db_manager) # Corrected attribute name
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        # These services would need to be created (e.g. app/services/accounting_services.py)
        # For now, assuming they are defined elsewhere and imported
        self._account_type_service_instance = AccountTypeService(self.db_manager) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)


        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        
        py_sequence_generator = SequenceGenerator(self.sequence_service)
        self._je_manager_instance = JournalEntryManager(
            self.journal_service, self.account_service, 
            self.fiscal_period_service, py_sequence_generator, self
        )
        self._fp_manager_instance = FiscalPeriodManager(self) 
        self._currency_manager_instance = CurrencyManager(self) 

        self._tax_calculator_instance = TaxCalculator(self.tax_code_service)
        self._gst_manager_instance = GSTManager(
            self.tax_code_service, self.journal_service, self.company_settings_service,
            self.gst_return_service, self.account_service, self.fiscal_period_service,
            py_sequence_generator, self
        )
        self._financial_statement_generator_instance = FinancialStatementGenerator(
            self.account_service, self.journal_service, self.fiscal_period_service,
            self.account_type_service, 
            self.tax_code_service, self.company_settings_service
        )
        self._report_engine_instance = ReportEngine(self)
        
        self.module_manager.load_all_modules()
        print("ApplicationCore startup complete.")

    async def shutdown(self):
        print("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        print("ApplicationCore shutdown complete.")

    @property
    def current_user(self): 
        return self.security_manager.get_current_user()

    @property
    def account_service(self) -> AccountService:
        if not self._account_service_instance: raise RuntimeError("AccountService not initialized.")
        return self._account_service_instance
    @property
    def journal_service(self) -> JournalService:
        if not self._journal_service_instance: raise RuntimeError("JournalService not initialized.")
        return self._journal_service_instance
    @property
    def fiscal_period_service(self) -> FiscalPeriodService:
        if not self._fiscal_period_service_instance: raise RuntimeError("FiscalPeriodService not initialized.")
        return self._fiscal_period_service_instance
    @property
    def sequence_service(self) -> SequenceService:
        if not self._sequence_service_instance: raise RuntimeError("SequenceService not initialized.")
        return self._sequence_service_instance
    @property
    def company_settings_service(self) -> CompanySettingsService:
        if not self._company_settings_service_instance: raise RuntimeError("CompanySettingsService not initialized.")
        return self._company_settings_service_instance
    @property
    def tax_code_service(self) -> TaxCodeService:
        if not self._tax_code_service_instance: raise RuntimeError("TaxCodeService not initialized.")
        return self._tax_code_service_instance
    @property
    def gst_return_service(self) -> GSTReturnService:
        if not self._gst_return_service_instance: raise RuntimeError("GSTReturnService not initialized.")
        return self._gst_return_service_instance
    @property
    def account_type_service(self) -> AccountTypeService: 
        if not self._account_type_service_instance: raise RuntimeError("AccountTypeService not initialized.")
        return self._account_type_service_instance 
    @property
    def currency_repo_service(self) -> CurrencyRepoService: 
        if not self._currency_repo_service_instance: raise RuntimeError("CurrencyRepoService not initialized.")
        return self._currency_repo_service_instance 
    @property
    def exchange_rate_service(self) -> ExchangeRateService: 
        if not self._exchange_rate_service_instance: raise RuntimeError("ExchangeRateService not initialized.")
        return self._exchange_rate_service_instance 
    @property
    def configuration_service(self) -> ConfigurationService: 
        if not self._configuration_service_instance: raise RuntimeError("ConfigurationService not initialized.")
        return self._configuration_service_instance


    @property
    def chart_of_accounts_manager(self) -> ChartOfAccountsManager:
        if not self._coa_manager_instance: raise RuntimeError("ChartOfAccountsManager not initialized.")
        return self._coa_manager_instance
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # Facade for UI, points to manager
        return self.chart_of_accounts_manager
    @property
    def journal_entry_manager(self) -> JournalEntryManager:
        if not self._je_manager_instance: raise RuntimeError("JournalEntryManager not initialized.")
        return self._je_manager_instance
    @property
    def fiscal_period_manager(self) -> FiscalPeriodManager: 
        if not self._fp_manager_instance: raise RuntimeError("FiscalPeriodManager not initialized.")
        return self._fp_manager_instance
    @property
    def currency_manager(self) -> CurrencyManager: 
        if not self._currency_manager_instance: raise RuntimeError("CurrencyManager not initialized.")
        return self._currency_manager_instance
    @property
    def gst_manager(self) -> GSTManager: 
        if not self._gst_manager_instance: raise RuntimeError("GSTManager not initialized.")
        return self._gst_manager_instance
    @property
    def tax_calculator(self) -> TaxCalculator: 
        if not self._tax_calculator_instance: raise RuntimeError("TaxCalculator not initialized.")
        return self._tax_calculator_instance
    @property
    def financial_statement_generator(self) -> FinancialStatementGenerator: 
        if not self._financial_statement_generator_instance: raise RuntimeError("FinancialStatementGenerator not initialized.")
        return self._financial_statement_generator_instance
    @property
    def report_engine(self) -> ReportEngine: 
        if not self._report_engine_instance: raise RuntimeError("ReportEngine not initialized.")
        return self._report_engine_instance

```

# app/ui/customers/__init__.py
```py
# File: app/ui/customers/__init__.py
# (Content as previously generated)
from .customers_widget import CustomersWidget

__all__ = ["CustomersWidget"]

```

# app/ui/customers/customers_widget.py
```py
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

# app/ui/__init__.py
```py
# File: app/ui/__init__.py
# (Content as previously generated)
from .main_window import MainWindow

__all__ = ["MainWindow"]

```

# app/ui/settings/__init__.py
```py
# File: app/ui/settings/__init__.py
# (Content as previously generated)
from .settings_widget import SettingsWidget

__all__ = ["SettingsWidget"]

```

# app/ui/settings/settings_widget.py
```py
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

# app/ui/banking/__init__.py
```py
# File: app/ui/banking/__init__.py
# (Content as previously generated)
from .banking_widget import BankingWidget

__all__ = ["BankingWidget"]

```

# app/ui/banking/banking_widget.py
```py
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

# app/ui/vendors/__init__.py
```py
# File: app/ui/vendors/__init__.py
# (Content as previously generated)
from .vendors_widget import VendorsWidget

__all__ = ["VendorsWidget"]

```

# app/ui/vendors/vendors_widget.py
```py
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

# app/ui/dashboard/__init__.py
```py
# File: app/ui/dashboard/__init__.py
# (Content as previously generated)
from .dashboard_widget import DashboardWidget

__all__ = ["DashboardWidget"]

```

# app/ui/dashboard/dashboard_widget.py
```py
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

# app/ui/main_window.py
```py
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

# app/ui/reports/__init__.py
```py
# File: app/ui/reports/__init__.py
# (Content as previously generated)
from .reports_widget import ReportsWidget

__all__ = ["ReportsWidget"]

```

# app/ui/reports/reports_widget.py
```py
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

# app/ui/accounting/__init__.py
```py
# File: app/ui/accounting/__init__.py
# (Content as previously generated)
from .accounting_widget import AccountingWidget
from .chart_of_accounts_widget import ChartOfAccountsWidget
from .account_dialog import AccountDialog

__all__ = ["AccountingWidget", "ChartOfAccountsWidget", "AccountDialog"]

```

# app/ui/accounting/chart_of_accounts_widget.py
```py
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

# app/ui/accounting/accounting_widget.py
```py
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

# app/models/__init__.py
```py
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

# app/models/base.py
```py
# File: app/models/base.py
# (Content previously generated, no changes needed)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy import DateTime, Integer, ForeignKey # Ensure Integer, ForeignKey are imported
from typing import Optional
import datetime

Base = declarative_base()

class TimestampMixin:
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=func.now(), server_default=func.now(), onupdate=func.now())

class UserAuditMixin:
    # Explicitly add ForeignKey references here as UserAuditMixin is generic.
    # The target table 'core.users' is known.
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

```

# app/models/core/__init__.py
```py
# File: app/models/core/__init__.py
# (Content previously generated)
from .configuration import Configuration
from .sequence import Sequence

__all__ = ["Configuration", "Sequence"]

```

# app/models/core/configuration.py
```py
# File: app/models/core/configuration.py
# New model for core.configuration table
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
# from app.models.user import User # For FK relationship
import datetime
from typing import Optional

class Configuration(Base, TimestampMixin):
    __tablename__ = 'configuration'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    config_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)

    # updated_by_user: Mapped[Optional["User"]] = relationship("User") # If User accessible

```

# app/models/core/company_setting.py
```py
# File: app/models/core/company_setting.py
# (Moved from app/models/company_setting.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, DateTime, LargeBinary, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User # For FK relationship type hint
import datetime
from typing import Optional

class CompanySetting(Base, TimestampMixin):
    __tablename__ = 'company_settings'
    __table_args__ = (
        CheckConstraint("fiscal_year_start_month BETWEEN 1 AND 12", name='ck_cs_fy_month'),
        CheckConstraint("fiscal_year_start_day BETWEEN 1 AND 31", name='ck_cs_fy_day'),
        {'schema': 'core'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True) 
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registration_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[str] = mapped_column(String(50), default='Singapore') 
    country: Mapped[str] = mapped_column(String(50), default='Singapore') 
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    logo: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1) 
    fiscal_year_start_day: Mapped[int] = mapped_column(Integer, default=1) 
    base_currency: Mapped[str] = mapped_column(String(3), default='SGD') 
    tax_id_label: Mapped[str] = mapped_column(String(50), default='UEN') 
    date_format: Mapped[str] = mapped_column(String(20), default='yyyy-MM-dd') 
    
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True) 

    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/core/sequence.py
```py
# File: app/models/core/sequence.py
# New model for core.sequences table
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin # Only TimestampMixin, no UserAuditMixin for this
from typing import Optional

class Sequence(Base, TimestampMixin):
    __tablename__ = 'sequences'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sequence_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    prefix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    suffix: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    next_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    increment_by: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    min_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    max_value: Mapped[int] = mapped_column(Integer, default=2147483647, nullable=False) # Max int4
    cycle: Mapped[bool] = mapped_column(Boolean, default=False)
    format_template: Mapped[str] = mapped_column(String(50), default='{PREFIX}{VALUE}{SUFFIX}')

```

# app/models/core/dimension.py.bak
```bak
# File: app/models/core/dimension.py
# New model for accounting.dimensions
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.user import User # For FKs
from typing import List, Optional

class Dimension(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'dimensions'
    __table_args__ = (
        UniqueConstraint('dimension_type', 'code', name='uq_dimensions_type_code'),
        {'schema': 'accounting'} # Reference schema places it in accounting
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension_type: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    
    parent: Mapped[Optional["Dimension"]] = relationship("Dimension", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Dimension"]] = relationship("Dimension", back_populates="parent")
    # created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by])
    # updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by])

```

# app/models/core/user.py
```py
# File: app/models/core/user.py
# (Moved from app/models/user.py and fields updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
import datetime 
from typing import List, Optional 

# Junction tables defined here using Base.metadata
user_roles_table = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

role_permissions_table = Table(
    'role_permissions', Base.metadata,
    Column('role_id', Integer, ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True),
    Column('permission_id', Integer, ForeignKey('core.permissions.id', ondelete="CASCADE"), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    schema='core'
)

class User(Base, TimestampMixin):
    __tablename__ = 'users'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True, index=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_login_attempt: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    require_password_change: Mapped[bool] = mapped_column(Boolean, default=False)
    
    roles: Mapped[List["Role"]] = relationship("Role", secondary=user_roles_table, back_populates="users")

class Role(Base, TimestampMixin):
    __tablename__ = 'roles'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    users: Mapped[List["User"]] = relationship("User", secondary=user_roles_table, back_populates="roles")
    permissions: Mapped[List["Permission"]] = relationship("Permission", secondary=role_permissions_table, back_populates="roles")

class Permission(Base): 
    __tablename__ = 'permissions'
    __table_args__ = {'schema': 'core'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) 
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False) 
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) # Only created_at

    roles: Mapped[List["Role"]] = relationship("Role", secondary=role_permissions_table, back_populates="permissions")

class UserRole(Base): 
    __tablename__ = 'user_roles' # Explicit model for junction table
    __table_args__ = {'schema': 'core'}
    user_id: Mapped[int] = mapped_column(ForeignKey('core.users.id', ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class RolePermission(Base): 
    __tablename__ = 'role_permissions' # Explicit model for junction table
    __table_args__ = {'schema': 'core'}
    role_id: Mapped[int] = mapped_column(ForeignKey('core.roles.id', ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[int] = mapped_column(ForeignKey('core.permissions.id', ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

```

# app/models/audit/__init__.py
```py
# File: app/models/audit/__init__.py
# (Content previously generated)
from .audit_log import AuditLog
from .data_change_history import DataChangeHistory

__all__ = ["AuditLog", "DataChangeHistory"]

```

# app/models/audit/audit_log.py
```py
# File: app/models/audit/audit_log.py
# New model for audit.audit_log table
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base
# from app.models.user import User # For FK relationship type hint
import datetime
from typing import Optional, Dict, Any

class AuditLog(Base):
    __tablename__ = 'audit_log'
    __table_args__ = {'schema': 'audit'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entity_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    changes: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # user: Mapped[Optional["User"]] = relationship("User") # If User model is accessible

```

# app/models/audit/data_change_history.py
```py
# File: app/models/audit/data_change_history.py
# New model for audit.data_change_history table
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base
# from app.models.user import User # For FK relationship type hint
import datetime
from typing import Optional

class DataChangeHistory(Base):
    __tablename__ = 'data_change_history'
    __table_args__ = {'schema': 'audit'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False) # Not necessarily FK, just the ID
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False) # CHECK constraint in DB
    changed_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=True)
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # changed_by_user: Mapped[Optional["User"]] = relationship("User") # If User model accessible

```

# app/models/business/customer.py
```py
# File: app/models/business/customer.py
# (Moved from app/models/customer.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List # Added List
from decimal import Decimal
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.models.core.user import User

class Customer(Base, TimestampMixin):
    __tablename__ = 'customers'
    __table_args__ = {'schema': 'business'} 

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    customer_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    legal_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uen_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    gst_registered: Mapped[bool] = mapped_column(Boolean, default=False)
    gst_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address_line1: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(50), default='Singapore')
    credit_terms: Mapped[int] = mapped_column(Integer, default=30) 
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    customer_since: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receivables_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by",Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by",Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code])
    receivables_account: Mapped[Optional["Account"]] = relationship("Account", back_populates="customer_receivables_links", foreign_keys=[receivables_account_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    sales_invoices: Mapped[List["SalesInvoice"]] = relationship("SalesInvoice", back_populates="customer") # type: ignore

```

# app/models/business/__init__.py
```py
# File: app/models/business/__init__.py
# (Content previously generated)
from .inventory_movement import InventoryMovement
from .sales_invoice import SalesInvoice, SalesInvoiceLine
from .purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine
from .bank_account import BankAccount
from .bank_transaction import BankTransaction
from .payment import Payment, PaymentAllocation

__all__ = [
    "InventoryMovement", 
    "SalesInvoice", "SalesInvoiceLine",
    "PurchaseInvoice", "PurchaseInvoiceLine",
    "BankAccount", "BankTransaction",
    "Payment", "PaymentAllocation",
]

```

# app/models/business/product.py
```py
# File: app/models/business/product.py
# (Moved from app/models/product.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List 
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.tax_code import TaxCode
from app.models.core.user import User

class Product(Base, TimestampMixin):
    __tablename__ = 'products'
    __table_args__ = (
        CheckConstraint("product_type IN ('Inventory', 'Service', 'Non-Inventory')", name='ck_products_product_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    product_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    unit_of_measure: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sales_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    sales_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    purchase_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    inventory_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=True)
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    min_stock_level: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    reorder_point: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    sales_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[sales_account_id], back_populates="product_sales_links")
    purchase_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[purchase_account_id], back_populates="product_purchase_links")
    inventory_account: Mapped[Optional["Account"]] = relationship("Account", foreign_keys=[inventory_account_id], back_populates="product_inventory_links")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code]) # Add back_populates to TaxCode if needed

    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    inventory_movements: Mapped[List["InventoryMovement"]] = relationship("InventoryMovement", back_populates="product") # type: ignore
    sales_invoice_lines: Mapped[List["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="product") # type: ignore
    purchase_invoice_lines: Mapped[List["PurchaseInvoiceLine"]] = relationship("PurchaseInvoiceLine", back_populates="product") # type: ignore

```

# app/models/business/vendor.py
```py
# File: app/models/business/vendor.py
# (Moved from app/models/vendor.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List # Added List
from decimal import Decimal
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.currency import Currency
from app.models.core.user import User

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

    purchase_invoices: Mapped[List["PurchaseInvoice"]] = relationship("PurchaseInvoice", back_populates="vendor") # type: ignore
    wht_certificates: Mapped[List["WithholdingTaxCertificate"]] = relationship("WithholdingTaxCertificate", back_populates="vendor") # type: ignore

```

# app/models/business/bank_account.py
```py
# File: app/models/business/bank_account.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account # Corrected path
from app.models.accounting.currency import Currency # Corrected path
from app.models.core.user import User
from typing import List, Optional
import datetime
from decimal import Decimal

class BankAccount(Base, TimestampMixin):
    __tablename__ = 'bank_accounts'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_swift_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    current_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    last_reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    gl_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    currency: Mapped["Currency"] = relationship("Currency")
    gl_account: Mapped["Account"] = relationship("Account", back_populates="bank_account_links")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    bank_transactions: Mapped[List["BankTransaction"]] = relationship("BankTransaction", back_populates="bank_account") # type: ignore
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="bank_account") # type: ignore

# Add back_populates to Account
Account.bank_account_links = relationship("BankAccount", back_populates="gl_account") # type: ignore

```

# app/models/business/purchase_invoice.py
```py
# File: app/models/business/purchase_invoice.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.vendor import Vendor # Corrected import path
from app.models.accounting.currency import Currency # Corrected import path
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
from typing import List, Optional
import datetime
from decimal import Decimal

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
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified
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

# Add back_populates to Vendor and Product:
Vendor.purchase_invoices = relationship("PurchaseInvoice", back_populates="vendor") # type: ignore
Product.purchase_invoice_lines = relationship("PurchaseInvoiceLine", back_populates="product") # type: ignore

```

# app/models/business/inventory_movement.py
```py
# File: app/models/business/inventory_movement.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin 
from app.models.business.product import Product
from app.models.core.user import User # For created_by FK
import datetime
from decimal import Decimal
from typing import Optional

class InventoryMovement(Base, TimestampMixin): 
    __tablename__ = 'inventory_movements'
    __table_args__ = (
        CheckConstraint("movement_type IN ('Purchase', 'Sale', 'Adjustment', 'Transfer', 'Return', 'Opening')", name='ck_inventory_movements_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.products.id'), nullable=False)
    movement_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    unit_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,4), nullable=True)
    total_cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(15,2), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="inventory_movements")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])

```

# app/models/business/payment.py
```py
# File: app/models/business/payment.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.bank_account import BankAccount
from app.models.accounting.currency import Currency # Corrected path
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from typing import List, Optional
import datetime
from decimal import Decimal

class Payment(Base, TimestampMixin):
    __tablename__ = 'payments'
    __table_args__ = (
        CheckConstraint("payment_type IN ('Customer Payment', 'Vendor Payment', 'Refund', 'Credit Note', 'Other')", name='ck_payments_payment_type'),
        CheckConstraint("payment_method IN ('Cash', 'Check', 'Bank Transfer', 'Credit Card', 'GIRO', 'PayNow', 'Other')", name='ck_payments_payment_method'),
        CheckConstraint("entity_type IN ('Customer', 'Vendor', 'Other')", name='ck_payments_entity_type'),
        CheckConstraint("status IN ('Draft', 'Approved', 'Completed', 'Voided', 'Returned')", name='ck_payments_status'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    payment_type: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bank_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15,6), default=Decimal(1))
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cheque_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='Draft', nullable=False)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    bank_account: Mapped[Optional["BankAccount"]] = relationship("BankAccount", back_populates="payments")
    currency: Mapped["Currency"] = relationship("Currency")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified
    allocations: Mapped[List["PaymentAllocation"]] = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class PaymentAllocation(Base, TimestampMixin):
    __tablename__ = 'payment_allocations'
    __table_args__ = (
        CheckConstraint("document_type IN ('Sales Invoice', 'Purchase Invoice', 'Credit Note', 'Debit Note', 'Other')", name='ck_payment_allocations_doc_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    payment_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.payments.id', ondelete="CASCADE"), nullable=False)
    document_type: Mapped[str] = mapped_column(String(20), nullable=False)
    document_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)

    payment: Mapped["Payment"] = relationship("Payment", back_populates="allocations")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])

```

# app/models/business/sales_invoice.py
```py
# File: app/models/business/sales_invoice.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.customer import Customer # Corrected import path
from app.models.accounting.currency import Currency # Corrected import path
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
from app.models.business.product import Product
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
from typing import List, Optional
import datetime
from decimal import Decimal

class SalesInvoice(Base, TimestampMixin):
    __tablename__ = 'sales_invoices'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Approved', 'Sent', 'Partially Paid', 'Paid', 'Overdue', 'Voided')", name='ck_sales_invoices_status'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.customers.id'), nullable=False)
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
    terms_and_conditions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    customer: Mapped["Customer"] = relationship("Customer", back_populates="sales_invoices")
    currency: Mapped["Currency"] = relationship("Currency")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified relationship
    lines: Mapped[List["SalesInvoiceLine"]] = relationship("SalesInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class SalesInvoiceLine(Base, TimestampMixin):
    __tablename__ = 'sales_invoice_lines'
    __table_args__ = {'schema': 'business'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.sales_invoices.id', ondelete="CASCADE"), nullable=False)
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
    
    invoice: Mapped["SalesInvoice"] = relationship("SalesInvoice", back_populates="lines")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="sales_invoice_lines")
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])

# Add back_populates to Customer and Product:
Customer.sales_invoices = relationship("SalesInvoice", back_populates="customer") # type: ignore
Product.sales_invoice_lines = relationship("SalesInvoiceLine", back_populates="product") # type: ignore

```

# app/models/business/bank_transaction.py
```py
# File: app/models/business/bank_transaction.py
# (Reviewed and confirmed path and fields from previous generation, ensure relationships set)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.business.bank_account import BankAccount
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry
import datetime
from decimal import Decimal
from typing import Optional

class BankTransaction(Base, TimestampMixin):
    __tablename__ = 'bank_transactions'
    __table_args__ = (
        CheckConstraint("transaction_type IN ('Deposit', 'Withdrawal', 'Transfer', 'Interest', 'Fee', 'Adjustment')", name='ck_bank_transactions_type'),
        {'schema': 'business'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_account_id: Mapped[int] = mapped_column(Integer, ForeignKey('business.bank_accounts.id'), nullable=False)
    transaction_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15,2), nullable=False)
    is_reconciled: Mapped[bool] = mapped_column(Boolean, default=False)
    reconciled_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    statement_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    bank_account: Mapped["BankAccount"] = relationship("BankAccount", back_populates="bank_transactions")
    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # Simplified
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/__init__.py
```py
# File: app/models/accounting/__init__.py
# New __init__.py for accounting models if moved to subdirectories
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
# (Content previously generated, but now placed in this path)
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
from app.models.business.vendor import Vendor 
import datetime
from decimal import Decimal
from typing import Optional

class WithholdingTaxCertificate(Base, TimestampMixin, UserAuditMixin):
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

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)

    vendor: Mapped["Vendor"] = relationship() 

```

# app/models/accounting/account.py
```py
# File: app/models/accounting/account.py
# (Moved from app/models/account.py and fields updated - completing relationships)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, CheckConstraint, Date, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import List, Optional 
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin 
from app.models.core.user import User 

# Forward string declarations for relationships
# These will be resolved by SQLAlchemy based on the string hints.
# "JournalEntryLine", "BudgetDetail", "TaxCode", "Customer", "Vendor", 
# "Product", "BankAccount"

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
    is_control_account: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bank_account: Mapped[bool] = mapped_column(Boolean, default=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    opening_balance_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
        
    # Self-referential relationship for parent/children
    parent: Mapped[Optional["Account"]] = relationship("Account", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Account"]] = relationship("Account", back_populates="parent")
    
    # Relationships to User for audit trails
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

    # Relationships defined by other models via back_populates
    journal_lines: Mapped[List["JournalEntryLine"]] = relationship(back_populates="account") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="account") # type: ignore
    
    # For TaxCode.affects_account_id
    tax_code_applications: Mapped[List["TaxCode"]] = relationship(back_populates="affects_account") # type: ignore
    
    # For Customer.receivables_account_id
    customer_receivables_links: Mapped[List["Customer"]] = relationship(back_populates="receivables_account") # type: ignore
    
    # For Vendor.payables_account_id
    vendor_payables_links: Mapped[List["Vendor"]] = relationship(back_populates="payables_account") # type: ignore
    
    # For Product fields (sales_account_id, purchase_account_id, inventory_account_id)
    product_sales_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.sales_account_id", back_populates="sales_account") # type: ignore
    product_purchase_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.purchase_account_id", back_populates="purchase_account") # type: ignore
    product_inventory_links: Mapped[List["Product"]] = relationship(foreign_keys="Product.inventory_account_id", back_populates="inventory_account") # type: ignore

    # For BankAccount.gl_account_id
    bank_account_links: Mapped[List["BankAccount"]] = relationship(back_populates="gl_account") # type: ignore


    def to_dict(self): # Kept from previous version, might be useful
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'account_type': self.account_type,
            'sub_type': self.sub_type,
            'parent_id': self.parent_id,
            'is_active': self.is_active,
            'description': self.description,
            'report_group': self.report_group,
            'is_control_account': self.is_control_account,
            'is_bank_account': self.is_bank_account,
            'opening_balance': self.opening_balance,
            'opening_balance_date': self.opening_balance_date,
        }

```

# app/models/accounting/gst_return.py
```py
# File: app/models/accounting/gst_return.py
# (Moved from app/models/gst_return.py and updated)
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.core.user import User
from app.models.accounting.journal_entry import JournalEntry

class GSTReturn(Base, TimestampMixin):
    __tablename__ = 'gst_returns'
    __table_args__ = (
        CheckConstraint("status IN ('Draft', 'Submitted', 'Amended')", name='ck_gst_returns_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    return_period: Mapped[str] = mapped_column(String(20), unique=True, nullable=False) 
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    filing_due_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    standard_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    zero_rated_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    exempt_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    total_supplies: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    taxable_purchases: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    output_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    input_tax: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_adjustments: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    tax_payable: Mapped[Decimal] = mapped_column(Numeric(15,2), default=Decimal(0))
    status: Mapped[str] = mapped_column(String(20), default='Draft')
    submission_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    submission_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    journal_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry") # No back_populates needed for one-to-one/opt-one
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/budget.py
```py
# File: app/models/accounting/budget.py
# (Moved from app/models/budget.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account 
from app.models.accounting.fiscal_year import FiscalYear
from app.models.accounting.fiscal_period import FiscalPeriod 
from app.models.accounting.dimension import Dimension 
from app.models.core.user import User
from typing import List, Optional 
from decimal import Decimal 

class Budget(Base, TimestampMixin): 
    __tablename__ = 'budgets'
    __table_args__ = {'schema': 'accounting'}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False) 
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year_obj: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="budgets")
    details: Mapped[List["BudgetDetail"]] = relationship("BudgetDetail", back_populates="budget", cascade="all, delete-orphan")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class BudgetDetail(Base, TimestampMixin): 
    __tablename__ = 'budget_details'
    __table_args__ = (
        # Reference schema has COALESCE(dimension1_id, 0), COALESCE(dimension2_id, 0) in UNIQUE.
        # This means NULLs are treated as 0 for uniqueness.
        # This is harder to model directly in SQLAlchemy UniqueConstraint if DB doesn't support function-based indexes for it directly.
        # For PostgreSQL, function-based unique indexes are possible.
        # For now, simple UniqueConstraint. DB schema will have the COALESCE logic.
        UniqueConstraint('budget_id', 'account_id', 'fiscal_period_id', 'dimension1_id', 'dimension2_id', name='uq_budget_details_key_dims_nullable'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    budget_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.budgets.id', ondelete="CASCADE"), nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    budget: Mapped["Budget"] = relationship("Budget", back_populates="details")
    account: Mapped["Account"] = relationship("Account", back_populates="budget_details")
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="budget_details")
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

# Add back-populates to Account and FiscalPeriod
Account.budget_details = relationship("BudgetDetail", back_populates="account") # type: ignore
FiscalPeriod.budget_details = relationship("BudgetDetail", back_populates="fiscal_period") # type: ignore

```

# app/models/accounting/exchange_rate.py
```py
# File: app/models/accounting/exchange_rate.py
# (Moved from app/models/exchange_rate.py and fields updated)
from sqlalchemy import Column, Integer, String, Date, Numeric, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.accounting.currency import Currency 
from app.models.core.user import User 
import datetime 
from decimal import Decimal 
from typing import Optional

class ExchangeRate(Base, TimestampMixin):
    __tablename__ = 'exchange_rates'
    __table_args__ = (
        UniqueConstraint('from_currency', 'to_currency', 'rate_date', name='uq_exchange_rates_pair_date'), 
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    from_currency_code: Mapped[str] = mapped_column("from_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    to_currency_code: Mapped[str] = mapped_column("to_currency", String(3), ForeignKey('accounting.currencies.code'), nullable=False)
    rate_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    exchange_rate_value: Mapped[Decimal] = mapped_column("exchange_rate", Numeric(15, 6), nullable=False) # Renamed attribute
    
    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    from_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[from_currency_code]) 
    to_currency_obj: Mapped["Currency"] = relationship("Currency", foreign_keys=[to_currency_code]) 
    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/journal_entry.py
```py
# File: app/models/accounting/journal_entry.py
# (Moved from app/models/journal_entry.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Numeric, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy.sql import func
from typing import List, Optional
import datetime
from decimal import Decimal

from app.models.base import Base, TimestampMixin
from app.models.accounting.account import Account
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.core.user import User
from app.models.accounting.currency import Currency
from app.models.accounting.tax_code import TaxCode
from app.models.accounting.dimension import Dimension
# from app.models.accounting.recurring_pattern import RecurringPattern # Forward reference with string

class JournalEntry(Base, TimestampMixin):
    __tablename__ = 'journal_entries'
    __table_args__ = {'schema': 'accounting'}
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    entry_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    journal_type: Mapped[str] = mapped_column(String(20), nullable=False) 
    entry_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_periods.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False)
    recurring_pattern_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.recurring_patterns.id'), nullable=True)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_reversed: Mapped[bool] = mapped_column(Boolean, default=False)
    reversing_entry_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', use_alter=True, name='fk_je_reversing_entry_id'), nullable=True)
    
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)
    
    fiscal_period: Mapped["FiscalPeriod"] = relationship("FiscalPeriod", back_populates="journal_entries")
    lines: Mapped[List["JournalEntryLine"]] = relationship("JournalEntryLine", back_populates="journal_entry", cascade="all, delete-orphan")
    generated_from_pattern: Mapped[Optional["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys=[recurring_pattern_id], back_populates="generated_journal_entries") # type: ignore
    
    reversing_entry: Mapped[Optional["JournalEntry"]] = relationship("JournalEntry", remote_side=[id], foreign_keys=[reversing_entry_id], uselist=False, post_update=True) # type: ignore
    template_for_patterns: Mapped[List["RecurringPattern"]] = relationship("RecurringPattern", foreign_keys="RecurringPattern.template_entry_id", back_populates="template_journal_entry") # type: ignore


    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

class JournalEntryLine(Base, TimestampMixin): 
    __tablename__ = 'journal_entry_lines'
    __table_args__ = (
        CheckConstraint(
            " (debit_amount > 0 AND credit_amount = 0) OR "
            " (credit_amount > 0 AND debit_amount = 0) OR "
            " (debit_amount = 0 AND credit_amount = 0) ", 
            name='jel_check_debit_credit'
        ),
        {'schema': 'accounting'}
    )
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    journal_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id', ondelete="CASCADE"), nullable=False)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.accounts.id'), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    debit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    credit_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    currency_code: Mapped[str] = mapped_column(String(3), ForeignKey('accounting.currencies.code'), default='SGD')
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(15, 6), default=Decimal(1))
    tax_code: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey('accounting.tax_codes.code'), nullable=True)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal(0))
    dimension1_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
    dimension2_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True) 
        
    journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", back_populates="lines")
    account: Mapped["Account"] = relationship("Account", back_populates="journal_lines")
    currency: Mapped["Currency"] = relationship("Currency", foreign_keys=[currency_code])
    tax_code_obj: Mapped[Optional["TaxCode"]] = relationship("TaxCode", foreign_keys=[tax_code])
    dimension1: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension1_id])
    dimension2: Mapped[Optional["Dimension"]] = relationship("Dimension", foreign_keys=[dimension2_id])
    
    @validates('debit_amount', 'credit_amount')
    def validate_amounts(self, key, value):
        value_decimal = Decimal(str(value)) 
        if key == 'debit_amount' and value_decimal > Decimal(0):
            self.credit_amount = Decimal(0)
        elif key == 'credit_amount' and value_decimal > Decimal(0):
            self.debit_amount = Decimal(0)
        return value_decimal

# Update Account relationships for journal_lines
Account.journal_lines = relationship("JournalEntryLine", back_populates="account") # type: ignore

```

# app/models/accounting/fiscal_year.py
```py
# File: app/models/accounting/fiscal_year.py
# (Previously generated as app/models/fiscal_year.py, reviewed and confirmed)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import DATERANGE # For GIST constraint if modeled in SQLAlchemy
# from sqlalchemy.sql.functions import GenericFunction # For functions like `daterange`
# from sqlalchemy.sql import literal_column
from app.models.base import Base, TimestampMixin # UserAuditMixin handled directly
from app.models.core.user import User
import datetime
from typing import List, Optional

class FiscalYear(Base, TimestampMixin):
    __tablename__ = 'fiscal_years'
    __table_args__ = (
        CheckConstraint('start_date <= end_date', name='fy_date_range_check'),
        # The EXCLUDE USING gist (daterange(start_date, end_date, '[]') WITH &&)
        # is a database-level constraint. SQLAlchemy doesn't model EXCLUDE directly in Core/ORM easily.
        # It's enforced by the DB schema from schema.sql.
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    year_name: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    closed_date: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by_user_id: Mapped[Optional[int]] = mapped_column("closed_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user_id: Mapped[int] = mapped_column("created_by",Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by",Integer, ForeignKey('core.users.id'), nullable=False)

    # Relationships
    closed_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[closed_by_user_id])
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    fiscal_periods: Mapped[List["FiscalPeriod"]] = relationship("FiscalPeriod", back_populates="fiscal_year") # type: ignore
    budgets: Mapped[List["Budget"]] = relationship("Budget", back_populates="fiscal_year_obj") # type: ignore

```

# app/models/accounting/fiscal_period.py
```py
# File: app/models/accounting/fiscal_period.py
# (Moved from app/models/fiscal_period.py and updated)
from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, UniqueConstraint, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.core.user import User
from typing import Optional, List

class FiscalPeriod(Base, TimestampMixin):
    __tablename__ = 'fiscal_periods'
    __table_args__ = (
        UniqueConstraint('fiscal_year_id', 'period_type', 'period_number', name='fp_unique_period_dates'),
        CheckConstraint('start_date <= end_date', name='fp_date_range_check'),
        CheckConstraint("period_type IN ('Month', 'Quarter', 'Year')", name='ck_fp_period_type'),
        CheckConstraint("status IN ('Open', 'Closed', 'Archived')", name='ck_fp_status'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    fiscal_year_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.fiscal_years.id'), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    period_type: Mapped[str] = mapped_column(String(10), nullable=False) 
    status: Mapped[str] = mapped_column(String(10), nullable=False, default='Open')
    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_adjustment: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    fiscal_year: Mapped["FiscalYear"] = relationship("FiscalYear", back_populates="fiscal_periods")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])
    
    journal_entries: Mapped[List["JournalEntry"]] = relationship(back_populates="fiscal_period") # type: ignore
    budget_details: Mapped[List["BudgetDetail"]] = relationship(back_populates="fiscal_period") # type: ignore

```

# app/models/accounting/tax_code.py
```py
# File: app/models/accounting/tax_code.py
# (Moved from app/models/tax_code.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, Numeric, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from typing import Optional, List # Added List
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

    # Relationship defined by other models via back_populates:
    # journal_entry_lines: Mapped[List["JournalEntryLine"]]
    # product_default_tax_codes: Mapped[List["Product"]]

# Add to Account model:
Account.tax_code_applications = relationship("TaxCode", back_populates="affects_account", foreign_keys=[TaxCode.affects_account_id]) # type: ignore

```

# app/models/accounting/dimension.py
```py
# File: app/models/accounting/dimension.py
# New model for accounting.dimensions
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin, UserAuditMixin
# from app.models.core.user import User # For FKs
from typing import List, Optional

class Dimension(Base, TimestampMixin, UserAuditMixin):
    __tablename__ = 'dimensions'
    __table_args__ = (
        UniqueConstraint('dimension_type', 'code', name='uq_dimensions_type_code'),
        {'schema': 'accounting'} 
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension_type: Mapped[str] = mapped_column(String(50), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('accounting.dimensions.id'), nullable=True)

    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by: Mapped[int] = mapped_column(Integer, ForeignKey('core.users.id'), nullable=False)
    
    parent: Mapped[Optional["Dimension"]] = relationship("Dimension", remote_side=[id], back_populates="children", foreign_keys=[parent_id])
    children: Mapped[List["Dimension"]] = relationship("Dimension", back_populates="parent")

```

# app/models/accounting/account_type.py
```py
# File: app/models/accounting/account_type.py
# (Moved from app/models/account_type.py and fields updated)
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

# app/models/accounting/recurring_pattern.py
```py
# File: app/models/accounting/recurring_pattern.py
# (Moved from app/models/recurring_pattern.py and updated)
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from typing import Optional, List # Added List
import datetime

from app.models.base import Base, TimestampMixin
from app.models.accounting.journal_entry import JournalEntry # For relationship type hint
from app.models.core.user import User

class RecurringPattern(Base, TimestampMixin):
    __tablename__ = 'recurring_patterns'
    __table_args__ = (
        CheckConstraint("frequency IN ('Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly')", name='ck_recurring_patterns_frequency'),
        CheckConstraint("day_of_month BETWEEN 1 AND 31", name='ck_recurring_patterns_day_of_month'),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name='ck_recurring_patterns_day_of_week'),
        {'schema': 'accounting'}
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    template_entry_id: Mapped[int] = mapped_column(Integer, ForeignKey('accounting.journal_entries.id'), nullable=False)
    
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    interval_value: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    start_date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    day_of_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    last_generated_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    next_generation_date: Mapped[Optional[datetime.date]] = mapped_column(Date, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_by_user_id: Mapped[int] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=False)
    updated_by_user_id: Mapped[int] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=False)

    template_journal_entry: Mapped["JournalEntry"] = relationship("JournalEntry", foreign_keys=[template_entry_id], back_populates="template_for_patterns")
    generated_journal_entries: Mapped[List["JournalEntry"]] = relationship("JournalEntry", foreign_keys="JournalEntry.recurring_pattern_id", back_populates="generated_from_pattern")
    created_by_user: Mapped["User"] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped["User"] = relationship("User", foreign_keys=[updated_by_user_id])

```

# app/models/accounting/currency.py
```py
# File: app/models/accounting/currency.py
# (Moved from app/models/currency.py and fields updated)
from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin
from app.models.core.user import User 
from typing import Optional

class Currency(Base, TimestampMixin):
    __tablename__ = 'currencies'
    __table_args__ = {'schema': 'accounting'}

    code: Mapped[str] = mapped_column(String(3), primary_key=True) 
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    decimal_places: Mapped[int] = mapped_column(Integer, default=2)
    format_string: Mapped[str] = mapped_column(String(20), default='#,##0.00') 

    created_by_user_id: Mapped[Optional[int]] = mapped_column("created_by", Integer, ForeignKey('core.users.id'), nullable=True)
    updated_by_user_id: Mapped[Optional[int]] = mapped_column("updated_by", Integer, ForeignKey('core.users.id'), nullable=True)

    created_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_user_id])
    updated_by_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[updated_by_user_id])

```


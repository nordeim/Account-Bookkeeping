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

# File: app/main.py
# (Content as provided before, verified for ApplicationCore startup/shutdown)
import sys
import asyncio
import threading # Required if using the threaded asyncio loop approach
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox # Added QMessageBox
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication # Added QCoreApplication
from PySide6.QtGui import QPixmap

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager

# Global variable for asyncio event loop if run in a separate thread
async_event_loop = None
async_loop_thread = None

class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        self.setApplicationName("SG Bookkeeper")
        self.setApplicationVersion("1.0.0")
        self.setOrganizationName("SGBookkeeperOrg") # Consistent org name
        self.setOrganizationDomain("sgbookkeeper.org")
        
        splash_pixmap = QPixmap("resources/images/splash.png") 
        # Check if resources_rc.py is imported and use QRC path if so:
        # try:
        #     import app.resources_rc # type: ignore
        #     splash_pixmap = QPixmap(":/images/splash.png")
        # except ImportError:
        #     splash_pixmap = QPixmap("resources/images/splash.png")


        if splash_pixmap.isNull():
            print("Warning: Splash image 'resources/images/splash.png' not found or invalid. Using fallback.")
            self.splash = QSplashScreen()
            fallback_label = QLabel("<h1>Loading SG Bookkeeper...</h1>") # Make it slightly more visible
            fallback_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # QSplashScreen doesn't have setCentralWidget. We can set a pixmap from a colored rect.
            pm = QPixmap(400,200)
            pm.fill(Qt.GlobalColor.lightGray)
            self.splash.setPixmap(pm)
            # A better fallback would be a QDialog as splash.
        else:
            self.splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)

        self.splash.show()
        self.processEvents() 
        
        self.main_window = None
        self.app_core = None

        QTimer.singleShot(100, self.initialize_app_async_wrapper)

    def initialize_app_async_wrapper(self):
        # This wrapper is to call the async initialize_app
        # It assumes an asyncio event loop is running and accessible
        # or it runs its own for this task.
        global async_event_loop
        if async_event_loop and async_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.initialize_app(), async_event_loop)
        else: # Fallback if no global loop running, run it synchronously for init
            try:
                asyncio.run(self.initialize_app())
            except RuntimeError as e:
                 QMessageBox.critical(None, "Asyncio Error", f"Failed to initialize application: {e}")
                 self.quit()


    async def initialize_app(self):
        """Deferred asynchronous initialization steps."""
        try:
            self.splash.showMessage("Loading configuration...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents() # More reliable than self.processEvents() from async context potentially
            
            config_manager = ConfigManager(app_name=QCoreApplication.applicationName()) # Pass app_name

            self.splash.showMessage("Initializing database manager...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            db_manager = DatabaseManager(config_manager)
            
            self.splash.showMessage("Initializing application core...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            self.app_core = ApplicationCore(config_manager, db_manager)

            await self.app_core.startup() # This is an async method

            # Example Authentication (replace with actual login UI flow)
            # For now, assume admin/password from initial_data.sql is used for dev.
            # Hashed password for 'password' is '$2b$12$DbmQO3qO3.xpLdf96nU6QOUHCw8F77sQZTN7q692xhoGf0A5bH9nC'
            # The initial_data.sql for users should have this.
            # The SecurityManager.authenticate_user will query DB.
            if not await self.app_core.security_manager.authenticate_user("admin", "password"): # Uses default admin
                # In a real app, show login dialog if auth fails or no user.
                # For now, if default admin fails, means DB data might be missing.
                 QMessageBox.warning(None, "Login Failed", "Default admin login failed. Check database initialization.")
                 # self.quit() # Or proceed as guest / show login
                 # For dev, allow to proceed.

            self.splash.showMessage("Loading main interface...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
            QApplication.processEvents()
            self.main_window = MainWindow(self.app_core) 
            
            self.main_window.show()
            self.splash.finish(self.main_window)
        except Exception as e:
            self.splash.hide() 
            # Ensure main_window is also hidden if it was somehow shown before error
            if self.main_window:
                self.main_window.hide()
            print(f"Critical error during application startup: {e}") # Log to console
            import traceback
            traceback.print_exc()
            QMessageBox.critical(None, "Application Initialization Error", 
                                 f"An error occurred during application startup:\n{e}\n\nThe application will now exit.")
            self.quit()


    async def shutdown_app_async(self):
        if self.app_core:
            await self.app_core.shutdown()

    def shutdown_app(self):
        print("Application shutting down...")
        
        global async_event_loop
        if self.app_core:
            if async_event_loop and async_event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.shutdown_app_async(), async_event_loop)
                try:
                    future.result(timeout=5) 
                except asyncio.TimeoutError: # Corrected exception type
                    print("Warning: Timeout during async shutdown.")
                except Exception as e:
                    print(f"Error during async shutdown: {e}")
            else:
                try:
                    # Create a new loop just for shutdown if none exists or old one closed
                    asyncio.run(self.shutdown_app_async())
                except RuntimeError: 
                    pass # Loop might be closed or already running within this scope
        print("Application shutdown process complete.")

def run_async_loop():
    global async_event_loop
    async_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_event_loop)
    try:
        async_event_loop.run_forever()
    finally:
        async_event_loop.close()

def main():
    # Start asyncio event loop in a separate thread
    # This allows Qt event loop to run in main thread and async tasks in another.
    # global async_loop_thread
    # async_loop_thread = threading.Thread(target=run_async_loop, daemon=True)
    # async_loop_thread.start()
    # A better approach might be to use a Qt-specific asyncio bridge like `qasync` or `qtinter`.
    # For this project, if most async operations are short or UI calls them via `asyncio.ensure_future`
    # managed by `QTimer` (like in `initialize_app_async_wrapper`), a separate thread might not be strictly
    # necessary for all cases, but it's safer for true async background work.
    # Given the complexity, the current `asyncio.run` within `initialize_app_async_wrapper` will block
    # the Qt event loop during that specific call if no external loop is provided.
    # The simplest for now is to rely on asyncio.run() for init and ensure_future for UI-triggered async tasks.

    app = Application(sys.argv)
    app.aboutToQuit.connect(app.shutdown_app) 
    
    exit_code = app.exec()
    
    # global async_event_loop, async_loop_thread
    # if async_event_loop and async_event_loop.is_running():
    #     async_event_loop.call_soon_threadsafe(async_event_loop.stop)
    # if async_loop_thread and async_loop_thread.is_alive():
    #     async_loop_thread.join(timeout=5)
        
    sys.exit(exit_code)

if __name__ == "__main__":
    # To use Qt Resource system, compile resources.qrc first:
    # pyside6-rcc resources/resources.qrc -o app/resources_rc.py
    # Then import it here:
    # try:
    #     import app.resources_rc # type: ignore
    # except ImportError:
    #     print("Warning: Compiled Qt resources (resources_rc.py) not found. Direct file paths will be used for icons/images.")
    #     print("Consider running: pyside6-rcc resources/resources.qrc -o app/resources_rc.py")
    main()

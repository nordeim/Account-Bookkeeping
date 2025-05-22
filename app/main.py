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

# File: app/main.py
# (Content as previously updated and verified)
import sys
import asyncio
import threading 
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication
from PySide6.QtGui import QPixmap

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager

async_event_loop = None
async_loop_thread = None

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
            print("Compiled Qt resources (resources_rc.py) not found. Using direct file paths.")
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
        global async_event_loop
        if async_event_loop and async_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(self.initialize_app(), async_event_loop)
        else: 
            try:
                asyncio.run(self.initialize_app())
            except RuntimeError as e:
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
                    QMessageBox.information(None, "Initial Setup", "Default admin login failed. Ensure database is initialized with an admin user, or proceed to user setup.")

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
        global async_event_loop
        if self.app_core:
            if async_event_loop and async_event_loop.is_running():
                future = asyncio.run_coroutine_threadsafe(self.shutdown_app_async(), async_event_loop)
                try:
                    future.result(timeout=5) 
                except asyncio.TimeoutError: 
                    print("Warning: Timeout during async shutdown.")
                except Exception as e:
                    print(f"Error during async shutdown: {e}")
            else:
                try:
                    asyncio.run(self.shutdown_app_async())
                except RuntimeError: 
                    pass 
        print("Application shutdown process complete.")

def run_async_loop_in_thread(): 
    global async_event_loop
    async_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_event_loop)
    try:
        print("Asyncio event loop starting in dedicated thread.")
        async_event_loop.run_forever()
    except KeyboardInterrupt:
        print("Asyncio event loop interrupted.")
    finally:
        print("Asyncio event loop stopping.")
        if async_event_loop and not async_event_loop.is_closed(): # Check if not closed
            tasks = asyncio.all_tasks(loop=async_event_loop)
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            # Wait for tasks to complete cancellation
            async_event_loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
            # Stop the loop before closing
            if async_event_loop.is_running():
                 async_event_loop.stop()
            async_event_loop.close()
        print("Asyncio event loop closed.")

def main():
    # Optional: Start asyncio event loop in a separate thread
    # global async_loop_thread
    # async_loop_thread = threading.Thread(target=run_async_loop_in_thread, daemon=True)
    # async_loop_thread.start()
    # For simple desktop app, direct asyncio.run and ensure_future might be sufficient initially.

    # Attempt to import compiled resources
    try:
        import app.resources_rc # type: ignore
        print("Successfully imported compiled Qt resources (resources_rc.py).")
    except ImportError:
        print("Warning: Compiled Qt resources (resources_rc.py) not found.")
        print("Consider running: pyside6-rcc resources/resources.qrc -o app/resources_rc.py (from project root)")

    app = Application(sys.argv)
    app.aboutToQuit.connect(app.shutdown_app) 
    
    exit_code = app.exec()
        
    sys.exit(exit_code)

if __name__ == "__main__":
    main()

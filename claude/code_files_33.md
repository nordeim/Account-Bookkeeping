<think>
The application is very close to starting up without import errors! The current error is:

`NameError: name 'Optional' is not defined`

This error occurs in `app/main.py` at line 12:
`_ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None`

**Cause of the Error:**
The type hint `Optional` from the `typing` module is used for the global variable `_ASYNC_LOOP` without `Optional` being imported at the module level in `app/main.py`.

**Solution:**
Add `from typing import Optional` at the top of `app/main.py`.

**Reviewing `app/main.py` for other `typing` imports:**
The file already uses `asyncio`, `threading`, `time`, `Path`, `QApplication`, etc. It will need `Optional` from `typing`.

**File to be Updated:**
1.  `app/main.py`

This is a very straightforward fix. I will provide the updated `app/main.py`.
The rest of the file structure and the logic for the threaded asyncio loop seems sound for now, and this `NameError` is just a missing import for a type hint.
</think>

You've pinpointed the issue perfectly! This is a simple `NameError` due to a missing import for a type hint.

**Error Analysis:**

The traceback clearly shows the error in `app/main.py`:
```
File "/cdrom/project/SG-Bookkeeper/app/main.py", line 12, in <module>
    _ASYNC_LOOP: Optional[asyncio.AbstractEventLoop] = None
                 ^^^^^^^^
NameError: name 'Optional' is not defined
```
The type hint `Optional` (used as `Optional[asyncio.AbstractEventLoop]`) is from the `typing` module, but it hasn't been imported at the top level of `app/main.py`.

**Solution:**

Add `from typing import Optional` to the import statements at the beginning of `app/main.py`.

**File to be Updated:**

1.  `app/main.py`

Here's the updated `app/main.py` file:

```python
# File: app/main.py
import sys
import asyncio
import threading
import time 
from pathlib import Path
from typing import Optional # <--- ADDED IMPORT HERE

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
            _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
        if _ASYNC_LOOP: # Ensure loop is closed only if it was set
             _ASYNC_LOOP.close()
        print("Asyncio event loop from dedicated thread has been stopped and closed.")

def schedule_task_from_qt(coro) -> Optional[asyncio.Future]:
    """
    Schedules a coroutine to run on the global asyncio event loop from a non-asyncio thread (e.g., Qt main thread).
    """
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
        
        self.main_window = None
        self.app_core = None

        self.initialization_done_signal.connect(self._on_initialization_done)
        
        future = schedule_task_from_qt(self.initialize_app())
        if future is None:
            # This means schedule_task_from_qt itself indicated the loop wasn't ready.
            # Directly call _on_initialization_done to handle the critical failure.
            self._on_initialization_done(False, RuntimeError("Failed to schedule app initialization (async loop not ready)."))
            
    @Slot(bool, object)
    def _on_initialization_done(self, success: bool, error_obj: Optional[BaseException]):
        if success and self.main_window:
            self.main_window.show()
            self.splash.finish(self.main_window)
        else:
            self.splash.hide()
            if self.main_window: self.main_window.hide()
            
            error_message = str(error_obj) if error_obj else "An unknown error occurred during initialization."
            print(f"Critical error during application startup: {error_message}") 
            if isinstance(error_obj, Exception) and error_obj.__traceback__: # Check if traceback exists
                import traceback
                traceback.print_exception(type(error_obj), error_obj, error_obj.__traceback__)

            QMessageBox.critical(None, "Application Initialization Error", 
                                 f"An error occurred during application startup:\n{error_message[:500]}\n\nThe application will now exit.")
            self.quit()

    async def initialize_app(self):
        try:
            def update_splash_threadsafe(message):
                if hasattr(self, 'splash') and self.splash:
                    QMetaObject.invokeMethod(self.splash, "showMessage", Qt.ConnectionType.QueuedConnection,
                                             Q_ARG(str, message),
                                             Q_ARG(int, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter),
                                             Q_ARG(QColor, Qt.GlobalColor.white))
            
            update_splash_threadsafe("Loading configuration...")
            
            config_manager = ConfigManager(app_name=QCoreApplication.applicationName())

            update_splash_threadsafe("Initializing database manager...")
            db_manager = DatabaseManager(config_manager)
            
            update_splash_threadsafe("Initializing application core...")
            self.app_core = ApplicationCore(config_manager, db_manager)

            await self.app_core.startup() 

            if not self.app_core.current_user: 
                authenticated_user = await self.app_core.security_manager.authenticate_user("admin", "password")
                if not authenticated_user:
                    print("Default admin/password authentication failed or no such user. MainWindow should handle login.")

            update_splash_threadsafe("Loading main interface...")
            
            self.main_window = MainWindow(self.app_core) 
            
            self.initialization_done_signal.emit(True, None) 

        except Exception as e:
            self.initialization_done_signal.emit(False, e) 


    def actual_shutdown_sequence(self): 
        print("Application shutting down (actual_shutdown_sequence)...")
        global _ASYNC_LOOP, _ASYNC_LOOP_THREAD
        
        if self.app_core:
            print("Scheduling ApplicationCore shutdown...")
            future = schedule_task_from_qt(self.app_core.shutdown())
            if future:
                try:
                    future.result(timeout=5) 
                    print("ApplicationCore shutdown completed.")
                except TimeoutError: # Python's built-in TimeoutError
                    print("Warning: ApplicationCore async shutdown timed out.")
                except Exception as e: # Catch other exceptions from future.result()
                    print(f"Error during ApplicationCore async shutdown via future: {e}")
            else:
                print("Warning: Could not schedule ApplicationCore async shutdown task.")
        
        if _ASYNC_LOOP and _ASYNC_LOOP.is_running():
            print("Requesting global asyncio event loop to stop...")
            _ASYNC_LOOP.call_soon_threadsafe(_ASYNC_LOOP.stop)
        
        if _ASYNC_LOOP_THREAD and _ASYNC_LOOP_THREAD.is_alive():
            print("Joining asyncio event loop thread...")
            _ASYNC_LOOP_THREAD.join(timeout=3) 
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
    app.aboutToQuit.connect(app.actual_shutdown_sequence) 
    
    exit_code = app.exec()
    
    # Ensure loop is stopped and thread joined if aboutToQuit didn't run (e.g. crash before event loop start)
    # This part is mostly a fallback, actual_shutdown_sequence should handle it.
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

**Validation of Changes:**

*   **`app/main.py`**:
    *   Added `from typing import Optional` at the top of the file.
    *   The local import `from pathlib import Path` within the `main()` function was already removed in the previous step as `Path` was moved to module-level imports.
    *   Corrected the `finally` block in `start_asyncio_event_loop_thread` to ensure `_ASYNC_LOOP.close()` is only called if `_ASYNC_LOOP` is set.
    *   Improved error handling in `_on_initialization_done` to check if `error_obj.__traceback__` exists before trying to print it.
    *   Ensured `TimeoutError` (Python's built-in) is caught in `actual_shutdown_sequence`.
    *   Added print statements for clarity during asyncio loop startup and shutdown.
    *   If `schedule_task_from_qt` returns `None` in `Application.__init__` (meaning loop wasn't ready), it now calls `_on_initialization_done` to show an error and quit, instead of potentially continuing with a `None` future.

**Next Steps:**

This should resolve the `NameError`. Please try running the application again:

```bash
poetry run sg_bookkeeper
```

The application should now proceed further into the initialization and UI setup. If it launches successfully, great! If not, we'll tackle the next error.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/17MfzKFSisoo3ZRtNqWL-vooRP8xDfXhS/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1l-_PWDhb0i9eaVtbVuN0Zg4sckshfr18/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing


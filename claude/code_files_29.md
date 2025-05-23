<think>
We have two errors in the traceback for `app/main.py`:

1.  `ModuleNotFoundError: No module named 'app.resources_rc'`
    *   This is expected and handled by a `try-except` block. The `except ImportError:` block then tries to load the splash image from a direct file path. This part is informational rather than a crash cause.

2.  `NameError: name 'Path' is not defined`
    *   This is the critical error causing the application to fail. It occurs within the `except ImportError:` block of the `Application.__init__` method, specifically at the line:
        `base_path = Path(__file__).resolve().parent.parent # SG-Bookkeeper project root`
    *   The `Path` object from the `pathlib` module is used without being imported.

**Cause of the `NameError`:**
The `Path` class from the `pathlib` module needs to be imported before it can be used.

**Solution:**
Add `from pathlib import Path` at the top of `app/main.py`.

**File to be Updated:**
1.  `app/main.py`

**Reviewing `app/main.py` for other `Path` usages:**
The `main()` function also used `Path` in my last generated version of `app/main.py`:
```python
def main():
    # Added Path import for splash image path resolution
    from pathlib import Path # This import is local to main()

    try:
        import app.resources_rc 
        # ...
```
This local import within `main()` wouldn't help the `__init__` method of the `Application` class. The import needs to be at the module level (top of the file) to be available for the `Application` class definition.

**Plan:**
1.  Move the `from pathlib import Path` import to the top of `app/main.py` to make it globally available within the module.
2.  Remove the redundant local import of `Path` from the `main()` function.

This will ensure `Path` is defined when the `Application.__init__` method tries to use it.
</think>

You're right, we've encountered a `NameError` now. The application successfully handled the absence of `app.resources_rc` (as designed) but then failed when trying to use `Path` because it wasn't imported.

**Error Analysis:**

1.  **`ModuleNotFoundError: No module named 'app.resources_rc'`**: This is caught by your `try-except ImportError` block and is not the cause of the crash. The application correctly prints the warning and attempts to use direct file paths.

2.  **`NameError: name 'Path' is not defined`**: This is the critical error. It occurs in `app/main.py` within the `Application.__init__` method, inside the `except ImportError:` block, at the line:
    ```python
    base_path = Path(__file__).resolve().parent.parent # SG-Bookkeeper project root
    ```
    The `Path` object from the `pathlib` module is used here, but `pathlib.Path` has not been imported at the module level, making `Path` an undefined name in this scope.

**Solution:**

To fix this, you need to import `Path` from the `pathlib` module at the top of `app/main.py`.

**File to be Updated:**

1.  `app/main.py`: Add the import statement and remove any redundant local imports of `Path`.

Here is the updated `app/main.py`:

```python
# File: app/main.py
import sys
import asyncio
from pathlib import Path # <--- ADDED IMPORT HERE
from PySide6.QtWidgets import QApplication, QSplashScreen, QLabel, QMessageBox, QCheckBox 
from PySide6.QtCore import Qt, QSettings, QTimer, QCoreApplication 
from PySide6.QtGui import QPixmap

from app.ui.main_window import MainWindow
from app.core.application_core import ApplicationCore
from app.core.config_manager import ConfigManager
from app.core.database_manager import DatabaseManager


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        
        self.setApplicationName("SGBookkeeper") 
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
            # Ensure the path is correct if running from project root
            # Assuming 'resources' is a top-level directory alongside 'app'
            base_path = Path(__file__).resolve().parent.parent # SG-Bookkeeper project root
            splash_image_path = base_path / "resources" / "images" / "splash.png"
            if splash_image_path.exists():
                splash_pixmap = QPixmap(str(splash_image_path))
            else:
                print(f"Warning: Splash image not found at {splash_image_path}. Using fallback.")


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
            self.splash.setObjectName("SplashScreen")


        self.splash.show()
        self.processEvents() 
        
        self.main_window = None
        self.app_core = None

        QTimer.singleShot(100, self.initialize_app_async_wrapper)

    def initialize_app_async_wrapper(self):
        try:
            asyncio.run(self.initialize_app())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.initialize_app()) 
                except RuntimeError: 
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
                authenticated_user = await self.app_core.security_manager.authenticate_user("admin", "password")
                if not authenticated_user:
                    print("Default admin/password authentication failed or no such user. MainWindow should handle login.")


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
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self.shutdown_app_async(), loop)
                    future.result(5) 
                else:
                    loop.run_until_complete(self.shutdown_app_async())
            except RuntimeError: 
                try:
                    asyncio.run(self.shutdown_app_async())
                except RuntimeError: 
                    print("Warning: Could not execute async shutdown cleanly due to event loop state.")
            except Exception as e:
                 print(f"Error during async shutdown: {e}")

        print("Application shutdown process complete.")

def main():
    # from pathlib import Path # Removed redundant local import

    try:
        import app.resources_rc 
        print("Successfully imported compiled Qt resources (resources_rc.py).")
    except ImportError:
        print("Warning: Compiled Qt resources (resources_rc.py) not found. Direct file paths will be used for icons/images.")
        print("Consider running from project root: pyside6-rcc resources/resources.qrc -o app/resources_rc.py")

    app = Application(sys.argv)
    app.aboutToQuit.connect(app.shutdown_app) 
    
    exit_code = app.exec()
            
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
```

**Validation of Changes:**

*   **`app/main.py`**:
    *   Added `from pathlib import Path` at the top of the file.
    *   Removed the local import `from pathlib import Path` from within the `main()` function as the module-level import now covers it.
    *   Added `QCheckBox` to the import from `PySide6.QtWidgets` as it was used in `settings_widget.py` and it's good practice to have common Qt widget imports in `main.py` or a central UI utility module if used frequently across many files. (Though `settings_widget.py` also imports it directly, this is not harmful).

**Next Steps:**

This change should resolve the `NameError: name 'Path' is not defined`. Please try running the application again:

```bash
poetry run sg_bookkeeper
```

We are getting very close to having the application launch without import or early runtime errors!

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing


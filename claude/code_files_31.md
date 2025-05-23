<think>
Excellent, the application UI is now launching! We have two main categories of issues to address:
1.  **Missing SVG Icons**: Many `qt.svg: Cannot open file ... No such file or directory` errors are appearing for icons used in `MainWindow` tabs and actions.
2.  **Asyncio `RuntimeError`**: `RuntimeError: There is no current event loop in thread 'MainThread'.` This happens when `asyncio.ensure_future()` is called from `QTimer.singleShot` in `ChartOfAccountsWidget` and `SettingsWidget` for loading data. This is a classic problem when integrating `asyncio` with Qt's event loop.

Let's tackle these.

**1. Missing SVG Icons**

**Analysis:**
The console output clearly lists all the missing SVG files. The `ls -l resources/icons/` output shows that only a few icons are present. The application attempts to load these icons in `MainWindow._add_module_tabs()` and `MainWindow._create_actions()`.

**Solution:**
Provide placeholder SVG content for all the missing icons reported and likely to be used based on `MainWindow`'s structure. The user previously requested help generating these.

**List of Missing Icons based on errors and `MainWindow` code:**
*   `accounting.svg`
*   `customers.svg`
*   `vendors.svg`
*   `banking.svg`
*   `reports.svg`
*   `settings.svg`
*   `new_company.svg`
*   `open_company.svg`
*   `backup.svg`
*   `restore.svg`
*   `exit.svg`
*   `preferences.svg`
*   `help.svg`
*   `about.svg`

I will generate simple placeholder SVGs for these.

**2. Asyncio `RuntimeError`: No current event loop**

**Analysis:**
The error `RuntimeError: There is no current event loop in thread 'MainThread'` occurs because `asyncio.ensure_future()` (and `asyncio.get_event_loop()` which it calls internally if no loop is explicitly passed) requires an asyncio event loop to be set for the current thread.
PySide6 (Qt) has its own event loop. When you run a PySide6 application with `app.exec()`, Qt's event loop is running. `asyncio`'s default event loop mechanisms don't automatically integrate with Qt's loop.
Calling `asyncio.run()` (as done in `Application.initialize_app_async_wrapper`) creates and runs an asyncio event loop until the given coroutine completes, then closes that loop. This is fine for a one-off startup task.
However, `QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))` schedules `_load_accounts` to run *after* `initialize_app` has finished and `app.exec()` has started Qt's main loop. At this point, the asyncio loop started by `asyncio.run()` is no longer running or set as the current loop for the main thread.

**Solution Options for Asyncio Integration with Qt:**

*   **A. Use a Qt-specific asyncio event loop policy/runner (e.g., `quamash` or `asyncqt`):**
    These libraries provide an asyncio event loop that integrates with Qt's event loop, allowing `asyncio` tasks and Qt events to coexist harmoniously. This is the most robust and recommended solution for complex GUI applications that heavily use `asyncio`.
    *   Pros: Proper integration, `async/await` can be used more naturally throughout the Qt application.
    *   Cons: Adds an external dependency. Requires setting up the policy early in `main()`.

*   **B. Run async tasks in a separate thread with its own asyncio loop:**
    Create a dedicated thread for running all asyncio operations. Use `asyncio.run_coroutine_threadsafe()` to schedule coroutines on this loop from the Qt main thread, and use Qt signals/slots or `QMetaObject.invokeMethod` to get results back to the UI thread.
    *   Pros: Decouples asyncio loop from Qt loop.
    *   Cons: More complex inter-thread communication for results and UI updates. `asyncio.run_coroutine_threadsafe` returns a `Future` that needs to be handled.

*   **C. Simple "Run and Block" for short async tasks (not ideal for UI responsiveness):**
    For very short, non-blocking async tasks that are fired from Qt, one *could* briefly run a new asyncio loop using `asyncio.run()`. However, if these tasks are meant to update the UI or are long-running, this will block the Qt event loop or cause issues. This is generally not suitable for tasks like `_load_accounts` which might involve network/DB I/O and should not block the UI thread.
    The `RuntimeWarning: coroutine ... was never awaited` indicates that `asyncio.ensure_future` created a task, but it was never actually run to completion because no compatible asyncio loop was effectively driving it from the Qt context.

*   **D. Use `QThread` with a worker object that runs `asyncio.run()` internally:**
    This is similar to B but uses Qt's threading primitives. Each async operation could be encapsulated. Still requires careful signal/slot communication.

**Chosen Approach (for now, to get it running without new dependencies):**
The most direct way to fix the current error without adding new dependencies like `quamash` is to ensure that an asyncio event loop is available and running when `asyncio.ensure_future` is called from a `QTimer`.

Since `Application.initialize_app_async_wrapper` already uses `asyncio.run()` which sets up a loop for the duration of `initialize_app()`, this loop is gone by the time the `QTimer`s fire.

A common pattern for integrating asyncio with a GUI framework without a full-fledged integration library is to run the asyncio event loop in a separate thread and use `asyncio.run_coroutine_threadsafe` to submit tasks from the GUI thread. The `shutdown_app` already has a similar pattern.

Let's modify `app/main.py` to manage a global asyncio event loop running in a separate thread.

**Revised Plan for Asyncio:**

1.  In `app/main.py`:
    *   Create a global asyncio event loop instance.
    *   Create and start a `threading.Thread` that runs this asyncio event loop (`loop.run_forever()`).
    *   Provide a function to safely schedule coroutines onto this loop from the Qt main thread using `asyncio.run_coroutine_threadsafe`.
    *   Modify `QTimer.singleShot` callbacks to use this scheduler.
    *   Ensure the asyncio loop is properly stopped on application shutdown.

**Implementation of Asyncio Loop in a Thread (in `app/main.py`):**

```python
# At the top of app/main.py
import threading
# ... other imports ...

# Global asyncio event loop and thread
async_event_loop = None
async_loop_thread = None

def start_async_loop():
    global async_event_loop
    async_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(async_event_loop)
    async_event_loop.run_forever()

def schedule_async_task(coro):
    global async_event_loop
    if async_event_loop and async_event_loop.is_running():
        return asyncio.run_coroutine_threadsafe(coro, async_event_loop)
    else:
        # Fallback or error if loop isn't running (should not happen if started correctly)
        print("Error: Asyncio event loop is not running. Cannot schedule task.")
        # Alternatively, could run it synchronously here for simple cases, but that defeats the purpose.
        # For critical tasks, this needs robust handling.
        # For UI loading, it might be acceptable to block briefly if loop setup failed.
        try:
            return asyncio.run(coro) # Last resort, will block
        except RuntimeError: # If asyncio.run itself fails (e.g. nested)
            return None


# In main() function, before app.exec():
    global async_loop_thread
    async_loop_thread = threading.Thread(target=start_async_loop, daemon=True)
    async_loop_thread.start()
    # Wait a brief moment for the loop to actually start
    import time
    time.sleep(0.1) # Crude way to ensure loop is up; better use an Event.

# In QTimer.singleShot callbacks, e.g., in ChartOfAccountsWidget:
# QTimer.singleShot(0, lambda: schedule_async_task(self._load_accounts()))

# In Application.shutdown_app():
    global async_event_loop, async_loop_thread
    if async_event_loop:
        async_event_loop.call_soon_threadsafe(async_event_loop.stop)
    if async_loop_thread:
        async_loop_thread.join(timeout=2) # Wait for thread to finish
    # Then proceed with app_core.shutdown()
```

This threaded approach is a common pattern. The `QTimer.singleShot` callbacks in `ChartOfAccountsWidget` and `SettingsWidget` would then use `schedule_async_task`.

```python
# Example in ChartOfAccountsWidget._init_ui
# from app.main import schedule_async_task # Need to import this helper
# QTimer.singleShot(0, lambda: schedule_async_task(self._load_accounts()))
```
However, importing from `app.main` into UI widgets creates another circular dependency potential. It's better if `Application` class itself provides a method to schedule tasks.

**Alternative for Asyncio (Simpler, but less ideal for true async in UI):**
The `initialize_app_async_wrapper` in `app/main.py` currently does:
```python
        try:
            asyncio.run(self.initialize_app())
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                loop = asyncio.get_running_loop()
                loop.create_task(self.initialize_app())
```
This `loop.create_task(self.initialize_app())` implies that if `asyncio.run()` fails because a loop is *already* running (e.g., `pytest-asyncio`), then `self.initialize_app()` (which is async) is scheduled on that *existing external* loop. This is fine for testing.
But for `QTimer` callbacks, there's no such external asyncio loop managed by default in the main Qt thread.

Let's try a slightly less intrusive change first for the `QTimer` problem.
If we simply want to run an async function from a sync context (like a QTimer callback) and there's no asyncio loop set on the current thread, `asyncio.run()` is the standard way. The `RuntimeError: There is no current event loop...` usually comes from `asyncio.get_event_loop()` when `asyncio.set_event_loop()` hasn't been called or the loop from a previous `asyncio.run()` has closed.

The `QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))` creates a *task* but doesn't *run* an event loop to drive that task.
Changing it to `QTimer.singleShot(0, lambda: asyncio.run(self._load_accounts()))` might work for these one-shot async loads, but `asyncio.run()` cannot be called when an event loop is already running in the same thread. This would conflict if, for example, `initialize_app` was already running in an asyncio loop on the main thread (which it's not after the initial `asyncio.run` in `initialize_app_async_wrapper` finishes).

The core issue is that `asyncio.ensure_future` (or `loop.create_task`) only schedules the coroutine. Something needs to *run* the event loop that these tasks are scheduled on.

Given the current `app/main.py` structure for startup:
```python
    def initialize_app_async_wrapper(self):
        try:
            asyncio.run(self.initialize_app()) # Runs 'initialize_app' in a new loop
        # ...
```
After `asyncio.run(self.initialize_app())` completes, its event loop is closed.
When `QTimer` later calls `lambda: asyncio.ensure_future(self._load_accounts())`, there's no current event loop for `ensure_future` to attach the task to.

**Minimal change to get past the `RuntimeError` for now:**
In `ChartOfAccountsWidget` and `SettingsWidget`, change:
`QTimer.singleShot(0, lambda: asyncio.ensure_future(self._load_accounts()))`
to
`QTimer.singleShot(0, lambda: self._run_async_load(self._load_accounts()))`

And add a helper in those widgets (or a base widget class):
```python
    def _run_async_load(self, coro):
        try:
            # This will block the QTimer callback until coro completes.
            # If _load_accounts is quick, it might be acceptable.
            # If it's long, UI will freeze.
            asyncio.run(coro)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e):
                # This case should ideally not happen if we are calling from QTimer in main thread
                # after the initial asyncio.run() has finished.
                # If it does, it means something else set up a persistent loop on main thread.
                QMessageBox.critical(self, "Async Error", f"Cannot run async load: {e}")
            else:
                QMessageBox.critical(self, "Async Error", f"Error in async load: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Async Error", f"Unexpected error in async load: {e}")
```
This approach will make the async loads blocking within the context of the QTimer callback, which isn't truly asynchronous from the UI's perspective but will get past the "no current event loop" error. For a proper async UI, a dedicated asyncio event loop integrated with Qt (like quamash) or a threaded asyncio loop is better.

Let's try this simpler, blocking `asyncio.run()` fix first for the QTimer-initiated calls. The `RuntimeWarning: coroutine ... was never awaited` also points to this.

**Final Plan:**
1.  **Fix `AttributeError` in `ChartOfAccountsWidget`**:
    *   Modify `app/ui/accounting/chart_of_accounts_widget.py` `_init_ui` method to define `self.account_tree` before `self._create_toolbar()`.
2.  **Address SVG Icon Issues:**
    *   Inform the user about `dashboard.svg`.
    *   Provide placeholders for *all* missing icons identified from the console log.
3.  **Fix Asyncio `RuntimeError` in `ChartOfAccountsWidget` and `SettingsWidget`**:
    *   Modify `app/ui/accounting/chart_of_accounts_widget.py` and `app/ui/settings/settings_widget.py`.
    *   Change `QTimer.singleShot(0, lambda: asyncio.ensure_future(coro()))`
      to `QTimer.singleShot(0, lambda: self._execute_async_task(coro()))`.
    *   Add a helper method `_execute_async_task(self, coro)` to these widgets (or a common base class they might inherit from eventually) that calls `asyncio.run(coro)`. This will make the load operations effectively synchronous within the timer's slot, but will allow the async methods themselves to be written with `async/await`.

The `QCheckBox` import was already fixed in `settings_widget.py` in the previous response.
</think>

Okay, the application UI is launching, which is fantastic progress! We have two distinct issues now:
1.  An `AttributeError` in `ChartOfAccountsWidget` due to the order of UI element initialization.
2.  Several `qt.svg: Cannot open file...` errors for missing icons, and one `Start tag expected` for `dashboard.svg`.
3.  A `RuntimeError: There is no current event loop in thread 'MainThread'` when `asyncio.ensure_future` is used with `QTimer.singleShot` for loading data in widgets.

Let's address these:

**1. AttributeError in `ChartOfAccountsWidget`**

This was diagnosed correctly in the previous step. The fix involves reordering calls in `ChartOfAccountsWidget._init_ui`. I'll provide the corrected file again with this specific fix applied.

**2. Missing/Invalid SVG Icons**

*   **Invalid `dashboard.svg`**: The error `qt.svg: Cannot read file '/cdrom/project/SG-Bookkeeper/resources/icons/dashboard.svg', because: Start tag expected.` means your `dashboard.svg` file is present but its content is not valid SVG XML. You'll need to ensure this file has correct SVG code. I cannot generate or fix complex graphical assets, but a very basic placeholder would look like this (which you can replace):
    **`resources/icons/dashboard.svg` (basic placeholder):**
    ```xml
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
      <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/>
    </svg>
    ```
    Please replace the content of your existing `resources/icons/dashboard.svg` with this or a valid SVG of your choice.

*   **Other Missing SVGs**: The console log lists several missing icons. I will provide placeholders for all of them. You should create these files in your `resources/icons/` directory.

**3. Asyncio `RuntimeError`: No current event loop**

This error occurs because `asyncio.ensure_future(self._load_accounts())` (and similar in `SettingsWidget`) is called from a `QTimer.singleShot`. The `asyncio.run()` in `main.py` completes, and its event loop closes *before* these timers fire. Thus, when `ensure_future` is called, there's no asyncio event loop running on the main thread.

**Solution for Asyncio Error:**
For now, to get the methods to execute without introducing a full asyncio/Qt integration library (like `quamash` or `asyncqt`) or a background asyncio thread, we can change the `QTimer` callbacks to call `asyncio.run(self.coro_to_run())` directly. This will make the async methods block the Qt event loop briefly while they execute (which is not ideal for long-running async tasks but will work for initial data loading if it's quick). This also resolves the `RuntimeWarning: coroutine ... was never awaited`.

**Files to be Updated:**
1.  `app/ui/accounting/chart_of_accounts_widget.py` (for `AttributeError` and `asyncio` call)
2.  `app/ui/settings/settings_widget.py` (for `asyncio` call)

**New SVG Files to Create (Placeholders):**
(Save these into `resources/icons/` directory with the specified names)

**`resources/icons/accounting.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h16v2H4v-2zm0 4h16v2H4v-2zm0-8h16v2H4V6zm0 12h10v2H4v-2zM16 18h4v2h-4v-2z"/></svg>
```
**`resources/icons/customers.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
```
**`resources/icons/vendors.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M16.5 12c1.38 0 2.5-1.12 2.5-2.5S17.88 7 16.5 7C15.12 7 14 8.12 14 9.5s1.12 2.5 2.5 2.5zM9 11c1.66 0 2.99-1.34 2.99-3S10.66 5 9 5C7.34 5 6 6.34 6 8s1.34 3 3 3zm7.5 3c-1.83 0-5.5.92-5.5 2.75V19h11v-2.25c0-1.83-3.67-2.75-5.5-2.75zM9 13c-2.33 0-7 1.17-7 3.5V19h7v-2.5c0-.85.33-2.34 2.37-3.47C10.5 13.1 9.66 13 9 13z"/></svg>
```
**`resources/icons/banking.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h3v7H4v-7zm6.5 0h3v7h-3v-7zM2 19h20v3H2v-3zm15-9h3v7h-3v-7zm-5-9L2 6v2h20V6L12 1z"/></svg>
```
**`resources/icons/reports.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
```
**`resources/icons/settings.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
```
**`resources/icons/new_company.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
```
**`resources/icons/open_company.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/></svg>
```
**`resources/icons/backup.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
```
**`resources/icons/restore.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8H12z"/></svg>
```
**`resources/icons/exit.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
```
**`resources/icons/preferences.svg`**: (Similar to settings)
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
```
**`resources/icons/help.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
```
**`resources/icons/about.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v-2h-2v2zm0-4h2V7h-2v4z"/></svg>
```

---
**Updated Files:**

```python
# File: app/ui/accounting/chart_of_accounts_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeView, QHeaderView,
    QPushButton, QToolBar, QMenu, QDialog, QMessageBox, QLabel, QSpacerItem, QSizePolicy 
)
from PySide6.QtCore import Qt, QModelIndex, Signal, Slot, QPoint, QSortFilterProxyModel, QTimer 
from PySide6.QtGui import QIcon, QStandardItemModel, QStandardItem, QAction 
from decimal import Decimal 
from datetime import date 
import asyncio 
from typing import Optional, Dict, Any, List 

from app.ui.accounting.account_dialog import AccountDialog
from app.core.application_core import ApplicationCore
from app.utils.result import Result 


class ChartOfAccountsWidget(QWidget):
    account_selected = Signal(int)
    
    def __init__(self, app_core: ApplicationCore, parent=None):
        super().__init__(parent)
        self.app_core = app_core
        self._init_ui()

    def _init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Define main UI elements like account_tree first
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
        
        # Now create toolbar as it might reference account_tree
        self._create_toolbar()
        self.main_layout.addWidget(self.toolbar) 

        self.main_layout.addWidget(self.account_tree) 
        
        self.button_layout = QHBoxLayout()
        self.button_layout.setContentsMargins(0, 10, 0, 0)
        
        icon_path_prefix = "" 
        try:
            import app.resources_rc # type: ignore
            icon_path_prefix = ":/icons/"
        except ImportError:
            icon_path_prefix = "resources/icons/"

        self.add_button = QPushButton(QIcon(icon_path_prefix + "edit.svg"), "Add Account") 
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

        QTimer.singleShot(0, lambda: self._execute_async_task(self._load_accounts()))

    def _create_toolbar(self):
        from PySide6.QtCore import QSize 
        self.toolbar = QToolBar("COA Toolbar") 
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
        self.refresh_action.triggered.connect(lambda: self._execute_async_task(self._load_accounts()))
        self.toolbar.addAction(self.refresh_action)
        
    def _execute_async_task(self, coro):
        """Helper to run an async task from a synchronous Qt slot."""
        try:
            # This creates a new event loop for each call, runs the coroutine, and closes the loop.
            # It will block the Qt slot until the coroutine completes.
            asyncio.run(coro)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e) or \
               "Event loop is closed" in str(e): # Handle if loop from main.py still lingers or closed early
                # This scenario indicates a more complex asyncio setup might be needed,
                # or the main asyncio loop management needs adjustment.
                # For now, try to create a new loop explicitly for this task if current_thread has no loop
                # or if the existing one is closed.
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(coro)
                    loop.close()
                except Exception as e_inner:
                     QMessageBox.critical(self, "Async Execution Error", f"Failed to run async task on new loop: {e_inner}")
            else:
                 QMessageBox.critical(self, "Async Execution Error", f"Failed to run async task: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Async Execution Error", f"Unexpected error during async task: {e}")


    async def _load_accounts(self):
        try:
            self.account_model.clear() 
            self.account_model.setHorizontalHeaderLabels(["Code", "Name", "Type", "Opening Balance", "Is Active"])
            
            manager = self.app_core.accounting_service 
            if not (manager and hasattr(manager, 'get_account_tree')):
                QMessageBox.critical(self, "Error", "Accounting service (ChartOfAccountsManager) or get_account_tree method not available.")
                return

            account_tree_data: List[Dict[str, Any]] = await manager.get_account_tree(active_only=False) 
            
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
        if not isinstance(ob_val, Decimal):
            try:
                ob_val = Decimal(str(ob_val))
            except:
                ob_val = Decimal(0) 
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
        
        dialog = AccountDialog(self.app_core, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted: 
            self._execute_async_task(self._load_accounts())
    
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

        dialog = AccountDialog(self.app_core, account_id=account_id, current_user_id=self.app_core.current_user.id, parent=self) 
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._execute_async_task(self._load_accounts())
            
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
            
        self._execute_async_task(self._perform_toggle_active_status_logic(account_id, self.app_core.current_user.id))

    async def _perform_toggle_active_status_logic(self, account_id: int, user_id: int):
        try:
            manager = self.app_core.accounting_service 
            if not manager: raise RuntimeError("Accounting service not available.")

            account = await manager.account_service.get_by_id(account_id) 
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
                    result = await manager.deactivate_account(account_id, user_id) 
            else: 
                confirm_msg = f"Are you sure you want to activate account '{account.code} - {account.name}'?"
                action_verb = "activated"
                reply = QMessageBox.question(self, "Confirm Activation", confirm_msg,
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.Yes:
                    account.is_active = True
                    account.updated_by_user_id = user_id 
                    saved_acc = await manager.account_service.save(account) 
                    result = Result.success(saved_acc)
            
            if result is None: 
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
# File: app/ui/settings/settings_widget.py
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QFormLayout, QLineEdit, QMessageBox, QComboBox, 
                               QSpinBox, QDateEdit, QCheckBox) 
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
        self.base_currency_combo = QComboBox() 

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
        QTimer.singleShot(0, lambda: self._execute_async_task(self.load_settings()))

    def _execute_async_task(self, coro):
        """Helper to run an async task from a synchronous Qt slot."""
        try:
            asyncio.run(coro)
        except RuntimeError as e:
            if "cannot be called from a running event loop" in str(e) or \
               "Event loop is closed" in str(e):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(coro)
                    loop.close()
                except Exception as e_inner:
                     QMessageBox.critical(self, "Async Execution Error", f"Failed to run async task on new loop: {e_inner}")
            else:
                 QMessageBox.critical(self, "Async Execution Error", f"Failed to run async task: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Async Execution Error", f"Unexpected error during async task: {e}")

    async def load_settings(self):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return
        
        # Populate currencies - this should ideally be done once or if currencies change
        if self.base_currency_combo.count() == 0 and self.app_core.currency_manager:
            try:
                currencies = await self.app_core.currency_manager.get_active_currencies()
                for curr in currencies:
                    self.base_currency_combo.addItem(curr.code, curr.code)
            except Exception as e:
                print(f"Error loading currencies for settings: {e}")

        settings_obj: Optional[CompanySetting] = await self.app_core.company_settings_service.get_company_settings()
        if settings_obj:
            self.company_name_edit.setText(settings_obj.company_name)
            self.legal_name_edit.setText(settings_obj.legal_name or "")
            self.uen_edit.setText(settings_obj.uen_no or "")
            self.gst_reg_edit.setText(settings_obj.gst_registration_no or "")
            self.gst_registered_check.setChecked(settings_obj.gst_registered)
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
            id=1, # Assuming ID 1 for the single company setting
            company_name=self.company_name_edit.text(),
            legal_name=self.legal_name_edit.text() or None,
            uen_no=self.uen_edit.text() or None,
            gst_registration_no=self.gst_reg_edit.text() or None,
            gst_registered=self.gst_registered_check.isChecked(),
            user_id=self.app_core.current_user.id,
            fiscal_year_start_month=1, # Placeholder - add UI elements for these
            fiscal_year_start_day=1,   # Placeholder
            base_currency=self.base_currency_combo.currentText() or "SGD", 
            tax_id_label="UEN",       # Placeholder
            date_format="yyyy-MM-dd", # Placeholder
            address_line1=None, 
            address_line2=None,
            postal_code=None,
            city="Singapore",
            country="Singapore",
            contact_person=None,
            phone=None,
            email=None,
            website=None,
            logo=None
        )
        self._execute_async_task(self.perform_save(dto))

    async def perform_save(self, settings_data: CompanySettingData):
        if not self.app_core.company_settings_service:
            QMessageBox.critical(self, "Error", "Company Settings Service not available.")
            return

        existing_settings = await self.app_core.company_settings_service.get_company_settings() 
        
        orm_obj_to_save: CompanySetting
        if existing_settings:
            orm_obj_to_save = existing_settings
            # Populate all fields from DTO
            for field_name, field_value in settings_data.model_dump(exclude={'user_id', 'id'}).items():
                if hasattr(orm_obj_to_save, field_name):
                    setattr(orm_obj_to_save, field_name, field_value)
        else: 
            dict_data = settings_data.model_dump(exclude={'user_id', 'id'}, by_alias=False)
            orm_obj_to_save = CompanySetting(**dict_data) # type: ignore
            if settings_data.id:
                 orm_obj_to_save.id = settings_data.id

        if self.app_core.current_user:
             orm_obj_to_save.updated_by_user_id = self.app_core.current_user.id 

        result = await self.app_core.company_settings_service.save_company_settings(orm_obj_to_save)
        if result:
            QMessageBox.information(self, "Success", "Settings saved successfully.")
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")
```

**SVG Files:**

Please create the following files in your `resources/icons/` directory with the SVG content provided below.

**`resources/icons/accounting.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h16v2H4v-2zm0 4h16v2H4v-2zm0-8h16v2H4V6zm0 12h10v2H4v-2zM16 18h4v2h-4v-2z"/></svg>
```
**`resources/icons/customers.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>
```
**`resources/icons/vendors.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M16.5 12c1.38 0 2.5-1.12 2.5-2.5S17.88 7 16.5 7C15.12 7 14 8.12 14 9.5s1.12 2.5 2.5 2.5zM9 11c1.66 0 2.99-1.34 2.99-3S10.66 5 9 5C7.34 5 6 6.34 6 8s1.34 3 3 3zm7.5 3c-1.83 0-5.5.92-5.5 2.75V19h11v-2.25c0-1.83-3.67-2.75-5.5-2.75zM9 13c-2.33 0-7 1.17-7 3.5V19h7v-2.5c0-.85.33-2.34 2.37-3.47C10.5 13.1 9.66 13 9 13z"/></svg>
```
**`resources/icons/banking.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M4 10h3v7H4v-7zm6.5 0h3v7h-3v-7zM2 19h20v3H2v-3zm15-9h3v7h-3v-7zm-5-9L2 6v2h20V6L12 1z"/></svg>
```
**`resources/icons/reports.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
```
**`resources/icons/settings.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
```
**`resources/icons/new_company.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 11h-4v4h-2v-4H7v-2h4V7h2v4h4v2z"/></svg>
```
**`resources/icons/open_company.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V6h5.17l2 2H20v10z"/></svg>
```
**`resources/icons/backup.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
```
**`resources/icons/restore.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M13 3a9 9 0 0 0-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42A8.954 8.954 0 0 0 13 21a9 9 0 0 0 0-18zm-1 5v5l4.25 2.52.77-1.28-3.52-2.09V8H12z"/></svg>
```
**`resources/icons/exit.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M10.09 15.59L11.5 17l5-5-5-5-1.41 1.41L12.67 11H3v2h9.67l-2.58 2.59zM19 3H5c-1.11 0-2 .9-2 2v4h2V5h14v14H5v-4H3v4c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z"/></svg>
```
**`resources/icons/preferences.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M19.43 12.98c.04-.32.07-.64.07-.98s-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.39-.3-.61-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.38-2.65C14.46 2.18 14.25 2 14 2h-4c-.25 0-.46.18-.49.42l-.38 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.23-.08-.49 0-.61.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.39.3.61.22l2.49-1c.52.4 1.08.73 1.69.98l.38 2.65c.03.24.24.42.49.42h4c.25 0 .46-.18.49-.42l.38-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.08.49 0 .61-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z"/></svg>
```
**`resources/icons/help.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17h-2v-2h2v2zm2.07-7.75l-.9.92C13.45 12.9 13 13.5 13 15h-2v-.5c0-1.1.45-2.1 1.17-2.83l1.24-1.26c.37-.36.59-.86.59-1.41 0-1.1-.9-2-2-2s-2 .9-2 2H8c0-2.21 1.79-4 4-4s4 1.79 4 4c0 .88-.36 1.68-.93 2.25z"/></svg>
```
**`resources/icons/about.svg`**:
```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-5h2v-2h-2v2zm0-4h2V7h-2v4z"/></svg>
```

**Validation of Changes:**
*   **`app/ui/accounting/chart_of_accounts_widget.py`**:
    *   Corrected the initialization order in `_init_ui()`: `self.account_tree` is now defined before `self._create_toolbar()` is called.
    *   The toolbar is now added to `self.main_layout` after `_create_toolbar()` returns.
    *   The `QTimer.singleShot` for `_load_accounts` is now called at the end of `_init_ui`.
    *   The `asyncio.ensure_future` calls are replaced with `self._execute_async_task(coro())`.
    *   Added `_execute_async_task` helper method to run asyncio coroutines using `asyncio.run()` with basic error handling for nested/closed loops. This will make the async operations block the QTimer slot but resolve the "no current event loop" error.
    *   Added missing imports for `date` and `List`.
*   **`app/ui/settings/settings_widget.py`**:
    *   The `QTimer.singleShot` for `load_settings` is changed to use `self._execute_async_task(self.load_settings())`.
    *   Added the same `_execute_async_task` helper method.
    *   Improved `load_settings` to populate `base_currency_combo` if it's empty.
    *   Improved `on_save_settings` and `perform_save` to better handle DTO-to-ORM mapping for `CompanySettingData` and `CompanySetting`.

**Next Steps:**

1.  Replace your `app/ui/accounting/chart_of_accounts_widget.py` and `app/ui/settings/settings_widget.py` with the updated content.
2.  Create all the missing SVG files listed above in your `resources/icons/` directory using the provided placeholder content.
3.  **Crucially, ensure your `resources/icons/dashboard.svg` contains valid SVG XML.** If it's empty or malformed, Qt will not be able to load it.
4.  Run the application again:
    ```bash
    poetry run sg_bookkeeper
    ```

The application should now launch the main window without the `AttributeError` and with fewer (or no) "Cannot open file" errors for icons. The async data loading in the widgets should also proceed, though it will be effectively synchronous within the timer slots.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/11KndoHQCP9vTKPlRbWLtqy6gHfC8w4Dk/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1R8FgPOnpgTglA_cwhgFBLyk0dxvW48GY/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing


<think>
The application now launches without `ImportError`s, which is great progress!
The user is reporting an issue where the Dashboard KPIs are stuck showing "Loading..." and has provided a screenshot and application logs.

**1. Deeply Understand Requirements:**
Identify and fix the cause of the Dashboard KPIs continuously showing "Loading..." instead of actual data or "N/A".

**2. Systematic Diagnosis:**

*   **Observation from Screenshot**:
    *   The "Period: Loading..." and "Currency: Loading..." labels are visible.
    *   All KPI value labels show "Loading...".
    *   The "Refresh KPIs" button is visible.
*   **Observation from Logs**:
    *   `ApplicationCore startup complete.` - Good.
    *   `Fetching dashboard KPIs...` - This log message comes from `DashboardManager.get_dashboard_kpis()`.
    *   `WARNING - No fiscal year found. Cannot calculate YTD KPIs.` - This log message also comes from `DashboardManager.get_dashboard_kpis()`.
    *   The `DashboardManager` then proceeds to calculate non-YTD KPIs (Cash, AR, AP) and returns a `DashboardKPIData` object with YTD values as 0 and a relevant `kpi_period_description`.
    *   There is **no explicit error** (exception) shown in the logs after the "Fetching dashboard KPIs..." message related to the KPI fetching itself. The next set of logs is about application shutdown.
    *   The `_update_kpi_display_slot` in `DashboardWidget` should be called with the `DashboardKPIData` object (even if YTD values are 0).
    *   If `_update_kpi_display_slot` was called, it should have updated the labels from "Loading..." to either actual values (or "0.00" for YTD if no FY) or "N/A - Error fetching data" if `kpi_data_dto` was `None`.

**Hypotheses for the "Loading..." issue:**

*   **H1: `_update_kpi_display_slot` is never called.**
    *   This could happen if `schedule_task_from_qt(self._fetch_kpis_data())` fails to schedule or if the future object's callback `lambda res: QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data))` is not correctly set up or triggered. The `kpi_data` in the lambda should be `res.result()`.
    *   Let's review `DashboardWidget._request_kpi_load` and `_fetch_kpis_data`.
    ```python
    # app/ui/dashboard/dashboard_widget.py
    @Slot()
    def _request_kpi_load(self):
        # ... sets labels to "Loading..." ...
        future = schedule_task_from_qt(self._fetch_kpis_data()) # This schedules _fetch_kpis_data
        if future:
            # This callback below will re-enable the refresh button.
            # It does NOT call _update_kpi_display_slot.
            future.add_done_callback( 
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
        # ...

    async def _fetch_kpis_data(self):
        # ...
        kpi_data = await self.app_core.dashboard_manager.get_dashboard_kpis()
        # This line correctly invokes _update_kpi_display_slot with the result from get_dashboard_kpis
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data))
    ```
    The logic in `_fetch_kpis_data` correctly calls `QMetaObject.invokeMethod` to trigger `_update_kpi_display_slot`. The `future.add_done_callback` in `_request_kpi_load` is only for re-enabling the refresh button. This seems okay.

*   **H2: `kpi_data_dto` in `_update_kpi_display_slot` is always `None`, and the "else" branch (displaying "N/A - Error fetching data") is hit, but somehow the "Loading..." text persists or the "N/A" message isn't visually distinct enough from "Loading...".**
    *   The logs show `WARNING - No fiscal year found. Cannot calculate YTD KPIs.` from `DashboardManager`.
    *   In this specific warning scenario, `DashboardManager.get_dashboard_kpis()` *still returns a `DashboardKPIData` object*, but with YTD values as `Decimal(0)` and a specific `kpi_period_description`. It does not return `None` solely because no fiscal year is found.
    *   It would return `None` only if a more severe exception occurred within `get_dashboard_kpis` that wasn't caught and re-packaged, or if `company_settings` were `None`.
    *   The log `ERROR - Error fetching dashboard KPIs: ... UndefinedFunctionError ...` from the *previous* error (which is now fixed) would have caused `kpi_data` to be `None` if that exception wasn't handled gracefully by the caller of `get_dashboard_kpis()` within `_fetch_kpis_data`. However, `get_dashboard_kpis` has a `try-except Exception` that returns `None`.
    *   Given the current logs, `DashboardManager` should return a valid `DashboardKPIData` object.

*   **H3: The `QMetaObject.invokeMethod` for `_update_kpi_display_slot` is not working as expected, or the `kpi_data_dto` argument gets corrupted.**
    *   This is less likely if other similar patterns in the app work. The `Q_ARG(object, kpi_data)` passes the Python object.

*   **H4: An issue within `_update_kpi_display_slot` prevents labels from being updated correctly even when `kpi_data_dto` is valid.**
    Let's review `_update_kpi_display_slot`:
    ```python
    # app/ui/dashboard/dashboard_widget.py
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        self.refresh_button.setEnabled(True) # This is good
        if kpi_data_dto: # This condition should be met based on current logs
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
        else: # This branch handles if kpi_data_dto is None
            error_text = "N/A - Error fetching data"
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            # ... sets all value labels to error_text ...
            QMessageBox.warning(self, "Dashboard Error", "Could not load Key Performance Indicators.")
    ```
    The logic here seems sound. If `kpi_data_dto` is a valid object, labels *should* be updated. If it's `None`, the `QMessageBox.warning` should appear, and labels should show "N/A - Error fetching data". The screenshot shows "Loading...", which means either:
    a.  `_update_kpi_display_slot` is not called.
    b.  `_update_kpi_display_slot` is called, but `kpi_data_dto` is somehow not a `DashboardKPIData` instance, and not `None` either, so it falls through without updating. This is highly unlikely for Python.
    c.  The `_request_kpi_load` function which sets "Loading..." is being called repeatedly in a loop.

**Revisiting H1 and the "looping messages" hint from the user:**
The user mentioned "looping messages on the dashboard". This strongly suggests that `_request_kpi_load()` might be getting called repeatedly.
What could cause `_request_kpi_load()` to be called in a loop?
It's called by:
1.  `QTimer.singleShot(0, self._request_kpi_load)` in `__init__`. This runs once.
2.  `self.refresh_button.clicked.connect(self._request_kpi_load)`. This is user-driven.

Is there anything in `_update_kpi_display_slot` or `_fetch_kpis_data` that might re-trigger `_request_kpi_load`? No, doesn't seem so.

Could it be that the event loop thread starting message `Global asyncio event loop <_UnixSelectorEventLoop running=True closed=False debug=False> confirmed running in dedicated thread.` is being printed repeatedly? The log only shows it once.

The "looping messages" might refer to the "Loading..." text flickering if `_request_kpi_load` was somehow called repeatedly.

**Let's reconsider the `asyncio` interaction.**
`_fetch_kpis_data` is an `async` function.
`schedule_task_from_qt(self._fetch_kpis_data())` submits this coroutine to the asyncio event loop.
`QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data))` is how the result from the asyncio thread is passed back to the Qt main thread to update the UI.

If `_fetch_kpis_data` encounters an unhandled exception *within the asyncio task itself* before it gets to `QMetaObject.invokeMethod`, the `future.add_done_callback` in `_request_kpi_load` (which re-enables the button) would still run. However, `_update_kpi_display_slot` might not be called with valid data.

The log shows `2025-06-03 19:12:19,115 - SGBookkeeperAppCore - INFO - Fetching dashboard KPIs...`
followed by `2025-06-03 19:12:19,544 - SGBookkeeperAppCore - WARNING - No fiscal year found. Cannot calculate YTD KPIs.`
This implies `DashboardManager.get_dashboard_kpis()` ran and returned.
The *next* log is `Application shutting down...` which is much later.

If `kpi_data` was `None` in `_fetch_kpis_data`, then `_update_kpi_display_slot` would be called with `None`. In this case, the `else` block in `_update_kpi_display_slot` should execute:
```python
        else: # This branch handles if kpi_data_dto is None
            error_text = "N/A - Error fetching data"
            self.period_label.setText("Period: N/A")
            # ... sets all value labels to error_text ...
            QMessageBox.warning(self, "Dashboard Error", "Could not load Key Performance Indicators.")
```
If this `QMessageBox.warning` was shown, the user would likely have mentioned it. The screenshot does not show this warning.
This suggests `kpi_data_dto` is *not* `None` when `_update_kpi_display_slot` is called.
Therefore, the `if kpi_data_dto:` block *should* be executing.

Could there be an issue with the `QGridLayout` and how labels are updated?
The `add_kpi_row` helper returns the `value_label`. These are stored as instance attributes:
`self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):")`
And then updated:
`self.revenue_value_label.setText(...)`
This looks standard and correct.

What if the `DashboardManager.get_dashboard_kpis()` method, despite the "No fiscal year found" warning, is still constructing and returning a `DashboardKPIData` object where all monetary values are `Decimal(0)` and the descriptions are set appropriately?
Yes, looking at `DashboardManager.get_dashboard_kpis()` from my previous response (response_39):
```python
            if not current_fy:
                # ...
                return DashboardKPIData(
                    kpi_period_description=kpi_period_description,
                    base_currency=base_currency,
                    total_revenue_ytd=Decimal(0), 
                    total_expenses_ytd=Decimal(0), 
                    net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance, # These could be non-zero
                    total_outstanding_ar=total_outstanding_ar, # These could be non-zero
                    total_outstanding_ap=total_outstanding_ap  # These could be non-zero
                )
            # ...
            # Normal path also returns DashboardKPIData
            return DashboardKPIData(...)
```
So, `kpi_data_dto` in `_update_kpi_display_slot` should always be a `DashboardKPIData` instance if `DashboardManager.get_dashboard_kpis()` completes without raising an unhandled exception (its own `try-except` returns `None` on internal error, which would trigger the `else` block in the slot).

The log `ERROR - Error fetching dashboard KPIs: ... UndefinedFunctionError ...` was from the *previous* run (response_42) where `get_total_outstanding_balance` had a SQL error. That error has been fixed.
The current logs (from response_43, the problem description) **do not show this SQL error anymore.** They only show the `WARNING - No fiscal year found.`

This means `get_dashboard_kpis()` should be returning a `DashboardKPIData` object successfully, even if some YTD values are zero.
So, the `if kpi_data_dto:` block in `_update_kpi_display_slot` *must* be executing.

Why would the labels remain "Loading..."?
The labels are set to "Loading..." in `_request_kpi_load`.
```python
    @Slot()
    def _request_kpi_load(self):
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label
        ]
        for label in labels_to_reset:
            label.setText("Loading...") # <--- SET HERE
        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...")

        future = schedule_task_from_qt(self._fetch_kpis_data())
        # ... future callback re-enables button ...
```
And then updated in `_update_kpi_display_slot`:
```python
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        self.refresh_button.setEnabled(True)
        if kpi_data_dto:
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}") # <--- UPDATED HERE
            # ... other labels updated ...
        else:
            # ... error handling, sets labels to "N/A - Error fetching data" ...
```

If the `asyncio` event loop (`_ASYNC_LOOP`) itself were not running correctly, `schedule_task_from_qt` might not work, or `QMetaObject.invokeMethod` might fail.
However, the logs show:
`Global asyncio event loop <_UnixSelectorEventLoop running=True closed=False debug=False> confirmed running in dedicated thread.`
This suggests the loop *is* running.

The user mentioned "looping messages". If `_request_kpi_load` is called repeatedly and `_update_kpi_display_slot` is slightly delayed or fails to update quickly enough, it might *appear* stuck on "Loading...".
What if the `QTimer.singleShot(0, self._request_kpi_load)` in `DashboardWidget.__init__` is somehow problematic or re-triggering? Unlikely for `singleShot`.

Could the problem be the main Qt event loop not processing the queued call to `_update_kpi_display_slot` effectively? If the `asyncio` task in `_fetch_kpis_data` is very fast, and the `QMetaObject.invokeMethod` call is also fast, the UI *should* update.

Let's consider the case where "No fiscal year found." This is logged.
`DashboardManager.get_dashboard_kpis()` then proceeds:
```python
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"
                current_cash_balance = await self._get_total_cash_balance(base_currency) # Runs
                total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance() # Runs
                total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance() # Runs
                return DashboardKPIData(
                    kpi_period_description=kpi_period_description,
                    base_currency=base_currency,
                    total_revenue_ytd=Decimal(0), total_expenses_ytd=Decimal(0), net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance,
                    total_outstanding_ar=total_outstanding_ar,
                    total_outstanding_ap=total_outstanding_ap
                )
```
This path returns a valid `DashboardKPIData` object. So the `if kpi_data_dto:` block in `_update_kpi_display_slot` should execute.

Is there any chance the labels being updated are not the same instances as the ones created?
No, they are instance attributes: `self.revenue_value_label`, etc.

The only way the labels would remain "Loading..." given the current logic is if:
1.  `_update_kpi_display_slot` is never called after `_fetch_kpis_data` completes its async work.
2.  `_request_kpi_load` is being called again *before* `_update_kpi_display_slot` gets a chance to run or complete, effectively resetting the labels to "Loading...".

The logs do not show repeated "Fetching dashboard KPIs..." messages, which would indicate `_request_kpi_load` (or `_fetch_kpis_data` directly) is looping. So hypothesis 2 is less likely.

This points back to an issue with the `QMetaObject.invokeMethod` or the event processing that should lead to `_update_kpi_display_slot` execution.

Is `_fetch_kpis_data` actually completing and `QMetaObject.invokeMethod` being called?
We have a log *before* `get_dashboard_kpis` and one *inside* it. We don't have one *after* it returns and just before `QMetaObject.invokeMethod`.
If `get_dashboard_kpis` itself raised an unhandled exception within the `async` task run by `schedule_task_from_qt`, that exception would be caught by the `future.add_done_callback` mechanism if one was set up to inspect `future.exception()`.
The `future.add_done_callback` in `_request_kpi_load` is only for re-enabling the button:
```python
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
```
This lambda doesn't check `res.exception()`. If `_fetch_kpis_data` (and thus `get_dashboard_kpis`) raised an exception, `kpi_data` would not be passed, and `_update_kpi_display_slot` would not be called with data.

Let's refine `_fetch_kpis_data` to be more robust and explicitly handle `None` from the manager.
```python
    async def _fetch_kpis_data(self):
        kpi_data_result: Optional[DashboardKPIData] = None # Initialize to None
        error_occurred = False
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("Dashboard Manager not available in _fetch_kpis_data.")
                error_occurred = True
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis()
                # If get_dashboard_kpis itself returns None due to an internal handled error
                if kpi_data_result is None:
                    self.app_core.logger.warning("DashboardManager.get_dashboard_kpis returned None.")
                    # error_occurred is implicitly true as kpi_data_result is None
        except Exception as e:
            self.app_core.logger.error(f"Exception in _fetch_kpis_data: {e}", exc_info=True)
            error_occurred = True
        
        # Pass the result (which could be None) to the slot
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data_result))
```
This improved `_fetch_kpis_data` will ensure `_update_kpi_display_slot` is always called, either with data or with `None`.
The `_update_kpi_display_slot` already has logic to handle `kpi_data_dto` being `None`:
```python
        else: # This branch handles if kpi_data_dto is None
            error_text = "N/A - Error fetching data"
            # ... sets labels to error_text ...
            QMessageBox.warning(self, "Dashboard Error", "Could not load Key Performance Indicators.")
```
If this `QMessageBox` is not appearing, it means `kpi_data_dto` is *not* `None` when the slot is called.
And the logs confirm `DashboardManager` *does* return a `DashboardKPIData` object even if no fiscal year is found.

This is puzzling. The "Loading..." state is set in `_request_kpi_load`.
The update to actual values or "N/A" happens in `_update_kpi_display_slot`.
If the logs show `DashboardManager` is doing its job and returning data (even if partial), then `_update_kpi_display_slot` *should* be called with that data.

Could there be an issue with `QGridLayout` and `QLabel` updates not refreshing visually? Highly unlikely with Qt.
Perhaps a subtle timing issue or event loop contention?

Let's focus on the "No fiscal year found" warning.
When this happens, `DashboardManager.get_dashboard_kpis()` returns:
```python
                return DashboardKPIData(
                    kpi_period_description=f"As of {today.strftime('%d %b %Y')} (No active FY)",
                    base_currency=base_currency, # This is fetched
                    total_revenue_ytd=Decimal(0), 
                    total_expenses_ytd=Decimal(0), 
                    net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance, # Fetched
                    total_outstanding_ar=total_outstanding_ar, # Fetched
                    total_outstanding_ap=total_outstanding_ap  # Fetched
                )
```
All these values (0 or fetched values for cash/AR/AP) should correctly update the labels from "Loading...".
The `kpi_period_description` should update.
The `base_currency` should update.

What if the `_update_kpi_display_slot` itself has an error *after* `self.refresh_button.setEnabled(True)` but *before* or *during* `setText` on the labels? That error wouldn't be caught by `_fetch_kpis_data`'s try-except.
However, if there was an error in `_update_kpi_display_slot`, the Qt runtime would typically print it to the console. No such error is visible in the logs.

Is it possible that `_request_kpi_load` is getting called, it sets labels to "Loading...", schedules `_fetch_kpis_data`, but then `_request_kpi_load` is called *again* (resetting labels to "Loading...") before the first `_fetch_kpis_data` completes and calls `_update_kpi_display_slot`?
What could trigger `_request_kpi_load` apart from the initial `QTimer.singleShot` and the refresh button?
    - `showEvent`? No, it's not overridden in the current code.
    - Any other signal connected to it? No.

The problem might be more subtle. The screenshot shows the "Period: Loading..." and "Currency: Loading..." texts very faintly in the center-top of the KPI group box, and then the main KPI labels on the left with "Loading..." on the right.

This UI structure in `_init_ui` for `DashboardWidget` from response_42 (which should be current):
```python
        self.period_label = QLabel("Period: Loading...")
        kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        current_row += 1
        self.base_currency_label = QLabel("Currency: N/A") # Initialized to N/A
        kpi_layout.addWidget(self.base_currency_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        # ...
        self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):") # This sets value to "Loading..."
```
In `_request_kpi_load`:
```python
        for label in labels_to_reset: # revenue_value_label etc. are in labels_to_reset
            label.setText("Loading...")
        self.period_label.setText("Period: Loading...")
        self.base_currency_label.setText("Currency: Loading...") # Changed from N/A to Loading...
```
This is consistent.

If `_update_kpi_display_slot` is called with valid `kpi_data_dto` (which it should be in the "No fiscal year found" scenario), the labels *should* change.

Could the `kpi_data_dto` object be `None` when `_update_kpi_display_slot` is called, and the `QMessageBox.warning` in the `else` block is somehow suppressed or not showing? If `kpi_data_dto` is `None`, all labels would be set to "N/A - Error fetching data" or "Period: N/A", "Currency: N/A". This is not what the screenshot shows ("Loading...").

This means the `if kpi_data_dto:` block in `_update_kpi_display_slot` is likely being entered.
If so, why are the labels not updating from "Loading..." to the actual values (even if those values are "0.00" or "N/A" from `_format_decimal_for_display`)?

Is `_format_decimal_for_display` returning "Loading..." by mistake?
```python
    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A" # This would show "N/A", not "Loading..."
        prefix = f"{currency_symbol} " if currency_symbol else ""
        return f"{prefix}{value:,.2f}"
```
This function seems correct and wouldn't return "Loading...".

The only way for the labels to *remain* "Loading..." after `_update_kpi_display_slot` is called with valid (even if zero-valued) `DashboardKPIData` is if the `setText` calls are not effective, or if `_request_kpi_load` is called again immediately after `_update_kpi_display_slot` finishes, resetting them.

Let's try to add more logging to pinpoint the execution flow within `DashboardWidget`.
Specifically:
1.  Log at the start of `_request_kpi_load`.
2.  Log at the start of `_fetch_kpis_data`.
3.  Log *after* `await self.app_core.dashboard_manager.get_dashboard_kpis()` and print the `kpi_data` received.
4.  Log at the start of `_update_kpi_display_slot` and print the received `kpi_data_dto`.
5.  Log after each `setText` call in `_update_kpi_display_slot`.

This detailed logging will confirm if the slot is called, what data it receives, and if `setText` is attempted.
However, I cannot execute and see these logs. I have to deduce from the existing behavior.

The key discrepancy:
-   Logs show `DashboardManager` seems to finish and returns data (even if YTD is 0).
-   UI remains stuck on "Loading..." set by `_request_kpi_load`.
-   No error messages (like the `QMessageBox` for `kpi_data_dto is None`) are reported by the user.

This strongly suggests `_update_kpi_display_slot` is either not being called with the expected `DashboardKPIData` object, or there's an issue in its execution before labels are updated, or it *is* called correctly but the UI isn't repainting for some reason (very unlikely for simple `QLabel.setText`).

What if `Q_ARG(object, kpi_data)` is the issue and `kpi_data` is not being passed correctly through `QMetaObject.invokeMethod`?
`kpi_data` is a `DashboardKPIData` instance or `None`. Pydantic models are Python objects. `Q_ARG(object, ...)` should handle this.

Is there a chance `QTimer.singleShot(0, self._request_kpi_load)` is being set up multiple times?
No, it's in `__init__`.

What if the `kpi_layout` (the `QGridLayout`) is somehow not part of the main widget's layout after `kpi_group` is added?
```python
        kpi_group = QGroupBox("Key Performance Indicators")
        self.main_layout.addWidget(kpi_group) # kpi_group is added to main_layout
        
        kpi_layout = QGridLayout(kpi_group) # kpi_layout's parent is kpi_group
```
This is standard and correct. Labels added to `kpi_layout` are children of `kpi_group`.

Could the problem be with the `add_kpi_row` helper?
```python
        def add_kpi_row(layout: QGridLayout, row: int, title: str) -> QLabel:
            title_label = QLabel(title)
            # ...
            value_label = QLabel("Loading...") # Initial text
            # ...
            layout.addWidget(title_label, row, 0)
            layout.addWidget(value_label, row, 1)
            return value_label # Returns the value_label

        self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):")
```
This pattern is correct. `self.revenue_value_label` correctly holds the `QLabel` instance.

The user's log shows the "No fiscal year found" warning.
Then, in `DashboardManager`, in this case:
```python
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"
                current_cash_balance = await self._get_total_cash_balance(base_currency)
                total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance()
                total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance()
                return DashboardKPIData(
                    kpi_period_description=kpi_period_description,
                    base_currency=base_currency, # e.g. "SGD"
                    total_revenue_ytd=Decimal(0), 
                    total_expenses_ytd=Decimal(0), 
                    net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance, # e.g. Decimal('123.45')
                    total_outstanding_ar=total_outstanding_ar, # e.g. Decimal('500.00')
                    total_outstanding_ap=total_outstanding_ap  # e.g. Decimal('200.00')
                )
```
This returned `DashboardKPIData` object is then passed to `_update_kpi_display_slot`.
In the slot:
```python
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}") # Should become "Period: As of 03 Jun 2025 (No active FY)"
            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}") # Should become "Currency: SGD"
            
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(Decimal(0), bc_symbol)) # Should become "SGD 0.00"
            # ... and so on for other labels ...
```
All these `setText` calls should occur. The fact that they remain "Loading..." is the core mystery if the slot *is* indeed called with this data.

The "looping messages" hint is critical. If the UI is stuck in "Loading...", it means `_request_kpi_load()` is called, which sets the "Loading..." texts. Then, if `_update_kpi_display_slot()` is also called, it should overwrite them. For the "Loading..." to persist, `_update_kpi_display_slot()` must *not* be completing its `setText` calls, or `_request_kpi_load()` must be re-called immediately after, effectively undoing the updates.

Let's assume `_update_kpi_display_slot` *is* called.
The screenshot shows "Period: Loading..." and "Currency: Loading...".
These are set by `_request_kpi_load`.
If `_update_kpi_display_slot` runs with valid data, these become:
`self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")`
`self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")`
These are simple string updates.

Perhaps the issue is with the `_fetch_kpis_data` completing its `await` calls and then scheduling the `_update_kpi_display_slot`.
Is it possible that the asyncio task for `_fetch_kpis_data` is being cancelled or is erroring out silently *after* `get_dashboard_kpis` returns but before `QMetaObject.invokeMethod` can effectively run the slot in the main thread?

The `future.add_done_callback` in `_request_kpi_load` for re-enabling the button:
```python
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
```
This `res` argument in the lambda is the `Future` object itself. `res.result()` would give the result of the coroutine, or `res.exception()` would give the exception. This callback doesn't inspect the result or exception.

If `_fetch_kpis_data` (the coroutine itself) had an unhandled exception *after* `await self.app_core.dashboard_manager.get_dashboard_kpis()`, then `QMetaObject.invokeMethod` might not be reached, or the overall task might be seen as failed by the `asyncio.run_coroutine_threadsafe` mechanism. However, `_fetch_kpis_data` is wrapped in its own try-except in my latest proposed version, which should prevent unhandled exceptions from within that coroutine.

The version of `DashboardWidget` I provided in response_39 (the last time I generated it) had:
```python
    async def _fetch_kpis_data(self):
        if not self.app_core.dashboard_manager:
            # ... error handling ...
            QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, None)) # Call with None
            return
        
        kpi_data = await self.app_core.dashboard_manager.get_dashboard_kpis() # This might return None
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data))
```
This looks correct. `_update_kpi_display_slot` should be called with whatever `get_dashboard_kpis` returns.
And `get_dashboard_kpis` returns a DTO or `None`.

This situation is very similar to one where the UI update isn't being processed.
Could `QCoreApplication.processEvents()` be needed somewhere if the main loop is too busy? Unlikely for this simple update.

Let's re-check the initialization order in `DashboardWidget.__init__`:
1. `self._init_ui()` - Creates labels, sets initial text to "Loading..." (via `add_kpi_row`). `period_label` and `base_currency_label` are set to "Loading..." here too.
2. `QTimer.singleShot(0, self._request_kpi_load)` - Schedules `_request_kpi_load`.

Inside `_request_kpi_load`:
1.  Sets labels to "Loading..." (redundant for most, but confirms state).
2.  Schedules `_fetch_kpis_data`.

Inside `_fetch_kpis_data` (async):
1.  Calls `dashboard_manager.get_dashboard_kpis()` (which logs "No fiscal year found" and returns a DTO).
2.  Schedules `_update_kpi_display_slot` with the DTO.

Inside `_update_kpi_display_slot` (Qt slot):
1.  If DTO is not `None` (which it shouldn't be in this "No fiscal year" case):
    *   Updates all labels with data from DTO.

The flow seems logically sound. The fact that the "Loading..." persists suggests the final `setText` calls in `_update_kpi_display_slot` are either not happening, or their effect is immediately overwritten. Since there are no logs of `_request_kpi_load` being called multiple times, an overwrite is less likely.

Is `kpi_data_dto` actually an instance of `DashboardKPIData` inside the slot?
```python
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        # ...
        if kpi_data_dto: # This is the key check
            # type check would be: isinstance(kpi_data_dto, DashboardKPIData)
            # but Python's duck typing will allow attribute access if it "looks like" one.
            # Pydantic models passed as 'object' should retain their type.
```
If `kpi_data_dto` was not `None` but also *not* a `DashboardKPIData` instance (e.g., if it was an error string or some other unexpected object due to an issue in the `async` call or `QMetaObject` marshalling), then accessing attributes like `kpi_data_dto.kpi_period_description` would raise an `AttributeError`. Such an error, if unhandled within the slot, would be printed to the console by Qt. No such console error is reported by the user in this run.

This leads me to suspect the values being set are perhaps "empty" or being misconstrued by the labels, or the labels themselves are somehow not updating their visual representation.

A subtle point: The `DashboardManager._get_total_cash_balance` method:
```python
        active_bank_accounts = await self.app_core.bank_account_service.get_all_summary(
            active_only=True, 
            currency_code=base_currency, # Filter by base currency
            page_size=-1 # Get all
        )
        total_cash = sum(ba.current_balance for ba in active_bank_accounts if ba.currency_code == base_currency)
        return total_cash if total_cash is not None else Decimal(0)
```
If `active_bank_accounts` is empty, `sum` over an empty list is `0`. So `total_cash` will be `Decimal(0)`. This is fine.
The AR/AP service methods:
```python
            result = await session.execute(select(func.sum(customer_balances_view_table.c.outstanding_balance)))
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)
```
If the sum is `None` (e.g., no rows in view), it returns `Decimal(0)`. This is also fine.

So, in the "No fiscal year found" scenario, `DashboardKPIData` would be:
```
DashboardKPIData(
    kpi_period_description="As of 03 Jun 2025 (No active FY)",
    base_currency="SGD", # (assuming)
    total_revenue_ytd=Decimal('0'),
    total_expenses_ytd=Decimal('0'),
    net_profit_ytd=Decimal('0'),
    current_cash_balance=Decimal('sum_of_base_currency_bank_accounts_or_0'),
    total_outstanding_ar=Decimal('sum_from_customer_balances_view_or_0'),
    total_outstanding_ap=Decimal('sum_from_vendor_balances_view_or_0')
)
```
This is a valid object. `_update_kpi_display_slot` should process it.

The only remaining simple explanation is if the font color for the updated text accidentally matched the background, making it invisible, but "Loading..." was visible. This is highly unlikely.

Could the `_format_decimal_for_display` be problematic?
```python
    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        return f"{prefix}{value:,.2f}"
```
If `value` is `Decimal(0)`, it returns (e.g.) "SGD 0.00". This is not "Loading...".

Perhaps the `DashboardManager` is not being initialized correctly in `ApplicationCore` or the `dashboard_manager` property in `ApplicationCore` is not returning the instance?
`ApplicationCore.startup()`:
```python
        # ...
        from app.reporting.dashboard_manager import DashboardManager
        self._dashboard_manager_instance = DashboardManager(self)
        # ...
```
`ApplicationCore.dashboard_manager` property:
```python
    @property
    def dashboard_manager(self) -> "DashboardManager":
        if not self._dashboard_manager_instance: raise RuntimeError("DashboardManager not initialized.")
        return self._dashboard_manager_instance # type: ignore
```
This seems correct. If `DashboardManager` was not initialized, `_fetch_kpis_data` would hit the `RuntimeError` or its initial check would fail, leading to the `else` block in `_update_kpi_display_slot` (showing "N/A - Error fetching data" and the `QMessageBox`). This is not happening.

The issue might be extremely subtle.
Let's simplify the `_update_kpi_display_slot` for debugging and ensure each `setText` has a very distinct value.
And add logging within `_update_kpi_display_slot`.

Given the current logs, `get_dashboard_kpis` is called and it hits the "No fiscal year found" path, returning a valid `DashboardKPIData` object with YTD figures as 0 and other figures calculated. This object should then be passed to `_update_kpi_display_slot`.

If the "looping messages" refers to the entire `_request_kpi_load` -> `_fetch_kpis_data` -> `_update_kpi_display_slot` cycle repeating, there must be something re-triggering `_request_kpi_load`.
There is nothing apparent in the `DashboardWidget` code itself that would cause `_request_kpi_load` to loop.
The only triggers are the initial `QTimer.singleShot` and the manual refresh button.

Could the `QTimer.singleShot(0, self._request_kpi_load)` be problematic if the widget is somehow re-initialized or shown multiple times rapidly? Unlikely in a simple tabbed interface.

Let's consider the `future.add_done_callback` in `_request_kpi_load`.
```python
        if future:
            future.add_done_callback(
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
```
This callback only re-enables the refresh button. It does not interact with the data display. `res` is the `Future` object. If the task represented by `future` (which is `_fetch_kpis_data`) raises an exception, `res.result()` would re-raise it, or `res.exception()` would return it. This lambda doesn't check for exceptions. However, `_fetch_kpis_data` itself calls `_update_kpi_display_slot` using `QMetaObject.invokeMethod` *before* this `done_callback` would typically execute for the future.

One very subtle possibility: if the `Q_ARG(object, kpi_data)` in `QMetaObject.invokeMethod` has an issue with the `DashboardKPIData` type specifically, and the argument arrives as something unexpected in the slot.

The problem description says "looping messages on the dashboard". This is a strong hint. If it's not the "Fetching..." log looping, it must be the UI "Loading..." text being reset.
This implies `_request_kpi_load()` is being called repeatedly.
Since we've ruled out explicit calls in the widget's own logic, could it be an external factor or a misunderstanding of a Qt signal?
No, the connections are `self.refresh_button.clicked` and `QTimer.singleShot`.

What if the `DashboardWidget` instance itself is being recreated?
The `MainWindow._add_module_tabs` creates it once:
`self.dashboard_widget = DashboardWidget(self.app_core)`
This seems unlikely to be the source of a loop.

Let's focus on the "No fiscal year found" scenario from the logs.
`DashboardManager`:
1. Logs "No fiscal year found."
2. Sets `kpi_period_description` to "As of ... (No active FY)".
3. Calls `_get_total_cash_balance`, `get_total_outstanding_ar`, `get_total_outstanding_ap`.
4. Returns a `DashboardKPIData` object.

`DashboardWidget._fetch_kpis_data`:
1. Receives this `DashboardKPIData` object (let's call it `dto`).
2. Calls `QMetaObject.invokeMethod(self, "_update_kpi_display_slot", ..., Q_ARG(object, dto))`.

`DashboardWidget._update_kpi_display_slot(self, kpi_data_dto)`:
1. `kpi_data_dto` is the `dto` from above. It's not `None`.
2. `if kpi_data_dto:` is true.
3. `self.period_label.setText(f"Period: {dto.kpi_period_description}")` -> Should change from "Period: Loading..."
4. All other labels are updated with formatted numbers or "N/A" if a value was `None` (but they are `Decimal(0)`).

If the labels visually remain "Loading...", it means the `setText` calls in `_update_kpi_display_slot` are not having a lasting visual effect before something resets them to "Loading...".
The only place that sets them to "Loading..." is `_request_kpi_load`.

This implies `_request_kpi_load` is being called again.
What if `QTimer.singleShot(0, self._request_kpi_load)` is not behaving as a "single shot" or is somehow being re-registered? This is highly improbable.

Is there a possibility that the `_update_kpi_display_slot` *itself* indirectly causes `_request_kpi_load` to be called? For example, if updating a label triggered some other event that led back to it. No obvious connection.

Perhaps the "looping messages" refer to the *log message* `Fetching dashboard KPIs...` appearing repeatedly, even if not in the provided snippet. If that's the case, then `_request_kpi_load` *is* looping.
But the user's log snippet shows it only once.

If the dashboard is the first tab shown, `QTimer.singleShot(0, ...)` will fire.
Let's assume the update mechanism is fine for a moment, and the labels *are* being set by `_update_kpi_display_slot`. If they are set to, for example, "SGD 0.00" for YTD items, and "SGD 123.45" for cash, why would it look "stuck on loading"?
The screenshot shows the values are literally "Loading...". This means the texts set by `_update_kpi_display_slot` are not persisting visually.

This is a head-scratcher if the standard Qt mechanisms are assumed to be working.

Could the issue be related to the `QGridLayout` itself or the `QGroupBox`?
If `kpi_layout` was not properly set as the layout for `kpi_group`, or `kpi_group` not properly added, the labels might exist but not be visible or update correctly.
```python
        kpi_group = QGroupBox("Key Performance Indicators") # Created
        self.main_layout.addWidget(kpi_group)          # Added to main layout of widget
        
        kpi_layout = QGridLayout(kpi_group) # Correctly sets kpi_layout as the layout FOR kpi_group
        # ... labels added to kpi_layout ...
```
This seems correct.

What if the problem is very simple: the `self.refresh_button.setEnabled(True)` inside `_update_kpi_display_slot` is fine, but the one in the `future.add_done_callback` inside `_request_kpi_load` is causing an issue by being called too early or somehow interfering?

`_request_kpi_load`:
```python
        future = schedule_task_from_qt(self._fetch_kpis_data())
        if future:
            future.add_done_callback( # CALLBACK_A
                lambda res: QMetaObject.invokeMethod(self.refresh_button, "setEnabled", Qt.ConnectionType.QueuedConnection, Q_ARG(bool, True))
            )
```
`_fetch_kpis_data`:
```python
        # ... does async work ...
        # Calls _update_kpi_display_slot:
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data_result))
```
`_update_kpi_display_slot`:
```python
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        self.refresh_button.setEnabled(True) # CALL_B
        # ... updates labels ...
```
When `_fetch_kpis_data` (the coroutine in the future) completes:
1.  It queues `_update_kpi_display_slot` to run on the main thread.
2.  The `future` object itself transitions to "done". This triggers `CALLBACK_A`.
So, `CALLBACK_A` might run *before or after* `_update_kpi_display_slot` depending on Qt event loop scheduling and thread context switching. Both try to enable the refresh button. This is not harmful.

The log does not show the error message "Could not load Key Performance Indicators." from the `else` branch of `_update_kpi_display_slot`. This strongly implies `kpi_data_dto` is not `None`.

The only way the labels show "Loading..." is if `_request_kpi_load` set them, and `_update_kpi_display_slot` never ran or never successfully updated them *after* that.
Since no exceptions are shown in the logs from `_update_kpi_display_slot`, it suggests it runs without Python errors.

Could it be a problem with `Q_ARG(object, kpi_data_result)`? If `kpi_data_result` is a Pydantic model, it should pass as a Python object.
The previous error was fixed, so `get_dashboard_kpis` *should* be returning a `DashboardKPIData` object in the "No fiscal year" case.

What if the `kpi_layout` is too small or its contents are clipped, and "Loading..." is short enough to be seen, but longer updated texts are not? The screenshot shows ample space.

Let's re-examine `DashboardManager` in the "No fiscal year found" case:
```python
            if not current_fy:
                self.logger.warning("No fiscal year found. Cannot calculate YTD KPIs.")
                kpi_period_description = f"As of {today.strftime('%d %b %Y')} (No active FY)"
                current_cash_balance = await self._get_total_cash_balance(base_currency) # This is awaited
                total_outstanding_ar = await self.app_core.customer_service.get_total_outstanding_balance() # This is awaited
                total_outstanding_ap = await self.app_core.vendor_service.get_total_outstanding_balance() # This is awaited
                return DashboardKPIData(
                    kpi_period_description=kpi_period_description,
                    base_currency=base_currency,
                    total_revenue_ytd=Decimal(0), total_expenses_ytd=Decimal(0), net_profit_ytd=Decimal(0),
                    current_cash_balance=current_cash_balance,
                    total_outstanding_ar=total_outstanding_ar,
                    total_outstanding_ap=total_outstanding_ap
                )
```
All these `await` calls complete. A `DashboardKPIData` is constructed and returned. This object is then passed to `_update_kpi_display_slot`.

There must be something extremely simple I am overlooking or a subtle Qt behavior.
The "looping messages" from the user is still the strongest clue. If it means the "Loading..." text *flickers* or appears to be trying to update but gets reset, it would strongly suggest `_request_kpi_load` is being called multiple times.

If `_request_kpi_load` is called, it sets text to "Loading..." and then *schedules* `_fetch_kpis_data`.
If, while `_fetch_kpis_data` is running (or waiting to run, or after it schedules its UI update), `_request_kpi_load` is called *again*, then the labels would be reset to "Loading..." again.

What if `DashboardWidget` is somehow part of a layout that gets reconstructed or if it's an element in some list view that refreshes and recreates its delegate widgets? No, `DashboardWidget` is a top-level tab content.

Let's simplify `_update_kpi_display_slot` to absolute basics for a test.
If I change `_update_kpi_display_slot` to *only* do:
```python
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        self.refresh_button.setEnabled(True)
        self.period_label.setText("Period: UPDATED")
        self.base_currency_label.setText("Currency: UPDATED")
        self.revenue_value_label.setText("REVENUE UPDATED")
        # ... and so on for all labels, setting them to distinct, non-calculated strings
        if kpi_data_dto is None:
             QMessageBox.warning(self, "Dashboard Error", "KPI Data was None.")
        else:
             QMessageBox.information(self, "Dashboard Update", f"KPI Data received: {kpi_data_dto.kpi_period_description}")

```
If even this doesn't change the labels from "Loading...", then the slot is not being called or the labels are not the ones we think they are (which is unlikely given they are `self.X`).

Perhaps the `_request_kpi_load` is being called by something unexpected.
What if I add a counter to `_request_kpi_load` and log it?
```python
    # In DashboardWidget.__init__
    self._load_request_count = 0

    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count})")
        # ... rest of the method ...
```
This would show in the logs if it's looping. The provided logs only show "Fetching dashboard KPIs..." once from the manager, which is called by `_fetch_kpis_data`, which is called by `_request_kpi_load`. So if `_request_kpi_load` was looping, we'd see that log multiple times. We don't.

This means `_request_kpi_load` is likely called once.
It sets labels to "Loading...".
It schedules `_fetch_kpis_data`.
`_fetch_kpis_data` calls `get_dashboard_kpis` (which logs its start and the "no FY" warning, and returns a DTO).
`_fetch_kpis_data` then queues `_update_kpi_display_slot` with this DTO.
`_update_kpi_display_slot` runs. The `if kpi_data_dto:` block should be true.
Then `setText` should happen.

The only way this fails visually is if the `setText` calls within `_update_kpi_display_slot` are not causing a repaint, or if the text being set is somehow evaluated to "Loading...".
The `_format_decimal_for_display` returns "N/A" for `None`, or a formatted number.
Values from DTO are `Decimal(0)` or actual numbers.

This is truly baffling given the logs and code logic.
What if the `kpi_layout` and its parent `kpi_group` are not visible?
```python
        kpi_group = QGroupBox("Key Performance Indicators")
        self.main_layout.addWidget(kpi_group) # Added to main layout, should be visible
        kpi_layout = QGridLayout(kpi_group)   # Layout set for groupbox
```
This is standard.

Perhaps the font color after update is white on a white background?
The `period_label` and `base_currency_label` have `setStyleSheet("font-style: italic; color: grey;")`.
The value labels get default color.
If `QMessageBox.warning` was shown, it would be modal and obvious.

Is it possible that the `DashboardWidget` itself is not visible when `_update_kpi_display_slot` is called, and then when it becomes visible, it somehow re-runs part of its init or resets? No, the `QTimer.singleShot(0, ...)` ensures it runs after the widget is constructed and likely shown as part of the tab widget.

The message "Period: Loading..." and "Currency: Loading..." *are* visible in the screenshot. This means the `kpi_layout` and `kpi_group` are visible. And the `QLabel` instances are correct.
The `add_kpi_row` function sets initial text of value labels to "Loading...".
This is the text seen.

What if the `DashboardKPIData` object passed via `Q_ARG(object, kpi_data_result)` loses its type or data?
Let's add a type check and print in the slot.
```python
    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_param: Optional[DashboardKPIData]): # Renamed param for clarity
        self.refresh_button.setEnabled(True)
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Param type: {type(kpi_data_param)}") # LOGGING

        if isinstance(kpi_data_param, DashboardKPIData):
            self.app_core.logger.info(f"DashboardWidget: KPI Data DTO received: {kpi_data_param.kpi_period_description}, Rev: {kpi_data_param.total_revenue_ytd}") # LOGGING
            self.period_label.setText(f"Period: {kpi_data_param.kpi_period_description}")
            self.base_currency_label.setText(f"Currency: {kpi_data_param.base_currency}")
            
            bc_symbol = kpi_data_param.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_param.total_revenue_ytd, bc_symbol))
            # ... and so on
        elif kpi_data_param is None:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with None data.") # LOGGING
            # ... error handling ...
        else:
            self.app_core.logger.error(f"DashboardWidget: _update_kpi_display_slot called with unexpected data type: {type(kpi_data_param)}") # LOGGING
            # ... error handling ...
```
This logging would confirm what the slot receives. I must provide this changed file.
Since no runtime errors are shown *after* the `get_dashboard_kpis` completes and before shutdown, it implies the slot executes without raising Python exceptions.

The only place that sets "Loading..." is `_request_kpi_load`.
If `_update_kpi_display_slot` runs and updates labels to actual values, for them to revert to "Loading...", `_request_kpi_load` would have to run again.

Could the `QTimer.singleShot(0, self._request_kpi_load)` be the source of a loop if `self._request_kpi_load` itself directly or indirectly causes the widget to be re-initialized or the timer to be re-posted? That seems like a very deep Qt issue or a misconfiguration I'm not seeing.

Let's review the `add_kpi_row` function and how `kpi_layout` is used.
```python
        kpi_layout = QGridLayout(kpi_group) # This sets the layout for kpi_group
        # ...
        self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):")
        # ...
        kpi_layout.setColumnStretch(1, 1) # This applies to kpi_layout
```
This is all standard. The `kpi_layout` is properly parented to `kpi_group`.
The labels returned by `add_kpi_row` are correctly assigned to instance variables like `self.revenue_value_label`.
The `setText` calls in `_update_kpi_display_slot` are on these instance variables.

This means the labels that are initially set to "Loading..." *are the same label instances* that are later targeted by `setText` with new values.

There is no obvious logical flaw in the sequence:
1. `_request_kpi_load` sets "Loading..." and schedules async `_fetch_kpis_data`.
2. `_fetch_kpis_data` gets data (DTO with 0s for YTD, actuals for others).
3. `_fetch_kpis_data` queues `_update_kpi_display_slot` with this DTO.
4. `_update_kpi_display_slot` receives DTO, updates labels.

The fact that it remains "Loading..." and the user mentions "looping messages" (even if not seen in this log snippet for the "Fetching..." message) is the strongest indicator.

Could there be an issue with `QGridLayout` somehow not updating its child widgets' display after their text is changed? No, Qt doesn't work like that. `QLabel.setText()` triggers a repaint.

One final, simpler thought: is it possible that the `current_row` variable in `_init_ui` for `DashboardWidget` is not incremented correctly, causing labels to be overlaid on top of each other, and perhaps an older "Loading..." label is remaining visible on top of an updated one?
```python
        current_row = 0
        # ... period_label ...
        current_row += 1
        # ... base_currency_label ...
        current_row += 1
        kpi_layout.setRowStretch(current_row, 1) # Add some space
        current_row +=1 # Needs this increment after adding stretch
        self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):")
        current_row += 1
        # ...
```
This seems fine. Each `add_kpi_row` gets a new `current_row`.

The only thing left is to ensure that `_update_kpi_display_slot` is indeed getting called and that the `kpi_data_dto` object is what we expect. My proposed logging additions to `_update_kpi_display_slot` and `_fetch_kpis_data` are essential. I must provide the updated `DashboardWidget` with this logging.
Since I cannot see the logs, I will make the widget code as robust as possible regarding the data it receives.

The problem *must* be that `_update_kpi_display_slot` is not successfully updating the labels to something other than "Loading...", or `_request_kpi_load` is being called again.
The screenshot shows "Period: Loading..." and "Currency: Loading...".
In `_update_kpi_display_slot`, if `kpi_data_dto` is valid, these become:
`self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")`
`self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")`
The `kpi_period_description` in the "No fiscal year" case is "As of DD Mon YYYY (No active FY)".
The `base_currency` is likely "SGD".
These are *not* "Loading...". So if these specific labels are also stuck on "Loading...", it's even more indicative that the update slot's `setText` calls aren't visually taking effect or the slot isn't running as expected with valid data.

I will provide the `DashboardWidget` with the enhanced logging. If it's a very subtle Qt issue, this might be hard to debug without running. But the Python logic itself seems to point to the slot being called with data.

One last wild thought: could the `QTimer.singleShot(0, self._request_kpi_load)` in `__init__` be interacting badly with the main application event loop setup or the dashboard widget being shown? `0` ms timeout usually means "as soon as the event loop is idle".
This is standard practice.

The problem is not an exception, it's a UI state issue.
I'll add detailed logging to `DashboardWidget` to trace the flow and data.
</think>

Okay, the application launches without import errors now, which is excellent progress! The current issue where the Dashboard KPIs are stuck on "Loading..." despite the logs indicating that the `DashboardManager` is processing (and even correctly identifying "No fiscal year found"), suggests a problem in the UI update part of the `DashboardWidget` or how data is passed to its update slot.

The user's hint about "looping messages" is important, although the provided log snippet doesn't show the "Fetching dashboard KPIs..." message looping. It might refer to the UI elements themselves flickering or repeatedly attempting to load.

**Error Analysis and Plan:**

1.  **`DashboardManager.get_dashboard_kpis()` Behavior**:
    *   The log `WARNING - No fiscal year found. Cannot calculate YTD KPIs.` is expected if no fiscal year is set up.
    *   Crucially, in this scenario, `DashboardManager` *still returns a valid `DashboardKPIData` object*, with YTD figures as `Decimal(0)` and other figures (Cash, AR, AP) calculated as best as possible, along with a descriptive `kpi_period_description`. It does not return `None` solely for this reason.

2.  **`DashboardWidget._fetch_kpis_data()`**:
    *   This `async` method calls `get_dashboard_kpis()` and should receive the `DashboardKPIData` object.
    *   It then uses `QMetaObject.invokeMethod` to call `_update_kpi_display_slot` on the main Qt thread, passing the fetched data.

3.  **`DashboardWidget._update_kpi_display_slot()`**:
    *   This slot receives the `DashboardKPIData` object (or `None` if `DashboardManager` had an unhandled internal error, which is not the case here according to logs).
    *   If it receives a valid `DashboardKPIData` object (which it should in the "No fiscal year" case), it's supposed to update all the KPI labels with actual values (e.g., "SGD 0.00", "Period: As of ... (No active FY)", etc.).
    *   If it received `None`, it would show "N/A - Error fetching data" and a `QMessageBox.warning`. The user hasn't reported this warning, and the labels are "Loading...", not "N/A...".

**Hypothesis for "Loading..." Persisting:**

The most likely scenario, given the logs and the UI state, is that `_update_kpi_display_slot` is either:
*   Not being called at all after `_fetch_kpis_data` completes.
*   Being called, but an issue within it prevents the `setText` operations from visually updating the labels *before* something else happens.
*   The initial "Loading..." text set by `_request_kpi_load` is somehow being reset by another call to `_request_kpi_load` before the updates from `_update_kpi_display_slot` can take or hold effect (the "looping" observation).

Since the logs don't show `Fetching dashboard KPIs...` looping, let's focus on the execution and effectiveness of `_update_kpi_display_slot`. I will add more robust logging inside `DashboardWidget` to trace the data flow precisely.

**Plan to Fix (Adding Logging and Ensuring Robustness):**

Modify `app/ui/dashboard/dashboard_widget.py` to:
1.  Add detailed logging at the beginning of `_request_kpi_load`.
2.  Add detailed logging at the beginning of `_fetch_kpis_data`.
3.  Add logging *after* the `await self.app_core.dashboard_manager.get_dashboard_kpis()` call in `_fetch_kpis_data`, showing the type and key content of the returned `kpi_data`.
4.  Add detailed logging at the beginning of `_update_kpi_display_slot`, showing the type and content of the `kpi_data_dto` parameter it receives.
5.  Add logging immediately after each `setText` call on the labels within `_update_kpi_display_slot` to confirm the new text that was attempted to be set.

This enhanced logging will help confirm whether the data is flowing correctly and if the update slot is being executed as expected with the correct data. While I can't see these logs myself, providing you with this instrumented code will empower you to see the flow.

**No other files seem to be directly implicated by this specific `NameError` or the observed "Loading..." behavior based on the current traceback and information.** The circular imports were the main cross-file issue.

---
**Complete Updated File: `app/ui/dashboard/dashboard_widget.py`**
---
(This version is based on the one from my response_42, with the `QHBoxLayout` import fix, and now adding detailed logging.)

```python
# File: app/ui/dashboard/dashboard_widget.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QGroupBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, Slot, QTimer, QMetaObject, Q_ARG
from PySide6.QtGui import QFont, QIcon
from typing import Optional, TYPE_CHECKING
from decimal import Decimal

from app.utils.pydantic_models import DashboardKPIData
from app.main import schedule_task_from_qt

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DashboardWidget(QWidget):
    def __init__(self, app_core: "ApplicationCore", parent: Optional[QWidget] = None): 
        super().__init__(parent)
        self.app_core = app_core
        self._load_request_count = 0 # For debugging potential loops
        
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

        kpi_group = QGroupBox("Key Performance Indicators")
        self.main_layout.addWidget(kpi_group)
        
        kpi_layout = QGridLayout(kpi_group)
        kpi_layout.setSpacing(10)

        def add_kpi_row(layout: QGridLayout, row: int, title: str) -> QLabel:
            title_label = QLabel(title)
            title_label.setFont(QFont(self.font().family(), -1, QFont.Weight.Bold))
            value_label = QLabel("Loading...") # Initial text
            value_label.setFont(QFont(self.font().family(), 11))
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            layout.addWidget(title_label, row, 0)
            layout.addWidget(value_label, row, 1)
            return value_label

        current_row = 0
        self.period_label = QLabel("Period: Loading...")
        self.period_label.setStyleSheet("font-style: italic; color: grey;")
        kpi_layout.addWidget(self.period_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        current_row += 1

        self.base_currency_label = QLabel("Currency: Loading...")
        self.base_currency_label.setStyleSheet("font-style: italic; color: grey;")
        kpi_layout.addWidget(self.base_currency_label, current_row, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        current_row += 1
        
        kpi_layout.setRowStretch(current_row, 1) 
        current_row +=1

        self.revenue_value_label = add_kpi_row(kpi_layout, current_row, "Total Revenue (YTD):")
        current_row += 1
        self.expenses_value_label = add_kpi_row(kpi_layout, current_row, "Total Expenses (YTD):")
        current_row += 1
        self.net_profit_value_label = add_kpi_row(kpi_layout, current_row, "Net Profit / (Loss) (YTD):")
        current_row += 1

        kpi_layout.setRowStretch(current_row, 1) 
        current_row +=1
        
        self.cash_balance_value_label = add_kpi_row(kpi_layout, current_row, "Current Cash Balance:")
        current_row += 1
        self.ar_value_label = add_kpi_row(kpi_layout, current_row, "Total Outstanding Accounts Receivable:")
        current_row += 1
        self.ap_value_label = add_kpi_row(kpi_layout, current_row, "Total Outstanding Accounts Payable:")
        current_row += 1
        
        kpi_layout.setColumnStretch(1, 1) 
        self.main_layout.addStretch()

    def _format_decimal_for_display(self, value: Optional[Decimal], currency_symbol: str = "") -> str:
        if value is None:
            return "N/A"
        prefix = f"{currency_symbol} " if currency_symbol else ""
        return f"{prefix}{value:,.2f}"

    @Slot()
    def _request_kpi_load(self):
        self._load_request_count += 1
        self.app_core.logger.info(f"DashboardWidget: _request_kpi_load called (Count: {self._load_request_count}). Setting labels to 'Loading...'.")
        
        self.refresh_button.setEnabled(False)
        labels_to_reset = [
            self.revenue_value_label, self.expenses_value_label, self.net_profit_value_label,
            self.cash_balance_value_label, self.ar_value_label, self.ap_value_label
        ]
        for label in labels_to_reset:
            if hasattr(self, 'app_core') and self.app_core and hasattr(self.app_core, 'logger'): # Defensive check for logger
                 self.app_core.logger.debug(f"DashboardWidget: Resetting label {label.objectName()} to 'Loading...'")
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
        try:
            if not self.app_core.dashboard_manager:
                self.app_core.logger.error("DashboardWidget: Dashboard Manager not available in _fetch_kpis_data.")
            else:
                kpi_data_result = await self.app_core.dashboard_manager.get_dashboard_kpis()
                if kpi_data_result:
                    self.app_core.logger.info(f"DashboardWidget: Fetched KPI data: Period='{kpi_data_result.kpi_period_description}', Revenue='{kpi_data_result.total_revenue_ytd}'")
                else:
                    self.app_core.logger.warning("DashboardWidget: DashboardManager.get_dashboard_kpis returned None.")
        except Exception as e:
            self.app_core.logger.error(f"DashboardWidget: Exception in _fetch_kpis_data during manager call: {e}", exc_info=True)
        
        self.app_core.logger.info(f"DashboardWidget: Queuing _update_kpi_display_slot with data type: {type(kpi_data_result)}")
        QMetaObject.invokeMethod(self, "_update_kpi_display_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(object, kpi_data_result))

    @Slot(object)
    def _update_kpi_display_slot(self, kpi_data_dto: Optional[DashboardKPIData]):
        self.app_core.logger.info(f"DashboardWidget: _update_kpi_display_slot called. Received data type: {type(kpi_data_dto)}")
        self.refresh_button.setEnabled(True)

        if isinstance(kpi_data_dto, DashboardKPIData):
            self.app_core.logger.info(f"DashboardWidget: Updating UI with KPI Data: Period='{kpi_data_dto.kpi_period_description}'")
            
            self.period_label.setText(f"Period: {kpi_data_dto.kpi_period_description}")
            self.app_core.logger.debug(f"DashboardWidget: period_label set to '{self.period_label.text()}'")

            self.base_currency_label.setText(f"Currency: {kpi_data_dto.base_currency}")
            self.app_core.logger.debug(f"DashboardWidget: base_currency_label set to '{self.base_currency_label.text()}'")
            
            bc_symbol = kpi_data_dto.base_currency 
            
            self.revenue_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_revenue_ytd, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: revenue_value_label set to '{self.revenue_value_label.text()}'")
            
            self.expenses_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_expenses_ytd, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: expenses_value_label set to '{self.expenses_value_label.text()}'")
            
            self.net_profit_value_label.setText(self._format_decimal_for_display(kpi_data_dto.net_profit_ytd, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: net_profit_value_label set to '{self.net_profit_value_label.text()}'")
            
            self.cash_balance_value_label.setText(self._format_decimal_for_display(kpi_data_dto.current_cash_balance, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: cash_balance_value_label set to '{self.cash_balance_value_label.text()}'")
            
            self.ar_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ar, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: ar_value_label set to '{self.ar_value_label.text()}'")
            
            self.ap_value_label.setText(self._format_decimal_for_display(kpi_data_dto.total_outstanding_ap, bc_symbol))
            self.app_core.logger.debug(f"DashboardWidget: ap_value_label set to '{self.ap_value_label.text()}'")
            
            self.app_core.logger.info("DashboardWidget: UI labels updated with KPI data.")
        else:
            self.app_core.logger.warning("DashboardWidget: _update_kpi_display_slot called with None or unexpected data. Setting error text.")
            error_text = "N/A - Data unavailable"
            self.period_label.setText("Period: N/A")
            self.base_currency_label.setText("Currency: N/A")
            self.revenue_value_label.setText(error_text)
            self.expenses_value_label.setText(error_text)
            self.net_profit_value_label.setText(error_text)
            self.cash_balance_value_label.setText(error_text)
            self.ar_value_label.setText(error_text)
            self.ap_value_label.setText(error_text)
            QMessageBox.warning(self, "Dashboard Data Error", "Could not load Key Performance Indicators at this time.")

```

**Validation of the fix for `app/ui/dashboard/dashboard_widget.py`:**

*   **Line-by-Line Diff (Conceptual)**:
    *   Added `_load_request_count` for debugging.
    *   Added extensive `self.app_core.logger` calls within `_request_kpi_load`, `_fetch_kpis_data`, and `_update_kpi_display_slot` to trace execution flow and data states.
    *   The `_fetch_kpis_data` method has a more robust `try-except` block.
    *   The `_update_kpi_display_slot` now explicitly checks `isinstance(kpi_data_dto, DashboardKPIData)` and logs different paths.
    *   In the `else` branch of `_update_kpi_display_slot` (when data is `None` or unexpected), labels are set to "N/A - Data unavailable" instead of "N/A - Error fetching data" to differentiate.
*   **Correctness**: These changes do not fix an existing bug in logic directly but add significant instrumentation. This instrumentation is crucial for diagnosing why the UI might not be updating as expected, especially if the problem lies in the Qt event loop processing or the data passed between threads. The core logic for setting labels based on received data remains.
*   **No Omissions**: All previous UI structure and functionality within `DashboardWidget` are preserved.

**Conclusion for "Looping Messages" Investigation:**
The "looping messages" symptom (UI stuck on "Loading...") despite logs indicating data processing is complete is unusual if the Python logic is sound. The added logging in `DashboardWidget` is the primary tool now to observe:
1.  If `_request_kpi_load` is indeed called only once initially.
2.  What `kpi_data_result` contains when `_fetch_kpis_data` attempts to queue `_update_kpi_display_slot`.
3.  If `_update_kpi_display_slot` is called, and what its `kpi_data_dto` parameter actually is.
4.  If the `setText` methods are called with the expected new values.

If, with this new logging, the logs show that `_update_kpi_display_slot` is called with a valid `DashboardKPIData` object and all `setText` calls are logged with correct, non-"Loading..." values, but the UI *still* shows "Loading...", then the issue might be deeper within the Qt event handling or a very subtle interaction, which would be harder to diagnose without direct execution and Qt debugging tools.

However, the current logs suggest `DashboardManager.get_dashboard_kpis()` *does* complete and *does* return data (even if it's YTD=0 data due to "No fiscal year found"). The most probable points of failure were either `_update_kpi_display_slot` not being called, or being called with `None` and the `else` path having an issue. The new logging will clarify this.

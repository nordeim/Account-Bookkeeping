<think>
The user has provided an error traceback. This is excellent as it gives precise information about the failure.

**Error Analysis:**

The error is an `sqlalchemy.exc.IntegrityError` wrapping an `asyncpg.exceptions.ForeignKeyViolationError`.
The core issue is: `insert or update on table "audit_log" violates foreign key constraint "fk_al_user"`.
The `DETAIL` provides the crucial information: `Key (user_id)=(0) is not present in table "users"`.

This error occurs during the `Application.initialize_app()` coroutine, specifically when `SecurityManager.authenticate_user("admin", "password")` is called. Inside `authenticate_user`, if the user is found and the password matches, `user.last_login` and `user.failed_login_attempts` are updated. This update to `core.users` table triggers the audit log function `audit.log_data_change_trigger_func()`.

The audit trigger function tries to insert a record into `audit.audit_log` with `user_id = 0`. The foreign key `fk_al_user` on `audit.audit_log.user_id` references `core.users.id`. Since there's no user with `id=0` in the `core.users` table, the foreign key constraint is violated.

**Why is `user_id=0` being used for the audit log?**

Let's look at `app/core/database_manager.py` where `app.current_user_id` is set:
```python
# Inside DatabaseManager.session()
# ...
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id_str}';"))
            elif self.app_core and not self.app_core.current_user: # System action, no user logged in
                 await session.execute(text("SET LOCAL app.current_user_id = '0';")) # Use 0 for system
# ...
```
And the audit trigger function `audit.log_data_change_trigger_func()` in `scripts/schema.sql`:
```sql
-- ...
    BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        END IF;
    END IF;
-- ...
    INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp) VALUES (v_user_id, ...);
-- ...
```

The sequence of events during startup:
1.  `Application.initialize_app()` starts.
2.  `ApplicationCore` is initialized. At this point, `app_core.current_user` is `None`.
3.  `ApplicationCore.startup()` is called.
4.  `db_manager.initialize()` is called.
5.  Then, `authenticated_user = await current_app_core.security_manager.authenticate_user("admin", "password")` is called.
    *   Inside `authenticate_user`, a new session is obtained via `self.db_manager.session()`.
    *   Since `self.app_core.current_user` is *still* `None` at this point (it only gets set *if* authentication is successful *after* this DB interaction), the `elif self.app_core and not self.app_core.current_user:` condition in `DatabaseManager.session()` becomes true.
    *   This sets `SET LOCAL app.current_user_id = '0';`.
    *   The `authenticate_user` method proceeds to find the "admin" user (ID 2) and verifies the password.
    *   Since the password "password" is correct (as per `initial_data.sql` where `admin` user is created with `crypt('password', gen_salt('bf'))`), the code updates `user.last_login` and `user.failed_login_attempts = 0`.
    *   This `UPDATE core.users ...` triggers the audit log.
    *   The audit log trigger reads `app.current_user_id` which is '0'.
    *   It attempts to insert `user_id = 0` into `audit.audit_log`, causing the FK violation because no user with ID 0 exists.

**The problem is the assumption of `user_id = 0` for "system" actions and the timing of `current_user` being set.**

**Possible Solutions & Deliberation:**

1.  **Create a System User with ID 0:**
    *   Modify `scripts/initial_data.sql` to insert a dummy "System" user with `id=0`.
    *   **Pros:** Simple, directly addresses the FK violation.
    *   **Cons:** `id=0` is often avoided for actual data as it can be ambiguous (uninitialized vs. specific system user). SERIAL sequences usually start from 1. We'd have to manage this ID 0 specially. The `system_init_user` already has ID 1.
    *   **Refinement:** The `initial_data.sql` already creates a `system_init_user` with `id=1`. Maybe system actions should be attributed to this user? Or, if we want a generic "unauthenticated system action" user, ID 0 is okay if explicitly created.

2.  **Use `NULL` for `user_id` in `audit_log` for system actions:**
    *   Make `audit.audit_log.user_id` nullable (it already is).
    *   In `DatabaseManager.session()`, if no current user, *don't* set `app.current_user_id`, or set it to an empty string/special value that the trigger function interprets as `NULL`.
    *   The trigger function already has a fallback: `EXCEPTION WHEN OTHERS THEN v_user_id := NULL;` if `current_setting` fails or `::INTEGER` fails. And further fallbacks using `NEW.created_by` etc.
    *   **Pros:** `NULL` clearly indicates "no specific app user" or "system-internal." Avoids a dummy user record.
    *   **Cons:** The trigger's fallback logic to `NEW.created_by` or `NEW.id` might still pick up an ID if `current_setting` is not set. We need to ensure `v_user_id` truly becomes `NULL` for these cases if `app.current_user_id` is not explicitly set to a valid user.
    *   **Modification for DatabaseManager:**
        ```python
        # if self.app_core and self.app_core.current_user:
        #     ... SET LOCAL app.current_user_id = '{user_id_str}';
        # else: # For system actions or unauthenticated contexts
        #     await session.execute(text("SET LOCAL app.current_user_id = NULL;")) # Or don't set it
        ```
        And the trigger will then take `NULL` if `current_setting` returns `NULL` or fails to cast.
        Actually, `SET LOCAL app.current_user_id = NULL;` then `current_setting(...)::INTEGER` would result in `NULL`, which is fine for the `audit_log.user_id` FK.

3.  **Delay Audit Logging for `core.users` table updates triggered by authentication:**
    *   This is complex. Audit logging is usually system-wide. Disabling it temporarily or for specific tables during auth might mask legitimate audit needs or be hard to manage transactionally. Not recommended.

4.  **Special Handling in Audit Trigger for `user_id = 0`:**
    *   If `v_user_id` becomes 0, the trigger could explicitly insert `NULL` into `audit_log.user_id`.
    *   This requires modifying `scripts/schema.sql`.
        ```sql
        -- In audit.log_data_change_trigger_func()
        -- ... after v_user_id is determined ...
        IF v_user_id = 0 THEN
            v_user_id := NULL;
        END IF;
        INSERT INTO audit.audit_log (user_id,action,entity_type,entity_id,entity_name,changes,timestamp)
        VALUES (v_user_id, ...);
        ```
    *   **Pros:** Directly targets the problematic `user_id=0`.
    *   **Cons:** DB-specific fix. Still relies on the app setting `app.current_user_id = '0'`.

5.  **Fix the `authenticate_user` flow or the `app.current_user_id` setting:**
    *   The `authenticate_user` method *updates* the user record (last_login, etc.). This update is the one causing the audit.
    *   If `authenticate_user` successfully authenticates user ID 2 (admin), then the audit log for *that specific update to user ID 2* should ideally be attributed to user ID 2 itself, not "system" (ID 0 or NULL).
    *   This means `app.current_user_id` should be set to the ID of the user *being authenticated and updated* within the scope of that transaction.

    Let's trace this:
    *   `SecurityManager.authenticate_user("admin", "password")`
    *   `db_manager.session()` is entered. `app_core.current_user` is `None`. So `app.current_user_id` is set to `'0'`.
    *   `user = session.execute(select(User)... where username == "admin")`. `user` becomes the admin User object (ID 2).
    *   Password verified.
    *   `user.last_login = ...` (This marks the `user` object as dirty).
    *   `session.commit()` is called.
        *   SQLAlchemy flushes the change to `user` (ID 2).
        *   Audit trigger for `core.users` fires.
        *   Trigger reads `app.current_user_id` as `'0'`. This is the issue.

    **The audit trigger's fallback logic is relevant here:**
    ```sql
    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN BEGIN v_user_id := NEW.created_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
        ELSIF TG_OP = 'UPDATE' THEN BEGIN v_user_id := NEW.updated_by; EXCEPTION WHEN undefined_column THEN IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id; ELSE v_user_id := NULL; END IF; END;
    END IF;
    ```
    For an `UPDATE` on `core.users`, if `app.current_user_id` was not set (or set to something uncastable causing the `EXCEPTION` in the first block for `v_user_id`), the trigger *should* fall back to `v_user_id := NEW.id`. In this case, `NEW.id` would be 2 (the admin user being updated). This seems like the desired behavior for self-updates.

    So, why is `current_setting('app.current_user_id', TRUE)::INTEGER` evaluating to `0` and not `NULL` or erroring out such that the fallback is used?
    It's because `SET LOCAL app.current_user_id = '0';` is explicitly run. If we change this to `SET LOCAL app.current_user_id = NULL;` (or just don't set it if no user), the trigger's logic might work as intended.

    Let's test this refined idea:
    If `app_core.current_user` is `None` in `DatabaseManager.session()`, we set `SET LOCAL app.current_user_id = NULL;`.
    Then, in the trigger:
    `BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;`
    This would make `v_user_id` become `NULL`.
    Then the fallback logic: `IF v_user_id IS NULL THEN ... ELSIF TG_OP = 'UPDATE' ... v_user_id := NEW.id;`
    This would set `v_user_id` to `2` (the admin user's ID).
    Then `audit_log` gets `user_id = 2`. This is valid. This seems like the most correct approach.

    What if the update to `core.users` is done by another admin (e.g. user 3 updates user 2)?
    *   User 3 logs in. `app_core.current_user` is user 3.
    *   `DatabaseManager.session()` sets `app.current_user_id = '3'`.
    *   User 3 updates User 2's record.
    *   Audit trigger fires. `v_user_id` becomes `3` from `current_setting`.
    *   `audit_log` gets `user_id = 3`. This is correct (user 3 performed the action on user 2).

    What about the `system_init_user` (ID 1) created in `initial_data.sql`?
    *   `initial_data.sql` runs outside the application's session management. `app.current_user_id` is not set.
    *   Trigger: `v_user_id` becomes `NULL` initially.
    *   Fallback: `TG_OP = 'INSERT'`, `TG_TABLE_SCHEMA = 'core'`, `TG_TABLE_NAME = 'users'`. So `v_user_id := NEW.id;`.
    *   For inserting `system_init_user` (ID 1), `audit_log.user_id` will be 1. Correct.
    *   For inserting `admin` user (ID 2), `audit_log.user_id` will be 2. Correct.

    This strategy seems robust. The key is to ensure that if there's no "application context" user, `app.current_user_id` is effectively `NULL` for the trigger, allowing its internal fallback logic for self-modification or initial data seed to take over.

**Plan to Fix:**

1.  Modify `app/core/database_manager.py`:
    *   In `session()` and `connection()` methods, if `self.app_core and not self.app_core.current_user` (i.e., an application-driven action without a logged-in user, like the initial failed auth attempt which is still app-driven), set `SET LOCAL app.current_user_id = NULL;`. This will make `current_setting('app.current_user_id', TRUE)::INTEGER` evaluate to `NULL` inside the trigger.
    *   The trigger's existing fallback logic `IF v_user_id IS NULL THEN ... ELSIF TG_OP = 'UPDATE' THEN ... v_user_id := NEW.id;` will then correctly attribute the `UPDATE core.users SET last_login=...` to the user being updated (i.e., the `admin` user, ID 2).

2.  Verify `initial_data.sql`:
    *   Ensure `system_init_user` (ID 1) and `admin` (ID 2) are created. This is already the case.
    *   The audit trigger should correctly log these insertions with the user ID of the record being inserted itself because `app.current_user_id` wouldn't be set during direct SQL execution of `initial_data.sql`.

3.  No changes needed to `scripts/schema.sql` (audit trigger) if the above change to `DatabaseManager` works as theorized. The trigger's fallback logic is already designed to handle `NULL` `app.current_user_id` by using `NEW.id` for `core.users` table modifications.

Let's implement the change in `app/core/database_manager.py`.

**Consider edge cases for `app.current_user_id = NULL`:**
What if an *actual* authenticated user (say, user ID 10) is performing an action, but `app_core.current_user` somehow becomes `None` just before `SET LOCAL`?
This shouldn't happen if `app_core.current_user` is managed correctly. If it does, the audit log `user_id` would become `NULL`, which is better than FK violation. The action would be auditable but not attributed. This is an application logic issue to ensure `current_user` is consistent.

The specific SQL that failed was:
`UPDATE core.users SET last_login=$1::TIMESTAMP WITH TIME ZONE, updated_at=now() WHERE core.users.id = $2::INTEGER`
Parameters: `(datetime.datetime(2025, ..., tzinfo=...), 2)`
Here, `NEW.id` would be `2`. So, the audit log should get `user_id = 2`.

If we set `app.current_user_id = NULL` when no user is logged in to the app context:
*   Trigger: `v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER;` -> `v_user_id` becomes `NULL`.
*   Trigger: `IF v_user_id IS NULL THEN ... TG_OP = 'UPDATE' ... v_user_id := NEW.id;` -> `v_user_id` becomes `2`.
*   Audit log gets `user_id = 2`. FK `fk_al_user` referencing `core.users.id=2` is valid.

This seems like the correct path.
The previous change to `DatabaseManager` was:
```python
            elif self.app_core and not self.app_core.current_user: # System action, no user logged in
                 await session.execute(text("SET LOCAL app.current_user_id = '0';")) # Use 0 for system
```
This needs to change to `SET LOCAL app.current_user_id = NULL;` or simply *not set* the variable if there's no current user from the app's perspective. If `app.current_user_id` is not set at all, `current_setting('app.current_user_id', TRUE)` will return `NULL` (or error if `TRUE` means "must exist", which is not the case here as it's the `missing_ok` param). So, not setting it is equivalent to setting it to `NULL` for the `::INTEGER` cast.

Let's try by *not setting* `app.current_user_id` if `self.app_core.current_user` is `None`. The trigger already has:
`BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;`
This `EXCEPTION WHEN OTHERS` block will catch the case where `app.current_user_id` is not set (leading to `current_setting` potentially erroring or returning NULL which then fails integer cast if not NULL but empty string, or if it returns NULL then `NULL::INTEGER` is NULL). This should make `v_user_id` NULL and trigger the fallback.

**Refined Plan for `DatabaseManager.py`:**

1.  In `session()` and `connection()`:
    *   If `self.app_core and self.app_core.current_user` is valid, set `app.current_user_id` to that user's ID.
    *   Otherwise (if `self.app_core` is None, or `self.app_core.current_user` is None), *do not set* `app.current_user_id` at all. Let the trigger's default behavior (which includes `EXCEPTION WHEN OTHERS THEN v_user_id := NULL;`) and subsequent fallback logic handle it. This is cleaner than explicitly setting to `NULL`.

This approach relies on the robustness of the trigger's error handling and fallback logic.
The trigger is:
```sql
    BEGIN
        v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; -- TRUE means missing_ok
    EXCEPTION
        WHEN OTHERS THEN -- This catches if current_setting returns NULL and NULL::INTEGER is error, OR if not set.
            v_user_id := NULL;
    END;

    IF v_user_id IS NULL THEN
        IF TG_OP = 'INSERT' THEN
            BEGIN
                v_user_id := NEW.created_by;
            EXCEPTION
                WHEN undefined_column THEN
                    IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                        v_user_id := NEW.id;
                    ELSE
                        v_user_id := NULL; -- Default to NULL if no created_by and not users table
                    END IF;
            END;
        ELSIF TG_OP = 'UPDATE' THEN
             BEGIN
                v_user_id := NEW.updated_by;
            EXCEPTION
                WHEN undefined_column THEN
                    IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN
                        v_user_id := NEW.id; -- This is the key for self-updates on users table
                    ELSE
                        v_user_id := NULL; -- Default to NULL
                    END IF;
            END;
        -- For DELETE TG_OP, OLD.updated_by or OLD.created_by might be used, or NULL if not applicable.
        -- Current trigger doesn't explicitly handle DELETE for v_user_id if current_setting is NULL.
        -- It will remain NULL, which is acceptable for audit_log.user_id.
        END IF;
    END IF;
```
If `app.current_user_id` is not set by `DatabaseManager`, `current_setting('app.current_user_id', TRUE)` will return `NULL`. Then `NULL::INTEGER` is `NULL`. So `v_user_id` becomes `NULL`.
The `IF v_user_id IS NULL THEN` block will execute.
For the failing SQL `UPDATE core.users ... WHERE core.users.id = 2`, `TG_OP = 'UPDATE'`, `TG_TABLE_SCHEMA = 'core'`, `TG_TABLE_NAME = 'users'`.
So, `v_user_id := NEW.id;` will be executed, setting `v_user_id` to `2`.
This is the desired behavior.

So, the change in `DatabaseManager` is simply to *only* set `app.current_user_id` if there *is* an `app_core.current_user`.
And the `logging` setup in `ApplicationCore` needs `logging` imported.
`FiscalPeriodService` constructor in `ApplicationCore` was: `FiscalPeriodService(self.db_manager)`. It does not take `app_core`. This is fine.
The original `DatabaseManager` in the prompt has `self.logger = asyncio.get_event_loop().set_debug(True)`. This is incorrect, `set_debug` returns `None`. It should be `self.logger = logging.getLogger(...)`. I'll use the logger setup from `ApplicationCore`.
</think>

I've analyzed the error traceback. The `ForeignKeyViolationError` on `audit_log` with `user_id = 0` is the culprit, occurring when the application tries to update `core.users` (specifically `last_login` for the 'admin' user) during the initial authentication attempt. This update triggers the audit mechanism, which then tries to use `user_id = 0` because no application user is fully authenticated and set in `app_core.current_user` *before* this specific database transaction begins.

The fix involves refining how `app.current_user_id` is set in the database session. Instead of setting it to '0' when no user is logged in via the app context, we will *not set it at all* in such cases. This will allow the audit trigger's existing fallback logic to correctly attribute self-updates on the `core.users` table (like `last_login`) to the ID of the user record being modified.

Here's the plan and the updated files:

**Plan to Fix:**

1.  **Modify `app/core/application_core.py`**:
    *   Ensure a basic logger instance is created and assigned to `self.db_manager.logger` if it doesn't have one. This is for better debugging messages from `DatabaseManager`.
2.  **Modify `app/core/database_manager.py`**:
    *   In `__init__`, correctly initialize `self.logger` using the logger provided by `app_core` or a default.
    *   In the `session()` and `connection()` context managers:
        *   Only `SET LOCAL app.current_user_id = '{user_id_str}';` if `self.app_core and self.app_core.current_user` is valid.
        *   If there's no `self.app_core.current_user`, *do not* set `app.current_user_id` at all. The audit trigger's `EXCEPTION WHEN OTHERS THEN v_user_id := NULL;` and subsequent `IF v_user_id IS NULL THEN ...` logic will handle attributing the action correctly (e.g., using `NEW.id` for updates to the `core.users` table itself).

---
**File Generation:**

**1. Update `app/core/application_core.py`**

```python
# app/core/application_core.py
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
from app.services.accounting_services import AccountTypeService, CurrencyService as CurrencyRepoService, ExchangeRateService, FiscalYearService


from app.utils.sequence_generator import SequenceGenerator

from app.tax.gst_manager import GSTManager
from app.tax.tax_calculator import TaxCalculator
from app.reporting.financial_statement_generator import FinancialStatementGenerator
from app.reporting.report_engine import ReportEngine
import logging 

class ApplicationCore:
    def __init__(self, config_manager: ConfigManager, db_manager: DatabaseManager):
        self.config_manager = config_manager
        self.db_manager = db_manager
        self.db_manager.app_core = self 
        
        # Setup a basic logger for db_manager if not already set
        # and ensure app_core also has a logger.
        self.logger = logging.getLogger("SGBookkeeperAppCore")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO) # Set appropriate level

        if not hasattr(self.db_manager, 'logger') or self.db_manager.logger is None:
             self.db_manager.logger = self.logger # Assign app_core's logger to db_manager


        self.security_manager = SecurityManager(self.db_manager)
        self.module_manager = ModuleManager(self)

        self._account_service_instance: Optional[AccountService] = None
        self._journal_service_instance: Optional[JournalService] = None
        self._fiscal_period_service_instance: Optional[FiscalPeriodService] = None
        self._fiscal_year_service_instance: Optional[FiscalYearService] = None
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

        self.logger.info("ApplicationCore initialized.")

    async def startup(self):
        self.logger.info("ApplicationCore starting up...")
        await self.db_manager.initialize() 
        
        self._account_service_instance = AccountService(self.db_manager, self)
        self._journal_service_instance = JournalService(self.db_manager, self)
        self._fiscal_period_service_instance = FiscalPeriodService(self.db_manager)
        self._fiscal_year_service_instance = FiscalYearService(self.db_manager, self)
        self._sequence_service_instance = SequenceService(self.db_manager)
        self._company_settings_service_instance = CompanySettingsService(self.db_manager, self)
        self._configuration_service_instance = ConfigurationService(self.db_manager)
        self._tax_code_service_instance = TaxCodeService(self.db_manager, self)
        self._gst_return_service_instance = GSTReturnService(self.db_manager, self)
        
        self._account_type_service_instance = AccountTypeService(self.db_manager, self) 
        self._currency_repo_service_instance = CurrencyRepoService(self.db_manager, self)
        self._exchange_rate_service_instance = ExchangeRateService(self.db_manager, self)


        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
        
        py_sequence_generator = SequenceGenerator(self.sequence_service, app_core_ref=self) # Pass app_core to SequenceGenerator
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
        self.logger.info("ApplicationCore startup complete.")

    async def shutdown(self):
        self.logger.info("ApplicationCore shutting down...")
        await self.db_manager.close_connections()
        self.logger.info("ApplicationCore shutdown complete.")

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
    def fiscal_year_service(self) -> FiscalYearService:
        if not self._fiscal_year_service_instance: raise RuntimeError("FiscalYearService not initialized.")
        return self._fiscal_year_service_instance
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
    def currency_service(self) -> CurrencyRepoService:
        return self.currency_repo_service
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
    def accounting_service(self) -> ChartOfAccountsManager: 
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

---
**2. Update `app/core/database_manager.py`**

```python
# app/core/database_manager.py
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, TYPE_CHECKING, Any 
import logging # Import standard logging

import asyncpg 
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text 

from app.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class DatabaseManager:
    def __init__(self, config_manager: ConfigManager, app_core: Optional["ApplicationCore"] = None):
        self.config = config_manager.get_database_config()
        self.app_core = app_core 
        self.engine: Optional[Any] = None 
        self.session_factory: Optional[async_sessionmaker[AsyncSession]] = None
        self.pool: Optional[asyncpg.Pool] = None
        self.logger: Optional[logging.Logger] = None # Initialize logger attribute

    async def initialize(self):
        if self.engine: 
            return
        
        # Set up logger if not already done by app_core injecting it
        if self.app_core and hasattr(self.app_core, 'logger'):
            self.logger = self.app_core.logger
        elif not self.logger: # Basic fallback logger if app_core didn't set one
            self.logger = logging.getLogger("DatabaseManager")
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)


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
        
        self.session_factory = async_sessionmaker(
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
            if self.logger: self.logger.error(f"Failed to create asyncpg pool: {e}", exc_info=True)
            else: print(f"Failed to create asyncpg pool: {e}")
            self.pool = None 

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]: 
        if not self.session_factory:
            # This log might happen before logger is fully set if initialize isn't called first.
            log_msg = "DatabaseManager not initialized. Call initialize() first."
            if self.logger: self.logger.error(log_msg)
            else: print(f"ERROR: {log_msg}")
            raise RuntimeError(log_msg)
            
        session: AsyncSession = self.session_factory()
        try:
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await session.execute(text(f"SET LOCAL app.current_user_id = '{user_id_str}';"))
            # If no app_core.current_user, we DO NOT set app.current_user_id.
            # The audit trigger's fallback logic (EXCEPTION WHEN OTHERS -> v_user_id := NULL; IF v_user_id IS NULL THEN NEW.id for users table)
            # will handle attributing self-updates to core.users or logging NULL for other system actions.
            
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
            if self.app_core and self.app_core.current_user:
                user_id_str = str(self.app_core.current_user.id)
                await connection.execute(f"SET LOCAL app.current_user_id = '{user_id_str}';") # type: ignore
            # Again, do not set if no current_user, let trigger handle it.
            yield connection # type: ignore 
    
    async def execute_query(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_scalar(self, query, *args):
        async with self.connection() as conn:
            return await conn.fetchval(query, *args)
    
    async def execute_transaction(self, callback): 
        async with self.connection() as conn:
            async with conn.transaction(): # type: ignore 
                return await callback(conn)
    
    async def close_connections(self):
        if self.pool:
            await self.pool.close()
            self.pool = None 
        
        if self.engine:
            await self.engine.dispose() # type: ignore
            self.engine = None
```

---
**Summary of Changes and Validation:**

**`app/core/application_core.py`:**
1.  **Logger Initialization**: Added `import logging`. Initialized `self.logger` for `ApplicationCore` itself.
2.  **DBManager Logger**: Ensured that `db_manager.logger` is set to `self.logger` if `db_manager` doesn't already have one. This provides a consistent logging mechanism.
3.  **SequenceGenerator Instantiation**: Modified to pass `app_core_ref=self` to `SequenceGenerator` so it can access `db_manager` if needed for calling the DB function.

**`app/core/database_manager.py`:**
1.  **Logger Initialization**: `self.logger` is initialized (either from `app_core` or a default "DatabaseManager" logger). This ensures `self.logger` calls are safe.
2.  **`session()` and `connection()` methods for `app.current_user_id`**:
    *   The logic `elif self.app_core and not self.app_core.current_user: await session.execute(text("SET LOCAL app.current_user_id = '0';"))` (and similar for raw connection) **has been removed**.
    *   Now, `SET LOCAL app.current_user_id` is *only* executed if `self.app_core and self.app_core.current_user` is valid.
    *   If there is no application-level current user, `app.current_user_id` is *not set* in the PostgreSQL session.
    *   This change relies on the audit trigger's (`audit.log_data_change_trigger_func` in `schema.sql`) internal error handling and fallback:
        *   `BEGIN v_user_id := current_setting('app.current_user_id', TRUE)::INTEGER; EXCEPTION WHEN OTHERS THEN v_user_id := NULL; END;` will result in `v_user_id` being `NULL` if `app.current_user_id` is not set.
        *   The subsequent `IF v_user_id IS NULL THEN ...` block, particularly the part `IF TG_TABLE_SCHEMA = 'core' AND TG_TABLE_NAME = 'users' THEN v_user_id := NEW.id;`, will then correctly attribute updates to the `core.users` table (like `last_login`) to the `id` of the user record being modified (e.g., user ID 2 for the 'admin' user). This resolves the original `ForeignKeyViolationError` where `user_id=0` was problematic.

With these changes, the application should now correctly handle the audit logging during the initial authentication process. The other files modified in the previous step (`journal_service.py`, `journal_entry_manager.py`, `sequence_generator.py`) are still relevant and contain the necessary logic for their respective functionalities.

The application should be tested again to confirm the startup error is resolved.

---
https://drive.google.com/file/d/1-lQNYxO1i_5DT1QqEfMtYybal2mzhUAc/view?usp=sharing, https://drive.google.com/file/d/16gFjJpsNDcAcE0E4TkhL40Ka12eBq0i_/view?usp=sharing, https://drive.google.com/file/d/1Io9vpSP3ST1lRbemAqr0SnAfSLSCmzqI/view?usp=sharing, https://drive.google.com/file/d/1JIsAZQEejE1qm-fGe1L-QpLfOWBWWW-9/view?usp=sharing, https://drive.google.com/file/d/1Oa85u5sAFd9OgiARagGmGnqJlSw0SV8u/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221SQTCjVSg9-JUmuGgq5bhvaOTbHhi2gWe%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1TArp9rSH4Oz6EVarWHaYNBHbdJOkuU1Z/view?usp=sharing, https://drive.google.com/file/d/1Z2KhH8Sd1yHpRUoz6TOU1jLev6icDwkd/view?usp=sharing, https://drive.google.com/file/d/1e9CQtKfd6E1LhSmXliLFwXUFxeGoR35E/view?usp=sharing, https://drive.google.com/file/d/1e9OAGmsj8Z2SAD1oNT2pAwmnm3zBnlGi/view?usp=sharing, https://drive.google.com/file/d/1km1x5NEIFLkBRhpyq7OS0PsXiMoXz1VY/view?usp=sharing, https://drive.google.com/file/d/1rnl0de93Aokl_FDNzUQTEu_C4p5LECWJ/view?usp=sharing, https://drive.google.com/file/d/1s6CXBUuwyh945SzNa2Ti4PUYJpTVTXdt/view?usp=sharing


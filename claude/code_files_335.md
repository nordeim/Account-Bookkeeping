<think>
The application is failing to launch due to an `ImportError: cannot import name 'AccountService' from partially initialized module 'app.services.account_service' (most likely due to a circular import)`.

Let's trace the import chain from the traceback:

1.  `app/main.py` imports `app.ui.main_window`
2.  `app.ui.main_window` imports `app.ui.dashboard.dashboard_widget`
3.  `app.ui.dashboard.dashboard_widget` imports `app.utils.pydantic_models` (which seems fine so far)
4.  The traceback then shows `app.utils.__init__.py` imports `app.utils.sequence_generator`
5.  `app.utils.sequence_generator` imports `app.services.core_services.SequenceService`
6.  `app.services.__init__.py` is executed during the import of `core_services` (because `core_services` might import something from `app.services` or `app.services` itself is imported to make its contents available). Inside `app/services/__init__.py`, it imports `from .account_service import AccountService`.
7.  `app.services.account_service.py` imports `from app.core.database_manager import DatabaseManager`.
8.  `app.core.__init__.py` imports `from .application_core import ApplicationCore`.
9.  `app.core.application_core.py` imports `from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager`.
10. `app.accounting.__init__.py` imports `from .chart_of_accounts_manager import ChartOfAccountsManager`.
11. `app.accounting.chart_of_accounts_manager.py` imports `from app.services.account_service import AccountService`.

**The Circular Import:**
The circle is:
`app.services.__init__` (tries to import `AccountService`)
  -> `app.services.account_service`
    -> `app.core.database_manager` (imported by `AccountService` constructor type hint or direct usage)
      -> `app.core.__init__`
        -> `app.core.application_core`
          -> `app.accounting.__init__`
            -> `app.accounting.chart_of_accounts_manager`
              -> `app.services.account_service` (tries to import `AccountService` *again* while it's still being initialized)

This is a classic circular dependency. `ChartOfAccountsManager` needs `AccountService`, and `ApplicationCore` (which initializes `ChartOfAccountsManager`) is part of an import chain that `AccountService` itself triggers.

**Why did this happen now?**
In the previous step (response_53), I modified `app/services/account_service.py` to add the method `get_total_balance_by_account_category_and_type_pattern`. In its implementation, I noted:
```python
# In AccountService
class AccountService(IAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core # app_core is available
        # self.journal_service will be self.app_core.journal_service

    async def get_total_balance_by_account_category_and_type_pattern(self, ...):
        # ...
        #   journal_service = self.app_core.journal_service if self.app_core else None  <-- Accesses app_core
        #   if not journal_service: raise Exception("JournalService not available")
        #   balance = await journal_service.get_account_balance(account.id, as_of_date)
        # ...
```
While the `AccountService` constructor *already* took `app_core`, the critical point is the import chain *leading* to `AccountService` being imported.

The problem likely arises from how `ApplicationCore` is structured with its properties and the eager imports at the top of `application_core.py` versus how services are imported in `app/services/__init__.py`.

**Let's examine the import chain in `app/core/application_core.py` more closely:**
It imports many managers and services directly at the top:
```python
from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager # This imports AccountService
# ...
from app.services.account_service import AccountService # This is also imported
# ...
```
And `app/services/__init__.py` also tries to make `AccountService` available for other modules that might just import `from app.services import ...`.

**Plan to Fix the Circular Import:**

The core issue is that `ChartOfAccountsManager` (imported by `ApplicationCore`) needs `AccountService`, and `AccountService` (or the chain it's part of) indirectly needs `ApplicationCore` (or modules initialized by it).

**Option 1: Type Hinting and Deferred Imports in Managers/Services**
*   Managers and Services should use forward references (strings) or `TYPE_CHECKING` blocks for type hints of other managers/services they depend on in their `__init__` signatures.
*   The actual instances of dependencies should be passed in during `ApplicationCore` initialization.
*   `ApplicationCore` itself should be careful about its own top-level imports.

`ChartOfAccountsManager` constructor:
```python
# app/accounting/chart_of_accounts_manager.py
# from app.services.account_service import AccountService # <--- Problematic direct import
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.services.account_service import AccountService
    from app.core.application_core import ApplicationCore

class ChartOfAccountsManager:
    def __init__(self, account_service: "AccountService", app_core: "ApplicationCore"): # Use string for AccountService
        self.account_service = account_service
        # ...
```
`ApplicationCore` would then instantiate it like:
```python
# app/core/application_core.py
# ...
# from app.services.account_service import AccountService # This is fine here as AppCore is higher level
# from app.accounting.chart_of_accounts_manager import ChartOfAccountsManager
# ...
# In startup or __init__ after services are ready:
# self._account_service_instance = AccountService(self.db_manager, self)
# self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self)
```
This is the standard way. Let's check if this pattern was violated.

Looking at `app/accounting/chart_of_accounts_manager.py` from `project_codebase_files_set-7.md`:
```python
# File: app/accounting/chart_of_accounts_manager.py
# (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
# Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
from app.services.account_service import AccountService # <<<<<<<< THIS IS A DIRECT IMPORT
from app.utils.result import Result
# ...
if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class ChartOfAccountsManager:
    def __init__(self, account_service: AccountService, app_core: "ApplicationCore"): # Takes AccountService directly
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 
```
Yes, `ChartOfAccountsManager` directly imports `AccountService`. This is a prime suspect.

**The fix involves:**
1.  Modify `app/accounting/chart_of_accounts_manager.py`:
    *   Remove the direct `from app.services.account_service import AccountService`.
    *   Ensure `AccountService` is type-hinted using `TYPE_CHECKING` or as a string `"AccountService"`.
2.  Modify `app/core/application_core.py`:
    *   Ensure `AccountService` is instantiated *before* `ChartOfAccountsManager`.
    *   Pass the `AccountService` instance to the `ChartOfAccountsManager` constructor.

Let's verify the instantiation order in `ApplicationCore.startup()` from `project_codebase_files_set-1.md`:
```python
# app/core/application_core.py in startup()
        # ...
        self._account_service_instance = AccountService(self.db_manager, self) # AccountService created
        # ...
        # Later:
        self._coa_manager_instance = ChartOfAccountsManager(self.account_service, self) # COAManager uses it
```
This order is correct. The issue is purely the import statement within `chart_of_accounts_manager.py`.

**Detailed Execution Plan for Fixing Circular Import:**

1.  **Identify the culprit direct import:** `from app.services.account_service import AccountService` in `app/accounting/chart_of_accounts_manager.py`.
2.  **Modify `app/accounting/chart_of_accounts_manager.py`**:
    *   Remove the direct import.
    *   Add `AccountService` to the `TYPE_CHECKING` block for type hinting, or use a string literal in the constructor.
    *   The constructor signature `__init__(self, account_service: AccountService, app_core: "ApplicationCore")` is already correct if `AccountService` is imported under `TYPE_CHECKING`.

Let's generate the updated `app/accounting/chart_of_accounts_manager.py`.

**Double-check other potential circular imports hinted by the traceback:**
The traceback shows the loop clearly:
`utils.sequence_generator` -> `services.core_services` -> `services.__init__` -> `services.account_service` -> `core.db_manager` -> `core.__init__` -> `core.application_core` -> `accounting.__init__` -> `accounting.chart_of_accounts_manager` -> `services.account_service` (again).

The chain starts quite early with `app.utils.sequence_generator` importing `app.services.core_services.SequenceService`.
*   `app.utils.sequence_generator.py`:
    ```python
    from app.models.core.sequence import Sequence
    from app.services.core_services import SequenceService # This seems fine, services should be importable by utils usually
    ```
*   `app.services.core_services.py`: This file itself does not seem to import anything that would lead back to `ApplicationCore` or managers. It imports models.
*   The problem is when `app.services.__init__.py` is processed due to the import of `SequenceService` (as `SequenceService` is part of the `app.services` package). If `app.services.__init__.py` tries to import `AccountService` too early, and `AccountService`'s module needs something that's still being set up via `ApplicationCore` (which itself imports things that might need services), the cycle can occur.

**Refined Analysis:**
The issue is that `ApplicationCore` imports `ChartOfAccountsManager` directly. `ChartOfAccountsManager` directly imports `AccountService`. `ApplicationCore` *also* directly imports `AccountService`.
When Python processes `ApplicationCore`, it sees `import ChartOfAccountsManager`. It goes to `chart_of_accounts_manager.py`.
`chart_of_accounts_manager.py` sees `import AccountService`. It goes to `account_service.py`.
`account_service.py` might import `TYPE_CHECKING` things related to `ApplicationCore` or other high-level modules, but its direct functional imports (`DatabaseManager`) are generally lower-level.

The trigger seems to be `app.services.__init__.py` executing and trying to import `AccountService` *while* `ApplicationCore` (which is needed to fully initialize services like `AccountService` with `app_core`) is still in its own import phase due to the chain starting from `main.py` -> `utils` -> `services`.

Let's trace the `main.py` path again:
`main.py` -> `app.ui.main_window` -> ... -> `app.utils.__init__` -> `app.utils.sequence_generator`
`app.utils.sequence_generator` imports `from app.services.core_services import SequenceService`.
This import causes `app.services.__init__.py` to be parsed (because `core_services.py` is in the `app.services` package, or `SequenceService` is re-exported by `app.services.__init__`).

Let's check `app.services.__init__.py` from `project_codebase_files_set-4.md`:
```python
# File: app/services/__init__.py
# ... (Interface definitions) ...
# ... (ORM Model Imports) ...
# ... (DTO Imports) ...
# --- Existing Interfaces ---
# ...
from .account_service import AccountService # <<< HERE
from .journal_service import JournalService
# ... and all other service imports
```
This file directly imports `AccountService`.

Then, `app/core/application_core.py` (which is part of the import chain *needed by `AccountService`'s `app_core` argument for full functionality*) itself imports `ChartOfAccountsManager`, which in turn imports `AccountService`.

The cycle is definitely:
`app.services.__init__` (triggered by an early import like `utils` needing `core_services`)
  -> tries to import `app.services.account_service`
    -> `app.services.account_service.py` is loaded. Its constructor takes `app_core: Optional["ApplicationCore"] = None`.
       It imports `DatabaseManager`.
       `DatabaseManager` constructor takes `app_core: Optional["ApplicationCore"] = None`.
       `ApplicationCore` is where services and managers get their `app_core` reference properly assigned.
       `AccountService` itself doesn't *directly* import `ApplicationCore` at the top level for its definition, but `ChartOfAccountsManager` does.

The direct import `from app.services.account_service import AccountService` in `app.accounting.chart_of_accounts_manager.py` is the primary culprit that completes the circular dependency path during the initial module loading phase.

**Solution Steps:**

1.  **Modify `app/accounting/chart_of_accounts_manager.py`**:
    *   Change `from app.services.account_service import AccountService` to be under `if TYPE_CHECKING:`.
    *   Ensure the constructor `__init__(self, account_service: "AccountService", ...)` uses a string literal or relies on the `TYPE_CHECKING` import.

This change should break the cycle. `ApplicationCore` will construct `AccountService` first, then pass the instance to `ChartOfAccountsManager`. When `ChartOfAccountsManager`'s methods are called, the `self.account_service` will be a fully initialized object.

Let's apply this fix.
</think>

You've encountered an `ImportError` due to a circular import. This is a common issue in Python projects when modules depend on each other in a way that forms a loop during the import process.

Let's trace and fix this:

**Error Analysis:**
The traceback shows the following import chain leading to the error:
1.  The application starts, and `app.main.py` eventually leads to imports within `app.utils.__init__.py`.
2.  `app.utils.__init__.py` imports `app.utils.sequence_generator`.
3.  `app.utils.sequence_generator` imports `SequenceService` from `app.services.core_services`.
4.  Importing from `app.services.core_services` effectively loads the `app.services` package, which means `app/services/__init__.py` is executed.
5.  `app/services/__init__.py` imports `AccountService` from `app.services.account_service`.
6.  `app.services.account_service.py` is now being initialized. It imports `DatabaseManager` from `app.core.database_manager`.
7.  `app.core.database_manager` (or an import it triggers, likely `app.core.__init__`) imports `ApplicationCore` from `app.core.application_core`.
8.  `app.core.application_core.py` (which is now being imported as part of `AccountService`'s initialization chain) imports `ChartOfAccountsManager` from `app.accounting.chart_of_accounts_manager`.
9.  `app.accounting.chart_of_accounts_manager.py` *directly imports* `AccountService` from `app.services.account_service`.

**The Circular Dependency:**
`AccountService` needs `ApplicationCore` (indirectly, via `DatabaseManager` which takes `app_core`, or for `AccountService` itself taking `app_core`). `ApplicationCore` initializes `ChartOfAccountsManager`. `ChartOfAccountsManager` directly imports `AccountService`. Python is trying to import `AccountService` while it's already in the process of being imported, leading to the "partially initialized module" error.

**Solution: Break the Direct Import Cycle**

The most common way to fix this is to use type hinting with forward references (strings) or conditional imports (`if TYPE_CHECKING:`) in the module that is lower in the dependency chain but needs a type hint from higher up. In this case, `ChartOfAccountsManager` should not directly import `AccountService` at the module level if it causes a cycle. It receives `AccountService` as a constructor argument.

**File to Modify:** `app/accounting/chart_of_accounts_manager.py`

**Detailed Plan:**
1.  In `app/accounting/chart_of_accounts_manager.py`:
    *   Remove the direct import: `from app.services.account_service import AccountService`.
    *   Ensure `AccountService` is correctly type-hinted in the `TYPE_CHECKING` block (it already is for `ApplicationCore`, so we'll add `AccountService` there).
    *   The constructor signature `__init__(self, account_service: AccountService, app_core: "ApplicationCore")` will then rely on this conditional import or a string literal for the type hint of `account_service`.

Let's apply this change.

---
**Complete Updated File: `app/accounting/chart_of_accounts_manager.py`**
---
```python
# File: app/accounting/chart_of_accounts_manager.py
# (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
# Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from app.models.accounting.account import Account 
# REMOVED: from app.services.account_service import AccountService 
from app.utils.result import Result
from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
from decimal import Decimal
from datetime import date 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.account_service import AccountService # MOVED HERE

class ChartOfAccountsManager:
    def __init__(self, account_service: "AccountService", app_core: "ApplicationCore"): # Use string literal for AccountService
        self.account_service = account_service
        self.account_validator = AccountValidator() 
        self.app_core = app_core 

    async def create_account(self, account_data: AccountCreateData) -> Result[Account]:
        validation_result = self.account_validator.validate_create(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        existing = await self.account_service.get_by_code(account_data.code)
        if existing:
            return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        account = Account(
            code=account_data.code, name=account_data.name,
            account_type=account_data.account_type, sub_type=account_data.sub_type,
            tax_treatment=account_data.tax_treatment, gst_applicable=account_data.gst_applicable,
            description=account_data.description, parent_id=account_data.parent_id,
            report_group=account_data.report_group, is_control_account=account_data.is_control_account,
            is_bank_account=account_data.is_bank_account, opening_balance=account_data.opening_balance,
            opening_balance_date=account_data.opening_balance_date, is_active=account_data.is_active,
            created_by_user_id=current_user_id, 
            updated_by_user_id=current_user_id 
        )
        
        try:
            saved_account = await self.account_service.save(account)
            return Result.success(saved_account)
        except Exception as e:
            return Result.failure([f"Failed to save account: {str(e)}"])
    
    async def update_account(self, account_data: AccountUpdateData) -> Result[Account]:
        existing_account = await self.account_service.get_by_id(account_data.id)
        if not existing_account:
            return Result.failure([f"Account with ID {account_data.id} not found."])
        
        validation_result = self.account_validator.validate_update(account_data)
        if not validation_result.is_valid:
            return Result.failure(validation_result.errors)
        
        if account_data.code != existing_account.code:
            code_exists = await self.account_service.get_by_code(account_data.code)
            if code_exists and code_exists.id != existing_account.id:
                return Result.failure([f"Account code '{account_data.code}' already exists."])
        
        current_user_id = account_data.user_id

        existing_account.code = account_data.code; existing_account.name = account_data.name
        existing_account.account_type = account_data.account_type; existing_account.sub_type = account_data.sub_type
        existing_account.tax_treatment = account_data.tax_treatment; existing_account.gst_applicable = account_data.gst_applicable
        existing_account.description = account_data.description; existing_account.parent_id = account_data.parent_id
        existing_account.report_group = account_data.report_group; existing_account.is_control_account = account_data.is_control_account
        existing_account.is_bank_account = account_data.is_bank_account; existing_account.opening_balance = account_data.opening_balance
        existing_account.opening_balance_date = account_data.opening_balance_date; existing_account.is_active = account_data.is_active
        existing_account.updated_by_user_id = current_user_id
        
        try:
            updated_account = await self.account_service.save(existing_account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to update account: {str(e)}"])
            
    async def deactivate_account(self, account_id: int, user_id: int) -> Result[Account]:
        account = await self.account_service.get_by_id(account_id)
        if not account:
            return Result.failure([f"Account with ID {account_id} not found."])
        
        if not account.is_active:
             return Result.failure([f"Account '{account.code}' is already inactive."])

        if not self.app_core or not hasattr(self.app_core, 'journal_service'): 
            return Result.failure(["Journal service not available for balance check."])

        total_current_balance = await self.app_core.journal_service.get_account_balance(account_id, date.today()) 

        if total_current_balance != Decimal(0):
            return Result.failure([f"Cannot deactivate account '{account.code}' as it has a non-zero balance ({total_current_balance:.2f})."])

        account.is_active = False
        account.updated_by_user_id = user_id 
        
        try:
            updated_account = await self.account_service.save(account)
            return Result.success(updated_account)
        except Exception as e:
            return Result.failure([f"Failed to deactivate account: {str(e)}"])

    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]:
        try:
            tree = await self.account_service.get_account_tree(active_only=active_only)
            return tree 
        except Exception as e:
            print(f"Error getting account tree: {e}") 
            return []

    async def get_accounts_for_selection(self, account_type: Optional[str] = None, active_only: bool = True) -> List[Account]:
        if account_type:
            return await self.account_service.get_by_type(account_type, active_only=active_only)
        elif active_only:
            return await self.account_service.get_all_active()
        else:
            if hasattr(self.account_service, 'get_all'):
                 return await self.account_service.get_all()
            else: 
                 return await self.account_service.get_all_active()
```

---
**Diff for `app/accounting/chart_of_accounts_manager.py`:**
```diff
--- app/accounting/chart_of_accounts_manager.py-original
+++ app/accounting/chart_of_accounts_manager.py
@@ -2,15 +2,15 @@
 # (Content previously updated to use AccountCreateData/UpdateData, ensure consistency)
 # Key: Uses AccountService. User ID comes from DTO which inherits UserAuditData.
 from typing import List, Optional, Dict, Any, TYPE_CHECKING
-from app.models.accounting.account import Account 
-from app.services.account_service import AccountService 
+from app.models.accounting.account import Account
+# from app.services.account_service import AccountService # REMOVED
 from app.utils.result import Result
 from app.utils.pydantic_models import AccountCreateData, AccountUpdateData, AccountValidator
 # from app.core.application_core import ApplicationCore # Removed direct import
 from decimal import Decimal
 from datetime import date # Added for type hint in deactivate_account
 
 if TYPE_CHECKING:
-    from app.core.application_core import ApplicationCore # For type hinting
+    from app.core.application_core import ApplicationCore
+    from app.services.account_service import AccountService # MOVED HERE
 
 class ChartOfAccountsManager:
-    def __init__(self, account_service: AccountService, app_core: "ApplicationCore"):
+    def __init__(self, account_service: "AccountService", app_core: "ApplicationCore"): # Use string literal for AccountService
         self.account_service = account_service
         self.account_validator = AccountValidator() 
         self.app_core = app_core 

```

**Validation of Changes:**
1.  **`app/accounting/chart_of_accounts_manager.py`**:
    *   The direct import `from app.services.account_service import AccountService` has been removed.
    *   `AccountService` has been added to the `if TYPE_CHECKING:` block.
    *   The constructor signature `__init__(self, account_service: "AccountService", ...)` now uses a string literal for `AccountService`, which is a valid way to handle forward references and break import cycles.
    *   All other logic within the file remains unchanged.

**Conclusion for this fix:**
The circular import issue should now be resolved by modifying `app/accounting/chart_of_accounts_manager.py` to use a forward reference for the `AccountService` type hint in its constructor and importing it conditionally under `TYPE_CHECKING`. This breaks the direct import loop that was causing the `ImportError`.

The application should now start without this specific import error. If other circular imports exist, they would need to be addressed similarly.

Let's try running the application again with this change. If successful, I will then proceed to the next roadmap item as requested.

---
https://drive.google.com/file/d/1-vPle_bsfW5q1aXJ4JI9VB5cOYY3f7oU/view?usp=sharing, https://drive.google.com/file/d/13M2zztt62TD_vYJ_XLKtW4t2E53jIHl4/view?usp=sharing, https://drive.google.com/file/d/14hkYD6mD9rl8PpF-MsJD9nZAy-1sAr0T/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%2216tABsm1Plf_0fhtruoJyyxobBli3e8-7%22%5D,%22action%22:%22open%22,%22userId%22:%22108686197475781557359%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/19ERvDxLdRedhVXYp9Gh0Xsg6tMIucGWO/view?usp=sharing, https://drive.google.com/file/d/19T9JbSrHCuXhHpzFMUh4Ti_0sDPDycSW/view?usp=sharing, https://drive.google.com/file/d/1D7GYodcMgZv3ROPPRJTYX0g9Rrsq8wJD/view?usp=sharing, https://drive.google.com/file/d/1EGOoM0TGqPgNBJzwxKdVO2u331Myhd4b/view?usp=sharing, https://drive.google.com/file/d/1Ivh39pjoqQ9z4_oj7w7hWc0zOje2-Xjb/view?usp=sharing, https://drive.google.com/file/d/1JsX5NYICgfKkbhMVeQ7ZONrbNZFb0ms3/view?usp=sharing, https://drive.google.com/file/d/1LzMu08SqY6E5ZuvISa4BsEHxatVPE9g_/view?usp=sharing, https://drive.google.com/file/d/1QyS0xlh6owfMif6KMlyXmE2Zx2hmcdza/view?usp=sharing, https://drive.google.com/file/d/1Y9orpJ67I0XwezEBeUhyJs03DdjkAMhH/view?usp=sharing, https://drive.google.com/file/d/1YG0Vqa2pI5htxdsACYigsS2TMjDHxTcl/view?usp=sharing, https://drive.google.com/file/d/1ZZODHjv2AX2Pn1cRh_0CJDTSzXRGjAt_/view?usp=sharing, https://drive.google.com/file/d/1_c8t-qcWtcVdVUEUkDQ760cjc0vL2Y9Z/view?usp=sharing, https://drive.google.com/file/d/1bSRRtsWeJI9djXTDZTZTjZxnsWS3cvsV/view?usp=sharing, https://drive.google.com/file/d/1cp5LuyXlsbaa_wFSiIMxRlBFSro8qhXq/view?usp=sharing, https://drive.google.com/file/d/1ghGjh0MtEZSDVftjVx583ocaaCDK2j9X/view?usp=sharing, https://drive.google.com/file/d/1mbj5C_Pqa-lbGFf4obvSnpdGm-ALui7y/view?usp=sharing, https://drive.google.com/file/d/1sYr8SFT1d9ZMDHLfxOS6VjtwJ3920sFT/view?usp=sharing, https://drive.google.com/file/d/1uKfTNXg8Oaes7aGaoaPB6klSZzywizh9/view?usp=sharing, https://drive.google.com/file/d/1vTPAoLcEetjBj17-5nTa_Z6RS7ND5Wmz/view?usp=sharing, https://drive.google.com/file/d/1xbA8X7irZHUayYcfOWWfi4oWm18hFDo2/view?usp=sharing


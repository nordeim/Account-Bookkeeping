# File: app/core/application_core.py
# Snippet adjustment for accounting_service property:
# ... (rest of ApplicationCore) ...
    @property
    def accounting_service(self) -> ChartOfAccountsManager: # Type hint to manager
        """Provides access to Chart of Accounts related business logic."""
        if not self._coa_manager_instance: 
            # This fallback is if startup() didn't run or direct access is attempted.
            # Better to ensure startup() always runs first.
            acc_service = AccountService(self.db_manager, self)
            self._coa_manager_instance = ChartOfAccountsManager(acc_service, self)
            # raise RuntimeError("ChartOfAccountsManager not initialized via startup().")
        return self._coa_manager_instance
# ...

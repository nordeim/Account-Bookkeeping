#!/bin/bash

# Root-level files
touch sg_bookkeeper/.gitignore
touch sg_bookkeeper/CODE_OF_CONDUCT.md
touch sg_bookkeeper/LICENSE
touch sg_bookkeeper/pyproject.toml
touch sg_bookkeeper/README.md

# .github/workflows files
touch sg_bookkeeper/.github/workflows/ci.yml

# app/ files
touch sg_bookkeeper/app/__init__.py

# app/accounting files
touch sg_bookkeeper/app/accounting/__init__.py
touch sg_bookkeeper/app/accounting/chart_of_accounts_manager.py
touch sg_bookkeeper/app/accounting/currency_manager.py
touch sg_bookkeeper/app/accounting/fiscal_period_manager.py
touch sg_bookkeeper/app/accounting/journal_entry_manager.py

# app/core files
touch sg_bookkeeper/app/core/__init__.py
touch sg_bookkeeper/app/core/application_core.py
touch sg_bookkeeper/app/core/config_manager.py
touch sg_bookkeeper/app/core/database_manager.py
touch sg_bookkeeper/app/core/module_manager.py
touch sg_bookkeeper/app/core/security_manager.py

# app/common files
touch sg_bookkeeper/app/common/enums.py

# app main file
touch sg_bookkeeper/app/main.py

# app/models files
touch sg_bookkeeper/app/models/__init__.py
touch sg_bookkeeper/app/models/base.py

# app/models/accounting files
touch sg_bookkeeper/app/models/accounting/__init__.py
touch sg_bookkeeper/app/models/accounting/account.py
touch sg_bookkeeper/app/models/accounting/account_type.py
touch sg_bookkeeper/app/models/accounting/budget.py
touch sg_bookkeeper/app/models/accounting/currency.py
touch sg_bookkeeper/app/models/accounting/dimension.py
touch sg_bookkeeper/app/models/accounting/exchange_rate.py
touch sg_bookkeeper/app/models/accounting/fiscal_period.py
touch sg_bookkeeper/app/models/accounting/fiscal_year.py
touch sg_bookkeeper/app/models/accounting/gst_return.py
touch sg_bookkeeper/app/models/accounting/journal_entry.py
touch sg_bookkeeper/app/models/accounting/recurring_pattern.py
touch sg_bookkeeper/app/models/accounting/tax_code.py
touch sg_bookkeeper/app/models/accounting/withholding_tax_certificate.py

# app/models/audit files
touch sg_bookkeeper/app/models/audit/__init__.py
touch sg_bookkeeper/app/models/audit/audit_log.py
touch sg_bookkeeper/app/models/audit/data_change_history.py

# app/models/business files
touch sg_bookkeeper/app/models/business/__init__.py
touch sg_bookkeeper/app/models/business/bank_account.py
touch sg_bookkeeper/app/models/business/bank_transaction.py
touch sg_bookkeeper/app/models/business/customer.py
touch sg_bookkeeper/app/models/business/inventory_movement.py
touch sg_bookkeeper/app/models/business/payment.py
touch sg_bookkeeper/app/models/business/product.py
touch sg_bookkeeper/app/models/business/purchase_invoice.py
touch sg_bookkeeper/app/models/business/sales_invoice.py
touch sg_bookkeeper/app/models/business/vendor.py

# app/models/core files
touch sg_bookkeeper/app/models/core/__init__.py
touch sg_bookkeeper/app/models/core/company_setting.py
touch sg_bookkeeper/app/models/core/configuration.py
touch sg_bookkeeper/app/models/core/sequence.py
touch sg_bookkeeper/app/models/core/user.py

# app/reporting files
touch sg_bookkeeper/app/reporting/__init__.py
touch sg_bookkeeper/app/reporting/financial_statement_generator.py
touch sg_bookkeeper/app/reporting/report_engine.py
touch sg_bookkeeper/app/reporting/tax_report_generator.py

# app/services files
touch sg_bookkeeper/app/services/__init__.py
touch sg_bookkeeper/app/services/account_service.py
touch sg_bookkeeper/app/services/core_services.py
touch sg_bookkeeper/app/services/fiscal_period_service.py
touch sg_bookkeeper/app/services/journal_service.py
touch sg_bookkeeper/app/services/tax_service.py

# app/tax files
touch sg_bookkeeper/app/tax/__init__.py
touch sg_bookkeeper/app/tax/gst_manager.py
touch sg_bookkeeper/app/tax/income_tax_manager.py
touch sg_bookkeeper/app/tax/tax_calculator.py
touch sg_bookkeeper/app/tax/withholding_tax_manager.py

# app/ui files
touch sg_bookkeeper/app/ui/__init__.py

# app/ui/accounting files
touch sg_bookkeeper/app/ui/accounting/__init__.py
touch sg_bookkeeper/app/ui/accounting/account_dialog.py
touch sg_bookkeeper/app/ui/accounting/accounting_widget.py
touch sg_bookkeeper/app/ui/accounting/chart_of_accounts_widget.py

# app/ui/banking files
touch sg_bookkeeper/app/ui/banking/__init__.py
touch sg_bookkeeper/app/ui/banking/banking_widget.py

# app/ui/customers files
touch sg_bookkeeper/app/ui/customers/__init__.py
touch sg_bookkeeper/app/ui/customers/customers_widget.py

# app/ui/dashboard files
touch sg_bookkeeper/app/ui/dashboard/__init__.py
touch sg_bookkeeper/app/ui/dashboard/dashboard_widget.py

# app/ui main file
touch sg_bookkeeper/app/ui/main_window.py

# app/ui/reports files
touch sg_bookkeeper/app/ui/reports/__init__.py
touch sg_bookkeeper/app/ui/reports/reports_widget.py

# app/ui/settings files
touch sg_bookkeeper/app/ui/settings/__init__.py
touch sg_bookkeeper/app/ui/settings/settings_widget.py

# app/ui/vendors files
touch sg_bookkeeper/app/ui/vendors/__init__.py
touch sg_bookkeeper/app/ui/vendors/vendors_widget.py

# app/utils files
touch sg_bookkeeper/app/utils/__init__.py
touch sg_bookkeeper/app/utils/converters.py
touch sg_bookkeeper/app/utils/formatting.py
touch sg_bookkeeper/app/utils/pydantic_models.py
touch sg_bookkeeper/app/utils/result.py
touch sg_bookkeeper/app/utils/sequence_generator.py
touch sg_bookkeeper/app/utils/validation.py

# data/ files
touch sg_bookkeeper/data/chart_of_accounts/general_template.csv
touch sg_bookkeeper/data/chart_of_accounts/retail_template.csv
touch sg_bookkeeper/data/report_templates/balance_sheet_default.json
touch sg_bookkeeper/data/tax_codes/sg_gst_codes_2023.csv

# docs/ files
touch sg_bookkeeper/docs/api_reference/index.md
touch sg_bookkeeper/docs/developer_guide/index.md
touch sg_bookkeeper/docs/user_guide/index.md

# resources/ files
touch sg_bookkeeper/resources/icons/dashboard.svg
touch sg_bookkeeper/resources/images/splash.png
touch sg_bookkeeper/resources/resources.qrc

# scripts/ files
touch sg_bookkeeper/scripts/db_init.py
touch sg_bookkeeper/scripts/initial_data.sql
touch sg_bookkeeper/scripts/schema.sql

# tests/ files at the root of tests
touch sg_bookkeeper/tests/__init__.py
touch sg_bookkeeper/tests/conftest.py

# tests/integration files
touch sg_bookkeeper/tests/integration/__init__.py
touch sg_bookkeeper/tests/integration/test_example_integration.py

# tests/ui files
touch sg_bookkeeper/tests/ui/__init__.py
touch sg_bookkeeper/tests/ui/test_example_ui.py

# tests/unit files
touch sg_bookkeeper/tests/unit/__init__.py
touch sg_bookkeeper/tests/unit/test_example_unit.py

echo "Placeholder files created successfully."

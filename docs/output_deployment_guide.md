<think>
The user wants a `deployment_guide.md` for the latest version of the application. This guide should cover:
1.  **Deployment Steps**: How to deploy the application, including database setup using the new schema and running the application.
2.  **Project File Directory Structure**: A complete tree showing all files and directories in the project.

My process to create this:

1.  **Review Current Project State**: I need to mentally (or actually, if I were a file system) list all the files and directories I've generated so far, especially after the refactoring to align with the new reference schema. This includes the new model subdirectories (`core`, `accounting`, `business`, `audit`), new services, and updated scripts.
2.  **Plan Deployment Guide Content**:
    *   **Introduction**: Brief overview.
    *   **Prerequisites**:
        *   Python version (3.9+ as per `pyproject.toml`).
        *   PostgreSQL version (14+ as per reference schema and TDS).
        *   `pip` and `poetry`.
        *   OS compatibility (Windows, macOS, Linux).
    *   **Project File Structure**: This will be a significant part, derived from my review.
    *   **Deployment Steps**:
        *   **Step 1: Obtain the Code**: Cloning from Git (conceptual repo) or downloading a release package.
        *   **Step 2: Install PostgreSQL**: General instructions for different OS.
        *   **Step 3: Set Up Python Environment & Install Dependencies**: Using Poetry.
        *   **Step 4: Configure Database Connection**: Pointing out `config.ini` and environment variables for `db_init.py`.
        *   **Step 5: Initialize the Database**: Running `sg_bookkeeper_db_init` script (which executes `schema.sql` and `initial_data.sql`).
        *   **Step 6: (Optional) Compile Qt Resources**: If `resources.qrc` is used for icons/images (my current Python code uses direct paths but `resources.qrc` is provided as an option).
        *   **Step 7: Run the Application**: Using `sg_bookkeeper` script.
    *   **Application Packaging (for Production/Distribution - Brief Mention)**: Briefly mention tools like PyInstaller, as noted in `pyproject.toml` and TDS. This guide is more about development/manual deployment.
    *   **Troubleshooting**: Common issues (DB connection, missing dependencies).
    *   **Updating the Application**: General steps (pull new code, re-run poetry install, handle DB migrations - though Alembic setup is basic in my current generation).

3.  **Generate File Structure**: I will list out the directory structure based on the files I've generated. This needs to be accurate.

    ```
    sg_bookkeeper/
    ├── .github/
    │   └── workflows/
    │       └── ci.yml
    ├── .gitignore
    ├── app/
    │   ├── __init__.py
    │   ├── accounting/
    │   │   ├── __init__.py
    │   │   ├── chart_of_accounts_manager.py
    │   │   ├── currency_manager.py
    │   │   ├── fiscal_period_manager.py
    │   │   └── journal_entry_manager.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── application_core.py
    │   │   ├── config_manager.py
    │   │   ├── database_manager.py
    │   │   ├── module_manager.py
    │   │   └── security_manager.py
    │   ├── common/
    │   │   └── enums.py
    │   ├── main.py
    │   ├── models/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── accounting/
    │   │   │   ├── __init__.py
    │   │   │   ├── account.py
    │   │   │   ├── account_type.py
    │   │   │   ├── budget.py
    │   │   │   ├── currency.py
    │   │   │   ├── dimension.py
    │   │   │   ├── exchange_rate.py
    │   │   │   ├── fiscal_period.py
    │   │   │   ├── fiscal_year.py
    │   │   │   ├── gst_return.py
    │   │   │   ├── journal_entry.py
    │   │   │   ├── recurring_pattern.py
    │   │   │   ├── tax_code.py
    │   │   │   └── withholding_tax_certificate.py
    │   │   ├── audit/
    │   │   │   ├── __init__.py
    │   │   │   ├── audit_log.py
    │   │   │   └── data_change_history.py
    │   │   ├── business/
    │   │   │   ├── __init__.py
    │   │   │   ├── bank_account.py
    │   │   │   ├── bank_transaction.py
    │   │   │   ├── customer.py  <-- Moved
    │   │   │   ├── inventory_movement.py
    │   │   │   ├── payment.py
    │   │   │   ├── product.py <-- Moved
    │   │   │   ├── purchase_invoice.py
    │   │   │   ├── sales_invoice.py
    │   │   │   └── vendor.py <-- Moved
    │   │   └── core/
    │   │       ├── __init__.py
    │   │       ├── company_setting.py <-- Moved
    │   │       ├── configuration.py
    │   │       ├── sequence.py
    │   │       └── user.py <-- Moved
    │   ├── reporting/
    │   │   ├── __init__.py
    │   │   ├── financial_statement_generator.py
    │   │   ├── report_engine.py
    │   │   └── tax_report_generator.py
    │   ├── services/
    │   │   ├── __init__.py
    │   │   ├── account_service.py
    │   │   ├── core_services.py # For SequenceService, CompanySettingsService, ConfigurationService
    │   │   ├── fiscal_period_service.py
    │   │   ├── journal_service.py
    │   │   └── tax_service.py # For TaxCodeService, GSTReturnService
    │   ├── tax/
    │   │   ├── __init__.py
    │   │   ├── gst_manager.py
    │   │   ├── income_tax_manager.py
    │   │   ├── tax_calculator.py
    │   │   └── withholding_tax_manager.py
    │   ├── ui/
    │   │   ├── __init__.py
    │   │   ├── accounting/
    │   │   │   ├── __init__.py
    │   │   │   ├── account_dialog.py
    │   │   │   ├── accounting_widget.py
    │   │   │   └── chart_of_accounts_widget.py
    │   │   ├── banking/
    │   │   │   ├── __init__.py
    │   │   │   └── banking_widget.py
    │   │   ├── customers/
    │   │   │   ├── __init__.py
    │   │   │   └── customers_widget.py
    │   │   ├── dashboard/
    │   │   │   ├── __init__.py
    │   │   │   └── dashboard_widget.py
    │   │   ├── main_window.py
    │   │   ├── reports/
    │   │   │   ├── __init__.py
    │   │   │   └── reports_widget.py
    │   │   ├── settings/
    │   │   │   ├── __init__.py
    │   │   │   └── settings_widget.py
    │   │   └── vendors/
    │   │       ├── __init__.py
    │   │       └── vendors_widget.py
    │   └── utils/
    │       ├── __init__.py # Should exist
    │       ├── converters.py
    │       ├── formatting.py
    │       ├── pydantic_models.py
    │       ├── result.py
    │       ├── sequence_generator.py
    │       └── validation.py
    ├── CODE_OF_CONDUCT.md
    ├── data/
    │   ├── chart_of_accounts/
    │   │   ├── general_template.csv
    │   │   └── retail_template.csv
    │   ├── report_templates/
    │   │   └── balance_sheet_default.json
    │   └── tax_codes/
    │       └── sg_gst_codes_2023.csv
    ├── docs/
    │   ├── api_reference/
    │   │   ├── index.md
    │   │   ├── account_service.md (etc. for all documented items)
    │   │   ├── ...
    │   ├── developer_guide/
    │   │   ├── index.md
    │   │   ├── ...
    │   └── user_guide/
    │       ├── index.md
    │       ├── ...
    ├── LICENSE
    ├── pyproject.toml
    ├── README.md
    ├── resources/
    │   ├── icons/
    │   │   ├── dashboard.svg (and all other .svg files)
    │   │   └── ...
    │   ├── images/
    │   │   └── splash.png
    │   └── resources.qrc (commented content previously, or user-created)
    ├── scripts/
    │   ├── db_init.py
    │   ├── initial_data.sql
    │   └── schema.sql
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── integration/
        │   ├── __init__.py
        │   └── test_example_integration.py
        ├── ui/
        │   ├── __init__.py
        │   └── test_example_ui.py
        └── unit/
            ├── __init__.py
            └── test_example_unit.py
    ```
    This structure seems correct based on the generated files. I will use this for the guide.

4.  **Write `deployment_guide.md`**: Structure it logically with clear, actionable steps. Emphasize the use of the new reference schema.

5.  **Review**: Check for clarity, accuracy, and completeness. Ensure it aligns with the capabilities of the generated code (e.g., `db_init.py` command).

Let's ensure the `db_init.py` script's entry point in `pyproject.toml` is correct for the deployment instructions.
It is `sg_bookkeeper_db_init = "scripts.db_init:main"`. This means from the project root, after `poetry install`, one can run `poetry run sg_bookkeeper_db_init`.

The guide should mention both development deployment (running from source) and a conceptual production deployment (using a packaged executable, though the packaging step itself won't be detailed as it's not part of code generation). The TDS 8.1 had `setup.py` which is now `pyproject.toml`. The TDS 8.3 was an installation guide for end-users using packaged app. My guide will be more for someone setting up from source or a pre-release.

A key point will be the database setup using `scripts/schema.sql` which is now the comprehensive reference schema.
The `ConfigManager` now uses platform-specific user config directories. This should be mentioned.
The `initial_data.sql` also comes from the reference schema now.
</think>

```markdown
# File: deployment_guide.md
# SG Bookkeeper - Deployment Guide

## 1. Introduction

This guide provides step-by-step instructions for deploying the SG Bookkeeper application. It covers setting up the necessary prerequisites, configuring the database with the official schema, installing dependencies, and running the application. This guide is primarily intended for developers, system administrators, or users setting up the application from source code.

## 2. Prerequisites

Before you begin, ensure your system meets the following requirements:

*   **Operating System**:
    *   Windows 10/11
    *   macOS 12+
    *   Linux (e.g., Ubuntu 20.04+)
*   **Python**: Version 3.9 or higher.
*   **PostgreSQL**: Version 14 or higher. The database server must be running and accessible.
*   **Poetry**: Python dependency management and packaging tool. Install via `pip install poetry`.
*   **Git**: For cloning the source code repository (optional if using a source archive).
*   **Hardware**:
    *   CPU: 2GHz dual-core processor or better
    *   RAM: 4GB minimum (8GB recommended)
    *   Storage: 500MB free disk space for application and dependencies, plus space for database growth.

## 3. Project File Structure

The SG Bookkeeper project has the following directory structure:

```
sg_bookkeeper/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── accounting/ # Business logic for accounting
│   │   ├── __init__.py
│   │   ├── chart_of_accounts_manager.py
│   │   ├── currency_manager.py
│   │   ├── fiscal_period_manager.py
│   │   └── journal_entry_manager.py
│   ├── core/       # Core application components
│   │   ├── __init__.py
│   │   ├── application_core.py
│   │   ├── config_manager.py
│   │   ├── database_manager.py
│   │   ├── module_manager.py
│   │   └── security_manager.py
│   ├── common/     # Common utilities, enums
│   │   └── enums.py
│   ├── main.py     # Main application entry point (GUI)
│   ├── models/     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── accounting/
│   │   │   ├── __init__.py
│   │   │   ├── account.py
│   │   │   ├── account_type.py
│   │   │   ├── budget.py
│   │   │   ├── currency.py
│   │   │   ├── dimension.py
│   │   │   ├── exchange_rate.py
│   │   │   ├── fiscal_period.py
│   │   │   ├── fiscal_year.py
│   │   │   ├── gst_return.py
│   │   │   ├── journal_entry.py
│   │   │   ├── recurring_pattern.py
│   │   │   ├── tax_code.py
│   │   │   └── withholding_tax_certificate.py
│   │   ├── audit/
│   │   │   ├── __init__.py
│   │   │   ├── audit_log.py
│   │   │   └── data_change_history.py
│   │   ├── business/
│   │   │   ├── __init__.py
│   │   │   ├── bank_account.py
│   │   │   ├── bank_transaction.py
│   │   │   ├── customer.py
│   │   │   ├── inventory_movement.py
│   │   │   ├── payment.py
│   │   │   ├── product.py
│   │   │   ├── purchase_invoice.py
│   │   │   ├── sales_invoice.py
│   │   │   └── vendor.py
│   │   └── core/ # Models for the 'core' DB schema
│   │       ├── __init__.py
│   │       ├── company_setting.py
│   │       ├── configuration.py
│   │       ├── sequence.py
│   │       └── user.py
│   ├── reporting/  # Business logic for reporting
│   │   ├── __init__.py
│   │   ├── financial_statement_generator.py
│   │   ├── report_engine.py
│   │   └── tax_report_generator.py
│   ├── services/   # Data access and low-level services
│   │   ├── __init__.py
│   │   ├── account_service.py
│   │   ├── core_services.py 
│   │   ├── fiscal_period_service.py
│   │   ├── journal_service.py
│   │   └── tax_service.py 
│   ├── tax/        # Business logic for taxation
│   │   ├── __init__.py
│   │   ├── gst_manager.py
│   │   ├── income_tax_manager.py
│   │   ├── tax_calculator.py
│   │   └── withholding_tax_manager.py
│   ├── ui/         # User interface (PySide6 widgets and dialogs)
│   │   ├── __init__.py
│   │   ├── accounting/
│   │   │   ├── __init__.py
│   │   │   ├── account_dialog.py
│   │   │   ├── accounting_widget.py
│   │   │   └── chart_of_accounts_widget.py
│   │   ├── banking/
│   │   │   ├── __init__.py
│   │   │   └── banking_widget.py
│   │   ├── customers/
│   │   │   ├── __init__.py
│   │   │   └── customers_widget.py
│   │   ├── dashboard/
│   │   │   ├── __init__.py
│   │   │   └── dashboard_widget.py
│   │   ├── main_window.py
│   │   ├── reports/
│   │   │   ├── __init__.py
│   │   │   └── reports_widget.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   └── settings_widget.py
│   │   └── vendors/
│   │       ├── __init__.py
│   │       └── vendors_widget.py
│   └── utils/      # Utility functions and helper classes
│       ├── __init__.py 
│       ├── converters.py
│       ├── formatting.py
│       ├── pydantic_models.py
│       ├── result.py
│       ├── sequence_generator.py
│       └── validation.py
├── CODE_OF_CONDUCT.md
├── data/                   # Default data, templates
│   ├── chart_of_accounts/
│   │   ├── general_template.csv
│   │   └── retail_template.csv
│   ├── report_templates/
│   │   └── balance_sheet_default.json
│   └── tax_codes/
│       └── sg_gst_codes_2023.csv
├── docs/                   # Documentation files
│   ├── api_reference/
│   │   ├── index.md 
│   │   └── ... (other .md files)
│   ├── developer_guide/
│   │   ├── index.md
│   │   └── ... (other .md files)
│   └── user_guide/
│       ├── index.md
│       └── ... (other .md files)
├── LICENSE
├── pyproject.toml          # Poetry project configuration
├── README.md
├── resources/              # Application assets (icons, images)
│   ├── icons/
│   │   ├── dashboard.svg 
│   │   └── ... (all other .svg icon files)
│   ├── images/
│   │   └── splash.png
│   └── resources.qrc       # Qt resource file (optional, for compiling resources)
├── scripts/                # Utility and build scripts
│   ├── db_init.py          # Database initialization script
│   ├── initial_data.sql    # SQL for initial data seeding
│   └── schema.sql          # Complete database schema SQL
└── tests/                  # Automated tests
    ├── __init__.py
    ├── conftest.py
    ├── integration/
    │   ├── __init__.py
    │   └── test_example_integration.py
    ├── ui/
    │   ├── __init__.py
    │   └── test_example_ui.py
    └── unit/
        ├── __init__.py
        └── test_example_unit.py
```

## 4. Deployment Steps

### Step 1: Obtain the Application Code

Clone the repository from GitHub (replace with actual repository URL):
```bash
git clone https://github.com/yourusername/sg_bookkeeper.git
cd sg_bookkeeper
```
Alternatively, download and extract a source code archive if provided.

### Step 2: Install and Configure PostgreSQL

1.  **Install PostgreSQL**: If not already installed, download and install PostgreSQL (version 14 or higher) from [postgresql.org](https://www.postgresql.org/download/). Follow the installation instructions for your operating system.
2.  **Ensure Server is Running**: Start the PostgreSQL server if it's not already running.
3.  **Create a Database User (Recommended)**: It's good practice to create a dedicated PostgreSQL user for the application. You can do this using `psql` or pgAdmin.
    ```sql
    CREATE USER sgbookkeeper_user WITH PASSWORD 'your_secure_password';
    -- The database itself will be created by the db_init.py script.
    -- If you prefer to create it manually:
    -- CREATE DATABASE sg_bookkeeper OWNER sgbookkeeper_user;
    -- GRANT ALL PRIVILEGES ON DATABASE sg_bookkeeper TO sgbookkeeper_user;
    ```
    Note: The `db_init.py` script can also use the default `postgres` superuser to create the database and then application can connect with a less privileged user if configured.

### Step 3: Set Up Python Environment and Install Dependencies

Navigate to the project root directory (`sg_bookkeeper`) and use Poetry to install dependencies:

1.  **Ensure Poetry is installed**: If not, run `pip install poetry`.
2.  **Install project dependencies**:
    ```bash
    poetry install
    ```
    This will create a virtual environment (if configured, typically in `.venv` inside the project) and install all packages listed in `pyproject.toml`.

### Step 4: Configure Database Connection

The application uses a configuration file to store database connection details and other settings.

1.  **Locate/Create Configuration File**:
    The `ConfigManager` will automatically create a default `config.ini` file in a platform-specific user configuration directory when the application (or `db_init.py` which uses `ConfigManager` indirectly) is run for the first time:
    *   Windows: `C:\Users\<YourUser>\AppData\Roaming\SGBookkeeper\config.ini`
    *   macOS: `~/Library/Application Support/SGBookkeeper/config.ini`
    *   Linux: `~/.config/SGBookkeeper/config.ini` (or `$XDG_CONFIG_HOME/SGBookkeeper/config.ini`)

2.  **Edit `config.ini` (if needed)**:
    Open the `config.ini` file and update the `[Database]` section if your PostgreSQL setup differs from the defaults (especially `username`, `password`, `host`, `port`, `database`).
    ```ini
    [Database]
    username = your_postgres_user ; e.g., sgbookkeeper_user or postgres
    password = your_secure_password ; Leave blank to be prompted by db_init.py if PGPASSWORD is not set
    host = localhost
    port = 5432
    database = sg_bookkeeper ; Name of the database to be created/used
    echo_sql = False
    ; ... other pool settings ...
    ```
    The `db_init.py` script also respects environment variables like `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`.

### Step 5: Initialize the Database

This step creates the database (if it doesn't exist and `--drop-existing` is not used for an existing one), schemas, tables, functions, views, and populates initial data using the `scripts/schema.sql` and `scripts/initial_data.sql` files.

Run the database initialization script using Poetry from the project root:
```bash
poetry run sg_bookkeeper_db_init --user your_postgres_admin_user --dbname sg_bookkeeper 
```
*   Replace `your_postgres_admin_user` with a PostgreSQL user that has privileges to create databases (e.g., `postgres` or the dedicated user if it has `CREATEDB` privilege).
*   You will be prompted for the PostgreSQL password unless it's set via the `PGPASSWORD` environment variable or specified with a `--password` argument (if the script supports it - current version prompts).
*   Use the `--drop-existing` flag if you want to delete and recreate the database:
    ```bash
    poetry run sg_bookkeeper_db_init --user your_postgres_admin_user --dbname sg_bookkeeper --drop-existing
    ```

    **Important**: The `--drop-existing` flag will permanently delete all data in the specified database. Use with caution.

### Step 6: (Optional) Compile Qt Resources

The application currently uses direct file paths for resources (e.g., `resources/icons/dashboard.svg`). If you wish to compile these into a Python module using the `resources/resources.qrc` file for potentially faster loading or cleaner packaging:

1.  Ensure `PySide6` development tools are available (usually installed with `PySide6`).
2.  Navigate to the `resources/` directory.
3.  Run the resource compiler:
    ```bash
    pyside6-rcc resources.qrc -o ../app/resources_rc.py
    ```
4.  If this step is performed, you would then need to import `app.resources_rc` in `app/main.py` or a similar central place and change all direct resource paths in the UI code (e.g., `QIcon("resources/icons/...")`) to Qt resource paths (e.g., `QIcon(":/icons/...")`).
    **Note**: This guide assumes direct paths are used unless specified otherwise by project maintainers.

### Step 7: Run the Application

Once the database is initialized and dependencies are installed, you can run the application:

```bash
poetry run sg_bookkeeper
```
This will launch the SG Bookkeeper GUI. On the first run after database setup, you might need to create an initial application admin user through the application's interface if it prompts for it (current `SecurityManager` has a mock admin, but a real setup would guide user creation).

## 5. Application Packaging (Brief Overview)

For distributing the application as a standalone executable, tools like PyInstaller can be used. The `pyproject.toml` includes `PyInstaller` as a development tool. A typical build command might look like:

```bash
poetry run pyinstaller --name SGBookkeeper --onefile --windowed app/main.py --add-data "resources:resources" --add-data "data:data"
```
This command is a basic example and would need refinement (e.g., handling icons, hidden imports). Refer to PyInstaller documentation for detailed usage.

## 6. Troubleshooting

*   **Database Connection Errors**:
    *   Ensure PostgreSQL server is running and accessible.
    *   Verify connection details in `config.ini` (username, password, host, port, database name) are correct.
    *   Check PostgreSQL logs for any connection issues.
    *   Ensure the PostgreSQL user has permissions to connect to the database and access its objects.
*   **`ModuleNotFoundError` or Missing Dependencies**:
    *   Make sure you are in the correct virtual environment activated by Poetry.
    *   Run `poetry install` again to ensure all dependencies are correctly installed.
*   **`db_init.py` Fails**:
    *   Check PostgreSQL user privileges. The user needs to be able to create databases or have the target database already created with correct ownership.
    *   Ensure `scripts/schema.sql` and `scripts/initial_data.sql` are present and readable.
    *   Check for detailed error messages printed by the script.
*   **Icons/Images Not Loading**:
    *   Verify that the `resources/` directory and its contents are correctly placed relative to the application's execution path, or that Qt resources are compiled and imported if that method is used.

## 7. Updating the Application

To update to a newer version of the application (when deployed from source):

1.  **Backup Your Database**: Always recommended before major updates. Use `pg_dump`.
2.  **Fetch Latest Code**:
    ```bash
    git pull origin main  # Or the relevant branch/tag
    ```
3.  **Update Dependencies**:
    ```bash
    poetry install
    ```
4.  **Database Migrations**: If the database schema has changed between versions, a migration script or tool (like Alembic, which is a dependency but full migration scripts are not yet generated) would be needed. For this version, if `schema.sql` has changed significantly, you might need to re-initialize the database (with data loss if not migrated) or manually apply `ALTER TABLE` commands. Always check release notes for migration instructions.
5.  **Restart the Application**.

This guide provides the fundamental steps for deploying SG Bookkeeper. For specific production environments, further considerations regarding security, backups, monitoring, and performance tuning will be necessary.
```

This `deployment_guide.md` provides a comprehensive set of instructions aligned with the latest state of the generated code, including the new database schema and project structure. I have reviewed its content for accuracy based on the files produced.

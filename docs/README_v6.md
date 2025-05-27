# SG Bookkeeper

<div align="center">

<!-- Replace with actual logo if available -->
<img src="https://raw.githubusercontent.com/nordeim/SG-Bookkeeper/refs/heads/main/home_screen.png" alt="SG Bookkeeper Logo" width="600"/>

**Singapore-Focused Small Business Accounting Software**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6 6.9+](https://img.shields.io/badge/UI-PySide6_6.9-green.svg)](https://doc.qt.io/qtforpython/)
[![PostgreSQL 14+](https://img.shields.io/badge/DB-PostgreSQL_14+-blue.svg)](https://www.postgresql.org/)
[![SQLAlchemy 2.0+](https://img.shields.io/badge/ORM-SQLAlchemy_2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Asyncpg](https://img.shields.io/badge/Async-Asyncpg-purple.svg)](https://github.com/MagicStack/asyncpg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Key Features](#key-features) • [Technology Stack](#technology-stack) • [Installation](#installation) • [Usage](#usage-guide) • [Project Structure](#project-structure) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed to meet the accounting and bookkeeping needs of small to medium-sized businesses in Singapore. Built with Python and leveraging the power of PySide6 for a modern user interface and PostgreSQL for robust data management, it offers professional-grade financial tools tailored to Singapore's regulatory environment.

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including customer and vendor management. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Core accounting, customer management, vendor management, and reporting UI are functional.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Partially Implemented, Basic UI Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; Sales/Purchases JEs via respective modules are planned)
-   **Multi-Currency Support** (Foundational - `accounting.currencies` & `exchange_rates` tables and models exist, `CurrencyManager` for backend logic. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation; period closing/reopening logic in manager.)
-   **Budgeting and Variance Analysis** (Foundational - `accounting.budgets` & `budget_details` tables and models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Partially Implemented - `TaxCode` setup for SR, ZR, ES, TX at 9%; `TaxCalculator` exists. `GSTManager` uses posted JE data. Full JE line item tax application in all transaction UIs is ongoing.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - `GSTManager` backend for data prep & finalization with JE settlement. UI in Reports tab for prep, view, draft save, and finalize.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` stub exists.)
-   **Withholding Tax Management** (Foundational - `accounting.withholding_tax_certificates` table/model and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer Management** (Implemented - List, Add, Edit, Toggle Active status for Customers, with search/filter.)
-   **Vendor Management** (Implemented - List, Add, Edit, Toggle Active status for Vendors, with search/filter.)
-   **Sales Invoicing and Accounts Receivable** (Foundational - `business.sales_invoices` tables/models exist. UI/Logic planned.)
-   **Purchase Invoicing and Accounts Payable** (Foundational - `business.purchase_invoices` tables/models exist. UI/Logic planned.)
-   **Payment Processing and Allocation** (Foundational - `business.payments` tables/models exist. UI/Logic planned.)
-   **Bank Account Management and Reconciliation Tools** (Foundational - `business.bank_accounts` & `bank_transactions` tables/models exist. UI is a stub.)
-   **Product and Service Management** (Backend Implemented - DTOs, Service, Manager integrated. UI Planned.)
-   **Basic Inventory Control** (Foundational - `business.inventory_movements` table/model exists. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - `FinancialStatementGenerator` produces data; `ReportEngine` exports basic PDF/Excel. UI in Reports tab for selection, on-screen view, and export.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above. Formatted GST reports planned.)
-   **Customizable Reporting Engine** (Planned - Current `ReportEngine` is basic.)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication with Role-Based Access Control (RBAC)** (Implemented)
-   **Granular Permissions System** (Foundational)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
(Section remains unchanged from previous README version)
...

## Installation
(Section remains unchanged from previous README version)
...

## Usage Guide

The application provides a range of functional modules accessible via tabs:

-   **Accounting Tab**:
    -   **Chart of Accounts**: View, add, edit, and (de)activate accounts.
    -   **Journal Entries**: List, filter, create, edit drafts, view, post, and reverse general journal entries.
-   **Customers Tab**:
    -   View a list of customers with search and active/inactive filter.
    -   Add new customers and edit existing customer details via a comprehensive dialog.
    -   Toggle the active/inactive status of customers.
-   **Vendors Tab**:
    -   View a list of vendors with search and active/inactive filter.
    -   Add new vendors and edit existing vendor details via a comprehensive dialog.
    -   Toggle the active/inactive status of vendors.
-   **Reports Tab**:
    -   **GST F5 Preparation**: Prepare GST F5 data, view summary, save as draft, and finalize (creates settlement JE).
    *   **Financial Statements**: Generate Balance Sheet, P&L, Trial Balance, or General Ledger. View on-screen and export to PDF/Excel.
-   **Settings Tab**:
    -   Configure Company Information and manage Fiscal Years (add new, auto-generate periods).

Other modules (Dashboard, Banking, Products & Services UI) are placeholders for future development.
The default `admin` user (password: `password` - change on first login) has full access.

## Project Structure
(Updated to include Vendor and Product backend files)
```
sg_bookkeeper/
├── app/                    # Application source code
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   ├── common/
│   ├── models/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── business_services.py   # Contains CustomerService, VendorService, ProductService
│   │   └── ... (other service files)
│   ├── accounting/
│   ├── tax/
│   ├── business_logic/     # Contains CustomerManager, VendorManager, ProductManager
│   │   ├── __init__.py
│   │   ├── customer_manager.py
│   │   ├── vendor_manager.py
│   │   └── product_manager.py # (NEW)
│   ├── reporting/
│   ├── ui/
│   │   ├── customers/      # Customer specific UI
│   │   │   ├── __init__.py
│   │   │   ├── customer_dialog.py 
│   │   │   ├── customer_table_model.py 
│   │   │   └── customers_widget.py 
│   │   ├── vendors/        # Vendor specific UI
│   │   │   ├── __init__.py
│   │   │   ├── vendor_dialog.py 
│   │   │   ├── vendor_table_model.py 
│   │   │   └── vendors_widget.py 
│   │   └── products/       # Product specific UI (foundational files created)
│   │       ├── __init__.py
│   │       ├── product_dialog.py
│   │       ├── product_table_model.py
│   │       └── products_widget.py # (Currently a stub or to be created fully)
│   └── utils/
├── data/
├── docs/
├── resources/
│   └── resources.qrc
├── scripts/
├── tests/
├── .gitignore
├── pyproject.toml
├── poetry.lock
├── README.md
└── LICENSE
```

## Database Schema
(Section remains unchanged)
...

## Development
(Section remains unchanged)
...

## Contributing
(Section remains unchanged)
...

## Roadmap

### Current Focus / Short-term
-   **Product/Service Management UI**: Implement basic UI (List, Add, Edit, Toggle Active) for products and services, using the established backend.
-   **Refine Reporting**: Improve on-screen display of financial reports (e.g., explore `QTableView` for better structure than HTML in `QTextEdit` for some reports).
-   **User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions.

### Medium-term
-   Basic Sales and Purchase Invoicing workflows (creating invoices, linking to customers/vendors/products, generating JEs).
-   Bank Account management and basic transaction entry UI in Banking module.
-   Enhance GST F5 report export options (e.g., consider IAF format if feasible).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation).
-   Multi-company support.
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

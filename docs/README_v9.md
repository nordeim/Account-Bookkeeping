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

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including customer, vendor, product/service management, and initial sales invoicing. User and Role management capabilities are also implemented. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Core accounting, business entity management (Customer, Vendor, Product), reporting UI, initial Sales Invoicing dialog, and User/Role Management are functional.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Backend Implemented, UI Dialog Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; transaction-specific JEs generated on posting of source documents like Sales Invoices)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales Invoicing Dialog uses it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab for prep, view, draft save, and finalize.)
-   **Income Tax Estimation Aids** (Planned - `IncomeTaxManager` stub exists.)
-   **Withholding Tax Management** (Foundational - Models and `WithholdingTaxManager` stub exist.)

### Business Operations
-   **Customer Management** (Implemented - List, Add, Edit, Toggle Active status, with search/filter.)
-   **Vendor Management** (Implemented - List, Add, Edit, Toggle Active status, with search/filter.)
-   **Product and Service Management** (Implemented - List, Add, Edit, Toggle Active status for Products & Services, with search/filter by type.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Draft CRUD, Posting with JE creation, List View UI.)
-   **Purchase Invoicing and Accounts Payable** (Foundational - Models exist. UI/Logic planned.)
-   **Payment Processing and Allocation** (Foundational - Models exist. UI/Logic planned.)
-   **Bank Account Management and Reconciliation Tools** (Foundational - Models exist. UI is a stub.)
-   **Basic Inventory Control** (Foundational - Models exist; `Product` model includes inventory-specific fields. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab for selection, on-screen view via native Qt views, and PDF/Excel export.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above. Formatted GST reports planned.)
-   **Customizable Reporting Engine** (Planned - Current `ReportEngine` is basic.)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication** (Implemented - Login, password hashing)
-   **Role-Based Access Control (RBAC)** (Implemented - UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented - Backend checks via `SecurityManager.has_permission()`, permissions seeded.)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
(Section remains unchanged from previous README version - already up-to-date)
...

## Installation
(Section remains unchanged from previous README version - already up-to-date)
...

## Usage Guide

The application provides a range of functional modules accessible via tabs:

-   **Accounting Tab**: Manage Chart of Accounts and Journal Entries.
-   **Sales Tab**: Create, view, edit draft, and post Sales Invoices.
-   **Customers Tab**: Manage customer information.
-   **Vendors Tab**: Manage vendor information.
-   **Products & Services Tab**: Manage products and services.
-   **Reports Tab**: Generate GST F5 data and standard Financial Statements (BS, P&L, TB, GL) with export options.
-   **Settings Tab**:
    -   **Company**: Configure company-wide information and Fiscal Years.
    -   **Users**: Manage user accounts (add, edit, toggle active, change password, assign roles).
    *   **Roles & Permissions**: Manage roles (add, edit, delete) and assign system permissions to roles.

Other modules (Dashboard, Banking, Purchase Invoicing) are placeholders or under active development.
The default `admin` user (password: `password` - change on first login) has full access.

## Project Structure
(Updated to include User/Role management UI files under `app/ui/settings/`)
```
sg_bookkeeper/
├── app/
│   ├── ... (core, common, models, services, accounting, tax, business_logic, reporting) ...
│   ├── ui/
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── settings_widget.py
│   │   │   ├── user_management_widget.py
│   │   │   ├── user_table_model.py
│   │   │   ├── user_dialog.py
│   │   │   ├── user_password_dialog.py
│   │   │   ├── role_management_widget.py
│   │   │   ├── role_table_model.py
│   │   │   └── role_dialog.py
│   │   └── ... (other ui modules like sales_invoices, customers, etc.)
│   └── utils/
├── ... (data, docs, resources, scripts, tests) ...
└── ... (project root files)
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
-   **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`.
    *   Enhance line item entry (e.g., better product search/selection).
    *   (Future) Handle inventory updates upon posting.
-   **Refine Reporting**:
    *   Improve PDF/Excel export formatting and layout.
    *   Add more reporting options/filters.
-   **Purchase Invoicing**: Begin implementation (similar lifecycle to Sales Invoicing: Draft -> Post with JE).

### Medium-term
-   Bank Account management and basic transaction entry UI in Banking module.
-   Payment recording and allocation to invoices.
-   Enhance GST F5 report export options (e.g., consider IAF format).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation).
-   Multi-company support.
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

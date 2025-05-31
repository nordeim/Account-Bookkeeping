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

The application features a double-entry accounting core, GST management, financial reporting, and modules for essential business operations including customer, vendor, product/service management, sales invoicing, and purchase invoicing (draft management). User and Role management capabilities with permission assignments are also fully implemented. Its goal is to provide an intuitive, powerful, and compliant solution that empowers business owners and accountants.

### Why SG Bookkeeper?

-   **Singapore-Centric**: Designed with Singapore Financial Reporting Standards (SFRS), GST regulations (including 9% rate), and IRAS compliance considerations at its core.
-   **Professional Grade**: Implements a full double-entry system, detailed audit trails (via database triggers), and robust data validation using Pydantic DTOs.
-   **User-Friendly Interface**: Aims for an intuitive experience for users who may not be accounting experts, while providing depth for professionals. Most core modules have functional UIs.
-   **Open Source & Local First**: Transparent development. Your financial data stays on your local machine or private server, ensuring privacy and control. No subscription fees.
-   **Modern & Performant**: Utilizes asynchronous operations for a responsive UI and efficient database interactions, with a dedicated asyncio event loop.

## Key Features

*(Status: Implemented, Backend Implemented, UI Dialog Implemented, Foundational (DB/Models ready), Planned)*

### Core Accounting
-   **Comprehensive Double-Entry Bookkeeping** (Implemented)
-   **Customizable Hierarchical Chart of Accounts** (Implemented - UI for CRUD)
-   **General Ledger with detailed transaction history** (Implemented - Report generation, on-screen view, export)
-   **Journal Entry System** (Implemented - UI for General Journal; transaction-specific JEs generated on posting of source documents)
-   **Multi-Currency Support** (Foundational - Models, CurrencyManager exist. UI integration in transactions pending.)
-   **Fiscal Year and Period Management** (Implemented - UI in Settings for FY creation and period auto-generation.)
-   **Budgeting and Variance Analysis** (Foundational - Models exist. UI/Logic planned.)

### Singapore Tax Compliance
-   **GST Tracking and Calculation** (Backend Implemented - `TaxCode` setup, `TaxCalculator` for line items. Sales/Purchase Invoice Dialogs use it.)
-   **GST F5 Return Data Preparation & Finalization** (Implemented - Backend for data prep & finalization with JE settlement. UI in Reports tab.)
-   **Income Tax Estimation Aids** (Planned)
-   **Withholding Tax Management** (Foundational)

### Business Operations
-   **Customer Management** (Implemented - Full CRUD and listing UI.)
-   **Vendor Management** (Implemented - Full CRUD and listing UI.)
-   **Product and Service Management** (Implemented - Full CRUD and listing UI.)
-   **Sales Invoicing and Accounts Receivable** (Implemented - Draft CRUD, Posting with JE creation, List View UI, "Save & Approve" in dialog.)
-   **Purchase Invoicing and Accounts Payable** (UI Dialog Implemented - Draft CRUD for Purchase Invoices. Backend draft management logic implemented. List view and posting planned.)
-   **Payment Processing and Allocation** (Foundational)
-   **Bank Account Management and Reconciliation Tools** (Foundational - UI is a stub.)
-   **Basic Inventory Control** (Foundational - `Product` model includes inventory fields. Logic planned.)

### Reporting & Analytics
-   **Standard Financial Statements**: Balance Sheet, Profit & Loss, Trial Balance, General Ledger (Implemented - UI in Reports tab with options for comparative/zero-balance, on-screen view, PDF/Excel export with enhanced formatting for BS/P&L.)
-   **Cash Flow Statement** (Planned)
-   **GST Reports** (Implemented - See GST F5 above.)
-   **Customizable Reporting Engine** (Planned)
-   **Dashboard with Key Performance Indicators (KPIs)** (Planned - UI is a stub.)

### System & Security
-   **User Authentication** (Implemented - Login, password hashing)
-   **Role-Based Access Control (RBAC)** (Implemented - UI for managing Users, Roles, and assigning Permissions to Roles.)
-   **Granular Permissions System** (Implemented - Backend checks via `SecurityManager.has_permission()`, permissions seeded.)
-   **Comprehensive Audit Trails** (Implemented - Via DB triggers and `app.current_user_id`.)
-   **PostgreSQL Database Backend** (Implemented)
-   **Data Backup and Restore Utilities** (Planned)

## Technology Stack
(Remains unchanged from previous README - accurate)
-   **Programming Language**: Python 3.9+ (up to 3.12)
-   **UI Framework**: PySide6 6.9.0+
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Async ORM with `asyncpg`)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (PDF), `openpyxl` (Excel)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`

## Installation
(Remains unchanged from previous README - accurate)
...

## Usage Guide

The application provides a range of functional modules accessible via tabs:

-   **Accounting Tab**: Manage Chart of Accounts and Journal Entries.
-   **Sales Tab**: Create, view, edit draft, and post Sales Invoices.
-   **(New Tab)** **Purchases Tab**: Create and edit draft Purchase Invoices using a dialog (accessed via a temporary button or future list view).
-   **Customers Tab**: Manage customer information.
-   **Vendors Tab**: Manage vendor information.
-   **Products & Services Tab**: Manage products and services.
-   **Reports Tab**: Generate GST F5 data and standard Financial Statements with enhanced export options and UI filters.
-   **Settings Tab**:
    -   **Company**: Configure company-wide information and Fiscal Years.
    -   **Users**: Manage user accounts (add, edit, toggle active, change password, assign roles).
    *   **Roles & Permissions**: Manage roles (add, edit, delete) and assign system permissions to roles.

Other modules (Dashboard, Banking) are placeholders. The "Purchases" tab list view is the next immediate UI task.
The default `admin` user (password: `password` - change on first login) has full access.

## Project Structure
(Updated to include Purchase Invoice UI files under `app/ui/purchase_invoices/`)
```
sg_bookkeeper/
├── app/
│   ├── ... (core, common, models, services, accounting, tax, business_logic, reporting) ...
│   ├── ui/
│   │   ├── purchase_invoices/ 
│   │   │   ├── __init__.py
│   │   │   ├── purchase_invoice_dialog.py
│   │   │   ├── purchase_invoice_table_model.py
│   │   │   └── purchase_invoices_widget.py # (New, even if basic stub initially)
│   │   ├── settings/
│   │   │   └── ... (user_dialog.py, role_dialog.py, user_password_dialog.py etc.)
│   │   └── ... (other ui modules)
│   └── utils/
├── ... (data, docs, resources, scripts, tests) ...
└── ... (project root files)
```

## Database Schema
(Remains unchanged)
...

## Development
(Remains unchanged)
...

## Contributing
(Remains unchanged)
...

## Roadmap

### Current Focus / Short-term
-   **Purchase Invoicing**:
    *   Complete UI for listing, viewing, and managing Purchase Invoices (`PurchaseInvoicesWidget`).
    *   Implement posting logic (JE creation) for Purchase Invoices.
-   **Sales Invoicing**:
    *   Enhance line item entry (e.g., better product search/selection in dialogs).
    *   (Future) Handle inventory updates upon posting.
-   **Refine Reporting**:
    *   Improve PDF/Excel export formatting for Trial Balance and General Ledger.
    *   Add more filtering options to existing reports (e.g., dimensions).

### Medium-term
-   Bank Account management and basic transaction entry UI in Banking module.
-   Payment recording and allocation to Sales and Purchase invoices.
-   Enhance GST F5 report export options (e.g., consider IAF format).

### Long-term
-   Bank Reconciliation features.
-   Advanced reporting and analytics, dashboard KPIs.
-   Inventory Control enhancements (e.g., stock movements, valuation).
-   Multi-company support.
-   Cloud synchronization options (optional).

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

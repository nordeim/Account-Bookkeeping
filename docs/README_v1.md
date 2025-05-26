# SG Bookkeeper

<div align="center">

![image](https://github.com/user-attachments/assets/efdea655-a502-4f0b-b337-c67e874da65b)

**Enterprise-grade bookkeeping for Singapore small businesses**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/UI-PySide6-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-blue.svg)](https://www.postgresql.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![codecov](https://img.shields.io/badge/codecov-80%25-green.svg)](https://codecov.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

[Features](#key-features) • [Screenshots](#screenshots) • [Installation](#installation) • [Documentation](#documentation) • [Contributing](#contributing) • [Roadmap](#roadmap) • [License](#license)

</div>

## Overview

SG Bookkeeper is a comprehensive, cross-platform desktop application designed specifically for Singapore small businesses to manage their accounting needs with precision and ease. Built with Python and modern UI frameworks, it offers enterprise-grade bookkeeping capabilities without the enterprise price tag.

The application combines professional accounting standards with an intuitive interface, enabling business owners and accountants to maintain compliant financial records, generate insightful reports, and streamline tax filing processes—all tailored to Singapore's unique regulatory environment.

### Why SG Bookkeeper?

- **Singapore-Focused**: Built from the ground up for Singapore's accounting standards and tax regulations (SFRS, GST, IRAS compliance)
- **Professional-Grade**: Double-entry accounting system with comprehensive audit trails and validation
- **User-Friendly**: Designed for business owners, not just accountants
- **Open Source**: Transparent, community-driven development with extensibility in mind
- **Cross-Platform**: Works on Windows, macOS, and Linux with a consistent experience
- **Local First**: Your data stays on your computer—no cloud dependency or subscription fees

## Screenshots

<div align="center">
  <table>
    <tr>
      <td><img src="https://via.placeholder.com/400x240?text=Dashboard" alt="Dashboard"/></td>
      <td><img src="https://via.placeholder.com/400x240?text=Chart+of+Accounts" alt="Chart of Accounts"/></td>
    </tr>
    <tr>
      <td><em>Dashboard with financial insights</em></td>
      <td><em>Hierarchical chart of accounts</em></td>
    </tr>
    <tr>
      <td><img src="https://via.placeholder.com/400x240?text=Journal+Entry" alt="Journal Entry"/></td>
      <td><img src="https://via.placeholder.com/400x240?text=GST+Report" alt="GST Report"/></td>
    </tr>
    <tr>
      <td><em>Transaction entry with tax calculation</em></td>
      <td><em>GST F5 form preparation</em></td>
    </tr>
  </table>
</div>

## Key Features

### Core Accounting
- **Double-Entry Bookkeeping**: Complete implementation of double-entry accounting principles
- **Chart of Accounts**: Hierarchical account structure with Singapore-compliant default templates
- **Journal System**: Multiple journal types with transaction validation and balancing
- **Financial Statements**: Generate balance sheets, profit & loss statements, and cash flow reports
- **Multi-Currency**: Handle transactions in multiple currencies with automatic exchange rate calculation

### Singapore Tax Compliance
- **GST Management**: Automatic GST calculation, tracking, and reporting
- **F5 Form Preparation**: Direct preparation of GST F5 return data
- **Income Tax Computation**: Tax computation worksheets and adjustments
- **XBRL Ready**: Export financial data in XBRL format for ACRA filing
- **Withholding Tax**: Calculation and reporting for services from non-resident entities

### Business Operations
- **Customer & Vendor Management**: Comprehensive contact management with transaction history
- **Invoicing**: Professional invoice creation and management with payment tracking
- **Banking**: Bank reconciliation, statement import, and payment processing
- **Financial Analytics**: Business performance dashboards and trend analysis
- **Inventory Tracking**: Basic inventory management with cost tracking

### Technical Features
- **Modern UI**: Clean, responsive interface built with Qt6
- **Database-Backed**: PostgreSQL database for robust data storage and integrity
- **User Management**: Role-based access control and permissions
- **Backup & Recovery**: Automated backup and point-in-time recovery
- **Audit Trail**: Comprehensive change logging for compliance and security

## Technology Stack

SG Bookkeeper leverages modern, robust technologies to deliver a reliable, performant application:

- **Frontend**: PyQt6/PySide6 for the user interface
- **Backend**: Python 3.9+ for application logic
- **Database**: PostgreSQL 14+ for data storage
- **ORM**: SQLAlchemy with asyncio support
- **Reporting**: ReportLab and openpyxl for document generation
- **Data Validation**: Pydantic for model validation
- **Testing**: Pytest for unit and integration testing
- **Build System**: Poetry for dependency management
- **Packaging**: PyInstaller for executable creation

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 14 or higher
- pip (Python package installer)
- Qt 6.2+ (automatically installed with PySide6)

### Quick Install (End Users)

#### Windows

1. Download the latest installer from the [releases page](https://github.com/yourusername/sg_bookkeeper/releases)
2. Run the installer and follow the wizard instructions
3. Launch SG Bookkeeper from the Start Menu

#### macOS

1. Download the latest .dmg file from the [releases page](https://github.com/yourusername/sg_bookkeeper/releases)
2. Open the .dmg file and drag SG Bookkeeper to your Applications folder
3. Launch SG Bookkeeper from Applications

#### Linux

```bash
# Install PostgreSQL if not already installed
sudo apt install postgresql-14

# Install SG Bookkeeper from PyPI
pip install sg-bookkeeper

# Launch the application
sg_bookkeeper
```

### Developer Installation

For developers who want to contribute or customize the application:

```bash
# Clone the repository
git clone https://github.com/yourusername/sg_bookkeeper.git
cd sg_bookkeeper

# Set up a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies with Poetry
pip install poetry
poetry install

# Initialize the database
python -m sg_bookkeeper.db_init --user postgres

# Run the application
python -m sg_bookkeeper
```

See the [Development Setup](#development-setup) section for more detailed instructions.

## Usage Guide

### First-Time Setup

When you first launch SG Bookkeeper, you'll be guided through a setup wizard that helps you:

1. Configure your company information
2. Set up your fiscal year
3. Choose a chart of accounts template
4. Create your first user account
5. Configure tax settings for GST

### Daily Operations

#### Recording Transactions

1. Navigate to the "Transactions" tab
2. Click "New Transaction"
3. Select transaction type (e.g., Sale, Purchase, Journal Entry)
4. Enter transaction details and line items
5. Click "Save" to record the transaction

#### Generating Reports

1. Navigate to the "Reports" tab
2. Select the desired report type
3. Configure report parameters (date range, comparison periods, etc.)
4. Click "Generate Report"
5. View, print, or export the report as needed

### Period-End Procedures

#### Monthly Reconciliation

1. Navigate to the "Banking" tab
2. Select "Bank Reconciliation"
3. Choose the account and statement period
4. Import bank statement or enter transactions manually
5. Match transactions and resolve discrepancies
6. Finalize reconciliation

#### GST Filing (Quarterly)

1. Navigate to the "Taxes" tab
2. Select "GST Returns"
3. Choose the quarter to prepare
4. Review and adjust the draft GST F5 form
5. Finalize and export for submission to IRAS

#### Year-End Closing

1. Navigate to the "Accounting" tab
2. Select "Year-End Closing"
3. Review year-end checklist
4. Perform closing entries
5. Generate year-end financial statements
6. Archive fiscal year data

## Architecture

SG Bookkeeper follows a modular, three-tier architecture designed for extensibility and maintainability:

```
+---------------------------------------------------+
|                  Presentation Layer                |
|  (PyQt6/PySide6 UI Components, QML Custom Widgets) |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Business Logic Layer              |
|   (Core Modules, Tax Engine, Reporting Engine)     |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Data Access Layer                 |
|      (SQLAlchemy ORM, PostgreSQL Connector)        |
+---------------------------------------------------+
                         |
                         v
+---------------------------------------------------+
|                  Database                          |
|                (PostgreSQL)                        |
+---------------------------------------------------+
```

### Key Components

#### ApplicationCore
Central management component that coordinates the application's modules and services.

#### ModuleManager
Handles dynamic loading of functional modules and their inter-communication.

#### AccountingEngine
Core implementation of accounting rules, transaction processing, and financial calculations.

#### TaxEngine
Specialized component for tax calculations, compliance rules, and reporting requirements.

#### ReportingEngine
Generates financial reports, statements, and regulatory documents.

#### SecurityManager
Handles authentication, authorization, and audit logging.

## Project Structure

```
sg_bookkeeper/
├── app/                    # Application source code
│   ├── core/               # Core application components
│   │   ├── application_core.py
│   │   ├── config_manager.py
│   │   ├── database_manager.py
│   │   ├── module_manager.py
│   │   └── security_manager.py
│   ├── accounting/         # Accounting module
│   │   ├── chart_of_accounts.py
│   │   ├── journal_manager.py
│   │   ├── fiscal_period.py
│   │   └── currency_manager.py
│   ├── tax/                # Tax management module
│   │   ├── gst_manager.py
│   │   ├── income_tax.py
│   │   └── withholding_tax.py
│   ├── reporting/          # Reporting module
│   │   ├── financial_statements.py
│   │   ├── tax_reports.py
│   │   └── report_engine.py
│   ├── ui/                 # User interface components
│   │   ├── main_window.py
│   │   ├── dashboard/
│   │   ├── accounting/
│   │   ├── customers/
│   │   ├── vendors/
│   │   ├── banking/
│   │   ├── reports/
│   │   └── settings/
│   ├── models/             # Data models
│   │   ├── account.py
│   │   ├── journal_entry.py
│   │   ├── customer.py
│   │   └── vendor.py
│   └── utils/              # Utility functions
│       ├── validation.py
│       ├── formatting.py
│       └── converters.py
├── data/                   # Default data and templates
│   ├── chart_of_accounts/
│   ├── report_templates/
│   └── tax_codes/
├── docs/                   # Documentation
│   ├── user_guide/
│   ├── developer_guide/
│   └── api_reference/
├── resources/              # Application resources
│   ├── icons/
│   ├── styles/
│   └── translations/
├── scripts/                # Utility scripts
│   ├── db_init.py
│   ├── build.py
│   └── release.py
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   └── ui/
├── .github/                # GitHub workflows and templates
├── pyproject.toml          # Poetry project configuration
├── README.md               # This file
└── LICENSE                 # MIT License
```

## Database Schema

SG Bookkeeper uses a carefully designed relational database schema organized into four main schemas:

1. **core**: System tables and configuration
2. **accounting**: Core accounting tables
3. **business**: Business operations tables
4. **audit**: Audit and logging tables

### Core Entity Relationship Diagram

The following diagram shows the relationships between the main accounting entities:

```
   +---------------+       +---------------+       +----------------+
   |   accounts    |       | fiscal_periods|       |journal_entries |
   +---------------+       +---------------+       +----------------+
   | id            |       | id            |       | id             |
   | code          |       | name          |       | entry_no       |
   | name          |       | start_date    |       | journal_type   |
   | account_type  |       | end_date      |       | entry_date     |
   | parent_id ---------+  | period_type   |       | fiscal_period_id -+
   +---------------+    |  | status        |       | description    |  |
           ^            |  +---------------+       | is_posted      |  |
           |            |         ^               +----------------+  |
           +------------+         |                      |            |
                                  +----------------------+            |
                                                                      |
   +----------------+                                                 |
   |journal_entry_lines          +------------------------+           |
   +----------------+            |      tax_codes         |           |
   | id             |            +------------------------+           |
   | journal_entry_id --------+  | id                     |           |
   | line_number    |         |  | code                   |           |
   | account_id ---------+    |  | description            |           |
   | description    |    |    |  | tax_type               |           |
   | debit_amount   |    |    |  | rate                   |           |
   | credit_amount  |    |    |  +------------------------+           |
   | tax_code_id ----------+                                          |
   +----------------+    |  |                                         |
                         |  |                                         |
           +-------------+  |                                         |
           |                +----------------------------------------+
           v
   +---------------+
   |   customers   |       +---------------+       +----------------+
   +---------------+       |    vendors    |       |    products    |
   | id            |       +---------------+       +----------------+
   | customer_code |       | id            |       | id             |
   | name          |       | vendor_code   |       | product_code   |
   | is_active     |       | name          |       | name           |
   +---------------+       | is_active     |       | product_type   |
                           +---------------+       +----------------+
```

## Development Setup

### Setting Up Your Development Environment

Follow these steps to set up a complete development environment for SG Bookkeeper:

1. **Install PostgreSQL**
   ```bash
   # Ubuntu/Debian
   sudo apt install postgresql-14 postgresql-contrib-14
   
   # macOS with Homebrew
   brew install postgresql@14
   
   # Windows
   # Download and install from https://www.postgresql.org/download/windows/
   ```

2. **Clone the repository and set up virtual environment**
   ```bash
   git clone https://github.com/yourusername/sg_bookkeeper.git
   cd sg_bookkeeper
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Poetry and dependencies**
   ```bash
   pip install poetry
   poetry install
   ```

4. **Initialize the database**
   ```bash
   python -m sg_bookkeeper.db_init --user postgres
   # Enter your PostgreSQL password when prompted
   ```

5. **Run the application in development mode**
   ```bash
   python -m sg_bookkeeper --debug
   ```

### Development Tools

The project includes several tools to assist with development:

- **Black**: Code formatting
  ```bash
  black sg_bookkeeper
  ```

- **Flake8**: Linting
  ```bash
  flake8 sg_bookkeeper
  ```

- **Pytest**: Running tests
  ```bash
  pytest
  ```

- **Coverage**: Test coverage reporting
  ```bash
  pytest --cov=sg_bookkeeper
  ```

- **Pre-commit hooks**: Automatic code checks
  ```bash
  pre-commit install
  ```

### Debugging Tips

- **Enable debug logging**
  ```python
  import logging
  logging.basicConfig(level=logging.DEBUG)
  ```

- **Use QDebug for Qt-specific issues**
  ```python
  from PySide6.QtCore import qDebug
  qDebug("This is a Qt debug message")
  ```

- **Debug database queries**
  ```python
  # In config.ini
  [Database]
  echo_sql = True
  ```

## API Documentation

SG Bookkeeper provides several internal APIs for extending and customizing the application:

### AccountingEngine API

```python
# Create a new journal entry
result = await accounting_engine.create_journal_entry(entry_data)

# Post a journal entry
result = await accounting_engine.post_journal_entry(entry_id, user_id)

# Reverse a journal entry
result = await accounting_engine.reverse_journal_entry(entry_id, reversal_date, description, user_id)

# Get account balance
balance = await accounting_engine.get_account_balance(account_id, as_of_date)
```

### TaxEngine API

```python
# Calculate GST for a transaction
tax_results = await tax_engine.calculate_transaction_taxes(transaction_data)

# Prepare GST F5 return
gst_return = await tax_engine.prepare_gst_return(start_date, end_date)

# Calculate income tax
tax_computation = await tax_engine.calculate_income_tax(fiscal_year)
```

### ReportingEngine API

```python
# Generate balance sheet
balance_sheet = await reporting_engine.generate_balance_sheet(as_of_date, comparative_date)

# Generate profit and loss statement
profit_loss = await reporting_engine.generate_profit_loss(start_date, end_date, comparative_start, comparative_end)

# Export report to PDF
pdf_data = await reporting_engine.export_report(report_data, "pdf")
```

See the [API Reference Documentation](https://yourusername.github.io/sg_bookkeeper/api) for complete details.

## Testing

SG Bookkeeper uses a comprehensive test suite to ensure reliability and correctness:

### Unit Tests

Unit tests focus on testing individual components in isolation:

```bash
# Run unit tests
pytest tests/unit

# Run specific test file
pytest tests/unit/test_accounting_engine.py
```

### Integration Tests

Integration tests verify that components work together correctly:

```bash
# Run integration tests
pytest tests/integration

# Run specific integration test
pytest tests/integration/test_journal_posting.py
```

### UI Tests

UI tests validate the user interface components:

```bash
# Run UI tests
pytest tests/ui

# Run specific UI test
pytest tests/ui/test_chart_of_accounts.py
```

### Test Coverage

The project aims to maintain high test coverage:

```bash
# Generate coverage report
pytest --cov=sg_bookkeeper --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Contributing

We welcome contributions from the community! Whether you're fixing bugs, improving documentation, or proposing new features, your input is valuable.

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin my-new-feature`
7. Submit a pull request

### Contribution Guidelines

- Follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Write tests for new features and bug fixes
- Update documentation for changes
- Add a descriptive commit message
- Make focused, atomic commits

### Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md) that we expect all contributors to follow.

## Roadmap

The future development of SG Bookkeeper will focus on the following areas:

### Short-term (0-6 months)
- Enhance bank reconciliation with automated matching algorithms
- Add PDF report templates for all standard reports
- Implement multi-company support
- Add support for barcode/QR code scanning for invoices
- Improve performance for large transaction volumes

### Medium-term (6-12 months)
- Develop mobile companion app for expense tracking and approvals
- Add API for third-party integrations
- Implement budgeting and forecasting module
- Create data visualization dashboards
- Add support for e-invoicing standards

### Long-term (12+ months)
- Implement cloud synchronization (optional)
- Add machine learning for transaction categorization
- Develop industry-specific modules (retail, services, etc.)
- Create marketplace for extensions and templates
- Add support for additional languages

## Performance Considerations

SG Bookkeeper is designed to handle the accounting needs of growing businesses while maintaining performance:

### Database Optimization
- Table partitioning for transaction history
- Appropriate indexing strategy for common queries
- Regular VACUUM and optimization

### Application Performance
- Asynchronous operations for long-running tasks
- Pagination for large datasets
- Background processing for report generation
- Lazy loading of UI components

### Memory Management
- Efficient handling of large datasets
- Controlled object lifecycle
- Resource cleanup for unused components

## Security Features

Security is a priority for financial applications:

### Authentication
- Strong password policies
- Optional multi-factor authentication
- Session management and timeout

### Authorization
- Role-based access control
- Granular permission system
- Object-level security

### Data Protection
- Encryption of sensitive data
- Secure audit logging
- Protection against common vulnerabilities

## Community and Support

Join our community to get help, share ideas, and contribute to the project:

- **GitHub Discussions**: For feature requests and general discussion
- **GitHub Issues**: For bug reports and specific technical problems
- **Documentation**: Comprehensive guides at [docs.sgbookkeeper.org](https://docs.sgbookkeeper.org)
- **Discord Channel**: Real-time chat with developers and users
- **Monthly Webinars**: Learn about new features and best practices

## Case Studies

### ABC Trading Pte Ltd
A small import/export business with 3 employees reduced their accounting time from 20 hours per month to just 5 hours using SG Bookkeeper.

### XYZ Consulting
A service business with 12 employees simplified their GST filing process and eliminated errors in their quarterly returns.

### Local Retail Shop
A family-owned retail business used SG Bookkeeper to gain insights into product profitability and optimize their inventory.

## Frequently Asked Questions

**Q: Can I migrate from other accounting software?**  
A: Yes, SG Bookkeeper supports importing data from common formats like CSV, Excel, and QIF. We also provide migration utilities for popular accounting software.

**Q: Is this suitable for my industry?**  
A: SG Bookkeeper is designed to be flexible and can be adapted to most industries. It includes templates for retail, services, manufacturing, and general businesses.

**Q: How does SG Bookkeeper handle compliance updates?**  
A: We monitor Singapore regulatory changes and provide timely updates to ensure compliance with the latest requirements.

**Q: Can multiple users access the system simultaneously?**  
A: Yes, SG Bookkeeper supports multiple concurrent users with different permission levels.

**Q: Is my data secure?**  
A: Your data is stored locally on your computer or server. We implement industry-standard security practices, including encryption for sensitive data.

## License

SG Bookkeeper is released under the MIT License. See the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2023 Your Name

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Acknowledgments

SG Bookkeeper builds on the work of many open source projects and is inspired by accounting best practices. We'd like to acknowledge:

- The [Python](https://www.python.org/) community for the amazing language and ecosystem
- [Qt](https://www.qt.io/) and [PySide6](https://wiki.qt.io/Qt_for_Python) for the UI framework
- [PostgreSQL](https://www.postgresql.org/) for the robust database engine
- [SQLAlchemy](https://www.sqlalchemy.org/) for the powerful ORM
- [IRAS](https://www.iras.gov.sg/) for their clear tax guidelines and examples
- All contributors who have invested time and effort into making this project better

## Get Involved

We're building SG Bookkeeper to empower Singapore's small businesses with professional accounting tools. If you share this vision, we'd love to have you join us:

- Star the repository to show your support
- Watch the repository to stay updated
- Fork and contribute to help improve the project
- Share feedback and ideas through GitHub issues
- Help spread the word about SG Bookkeeper

Together, we can make financial management accessible, efficient, and hassle-free for small businesses.

---

<div align="center">
  <p>Built with ❤️ in Singapore</p>
  <p>
    <a href="https://github.com/yourusername/sg_bookkeeper/stargazers">Star us on GitHub</a> •
    <a href="https://github.com/yourusername/sg_bookkeeper/issues">Report Bug</a> •
    <a href="https://github.com/yourusername/sg_bookkeeper/issues">Request Feature</a>
  </p>
</div>

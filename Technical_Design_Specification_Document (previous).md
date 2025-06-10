# Technical Design Specification Document: SG Bookkeeper (v17)

**Version:** 17.0
**Date:** 2025-06-11

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version **17.0**, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version **1.0.7**.

This version specifically details major new features and enhancements:
*   **Multi-Currency Accounting**: Full implementation of foreign currency transaction handling, including the calculation and automated posting of realized foreign exchange gains and losses at the time of payment.
*   **Withholding Tax (WHT) Management**: A complete workflow for applying WHT on vendor payments, including automated liability tracking through the journal.
*   **Cash Flow Statement Reporting**: A new, comprehensive Statement of Cash Flows generated using the indirect method, supported by a new account-tagging system.

These features build upon the previously implemented multi-company architecture, advanced bank reconciliation module, and interactive KPI dashboard.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   **System Architecture**: The layered architecture and its support for advanced accounting workflows like multi-currency and WHT.
-   **Database Schema**: Details and organization as defined in `scripts/schema.sql` (v1.0.7), including the new `cash_flow_category` field in the `accounts` table and new system accounts.
-   **Key UI Implementation Patterns**: Changes to the `PaymentDialog` and `AccountDialog` to support the new features.
-   **Core Business Logic**: Detailed explanation of the logic within `PaymentManager` for handling Forex and WHT, and the new `FinancialStatementGenerator` logic for the Cash Flow Statement.
-   **Data Models & DTOs**: Structure and purpose of updated ORM models and Pydantic DTOs.
-   **Security Implementation**: Authentication, Role-Based Access Control (RBAC), and audit mechanisms.

### 1.3 Intended Audience
-   **Software Developers**: For implementation, feature development, and understanding system design.
-   **QA Engineers**: For comprehending system behavior, designing effective test cases, and validation.
-   **System Administrators**: For deployment strategies, database setup, and maintenance.
-   **Technical Project Managers**: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its GUI and PostgreSQL for robust data storage. Its multi-company architecture allows users to manage multiple businesses, each with its data securely isolated in a dedicated database.

The application provides a full double-entry accounting core, Singapore-specific GST and Withholding Tax management, and a suite of interactive financial reports, including a Statement of Cash Flows. Core business operations (Customers, Vendors, Invoicing, Payments) are fully supported with multi-currency capabilities, including the automatic calculation of realized foreign exchange gains and losses. The application's focus on user experience is evident in its interactive dashboard with graphical KPIs and its advanced bank reconciliation module with draft persistence and visual matching aids.

### 1.5 Current Implementation Status
As of version 17.0 (reflecting schema v1.0.7):
*   **Multi-Currency Support**: Fully implemented. The system now correctly calculates and posts realized foreign exchange gains or losses when foreign currency invoices are settled on a date with a different exchange rate.
*   **Withholding Tax Management**: Fully implemented. The `PaymentDialog` now supports the application of WHT for applicable vendors, automatically creating the correct JE to debit A/P and credit both the bank and the WHT Payable liability account.
*   **Cash Flow Statement**: Implemented. A new report generates a Statement of Cash Flows using the indirect method. The `AccountDialog` now allows users to tag accounts with a cash flow category (`Operating`, `Investing`, `Financing`) to ensure accurate reporting.
*   **Database**: Schema updated to v1.0.7 to support the Cash Flow Statement (`cash_flow_category` column) and the new system accounts for Forex and WHT.
*   All previously documented features (multi-company, bank reconciliation, dashboard, etc.) are stable and integrated with these new capabilities.

## 2. System Architecture

### 2.1 High-Level Architecture
The application maintains its robust layered architecture, now enhanced to support more complex financial transactions.

```mermaid
graph TD
    subgraph UI Layer
        A[Presentation (app/ui)]
    end
    
    subgraph Logic Layer
        B[Business Logic (Managers)]
    end

    subgraph Data Layer
        C[Services / DAL (app/services)]
        E[Database (PostgreSQL)]
    end

    subgraph Core
        F[Application Core (app/core)]
        D[Database Manager (app/core)]
        G[Utilities & Common (app/utils, app/common)]
    end

    A -->|User Actions & DTOs| B;
    B -->|Service Calls| C;
    C -->|SQLAlchemy & asyncpg| D;
    D <--> E;

    B -->|Accesses shared services via| F;
    A -->|Schedules tasks via| F;
    C -->|Uses DB sessions from| F;
    B -->|Uses| G;
    A -->|Uses| G;
    
    style A fill:#cde4ff,stroke:#333,stroke-width:2px
    style B fill:#d5e8d4,stroke:#333,stroke-width:2px
    style C fill:#ffe6cc,stroke:#333,stroke-width:2px
    style D fill:#f8cecc,stroke:#333,stroke-width:2px
    style E fill:#dae8fc,stroke:#333,stroke-width:2px
    style F fill:#e1d5e7,stroke:#333,stroke-width:2px
    style G fill:#fff2cc,stroke:#333,stroke-width:2px
```

### 2.2 Component Architecture (Updates for New Features)

#### 2.2.1 Core Components (`app/core/`)
*   No significant changes to the core components. They continue to provide the foundational services (DB connections, configuration, security) that the new features rely upon.

#### 2.2.2 Services (Data Access Layer - `app/services/`)
*   **`AccountService`**: A new method, `get_accounts_by_tax_treatment`, was added to fetch accounts tagged for specific purposes (e.g., 'Non-Deductible'), which is used by the Income Tax Computation report.
*   Other services remain largely unchanged, as the new logic is primarily orchestrated at the manager level.

#### 2.2.3 Managers (Business Logic Layer)
*   **`PaymentManager` (`app/business_logic/payment_manager.py`)**: This manager has undergone the most significant refactoring. Its `create_payment` method is now a sophisticated transaction processor that correctly handles:
    1.  Standard (base currency) payments.
    2.  Foreign currency payments, calculating and posting realized forex gain/loss.
    3.  Vendor payments with withholding tax deductions.
    4.  A combination of foreign currency and withholding tax on the same payment.
    The journal entry creation logic within this manager is now highly complex to ensure all these scenarios result in a balanced, compliant JE.
*   **`FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)**:
    *   A new method, `generate_cash_flow_statement`, has been implemented. It uses the indirect method, starting with net income and making adjustments based on the new `cash_flow_category` tag on accounts.
    *   The `generate_income_tax_computation` method has been fleshed out from a stub to a functional implementation.
*   **`WithholdingTaxManager` (`app/tax/withholding_tax_manager.py`)**: The stub has been updated with a foundational implementation for `generate_s45_form_data`, demonstrating how data from a payment transaction can be mapped to a tax form structure.

#### 2.2.4 User Interface (Presentation Layer - `app/ui/`)
*   **`AccountDialog` (`app/ui/accounting/account_dialog.py`)**: A `QComboBox` for "Cash Flow Category" has been added, allowing users to tag accounts as Operating, Investing, or Financing.
*   **`PaymentDialog` (`app/ui/payments/payment_dialog.py`)**:
    *   A new "Withholding Tax" section with a checkbox (`self.apply_wht_check`) and display labels dynamically appears for applicable vendor payments.
    *   The dialog's internal logic updates the display to show the calculated WHT amount and net payment when the feature is enabled.
*   **`ReportsWidget` (`app/ui/reports/reports_widget.py`)**:
    *   The "Report Type" dropdown now includes "Cash Flow Statement" and "Income Tax Computation".
    *   The UI dynamically adjusts the available parameter fields based on the selected report.
    *   New `QTreeView` displays have been added to the internal `QStackedWidget` to render these new hierarchical reports.

## 3. Data Architecture

### 3.1. Database Schema (v1.0.7)
*   The master schema is now at version **1.0.7**.
*   **`accounting.accounts` table**: A new nullable column, `cash_flow_category VARCHAR(20)`, has been added. It has a `CHECK` constraint to only allow the values 'Operating', 'Investing', or 'Financing'. This is the key change enabling the automated Cash Flow Statement.
*   **`core.configuration` table**: Three new keys have been added to `initial_data.sql` to support the new features: `SysAcc_WHTPayable`, `SysAcc_ForexGain`, and `SysAcc_ForexLoss`.
*   **`accounting.accounts` initial data**: New default accounts have been added to `initial_data.sql`: `2130 - Withholding Tax Payable`, `7200 - Foreign Exchange Gain`, and `8200 - Foreign Exchange Loss`.

### 3.2. Data Models & DTOs
*   **`Account` ORM Model (`app/models/accounting/account.py`)**: Updated to include the `cash_flow_category: Mapped[Optional[str]]` attribute.
*   **`AccountCreateData` / `AccountUpdateData` DTOs**: Updated to include the optional `cash_flow_category` field.
*   **`PaymentCreateData` DTO**: Updated with `apply_withholding_tax: bool` and `withholding_tax_amount: Optional[Decimal]` to carry WHT information from the UI to the `PaymentManager`.

## 4. Detailed Feature Implementation

### 4.1. Multi-Currency Workflow
1.  **Invoice Posting**: A foreign currency (FC) invoice (e.g., for 1,000 USD) is created. At the invoice date exchange rate (e.g., 1.35), the system posts a JE debiting AR for 1,350 SGD and crediting Revenue for 1,350 SGD. The AR sub-ledger tracks both the 1,000 USD and the 1,350 SGD amounts.
2.  **Payment Receipt**: The customer pays 1,000 USD. The payment is received on a later date when the exchange rate is 1.32. The actual cash received in the bank (after conversion) is 1,320 SGD.
3.  **Forex Calculation (`PaymentManager`)**:
    *   The manager sees a payment of 1,000 USD applied to an invoice of 1,000 USD.
    *   It calculates the value of the payment in base currency: `1000 USD * 1.32 = 1320 SGD`.
    *   It looks up the original invoice and sees it was booked to AR at 1,350 SGD.
    *   It calculates the difference: `1350 SGD (original AR) - 1320 SGD (cash received) = 30 SGD`.
    *   Since less base currency was received than expected for an asset, this is a **Realized Foreign Exchange Loss**.
4.  **Journal Entry (`PaymentManager`)**: A single, balanced JE is created:
    *   `Dr Bank Account: 1320 SGD`
    *   `Dr Foreign Exchange Loss: 30 SGD`
    *   `Cr Accounts Receivable: 1350 SGD`
5.  This process correctly clears the AR in the base currency and recognizes the forex loss in the P&L. The logic is reversed for vendor payments.

### 4.2. Withholding Tax Workflow
1.  **Setup**: A vendor is marked as `withholding_tax_applicable` with a rate of 15% in `VendorDialog`. A `WHT Payable` liability account (`2130`) exists.
2.  **Payment Creation (`PaymentDialog`)**: A user creates a payment for a $1,000 invoice from this vendor.
    *   The `PaymentDialog` detects the vendor is WHT-applicable and displays the "Apply Withholding Tax" checkbox.
    *   The user checks the box. The UI displays "WHT Rate: 15.00%" and "WHT Amount: 150.00".
    *   The net amount paid to the vendor is implied to be $850.
3.  **Manager Logic (`PaymentManager`)**: The `PaymentCreateData` DTO received by the manager includes `apply_withholding_tax=True`.
    *   The manager calculates the WHT amount: `1000 * 15% = 150`.
    *   It calculates the net cash paid: `1000 - 150 = 850`.
    *   It creates the following balanced JE:
        *   `Dr Accounts Payable: 1000.00` (Clears the full invoice liability)
        *   `Cr Bank Account: 850.00` (Reflects actual cash outflow)
        *   `Cr WHT Payable: 150.00` (Recognizes the liability to the tax authority)
4.  **Reporting**: The `WHT Payable` account balance will appear on the Balance Sheet until it is cleared by a separate payment to IRAS. The `WithholdingTaxManager` can be used to generate supporting documentation.

### 4.3. Cash Flow Statement Generation
1.  **User Setup (`AccountDialog`)**: The user (or an initial setup script) must tag relevant balance sheet accounts with a `cash_flow_category`. For example:
    *   Accounts Receivable -> `Operating`
    *   Inventory -> `Operating`
    *   Property, Plant & Equipment -> `Investing`
    *   Bank Loans -> `Financing`
    *   Share Capital -> `Financing`
2.  **Report Generation (`FinancialStatementGenerator`)**:
    *   **Start with Net Income**: Fetches the net profit for the period from the P&L.
    *   **Adjust for Non-Cash Items**: Identifies depreciation accounts (by `sub_type` convention) and adds back the depreciation expense for the period (calculated as the change in the accumulated depreciation account balance).
    *   **Adjust for Working Capital**: For each account tagged as `Operating`, it calculates the change in its balance between the start and end dates.
        *   An *increase* in an operating asset (like AR) is a *use* of cash, so it's **subtracted**.
        *   An *increase* in an operating liability (like AP) is a *source* of cash, so it's **added**.
    *   **Calculate CFI & CFF**: It calculates the change in balance for all accounts tagged as `Investing` or `Financing` and lists these changes directly in their respective sections.
    *   **Reconcile**: The net increase/decrease in cash is calculated. This is reconciled against the actual change in the cash and bank account balances over the period to ensure accuracy.

## 5. Conclusion
Version 17.0 represents a significant leap in functionality, moving SG Bookkeeper from a solid foundational tool to a more mature accounting application capable of handling complex, real-world business scenarios. The introduction of robust multi-currency accounting, integrated WHT management, and a compliant Cash Flow Statement drastically increases the application's value proposition for its target audience. The architectural enhancements, particularly the account tagging system and the complex logic encapsulated within the `PaymentManager`, have been implemented in a maintainable way that builds upon the existing layered design.

---
https://drive.google.com/file/d/13a54HCe719DE9LvoTL2G3fufXVAZ68s9/view?usp=sharing, https://drive.google.com/file/d/16sEyvS8ZfOJFIHl3N-L34xQnhEo5XPcI/view?usp=sharing, https://drive.google.com/file/d/17Lx6TxeEQJauqxEwWQIjL_Vounz-OOuU/view?usp=sharing, https://drive.google.com/file/d/17M3-d4q02eUhkRMgogRQMxwSbiDkCJow/view?usp=sharing, https://drive.google.com/file/d/1MxP_SNNW86u44e2wupzz6i2gb0ibGeUE/view?usp=sharing, https://drive.google.com/file/d/1QsDwk2m_1Nh4JHOshQw4zjEI3x1mgGkM/view?usp=sharing, https://drive.google.com/file/d/1RkrdC_e7A_-nbzKVAiL_fX48uib6mu1T/view?usp=sharing, https://drive.google.com/file/d/1Wvi2CiVPY0EL2kErW2muu_LbMy4J_sRF/view?usp=sharing, https://drive.google.com/file/d/1XPEV3rOOikcWVvhB7GwX0raI__osRg-Z/view?usp=sharing, https://drive.google.com/file/d/1Z0gGlgu698IMIFg56GxD60l4xKNg1fIt/view?usp=sharing, https://drive.google.com/file/d/1cJjbc9s6IGkKHeAhk-dh7ey9i7ArJMJe/view?usp=sharing, https://drive.google.com/file/d/1jNlP9TOSJtMzQMeLH1RoqmU2Hx7iwQkJ/view?usp=sharing, https://drive.google.com/file/d/1q3W6Cs4WVx7dLwL1XGN9aQ6bb-hyHmWS/view?usp=sharing, https://drive.google.com/file/d/1qYszGazA6Zm1-3YGdaKdDlPEr3HipU5k/view?usp=sharing, https://drive.google.com/file/d/1uYEc0AZDEBE2A4qrR5O1OFcFVHJsCtds/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221v7mZ4CEkZueuPt-aoH1XmYRmOooNELC3%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing


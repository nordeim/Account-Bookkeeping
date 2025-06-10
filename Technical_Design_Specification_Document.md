# Technical Design Specification Document: SG Bookkeeper (v17)

**Version:** 17.0
**Date:** 2025-06-11

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version **17.0**, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version **1.0.7**.

This version specifically details major new features and enhancements:
*   **Full Multi-Currency Support**: Implementation of foreign exchange gain/loss calculations on payments.
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
-   **Security & Data Isolation**: How the application ensures data separation between companies.

### 1.3 Intended Audience
-   **Software Developers**: For implementation, feature development, and understanding system design.
-   **QA Engineers**: For comprehending system behavior, designing effective test cases, and validation.
-   **System Administrators**: For deployment strategies, database setup, and maintenance.
-   **Technical Project Managers**: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its GUI and PostgreSQL for robust data storage. Its architecture supports a **multi-company environment**, where each company's data is securely isolated in its own dedicated PostgreSQL database.

Its core functionality includes a full double-entry bookkeeping system, Singapore-specific GST and Withholding Tax management, and a suite of interactive financial reports, including a Statement of Cash Flows. Core business operations are fully supported with multi-currency capabilities, including the automatic calculation of realized foreign exchange gains and losses. The application's focus on user experience is evident in its interactive dashboard with graphical KPIs and its advanced bank reconciliation module with draft persistence and visual matching aids.

### 1.5 Current Implementation Status
As of version 17.0 (reflecting schema v1.0.7):
*   **Multi-Currency Support**: Fully implemented. The system now correctly calculates and posts realized foreign exchange gains or losses when foreign currency invoices are settled.
*   **Withholding Tax Management**: Fully implemented. The `PaymentDialog` supports the application of WHT for applicable vendors, automatically creating the correct JE to record the liability.
*   **Cash Flow Statement**: Implemented. A new report generates a Statement of Cash Flows using the indirect method, based on a new account tagging system.
*   **Multi-Company Architecture**: Fully functional, allowing creation and switching between company databases.
*   **Bank Reconciliation Module**: Fully functional with draft persistence, visual grouping of matched items, and history viewing.
*   **Dashboard KPIs**: Fully functional with an "As of Date" selector, graphical aging charts, and key financial ratios.
*   **Database**: Schema is at v1.0.7, supporting all current features.

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
```

### 2.2 Component Architecture (Updates for New Features)

#### 2.2.1 Core Components (`app/core/`)
*   No significant changes to the core components. They continue to provide the foundational services (DB connections, configuration, security) that the new features rely upon.

#### 2.2.2 Services (Data Access Layer - `app/services/`)
*   **`AccountService` (`account_service.py`)**: A new method, `get_accounts_by_tax_treatment`, was added to fetch accounts tagged for specific purposes (e.g., 'Non-Deductible'), which is used by the Income Tax Computation report.
*   Other services remain largely unchanged, as the new logic is primarily orchestrated at the manager level.

#### 2.2.3 Managers (Business Logic Layer)
*   **`PaymentManager` (`app/business_logic/payment_manager.py`)**: This manager has undergone the most significant refactoring. Its `create_payment` method is now a sophisticated transaction processor that correctly handles:
    1.  Standard (base currency) payments.
    2.  Foreign currency payments, calculating and posting realized forex gain/loss.
    3.  Vendor payments with withholding tax deductions.
    4.  A combination of foreign currency and withholding tax on the same payment.
    The journal entry creation logic within this manager is now highly complex to ensure all these scenarios result in a balanced, compliant JE.
*   **`FinancialStatementGenerator` (`app/reporting/financial_statement_generator.py`)**:
    *   A new public method, `generate_cash_flow_statement`, has been implemented. It uses the indirect method, starting with net income and making adjustments based on the new `cash_flow_category` tag on accounts.
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

### 3.1. Company Registry & Database Isolation
*   A central `companies.json` file, managed by `CompanyManager`, stores the list of available company databases.
*   Each company operates in a completely separate PostgreSQL database, created from the same master `schema.sql` file, ensuring total data segregation.

### 3.2. Database Schema (v1.0.7)
*   **`accounting.accounts` table**: The schema has been updated to include a `cash_flow_category VARCHAR(20)` column. This nullable field has a `CHECK` constraint to allow only 'Operating', 'Investing', or 'Financing', and is the cornerstone of the automated Cash Flow Statement generation.
*   **Initial Data**: `scripts/initial_data.sql` has been updated to include new system accounts for WHT Payable (`2130`), Foreign Exchange Gain (`7200`), and Foreign Exchange Loss (`8200`), along with their corresponding entries in the `core.configuration` table.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **`AccountCreateData` / `AccountUpdateData`**: These DTOs now include the optional `cash_flow_category: Optional[str]` field.
*   **`PaymentCreateData`**: This DTO is now extended with `apply_withholding_tax: bool` and `withholding_tax_amount: Optional[Decimal]` to transport WHT information from the UI to the business logic layer.
*   All other DTOs remain stable, with their usage patterns consistent with previous versions.

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
    *   **Adjust for Working Capital**: For each account tagged as `Operating`, it calculates the change in its balance between the start and end dates. An increase in an operating asset (like AR) is a *use* of cash (subtracted), while an increase in an operating liability (like AP) is a *source* of cash (added).
    *   **Calculate CFI & CFF**: It calculates the change in balance for all accounts tagged as `Investing` or `Financing` and lists these changes directly in their respective sections.
    *   **Reconcile**: The net increase/decrease in cash is calculated. This is reconciled against the actual change in the cash and bank account balances over the period to ensure accuracy.

## 5. Conclusion
Version 17.0 of SG Bookkeeper introduces significant enhancements to its accounting capabilities, moving it closer to a professional-grade financial management tool. The implementation of full multi-currency transaction handling, integrated withholding tax management, and an automated Statement of Cash Flows provides immense value for businesses operating in a global and regulated environment like Singapore. These features are built upon a stable, layered, and multi-company architecture, ensuring that complexity is managed effectively and the system remains robust and maintainable.

---
https://drive.google.com/file/d/13a54HCe719DE9LvoTL2G3fufXVAZ68s9/view?usp=sharing, https://drive.google.com/file/d/16sEyvS8ZfOJFIHl3N-L34xQnhEo5XPcI/view?usp=sharing, https://drive.google.com/file/d/17Lx6TxeEQJauqxEwWQIjL_Vounz-OOuU/view?usp=sharing, https://drive.google.com/file/d/17M3-d4q02eUhkRMgogRQMxwSbiDkCJow/view?usp=sharing, https://drive.google.com/file/d/1MxP_SNNW86u44e2wupzz6i2gb0ibGeUE/view?usp=sharing, https://drive.google.com/file/d/1QsDwk2m_1Nh4JHOshQw4zjEI3x1mgGkM/view?usp=sharing, https://drive.google.com/file/d/1RkrdC_e7A_-nbzKVAiL_fX48uib6mu1T/view?usp=sharing, https://drive.google.com/file/d/1Wvi2CiVPY0EL2kErW2muu_LbMy4J_sRF/view?usp=sharing, https://drive.google.com/file/d/1XPEV3rOOikcWVvhB7GwX0raI__osRg-Z/view?usp=sharing, https://drive.google.com/file/d/1Z0gGlgu698IMIFg56GxD60l4xKNg1fIt/view?usp=sharing, https://drive.google.com/file/d/1cJjbc9s6IGkKHeAhk-dh7ey9i7ArJMJe/view?usp=sharing, https://drive.google.com/file/d/1jNlP9TOSJtMzQMeLH1RoqmU2Hx7iwQkJ/view?usp=sharing, https://drive.google.com/file/d/1q3W6Cs4WVx7dLwL1XGN9aQ6bb-hyHmWS/view?usp=sharing, https://drive.google.com/file/d/1qYszGazA6Zm1-3YGdaKdDlPEr3HipU5k/view?usp=sharing, https://drive.google.com/file/d/1uYEc0AZDEBE2A4qrR5O1OFcFVHJsCtds/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221v7mZ4CEkZueuPt-aoH1XmYRmOooNELC3%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing

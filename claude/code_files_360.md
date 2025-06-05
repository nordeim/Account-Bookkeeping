<think>
The user wants me to update the `Technical_Design_Specification_Document (draft).md` (which I will refer to as TDS).
I need to:
1.  **Carefully review all attached documents**:
    *   `Technical_Design_Specification_Document (draft).md` (TDS v15) - This is the base document to be updated.
    *   `diff_output_schema.sql.md` - Contains diffs for `schema.sql` and `initial_data.sql`. This shows schema changes up to v1.0.5.
    *   `README (v13).md` - An older README.
    *   `README.md` - The latest README, reflecting current features and schema v1.0.5.
    *   `Project Architecture Document v4.md` - An older architecture document.
    *   `Project Architecture Document.md` (which I will refer to as PAD v5) - The latest architecture document.
    *   The two screenshots: `Dashboard` and `Bank Reconciliation` UI.
2.  **Identify areas for update in the TDS**:
    *   Remove repeating details (if any significant redundancy is found, especially if better covered elsewhere or too verbose).
    *   Add missing details, particularly those from the latest README.md, PAD v5, and schema diffs, to ensure the TDS is comprehensive and up-to-date.
    *   Ensure consistency with the latest feature set described in README.md and PAD v5.
    *   The TDS is currently labeled "v15" and references schema "v1.0.5". I should maintain this versioning or update if implied by other documents. The current TDS seems to *already* describe schema v1.0.5 and the related features (draft reconciliations, new KPIs). My task is to refine it, remove redundancy, and incorporate any *additional* details or clarifications from the other latest documents.

**Plan of Action:**

I will go through the TDS section by section and compare it with the information available in the other documents (README.md, PAD v5, schema diffs, screenshots).

*   **Section 1: Introduction**
    *   **1.1 Purpose**: Check if the summary of refinements (Bank Rec, Automated Bank Txn, Dashboard KPIs, DB Enhancements) is complete and accurate based on README/PAD v5. The TDS seems to cover these already.
    *   **1.2 Scope**: Ensure it aligns with the latest features and architectural layers described in PAD v5.
    *   **1.4 System Overview**: Update description to match the latest README.md, especially regarding Bank Rec (draft persistence, unmatching) and Dashboard (AR/AP aging, current ratio).
    *   **1.5 Current Implementation Status**: Verify this matches the "Recently Completed" section of README.md and the feature set described in PAD v5.

*   **Section 2: System Architecture**
    *   **2.1 High-Level Architecture**: Compare the diagram and description with PAD v5 (Section 4). They look very similar. Ensure consistency.
    *   **2.2 Component Architecture**: This is a critical section.
        *   **2.2.1 Core Components**: Compare `ApplicationCore` description with PAD v5 (Section 5.1). PAD v5 is more detailed. I might integrate some details.
        *   **2.2.3 Services**: Compare changes in `CustomerService`, `VendorService`, `AccountService`, `BankReconciliationService` with PAD v5 (Section 5.3 and specific service mentions) and the TDS's own DTO/Interface section (3.4). The current TDS seems to have these specific method additions.
        *   **2.2.4 Managers**: Compare `DashboardManager` and `BankTransactionManager` descriptions with PAD v5 (Section 5.4) and README.md. Pay attention to how AR/AP aging and Current Ratio are calculated in `DashboardManager`.
        *   **2.2.5 User Interface**: Compare `DashboardWidget` and `BankReconciliationWidget` descriptions with PAD v5 (Section 5.5), README.md usage guide, and the screenshots. The screenshots are vital here.
            *   *Dashboard Screenshot Analysis*: Shows "Key Performance Indicators" with YTD figures, Cash Balance, Current Ratio on the right. AR/AP summaries on the left with "Current (Not Overdue)", "Overdue (1-30 days)", "Overdue (31-60 days)", "Overdue (61-90 days)", "Overdue (91+ days)". The TDS describes this.
            *   *Bank Reconciliation Screenshot Analysis*: Shows "Bank Account", "Statement End Date", "Statement End Balance". "Reconciliation Summary" box. Tables: "Bank Statement Items (Unreconciled)", "System Bank Transactions (Unreconciled)", "Provisionally Matched Statement Items (This Session)", "Provisionally Matched System Transactions (This Session)". Buttons: "Match Selected", "Unmatch Selected", "Add Journal Entry", "Save Final Reconciliation". "Reconciliation History" table at the bottom with pagination. The TDS describes this.

*   **Section 3: Data Architecture**
    *   **3.1 Database Schema Overview**: Confirm schema version is 1.0.5 and `bank_reconciliations.status` field is correctly noted. The diff file confirms this.
    *   **3.2 SQLAlchemy ORM Models**: Check `BankReconciliation` model for `status` field.
    *   **3.3 Data Transfer Objects (DTOs)**: Confirm `DashboardKPIData` extension.
    *   **3.4 Data Access Layer Interfaces**: Check consistency of method signatures with what's described for services.

*   **Section 4: Module and Component Specifications**
    *   **4.1 Core Accounting**: Specifically check "Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction." This is mentioned in TDS 1.1 and README/PAD v5. Ensure `JournalEntryManager.post_journal_entry` is mentioned.
    *   **4.2 Tax Management**: Ensure GST F5 description is up-to-date (detailed export).
    *   **4.6 Dashboard Module (Enhanced)**: This section seems to already reflect the enhanced KPIs. Cross-verify with PAD v5 and README.md details (e.g., calculation method for current assets/liabilities if specified).
    *   **4.7 Banking Module (Refined Bank Reconciliation Workflow)**: This is a key area.
        *   Compare the step-by-step process with README.md usage guide and PAD v5 data flow.
        *   Ensure it accurately reflects draft persistence, provisional matching (DB updates), unmatching (DB updates), finalization (status update).
        *   The TDS has a good detailed flow. "BankReconciliationService.get_transactions_for_reconciliation" is mentioned for fetching provisionally matched items. The old TDS v15 text in "Section 9. Data Flow Examples (Updates)" for Bank Rec is also very detailed and seems good. I should check if the main Section 4.7 could be made more concise if Section 9 already covers it in great detail, or if 4.7 should be the primary detailed description. The current TDS has detail in 4.7 and then *again* in 9.2 (updated). This looks like a point for consolidation/refinement.
            *   Decision: Section 4.7 should provide a concise overview of the process and key components/services involved. Section 9.2 (Data Flow Example) should provide the step-by-step detailed interaction. I will check if TDS 4.7 is already concise enough or if it mirrors too much of 9.2. On review, TDS 4.7 *is* quite detailed. I'll try to make 4.7 a bit more high-level about the *components* and *responsibilities*, and let 9.2 be the very granular flow.

*   **Section 5: User Interface Implementation**
    *   Compare `DashboardWidget` and `BankReconciliationWidget` descriptions with the latest UI elements seen in screenshots and described in README/PAD v5. The TDS already mentions `QGroupBox`, `QFormLayout`, `QGridLayout`, `QScrollArea` for Dashboard, and `QSplitter`, new tables/buttons for Bank Rec. This seems mostly up-to-date.

*   **Section 6: Security Considerations**
    *   Compare with PAD v5 (Section 11) for completeness and accuracy. PAD v5 might have more detail on `app.current_user_id` usage with triggers. TDS already mentions this.

*   **Section 7: Database Access Implementation**
    *   Compare with PAD v5 (Section 6.4, and `DatabaseManager` in 5.1). Ensure atomicity of transactions is correctly described. The TDS mentions "BankReconciliationService.save_reconciliation_details" (this method name seems to be from an older version as per TDS 2.2.3 note: "Old `save_reconciliation_details` is removed/refactored into the new methods"). This should be `finalize_reconciliation` or the relevant new service methods. I need to correct this.
        *   Correction: The sentence "BankReconciliationService.save_reconciliation_details ensures that saving..." should be updated to reflect the new service methods like `finalize_reconciliation` that handle the atomic operations.

*   **Section 8: Deployment and Installation**
    *   Compare with README.md's installation section. Ensure DB initialization script references `schema.sql` v1.0.5.
    *   README.md has more detailed steps for `config.ini` and PostgreSQL user setup. TDS is more brief. TDS is a *technical design* spec, so it might not need full user-facing install steps. It should focus on the *technical* aspects of deployment. The current level of detail in TDS might be fine.

*   **Section 9: Data Flow Examples**
    *   **9.1 Sales Invoice Posting**: Compare with PAD v5 (Section 14.1).
    *   **9.2 Bank Reconciliation Process (Refined)**: This is the *updated* data flow in the current TDS. Compare this meticulously with PAD v5 (Section 14.2, and the Bank Reconciliation specific flow in Section 9 of TDS v15 itself - oh, the user provided TDS *is* v15, so it has the updated data flow already). This section in the current TDS draft is very detailed and seems accurate to the new workflow.
        *   I should ensure there's no major contradiction between the flow described in 4.7 and 9.2. As decided earlier, 4.7 will be component-focused overview, 9.2 will be the detailed interaction flow.
        *   The current TDS draft's 9.2 already describes the refined flow with `get_or_create_draft_reconciliation`, provisional matching, unmatching, and finalization. This looks good.

*   **Section 10: Conclusion**
    *   Ensure it reflects the latest enhancements (Bank Rec refinements, new Dashboard KPIs, circular import fixes). The current TDS draft conclusion looks appropriate for "Version 15".

**General Strategy for "Removing Repeating Details":**
The TDS is already quite dense. I'll look for:
1.  Identical or near-identical paragraphs/lists appearing in multiple sections if one is a summary and the other is detail.
2.  Overly verbose descriptions if PAD v5 or README.md covers the same point more concisely or appropriately for its document type, and the TDS can link or assume that knowledge. However, a TDS is *meant* to be detailed. I should be cautious about removing too much technical detail. The primary candidate for "repetition" identified is the detailed bank rec flow appearing in both section 4.7 and 9.2. I will trim 4.7 to be more of an overview.

**General Strategy for "Adding Missing Details":**
1.  Anything from PAD v5's architectural descriptions that provides more clarity or depth to a component/layer description in the TDS.
2.  Specifics from README.md about user-facing features or setup that have direct technical design implications not fully captured.
3.  Ensuring all service method changes or DTO changes mentioned in TDS sections 2 and 3 are consistently reflected in section 4 (module specs) or 9 (data flows).

**Key areas from PAD v5 to potentially integrate/enhance TDS:**
*   PAD v5 Section 5.1 `ApplicationCore` description (more on service locator role).
*   PAD v5 Section 5.1 `DatabaseManager` (more on `app.current_user_id` and raw `asyncpg` connection).
*   PAD v5 Section 5.1 `SecurityManager` (more on `current_user` object).
*   PAD v5 Section 5.1 Asynchronous Task Management details.
*   PAD v5 Section 5.2 ORM Models (Base classes, organization, features like `Mapped`, `mapped_column`).
*   PAD v5 Section 5.6 Utilities (`json_helpers.py`, `result.py`, `sequence_generator.py` details).
*   PAD v5 Section 5.7 Common (`enums.py`).
*   PAD v5 Section 11 Security Architecture might have more nuance than TDS Section 6.
*   PAD v5's description of the async model (Section 9) is quite good and could enhance the TDS.

**Let's start the process.**

**Reviewing TDS v15 (the input file) and comparing:**

**Section 1: Introduction**
*   1.1 Purpose: Seems fine. Schema v1.0.5 and status field are mentioned.
*   1.2 Scope: Mentions ORM models and DTOs. PAD v5 has more detail on these (SQLAlchemy 2.0 style, Pydantic DTO purposes). Could add a brief note about their specific roles.
*   1.4 System Overview:
    *   TDS: "...CSV bank statement import, **a full bank reconciliation module with draft persistence and unmatching capabilities**, an **enhanced dashboard displaying AR/AP aging and current ratio KPIs**..." This is good and matches recent changes.
    *   README.md Overview: "...Bank Reconciliation module (including draft persistence, provisional matching/unmatching, and history viewing), an enhanced Dashboard with Key Performance Indicators (KPIs like AR/AP Aging and Current Ratio)..." Very similar. No major changes needed here.
*   1.5 Current Implementation Status:
    *   TDS lists "Draft Reconciliation Persistence", "Provisional Matching", "Unmatching", "Finalization", "History Viewing" for Bank Rec. And AR/AP Aging, Current Ratio for Dashboard. Also `status` in `bank_reconciliations` and circular import fixes. This seems to align well with recent developments.

**Section 2: System Architecture**
*   2.1 High-Level Architecture: Diagram and description are consistent with PAD v5. Minor wording tweak: "Orchestrates Services. Returns `Result` objects." (TDS) vs "Orchestrates Services. Returns `Result` objects." (PAD v5 has same). It's fine.
*   2.2 Component Architecture:
    *   2.2.1 `ApplicationCore`: TDS says "Refactored to use local imports...". PAD v5 (5.1) gives a broader role: "central singleton orchestrator", "Initializes and provides access to all services and managers", "service locator/dependency injector". This broader role description can be added/merged.
    *   2.2.3 Services (`CustomerService`, `VendorService`, `AccountService`, `BankReconciliationService`): Method additions listed in TDS seem correct and align with the new features.
        *   TDS: `BankReconciliationService`: `get_or_create_draft_reconciliation`, `mark_transactions_as_provisionally_reconciled`, `finalize_reconciliation`, `unreconcile_transactions`. Old `save_reconciliation_details` removed. This is accurate.
    *   2.2.4 Managers (`DashboardManager`, `BankTransactionManager`):
        *   `DashboardManager`: TDS: "Calculate total current assets and liabilities by fetching active accounts... filtering by predefined `CURRENT_ASSET_SUBTYPES` and `CURRENT_LIABILITY_SUBTYPES`." This is good detail.
        *   `BankTransactionManager`: TDS: "`get_unreconciled_transactions_for_matching()` logic remains focused on `is_reconciled=False` items. The new UI for provisionally matched items will use a different service call." (This different service call is likely `BankReconciliationService.get_transactions_for_reconciliation` mentioned in TDS 4.7.2). This is consistent.
    *   2.2.5 UI (`DashboardWidget`, `BankReconciliationWidget`): Descriptions of UI elements (QGroupBox, QFormLayout for aging; new tables, unmatch button for bank rec) seem consistent with screenshots and latest features.

**Section 3: Data Architecture**
*   3.1 Database Schema Overview: `status VARCHAR(20) NOT NULL DEFAULT 'Draft'` with `CHECK` constraint. Correct per schema diff.
*   3.2 SQLAlchemy ORM Models: `BankReconciliation` model has `status`. Correct.
*   3.3 DTOs: `DashboardKPIData` extended fields. Correct.
*   3.4 Data Access Layer Interfaces: New methods listed are consistent with service changes in 2.2.3.

**Section 4: Module and Component Specifications**
*   4.1 Core Accounting Module:
    *   TDS: "`JournalEntryManager.post_journal_entry` now auto-creates `BankTransaction` if a bank-linked GL account is affected." This is important and correctly noted.
*   4.6 Dashboard Module (Enhanced):
    *   The description of how current assets/liabilities are calculated is good: "Fetching all active accounts from `AccountService`. Iterating and summing balances (via `JournalService`) for accounts whose `account_type` (category) and `sub_type` match predefined lists..."
*   4.7 Banking Module (Refined Bank Reconciliation Workflow):
    *   This section is very detailed. Step 2: "Fetch Unreconciled & Provisionally Matched": Mentions `BankTransactionManager.get_unreconciled_transactions_for_matching` for unreconciled and `BankReconciliationService.get_transactions_for_reconciliation` for provisionally matched. This is key.
    *   Step 3: "Provisional Matching": `BankReconciliationService.mark_transactions_as_provisionally_reconciled`. DB updates and reload.
    *   Step 4: "Unmatching": `BankReconciliationService.unreconcile_transactions`. DB updates and reload.
    *   Step 6: "Finalizing": `BankReconciliationService.finalize_reconciliation`. Updates status to "Finalized", updates balances.
    *   This seems accurate. I will make this section slightly more high-level, focusing on *what* happens and *which components* are involved, then ensure Section 9.2 (Data Flow) has the exhaustive step-by-step user and system actions.
    *   *Refinement for 4.7*: I'll rephrase it to be an overview of the *module's* capabilities and key service interactions rather than a full step-by-step user flow, as that's better placed in Section 9.

**Section 5: User Interface Implementation**
*   Seems accurate and consistent with screenshots. `QScrollArea` for Dashboard is a good detail. `QSplitter` for bank rec tables.

**Section 6: Security Considerations**
*   TDS mentions `DatabaseManager` setting `app.current_user_id`. PAD v5 (Section 11) also emphasizes this for audit triggers. Consistent.

**Section 7: Database Access Implementation**
*   TDS: "Transactions: ... `BankReconciliationService.save_reconciliation_details` ensures that saving the `BankReconciliation` record, updating multiple `BankTransaction` records, and updating the `BankAccount` record occurs within a single atomic database transaction."
    *   As noted earlier, `save_reconciliation_details` is old. This should refer to `finalize_reconciliation` (which updates the main `BankReconciliation` record and `BankAccount`) and also imply that `mark_transactions_as_provisionally_reconciled` and `unreconcile_transactions` are also atomic for their respective operations on `BankTransaction` records.
    *   I will rephrase this to: "Multi-step database operations (e.g., invoice posting, payment recording, provisional matching/unmatching of bank transactions, and finalization of bank reconciliations) are handled within a single database session (`async with db_manager.session():`) managed by manager or service methods to ensure atomicity. For example, `BankReconciliationService.finalize_reconciliation` ensures that updating the `BankReconciliation` record to 'Finalized', its balances, and the linked `BankAccount`'s last reconciled information occurs atomically. Similarly, methods for provisional matching and unmatching ensure atomicity for their respective `BankTransaction` updates."

**Section 8: Deployment and Installation**
*   TDS mentions "executes `scripts/schema.sql` (DDL, v1.0.4)". Schema diff shows current is v1.0.5. **This needs correction.** The header of schema diff states "SG Bookkeeper - Complete Database Schema - Version 1.0.5".
*   And "initial_data.sql (seeding, updated for new permissions/configs)". The initial_data.sql diff shows it's also aligned with 1.0.5.
    *   Correction for 8. Setup: "Initialize database: ... This executes `scripts/schema.sql` (DDL, **v1.0.5**) and `scripts/initial_data.sql`..."

**Section 9: Data Flow Examples**
*   9.1 Sales Invoice Posting: Seems fine.
*   9.2 Data Flow Example: Bank Reconciliation Process (Refined): This is very detailed and accurate for the new workflow.
    *   Step 2: "Get/Create Draft & Fetch Data": Mentions `get_or_create_draft_reconciliation`, `get_unreconciled_transactions_for_matching`, `get_transactions_for_reconciliation`. Correct.
    *   Step 4: Provisional Matching: `mark_transactions_as_provisionally_reconciled`. Correct.
    *   Step 5: Unmatching: `unreconcile_transactions`. Correct.
    *   Step 7: Finalizing: `finalize_reconciliation`. Correct.
    *   This detailed flow in 9.2 is excellent and should be preserved. This means I will definitely trim 4.7.

**Section 10: Conclusion**
*   "Version 15 of SG Bookkeeper significantly refines the Bank Reconciliation module... Dashboard has been enhanced... Circular import resolution..." This is all accurate for the current state.

**Integrating details from PAD v5:**

*   **General Architectural Patterns/Concepts**: PAD v5 lists more architectural patterns (MVC/MVP, Observer, DI, Singleton, Mixins) and has dedicated sections for Asynchronous Processing Model, Configuration Management. The TDS touches upon some of these implicitly. I could add a small subsection in TDS Section 2 for "Key Architectural Patterns" or "Architectural Principles" and summarize these briefly, or weave relevant ones into component descriptions.
    *   Decision: Briefly list key patterns in TDS Section 2.3 (Technology Stack) and maybe expand 2.4 (Design Patterns). The current 2.3 and 2.4 in TDS are just "(No significant changes...)". This is an opportunity.

*   **TDS 2.2.1 `ApplicationCore`**: I'll merge the broader role description from PAD v5 (5.1).
*   **TDS Section 2**: I will add a new sub-section, perhaps 2.5, for "Asynchronous Processing Model" and summarize the details from PAD v5 (Section 9 and 5.1).
*   **ORM Model Details (PAD v5 Section 5.2)**: The TDS doesn't detail ORM base classes (`TimestampMixin`, `UserAuditMixin`) or the SQLAlchemy 2.0 style (`Mapped`, `mapped_column`). This is good technical detail for a TDS. I'll add a subsection under 3.2 for this.
*   **Utilities (PAD v5 Section 5.6)**: TDS mentions DTOs in 3.3 but could briefly mention other key utils like `Result` object, `json_helpers` in a general utilities section if one doesn't exist, or within relevant component descriptions. The current TDS doesn't have a dedicated "Utilities" section in its component breakdown. I can add a brief mention in Section 2.2 (perhaps a new 2.2.2 for "Common Utilities & DTOs").
    *   Decision: I will add a small paragraph about `app.utils.result.Result` and `app.utils.json_helpers` in the context of manager-UI communication or async task handling. The DTOs are already well covered.
*   **Enums (PAD v5 Section 5.7)**: PAD v5 mentions `app/common/enums.py`. This is a good detail for completeness. I can add this to the "Component Architecture" overview or when discussing DTOs/Models.
    *   Decision: Mention `app/common/enums.py` perhaps under 2.2, general components.

**Final check on "removing repeating details":**
The main repetition is Bank Rec flow in 4.7 and 9.2. I will make 4.7 a module overview: purpose, key features (drafts, matching, unmatching, finalization, history), and list the main UI components (`BankReconciliationWidget`) and Services (`BankReconciliationService`, `BankTransactionManager`) involved and their primary roles in the workflow. The detailed step-by-step stays in 9.2.

**The screenshots**: They confirm the UI elements for Dashboard (KPIs, AR/AP aging) and Bank Reconciliation (tables for unreconciled/provisionally matched, buttons). The TDS descriptions in 2.2.5 and 5 seem to cover these well. No new information to extract beyond confirming the TDS descriptions are accurate.

The file to be produced is `Technical_Design_Specification_Document.md`. The input is `Technical_Design_Specification_Document (draft).md`. I need to be careful to output the *complete* file with changes.

Okay, I have a clear plan. I will now proceed to generate the updated TDS.
I need to be careful with Markdown formatting.
The TDS is already "v15". I will keep it as "v15" but ensure its content reflects the synthesis of all provided documents and truly represents the state after schema v1.0.5.
The title in the TDS is `# Technical Design Specification Document: SG Bookkeeper (v15)`. I will keep this.
The version in 1.1 is also `15.0` and date `2025-06-04`. This date matches the schema diff file, so it's current.

Let's start generating the modified content section by section based on these thoughts.
I will be very careful to only modify what's necessary and preserve harmless original code. The request is to *update* by removing repeats and adding missing details.

Re-check Section 7 about atomicity:
Original TDS: "...`BankReconciliationService.save_reconciliation_details` ensures that saving the `BankReconciliation` record, updating multiple `BankTransaction` records, and updating the `BankAccount` record occurs within a single atomic database transaction."
Corrected thought: Change `save_reconciliation_details` to `finalize_reconciliation` and broaden the scope.
Proposed text for TDS Section 7: "Multi-step database operations (e.g., invoice posting, payment recording, provisional matching/unmatching of bank transactions, and finalization of bank reconciliations) are handled within a single database session (`async with db_manager.session():`) managed by the relevant manager or service methods to ensure atomicity. For instance, `BankReconciliationService.finalize_reconciliation` ensures that updating the `BankReconciliation` record (e.g., status to 'Finalized', balance figures) and the parent `BankAccount`'s last reconciled information occurs as a single atomic unit. Similarly, methods like `mark_transactions_as_provisionally_reconciled` and `unreconcile_transactions` ensure their respective updates to `BankTransaction` records are atomic." This is more accurate.

Re-check Section 2.3 and 2.4 which are currently "No significant changes".
PAD v5 lists Key Technologies and Design Patterns. I should populate these sections in the TDS.
TDS 2.3 Technology Stack: I'll list the stack from PAD v5 (Section 7).
TDS 2.4 Design Patterns: I'll list the patterns from PAD v5 (Section 8).

Adding a brief mention of `app/common/enums.py` and key utilities.
In Section 2.2 (Component Architecture), I can add a small introductory paragraph before 2.2.1:
"The application's components are organized into core functionalities, data access services, business logic managers, and UI elements. Common utilities in `app/utils/` (like `pydantic_models.py` for DTOs, `result.py` for operation outcomes, `json_helpers.py` for data serialization) and shared enumerations in `app/common/enums.py` support these layers."

This should cover the main points. I am ready to construct the file.

```markdown
# Technical Design Specification Document: SG Bookkeeper (v15)

**Version:** 15.0
**Date:** 2025-06-04

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version **15.0**, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version **1.0.5**. This version specifically details refinements and enhancements to:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements, including CSV import, draft reconciliation persistence, provisional matching/unmatching of transactions, creating adjustment journal entries, finalizing reconciliations, and viewing history of finalized reconciliations.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Dashboard KPIs (Enhanced)**: Display of key financial indicators including YTD P&L figures, cash balance, AR/AP totals (outstanding and overdue), detailed AR/AP Aging summaries, and Current Ratio.
*   **Database Enhancements**: Schema reflects v1.0.5, including the `status` field in `business.bank_reconciliations` and related logic.
These build upon previously documented features like Payments, Audit Log UI, enhanced GST Reporting, Sales/Purchase Invoicing, and core accounting/admin functionalities.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Details and organization as defined in `scripts/schema.sql` (reflecting v1.0.5 changes), including the `status` field in `bank_reconciliations`.
-   Key UI Implementation Patterns: `PySide6` interactions for new/enhanced banking (drafts, unmatching, history) and dashboard features (AR/AP aging, current ratio).
-   Core Business Logic: Component structures and interactions for refined bank reconciliation workflow and new KPI generation.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs), including their structure, purpose, and validation roles.
-   Security Implementation: Authentication, Role-Based Access Control (RBAC), and audit mechanisms including UI.
-   Deployment and Initialization procedures (technical aspects).
-   Current Implementation Status: Highlighting features implemented up to this version.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It is designed to provide comprehensive accounting solutions for Singaporean Small to Medium-sized Businesses (SMBs). Key features include a full double-entry bookkeeping system, Singapore-specific GST management (including F5 return preparation with detailed export), interactive financial reporting, modules for managing essential business operations (Customers, Vendors, Products/Services, full Sales & Purchase Invoicing lifecycle, Payments with allocations), Bank Account management with manual transaction entry, CSV bank statement import, a full bank reconciliation module with draft persistence, provisional matching/unmatching capabilities, and history viewing. It also features an enhanced dashboard displaying AR/AP aging summaries and current ratio KPIs, alongside comprehensive system administration for Users, Roles, Permissions, and Audit Log viewing. The application emphasizes data integrity, compliance with local accounting standards, user-friendliness, and robust auditability.

### 1.5 Current Implementation Status
As of version 15.0 (reflecting schema v1.0.5):
*   All features listed in the previous TDS iteration (covering initial bank rec, CSV import, auto bank txns from JEs, basic dashboard) are implemented.
*   **Enhanced Banking Features (Bank Reconciliation Refinements)**:
    *   **Draft Reconciliation Persistence**: Reconciliations can be started and saved in a "Draft" state. When a user returns to a bank account/statement date combination with an existing draft, it's loaded.
    *   **Provisional Matching**: UI "Match Selected" action persists matches against the current draft reconciliation ID by updating `BankTransaction` records (`is_reconciled=True`, `reconciled_bank_reconciliation_id` set to draft's ID).
    *   **Unmatching**: UI "Unmatch Selected Items" action allows users to revert provisionally matched items within the current draft session by clearing their reconciliation linkage.
    *   **Finalization**: "Save Final Reconciliation" updates the draft reconciliation's status to "Finalized" and confirms balances.
    *   **History Viewing**: Reconciliation history list now displays only "Finalized" reconciliations, with paginated results.
*   **Enhanced Dashboard KPIs**:
    *   Displays AR Aging Summary (Current, 1-30, 31-60, 61-90, 91+ days).
    *   Displays AP Aging Summary (Current, 1-30, 31-60, 61-90, 91+ days).
    *   Displays Current Ratio.
    *   `DashboardManager` and underlying services updated to calculate these new metrics.
*   **Database**: Schema updated to v1.0.5, primarily adding `status` to `business.bank_reconciliations`.
*   **Circular Import Resolution**: Systematic fixes applied to managers, services, and `ApplicationCore` to resolve module-level circular import dependencies, primarily using conditional imports (`if TYPE_CHECKING:`) and string literal type hints.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-----------------------------------------------------------------+
|                       Presentation Layer (UI)                   |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
+-----------------------------------------------------------------+
      ^                         | (schedule_task_from_qt for async calls)
      | (UI Events, Pydantic DTOs) | (Results/Updates via QMetaObject.invokeMethod)
      v                         v
+-----------------------------------------------------------------+
|                  Business Logic Layer (Managers)                |
| (ApplicationCore, *Manager classes e.g., SalesInvoiceManager,  |
|  PaymentManager, JournalEntryManager, BankTransactionManager)   |
| Encapsulates Business Rules, Complex Workflows, Validation.     |
| Orchestrates Services. Returns `Result` objects.                |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, SQLAlchemy ORM Objects/DTOs)
      | (Service results/ORM Objects) | (SQLAlchemy Async Operations within Services)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer (Services)              |
| (DatabaseManager, *Service classes e.g., AccountService,       |
|  SalesInvoiceService, BankReconciliationService), SQLAlchemy Models|
| Implements Repository Pattern. Abstracts Database Interactions. |
| Manages ORM query logic.                                        |
+-----------------------------------------------------------------+
                                | (asyncpg DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers, Constraints)               |
+-----------------------------------------------------------------+
```

### 2.2 Component Architecture (Updates for Reconciliation Drafts & Dashboard KPIs)
The application's components are organized into core functionalities, data access services, business logic managers, and UI elements. Common utilities in `app/utils/` (like `pydantic_models.py` for DTOs, `result.py` for operation outcomes, `json_helpers.py` for data serialization between threads) and shared enumerations in `app/common/enums.py` support these layers.

#### 2.2.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`application_core.py`)**:
    *   The central singleton orchestrator for the backend.
    *   Initializes and provides access to all Manager and Service instances, acting as a service locator and facilitating dependency injection.
    *   Refactored to use local imports for service instantiations within `startup()` to resolve circular dependencies. Top-level service imports removed; service types are now in `TYPE_CHECKING` block for property hints.
    *   Holds references to global `ConfigManager`, `DatabaseManager`, and logger.
*   **`DatabaseManager` (`database_manager.py`)**: Manages asynchronous PostgreSQL connections (SQLAlchemy async engine, `asyncpg` pool). Provides sessions and sets `app.current_user_id` for audit triggers.
*   **`ConfigManager` (`config_manager.py`)**: Loads and manages application settings from `config.ini`.
*   **`SecurityManager` (`security_manager.py`)**: Handles user authentication (bcrypt) and Role-Based Access Control (RBAC), including managing the `current_user` ORM object.

#### 2.2.2 Services (Data Access Layer - `app/services/`)
*   **`CustomerService` (`business_services.py`)**: Added `get_ar_aging_summary()` method.
*   **`VendorService` (`business_services.py`)**: Added `get_ap_aging_summary()` method.
*   **`AccountService` (`account_service.py`)**: Added `get_total_balance_by_account_category_and_type_pattern()` method for calculating parts of current assets/liabilities.
*   **`BankReconciliationService` (`business_services.py`)**:
    *   Modified `get_reconciliations_for_account` to filter for `status='Finalized'`.
    *   Added `get_or_create_draft_reconciliation()`: Retrieves or creates a 'Draft' reconciliation for a given bank account and statement date.
    *   Added `mark_transactions_as_provisionally_reconciled()`: Updates `BankTransaction` records to link them to a draft reconciliation and set `is_reconciled=True`.
    *   Added `finalize_reconciliation()`: Updates a 'Draft' reconciliation to 'Finalized', updates its balances, and updates the linked `BankAccount`'s last reconciled info.
    *   Added `unreconcile_transactions()`: Clears reconciliation linkage from `BankTransaction` records.
    *   The old `save_reconciliation_details` method is removed/refactored into these new methods.
    *   Added `get_transactions_for_reconciliation()`: Fetches transactions linked to a specific reconciliation ID (used for populating provisionally matched items).

#### 2.2.3 Managers (Business Logic Layer)
*   Multiple managers (e.g., `CustomerManager`, `VendorManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`, `BankAccountManager`, `BankTransactionManager`, `PaymentManager`, `GSTManager`, `FinancialStatementGenerator`) were refactored to use conditional imports (`if TYPE_CHECKING:`) and string literal type hints for their service dependencies in constructor signatures to resolve circular import issues.
*   **`DashboardManager` (`app/reporting/dashboard_manager.py`)**:
    *   `get_dashboard_kpis()` method significantly enhanced to:
        *   Call new service methods for AR/AP aging (`CustomerService.get_ar_aging_summary`, `VendorService.get_ap_aging_summary`).
        *   Calculate total current assets and liabilities by fetching active accounts (via `AccountService`) and their balances (via `JournalService`), then filtering by predefined `CURRENT_ASSET_SUBTYPES` and `CURRENT_LIABILITY_SUBTYPES` (constants defined within `DashboardManager` or a shared config).
        *   Calculate the Current Ratio.
        *   Populate the extended `DashboardKPIData` DTO.
*   **`BankTransactionManager` (`app/business_logic/bank_transaction_manager.py`)**:
    *   `get_unreconciled_transactions_for_matching()` logic remains focused on `is_reconciled=False` items, providing data for the "Unreconciled" tables in the UI.

#### 2.2.4 User Interface (Presentation Layer - `app/ui/`)
*   **`DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`)**:
    *   UI updated with `QGroupBox` sections for "AR Aging Summary" and "AP Aging Summary", each containing `QLabel`s arranged with `QFormLayout` for aging buckets (Current, 1-30, 31-60, 61-90, 91+ days).
    *   A new row added for displaying "Current Ratio".
    *   Layout adjusted (e.g., using `QGridLayout`) to accommodate new KPIs, potentially using a two-column arrangement for primary KPIs and group boxes for aging summaries. `QScrollArea` may be used for scalability.
*   **`BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**:
    *   Manages `self._current_draft_reconciliation_id` obtained from `BankReconciliationService`.
    *   `_on_load_transactions_clicked` / `_fetch_and_populate_transactions` first calls `get_or_create_draft_reconciliation` service method. It then fetches unreconciled items (via `BankTransactionManager`) and provisionally matched items for the current draft (via `BankReconciliationService.get_transactions_for_reconciliation`).
    *   `_on_match_selected_clicked` calls a helper `_perform_provisional_match` which uses `BankReconciliationService.mark_transactions_as_provisionally_reconciled` to persist matches against the draft. Match logic enhanced to check `abs(sum_stmt_amounts - sum_sys_amounts) < tolerance`.
    *   `_on_save_reconciliation_clicked` (renamed "Save Final Reconciliation" in UI) calls `_perform_finalize_reconciliation` which uses `BankReconciliationService.finalize_reconciliation` with the draft ID.
    *   Added new UI sections ("Provisionally Matched Statement Items (This Session)", "Provisionally Matched System Transactions (This Session)") with tables (`draft_matched_statement_table`, `draft_matched_system_table`) using `ReconciliationTableModel`. A `QSplitter` is used to manage the layout of these tables.
    *   Added "Unmatch Selected Items" button (`self.unmatch_button`) and corresponding logic (`_on_unmatch_selected_clicked`, `_perform_unmatch`) to call `BankReconciliationService.unreconcile_transactions`.
    *   History list (`self.history_table`) correctly populates with finalized reconciliations and allows viewing details.

### 2.3 Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12 supported)
-   **UI Framework**: PySide6 6.9.0+ (Qt 6 bindings)
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Asynchronous ORM)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (for PDF generation), `openpyxl` (for Excel generation/manipulation)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`
-   **Asynchronous Programming**: `asyncio`, `threading` (for dedicated asyncio event loop)

### 2.4 Design Patterns Used
The application employs several design patterns to promote maintainability, flexibility, and separation of concerns:
-   **Layered Architecture**: Separates UI, Business Logic, and Data Access.
-   **Model-View-Controller (MVC) / Model-View-Presenter (MVP) variant**: UI widgets (View/Presenter) interact with Managers (Controller/Presenter) which use Services and Models.
-   **Repository Pattern**: Implemented by Service classes in the Data Access Layer.
-   **Data Transfer Object (DTO)**: Pydantic models are used for structured data exchange between layers, especially UI and Managers, providing validation.
-   **Result Object Pattern**: The `app/utils/result.Result` class standardizes return values from manager/service methods.
-   **Observer Pattern**: Qt's Signal/Slot mechanism for communication within the UI and between UI and backend callback handlers.
-   **Dependency Injection (Conceptual)**: `ApplicationCore` initializes and provides dependencies (services to managers, managers to UI layers indirectly).
-   **Singleton (Conceptual)**: `ApplicationCore` and its managed service/manager instances behave as singletons within the application's context.
-   **Mixin Classes**: Used for ORM models (`TimestampMixin`, `UserAuditMixin`) to share common fields and functionalities.

### 2.5 Asynchronous Processing Model
To ensure UI responsiveness, particularly during database operations or complex calculations, SG Bookkeeper uses an asynchronous processing model:
1.  A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD` in `app/main.py`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`), separate from the Qt GUI event loop.
2.  UI actions that require backend processing (e.g., fetching data, saving records) schedule an `async` coroutine (typically a manager method) onto this dedicated asyncio loop using the `schedule_task_from_qt(coroutine)` utility. This uses `asyncio.run_coroutine_threadsafe`.
3.  The manager method, now executing in the asyncio thread, performs its operations, which may include calling `async` service methods that interact with the database via `asyncpg` and SQLAlchemy's async features.
4.  Upon completion of the asynchronous task, results or data intended for UI updates are marshaled back to the Qt main GUI thread. This is typically done using `QMetaObject.invokeMethod(target_widget, "slot_name", Qt.ConnectionType.QueuedConnection, Q_ARG(type, data))`. Data passed between threads (e.g., DTOs) is often serialized to JSON (using `app/utils/json_helpers.py`) to ensure thread safety and compatibility with `Q_ARG`.
5.  The designated slot method in the UI widget then safely updates the UI components with the received data.

This architecture prevents the GUI from freezing during potentially long-running backend operations, enhancing user experience.

## 3. Data Architecture (Updates based on Schema v1.0.5)

### 3.1 Database Schema Overview
*   The database schema is now at version **1.0.5**, defined in `scripts/schema.sql`.
*   Key table for recent enhancements: **`business.bank_reconciliations`**:
    *   Now includes a `status VARCHAR(20) NOT NULL DEFAULT 'Draft'` column with a `CHECK` constraint (`status IN ('Draft', 'Finalized')`). This is central to managing the lifecycle of a reconciliation process, allowing users to save drafts and finalize them later.
*   Related changes:
    *   `business.bank_accounts` includes `last_reconciled_balance NUMERIC(15,2) NULL`.
    *   `business.bank_transactions` includes `reconciled_bank_reconciliation_id INT NULL` as a foreign key to `business.bank_reconciliations`.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
*   **`app/models/business/bank_reconciliation.py`**: The `BankReconciliation` ORM model is updated to include the `status: Mapped[str]` field, corresponding to the database schema change.
*   **ORM Style and Base Classes**:
    *   Models use SQLAlchemy 2.0 style with `Mapped` and `mapped_column` annotations for type safety and clarity.
    *   Common functionalities are inherited from base/mixin classes in `app/models/base.py`:
        *   `Base`: The declarative base for all models.
        *   `TimestampMixin`: Provides `created_at` and `updated_at` columns with automatic server-side timestamp management.
        *   `UserAuditMixin`: Provides `created_by_user_id` and `updated_by_user_id` columns (linking to `core.users.id`) for tracking data modifications.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **`DashboardKPIData`**: Extended to include new fields for AR/AP aging summaries and current ratio metrics:
    *   `ar_aging_current`, `ar_aging_1_30`, `ar_aging_31_60`, `ar_aging_61_90`, `ar_aging_91_plus`
    *   `ap_aging_current`, `ap_aging_1_30`, `ap_aging_31_60`, `ap_aging_61_90`, `ap_aging_91_plus`
    *   `total_current_assets`, `total_current_liabilities`
    *   `current_ratio`
*   Pydantic DTOs are extensively used for validating data passed from the UI to managers and for structuring data returned to the UI.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
Interface definitions for services are updated to reflect new functionalities:
*   **`IBankAccountRepository`**: Added `async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: pass`.
*   **`ICustomerRepository`**: Added `async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass`.
*   **`IVendorRepository`**: Added `async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass`.
*   **`IAccountRepository`**: Added `async def get_total_balance_by_account_category_and_type_pattern(self, account_category: str, account_type_name_like: str, as_of_date: date) -> Decimal: pass`.
*   **`IBankReconciliationRepository`**:
    *   Added `async def get_or_create_draft_reconciliation(...) -> BankReconciliation: pass`.
    *   Added `async def mark_transactions_as_provisionally_reconciled(...) -> Result: pass`.
    *   Added `async def finalize_reconciliation(...) -> Result: pass`.
    *   Added `async def unreconcile_transactions(...) -> Result: pass`.
    *   Added `async def get_transactions_for_reconciliation(...) -> List[BankTransaction]: pass`.
    *   Old `save_reconciliation_details` interface method removed.

## 4. Module and Component Specifications

### 4.1 Core Accounting Module (`app/accounting/`, `app/ui/accounting/`)
-   **Chart of Accounts**: Hierarchical account management.
    -   Manager: `ChartOfAccountsManager`. Service: `AccountService`. UI: `ChartOfAccountsWidget`, `AccountDialog`.
-   **Journal Entries**: Manual journal entry creation and management.
    -   Manager: `JournalEntryManager`. Service: `JournalService`. UI: `JournalEntriesWidget`, `JournalEntryDialog`.
    *   `JournalEntryManager.post_journal_entry` now automatically creates a system `BankTransaction` if a journal line debits or credits a GL account linked to a `BankAccount`. This facilitates bank reconciliation by ensuring such internal movements are available for matching.
-   **Fiscal Period Management**: Setup and control of fiscal years/periods.
    -   Manager: `FiscalPeriodManager`. Services: `FiscalYearService`, `FiscalPeriodService`. UI: In `SettingsWidget`, `FiscalYearDialog`.

### 4.2 Tax Management Module (`app/tax/`, `app/ui/reports/`)
-   **GST Management**:
    *   Manager: `GSTManager` (prepares `GSTReturnData` DTO including `detailed_breakdown` of `GSTTransactionLineDetail` objects for F5 boxes, saves draft, finalizes with settlement JE).
    *   Service: `TaxCodeService`, `GSTReturnService`.
    *   UI: `ReportsWidget` (GST F5 tab) includes "Export Details (Excel)" for detailed breakdown.
-   **Tax Calculation**: `TaxCalculator` service (`calculate_line_tax`) used by invoice managers.

### 4.3 Business Operations Modules (`app/business_logic/`, `app/ui/.../`)
-   **Customer, Vendor, Product/Service Management**: Full CRUD and list views.
    -   Managers: `CustomerManager`, `VendorManager`, `ProductManager`. Services: `CustomerService`, `VendorService`, `ProductService`. UI: `CustomersWidget`, `VendorsWidget`, `ProductsWidget`, respective dialogs.
-   **Sales Invoicing Module**: Full lifecycle.
    -   Manager: `SalesInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `SalesInvoiceService`. UI: `SalesInvoicesWidget`, `SalesInvoiceDialog`.
-   **Purchase Invoicing Module**: Full lifecycle.
    -   Manager: `PurchaseInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `PurchaseInvoiceService`. UI: `PurchaseInvoicesWidget`, `PurchaseInvoiceDialog`.

### 4.4 System Administration Modules (`app/core/security_manager.py`, `app/ui/settings/`, `app/ui/audit/`)
-   **User Management**:
    -   Manager: `SecurityManager`. UI: `UserManagementWidget`, `UserDialog`, `UserPasswordDialog`.
-   **Role & Permission Management**:
    -   Manager: `SecurityManager`. UI: `RoleManagementWidget`, `RoleDialog`.
-   **Audit Log Viewing**:
    -   Service: `AuditLogService` (fetches `AuditLog`, `DataChangeHistory` with pagination/filtering). UI: `AuditLogWidget` in `SettingsWidget` with "Action Log" and "Data Change History" tabs. Minor improvements to change summary formatting.

### 4.5 Reporting Module (`app/reporting/`, `app/ui/reports/`)
-   **Financial Statements**: Generation and export (BS, P&L, TB, GL).
    -   Manager: `FinancialStatementGenerator`, `ReportEngine` (PDF/Excel export with enhanced formatting). UI: Financial Statements tab in `ReportsWidget`.

### 4.6 Dashboard Module (Enhanced) (`app/reporting/dashboard_manager.py`, `app/ui/dashboard/`)
-   **Purpose**: Provide a quick overview of key financial metrics.
-   **Manager (`DashboardManager`)**:
    *   `get_dashboard_kpis()`:
        *   Retrieves YTD Revenue, Expenses, Net Profit (via `FinancialStatementGenerator`).
        *   Calculates Current Cash Balance (sum of base currency active bank accounts via `BankAccountService` and `JournalService`).
        *   Retrieves Total Outstanding AR/AP (via `CustomerService`/`VendorService` or GL balances).
        *   Fetches AR/AP aging summaries (Current, 1-30, 31-60, 61-90, 91+ days) from `CustomerService.get_ar_aging_summary` and `VendorService.get_ap_aging_summary`.
        *   Calculates Total Current Assets and Total Current Liabilities by:
            1.  Fetching all active accounts from `AccountService`.
            2.  Iterating and summing balances (via `JournalService.get_account_balance_by_type_and_subtype` or similar, using `AccountService.get_total_balance_by_account_category_and_type_pattern`) for accounts whose types/subtypes match predefined lists for current assets/liabilities (e.g., `CURRENT_ASSET_SUBTYPES`, `CURRENT_LIABILITY_SUBTYPES` constants).
        *   Calculates Current Ratio (`Total Current Assets / Total Current Liabilities`), handling division by zero.
        *   Populates the extended `DashboardKPIData` DTO with all these metrics.
-   **UI (`DashboardWidget`)**:
    *   Displays all KPIs fetched from `DashboardManager`.
    *   Includes dedicated `QGroupBox` sections with `QFormLayout` for AR Aging Summary and AP Aging Summary, showing the different aging buckets.
    *   Displays the Current Ratio.
    *   Layout uses `QGridLayout` for organization and `QScrollArea` for better viewing of content.
    *   Includes a "Refresh KPIs" button.

### 4.7 Banking Module (Refined Bank Reconciliation Workflow)
-   **Purpose**: Enables users to reconcile bank account statements with system bank transactions, manage discrepancies, and maintain an audit trail of reconciliations.
-   **Key Features**:
    *   **Draft Persistence**: Reconciliations can be started, partially completed, and saved as a 'Draft'. Users can resume these drafts later.
    *   **Provisional Matching**: Users can select and match statement items with system transactions. These matches are persisted against the current draft reconciliation.
    *   **Unmatching**: Provisionally matched items can be unmatched within the draft session.
    *   **Adjustment Journal Entries**: Facilitates creation of JEs for items appearing only on the bank statement (e.g., bank charges, interest earned). These JEs auto-create corresponding system bank transactions.
    *   **Finalization**: Once reconciled (difference is zero), the draft can be finalized, updating its status and the bank account's last reconciled details.
    *   **History**: A paginated history of all "Finalized" reconciliations is viewable, with details of cleared transactions.
-   **Core UI Component**: `BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`).
-   **Key Service**: `BankReconciliationService` (`app/services/business_services.py`) handles the lifecycle of reconciliations (draft creation, provisional matching/unmatching, finalization).
-   **Supporting Services/Managers**:
    *   `BankTransactionManager`: Fetches unreconciled bank transactions.
    *   `JournalEntryManager`: Used for creating adjustment JEs.
    *   `BankAccountService`: Provides bank account details.
-   The detailed step-by-step data flow for the reconciliation process is outlined in Section 9.2.

## 5. User Interface Implementation (`app/ui/`) (Updates)
*   **`DashboardWidget`**:
    *   Uses `QGridLayout` to arrange KPIs into columns and sections for better visual organization.
    *   Introduced `QGroupBox` elements for "AR Aging Summary" and "AP Aging Summary", utilizing `QFormLayout` within them to display aging bucket labels and values.
    *   A specific `QLabel` is dedicated to displaying the "Current Ratio".
    *   Encased within a `QScrollArea` to handle varying content sizes and improve usability on smaller screens.
*   **`BankReconciliationWidget`**:
    *   Incorporates two new `QGroupBox` sections, each containing a `QTableView` (populated by `ReconciliationTableModel`), for "Provisionally Matched Statement Items (This Session)" and "Provisionally Matched System Transactions (This Session)". This clearly separates items actively being worked on in the current draft.
    *   A `QSplitter` is employed to allow users to dynamically resize the areas dedicated to unreconciled tables versus provisionally matched tables.
    *   Includes a new "Unmatch Selected Items" button to revert provisional matches.
    *   The button for saving the final reconciliation is labeled "Save Final Reconciliation".
    *   Maintains internal state for `_current_draft_reconciliation_id` to manage context across operations.

## 6. Security Considerations
-   **Authentication**: User login handled by `SecurityManager` using `bcrypt` for password hashing and salting. Failed login attempts are tracked; accounts can be configured for lockout.
-   **Authorization (RBAC)**: A granular permission system (`core.permissions`, `core.roles`, `core.user_roles`, `core.role_permissions` tables) is enforced by `SecurityManager.has_permission()`. The "Administrator" role has all permissions and is protected.
-   **Audit Trails**: Comprehensive database-level audit logging is implemented via PL/pgSQL triggers (e.g., `audit.log_data_change_trigger_func`). The `DatabaseManager` sets the `app.current_user_id` session variable in PostgreSQL, which is captured by these triggers. Data is stored in `audit.audit_log` (action summaries) and `audit.data_change_history` (field-level changes). A UI for viewing these logs is provided.
-   **Data Integrity**: Enforced by database constraints (PK, FK, CHECK, UNIQUE, NOT NULL), Pydantic DTO validation at the boundary between UI and Business Logic Layer, and business rule validation within Manager classes.

## 7. Database Access Implementation
-   **`DatabaseManager`**: Manages the SQLAlchemy asynchronous engine and `asyncpg` connection pool. Provides `AsyncSession` instances through an `asynccontextmanager` (`session()`).
-   **Services (Repository Pattern)**: Service classes (e.g., `AccountService`, `SalesInvoiceService`, `BankReconciliationService`) encapsulate all data access logic for specific ORM models or related groups of models. They use SQLAlchemy's async session for all database operations.
-   **ORM Models (`app/models/`)**: Define the mapping between Python objects and database tables, including relationships, constraints, and potentially model-level behavior via mixins (e.g., `TimestampMixin`, `UserAuditMixin`).
-   **Transactions**: Multi-step database operations (e.g., invoice posting, payment recording, provisional matching/unmatching of bank transactions, and finalization of bank reconciliations) are handled within a single database session (`async with db_manager.session():`) managed by the relevant manager or service methods to ensure atomicity. For instance, `BankReconciliationService.finalize_reconciliation` ensures that updating the `BankReconciliation` record (e.g., status to 'Finalized', balance figures) and the parent `BankAccount`'s last reconciled information occurs as a single atomic unit. Similarly, methods like `mark_transactions_as_provisionally_reconciled` and `unreconcile_transactions` ensure their respective updates to `BankTransaction` records are atomic.

## 8. Deployment and Installation
-   **Prerequisites**: Python 3.9+, PostgreSQL 14+, Poetry.
-   **Setup**:
    1.  Clone repository.
    2.  Install dependencies: `poetry install`.
    3.  Configure database connection in `config.ini` (located in a platform-specific user config directory). Create `config.ini` from `config.example.ini` if it doesn't exist, ensuring correct database credentials and name.
    4.  Initialize database: `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This executes `scripts/schema.sql` (DDL, v1.0.5) and `scripts/initial_data.sql` (seeding roles, permissions, default user, system accounts, etc.).
-   **Execution**: `poetry run sg_bookkeeper`.
-   Refer to `README.md` and potentially a separate `deployment_guide.md` for more detailed user-facing instructions.

## 9. Data Flow Examples

### 9.1 Data Flow Example: Sales Invoice Posting
1.  **UI (`SalesInvoiceDialog`)**: User completes invoice details (customer, items, quantities, dates), clicks "Save & Approve".
2.  **Data Collection & DTO (UI/Manager)**: UI data (header, lines) gathered into `SalesInvoiceCreateData` DTO.
3.  **Manager (`SalesInvoiceManager.create_and_post_invoice`)**:
    *   Receives DTO. Performs validations (fiscal period open, customer valid, product valid, quantities available for inventory items).
    *   Calculates line totals, subtotals, tax amounts (using `TaxCalculator`), and grand total.
    *   Generates unique invoice number (via `SequenceService` or equivalent DB function).
    *   Calls `SalesInvoiceService.create_invoice_from_dto()` to save `SalesInvoice` and `SalesInvoiceLine` ORM objects to database (typically as a draft first).
4.  **Financial Journal Entry (Manager: `JournalEntryManager`)**:
    *   If invoice saved successfully, `SalesInvoiceManager` prepares data for financial JE (Debit Accounts Receivable, Credit Sales Revenue, Credit GST Payable).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` with JE data. This validates, creates, and posts the JE, updating account balances.
5.  **Inventory Journal Entry (Manager: `JournalEntryManager`, Service: `ProductService`)**:
    *   If invoice includes inventory items, `SalesInvoiceManager` calculates Cost of Goods Sold (COGS) using Weighted Average Cost (WAC) from `ProductService` (or `inventory_summary` view).
    *   Prepares data for COGS JE (Debit COGS, Credit Inventory).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` for COGS JE.
    *   `InventoryMovement` records are also created.
6.  **Invoice Status Update (Service: `SalesInvoiceService`)**:
    *   `SalesInvoiceManager` calls `SalesInvoiceService` to update the invoice's status to "Posted" (or similar) and links the main financial JE ID.
7.  **UI Feedback**: Success message. Sales invoice list view updates.

### 9.2 Data Flow Example: Bank Reconciliation Process (Refined)
1.  **Setup (UI: `BankReconciliationWidget`)**: User selects Bank Account, Statement Date, enters Statement Ending Balance. Clicks "Load / Refresh Transactions".
2.  **Get/Create Draft & Fetch Data (Widget -> Service/Manager)**:
    *   The widget's `_fetch_and_populate_transactions` method (or similar handler) is invoked.
    *   It calls `BankReconciliationService.get_or_create_draft_reconciliation`, passing bank account ID, statement date, and the statement ending balance from the UI. The service returns a `BankReconciliation` ORM object (the draft) and its ID is stored in `self._current_draft_reconciliation_id`. The UI statement balance is updated if the loaded draft had a different persisted balance.
    *   The widget fetches the current GL balance for the bank account's linked GL account (via `JournalService.get_account_balance`).
    *   It fetches unreconciled transactions (`is_reconciled=False`) for the bank account up to the statement date via `BankTransactionManager.get_unreconciled_transactions_for_matching`. These populate the "Unreconciled" tables.
    *   It fetches transactions already provisionally matched to the current `_current_draft_reconciliation_id` via `BankReconciliationService.get_transactions_for_reconciliation`. These populate the "Provisionally Matched (This Session)" tables.
3.  **Display & Calculate (UI)**: The UI populates all tables. The initial "Reconciliation Summary" (Difference, Adjusted Book Balance, etc.) is calculated based on the statement ending balance, current GL balance, and the sum of *unreconciled* items (as provisionally matched items are considered 'cleared' for the draft).
4.  **User Interaction - Provisional Matching (UI -> Service)**:
    *   User selects one or more items from the "Unreconciled Bank Statement Items" table and one or more items from the "Unreconciled System Transactions" table.
    *   User clicks "Match Selected".
    *   The UI validates if the sum of selected statement item amounts equals the sum of selected system transaction amounts (within a small tolerance).
    *   If valid, `_perform_provisional_match` calls `BankReconciliationService.mark_transactions_as_provisionally_reconciled` with the `_current_draft_reconciliation_id` and lists of selected statement and system transaction IDs. The service updates these `BankTransaction` records in the DB (sets `is_reconciled=True`, `reconciled_date` to statement date, and `reconciled_bank_reconciliation_id` to the draft's ID).
    *   UI reloads all transaction lists (effectively re-running step 2). Matched items now appear in "Provisionally Matched" tables. The summary recalculates.
5.  **User Interaction - Unmatching (UI -> Service)**:
    *   User selects one or more items from the "Provisionally Matched Statement Items (This Session)" table and/or "Provisionally Matched System Transactions (This Session)" table.
    *   User clicks "Unmatch Selected Items".
    *   `_perform_unmatch` calls `BankReconciliationService.unreconcile_transactions` with the IDs of the selected transactions. The service updates these `BankTransaction` records in the DB (sets `is_reconciled=False`, clears `reconciled_date` and `reconciled_bank_reconciliation_id`).
    *   UI reloads all transaction lists. Unmatched items move back to "Unreconciled" tables. Summary recalculates.
6.  **User Interaction - New JE for Statement Item (UI -> Manager -> Service)**:
    *   User selects an unmatched bank statement item (e.g., a bank charge not yet in books). Clicks "Add Journal Entry".
    *   `JournalEntryDialog` opens, possibly pre-filled (e.g., credit Bank GL Account, debit Bank Charge Expense).
    *   User completes and posts the JE via `JournalEntryManager`. This manager, upon posting a JE affecting a bank-linked GL account, automatically creates a new system `BankTransaction`.
    *   UI reloads transaction lists. The newly created system `BankTransaction` appears in the "Unreconciled System Transactions" table, ready for matching.
7.  **Finalizing (UI -> Service)**:
    *   When the "Difference" in the reconciliation summary is zero (or within acceptable tolerance), the user clicks "Save Final Reconciliation".
    *   `_perform_finalize_reconciliation` calls `BankReconciliationService.finalize_reconciliation` with the current `_current_draft_reconciliation_id`, the final statement ending balance, the calculated book balance, and the difference.
    *   The service updates the `BankReconciliation` record's `status` to "Finalized", updates its `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, and `reconciliation_date`. It also updates the linked `BankAccount` record's `last_reconciled_date` and `last_reconciled_balance`. All these DB operations occur within a single transaction.
8.  **UI Feedback**: Success/error message. The UI typically clears the current reconciliation workspace or resets for a new one. The "Reconciliation History" list is refreshed.

## 10. Conclusion (Updated)
Version 15 of SG Bookkeeper significantly refines the Bank Reconciliation module by introducing persistent draft sessions with provisional matching and unmatching capabilities, leading to a more robust and user-friendly reconciliation experience. The Dashboard has been enhanced with crucial AR/AP Aging summaries and the Current Ratio, providing deeper financial insights at a glance. Continuous architectural improvements, such as the resolution of circular import dependencies, strengthen the codebase's maintainability and stability. These features further solidify SG Bookkeeper as a comprehensive accounting tool for SMBs. Future work will focus on expanding automated test coverage, potentially handling more complex reconciliation matching scenarios (e.g., many-to-one), and further enriching dashboard and reporting functionalities based on user feedback and evolving business needs.

```Okay, I have carefully reviewed all the provided documents:
*   `Technical_Design_Specification_Document (draft).md` (TDS v15 - the input)
*   `diff_output_schema.sql.md` (schema v1.0.5 diffs)
*   `README (v13).md` (older README)
*   `README.md` (latest README reflecting v1.0.5)
*   `Project Architecture Document v4.md` (older PAD)
*   `Project Architecture Document.md` (PAD v5 - latest)
*   The two screenshots of the Dashboard and Bank Reconciliation UI.

Based on this review, I've created the updated `Technical_Design_Specification_Document.md` (still labeled v15 as the core content was already targeting this version, but now refined and augmented).

**Key changes made:**

1.  **Refined Section 1.2 (Scope)**: Added more specific mention of DTO/ORM roles.
2.  **Updated Section 1.4 (System Overview)**: Ensured alignment with the latest README description, emphasizing draft persistence, provisional matching/unmatching, and history for bank reconciliation, plus new dashboard KPIs.
3.  **Enhanced Section 2.2 (Component Architecture)**:
    *   Added an introductory sentence about common utilities (`app/utils`) and enums (`app/common`).
    *   **2.2.1 `ApplicationCore`**: Expanded description based on PAD v5 to include its role as a service locator and orchestrator. Added brief notes on `DatabaseManager`, `ConfigManager`, `SecurityManager`.
    *   **2.2.2 `Services`**: Added `BankReconciliationService.get_transactions_for_reconciliation()` which was implied but not explicitly listed in the draft TDS service method changes.
    *   **2.2.4 `UI`**: Ensured consistency with screenshots and descriptions from README/PAD v5 regarding UI elements like `QScrollArea` and `QSplitter`.
4.  **Added Section 2.3 (Technology Stack)**: Populated with the comprehensive list from PAD v5.
5.  **Added Section 2.4 (Design Patterns Used)**: Populated with the list from PAD v5.
6.  **Added Section 2.5 (Asynchronous Processing Model)**: Summarized the detailed explanation from PAD v5.
7.  **Enhanced Section 3.2 (SQLAlchemy ORM Models)**: Added details about ORM style (SQLAlchemy 2.0 `Mapped`, `mapped_column`) and base/mixin classes (`TimestampMixin`, `UserAuditMixin`) from PAD v5.
8.  **Clarified Section 4.1 (Core Accounting Module)**: Emphasized how `JournalEntryManager.post_journal_entry` creating `BankTransaction` records facilitates reconciliation.
9.  **Refined Section 4.6 (Dashboard Module)**: Ensured the description of KPI calculation aligns with other documents.
10. **Restructured Section 4.7 (Banking Module)**: Made this section a higher-level overview of the module's purpose, key features, and main components involved, deferring the detailed step-by-step flow to Section 9.2 to avoid repetition.
11. **Enhanced Section 5 (User Interface Implementation)**: Added details like `QGridLayout` and `QScrollArea` for Dashboard, and `QSplitter` for Bank Reconciliation UI, based on cross-referencing.
12. **Corrected Section 7 (Database Access Implementation)**: Updated the description of transactional atomicity to accurately reflect new service methods like `finalize_reconciliation`, `mark_transactions_as_provisionally_reconciled`, and `unreconcile_transactions`, replacing the outdated `save_reconciliation_details`.
13. **Corrected Section 8 (Deployment and Installation)**: Updated the referenced schema version in `scripts/schema.sql` to `v1.0.5`.
14. **Verified Section 9.2 (Data Flow Example: Bank Reconciliation)**: Ensured this detailed flow remains accurate and comprehensive for the refined reconciliation process.
15. **Updated Section 10 (Conclusion)**: Minor wording adjustments to ensure it fully reflects the "v15" scope.

The aim was to make the TDS more comprehensive by integrating details from the latest Project Architecture Document (PAD v5) and README, remove redundancy (primarily by making section 4.7 an overview and 9.2 the detail for bank rec), and ensure all technical specifics align with schema v1.0.5 and the described feature set.

Here is the complete updated replacement file for `Technical_Design_Specification_Document.md`:

```markdown
# Technical Design Specification Document: SG Bookkeeper (v15)

**Version:** 15.0
**Date:** 2025-06-04

## 1. Introduction

### 1.1 Purpose
This Technical Design Specification (TDS) document, version **15.0**, provides a detailed and up-to-date overview of the SG Bookkeeper application's technical design and implementation. It reflects the current state of the project, incorporating architectural decisions, component structures, and functionalities up to schema version **1.0.5**. This version specifically details refinements and enhancements to:
*   **Bank Reconciliation Module**: Comprehensive UI and backend logic for reconciling bank statements, including CSV import, draft reconciliation persistence, provisional matching/unmatching of transactions, creating adjustment journal entries, finalizing reconciliations, and viewing history of finalized reconciliations.
*   **Automated Bank Transaction Creation from Journal Entries**: Posting a journal entry that affects a bank-linked GL account now automatically generates a corresponding system bank transaction.
*   **Dashboard KPIs (Enhanced)**: Display of key financial indicators including YTD P&L figures, cash balance, AR/AP totals (outstanding and overdue), detailed AR/AP Aging summaries, and Current Ratio.
*   **Database Enhancements**: Schema reflects v1.0.5, including the `status` field in `business.bank_reconciliations` and related logic.
These build upon previously documented features like Payments, Audit Log UI, enhanced GST Reporting, Sales/Purchase Invoicing, and core accounting/admin functionalities.

### 1.2 Scope
This TDS covers the following aspects of the SG Bookkeeper application:
-   System Architecture: UI, business logic, data access layers, and asynchronous processing.
-   Database Schema: Details and organization as defined in `scripts/schema.sql` (reflecting v1.0.5 changes), including the `status` field in `bank_reconciliations`.
-   Key UI Implementation Patterns: `PySide6` interactions for new/enhanced banking (drafts, unmatching, history) and dashboard features (AR/AP aging, current ratio).
-   Core Business Logic: Component structures and interactions for refined bank reconciliation workflow and new KPI generation.
-   Data Models (SQLAlchemy ORM) and Data Transfer Objects (Pydantic DTOs), including their structure, purpose, and validation roles.
-   Security Implementation: Authentication, Role-Based Access Control (RBAC), and audit mechanisms including UI.
-   Deployment and Initialization procedures (technical aspects).
-   Current Implementation Status: Highlighting features implemented up to this version.

### 1.3 Intended Audience
-   Software Developers: For implementation, feature development, and understanding system design.
-   QA Engineers: For comprehending system behavior, designing effective test cases, and validation.
-   System Administrators: For deployment strategies, database setup, and maintenance.
-   Technical Project Managers: For project oversight, planning, and resource allocation.

### 1.4 System Overview
SG Bookkeeper is a cross-platform desktop application engineered with Python, utilizing PySide6 for its graphical user interface and PostgreSQL for robust data storage. It is designed to provide comprehensive accounting solutions for Singaporean Small to Medium-sized Businesses (SMBs). Key features include a full double-entry bookkeeping system, Singapore-specific GST management (including F5 return preparation with detailed export), interactive financial reporting, modules for managing essential business operations (Customers, Vendors, Products/Services, full Sales & Purchase Invoicing lifecycle, Payments with allocations), Bank Account management with manual transaction entry, CSV bank statement import, a full bank reconciliation module with draft persistence, provisional matching/unmatching capabilities, and history viewing. It also features an enhanced dashboard displaying AR/AP aging summaries and current ratio KPIs, alongside comprehensive system administration for Users, Roles, Permissions, and Audit Log viewing. The application emphasizes data integrity, compliance with local accounting standards, user-friendliness, and robust auditability.

### 1.5 Current Implementation Status
As of version 15.0 (reflecting schema v1.0.5):
*   All features listed in the previous TDS iteration (covering initial bank rec, CSV import, auto bank txns from JEs, basic dashboard) are implemented.
*   **Enhanced Banking Features (Bank Reconciliation Refinements)**:
    *   **Draft Reconciliation Persistence**: Reconciliations can be started and saved in a "Draft" state. When a user returns to a bank account/statement date combination with an existing draft, it's loaded.
    *   **Provisional Matching**: UI "Match Selected" action persists matches against the current draft reconciliation ID by updating `BankTransaction` records (`is_reconciled=True`, `reconciled_bank_reconciliation_id` set to draft's ID).
    *   **Unmatching**: UI "Unmatch Selected Items" action allows users to revert provisionally matched items within the current draft session by clearing their reconciliation linkage.
    *   **Finalization**: "Save Final Reconciliation" updates the draft reconciliation's status to "Finalized" and confirms balances.
    *   **History Viewing**: Reconciliation history list now displays only "Finalized" reconciliations, with paginated results.
*   **Enhanced Dashboard KPIs**:
    *   Displays AR Aging Summary (Current, 1-30, 31-60, 61-90, 91+ days).
    *   Displays AP Aging Summary (Current, 1-30, 31-60, 61-90, 91+ days).
    *   Displays Current Ratio.
    *   `DashboardManager` and underlying services updated to calculate these new metrics.
*   **Database**: Schema updated to v1.0.5, primarily adding `status` to `business.bank_reconciliations`.
*   **Circular Import Resolution**: Systematic fixes applied to managers, services, and `ApplicationCore` to resolve module-level circular import dependencies, primarily using conditional imports (`if TYPE_CHECKING:`) and string literal type hints.

## 2. System Architecture

### 2.1 High-Level Architecture

```
+-----------------------------------------------------------------+
|                       Presentation Layer (UI)                   |
| (PySide6: MainWindow, Module Widgets, Dialogs, TableModels)   |
| Handles User Interaction, Displays Data, Qt Signals/Slots       |
+-----------------------------------------------------------------+
      ^                         | (schedule_task_from_qt for async calls)
      | (UI Events, Pydantic DTOs) | (Results/Updates via QMetaObject.invokeMethod)
      v                         v
+-----------------------------------------------------------------+
|                  Business Logic Layer (Managers)                |
| (ApplicationCore, *Manager classes e.g., SalesInvoiceManager,  |
|  PaymentManager, JournalEntryManager, BankTransactionManager)   |
| Encapsulates Business Rules, Complex Workflows, Validation.     |
| Orchestrates Services. Returns `Result` objects.                |
+-----------------------------------------------------------------+
      ^                         | (Service Calls, SQLAlchemy ORM Objects/DTOs)
      | (Service results/ORM Objects) | (SQLAlchemy Async Operations within Services)
      v                         v
+-----------------------------------------------------------------+
|                       Data Access Layer (Services)              |
| (DatabaseManager, *Service classes e.g., AccountService,       |
|  SalesInvoiceService, BankReconciliationService), SQLAlchemy Models|
| Implements Repository Pattern. Abstracts Database Interactions. |
| Manages ORM query logic.                                        |
+-----------------------------------------------------------------+
                                | (asyncpg DB Driver)
                                v
+-----------------------------------------------------------------+
|                          Database Layer                         |
| (PostgreSQL: Schemas [core, accounting, business, audit],      |
|  Tables, Views, Functions, Triggers, Constraints)               |
+-----------------------------------------------------------------+
```

### 2.2 Component Architecture (Updates for Reconciliation Drafts & Dashboard KPIs)
The application's components are organized into core functionalities, data access services, business logic managers, and UI elements. Common utilities in `app/utils/` (like `pydantic_models.py` for DTOs, `result.py` for operation outcomes, `json_helpers.py` for data serialization between threads) and shared enumerations in `app/common/enums.py` support these layers.

#### 2.2.1 Core Components (`app/core/`)
*   **`ApplicationCore` (`application_core.py`)**:
    *   The central singleton orchestrator for the backend.
    *   Initializes and provides access to all Manager and Service instances, acting as a service locator and facilitating dependency injection.
    *   Refactored to use local imports for service instantiations within `startup()` to resolve circular dependencies. Top-level service imports removed; service types are now in `TYPE_CHECKING` block for property hints.
    *   Holds references to global `ConfigManager`, `DatabaseManager`, and logger.
*   **`DatabaseManager` (`database_manager.py`)**: Manages asynchronous PostgreSQL connections (SQLAlchemy async engine, `asyncpg` pool). Provides sessions and sets `app.current_user_id` for audit triggers.
*   **`ConfigManager` (`config_manager.py`)**: Loads and manages application settings from `config.ini`.
*   **`SecurityManager` (`security_manager.py`)**: Handles user authentication (bcrypt) and Role-Based Access Control (RBAC), including managing the `current_user` ORM object.

#### 2.2.2 Services (Data Access Layer - `app/services/`)
*   **`CustomerService` (`business_services.py`)**: Added `get_ar_aging_summary()` method.
*   **`VendorService` (`business_services.py`)**: Added `get_ap_aging_summary()` method.
*   **`AccountService` (`account_service.py`)**: Added `get_total_balance_by_account_category_and_type_pattern()` method for calculating parts of current assets/liabilities.
*   **`BankReconciliationService` (`business_services.py`)**:
    *   Modified `get_reconciliations_for_account` to filter for `status='Finalized'`.
    *   Added `get_or_create_draft_reconciliation()`: Retrieves or creates a 'Draft' reconciliation for a given bank account and statement date.
    *   Added `mark_transactions_as_provisionally_reconciled()`: Updates `BankTransaction` records to link them to a draft reconciliation and set `is_reconciled=True`.
    *   Added `finalize_reconciliation()`: Updates a 'Draft' reconciliation to 'Finalized', updates its balances, and updates the linked `BankAccount`'s last reconciled info.
    *   Added `unreconcile_transactions()`: Clears reconciliation linkage from `BankTransaction` records.
    *   The old `save_reconciliation_details` method is removed/refactored into these new methods.
    *   Added `get_transactions_for_reconciliation()`: Fetches transactions linked to a specific reconciliation ID (used for populating provisionally matched items).

#### 2.2.3 Managers (Business Logic Layer)
*   Multiple managers (e.g., `CustomerManager`, `VendorManager`, `SalesInvoiceManager`, `PurchaseInvoiceManager`, `BankAccountManager`, `BankTransactionManager`, `PaymentManager`, `GSTManager`, `FinancialStatementGenerator`) were refactored to use conditional imports (`if TYPE_CHECKING:`) and string literal type hints for their service dependencies in constructor signatures to resolve circular import issues.
*   **`DashboardManager` (`app/reporting/dashboard_manager.py`)**:
    *   `get_dashboard_kpis()` method significantly enhanced to:
        *   Call new service methods for AR/AP aging (`CustomerService.get_ar_aging_summary`, `VendorService.get_ap_aging_summary`).
        *   Calculate total current assets and liabilities by fetching active accounts (via `AccountService`) and their balances (via `JournalService`), then filtering by predefined `CURRENT_ASSET_SUBTYPES` and `CURRENT_LIABILITY_SUBTYPES` (constants defined within `DashboardManager` or a shared config).
        *   Calculate the Current Ratio.
        *   Populate the extended `DashboardKPIData` DTO.
*   **`BankTransactionManager` (`app/business_logic/bank_transaction_manager.py`)**:
    *   `get_unreconciled_transactions_for_matching()` logic remains focused on `is_reconciled=False` items, providing data for the "Unreconciled" tables in the UI.

#### 2.2.4 User Interface (Presentation Layer - `app/ui/`)
*   **`DashboardWidget` (`app/ui/dashboard/dashboard_widget.py`)**:
    *   UI updated with `QGroupBox` sections for "AR Aging Summary" and "AP Aging Summary", each containing `QLabel`s arranged with `QFormLayout` for aging buckets (Current, 1-30, 31-60, 61-90, 91+ days).
    *   A new row added for displaying "Current Ratio".
    *   Layout adjusted (e.g., using `QGridLayout`) to accommodate new KPIs, potentially using a two-column arrangement for primary KPIs and group boxes for aging summaries. `QScrollArea` may be used for scalability.
*   **`BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`)**:
    *   Manages `self._current_draft_reconciliation_id` obtained from `BankReconciliationService`.
    *   `_on_load_transactions_clicked` / `_fetch_and_populate_transactions` first calls `get_or_create_draft_reconciliation` service method. It then fetches unreconciled items (via `BankTransactionManager`) and provisionally matched items for the current draft (via `BankReconciliationService.get_transactions_for_reconciliation`).
    *   `_on_match_selected_clicked` calls a helper `_perform_provisional_match` which uses `BankReconciliationService.mark_transactions_as_provisionally_reconciled` to persist matches against the draft. Match logic enhanced to check `abs(sum_stmt_amounts - sum_sys_amounts) < tolerance`.
    *   `_on_save_reconciliation_clicked` (renamed "Save Final Reconciliation" in UI) calls `_perform_finalize_reconciliation` which uses `BankReconciliationService.finalize_reconciliation` with the draft ID.
    *   Added new UI sections ("Provisionally Matched Statement Items (This Session)", "Provisionally Matched System Transactions (This Session)") with tables (`draft_matched_statement_table`, `draft_matched_system_table`) using `ReconciliationTableModel`. A `QSplitter` is used to manage the layout of these tables.
    *   Added "Unmatch Selected Items" button (`self.unmatch_button`) and corresponding logic (`_on_unmatch_selected_clicked`, `_perform_unmatch`) to call `BankReconciliationService.unreconcile_transactions`.
    *   History list (`self.history_table`) correctly populates with finalized reconciliations and allows viewing details.

### 2.3 Technology Stack
-   **Programming Language**: Python 3.9+ (up to 3.12 supported)
-   **UI Framework**: PySide6 6.9.0+ (Qt 6 bindings)
-   **Database**: PostgreSQL 14+
-   **ORM**: SQLAlchemy 2.0+ (Asynchronous ORM)
-   **Async DB Driver**: `asyncpg`
-   **Data Validation (DTOs)**: Pydantic V2 (with `email-validator`)
-   **Password Hashing**: `bcrypt`
-   **Reporting Libraries**: `reportlab` (for PDF generation), `openpyxl` (for Excel generation/manipulation)
-   **Dependency Management**: Poetry
-   **Date/Time Utilities**: `python-dateutil`
-   **Asynchronous Programming**: `asyncio`, `threading` (for dedicated asyncio event loop)

### 2.4 Design Patterns Used
The application employs several design patterns to promote maintainability, flexibility, and separation of concerns:
-   **Layered Architecture**: Separates UI, Business Logic, and Data Access.
-   **Model-View-Controller (MVC) / Model-View-Presenter (MVP) variant**: UI widgets (View/Presenter) interact with Managers (Controller/Presenter) which use Services and Models.
-   **Repository Pattern**: Implemented by Service classes in the Data Access Layer.
-   **Data Transfer Object (DTO)**: Pydantic models are used for structured data exchange between layers, especially UI and Managers, providing validation.
-   **Result Object Pattern**: The `app/utils/result.Result` class standardizes return values from manager/service methods.
-   **Observer Pattern**: Qt's Signal/Slot mechanism for communication within the UI and between UI and backend callback handlers.
-   **Dependency Injection (Conceptual)**: `ApplicationCore` initializes and provides dependencies (services to managers, managers to UI layers indirectly).
-   **Singleton (Conceptual)**: `ApplicationCore` and its managed service/manager instances behave as singletons within the application's context.
-   **Mixin Classes**: Used for ORM models (`TimestampMixin`, `UserAuditMixin`) to share common fields and functionalities.

### 2.5 Asynchronous Processing Model
To ensure UI responsiveness, particularly during database operations or complex calculations, SG Bookkeeper uses an asynchronous processing model:
1.  A dedicated Python `threading.Thread` (`_ASYNC_LOOP_THREAD` in `app/main.py`) runs a persistent `asyncio` event loop (`_ASYNC_LOOP`), separate from the Qt GUI event loop.
2.  UI actions that require backend processing (e.g., fetching data, saving records) schedule an `async` coroutine (typically a manager method) onto this dedicated asyncio loop using the `schedule_task_from_qt(coroutine)` utility. This uses `asyncio.run_coroutine_threadsafe`.
3.  The manager method, now executing in the asyncio thread, performs its operations, which may include calling `async` service methods that interact with the database via `asyncpg` and SQLAlchemy's async features.
4.  Upon completion of the asynchronous task, results or data intended for UI updates are marshaled back to the Qt main GUI thread. This is typically done using `QMetaObject.invokeMethod(target_widget, "slot_name", Qt.ConnectionType.QueuedConnection, Q_ARG(type, data))`. Data passed between threads (e.g., DTOs) is often serialized to JSON (using `app/utils/json_helpers.py`) to ensure thread safety and compatibility with `Q_ARG`.
5.  The designated slot method in the UI widget then safely updates the UI components with the received data.

This architecture prevents the GUI from freezing during potentially long-running backend operations, enhancing user experience.

## 3. Data Architecture (Updates based on Schema v1.0.5)

### 3.1 Database Schema Overview
*   The database schema is now at version **1.0.5**, defined in `scripts/schema.sql`.
*   Key table for recent enhancements: **`business.bank_reconciliations`**:
    *   Now includes a `status VARCHAR(20) NOT NULL DEFAULT 'Draft'` column with a `CHECK` constraint (`status IN ('Draft', 'Finalized')`). This is central to managing the lifecycle of a reconciliation process, allowing users to save drafts and finalize them later.
*   Related changes:
    *   `business.bank_accounts` includes `last_reconciled_balance NUMERIC(15,2) NULL`.
    *   `business.bank_transactions` includes `reconciled_bank_reconciliation_id INT NULL` as a foreign key to `business.bank_reconciliations`.

### 3.2 SQLAlchemy ORM Models (`app/models/`)
*   **`app/models/business/bank_reconciliation.py`**: The `BankReconciliation` ORM model is updated to include the `status: Mapped[str]` field, corresponding to the database schema change.
*   **ORM Style and Base Classes**:
    *   Models use SQLAlchemy 2.0 style with `Mapped` and `mapped_column` annotations for type safety and clarity.
    *   Common functionalities are inherited from base/mixin classes in `app/models/base.py`:
        *   `Base`: The declarative base for all models.
        *   `TimestampMixin`: Provides `created_at` and `updated_at` columns with automatic server-side timestamp management.
        *   `UserAuditMixin`: Provides `created_by_user_id` and `updated_by_user_id` columns (linking to `core.users.id`) for tracking data modifications.

### 3.3 Data Transfer Objects (DTOs - `app/utils/pydantic_models.py`)
*   **`DashboardKPIData`**: Extended to include new fields for AR/AP aging summaries and current ratio metrics:
    *   `ar_aging_current`, `ar_aging_1_30`, `ar_aging_31_60`, `ar_aging_61_90`, `ar_aging_91_plus`
    *   `ap_aging_current`, `ap_aging_1_30`, `ap_aging_31_60`, `ap_aging_61_90`, `ap_aging_91_plus`
    *   `total_current_assets`, `total_current_liabilities`
    *   `current_ratio`
*   Pydantic DTOs are extensively used for validating data passed from the UI to managers and for structuring data returned to the UI.

### 3.4 Data Access Layer Interfaces (`app/services/__init__.py`)
Interface definitions for services are updated to reflect new functionalities:
*   **`IBankAccountRepository`**: Added `async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: pass`.
*   **`ICustomerRepository`**: Added `async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass`.
*   **`IVendorRepository`**: Added `async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass`.
*   **`IAccountRepository`**: Added `async def get_total_balance_by_account_category_and_type_pattern(self, account_category: str, account_type_name_like: str, as_of_date: date) -> Decimal: pass`.
*   **`IBankReconciliationRepository`**:
    *   Added `async def get_or_create_draft_reconciliation(...) -> BankReconciliation: pass`.
    *   Added `async def mark_transactions_as_provisionally_reconciled(...) -> Result: pass`.
    *   Added `async def finalize_reconciliation(...) -> Result: pass`.
    *   Added `async def unreconcile_transactions(...) -> Result: pass`.
    *   Added `async def get_transactions_for_reconciliation(...) -> List[BankTransaction]: pass`.
    *   Old `save_reconciliation_details` interface method removed.

## 4. Module and Component Specifications

### 4.1 Core Accounting Module (`app/accounting/`, `app/ui/accounting/`)
-   **Chart of Accounts**: Hierarchical account management.
    -   Manager: `ChartOfAccountsManager`. Service: `AccountService`. UI: `ChartOfAccountsWidget`, `AccountDialog`.
-   **Journal Entries**: Manual journal entry creation and management.
    -   Manager: `JournalEntryManager`. Service: `JournalService`. UI: `JournalEntriesWidget`, `JournalEntryDialog`.
    *   `JournalEntryManager.post_journal_entry` now automatically creates a system `BankTransaction` if a journal line debits or credits a GL account linked to a `BankAccount`. This facilitates bank reconciliation by ensuring such internal movements are available for matching.
-   **Fiscal Period Management**: Setup and control of fiscal years/periods.
    -   Manager: `FiscalPeriodManager`. Services: `FiscalYearService`, `FiscalPeriodService`. UI: In `SettingsWidget`, `FiscalYearDialog`.

### 4.2 Tax Management Module (`app/tax/`, `app/ui/reports/`)
-   **GST Management**:
    *   Manager: `GSTManager` (prepares `GSTReturnData` DTO including `detailed_breakdown` of `GSTTransactionLineDetail` objects for F5 boxes, saves draft, finalizes with settlement JE).
    *   Service: `TaxCodeService`, `GSTReturnService`.
    *   UI: `ReportsWidget` (GST F5 tab) includes "Export Details (Excel)" for detailed breakdown.
-   **Tax Calculation**: `TaxCalculator` service (`calculate_line_tax`) used by invoice managers.

### 4.3 Business Operations Modules (`app/business_logic/`, `app/ui/.../`)
-   **Customer, Vendor, Product/Service Management**: Full CRUD and list views.
    -   Managers: `CustomerManager`, `VendorManager`, `ProductManager`. Services: `CustomerService`, `VendorService`, `ProductService`. UI: `CustomersWidget`, `VendorsWidget`, `ProductsWidget`, respective dialogs.
-   **Sales Invoicing Module**: Full lifecycle.
    -   Manager: `SalesInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `SalesInvoiceService`. UI: `SalesInvoicesWidget`, `SalesInvoiceDialog`.
-   **Purchase Invoicing Module**: Full lifecycle.
    -   Manager: `PurchaseInvoiceManager` (validation, calculations, draft CRUD, posting with financial & inventory JEs). Service: `PurchaseInvoiceService`. UI: `PurchaseInvoicesWidget`, `PurchaseInvoiceDialog`.

### 4.4 System Administration Modules (`app/core/security_manager.py`, `app/ui/settings/`, `app/ui/audit/`)
-   **User Management**:
    -   Manager: `SecurityManager`. UI: `UserManagementWidget`, `UserDialog`, `UserPasswordDialog`.
-   **Role & Permission Management**:
    -   Manager: `SecurityManager`. UI: `RoleManagementWidget`, `RoleDialog`.
-   **Audit Log Viewing**:
    -   Service: `AuditLogService` (fetches `AuditLog`, `DataChangeHistory` with pagination/filtering). UI: `AuditLogWidget` in `SettingsWidget` with "Action Log" and "Data Change History" tabs. Minor improvements to change summary formatting.

### 4.5 Reporting Module (`app/reporting/`, `app/ui/reports/`)
-   **Financial Statements**: Generation and export (BS, P&L, TB, GL).
    -   Manager: `FinancialStatementGenerator`, `ReportEngine` (PDF/Excel export with enhanced formatting). UI: Financial Statements tab in `ReportsWidget`.

### 4.6 Dashboard Module (Enhanced) (`app/reporting/dashboard_manager.py`, `app/ui/dashboard/`)
-   **Purpose**: Provide a quick overview of key financial metrics.
-   **Manager (`DashboardManager`)**:
    *   `get_dashboard_kpis()`:
        *   Retrieves YTD Revenue, Expenses, Net Profit (via `FinancialStatementGenerator`).
        *   Calculates Current Cash Balance (sum of base currency active bank accounts via `BankAccountService` and `JournalService`).
        *   Retrieves Total Outstanding AR/AP (via `CustomerService`/`VendorService` or GL balances).
        *   Fetches AR/AP aging summaries (Current, 1-30, 31-60, 61-90, 91+ days) from `CustomerService.get_ar_aging_summary` and `VendorService.get_ap_aging_summary`.
        *   Calculates Total Current Assets and Total Current Liabilities by:
            1.  Fetching all active accounts from `AccountService`.
            2.  Iterating and summing balances (via `JournalService.get_account_balance_by_type_and_subtype` or similar, using `AccountService.get_total_balance_by_account_category_and_type_pattern`) for accounts whose types/subtypes match predefined lists for current assets/liabilities (e.g., `CURRENT_ASSET_SUBTYPES`, `CURRENT_LIABILITY_SUBTYPES` constants).
        *   Calculates Current Ratio (`Total Current Assets / Total Current Liabilities`), handling division by zero.
        *   Populates the extended `DashboardKPIData` DTO with all these metrics.
-   **UI (`DashboardWidget`)**:
    *   Displays all KPIs fetched from `DashboardManager`.
    *   Includes dedicated `QGroupBox` sections with `QFormLayout` for AR Aging Summary and AP Aging Summary, showing the different aging buckets.
    *   Displays the Current Ratio.
    *   Layout uses `QGridLayout` for organization and `QScrollArea` for better viewing of content.
    *   Includes a "Refresh KPIs" button.

### 4.7 Banking Module (Refined Bank Reconciliation Workflow)
-   **Purpose**: Enables users to reconcile bank account statements with system bank transactions, manage discrepancies, and maintain an audit trail of reconciliations.
-   **Key Features**:
    *   **Draft Persistence**: Reconciliations can be started, partially completed, and saved as a 'Draft'. Users can resume these drafts later.
    *   **Provisional Matching**: Users can select and match statement items with system transactions. These matches are persisted against the current draft reconciliation.
    *   **Unmatching**: Provisionally matched items can be unmatched within the draft session.
    *   **Adjustment Journal Entries**: Facilitates creation of JEs for items appearing only on the bank statement (e.g., bank charges, interest earned). These JEs auto-create corresponding system bank transactions.
    *   **Finalization**: Once reconciled (difference is zero), the draft can be finalized, updating its status and the bank account's last reconciled details.
    *   **History**: A paginated history of all "Finalized" reconciliations is viewable, with details of cleared transactions.
-   **Core UI Component**: `BankReconciliationWidget` (`app/ui/banking/bank_reconciliation_widget.py`).
-   **Key Service**: `BankReconciliationService` (`app/services/business_services.py`) handles the lifecycle of reconciliations (draft creation, provisional matching/unmatching, finalization). It uses methods like `get_or_create_draft_reconciliation`, `mark_transactions_as_provisionally_reconciled`, `unreconcile_transactions`, and `finalize_reconciliation`. It also provides `get_transactions_for_reconciliation` to load items already matched to a draft.
-   **Supporting Services/Managers**:
    *   `BankTransactionManager`: Fetches unreconciled bank transactions via `get_unreconciled_transactions_for_matching`.
    *   `JournalEntryManager`: Used for creating adjustment JEs, which in turn can generate new system bank transactions.
    *   `BankAccountService`: Provides bank account details.
-   The detailed step-by-step data flow for the reconciliation process is outlined in Section 9.2.

## 5. User Interface Implementation (`app/ui/`) (Updates)
*   **`DashboardWidget`**:
    *   Uses `QGridLayout` to arrange KPIs into columns and sections for better visual organization.
    *   Introduced `QGroupBox` elements for "AR Aging Summary" and "AP Aging Summary", utilizing `QFormLayout` within them to display aging bucket labels and values.
    *   A specific `QLabel` is dedicated to displaying the "Current Ratio".
    *   Encased within a `QScrollArea` to handle varying content sizes and improve usability on smaller screens.
*   **`BankReconciliationWidget`**:
    *   Incorporates two new `QGroupBox` sections, each containing a `QTableView` (populated by `ReconciliationTableModel`), for "Provisionally Matched Statement Items (This Session)" and "Provisionally Matched System Transactions (This Session)". This clearly separates items actively being worked on in the current draft.
    *   A `QSplitter` is employed to allow users to dynamically resize the areas dedicated to unreconciled tables versus provisionally matched tables.
    *   Includes a new "Unmatch Selected Items" button to revert provisional matches.
    *   The button for saving the final reconciliation is labeled "Save Final Reconciliation".
    *   Maintains internal state for `_current_draft_reconciliation_id` to manage context across operations.

## 6. Security Considerations
-   **Authentication**: User login handled by `SecurityManager` using `bcrypt` for password hashing and salting. Failed login attempts are tracked; accounts can be configured for lockout.
-   **Authorization (RBAC)**: A granular permission system (`core.permissions`, `core.roles`, `core.user_roles`, `core.role_permissions` tables) is enforced by `SecurityManager.has_permission()`. The "Administrator" role has all permissions and is protected.
-   **Audit Trails**: Comprehensive database-level audit logging is implemented via PL/pgSQL triggers (e.g., `audit.log_data_change_trigger_func`). The `DatabaseManager` sets the `app.current_user_id` session variable in PostgreSQL, which is captured by these triggers. Data is stored in `audit.audit_log` (action summaries) and `audit.data_change_history` (field-level changes). A UI for viewing these logs is provided.
-   **Data Integrity**: Enforced by database constraints (PK, FK, CHECK, UNIQUE, NOT NULL), Pydantic DTO validation at the boundary between UI and Business Logic Layer, and business rule validation within Manager classes.

## 7. Database Access Implementation
-   **`DatabaseManager`**: Manages the SQLAlchemy asynchronous engine and `asyncpg` connection pool. Provides `AsyncSession` instances through an `asynccontextmanager` (`session()`).
-   **Services (Repository Pattern)**: Service classes (e.g., `AccountService`, `SalesInvoiceService`, `BankReconciliationService`) encapsulate all data access logic for specific ORM models or related groups of models. They use SQLAlchemy's async session for all database operations.
-   **ORM Models (`app/models/`)**: Define the mapping between Python objects and database tables, including relationships, constraints, and potentially model-level behavior via mixins (e.g., `TimestampMixin`, `UserAuditMixin`).
-   **Transactions**: Multi-step database operations (e.g., invoice posting, payment recording, provisional matching/unmatching of bank transactions, and finalization of bank reconciliations) are handled within a single database session (`async with db_manager.session():`) managed by the relevant manager or service methods to ensure atomicity. For instance, `BankReconciliationService.finalize_reconciliation` ensures that updating the `BankReconciliation` record (e.g., status to 'Finalized', balance figures) and the parent `BankAccount`'s last reconciled information occurs as a single atomic unit. Similarly, methods like `mark_transactions_as_provisionally_reconciled` and `unreconcile_transactions` ensure their respective updates to `BankTransaction` records are atomic.

## 8. Deployment and Installation
-   **Prerequisites**: Python 3.9+, PostgreSQL 14+, Poetry.
-   **Setup**:
    1.  Clone repository.
    2.  Install dependencies: `poetry install`.
    3.  Configure database connection in `config.ini` (located in a platform-specific user config directory). Create `config.ini` from `config.example.ini` if it doesn't exist, ensuring correct database credentials and name.
    4.  Initialize database: `poetry run sg_bookkeeper_db_init --user <pg_admin_user> ...`. This executes `scripts/schema.sql` (DDL, v1.0.5) and `scripts/initial_data.sql` (seeding roles, permissions, default user, system accounts, etc.).
-   **Execution**: `poetry run sg_bookkeeper`.
-   Refer to `README.md` and potentially a separate `deployment_guide.md` for more detailed user-facing instructions.

## 9. Data Flow Examples

### 9.1 Data Flow Example: Sales Invoice Posting
1.  **UI (`SalesInvoiceDialog`)**: User completes invoice details (customer, items, quantities, dates), clicks "Save & Approve".
2.  **Data Collection & DTO (UI/Manager)**: UI data (header, lines) gathered into `SalesInvoiceCreateData` DTO.
3.  **Manager (`SalesInvoiceManager.create_and_post_invoice`)**:
    *   Receives DTO. Performs validations (fiscal period open, customer valid, product valid, quantities available for inventory items).
    *   Calculates line totals, subtotals, tax amounts (using `TaxCalculator`), and grand total.
    *   Generates unique invoice number (via `SequenceService` or equivalent DB function).
    *   Calls `SalesInvoiceService.create_invoice_from_dto()` to save `SalesInvoice` and `SalesInvoiceLine` ORM objects to database (typically as a draft first).
4.  **Financial Journal Entry (Manager: `JournalEntryManager`)**:
    *   If invoice saved successfully, `SalesInvoiceManager` prepares data for financial JE (Debit Accounts Receivable, Credit Sales Revenue, Credit GST Payable).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` with JE data. This validates, creates, and posts the JE, updating account balances.
5.  **Inventory Journal Entry (Manager: `JournalEntryManager`, Service: `ProductService`)**:
    *   If invoice includes inventory items, `SalesInvoiceManager` calculates Cost of Goods Sold (COGS) using Weighted Average Cost (WAC) from `ProductService` (or `inventory_summary` view).
    *   Prepares data for COGS JE (Debit COGS, Credit Inventory).
    *   Calls `JournalEntryManager.create_and_post_journal_entry()` for COGS JE.
    *   `InventoryMovement` records are also created.
6.  **Invoice Status Update (Service: `SalesInvoiceService`)**:
    *   `SalesInvoiceManager` calls `SalesInvoiceService` to update the invoice's status to "Posted" (or similar) and links the main financial JE ID.
7.  **UI Feedback**: Success message. Sales invoice list view updates.

### 9.2 Data Flow Example: Bank Reconciliation Process (Refined)
1.  **Setup (UI: `BankReconciliationWidget`)**: User selects Bank Account, Statement Date, enters Statement Ending Balance. Clicks "Load / Refresh Transactions".
2.  **Get/Create Draft & Fetch Data (Widget -> Service/Manager)**:
    *   The widget's `_fetch_and_populate_transactions` method (or similar handler) is invoked.
    *   It calls `BankReconciliationService.get_or_create_draft_reconciliation`, passing bank account ID, statement date, and the statement ending balance from the UI. The service returns a `BankReconciliation` ORM object (the draft) and its ID is stored in `self._current_draft_reconciliation_id`. The UI statement balance is updated if the loaded draft had a different persisted balance.
    *   The widget fetches the current GL balance for the bank account's linked GL account (via `JournalService.get_account_balance`).
    *   It fetches unreconciled transactions (`is_reconciled=False`) for the bank account up to the statement date via `BankTransactionManager.get_unreconciled_transactions_for_matching`. These populate the "Unreconciled" tables.
    *   It fetches transactions already provisionally matched to the current `_current_draft_reconciliation_id` via `BankReconciliationService.get_transactions_for_reconciliation`. These populate the "Provisionally Matched (This Session)" tables.
3.  **Display & Calculate (UI)**: The UI populates all tables. The initial "Reconciliation Summary" (Difference, Adjusted Book Balance, etc.) is calculated based on the statement ending balance, current GL balance, and the sum of *unreconciled* items (as provisionally matched items are considered 'cleared' for the draft).
4.  **User Interaction - Provisional Matching (UI -> Service)**:
    *   User selects one or more items from the "Unreconciled Bank Statement Items" table and one or more items from the "Unreconciled System Transactions" table.
    *   User clicks "Match Selected".
    *   The UI validates if the sum of selected statement item amounts equals the sum of selected system transaction amounts (within a small tolerance).
    *   If valid, `_perform_provisional_match` calls `BankReconciliationService.mark_transactions_as_provisionally_reconciled` with the `_current_draft_reconciliation_id` and lists of selected statement and system transaction IDs. The service updates these `BankTransaction` records in the DB (sets `is_reconciled=True`, `reconciled_date` to statement date, and `reconciled_bank_reconciliation_id` to the draft's ID).
    *   UI reloads all transaction lists (effectively re-running step 2). Matched items now appear in "Provisionally Matched" tables. The summary recalculates.
5.  **User Interaction - Unmatching (UI -> Service)**:
    *   User selects one or more items from the "Provisionally Matched Statement Items (This Session)" table and/or "Provisionally Matched System Transactions (This Session)" table.
    *   User clicks "Unmatch Selected Items".
    *   `_perform_unmatch` calls `BankReconciliationService.unreconcile_transactions` with the IDs of the selected transactions. The service updates these `BankTransaction` records in the DB (sets `is_reconciled=False`, clears `reconciled_date` and `reconciled_bank_reconciliation_id`).
    *   UI reloads all transaction lists. Unmatched items move back to "Unreconciled" tables. Summary recalculates.
6.  **User Interaction - New JE for Statement Item (UI -> Manager -> Service)**:
    *   User selects an unmatched bank statement item (e.g., a bank charge not yet in books). Clicks "Add Journal Entry".
    *   `JournalEntryDialog` opens, possibly pre-filled (e.g., credit Bank GL Account, debit Bank Charge Expense).
    *   User completes and posts the JE via `JournalEntryManager`. This manager, upon posting a JE affecting a bank-linked GL account, automatically creates a new system `BankTransaction`.
    *   UI reloads transaction lists. The newly created system `BankTransaction` appears in the "Unreconciled System Transactions" table, ready for matching.
7.  **Finalizing (UI -> Service)**:
    *   When the "Difference" in the reconciliation summary is zero (or within acceptable tolerance), the user clicks "Save Final Reconciliation".
    *   `_perform_finalize_reconciliation` calls `BankReconciliationService.finalize_reconciliation` with the current `_current_draft_reconciliation_id`, the final statement ending balance, the calculated book balance, and the difference.
    *   The service updates the `BankReconciliation` record's `status` to "Finalized", updates its `statement_ending_balance`, `calculated_book_balance`, `reconciled_difference`, and `reconciliation_date`. It also updates the linked `BankAccount` record's `last_reconciled_date` and `last_reconciled_balance`. All these DB operations occur within a single transaction.
8.  **UI Feedback**: Success/error message. The UI typically clears the current reconciliation workspace or resets for a new one. The "Reconciliation History" list is refreshed.

## 10. Conclusion (Updated)
Version 15 of SG Bookkeeper significantly refines the Bank Reconciliation module by introducing persistent draft sessions with provisional matching and unmatching capabilities, leading to a more robust and user-friendly reconciliation experience. The Dashboard has been enhanced with crucial AR/AP Aging summaries and the Current Ratio, providing deeper financial insights at a glance. Continuous architectural improvements, such as the resolution of circular import dependencies, strengthen the codebase's maintainability and stability. These features further solidify SG Bookkeeper as a comprehensive accounting tool for SMBs. Future work will focus on expanding automated test coverage, potentially handling more complex reconciliation matching scenarios (e.g., many-to-one), and further enriching dashboard and reporting functionalities based on user feedback and evolving business needs.
```

---
https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221C3YLnRKPRGzPZnYLR1QTk7UWEwAsh3Nz%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1Ca9966PXKMDnjAxCsyT8OmVM2CPRlb-7/view?usp=sharing, https://drive.google.com/file/d/1ZsmOW6huYvGv9eyPviU1VZzh2YZqtxgW/view?usp=sharing, https://drive.google.com/file/d/1azUf7bWoZO_Niu3T7P81Vg8osVNEAvdG/view?usp=sharing, https://drive.google.com/file/d/1bI33CCtQPwhzoEUl854m3V002dxflsWg/view?usp=sharing, https://drive.google.com/file/d/1eFLuD4rI0YIctcHcXtE_aGXdEI19KS7A/view?usp=sharing, https://drive.google.com/file/d/1i0d3rPoQdMDESiN3d1xl0HwlhxsW8IKA/view?usp=sharing, https://drive.google.com/file/d/1peEbFNwTqJse_rI4-Cr6AHJC5VkdMEyJ/view?usp=sharing, https://drive.google.com/file/d/1wiAxnIzKK89xeuNXnUIwze7jX3IRpmh0/view?usp=sharing


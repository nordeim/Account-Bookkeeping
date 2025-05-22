# Product Requirements Document  (o3, v2)
## Singapore Small Business Bookkeeping Application (“LumiLedger 2.0”)

---

### 0. Executive Summary
LumiLedger 2.0 is a cross-platform desktop bookkeeping suite that allows Singapore micro- and small-enterprise operators to keep fully compliant double-entry books, generate statutory GST & income-tax artefacts, and obtain real-time financial insight—all without needing accounting expertise.  
Built with Python 3.11 + PySide 6 (Qt 6) and a bundled, encrypted PostgreSQL 15 datastore, the application targets Windows 10/11, macOS 13 +, and Ubuntu 22.04 +. Its design philosophy: **zero-friction data entry, strong compliance guard-rails, and delightful modern UX.**

---

## 1. Goals, Objectives & Success Metrics
| Goal | Objective (SMART) | KPI / Target |
|------|--------------------|--------------|
| G1: Simplify bookkeeping | Reduce average transaction-entry time for non-accountant users | ≤ 25 s per entry (50 % faster than spreadsheets) |
| G2: Ensure compliance | Provide out-of-the-box SFRS chart & IRAS tax pack | 100 % field-level mapping coverage |
| G3: Improve visibility | 1-click generation of core financial statements | < 3 s render for 100 k transactions |
| G4: Protect data | Automatic encrypted backups | Zero data-loss incidents in beta period |
| G5: Delight users | Reduce support tickets | ≤ 1 ticket / 10 active users / month |

---

## 2. Target Users & Personas
| Persona | Goals | Frustrations |
|---------|-------|--------------|
| Amanda – Café Owner | Quick daily sales logging, GST filing | Hates journal jargon |
| Brian – Freelance Designer | Track deductible expenses, generate Form B schedules | Loses receipts |
| Cheryl – Contract Accountant | Serve 5 SMEs concurrently | Juggling spreadsheets, no audit trail |
| Dev – External Consultant | Needs read-only access to P&L | Version chaos, data sent over email |

---

## 3. Scope

### 3.1 In-Scope (MVP + v1.1)
1. Company lifecycle (create, edit FY, close books, archive).
2. Pre-seeded SFRS 2022 Chart of Accounts (CoA) with code ranges.
3. Double-Entry Engine — atomic balancing, accrual basis only.
4. AP / AR modules with invoice, credit-note, payment, ageing.
5. Bank Statement Import (CSV/OFX) & rule-based reconciliation.
6. GST Module  
   • Support TX, SR, ZF, EX, IM, OS, ME, RC codes  
   • Automatic F5 generation with two-tier rounding, offset logic  
7. Financial Statements (P&L, Balance Sheet, Cash-Flow, Equity).
8. IRAS Income-Tax Pack (Form C-S/C) export in Excel + PDF.
9. Multi-company switcher (schema-per-company in same DB cluster).
10. Role-based Access Control (Owner, Accountant, Staff, External).
11. Offline-first encrypted backups, restore wizard.
12. Dark/Light themes, screen-reader labels, font scaling.

### 3.2 Out-of-Scope (Future)
• Payroll & CPF, Peppol e-Invoicing, cloud sync, mobile companion, SGFinDex feeds.

---

## 4. Functional Requirements

### 4.1 Company Setup Wizard
FR-1: Capture UEN, FY start/end, GST registration date, functional currency (SGD default, multi-currency flag).  
FR-2: Allow import of Chart of Accounts template or custom CSV.

### 4.2 Transaction Entry
FR-3: “Guided” entry form (natural language–friendly) with auto-fill:  
  Example: “Rent 2500 to Office Rent” → parses amount, account, GST = ZF.  
FR-4: Live debit/credit equality indicator.  
FR-5: Bulk journal import (CSV) with column mapper & preview diff.

### 4.3 AP / AR
FR-6: Generate sequential invoice numbers (configurable prefix).  
FR-7: Track payment status; support partial & multi-currency payments (Phase 1: conversational FX rate entry, behind-the-scenes triangulation to SGD).  
FR-8: Print / email invoice PDF with IRAS-compliant format.

### 4.4 Bank Reconciliation
FR-9: Statement ingestion (CSV, OFX).  
FR-10: Matching engine using rules (Amount ± S$0.50, date ± 3 d, memo fuzzy match).  
FR-11: User can confirm, split or create new transactions from unmatched lines.

### 4.5 GST
FR-12: Assign GST code at line level; persistent mapping table (Supplier → IM).  
FR-13: Generate GST F5 with breakdown boxes 1–14, plus annex.  
FR-14: Perform two-tier rounding (0.50 to 1) per IRAS guide.  
FR-15: Produce audit file (IAF XML) flag ready; implemented in Phase 1.1.

### 4.6 Reporting
FR-16: Standard statements with comparative periods.  
FR-17: Drill-down from statements → source journal.  
FR-18: Customisable management dashboards (graphs) – embed matplotlib/QtCharts.

### 4.7 Data Import / Export
FR-19: Export ledgers to Excel, CSV.  
FR-20: One-click IRAS tax pack: P&L, Schedules 1–5, Capital Allowances.  
FR-21: XBRL (BizFinx) template CSV generator (Phase 1.1).

### 4.8 Security & Backup
FR-22: Master passphrase-derived AES-256 key; key never stored in plaintext.  
FR-23: Auto-lock after 10 min idle; unlock re-prompts passphrase/OS biometrics.  
FR-24: Nightly encrypted snapshot (pg_dump) with optional S3/Google Drive push.

---

## 5. Non-Functional Requirements

| Category      | Requirement |
|---------------|-------------|
| Performance   | < 200 ms UI action latency; < 3 s report render on 100 k txns / 8 GB RAM machine |
| Availability  | Desktop app: 99.9 % uptime; recover on crash in < 5 s |
| Reliability   | ACID compliance via PostgreSQL; transaction journaling |
| Security      | OWASP Top-10 desktop mitigations; CODE-SIGNED installers |
| Usability     | Onboarding ≤ 15 min; WCAG 2.1 AA accessibility |
| Portability   | Single source base; PyInstaller‐packaged; no admin rights needed |
| Extensibility | Plugin loader (entry-point “lumiledger.plugins”) |

---

## 6. Technical Architecture

### 6.1 Runtime Stack
Frontend        : Python 3.11, PySide6 (Qt 6)  
State Mgmt      : MVVM pattern (Pydantic models as Observable Layer)  
Backend ORM     : SQLModel (SQLAlchemy 2 core) – Async not required (local DB)  
Database        : PostgreSQL 15 (bundled, runs on non-privileged port 6543)  
Encryption      : pgcrypto extension; tablespace-level LUKS optional  
Reporting       : Jinja2 ➜ HTML ➜ Qt WebEngine ➜ PDF export  
Packaging       : PyInstaller + Qt6 plug-in collector; NSIS (Win), DMG (mac), AppImage (Linux)

### 6.2 Layered Diagram (textual)
[UI(QML widgets)] ⇄ [ViewModels] ⇄ [Service Layer] ⇄ [Repository / ORM] ⇄ [PostgreSQL]  
                          ↑                                               ↕︎  
        [Plugin API (entry-points)]                [pgcrypto / backup engine]

### 6.3 Core Services
| Service | Key Public Methods |
|---------|--------------------|
| AccountingService | post_journal(), get_trial_balance(fy_id), close_period() |
| GSTService | calc_return(fy_qtr), export_f5_pdf(), export_iaf() |
| InvoiceService | create_invoice(), record_payment(), aging_report() |
| ImportService | parse_bank_csv(file), suggest_matches(), commit_matches() |
| BackupService | run_snapshot(), restore(path), verify_checksum() |

### 6.4 Event Bus
Qt signals: domain events (JournalPosted, InvoicePaid) broadcast → UI refresh & plugin hooks.

---

## 7. Data Model (DDL Snippet)

```sql
CREATE TABLE company (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  uen CHAR(9) UNIQUE NOT NULL,
  gst_registered BOOLEAN DEFAULT FALSE,
  fy_start DATE NOT NULL,
  fy_end DATE NOT NULL
);

CREATE TABLE account (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES company(id),
  code VARCHAR(10) NOT NULL,
  name TEXT,
  type VARCHAR(20) CHECK (type IN ('ASSET','LIABILITY','EQUITY','REVENUE','EXPENSE')),
  gst_code CHAR(2) DEFAULT NULL,
  UNIQUE(company_id, code)
);

CREATE TABLE journal_entry (
  id UUID PRIMARY KEY,
  company_id UUID REFERENCES company(id),
  ref TEXT,
  doc_date DATE,
  description TEXT,
  posted_at TIMESTAMP DEFAULT NOW(),
  posted_by UUID REFERENCES "user"(id)
);

CREATE TABLE journal_line (
  id UUID PRIMARY KEY,
  entry_id UUID REFERENCES journal_entry(id) ON DELETE CASCADE,
  account_id UUID REFERENCES account(id),
  debit NUMERIC(14,2) DEFAULT 0,
  credit NUMERIC(14,2) DEFAULT 0,
  gst_code CHAR(2)
);

-- Constraint to ensure entry balances
CREATE OR REPLACE FUNCTION assert_entry_balanced() RETURNS TRIGGER AS $$
BEGIN
  IF (SELECT COALESCE(SUM(debit),0) - COALESCE(SUM(credit),0)
        FROM journal_line WHERE entry_id = NEW.entry_id) <> 0 THEN
       RAISE EXCEPTION 'Unbalanced journal %', NEW.entry_id;
  END IF;
  RETURN NEW;
END; $$ LANGUAGE plpgsql;
```

(Full ERD attached in Appendix A).

---

## 8. Roles & Permissions Matrix

| Module / Action           | Owner | Accountant | Staff | External |
|---------------------------|:-----:|:----------:|:-----:|:--------:|
| Company Settings          | CRUD  | R          | –     | – |
| Post Journal              | C/R/U | C/R        | C     | – |
| Approve Journal           | A     | A          | –     | – |
| Invoice                   | CRUD  | CRUD       | C/R   | R |
| Bank Reconciliation       | CRUD  | CRUD       | R     | – |
| GST Filing                | A     | A          | –     | – |
| Financial Reports         | R     | R          | R     | R |
Legend: C=create, R=read, U=update, D=delete, A=approve.

---

## 9. UI / UX Specifications

### 9.1 Navigation
Left vertical navigation rail with icons: Dashboard, Sales, Purchases, Banking, GST, Reports, Settings.

### 9.2 Design Tokens
• Primary colour: #006DCC (SG blue), secondary: #F57C00 (accent).  
• Typography: Inter / Noto Sans, min 12 pt.  
• Spacing: 8 px grid.  
• Theme JSON exported for Qt StyleSheet generation.

### 9.3 Key Screens
1. **Home → Dashboard**  
   – KPI cards (Revenue MTD, Expenses MTD, Cash on Hand).  
   – Chart: Monthly P&L.  
2. **Transactions List**  
   – Virtualised table, 50 fps scroll on 100 k rows.  
   – Column filter bar, fuzzy search.  
3. **Invoice Editor**  
   – Left: Header (client, dates).  
   – Central grid: line items with GST dropdown.  
   – Right sidebar: totals, attachment drag-and-drop.  
4. **GST F5 Preview**  
   – Box 1–14 grid; clicking cell shows supporting transactions.  
   – “File Now” opens IRAS-myTax Portal link with generated XML ready (Phase 1.1).

Wireframes: see Figma link “LumiLedger 2.0 UX v3”.

---

## 10. Workflows (Happy Path)

### 10.1 Daily Sales Entry (Retail POS import)
1. Admin imports CSV from POS → ImportService.parse_bank_csv.  
2. System auto-detects “Sales” → maps to revenue account 4000.  
3. GST code defaults to SR (7 %).  
4. Preview diff → user confirms → AccountingService.post_journal.  
5. JournalPosted event triggers dashboard refresh.

### 10.2 GST Filing
1. User selects “GST → Prepare Return”.  
2. GSTService.calc_return fetches QN transactions.  
3. Preview window shows breakdown, rounding deltas.  
4. User clicks “Lock Period”. Entries after lock can’t change code.  
5. Export PDF & Excel; optionally push XML to IRAS (future).

---

## 11. Validation Rules / Business Logic

| Rule ID | Description |
|---------|-------------|
| VAL-01 | Journal must balance to zero (trigger see §6). |
| VAL-02 | No back-dating beyond closed period unless Owner override. |
| VAL-03 | GST code required for all PL accounts if company GST-registered. |
| VAL-04 | FX entry must contain rate (to 6 dp) on transaction date. |
| VAL-05 | Sequential invoice numbers; gaps flagged in audit report. |

---

## 12. Error Handling & Logging
• QtMessageHandler redirects to rotating log (10 MB × 5) at `%APPDATA%/LumiLedger/logs`.  
• Critical exceptions → Sentry SDK if user opts-in.  
• Graceful UI toast for recoverable errors; blocking modal for critical rollbacks.

---

## 13. Testing Strategy

| Layer          | Tooling                       | Coverage Goal |
|----------------|------------------------------|---------------|
| Unit           | pytest + hypothesis           | 90 % of services |
| DB Migration   | pytest-postgres fixtures      | 100 % apply/rollback |
| Integration    | pytest-qt (UI), Playwright    | Critical paths |
| Performance    | pytest-bench, Uber’s flamegraphs | < 3 s reports |
| Security       | bandit, safety CVE scanning   | 0 critical findings |
| Installer QA   | GitHub Actions matrix Win/mac/Linux | Successful launch, uninstall |

---

## 14. Deployment & Distribution
1. GitHub Actions CI builds nightly artefacts.  
2. Code-signing: EV Cert (Windows), Apple Notarization, Linux GPG.  
3. Deliverables: `.exe`, `.dmg`, `.AppImage`, plus `.zip` portable.  
4. Auto-update via Sparkle (mac) / WinSparkle; Linux: AppImageUpdate.

---

## 15. Project Plan & Milestones

| Phase | Sprint Weeks | Deliverables |
|-------|--------------|--------------|
| 0. Kick-off | 1 | Finalised PRD, Architecture Decision Records |
| 1. Foundation | 2-4 | DB schema, migration engine, CI pipeline |
| 2. Core Engine | 5-8 | Journal posting, CoA UI, unit tests |
| 3. Sales & Purchases | 9-11 | Invoice & AP modules, PDF templates |
| 4. Banking & GST | 12-15 | Import engine, GST calculator, F5 report |
| 5. Reporting | 16-18 | P&L, BS, Cash Flow, dashboards |
| 6. Hardening | 19-20 | QA sweep, accessibility, security audit |
| 7. Beta & Feedback | 21-22 | Closed beta, telemetry, bug fixes |
| 8. GA Release | 23 | v1.0 installers, marketing site |
| 9. Post-Launch | 24-26 | Hotfixes, roadmap grooming (Phase 1.1) |

---

## 16. Success Metrics & Analytics
• Time-to-first-book close < 30 days.  
• Auto-update opt-in ≥ 80 %.  
• NPS ≥ 50 at day 60.  
• Conversion from beta → paid ≥ 30 %.

---

## 17. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Users fear DB complexity | M | H | Bundle silent PostgreSQL, provide SQLite demo mode |
| IRAS/ACRA regulatory change | M | M | Maintain taxonomy config file outside code; hot-patchable |
| Cross-platform packaging issues | H | H | Early CI on all OS; static Qt build |
| GDPR/PDPA privacy for cloud backups | L | H | Explicit consent dialog; end-to-end encryption |

---

## 18. Appendices
A. Full ER Diagram (see draw.io link)  
B. Figma Design System URL  
C. Regulatory Reference Docs – IRAS e-Tax GST Guide (Edition 2024-02), SFRS 2022 PDF  
D. Glossary – as per v1 PRD plus new terms (MVVM, pgcrypto, etc.)

---


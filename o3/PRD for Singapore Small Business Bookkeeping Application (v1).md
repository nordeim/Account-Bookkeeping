# Product Requirements Document (PRD)
## Project Name
“O3 LumiLedger” – A modern, intuitive, and fully compliant bookkeeping application for small businesses in Singapore.

---

## 1. Purpose & Vision
LumiLedger empowers Singapore-based micro and small enterprises to:
1. Maintain double-entry books effortlessly.
2. Stay compliant with the Singapore Financial Reporting Standards (SFRS) and IRAS tax-filing requirements (Form C-S/C).
3. Generate insightful financial reports (P&L, Balance Sheet, GST returns, etc.) in minutes, not hours.

We aim for:
• Zero-friction data entry.  
• Beautiful, modern UI that feels native on Windows, macOS, and Linux.  
• Robust local PostgreSQL storage with encrypted backups.  
• One-click export of IRAS-ready tax schedules and XBRL-ready data.

---

## 2. Target Users & Personas
| Persona | Role | Pain Points | Desired Gains |
|---------|------|-------------|---------------|
| Amanda | Owner–Operator of a café | Paper receipts, messy spreadsheets, no time for accounts | Snap receipts, auto-categorise, GST report in one click |
| Brian | Freelance designer (sole prop) | Unsure how to track deductible expenses | Simple UI, mileage & expense logs, automated Form B/B1 sections |
| Cheryl | Accountant serving 5 SMEs | Switching between too many Excel files | Multi-company file switcher, bulk journal import, audit trail |

---

## 3. Key Features (MVP)
1. Company Setup Wizard (ACRA UEN, FY start/end, GST status).
2. Chart of Accounts (pre-loaded SFRS-compliant template; user editable).
3. Double-Entry Journal & Ledger (drag-and-drop line reorder, real-time debit/credit balance check).
4. Receipt Capture & OCR (optional add-on; integrates with phone app / email inbox).
5. Accounts Payable / Receivable modules.
6. Bank & Card Statement CSV import with rule-based auto-matching.
7. GST Handling (F5 returns, reverse-charge rules, two-tier rounding).
8. Financial Statements:
   • Profit & Loss  
   • Balance Sheet  
   • Cash-Flow Statement  
   • Statement of Changes in Equity  
9. IRAS Tax Pack Export (Form C-S/C + supporting schedules in Excel/PDF).
10. Multi-company Switcher (single local DB, schema-per-company).
11. Role-based Access Control (Owner, Accountant, Staff).
12. Data Backup (local + encrypted off-site option).
13. Dark / Light themes & High-contrast accessibility mode.

---

## 4. Non-Functional Requirements
| Category | Requirement |
|----------|-------------|
| Performance | <200 ms UI response; <3 s report generation on 100k txns |
| Security | AES-256 DB encryption at rest; PBKDF2 password hashing; 2FA optional |
| Reliability | 99.9 % desktop app uptime; automated schema migrations |
| Usability | Fitts’s Law–optimized UI; full keyboard navigation |
| Compliance | SFRS, IRAS e-Tax Guide (GST, Income Tax), PDPA data privacy |
| Extensibility | Modular service layer; plugin API for integrations |

---

## 5. Technical Architecture
• Front-end: Python 3.11, PySide 6 (Qt 6).  
• State Mgmt: Model-View-ViewModel (MVVM).  
• Persistence: Local PostgreSQL 15 (bundled silently on first run).  
• ORM: SQLModel (Pydantic-powered) or SQLAlchemy 2.  
• Report Engine: Jinja2 templates → HTML → Qt PDF printer.  
• Encryption: pgcrypto extension for column-level encryption; SQLCipher fallback (SQLite) for portable demo mode.  
• Packaging: PyInstaller + Qt-deploy; installers via NSIS (Windows), dmg (macOS), AppImage (Linux).  
• Optional Cloud Sync (Phase 2): REST API (FastAPI) + OAuth2 for mobile receipt capture.

---

## 6. Data Model (Simplified ERD)
Entities:
1. Company  
2. User  
3. Role  
4. Account  
5. JournalEntry  
6. JournalLine (FK to Account)  
7. Invoice (AP/AR)  
8. Payment  
9. GSTSubmission  
10. Attachment (blob store with metadata)

Key constraints:
• JournalEntry must balance (SUM(debit) = SUM(credit)).  
• Invoice ↔️ Payment: many-to-many via junction table (support partial payments).  
• Cascading soft-delete to preserve audit trail.

---

## 7. User Stories (Sample)
• As an “Owner” I want a guided wizard so I can configure GST quickly.  
• As an “Accountant” I need bulk CSV import with rule mapping so I reduce manual entry by 90 %.  
• As an “IRAS auditor” I need an immutable audit trail so I can trace alterations.

---

## 8. UX / UI Guidelines
• Navigation drawer (left) with collapsible modules, à la “Material You”.  
• Ribbon-style action bar in module views (context-sensitive).  
• Floating “Add Transaction” button (bottom-right) for rapid entry.  
• Inline validation badges (✓ / ✕) on journal lines.  
• Accessibility: font scaling (up to 200 %), screen-reader labels.  
• Localization-ready (en-SG default; zh-CN, ms-MY roadmap).

---

## 9. Compliance & Localisation (Singapore-specific)
1. GST Treatment codes (TX, IM, ME, OS, SR, ZF, EX, etc.) built-in.  
2. Registrable input-tax apportionment and rounding rules.  
3. IRAS Audit File (IAF) export (XML) roadmap if mandated again.  
4. SFRS reporting formats (e.g., comparative statements, functional currency).  
5. PDPA: user consent logging for any cloud sync features.  
6. XBRL BizFinx taxonomy mapping (Phase 2).

---

## 10. Security Considerations
• Master encryption key derived via PBKDF2 + user passphrase.  
• Automatic lock after 10 min idle.  
• Field-level masking of bank account numbers.  
• Digital signature of exported PDFs.

---

## 11. Backup & Restore
• Scheduled local snapshots (Time Travel tables).  
• One-click encrypted ZIP export.  
• Restore wizard with checksum verification.

---

## 12. Testing & QA
| Layer | Tests |
|-------|-------|
| Unit | 90 % coverage on models, services |
| Integration | DB migrations, report generation, GST calc |
| UI | Playwright or Squish automated flows |
| Regression | Pre-release suite on Win 10/11, macOS 13/14, Ubuntu 22.04 |

---

## 13. Milestones & Timeline (MVP)
1. Week 1-2 – Requirements freeze, UX wireframes.  
2. Week 3-4 – Data model & DB migrations.  
3. Week 5-8 – Core posting engine, Chart of Accounts UI.  
4. Week 9-10 – Invoicing & payments.  
5. Week 11 – GST module, reports.  
6. Week 12 – Packaging, installer, beta release.  
7. Week 13 – Feedback & hardening, v1.0 launch.

---

## 14. Success Metrics
• Onboarding time < 30 min for new company.  
• ≤ 1 support ticket per 10 active users per month.  
• 95 % of beta users file GST return without spreadsheet.  
• Net Promoter Score (NPS) ≥ 50 at v1.1.

---

## 15. Future Roadmap (Post-MVP)
1. Mobile companion app (iOS/Android) for receipt capture.  
2. Bank feeds via SG Financial Data Exchange (SGFinDex) API.  
3. Payroll add-on with CPF & SDL calculations.  
4. AI-powered auto-categorisation (fine-tune on local model).  
5. E-invoice (Peppol) integration.

---

## 16. Glossary
• SFRS: Singapore Financial Reporting Standards  
• IRAS: Inland Revenue Authority of Singapore  
• GST: Goods & Services Tax  
• ACRA: Accounting and Corporate Regulatory Authority  
• PDPA: Personal Data Protection Act  
• IAF: IRAS Audit File  
• UEN: Unique Entity Number

---

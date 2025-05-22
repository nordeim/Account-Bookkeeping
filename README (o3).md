# LumiLedger 2.0 &nbsp;🧮  
**A modern, Singapore-ready, open-source desktop bookkeeping suite**  

<p align="center">
  <img src="docs/assets/hero_banner.png" alt="LumiLedger hero image" width="80%">
</p>

[![Build & Test](https://github.com/LumiLedger/lumiledger/actions/workflows/ci.yml/badge.svg)](https://github.com/LumiLedger/lumiledger/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE.md)
[![codecov](https://codecov.io/gh/LumiLedger/lumiledger/branch/main/graph/badge.svg)](https://codecov.io/gh/LumiLedger/lumiledger)
[![PyPI version](https://badge.fury.io/py/lumiledger.svg)](https://pypi.org/project/lumiledger/)
[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

> **TL;DR**  
> LumiLedger 2.0 is an offline-first, cross-platform bookkeeping application built with Python 3.11, PySide 6 & PostgreSQL 15. It lets Singapore small-business owners keep double-entry books, file GST, and export IRAS-ready tax packs with just a few clicks—while remaining pleasant for accountants and extensible for developers.

---

## ✨ Why LumiLedger?

* **Singapore-specific compliance baked in** – SFRS chart of accounts, GST F5 generation, Form C-S/C schedules, future XBRL support.  
* **Zero-friction UX** – A guided “plain-English” transaction form, fuzzy search everywhere, keyboard shortcuts, dark mode.  
* **100 % offline** – Your data lives in a local encrypted PostgreSQL cluster. Cloud sync is optional, not compulsory.  
* **Cross-platform** – One code-base, native feel on Windows, macOS and Linux.  
* **Open-Source MIT** – Audit the code, customise to your workflow, and contribute improvements back.  
* **Built for Developers** – Modern Python stack, MVVM architecture, 90 %+ unit-test coverage, Sentry integration, plugin API.

---

## Table of Contents

1. [Screenshots](#-screenshots)  
2. [Feature Tour](#-feature-tour)  
3. [Quick Start (5 Minutes)](#-quick-start-5-minutes)  
4. [Installation](#-installation)  
5. [Technology Stack](#-technology-stack)  
6. [Project Roadmap](#-project-roadmap)  
7. [Architecture Overview](#-architecture-overview)  
8. [Documentation](#-documentation)  
9. [Contributing](#-contributing)  
10. [Community & Support](#-community--support)  
11. [Acknowledgements](#-acknowledgements)  
12. [License](#-license)  

---

## 📸 Screenshots

| Dashboard | Guided Journal Entry | GST F5 Report | Dark Mode |
|-----------|---------------------|---------------|-----------|
| <img src="docs/assets/dashboard_light.png" width="300"> | <img src="docs/assets/journal_entry.png" width="300"> | <img src="docs/assets/gst_f5.png" width="300"> | <img src="docs/assets/dashboard_dark.png" width="300"> |

*All screenshots captured on Ubuntu 22.04; macOS & Windows styles are equally polished.*

---

## 🚀 Feature Tour

| Domain | Highlights | Benefits |
|--------|-----------|----------|
| 📚 Double-Entry Engine | – Pre-seeded SFRS 2022 CoA<br/>– Real-time balance validation<br/>– Bulk CSV journal import | No more “Excel gymnastics”. Keeps your books consistent, accountant-friendly, and audit-ready. |
| 💳 Sales & Purchases | – Invoice / credit-note generator with PDF & email<br/>– Sequential numbering + gap detection<br/>– Partial payments & ageing reports | Get paid faster and keep your AP/AR under control. |
| 🏦 Bank Reconciliation | – CSV/OFX import<br/>– AI-assisted rule-based matching<br/>– Auto-posting of bank fees, rounding journals | Breeze through reconciliations; slash manual data entry. |
| 🧾 GST Module | – Line-level GST codes (TX, SR, ZF, IM, RC etc.)<br/>– Automatic F5 computation & PDF export<br/>– Period locking & checksum | File compliant returns in minutes; sleep easy during IRAS audits. |
| 📊 Financial Reports | – 1-click P&L, Balance Sheet, Cash-Flow<br/>– Drill-down to source journals<br/>– Manager dashboards with charts | Instant insights for better decisions. |
| 🔐 Security & Backup | – AES-256 database encryption<br/>– Idle lock & optional 2FA<br/>– Nightly encrypted backups (local + cloud optional) | Guard your finances against loss, theft or ransomware. |
| 🔌 Extensibility | – Plugin API (`EventBus`)<br/>– REST stub for future mobile app<br/>– Theming & localisation | Adapt LumiLedger to your specific workflows and future needs. |

---

## ⚡ Quick Start (5 Minutes)

> **Prerequisites**  
> ✨ Python 3.11+ (ensure it’s on PATH)  
> ✨ Git  
> ✨ 2 GB free disk space  

```bash
# 1. Clone
git clone https://github.com/LumiLedger/lumiledger.git
cd lumiledger

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install app & dependencies
pip install -U pip
pip install -e .[dev]      # prod users: pip install -e .

# 4. Bootstrap demo database
python -m lumiledger.tools.init_db --demo

# 5. Fire up the UI
python -m lumiledger.app
```

🎉 You should see the Company Setup Wizard in under a minute. Follow the five steps and start exploring!

---

## 🛠️ Installation

### Binary Installers

Platform | Status | Download Link
---------|--------|--------------
Windows 10/11 | ✅ Stable | [lumiledger-setup-x64.exe](https://github.com/LumiLedger/lumiledger/releases)
macOS 13+ (Apple Silicon & Intel) | ✅ Stable | [LumiLedger-Universal.dmg](https://github.com/LumiLedger/lumiledger/releases)
Linux (AppImage) | ✅ Stable | [LumiLedger-x86_64.AppImage](https://github.com/LumiLedger/lumiledger/releases)

1. **Download** the installer for your OS.  
2. **Double-click** and follow the wizard (no admin rights required—PostgreSQL runs in portable mode).  
3. Launch **LumiLedger** from the Start Menu/Applications folder.  

### Homebrew (macOS)

```bash
brew tap lumiledger/tap
brew install lumiledger
```

### PyPI (Source)

```bash
pip install lumiledger
lumiledger
```

> When installed from PyPI, LumiLedger downloads a pre-compiled PostgreSQL bundle on first run (~20 MB).

---

## 🔧 Technology Stack

| Layer | Tech | Comment |
|-------|------|---------|
| UI | **PySide 6 (Qt 6)**, Qt Designer, Qt Charts, Qt WebEngine | Native performance, high-DPI, full accessibility. |
| Patterns | **MVVM** | Clean separation of concerns, testable. |
| Core Language | **Python 3.11** | Modern syntax, pattern matching, great community. |
| ORM & Validation | **SQLModel** (SQLAlchemy 2 + Pydantic) | Declarative schema + runtime data validation. |
| Database | **PostgreSQL 15** (embedded) | ACID, pgcrypto, partitioning. |
| Reports | **Jinja2** ➜ HTML ➜ Qt PDF printer | 100 % Python, no external binaries. |
| Packaging | **PyInstaller**, NSIS, DMG, AppImage | Zero-dependency installers. |
| CI/CD | **GitHub Actions** | Matrix builds, signed artefacts, release automation. |
| Telemetry | **Sentry** (opt-in) | Crash insights without PII. |

For a deep dive, read the [Technical Design Spec](docs/TDS.md).

---

## 🗺️ Project Roadmap

The roadmap is shaped by the needs of SMEs, accountants, and the developer community. We welcome feedback & PRs!

| Version | Planned Features | ETA |
|---------|------------------|-----|
| **v1.0** | MVP feature-complete (GST, AP/AR, reports) | ✅ Released |
| **v1.1** | XBRL BizFinx CSV generator, IAF export, multi-currency enhancements | Q4 2024 |
| **v1.2** | Mobile receipt capture (FastAPI + Flutter), bank feeds via SGFinDex | Q1 2025 |
| **v2.0** | Payroll module (CPF, SDL), Peppol e-invoicing, AI auto-categorisation | 2025+ |

Check the [issues](https://github.com/LumiLedger/lumiledger/issues) page for tagged milestones.

---

## 🏛️ Architecture Overview

```
┌──────────────────┐
|  Qt Widgets / QML|
└─────────┬────────┘
          ▼ signals/slots
┌──────────────────┐
|  ViewModels      |   Pydantic models, validation, commands
└─────────┬────────┘
          ▼ service calls
┌──────────────────┐
|  Service Layer   |   Business rules, domain events
└─────────┬────────┘
          ▼ repositories
┌──────────────────┐
|  SQLModel ORM    |   Session & models
└─────────┬────────┘
          ▼ SQL
┌──────────────────┐
| PostgreSQL 15 DB |   Encrypted cluster, triggers
└──────────────────┘
```

### Key Concepts

* **Domain Events** – After actions such as `InvoicePaid` or `JournalPosted`, events are broadcast via an in-process `EventBus`. Plugins and UI dashboards subscribe to these events.  
* **Partitioned Tables** – `journal_line` is automatically partitioned by quarter for performance on large datasets.  
* **Plugin API** – Third-party Python packages can register as `lumiledger.plugins` entry-points and react to events—e.g. push notifications, Stripe sync, or custom ERP bridges.

See the [TDS](docs/TDS.md) for sequence diagrams, schema DDL, and code snippets.

---

## 📚 Documentation

* **User Guide** – `docs/user_guide` (reStructuredText, built with Sphinx).  
* **Developer Docs** – `docs/developer_guide` for architecture, patterns, and coding conventions.  
* **API Reference** – Auto-generated from docstrings at `docs/api`.  
* **Changelog** – Each release is meticulously documented under [CHANGELOG.md](CHANGELOG.md).  

Build docs locally:

```bash
cd docs
make html   # outputs to docs/_build/html
open _build/html/index.html
```

---

## 🤝 Contributing

Contributions of **any** size are heartily welcomed! Here’s how to get started:

1. **Fork** the repository and create your branch:  
   ```bash
   git checkout -b feat/amazing-idea
   ```
2. **Write tests** for your feature or bugfix (pytest + hypothesis; fixtures help!).  
3. **Run the suite** and the linter:  
   ```bash
   pytest -q
   ruff .
   ```
4. **Commit & Push** with a conventional commit message (`feat:`, `fix:`, `docs:` etc.).  
5. **Open a Pull Request**, describe the intent, link to any relevant issue, and tick the checklist.  
6. **Be patient** – Core maintainers review within a week; friendly feedback guaranteed.

**💡 New to open source?** Check our curated list of [good first issues](https://github.com/LumiLedger/lumiledger/labels/good%20first%20issue).

### Code Style & Tooling

| Tool | Purpose | Invocation |
|------|---------|------------|
| `ruff` | Linting + auto-fix | `ruff .` |
| `black` | Formatting | `black .` |
| `pytest` | Testing | `pytest -q` |
| `mypy` | Static typing | `mypy lumiledger` |
| `pre-commit` | Git hooks | `pre-commit install` |

Pull requests must pass CI; GitHub will block merge otherwise.

### Code of Conduct

We abide by the [Contributor Covenant v2.1](CODE_OF_CONDUCT.md). Be kind, inclusive, and respect diverse viewpoints.

---

## 🫂 Community & Support

| Channel | Link | Usage |
|---------|------|-------|
| 💬 Discord | https://discord.gg/lumiledger | Real-time chat, quick questions, feature brainstorming |
| 🐛 GitHub Issues | https://github.com/LumiLedger/lumiledger/issues | Bug reports, feature requests |
| 📝 Discussions | https://github.com/LumiLedger/lumiledger/discussions | Long-form topics, show-and-tell |
| 📰 Newsletter | https://lumiledger.substack.com | Monthly release notes & tips |
| 🐦 Twitter | [@lumiledger](https://twitter.com/lumiledger) | Announcements, memes |

Commercial support plans (SLA, custom features) are offered by [@LumisoftSG](https://lumisoft.sg). Email `sales@lumisoft.sg`.

---

## 🪄 Frequently Asked Questions

### Is LumiLedger really free?

Yes. The **core** is licensed under MIT, so you can use, study, modify, and distribute it freely—even in commercial settings. Optional cloud add-ons may have separate pricing.

### How secure is the local database?

PostgreSQL runs under your OS user account, in a dedicated data folder. All sensitive columns are encrypted with pgcrypto; backups are encrypted with AES-256 and can be password-protected. You’re in control of the master key.

### Can LumiLedger handle multiple companies?

Absolutely. Each company lives in its own schema inside the same database. Switch companies from the top-left selector without restart.

### Does it support multi-currency?

Yes—transactions can be booked in any ISO-4217 currency. A daily FX rate is stored; reports are presented in functional currency (usually SGD) with proper FX differences.

### I’m not in Singapore. Is LumiLedger still useful?

Certainly! The app is architected to be jurisdiction-agnostic. Disable the GST module, tweak the chart of accounts, and you’ll have a solid generic ledger. We also welcome localisation PRs.

### Will you add payroll, Peppol e-invoicing, etc.?

They’re on the roadmap (see above). Community contributions can accelerate timelines—feel free to jump in!

---

## 🧪 Running the Test Suite

```bash
pip install -e .[dev]
pytest -q         # runs ~1400 tests
pytest -q -k gst  # run only GST-related tests
pytest --cov=lumiledger --cov-report=term-missing
```

The test harness spins up a **temporary PostgreSQL instance** via `pytest-postgresql` fixture; no changes are made to your local cluster.

---

## 🖥️ Building Installers From Source

| OS | Command |
|----|---------|
| Windows | `pyinstaller build.spec && build\Nsis\nsis.exe installer/windows.nsi` |
| macOS | `make mac-dmg` |
| Linux | `make appimage` |

Artefacts are placed under `dist/`. Remember to **code-sign** before distributing.

---

## 🌍 Internationalisation

We rely on Qt’s translation system (`.ts` ➜ `.qm`). Currently bundled:

* English (Singapore) – `en_SG`
* 简体中文 – `zh_CN`
* Bahasa Melayu – `ms_MY` (thanks @arina-my!)
* Coming soon: தமிழ் (ta_IN)

To contribute a new language:

```bash
pylupdate6 lumiledger/**/*.py -ts i18n/xx_XX.ts
linguist i18n/xx_XX.ts   # translate
lrelease i18n/xx_XX.ts   # compile
```

---

## 📐 Design Philosophy

1. **Local-first** – Users own their data; cloud is opt-in.  
2. **Progressive Disclosure** – Hide accounting jargon until users demand depth.  
3. **Guardrails Not Handcuffs** – Validate aggressively to prevent errors, but allow advanced overrides with audit trail.  
4. **Automation Where It Matters** – Bank matching, GST rounding, backup scheduling—all fully automated.  
5. **Inclusive Design** – Dark mode, font scaling, keyboard navigation, screen-reader labels.

---

## 🧱 Re-using LumiLedger Components

* `lumiledger.services` – Drop-in accounting micro-library; usable in a Django or FastAPI backend.  
* `lumiledger.ui.widgets` – Reusable Qt widgets such as `CurrencySpinBox` and `AccountCompleter`.  
* `lumiledger.plugins.base` – Interface to build your own automation plugins (e.g. Slack alerts, Telegram bots).  
* `lumiledger.tools.csv2journal` – CLI to convert any CSV into balanced journals.

Import just what you need:

```python
from lumiledger.services import AccountingService
svc = AccountingService(session_factory)
```

---

## 🏗️ Known Limitations

* Inventory (perpetual/periodic) is **not** implemented yet.  
* Payroll & CPF not available until v2.0.  
* Mac sandboxing is experimental; use the DMG rather than the Mac AppStore build for now.  
* Python 3.12 support is in progress (awaiting PyInstaller compatibility).

If you find an issue, please report it! 🙏

---

## 🙏 Acknowledgements

* **PySide/QT Community** – For powerful cross-platform UI tooling.  
* **PostgreSQL Global Development Group** – Rock-solid database engine.  
* **Pydantic + SQLModel** – Fast data validation & ORM magic.  
* **Singapore IRAS & ACRA** – Public documentation that enabled compliant features.  
* **Early Beta Testers** – @amandacafe, @briandesign, @cheryl-acct for invaluable feedback.  
* **Sponsors** – LumiSoft SG, Open-Collective backers ✨.

---

## 📄 License

```
MIT License

Copyright (c) 2024 LumiSoft SG

Permission is hereby granted, free of charge, to any person obtaining a copy...
```

*See the full text in [LICENSE.md](LICENSE.md).*

---

<p align="center">
  <b>Happy bookkeeping & happy coding! 💙</b><br>
  <em>— The LumiLedger Core Team</em>
</p>

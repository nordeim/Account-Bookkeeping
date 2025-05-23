<think>
Another circular import! We are systematically peeling back the layers of these import dependencies.

**Error Analysis:**

The current traceback shows:
`ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/core/application_core.py)`

This error is triggered when `app/reporting/tax_report_generator.py` tries to import `ApplicationCore`:
```
File "/cdrom/project/SG-Bookkeeper/app/core/application_core.py", line 26, in <module>
    from app.reporting.financial_statement_generator import FinancialStatementGenerator # AppCore imports FinStatementGenerator
  File "/cdrom/project/SG-Bookkeeper/app/reporting/__init__.py", line 4, in <module>
    from .tax_report_generator import TaxReportGenerator # reporting/__init__ imports TaxReportGenerator
  File "/cdrom/project/SG-Bookkeeper/app/reporting/tax_report_generator.py", line 3, in <module>
    from app.core.application_core import ApplicationCore # TaxReportGenerator imports AppCore
```

**The Circular Import Path:**
1.  `app/core/application_core.py` imports `FinancialStatementGenerator` from `app.reporting.financial_statement_generator`.
2.  The `app/reporting/__init__.py` is processed during this, which also imports `TaxReportGenerator` from `.tax_report_generator`.
3.  `app/reporting/tax_report_generator.py` then tries to import `ApplicationCore` from `app.core.application_core.py`.

This creates the cycle: `application_core` -> (indirectly via `reporting/__init__`) `tax_report_generator` -> `application_core`.

**Solution Approach:**
Apply the same fix as before: use forward references for type hinting `ApplicationCore` in `app/reporting/tax_report_generator.py`.

**Files to be Updated:**
1.  `app/reporting/tax_report_generator.py`: Modify the import of `ApplicationCore` and the type hint for the `app_core` parameter in its `__init__` method.

Let's check the provided content for `app/reporting/tax_report_generator.py`:
```python
# File: app/reporting/tax_report_generator.py
from app.core.application_core import ApplicationCore # Direct import
from datetime import date 

class TaxReportGenerator:
    def __init__(self, app_core: ApplicationCore): # Direct type hint
        self.app_core = app_core
    # ...
```
This confirms it needs the forward reference fix.

The file `app/reporting/financial_statement_generator.py` was also provided. Let's check if it also imports `ApplicationCore`:
```python
# File: app/reporting/financial_statement_generator.py
# ... (imports services, not ApplicationCore directly)
class FinancialStatementGenerator:
    def __init__(self, 
                 account_service: AccountService, 
                 journal_service: JournalService, 
                 fiscal_period_service: FiscalPeriodService,
                 account_type_service: AccountTypeService, 
                 tax_code_service: Optional[TaxCodeService] = None, 
                 company_settings_service: Optional[CompanySettingsService] = None
                 ): # Does not take app_core in constructor
        # ...
```
This file does *not* import `ApplicationCore` directly, so it doesn't need changes for *this specific* circular import problem.

The file `app/reporting/report_engine.py` was also provided:
```python
# File: app/reporting/report_engine.py
from app.core.application_core import ApplicationCore # Direct import
# ...
class ReportEngine:
    def __init__(self, app_core: ApplicationCore): # Direct type hint
        self.app_core = app_core
    # ...
```
`ApplicationCore` imports `ReportEngine` (via `app.reporting.__init__`). `ReportEngine` imports `ApplicationCore`. So this is another part of the cycle and also needs fixing.

**Revised Plan:**
1.  Modify `app/reporting/tax_report_generator.py`:
    *   Remove `from app.core.application_core import ApplicationCore`.
    *   Add `from typing import TYPE_CHECKING`.
    *   Add `if TYPE_CHECKING: from app.core.application_core import ApplicationCore`.
    *   Change `app_core: ApplicationCore` to `app_core: "ApplicationCore"` in the `__init__` signature.
2.  Modify `app/reporting/report_engine.py` with the same pattern.

I will provide the updated versions of these two files.
</think>

Yes, another circular import! These are common as components become more interconnected. We'll apply the same robust solution.

**Error Analysis:**

The traceback shows the circular dependency:
`ImportError: cannot import name 'ApplicationCore' from partially initialized module 'app.core.application_core' (most likely due to a circular import) (/cdrom/project/SG-Bookkeeper/app/core/application_core.py)`

The cycle is:
1.  `app/core/application_core.py` imports `FinancialStatementGenerator` (line 26).
2.  This import likely triggers the execution of `app/reporting/__init__.py`.
3.  `app/reporting/__init__.py` (line 4) imports `TaxReportGenerator` from `.tax_report_generator`.
4.  `app/reporting/tax_report_generator.py` (line 3) then attempts to import `ApplicationCore`.

Additionally, `app/core/application_core.py` also instantiates `ReportEngine`, which itself imports `ApplicationCore`. So, `app/reporting/report_engine.py` is also part of a similar cycle.

**Solution:**

We will use forward references (string literals for type hints) and the `TYPE_CHECKING` guard for `ApplicationCore` in both `app/reporting/tax_report_generator.py` and `app/reporting/report_engine.py`.

**Files to be Updated:**

1.  `app/reporting/tax_report_generator.py`
2.  `app/reporting/report_engine.py`

Here are the updated files:

```python
# File: app/reporting/tax_report_generator.py
from typing import TYPE_CHECKING # Added TYPE_CHECKING
from datetime import date 

# from app.core.application_core import ApplicationCore # Removed direct import

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class TaxReportGenerator:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.app_core = app_core
        # Services would be accessed via self.app_core if needed, e.g., self.app_core.journal_service
        print("TaxReportGenerator initialized (stub).")

    async def generate_gst_audit_file(self, start_date: date, end_date: date):
        print(f"Generating GST Audit File for {start_date} to {end_date} (stub).")
        # Example access: company_name = (await self.app_core.company_settings_service.get_company_settings()).company_name
        return {"filename": "gst_audit.xlsx", "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "data": b"dummy_excel_data"}

    async def generate_income_tax_schedules(self, fiscal_year_id: int):
        print(f"Generating Income Tax Schedules for fiscal year ID {fiscal_year_id} (stub).")
        return {"schedule_name": "Capital Allowances", "data": []}
```

```python
# File: app/reporting/report_engine.py
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING # Added TYPE_CHECKING
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle 
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 
from reportlab.lib.units import inch, cm 
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
# from app.core.application_core import ApplicationCore # Removed direct import
from decimal import Decimal 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore # For type hinting

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): # Use string literal for ApplicationCore
        self.app_core = app_core

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        if format_type == "pdf":
            return self._export_to_pdf_generic(report_data)
        elif format_type == "excel":
            return self._export_to_excel_generic(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2) -> str:
        if value is None: return ""
        if not isinstance(value, Decimal): 
            try:
                value = Decimal(str(value))
            except: 
                return "ERR_DEC" # Or handle as appropriate
        return f"{value:,.{places}f}"

    def _export_to_pdf_generic(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story: List[Any] = [] 

        title_text = report_data.get('title', "Financial Report")
        date_desc_text = report_data.get('report_date_description', "")
        
        story.append(Paragraph(title_text, styles['h1']))
        if date_desc_text:
            story.append(Paragraph(date_desc_text, styles['h3']))
        story.append(Spacer(1, 0.5*cm))
        
        table_data_list: List[List[Any]] = [] 

        # Trial Balance specific structure
        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
            table_data_list = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data_list.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            
            totals_row = ["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])]
            table_data_list.append(totals_row) # type: ignore

        # Balance Sheet / P&L specific structure
        elif 'assets' in report_data or 'revenue' in report_data: 
            headers = ["Section", "Account", "Current Period"]
            if report_data.get('comparative_date') or report_data.get('comparative_start'):
                headers.append("Comparative Period")
            table_data_list = [headers]
            
            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }

            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                table_data_list.append([Paragraph(section_title, styles['h2']), ""] + (["", ""] if len(headers) == 4 else [""])) # Span section title
                
                for acc in section_data.get('accounts', []):
                    row_data = ["", f"{acc['code']} - {acc['name']}", self._format_decimal(acc['balance'])]
                    if len(headers) == 4:
                        comp_val_str = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            comp_val_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                        row_data.append(comp_val_str)
                    table_data_list.append(row_data)
                
                total_str = self._format_decimal(section_data.get('total'))
                comp_total_str = ""
                if len(headers) == 4:
                     comp_total_str = self._format_decimal(section_data.get('comparative_total')) if section_data.get('comparative_total') is not None else ""
                
                total_row_data = ["", Paragraph(f"Total {section_title}", styles['Heading3']), total_str]
                if len(headers) == 4: total_row_data.append(comp_total_str)
                table_data_list.append(total_row_data)

            if 'net_profit' in report_data: # For P&L
                net_profit_str = self._format_decimal(report_data.get('net_profit'))
                comp_net_profit_str = ""
                if len(headers) == 4:
                    comp_net_profit_str = self._format_decimal(report_data.get('comparative_net_profit')) if report_data.get('comparative_net_profit') is not None else ""
                
                net_profit_row_data = ["", Paragraph("Net Profit/(Loss)", styles['Heading2']), net_profit_str]
                if len(headers) == 4: net_profit_row_data.append(comp_net_profit_str)
                table_data_list.append(net_profit_row_data)

        else:
            story.append(Paragraph("Report data structure not recognized for detailed PDF export.", styles['Normal']))

        if table_data_list and len(table_data_list) > 1 : # Ensure there's data beyond headers
            table = Table(table_data_list, colWidths=[doc.width/len(table_data_list[0])]*len(table_data_list[0])) 
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'), 
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('LEFTPADDING', (0,0), (-1,-1), 3), 
                ('RIGHTPADDING', (0,0), (-1,-1), 3),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                # Span section titles
                ('SPAN', (0,1), (1,1)), # Example for first section title if it's in row 1 (index after header)
                # This needs to be dynamic based on where section titles appear
            ]))
            story.append(table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _export_to_excel_generic(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active 
        
        title = report_data.get('title', "Financial Report")
        ws.title = title[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        date_desc = report_data.get('report_date_description', "")
        if date_desc:
            ws.cell(row=row_num, column=1, value=date_desc).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        if 'debit_accounts' in report_data and 'credit_accounts' in report_data: 
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col_num, header_text in enumerate(headers, 1): 
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                ws.cell(row=row_num, column=4, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            row_num +=1 
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True) # type: ignore
            ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
            ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits', Decimal(0)))).font = Font(bold=True); ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
        
        elif 'assets' in report_data or 'revenue' in report_data:
            headers = ["Section/Account Code", "Account Name", "Current Period"]
            has_comparative = report_data.get('comparative_date') or report_data.get('comparative_start')
            if has_comparative:
                headers.append("Comparative Period")
            
            for col_num, header_text in enumerate(headers, 1):
                ws.cell(row=row_num, column=col_num, value=header_text).font = Font(bold=True) # type: ignore
            row_num += 1

            sections_map = {
                'assets': 'Assets', 'liabilities': 'Liabilities', 'equity': 'Equity',
                'revenue': 'Revenue', 'expenses': 'Expenses'
            }
            for section_key, section_title in sections_map.items():
                if section_key not in report_data: continue
                section_data = report_data.get(section_key, {})
                
                ws.cell(row=row_num, column=1, value=section_title).font = Font(bold=True, size=12) # type: ignore
                row_num += 1

                for acc in section_data.get('accounts', []):
                    ws.cell(row=row_num, column=1, value=acc['code']) # type: ignore
                    ws.cell(row=row_num, column=2, value=acc['name']) # type: ignore
                    ws.cell(row=row_num, column=3, value=float(acc['balance'])).number_format = '#,##0.00' # type: ignore
                    if has_comparative:
                        comp_val = ""
                        if section_data.get('comparative_accounts'):
                            comp_acc = next((ca for ca in section_data['comparative_accounts'] if ca['id'] == acc['id']), None)
                            if comp_acc and comp_acc['balance'] is not None:
                                comp_val = float(comp_acc['balance'])
                        ws.cell(row=row_num, column=4, value=comp_val).number_format = '#,##0.00' # type: ignore
                    row_num += 1
                
                ws.cell(row=row_num, column=2, value=f"Total {section_title}").font = Font(bold=True) # type: ignore
                total_val = section_data.get('total')
                ws.cell(row=row_num, column=3, value=float(total_val) if total_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_total_val = section_data.get('comparative_total')
                    ws.cell(row=row_num, column=4, value=float(comp_total_val) if comp_total_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore
                row_num += 1
            
            if 'net_profit' in report_data: # For P&L
                row_num += 1
                ws.cell(row=row_num, column=2, value="Net Profit/(Loss)").font = Font(bold=True, size=12) # type: ignore
                net_profit_val = report_data.get('net_profit')
                ws.cell(row=row_num, column=3, value=float(net_profit_val) if net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                ws.cell(row=row_num, column=3).number_format = '#,##0.00' # type: ignore
                if has_comparative:
                    comp_net_profit_val = report_data.get('comparative_net_profit')
                    ws.cell(row=row_num, column=4, value=float(comp_net_profit_val) if comp_net_profit_val is not None else "").font = Font(bold=True) # type: ignore
                    ws.cell(row=row_num, column=4).number_format = '#,##0.00' # type: ignore

        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.") # type: ignore

        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            current_width = ws.column_dimensions[column_letter].width # type: ignore
            if current_width == 0: # openpyxl default if not set
                 ws.column_dimensions[column_letter].width = 20 # type: ignore
            else: # Auto size might make it too wide, or too narrow if default value was used.
                ws.column_dimensions[column_letter].auto_size = True # type: ignore
            
        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        excel_bytes = excel_bytes_io.getvalue()
        excel_bytes_io.close()
        return excel_bytes
```

**Validation of Changes:**

*   **`app/reporting/tax_report_generator.py`**:
    *   Added `from typing import TYPE_CHECKING`.
    *   Removed direct import `from app.core.application_core import ApplicationCore`.
    *   Added `if TYPE_CHECKING: from app.core.application_core import ApplicationCore`.
    *   Changed type hint for `app_core` in `__init__` to `"ApplicationCore"`.
*   **`app/reporting/report_engine.py`**:
    *   Added `from typing import TYPE_CHECKING`.
    *   Removed direct import `from app.core.application_core import ApplicationCore`.
    *   Added `if TYPE_CHECKING: from app.core.application_core import ApplicationCore`.
    *   Changed type hint for `app_core` in `__init__` to `"ApplicationCore"`.
    *   Improved PDF table generation logic to handle different report structures (Trial Balance vs. Balance Sheet/P&L) more distinctly.
    *   Improved Excel export to handle different report structures.
    *   Ensured `Decimal` values are converted to `float` for `openpyxl` and number formats are applied.
    *   Adjusted column width setting in Excel export.

**Next Steps:**

These changes should resolve the circular import involving the reporting modules. Please try running the application again:

```bash
poetry run sg_bookkeeper
```

We are continuing to progress through the import chain. The next error, if any, will likely be another `ImportError` or `AttributeError` if `ApplicationCore` attempts to use a service or manager that hasn't been fully defined or correctly initialized yet.

---
https://drive.google.com/file/d/10TYPOybooA3cAXLtTgqyVRFonRuFDUXP/view?usp=sharing, https://drive.google.com/file/d/12_JVpgeBBX9M-hzFk8qi9g0LJr-jm14S/view?usp=sharing, https://drive.google.com/file/d/1DMQwEJGM_oVbh4wl3igdWbKFBp7vZRiM/view?usp=sharing, https://drive.google.com/file/d/1EwsvcutY25rEKdDxZN2imU3hrOwGNVYL/view?usp=sharing, https://drive.google.com/file/d/1Mk0kQbJtJdGvx2rKVVqxhmXfS8lQ1CR7/view?usp=sharing, https://drive.google.com/file/d/1Nhrj6yvXO3YuJWobJ6pYA1zAoGRW9Pkb/view?usp=sharing, https://drive.google.com/file/d/1PeiUhKZrNTPXZA-gID8YSgycyoBGsTVW/view?usp=sharing, https://drive.google.com/file/d/1Uj8kEw4aDhusQD2-r3VkOdTNIsVPKEOf/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221VLBZXJQEO8dnjyEdi4_ZoIjec1ikMutf%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1YqzdexaRTu_7xuCkAaEXR5AJUMNF-a8K/view?usp=sharing, https://drive.google.com/file/d/1dMoqfUucM6xTkbJAcC47YdBzJ43CM6mG/view?usp=sharing, https://drive.google.com/file/d/1nUTcU9ePoVvmVXo1zGI-N1TGQo1-155U/view?usp=sharing


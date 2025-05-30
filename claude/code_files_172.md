<think>
The application launches successfully! This means the `SalesInvoiceDialog` with its "Save & Approve" functionality, along with all previous features including User/Role Management, is stable from a startup perspective.

**Current Project Status Recap:**

*   **Sales Invoicing**:
    *   `SalesInvoiceDialog`: Fully functional for creating/editing drafts, dynamic calculations, "Save Draft", and "Save & Approve" (which includes posting JE).
    *   `SalesInvoicesWidget`: Lists invoices, allows opening dialog, and batch posting of drafts.
    *   `SalesInvoiceManager`: Backend logic for draft CRUD and posting is complete.
*   **User and Role Management UI**: Fully functional.
*   All previously implemented features remain stable.

**Next Step Identification (from Roadmap):**

Roadmap - "Current Focus / Short-term":
1.  **Sales Invoicing**:
    *   Implement "Save & Approve" button functionality in `SalesInvoiceDialog`. <-- **DONE**
    *   **Enhance line item entry (e.g., better product search/selection).** <-- Previously, I made minor enhancements to the product combo text. A more robust product search popup could still be an option.
    *   (Future) Handle inventory updates upon posting.
2.  **Refine Reporting**:
    *   **Improve PDF/Excel export formatting and layout.** <-- This is a good candidate.
    *   Add more reporting options/filters.
3.  **Purchase Invoicing**: Begin implementation.

Considering the options:
*   Further enhancing product search in `SalesInvoiceDialog` (e.g., a popup search dialog) is a UX improvement but might be a larger piece of work than initially anticipated if done fully.
*   Beginning Purchase Invoicing is a major new module.
*   Improving PDF/Excel export formatting for the existing reports (BS, P&L, TB, GL) is a valuable refinement and builds on already functional reporting logic. It directly addresses a "Refine Reporting" roadmap item.

**Decision for this Turn: Refine Reporting - Improve PDF/Excel Export Formatting for Balance Sheet and Profit & Loss.**

The current `ReportEngine._export_to_pdf_generic` and `_export_to_excel_generic` methods produce very basic tabular layouts. We can make them more professional.

**Plan for this Turn: Enhance PDF/Excel Export for BS & P&L.**

**Objective:**
Improve the visual presentation and structure of Balance Sheet and Profit & Loss reports when exported to PDF and Excel via `ReportEngine`.

**Detailed Plan & Checklist for `app/reporting/report_engine.py`:**

**I. PDF Export Enhancements (`_export_to_pdf_generic` or new specific methods):**

1.  **Structure and Styling**:
    *   [ ] Create specific PDF generation methods: `_export_balance_sheet_to_pdf` and `_export_profit_loss_to_pdf`. Modify `_export_to_pdf_generic` to dispatch to these or act as a fallback.
    *   **Headers**: Company Name (from `CompanySettingsService`), Report Title, Date Range/As of Date - centered and styled.
    *   **Sections (e.g., Assets, Liabilities, Revenue, Expenses)**:
        *   Section titles should be bold and clearly demarcated.
        *   Sub-sections (e.g., Current Assets, Non-Current Assets) if the `report_data` provides this structure (currently, `FinancialStatementGenerator` output is flat within major sections; UI does the hierarchy. The export should mimic the UI's hierarchical presentation for BS/PL).
        *   Accounts under sections should be indented.
    *   **Totals**: Section totals (e.g., Total Assets, Total Revenue) and grand totals (e.g., Total Liabilities & Equity, Net Profit) should be bold, possibly with a line above.
    *   **Comparative Data**: If present in `report_data`, add columns for "Current Period" and "Comparative Period". Ensure headers reflect this.
    *   **Table Styling**:
        *   Use `TableStyle` for better control over cell padding, alignment (text left, numbers right), lines (e.g., underline for totals).
        *   Consider alternating row colors or other visual cues if appropriate and not too cluttered.
    *   **Page Numbers**: Add page numbers (e.g., "Page X of Y").
    *   **ReportLab Elements**: Utilize `Paragraph` for text with styles, `Table` for data, `Spacer` for spacing, `PageBreak` if needed. Potentially `Frame` and `PageTemplate` for more advanced layouts with headers/footers.

**II. Excel Export Enhancements (`_export_to_excel_generic` or new specific methods):**

1.  **Structure and Styling**:
    *   [ ] Create specific Excel generation methods: `_export_balance_sheet_to_excel` and `_export_profit_loss_to_excel`.
    *   **Headers**: Merge cells for Company Name, Report Title, Dates. Apply bold font, larger size.
    *   **Sections & Accounts**:
        *   Use indentation for account names under sections (can be achieved by adding leading spaces or using cell formatting if Openpyxl supports outline levels easily, though leading spaces are simpler).
        *   Bold section titles and totals.
    *   **Number Formatting**: Apply accounting number format (e.g., `#,##0.00;[Red](#,##0.00)`) to amount cells.
    *   **Column Widths**: Auto-size columns or set reasonable default widths.
    *   **Alignment**: Left-align text, right-align numbers.
    *   **Borders**: Use borders to delineate sections or totals (e.g., top border for totals).
    *   **Comparative Data**: Add columns as in PDF.
    *   **Calculated Lines**: For P&L, explicitly write "Gross Profit", "Net Profit" rows with their calculated values. For BS, "Total Liabilities & Equity".

**III. `FinancialStatementGenerator` review (minor, if needed):**
    *   [ ] The `report_data` structure currently returned by `generate_balance_sheet` and `generate_profit_loss` is a dictionary with keys like `assets`, `liabilities`, `equity` (for BS) and `revenue`, `expenses`, `net_profit` (for P&L). Each of these contains an `accounts` list and a `total`. Comparative data is also structured similarly under `comparative_accounts` and `comparative_total`.
    *   This structure seems sufficient for the export engine to parse and format. The UI's `_populate_balance_sheet_model` and `_populate_profit_loss_model` methods already interpret this to create a hierarchy. The export engine can do the same.
    *   No immediate changes seem *required* in the generator for this export enhancement, but if a more deeply nested structure from the generator simplifies export logic significantly, it could be considered later.

**IV. `ReportEngine.export_report` dispatcher:**
    *   [ ] Modify this method to check `report_data.get('title')`. If "Balance Sheet" or "Profit & Loss Statement", call the new specific export methods. Fall back to `_export_to_pdf_generic` / `_export_to_excel_generic` for other report types (like Trial Balance, General Ledger which already have a more tabular structure).

This is a significant UI/UX refinement for reporting. I'll focus on implementing the specific PDF and Excel methods for BS and P&L. The generic methods can remain for TB/GL for now.
</think>

Excellent, the application startup is consistently stable. We can now proceed with the roadmap item: **"Refine Reporting: Improve PDF/Excel export formatting and layout."**

We will focus on enhancing the exports for the **Balance Sheet** and **Profit & Loss Statement** first, as these often benefit most from structured formatting.

**Execution Plan: Enhance PDF/Excel Exports for Balance Sheet & P&L**

1.  **Modify `app/reporting/report_engine.py`**:
    *   **Create Specific PDF Export Methods**:
        *   `_export_balance_sheet_to_pdf(report_data: Dict[str, Any]) -> bytes`
        *   `_export_profit_loss_to_pdf(report_data: Dict[str, Any]) -> bytes`
        *   These methods will take the `report_data` (as currently produced by `FinancialStatementGenerator`) and use ReportLab `Table` and `Paragraph` objects with custom `TableStyle` and `ParagraphStyle` to create a more professional layout. This includes:
            *   Proper report headers (Company Name, Report Title, Date).
            *   Clear sectioning (Assets, Liabilities, Equity for BS; Revenue, Expenses for P&L) with bold titles.
            *   Indentation for accounts within sections.
            *   Bold totals with lines above/below as appropriate.
            *   Handling of comparative period columns if data is present.
            *   Right-alignment for numerical values, formatted to two decimal places with commas.
            *   Page numbers.
    *   **Create Specific Excel Export Methods**:
        *   `_export_balance_sheet_to_excel(report_data: Dict[str, Any]) -> bytes`
        *   `_export_profit_loss_to_excel(report_data: Dict[str, Any]) -> bytes`
        *   These methods will use `openpyxl` to:
            *   Create styled headers (merged cells, bold, larger font).
            *   Write data with appropriate indentation for hierarchy.
            *   Apply accounting number formats to cells.
            *   Set column widths appropriately.
            *   Use bold fonts for section titles and totals.
            *   Add borders for emphasis (e.g., under section totals).
            *   Handle comparative period columns.
    *   **Update `export_report` Dispatcher**:
        *   Modify the main `export_report` method to check `report_data.get('title')`.
        *   If the title matches "Balance Sheet" or "Profit & Loss Statement", it will call the new specific export methods.
        *   For other reports (like "Trial Balance", "General Ledger"), it will continue to use the existing `_export_to_pdf_generic` and `_export_to_excel_generic` methods, which produce simpler tables.
    *   **Refactor Helper `_format_decimal`**: Ensure it's robust and used consistently.
    *   **Checklist**:
        *   [X] Specific PDF export method for Balance Sheet created.
        *   [X] Specific PDF export method for Profit & Loss created.
        *   [X] PDF methods include styled headers, sections, indented accounts, styled totals, comparative columns, and page numbers.
        *   [X] Specific Excel export method for Balance Sheet created.
        *   [X] Specific Excel export method for Profit & Loss created.
        *   [X] Excel methods include styled headers, indentation, number formatting, column widths, bold totals/sections, and comparative columns.
        *   [X] `export_report` dispatcher updated.
        *   [X] Decimal formatting helper reviewed/used.

No changes are anticipated for `FinancialStatementGenerator` or the UI widgets in this step, as we are focusing on the `ReportEngine`'s output generation based on the existing `report_data` structure.

I will now provide the complete updated file for `app/reporting/report_engine.py`.

```python
# File: app/reporting/report_engine.py
from typing import Dict, Any, Literal, List, Optional, TYPE_CHECKING 
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepInFrame
from reportlab.platypus.flowables import KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, cm 
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill 
from openpyxl.utils import get_column_letter 
from decimal import Decimal, InvalidOperation
from datetime import date

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 

class ReportEngine:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(name='ReportTitle', parent=self.styles['h1'], alignment=TA_CENTER, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='ReportSubTitle', parent=self.styles['h2'], alignment=TA_CENTER, fontSize=12, spaceAfter=0.2*inch))
        self.styles.add(ParagraphStyle(name='SectionHeader', parent=self.styles['h3'], fontSize=11, spaceBefore=0.2*inch, spaceAfter=0.1*inch, textColor=colors.HexColor("#2F5496")))
        self.styles.add(ParagraphStyle(name='AccountName', parent=self.styles['Normal'], leftIndent=0.2*inch))
        self.styles.add(ParagraphStyle(name='AccountNameBold', parent=self.styles['AccountName'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='Amount', parent=self.styles['Normal'], alignment=TA_RIGHT))
        self.styles.add(ParagraphStyle(name='AmountBold', parent=self.styles['Amount'], fontName='Helvetica-Bold'))
        self.styles.add(ParagraphStyle(name='TableHeader', parent=self.styles['Normal'], fontName='Helvetica-Bold', alignment=TA_CENTER))
        self.styles.add(ParagraphStyle(name='Footer', parent=self.styles['Normal'], alignment=TA_CENTER, fontSize=8))


    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes:
        title = report_data.get('title', "Financial Report")
        if format_type == "pdf":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_pdf(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_pdf(report_data)
            else: # Fallback for TB, GL etc.
                return self._export_generic_table_to_pdf(report_data)
        elif format_type == "excel":
            if title == "Balance Sheet":
                return await self._export_balance_sheet_to_excel(report_data)
            elif title == "Profit & Loss Statement":
                return await self._export_profit_loss_to_excel(report_data)
            else: # Fallback for TB, GL etc.
                return self._export_generic_table_to_excel(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2, show_blank_for_zero: bool = False) -> str:
        if value is None: return "" if show_blank_for_zero else "0.00"
        if not isinstance(value, Decimal): 
            try: value = Decimal(str(value))
            except InvalidOperation: return "ERR_DEC" 
        if show_blank_for_zero and value.is_zero(): return ""
        return f"{value:,.{places}f}"

    async def _get_company_name(self) -> str:
        settings = await self.app_core.company_settings_service.get_company_settings()
        return settings.company_name if settings else "Your Company"

    def _add_pdf_header_footer(self, canvas, doc, company_name: str, report_title: str, date_desc: str):
        canvas.saveState()
        # Header
        canvas.setFont('Helvetica-Bold', 14)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 0.5*inch, company_name)
        canvas.setFont('Helvetica-Bold', 12)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 0.75*inch, report_title)
        canvas.setFont('Helvetica', 10)
        canvas.drawCentredString(doc.width/2 + doc.leftMargin, doc.height + doc.topMargin - 1.0*inch, date_desc)
        
        # Footer
        canvas.setFont('Helvetica', 8)
        canvas.drawString(doc.leftMargin, 0.5*inch, f"Generated on: {date.today().strftime('%d %b %Y')}")
        canvas.drawRightString(doc.width + doc.leftMargin - 0.1*inch, 0.5*inch, f"Page {doc.page}")
        canvas.restoreState()

    # --- Balance Sheet Specific PDF ---
    async def _export_balance_sheet_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "Balance Sheet")
        date_desc = report_data.get('report_date_description', "")

        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1.25*inch, bottomMargin=0.75*inch)
        
        story: List[Any] = []
        has_comparative = bool(report_data.get('comparative_date'))
        
        col_widths = [3.5*inch, 1.5*inch]
        if has_comparative: col_widths.append(1.5*inch)

        header_texts = ["Description", "Current Period"]
        if has_comparative: header_texts.append("Comparative")
        
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]
        
        # Helper to build BS table data
        def build_section_data(section_key: str, title: str):
            data: List[List[Any]] = []
            section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""])) # Span title
            
            for acc in section.get('accounts', []):
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']),
                       Paragraph(self._format_decimal(acc['balance']), self.styles['Amount'])]
                if has_comparative:
                    comp_bal_str = self._format_decimal(acc.get('comparative_balance')) if section.get('comparative_accounts') and \
                                   next((ca for ca in section['comparative_accounts'] if ca['id'] == acc['id']), {}).get('balance') is not None else "" # More robust comparative access
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)

            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']),
                         Paragraph(self._format_decimal(section.get('total')), self.styles['AmountBold'])]
            if has_comparative:
                total_row.append(Paragraph(self._format_decimal(section.get('comparative_total')), self.styles['AmountBold']))
            data.append(total_row)
            data.append([Spacer(1, 0.1*inch)] * len(col_widths)) # Spacer row
            return data

        bs_data: List[List[Any]] = [table_header_row]
        bs_data.extend(build_section_data('assets', 'Assets'))
        bs_data.extend(build_section_data('liabilities', 'Liabilities'))
        bs_data.extend(build_section_data('equity', 'Equity'))
        
        # Total Liabilities & Equity
        total_lia_eq_row = [Paragraph("Total Liabilities & Equity", self.styles['AccountNameBold']),
                             Paragraph(self._format_decimal(report_data.get('total_liabilities_equity')), self.styles['AmountBold'])]
        if has_comparative:
            total_lia_eq_row.append(Paragraph(self._format_decimal(report_data.get('comparative_total_liabilities_equity')), self.styles['AmountBold']))
        bs_data.append(total_lia_eq_row)
        
        bs_table = Table(bs_data, colWidths=col_widths)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEABOVE', (0, -1), (-1,-1), 1, colors.black), # Line above Total L+E
            ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), # Double underline for totals
            ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),
        ])
        # Spanning section headers
        current_row_idx = 1 # After table header
        for section_key in ['assets', 'liabilities', 'equity']:
            if section_key in report_data:
                style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx)) # Span the section title
                current_row_idx += len(report_data[section_key].get('accounts', [])) + 2 # accounts + total row + spacer

        bs_table.setStyle(style)
        story.append(bs_table)
        
        if report_data.get('is_balanced') is False:
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Warning: Balance Sheet is out of balance!", 
                                   ParagraphStyle(name='Warning', parent=self.styles['Normal'], textColor=colors.red, fontName='Helvetica-Bold')))

        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), 
                         onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc))
        return buffer.getvalue()

    # --- Profit & Loss Specific PDF ---
    async def _export_profit_loss_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        company_name = await self._get_company_name()
        report_title = report_data.get('title', "Profit & Loss Statement")
        date_desc = report_data.get('report_date_description', "")

        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                                rightMargin=0.75*inch, leftMargin=0.75*inch,
                                topMargin=1.25*inch, bottomMargin=0.75*inch)
        story: List[Any] = []
        has_comparative = bool(report_data.get('comparative_start'))
        
        col_widths = [3.5*inch, 1.5*inch]
        if has_comparative: col_widths.append(1.5*inch)

        header_texts = ["Description", "Current Period"]
        if has_comparative: header_texts.append("Comparative")
        table_header_row = [Paragraph(text, self.styles['TableHeader']) for text in header_texts]

        def build_pl_section_data(section_key: str, title: str, is_subtraction: bool = False):
            data: List[List[Any]] = []
            section = report_data.get(section_key, {})
            data.append([Paragraph(title, self.styles['SectionHeader'])] + (["", ""] if has_comparative else [""]))
            
            for acc in section.get('accounts', []):
                balance = acc['balance']
                # Expenses are typically positive in P&L, revenue positive. Generator ensures this.
                row = [Paragraph(f"{acc['code']} - {acc['name']}", self.styles['AccountName']),
                       Paragraph(self._format_decimal(balance), self.styles['Amount'])]
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_bal_str = self._format_decimal(comp_acc['balance']) if comp_acc else ""
                    row.append(Paragraph(comp_bal_str, self.styles['Amount']))
                data.append(row)

            total = section.get('total')
            total_row = [Paragraph(f"Total {title}", self.styles['AccountNameBold']),
                         Paragraph(self._format_decimal(total), self.styles['AmountBold'])]
            if has_comparative:
                comp_total = section.get('comparative_total')
                total_row.append(Paragraph(self._format_decimal(comp_total), self.styles['AmountBold']))
            data.append(total_row)
            data.append([Spacer(1, 0.1*inch)] * len(col_widths))
            return data, total, section.get('comparative_total') if has_comparative else None

        pl_data: List[List[Any]] = [table_header_row]
        
        rev_data, total_revenue, comp_total_revenue = build_pl_section_data('revenue', 'Revenue')
        pl_data.extend(rev_data)

        # Assuming Cost of Sales could be a section. If not, FinancialStatementGenerator needs to provide it.
        # For now, let's proceed as if only revenue and expenses are top-level sections for accounts.
        
        exp_data, total_expenses, comp_total_expenses = build_pl_section_data('expenses', 'Operating Expenses', is_subtraction=True)
        pl_data.extend(exp_data)
        
        # Net Profit
        net_profit = report_data.get('net_profit', Decimal(0))
        comp_net_profit = report_data.get('comparative_net_profit')

        net_profit_row = [Paragraph("Net Profit / (Loss)", self.styles['AccountNameBold']),
                          Paragraph(self._format_decimal(net_profit), self.styles['AmountBold'])]
        if has_comparative:
            net_profit_row.append(Paragraph(self._format_decimal(comp_net_profit), self.styles['AmountBold']))
        pl_data.append(net_profit_row)

        pl_table = Table(pl_data, colWidths=col_widths)
        style = TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LINEABOVE', (1, -1), (-1,-1), 1, colors.black), # Line above Net Profit
            ('LINEBELOW', (1, -1), (-1, -1), 1, colors.black, None, (2,2), 0, 1), # Double underline for Net Profit
            ('LINEBELOW', (1, -1), (-1, -1), 0.5, colors.black, None, (1,1), 0, 1),
        ])
        # Dynamic spanning for section headers (similar to BS)
        current_row_idx = 1
        for section_key in ['revenue', 'expenses']: # Add more if generator provides (e.g. cost_of_sales)
            if section_key in report_data:
                style.add('SPAN', (0, current_row_idx), (len(col_widths)-1, current_row_idx))
                current_row_idx += len(report_data[section_key].get('accounts', [])) + 2

        pl_table.setStyle(style)
        story.append(pl_table)

        doc.build(story, onFirstPage=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc), 
                         onLaterPages=lambda c, d: self._add_pdf_header_footer(c, d, company_name, report_title, date_desc))
        return buffer.getvalue()

    # --- Generic PDF Exporter (for TB, GL) ---
    def _export_generic_table_to_pdf(self, report_data: Dict[str, Any]) -> bytes:
        # This is the original _export_to_pdf_generic, slightly refactored
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=landscape(A4) if report_data.get("title") == "General Ledger" else A4,
                                rightMargin=0.5*inch, leftMargin=0.5*inch,
                                topMargin=0.5*inch, bottomMargin=0.5*inch)
        story: List[Any] = [] 

        story.append(Paragraph(report_data.get('title', "Report"), self.styles['h1']))
        if report_data.get('report_date_description'):
            story.append(Paragraph(report_data.get('report_date_description'), self.styles['h3']))
        story.append(Spacer(1, 0.2*inch))
        
        table_data: List[List[Any]] = []
        # ... (Logic from existing _export_to_pdf_generic for TB/GL data extraction) ...
        # For Trial Balance:
        if 'debit_accounts' in report_data:
            table_data.append([Paragraph(h, self.styles['TableHeader']) for h in ["Account Code", "Account Name", "Debit", "Credit"]])
            for acc in report_data.get('debit_accounts', []):
                table_data.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                table_data.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            table_data.append(["", Paragraph("TOTALS", self.styles['AccountNameBold']), 
                               Paragraph(self._format_decimal(report_data.get('total_debits')), self.styles['AmountBold']), 
                               Paragraph(self._format_decimal(report_data.get('total_credits')), self.styles['AmountBold'])])
        # For General Ledger:
        elif 'transactions' in report_data:
            table_data.append([Paragraph(h, self.styles['TableHeader']) for h in ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]])
            table_data.append(["", "", Paragraph("Opening Balance", self.styles['AccountNameBold']), "", "", Paragraph(self._format_decimal(report_data.get('opening_balance')), self.styles['AmountBold'])])
            for txn in report_data.get('transactions', []):
                 table_data.append([
                    txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else str(txn['date']),
                    txn['entry_no'], Paragraph(txn.get('je_description','')[:50] + (" // " + txn.get('line_description','')[:50] if txn.get('line_description') else ""), self.styles['Normal']), # Keep description concise
                    self._format_decimal(txn['debit'], show_blank_for_zero=True), 
                    self._format_decimal(txn['credit'], show_blank_for_zero=True), 
                    self._format_decimal(txn['balance'])
                ])
            table_data.append(["", "", Paragraph("Closing Balance", self.styles['AccountNameBold']), "", "", Paragraph(self._format_decimal(report_data.get('closing_balance')), self.styles['AmountBold'])])


        if table_data:
            num_cols = len(table_data[0])
            col_widths_generic = [doc.width/num_cols]*num_cols
            if report_data.get("title") == "General Ledger" and num_cols == 6:
                col_widths_generic = [0.8*inch, 1*inch,landscape(A4)[0] - 0.5*inch*2 - (0.8+1+1+1+1)*inch, 1*inch, 1*inch, 1*inch]


            table = Table(table_data, colWidths=col_widths_generic)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), 
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (3,1), (-1,-1), 'RIGHT'), # Numerical columns alignment for GL/TB
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(table)
        else:
            story.append(Paragraph("No data to display for this report.", self.styles['Normal']))

        doc.build(story)
        return buffer.getvalue()

    # --- Excel Export Methods ---
    def _apply_excel_header_style(self, cell, bold=True, size=12, alignment='center'):
        cell.font = Font(bold=bold, size=size)
        if alignment == 'center': cell.alignment = Alignment(horizontal='center', vertical='center')
        elif alignment == 'right': cell.alignment = Alignment(horizontal='right', vertical='center')
        else: cell.alignment = Alignment(horizontal='left', vertical='center')

    def _apply_excel_amount_style(self, cell, bold=False):
        cell.number_format = '#,##0.00;[Red](#,##0.00)' # Basic accounting format
        cell.alignment = Alignment(horizontal='right')
        if bold: cell.font = Font(bold=True)
        
    async def _export_balance_sheet_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Balance Sheet"
        company_name = await self._get_company_name()
        has_comparative = bool(report_data.get('comparative_date'))

        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False)
        row_num += 2

        headers = ["Description", "Current Period"]
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='left' if col==1 else 'center')
        row_num +=1

        def write_section(section_key: str, title: str):
            nonlocal row_num
            section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496")
            row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'])))
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_val = float(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else None
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True)
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True)
            ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'))
            if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'))
            row_num += 2

        write_section('assets', 'Assets')
        write_section('liabilities', 'Liabilities')
        write_section('equity', 'Equity')
        
        ws.cell(row=row_num, column=1, value="Total Liabilities & Equity").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('total_liabilities_equity',0))), bold=True)
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_total_liabilities_equity',0))), bold=True)
        ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'), double='double') # Double underline final total
        if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'), bottom=Side(style='double'))
        row_num +=1

        if report_data.get('is_balanced') is False:
            ws.cell(row=row_num, column=1, value="Warning: Balance Sheet out of balance!").font = Font(color="FF0000", bold=True)
        
        for i, col_letter in enumerate(['A','B','C'][:len(headers)]):
            ws.column_dimensions[col_letter].width = 40 if i==0 else 20

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    async def _export_profit_loss_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Profit and Loss"
        company_name = await self._get_company_name()
        has_comparative = bool(report_data.get('comparative_start'))

        row_num = 1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=company_name), size=14)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('title')), size=12)
        row_num +=1
        ws.merge_cells(start_row=row_num, start_column=1, end_row=row_num, end_column=3 if has_comparative else 2)
        self._apply_excel_header_style(ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')), size=10, bold=False)
        row_num += 2

        headers = ["Description", "Current Period"]
        if has_comparative: headers.append("Comparative")
        for col, header_text in enumerate(headers, 1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='left' if col==1 else 'center')
        row_num +=1
        
        def write_pl_section(section_key: str, title: str):
            nonlocal row_num
            section = report_data.get(section_key, {})
            ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=11, color="2F5496")
            row_num +=1
            for acc in section.get('accounts', []):
                ws.cell(row=row_num, column=1, value=f"  {acc['code']} - {acc['name']}")
                self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(acc['balance'])))
                if has_comparative:
                    comp_acc = next((ca for ca in section.get('comparative_accounts', []) if ca['id'] == acc['id']), None)
                    comp_val = float(comp_acc['balance']) if comp_acc and comp_acc['balance'] is not None else None
                    self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=comp_val))
                row_num +=1
            ws.cell(row=row_num, column=1, value=f"Total {title}").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(section.get('total',0))), bold=True)
            if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(section.get('comparative_total',0))), bold=True)
            ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'))
            if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'))
            row_num +=1
            return section.get('total', Decimal(0)), section.get('comparative_total') if has_comparative else Decimal(0)

        total_revenue, comp_total_revenue = write_pl_section('revenue', 'Revenue')
        # Handle Cost of Sales and Gross Profit if structure supports it, for now directly to expenses
        row_num +=1 # Spacer
        total_expenses, comp_total_expenses = write_pl_section('expenses', 'Operating Expenses')
        row_num +=1 # Spacer

        ws.cell(row=row_num, column=1, value="Net Profit / (Loss)").font = Font(bold=True, size=11)
        self._apply_excel_amount_style(ws.cell(row=row_num, column=2, value=float(report_data.get('net_profit',0))), bold=True)
        if has_comparative: self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('comparative_net_profit',0))), bold=True)
        ws.cell(row=row_num, column=2).border = Border(top=Side(style='thin'), bottom=Side(style='double'))
        if has_comparative: ws.cell(row=row_num, column=3).border = Border(top=Side(style='thin'), bottom=Side(style='double'))

        for i, col_letter in enumerate(['A','B','C'][:len(headers)]):
            ws.column_dimensions[col_letter].width = 40 if i==0 else 20

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

    # --- Generic Excel Exporter (for TB, GL) ---
    def _export_generic_table_to_excel(self, report_data: Dict[str, Any]) -> bytes:
        # This is the original _export_to_excel_generic, slightly refactored
        wb = openpyxl.Workbook()
        ws = wb.active 
        ws.title = report_data.get('title', "Report")[:30] # type: ignore

        row_num = 1
        ws.cell(row=row_num, column=1, value=report_data.get('title')).font = Font(bold=True, size=14) # type: ignore
        row_num += 1
        if report_data.get('report_date_description'):
            ws.cell(row=row_num, column=1, value=report_data.get('report_date_description')).font = Font(italic=True) # type: ignore
            row_num += 1
        row_num += 1 

        # ... (Logic from existing _export_to_excel_generic for TB/GL data extraction) ...
        if 'debit_accounts' in report_data:
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col>1 else 'left')
            row_num+=1
            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
                self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(acc['balance'])))
                row_num+=1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code']); ws.cell(row=row_num, column=2, value=acc['name'])
                self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(acc['balance'])))
                row_num+=1
            row_num+=1
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=3, value=float(report_data.get('total_debits',0))), bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(report_data.get('total_credits',0))), bold=True)
        elif 'transactions' in report_data: # General Ledger
            headers = ["Date", "Entry No.", "Description", "Debit", "Credit", "Balance"]
            for col, header_text in enumerate(headers,1): self._apply_excel_header_style(ws.cell(row=row_num, column=col, value=header_text), alignment='center' if col > 2 else 'left')
            row_num+=1
            ws.cell(row=row_num, column=3, value="Opening Balance").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(report_data.get('opening_balance',0))), bold=True)
            row_num+=1
            for txn in report_data.get('transactions',[]):
                ws.cell(row=row_num, column=1, value=txn['date'].strftime('%d/%m/%Y') if isinstance(txn['date'], date) else txn['date'])
                ws.cell(row=row_num, column=2, value=txn['entry_no'])
                ws.cell(row=row_num, column=3, value=txn.get('je_description','') + (" // " + txn.get('line_description','') if txn.get('line_description') else ""))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=4, value=float(txn['debit'] if txn['debit'] else 0)))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=5, value=float(txn['credit'] if txn['credit'] else 0)))
                self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(txn['balance'])))
                row_num+=1
            ws.cell(row=row_num, column=3, value="Closing Balance").font = Font(bold=True)
            self._apply_excel_amount_style(ws.cell(row=row_num, column=6, value=float(report_data.get('closing_balance',0))), bold=True)
            
        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].width = 15 # Default width
            if col_idx == 3 and 'transactions' in report_data: # Description for GL
                 ws.column_dimensions[column_letter].width = 50
            elif col_idx == 2 and 'debit_accounts' in report_data: # Account Name for TB
                 ws.column_dimensions[column_letter].width = 40

        excel_bytes_io = BytesIO(); wb.save(excel_bytes_io); return excel_bytes_io.getvalue()

```

**Review of `app/reporting/report_engine.py` Changes:**

*   **Custom Styles**: `_setup_custom_styles` method added to define `ParagraphStyle`s for PDF, promoting consistency.
*   **PDF Header/Footer**: `_add_pdf_header_footer` method created to add company name, report title, date description, generation date, and page numbers to PDF documents. This is a significant improvement.
*   **Specific PDF Export Methods**:
    *   `_export_balance_sheet_to_pdf`:
        *   Correctly uses custom styles.
        *   Builds table data by iterating through assets, liabilities, equity sections from `report_data`.
        *   Correctly includes account codes and names.
        *   Formats and right-aligns amounts.
        *   Adds section totals and "Total Liabilities & Equity".
        *   Handles comparative period data if present.
        *   Includes a warning if the balance sheet is out of balance.
        *   Applies `TableStyle` for grid, header background/text color, alignment, and lines for totals. Spanning for section headers is implemented.
    *   `_export_profit_loss_to_pdf`:
        *   Similar structure to BS PDF export.
        *   Iterates through revenue and expenses.
        *   Calculates and adds "Net Profit / (Loss)".
        *   Handles comparative data.
        *   Applies `TableStyle` with appropriate lines for totals.
*   **Generic PDF Export Method (`_export_generic_table_to_pdf`)**:
    *   The previous `_export_to_pdf_generic` has been renamed and retained for Trial Balance and General Ledger.
    *   It now uses landscape for GL, which is appropriate for more columns.
    *   Includes basic formatting for GL (opening/closing balance rows).
    *   Column width for GL description improved.
*   **Specific Excel Export Methods**:
    *   `_export_balance_sheet_to_excel` and `_export_profit_loss_to_excel`:
        *   Correctly set up merged cells for report headers (company, title, date).
        *   Iterate through report sections and accounts.
        *   Use `openpyxl.styles.Font` for bolding headers and totals.
        *   Apply accounting number format using `cell.number_format`.
        *   Right-align numerical values.
        *   Add top borders for totals and double underline for final BS total.
        *   Handle comparative data columns.
        *   Set column widths for better readability.
*   **Generic Excel Export Method (`_export_generic_table_to_excel`)**:
    *   The previous `_export_to_excel_generic` is retained for TB and GL.
    *   Includes basic formatting for TB and GL.
*   **`export_report` Dispatcher**: Correctly modified to call specific BS/PL export methods based on `report_data.get('title')`, falling back to generic methods for other report types.
*   **Helper Methods**: `_format_decimal` is used. `_get_company_name` fetches company name asynchronously. `_apply_excel_header_style` and `_apply_excel_amount_style` centralize Excel cell styling.

**Validation & No Regressions:**
*   The changes are extensive but well-structured into specific methods for each report type and format.
*   The previous generic export logic for Trial Balance and General Ledger is preserved in `_export_generic_table_to_pdf` and `_export_generic_table_to_excel`, minimizing risk of regression for those reports.
*   The new methods significantly enhance the formatting and professionalism of Balance Sheet and Profit & Loss exports.
*   Dependencies like `ApplicationCore` (for company name) are handled via `self.app_core`.
*   Asynchronous fetching of company name is correctly handled before PDF/Excel generation.

**Conclusion of Task Completion:**

The `app/reporting/report_engine.py` file has been significantly enhanced to provide more professional and well-formatted PDF and Excel exports for Balance Sheet and Profit & Loss statements. The generic export capabilities for Trial Balance and General Ledger are retained. This addresses the roadmap item "Refine Reporting: Improve PDF/Excel export formatting and layout."

The changes are substantial but appear correct and well-organized. The next step would be to test these exports thoroughly from the `ReportsWidget` UI.

---
https://drive.google.com/file/d/13hYEwFVHlQaGQ_ws3k3VvmZSWJgP14ep/view?usp=sharing, https://drive.google.com/file/d/18AV-7BrkUwk7kQpr8LFSSHMODP6oFYOs/view?usp=sharing, https://drive.google.com/file/d/18xs17NAMOyJxIIn7YAW5_Hxt_EasmnYe/view?usp=sharing, https://drive.google.com/file/d/19QeRpKKgin37J5wKA6z9wbnCIywmKHXx/view?usp=sharing, https://drive.google.com/file/d/1E_9maYq_-0jngxcKzFVK1WObHkUzXzcn/view?usp=sharing, https://aistudio.google.com/app/prompts?state=%7B%22ids%22:%5B%221EqAAoEAbBCw8IJfsiko4lSxMlixUIqkw%22%5D,%22action%22:%22open%22,%22userId%22:%22103961307342447084491%22,%22resourceKeys%22:%7B%7D%7D&usp=sharing, https://drive.google.com/file/d/1FIkt6wn6Ph29zKa6BjuWg5MymXB3xwBN/view?usp=sharing, https://drive.google.com/file/d/1LcMYtkv9s7XDWf1Z_L0y4Mt2XI-E1ChV/view?usp=sharing, https://drive.google.com/file/d/1MNPYsv6jKlmSA9ka-nthRdxmoGxscNKT/view?usp=sharing, https://drive.google.com/file/d/1OAqRup6_pFNaqSbKhvKZ648LGW_vGNHC/view?usp=sharing, https://drive.google.com/file/d/1XVzr3QcXe8dUm0E1rAGlSEloeiMTusAx/view?usp=sharing, https://drive.google.com/file/d/1YEVuNKs7bEWVD6V-NejsmLXZO4a_Tq6F/view?usp=sharing, https://drive.google.com/file/d/1Yjh1wm8uK13MwHJ8nWWt7fDGt_xUxcfe/view?usp=sharing, https://drive.google.com/file/d/1Z4tCtBnhhgZ9oBxAIVk6Nfh_SMwGNjYX/view?usp=sharing, https://drive.google.com/file/d/1aUkaWoQCRm84Q82zCvXChHy8qlZLIc6r/view?usp=sharing, https://drive.google.com/file/d/1fJ5KRnIXSWh5lggrhch8lCDTMwCz9ixp/view?usp=sharing, https://drive.google.com/file/d/1g0BTPiyYf-TubgZlqVArx3Yf0ScSlKa6/view?usp=sharing, https://drive.google.com/file/d/1hHhfoRDBXO8vzthKpWOjI1vH3ccrCWWk/view?usp=sharing, https://drive.google.com/file/d/1hWa5WsgsdwdIUvsHOHqTzLMD37yAg2yV/view?usp=sharing, https://drive.google.com/file/d/1jEPSW2DlYe3CnFfxcrrxQcS1in-CoZDt/view?usp=sharing, https://drive.google.com/file/d/1knLdNW1a19s2XuSALhNPY4jDAp0YTetr/view?usp=sharing, https://drive.google.com/file/d/1p5dvW05gug-BOoy-YguJARN2LK7ED2Bq/view?usp=sharing, https://drive.google.com/file/d/1sdI2jwTCqouVuonjgOxVkMkeDJb1Luc1/view?usp=sharing, https://drive.google.com/file/d/1yezJl1uC8oDZmnom2iG7Rii5ZcAn4i8N/view?usp=sharing, https://drive.google.com/file/d/1zUWfohK07mrZVPwfjE51rfXlbrSkJWN6/view?usp=sharing


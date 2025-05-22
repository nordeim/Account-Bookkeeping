# File: app/reporting/report_engine.py
# (Content previously generated, ensure ApplicationCore type hint, Decimal handling in export)
from typing import Dict, Any, Literal, List # Added List
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # type: ignore
from reportlab.lib import colors 
from reportlab.lib.pagesizes import A4 # Changed to A4
from reportlab.lib.units import inch, cm # Added cm
from io import BytesIO
import openpyxl 
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill # For styling Excel
from openpyxl.utils import get_column_letter 
from app.core.application_core import ApplicationCore # For app_core type hint
from decimal import Decimal # For number formatting

class ReportEngine:
    def __init__(self, app_core: ApplicationCore):
        self.app_core = app_core
        # print("ReportEngine initialized.") # Optional

    async def export_report(self, report_data: Dict[str, Any], format_type: Literal["pdf", "excel"]) -> bytes: # Removed CSV for now
        if format_type == "pdf":
            # Assuming report_data is structured for a generic financial report
            return self._export_to_pdf_generic(report_data)
        elif format_type == "excel":
            return self._export_to_excel_generic(report_data)
        else:
            raise ValueError(f"Unsupported report format: {format_type}")

    def _format_decimal(self, value: Optional[Decimal], places: int = 2) -> str:
        if value is None: return ""
        if not isinstance(value, Decimal): value = Decimal(str(value))
        return f"{value:,.{places}f}"

    def _export_to_pdf_generic(self, report_data: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=inch, leftMargin=inch,
                                topMargin=inch, bottomMargin=inch)
        styles = getSampleStyleSheet()
        story = []

        title = report_data.get('title', "Financial Report")
        date_desc = report_data.get('report_date_description', "")
        
        story.append(Paragraph(title, styles['h1']))
        if date_desc:
            story.append(Paragraph(date_desc, styles['h3']))
        story.append(Spacer(1, 0.5*cm))

        # Example: Generic handling for sections with accounts and totals
        # This needs to be made more robust based on actual report_data structures
        # (e.g., from Balance Sheet, P&L)
        
        # This is a placeholder, specific report structures (BS, P&L) need dedicated PDF layouts
        if 'assets' in report_data and 'liabilities' in report_data: # Balance Sheet like
            data = [["Section", "Account Code", "Account Name", "Amount"]]
            for section_name in ['assets', 'liabilities', 'equity']:
                section = report_data.get(section_name, {})
                data.append([Paragraph(section_name.title(), styles['h2']), "", "", ""])
                for acc in section.get('accounts', []):
                    data.append(["", acc['code'], acc['name'], self._format_decimal(acc['balance'])])
                data.append(["", "", Paragraph(f"Total {section_name.title()}", styles['Heading3']), 
                             Paragraph(self._format_decimal(section.get('total')), styles['Heading3'])])
            # ... Add more for comparative, totals, etc.
        elif 'revenue' in report_data and 'expenses' in report_data: # P&L like
             # Similar tabular layout for P&L sections
             pass
        elif 'debit_accounts' in report_data: # Trial Balance like
            data = [["Account Code", "Account Name", "Debit", "Credit"]]
            for acc in report_data.get('debit_accounts', []):
                data.append([acc['code'], acc['name'], self._format_decimal(acc['balance']), ""])
            for acc in report_data.get('credit_accounts', []):
                data.append([acc['code'], acc['name'], "", self._format_decimal(acc['balance'])])
            data.append(["", Paragraph("TOTALS", styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_debits')), styles['Heading3']), 
                         Paragraph(self._format_decimal(report_data.get('total_credits')), styles['Heading3'])])
        else:
            story.append(Paragraph("Report data structure not recognized for PDF export.", styles['Normal']))


        if 'data' in locals() and data: # Check if data was populated
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#4F81BD")), # Header bg
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('ALIGN', (2,1), (-1,-1), 'RIGHT'), # Amounts right for TB
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('LEFTPADDING', (0,0), (-1,-1), 6),
                ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ]))
            story.append(table)
        
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    def _export_to_excel_generic(self, report_data: Dict[str, Any]) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active # type: ignore
        
        title = report_data.get('title', "Financial Report")
        ws.title = title[:30] 

        row_num = 1
        ws.cell(row=row_num, column=1, value=title).font = Font(bold=True, size=14)
        row_num += 1
        date_desc = report_data.get('report_date_description', "")
        if date_desc:
            ws.cell(row=row_num, column=1, value=date_desc).font = Font(italic=True)
            row_num += 1
        row_num += 1 # Spacer

        # Placeholder for generic Excel export structure, similar to PDF one
        if 'debit_accounts' in report_data: # Trial Balance like
            headers = ["Account Code", "Account Name", "Debit", "Credit"]
            for col_num, header in enumerate(headers, 1):
                ws.cell(row=row_num, column=col_num, value=header).font = Font(bold=True)
            row_num += 1

            for acc in report_data.get('debit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code'])
                ws.cell(row=row_num, column=2, value=acc['name'])
                ws.cell(row=row_num, column=3, value=acc['balance']).number_format = '#,##0.00'
                row_num += 1
            for acc in report_data.get('credit_accounts', []):
                ws.cell(row=row_num, column=1, value=acc['code'])
                ws.cell(row=row_num, column=2, value=acc['name'])
                ws.cell(row=row_num, column=4, value=acc['balance']).number_format = '#,##0.00'
                row_num += 1
            
            row_num +=1 # Spacer
            ws.cell(row=row_num, column=2, value="TOTALS").font = Font(bold=True)
            ws.cell(row=row_num, column=3, value=report_data.get('total_debits', 0)).font = Font(bold=True); ws.cell(row=row_num, column=3).number_format = '#,##0.00'
            ws.cell(row=row_num, column=4, value=report_data.get('total_credits', 0)).font = Font(bold=True); ws.cell(row=row_num, column=4).number_format = '#,##0.00'
        else:
            ws.cell(row=row_num, column=1, value="Report data structure not recognized for Excel export.")


        for col_idx in range(1, ws.max_column + 1): # type: ignore
            column_letter = get_column_letter(col_idx)
            ws.column_dimensions[column_letter].autosize = True
            
        excel_bytes_io = BytesIO()
        wb.save(excel_bytes_io)
        excel_bytes = excel_bytes_io.getvalue()
        excel_bytes_io.close()
        return excel_bytes

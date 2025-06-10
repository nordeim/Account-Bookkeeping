# File: app/tax/withholding_tax_manager.py
from typing import TYPE_CHECKING, Dict, Any
from app.models.business.payment import Payment # For type hint

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore 
    from app.services.journal_service import JournalService 
    from app.services.tax_service import TaxCodeService

class WithholdingTaxManager:
    def __init__(self, app_core: "ApplicationCore"): 
        self.app_core = app_core
        self.tax_code_service: "TaxCodeService" = app_core.tax_code_service # type: ignore
        self.journal_service: "JournalService" = app_core.journal_service # type: ignore 
        self.logger = app_core.logger
        self.logger.info("WithholdingTaxManager initialized.")

    async def generate_s45_form_data(self, payment: Payment) -> Dict[str, Any]:
        """
        Generates a dictionary of data required for IRAS Form S45, based on a vendor payment.
        """
        self.logger.info(f"Generating S45 form data for Payment ID {payment.id}")
        
        if not payment or not payment.vendor:
            self.logger.error(f"Cannot generate S45 data: Payment {payment.id} or its vendor is not loaded.")
            return {}

        # The amount subject to WHT is the gross amount of the invoice(s) paid, not the net cash outflow.
        # This manager needs the gross amount before WHT was deducted. The `payment.amount` is the gross.
        gross_payment_amount = payment.amount
        
        # A full implementation would need to determine the WHT rate from the payment or related invoices/vendor.
        # For now, this is a conceptual data structure.
        vendor = payment.vendor
        wht_rate = vendor.withholding_tax_rate if vendor.withholding_tax_applicable else None
        
        if wht_rate is None:
             self.logger.warning(f"Vendor '{vendor.name}' has no WHT rate specified for Payment ID {payment.id}.")
             wht_amount = 0
        else:
             wht_amount = (gross_payment_amount * wht_rate) / 100

        # Assuming payee details come from the Vendor record
        payee_details = {
            "name": vendor.name,
            "address": f"{vendor.address_line1 or ''}, {vendor.address_line2 or ''}".strip(", "),
            "tax_ref_no": vendor.uen_no or "N/A", # UEN as tax reference
        }

        # Payer details would come from Company Settings
        company_settings = await self.app_core.company_settings_service.get_company_settings()
        payer_details = {
            "name": company_settings.company_name if company_settings else "N/A",
            "tax_ref_no": company_settings.uen_no if company_settings else "N/A",
        }

        form_data = {
            "s45_payee_name": payee_details["name"],
            "s45_payee_address": payee_details["address"],
            "s45_payee_tax_ref": payee_details["tax_ref_no"],
            "s45_payer_name": payer_details["name"],
            "s45_payer_tax_ref": payer_details["tax_ref_no"],
            "s45_payment_date": payment.payment_date,
            "s45_nature_of_payment": "Director's Remuneration or Fees", # This needs to be determined based on context
            "s45_gross_payment": gross_payment_amount,
            "s45_wht_rate_percent": wht_rate,
            "s45_wht_amount": wht_amount,
        }
        self.logger.info(f"S45 data generated for Payment ID {payment.id}: {form_data}")
        return form_data

    async def record_wht_payment(self, certificate_id: int, payment_date: str, reference: str):
        """
        This method would be responsible for creating the journal entry when the withheld tax
        is actually paid to IRAS. This is a separate process from the initial payment to the vendor.
        """
        self.logger.info(f"Recording WHT payment for certificate {certificate_id} (stub).")
        # Logic would involve:
        # 1. Fetching the WHT certificate/liability record.
        # 2. Creating a JE: Dr WHT Payable, Cr Bank.
        # 3. Posting the JE.
        # 4. Updating the certificate status to 'Paid'.
        return True

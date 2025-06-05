# File: app/business_logic/payment_manager.py
from typing import List, Optional, Dict, Any, TYPE_CHECKING, Union, cast
from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from app.models.business.payment import Payment, PaymentAllocation
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
# REMOVED: from app.models.accounting.account import Account # Not directly used by PaymentManager
from app.models.accounting.journal_entry import JournalEntry 
# REMOVED: from app.models.business.bank_account import BankAccount # Not directly used by PaymentManager

# REMOVED: from app.services.business_services import (
#     PaymentService, BankAccountService, CustomerService, VendorService,
#     SalesInvoiceService, PurchaseInvoiceService
# )
# REMOVED: from app.services.core_services import SequenceService, ConfigurationService
# REMOVED: from app.services.account_service import AccountService
# REMOVED: from app.accounting.journal_entry_manager import JournalEntryManager 

from app.utils.result import Result
from app.utils.pydantic_models import (
    PaymentCreateData, PaymentSummaryData, PaymentAllocationBaseData,
    JournalEntryData, JournalEntryLineData
)
from app.common.enums import (
    PaymentEntityTypeEnum, PaymentTypeEnum, PaymentStatusEnum,
    InvoiceStatusEnum, JournalTypeEnum, PaymentAllocationDocTypeEnum 
)

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore
    from sqlalchemy.ext.asyncio import AsyncSession 
    from app.services.business_services import (
        PaymentService, BankAccountService, CustomerService, VendorService,
        SalesInvoiceService, PurchaseInvoiceService
    )
    from app.services.core_services import SequenceService, ConfigurationService
    from app.services.account_service import AccountService
    from app.accounting.journal_entry_manager import JournalEntryManager 

class PaymentManager:
    def __init__(self,
                 payment_service: "PaymentService",
                 sequence_service: "SequenceService",
                 bank_account_service: "BankAccountService",
                 customer_service: "CustomerService",
                 vendor_service: "VendorService",
                 sales_invoice_service: "SalesInvoiceService",
                 purchase_invoice_service: "PurchaseInvoiceService",
                 journal_entry_manager: "JournalEntryManager",
                 account_service: "AccountService",
                 configuration_service: "ConfigurationService",
                 app_core: "ApplicationCore"):
        self.payment_service = payment_service
        self.sequence_service = sequence_service
        self.bank_account_service = bank_account_service
        self.customer_service = customer_service
        self.vendor_service = vendor_service
        self.sales_invoice_service = sales_invoice_service
        self.purchase_invoice_service = purchase_invoice_service
        self.journal_entry_manager = journal_entry_manager
        self.account_service = account_service
        self.configuration_service = configuration_service
        self.app_core = app_core
        self.logger = app_core.logger

    async def _validate_payment_data(self, dto: PaymentCreateData, session: "AsyncSession") -> List[str]:
        errors: List[str] = []
        
        entity_name_for_desc: str = "Entity"
        if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
            entity = await self.customer_service.get_by_id(dto.entity_id) 
            if not entity or not entity.is_active: errors.append(f"Active Customer ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
            entity = await self.vendor_service.get_by_id(dto.entity_id) 
            if not entity or not entity.is_active: errors.append(f"Active Vendor ID {dto.entity_id} not found.")
            else: entity_name_for_desc = entity.name
        
        if dto.payment_method != PaymentMethodEnum.CASH: 
            if not dto.bank_account_id: errors.append("Bank Account is required for non-cash payments.")
            else:
                bank_acc = await self.bank_account_service.get_by_id(dto.bank_account_id) 
                if not bank_acc or not bank_acc.is_active: errors.append(f"Active Bank Account ID {dto.bank_account_id} not found.")
                elif bank_acc.currency_code != dto.currency_code: errors.append(f"Payment currency ({dto.currency_code}) does not match bank account currency ({bank_acc.currency_code}).")
        
        currency = await self.app_core.currency_manager.get_currency_by_code(dto.currency_code)
        if not currency or not currency.is_active: errors.append(f"Currency '{dto.currency_code}' is invalid or inactive.")

        total_allocated = Decimal(0)
        for i, alloc_dto in enumerate(dto.allocations):
            total_allocated += alloc_dto.amount_allocated
            invoice_orm: Union[SalesInvoice, PurchaseInvoice, None] = None
            doc_type_str = ""
            if alloc_dto.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE:
                invoice_orm = await self.sales_invoice_service.get_by_id(alloc_dto.document_id) 
                doc_type_str = "Sales Invoice"
            elif alloc_dto.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE:
                invoice_orm = await self.purchase_invoice_service.get_by_id(alloc_dto.document_id) 
                doc_type_str = "Purchase Invoice"
            
            if not invoice_orm: errors.append(f"Allocation {i+1}: {doc_type_str} ID {alloc_dto.document_id} not found.")
            elif invoice_orm.status not in [InvoiceStatusEnum.APPROVED, InvoiceStatusEnum.PARTIALLY_PAID, InvoiceStatusEnum.OVERDUE]:
                errors.append(f"Allocation {i+1}: {doc_type_str} {invoice_orm.invoice_no} is not in an allocatable status ({invoice_orm.status.value}).") 
            elif isinstance(invoice_orm, SalesInvoice) and invoice_orm.customer_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Sales Invoice {invoice_orm.invoice_no} does not belong to selected customer.")
            elif isinstance(invoice_orm, PurchaseInvoice) and invoice_orm.vendor_id != dto.entity_id:
                 errors.append(f"Allocation {i+1}: Purchase Invoice {invoice_orm.invoice_no} does not belong to selected vendor.")
            elif (invoice_orm.total_amount - invoice_orm.amount_paid) < alloc_dto.amount_allocated:
                 outstanding_bal = invoice_orm.total_amount - invoice_orm.amount_paid
                 errors.append(f"Allocation {i+1}: Amount for {doc_type_str} {invoice_orm.invoice_no} ({alloc_dto.amount_allocated:.2f}) exceeds outstanding balance ({outstanding_bal:.2f}).")
        
        if total_allocated > dto.amount:
            errors.append(f"Total allocated amount ({total_allocated}) cannot exceed total payment amount ({dto.amount}).")
        
        return errors

    async def create_payment(self, dto: PaymentCreateData) -> Result[Payment]:
        async with self.app_core.db_manager.session() as session: 
            try:
                validation_errors = await self._validate_payment_data(dto, session=session)
                if validation_errors:
                    return Result.failure(validation_errors)

                payment_no_str = await self.app_core.db_manager.execute_scalar("SELECT core.get_next_sequence_value($1);", "payment", session=session)
                if not payment_no_str: return Result.failure(["Failed to generate payment number."])

                cash_or_bank_gl_id: Optional[int] = None
                ar_ap_gl_id: Optional[int] = None
                entity_name_for_desc: str = "Entity"

                if dto.payment_method != PaymentMethodEnum.CASH:
                    bank_account = await self.bank_account_service.get_by_id(dto.bank_account_id) # type: ignore
                    if not bank_account or not bank_account.gl_account_id: return Result.failure(["Bank account or its GL link not found."])
                    cash_or_bank_gl_id = bank_account.gl_account_id
                else: 
                    cash_acc_code = await self.configuration_service.get_config_value("SysAcc_DefaultCash", "1112") 
                    cash_gl_acc = await self.account_service.get_by_code(cash_acc_code) if cash_acc_code else None
                    if not cash_gl_acc or not cash_gl_acc.is_active: return Result.failure([f"Default Cash account ({cash_acc_code}) not configured or inactive."])
                    cash_or_bank_gl_id = cash_gl_acc.id

                if dto.entity_type == PaymentEntityTypeEnum.CUSTOMER:
                    customer = await self.customer_service.get_by_id(dto.entity_id)
                    if not customer or not customer.receivables_account_id: return Result.failure(["Customer AR account not found."])
                    ar_ap_gl_id = customer.receivables_account_id
                    entity_name_for_desc = customer.name
                elif dto.entity_type == PaymentEntityTypeEnum.VENDOR:
                    vendor = await self.vendor_service.get_by_id(dto.entity_id)
                    if not vendor or not vendor.payables_account_id: return Result.failure(["Vendor AP account not found."])
                    ar_ap_gl_id = vendor.payables_account_id
                    entity_name_for_desc = vendor.name
                
                if not cash_or_bank_gl_id or not ar_ap_gl_id:
                    return Result.failure(["Could not determine all necessary GL accounts for the payment journal."])

                payment_orm = Payment(
                    payment_no=payment_no_str, payment_type=dto.payment_type.value,
                    payment_method=dto.payment_method.value, payment_date=dto.payment_date,
                    entity_type=dto.entity_type.value, entity_id=dto.entity_id,
                    bank_account_id=dto.bank_account_id, currency_code=dto.currency_code,
                    exchange_rate=dto.exchange_rate, amount=dto.amount, reference=dto.reference,
                    description=dto.description, cheque_no=dto.cheque_no,
                    status=PaymentStatusEnum.APPROVED.value, 
                    created_by_user_id=dto.user_id, updated_by_user_id=dto.user_id
                )
                for alloc_dto in dto.allocations:
                    payment_orm.allocations.append(PaymentAllocation(
                        document_type=alloc_dto.document_type.value,
                        document_id=alloc_dto.document_id,
                        amount=alloc_dto.amount_allocated,
                        created_by_user_id=dto.user_id 
                    ))
                
                je_lines_data: List[JournalEntryLineData] = []
                desc_suffix = f"Pmt No: {payment_no_str} for {entity_name_for_desc}"
                
                if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Customer Receipt - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Clear A/R - {desc_suffix}"))
                elif dto.payment_type == PaymentTypeEnum.VENDOR_PAYMENT: 
                    je_lines_data.append(JournalEntryLineData(account_id=ar_ap_gl_id, debit_amount=dto.amount, credit_amount=Decimal(0), description=f"Clear A/P - {desc_suffix}"))
                    je_lines_data.append(JournalEntryLineData(account_id=cash_or_bank_gl_id, debit_amount=Decimal(0), credit_amount=dto.amount, description=f"Vendor Payment - {desc_suffix}"))
                
                je_dto = JournalEntryData(
                    journal_type=JournalTypeEnum.CASH_RECEIPT.value if dto.payment_type == PaymentTypeEnum.CUSTOMER_PAYMENT else JournalTypeEnum.CASH_DISBURSEMENT.value,
                    entry_date=dto.payment_date, description=f"{dto.payment_type.value} - {entity_name_for_desc}",
                    reference=dto.reference or payment_no_str, user_id=dto.user_id, lines=je_lines_data,
                    source_type="Payment", source_id=0 
                )
                
                saved_payment = await self.payment_service.save(payment_orm, session=session)
                je_dto.source_id = saved_payment.id 

                create_je_result = await self.journal_entry_manager.create_journal_entry(je_dto, session=session)
                if not create_je_result.is_success or not create_je_result.value:
                    raise Exception(f"Failed to create JE for payment: {', '.join(create_je_result.errors)}") 
                
                created_je: JournalEntry = create_je_result.value
                post_je_result = await self.journal_entry_manager.post_journal_entry(created_je.id, dto.user_id, session=session)
                if not post_je_result.is_success:
                    raise Exception(f"JE (ID: {created_je.id}) created but failed to post: {', '.join(post_je_result.errors)}")

                saved_payment.journal_entry_id = created_je.id
                session.add(saved_payment) 
                
                for alloc_orm in saved_payment.allocations:
                    if alloc_orm.document_type == PaymentAllocationDocTypeEnum.SALES_INVOICE.value:
                        inv = await session.get(SalesInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)
                    elif alloc_orm.document_type == PaymentAllocationDocTypeEnum.PURCHASE_INVOICE.value:
                        inv = await session.get(PurchaseInvoice, alloc_orm.document_id)
                        if inv: 
                            inv.amount_paid = (inv.amount_paid or Decimal(0)) + alloc_orm.amount
                            inv.status = InvoiceStatusEnum.PAID.value if inv.amount_paid >= inv.total_amount else InvoiceStatusEnum.PARTIALLY_PAID.value
                            session.add(inv)

                await session.flush()
                await session.refresh(saved_payment, attribute_names=['allocations', 'journal_entry']) 
                
                self.logger.info(f"Payment '{saved_payment.payment_no}' created and posted successfully. JE ID: {created_je.id}")
                return Result.success(saved_payment)

            except Exception as e:
                self.logger.error(f"Error in create_payment transaction: {e}", exc_info=True)
                return Result.failure([f"Failed to create payment: {str(e)}"])


    async def get_payment_for_dialog(self, payment_id: int) -> Optional[Payment]:
        try:
            return await self.payment_service.get_by_id(payment_id)
        except Exception as e:
            self.logger.error(f"Error fetching Payment ID {payment_id} for dialog: {e}", exc_info=True)
            return None

    async def get_payments_for_listing(
        self,
        entity_type: Optional[PaymentEntityTypeEnum] = None,
        entity_id: Optional[int] = None,
        status: Optional[PaymentStatusEnum] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Result[List[PaymentSummaryData]]:
        try:
            summaries = await self.payment_service.get_all_summary(
                entity_type=entity_type, entity_id=entity_id, status=status,
                start_date=start_date, end_date=end_date,
                page=page, page_size=page_size
            )
            return Result.success(summaries)
        except Exception as e:
            self.logger.error(f"Error fetching payment listing: {e}", exc_info=True)
            return Result.failure([f"Failed to retrieve payment list: {str(e)}"])

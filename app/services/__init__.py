# File: app/services/__init__.py
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Generic, TypeVar, Dict, Tuple 
from datetime import date, datetime 
from decimal import Decimal 
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar('T') 
ID = TypeVar('ID') 

class IRepository(ABC, Generic[T, ID]):
    @abstractmethod
    async def get_by_id(self, id_val: ID) -> Optional[T]: pass
    @abstractmethod
    async def get_all(self) -> List[T]: pass
    @abstractmethod
    async def add(self, entity: T) -> T: pass
    @abstractmethod
    async def update(self, entity: T) -> T: pass
    @abstractmethod
    async def delete(self, id_val: ID) -> bool: pass

# --- ORM Model Imports ---
from app.models.accounting.account import Account
from app.models.accounting.journal_entry import JournalEntry, JournalEntryLine 
from app.models.accounting.fiscal_period import FiscalPeriod
from app.models.accounting.tax_code import TaxCode
from app.models.core.company_setting import CompanySetting 
from app.models.accounting.gst_return import GSTReturn
from app.models.accounting.recurring_pattern import RecurringPattern
from app.models.accounting.fiscal_year import FiscalYear 
from app.models.accounting.account_type import AccountType 
from app.models.accounting.currency import Currency 
from app.models.accounting.exchange_rate import ExchangeRate 
from app.models.core.sequence import Sequence 
from app.models.core.configuration import Configuration 
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice
from app.models.business.purchase_invoice import PurchaseInvoice
from app.models.business.inventory_movement import InventoryMovement
from app.models.accounting.dimension import Dimension 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction 
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.audit.audit_log import AuditLog 
from app.models.audit.data_change_history import DataChangeHistory 
from app.models.business.bank_reconciliation import BankReconciliation

# --- DTO Imports (for return types in interfaces) ---
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData,
    AuditLogEntryData, DataChangeHistoryEntryData, BankReconciliationData,
    BankReconciliationSummaryData, 
    DashboardKPIData
)
from app.utils.result import Result 
from app.common.enums import ( 
    ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum,
    PaymentTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum, DataChangeTypeEnum 
)

# --- Interfaces ---
class IAccountRepository(IRepository[Account, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Account]: pass
    @abstractmethod
    async def get_all_active(self) -> List[Account]: pass
    @abstractmethod
    async def get_by_type(self, account_type: str, active_only: bool = True) -> List[Account]: pass
    @abstractmethod
    async def save(self, account: Account) -> Account: pass 
    @abstractmethod
    async def get_account_tree(self, active_only: bool = True) -> List[Dict[str, Any]]: pass 
    @abstractmethod
    async def has_transactions(self, account_id: int) -> bool: pass
    @abstractmethod
    async def get_accounts_by_tax_treatment(self, tax_treatment_code: str) -> List[Account]: pass
    @abstractmethod
    async def get_total_balance_by_account_category_and_type_pattern(self, account_category: str, account_type_name_like: str, as_of_date: date) -> Decimal: pass

class IJournalEntryRepository(IRepository[JournalEntry, int]): 
    @abstractmethod
    async def get_by_entry_no(self, entry_no: str) -> Optional[JournalEntry]: pass
    @abstractmethod
    async def get_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def get_posted_entries_by_date_range(self, start_date: date, end_date: date) -> List[JournalEntry]: pass
    @abstractmethod
    async def save(self, journal_entry: JournalEntry) -> JournalEntry: pass
    @abstractmethod
    async def get_account_balance(self, account_id: int, as_of_date: date) -> Decimal: pass
    @abstractmethod
    async def get_account_balance_for_period(self, account_id: int, start_date: date, end_date: date) -> Decimal: pass
    @abstractmethod
    async def get_recurring_patterns_due(self, as_of_date: date) -> List[RecurringPattern]: pass
    @abstractmethod
    async def save_recurring_pattern(self, pattern: RecurringPattern) -> RecurringPattern: pass
    @abstractmethod
    async def get_all_summary(self, start_date_filter: Optional[date] = None, 
                              end_date_filter: Optional[date] = None, 
                              status_filter: Optional[str] = None,
                              entry_no_filter: Optional[str] = None,
                              description_filter: Optional[str] = None,
                              journal_type_filter: Optional[str] = None
                             ) -> List[Dict[str, Any]]: pass
    @abstractmethod
    async def get_posted_lines_for_account_in_range(self, account_id: int, start_date: date, end_date: date, 
                                                    dimension1_id: Optional[int] = None, dimension2_id: Optional[int] = None
                                                    ) -> List[JournalEntryLine]: pass 

class IFiscalPeriodRepository(IRepository[FiscalPeriod, int]): 
    @abstractmethod
    async def get_by_date(self, target_date: date) -> Optional[FiscalPeriod]: pass
    @abstractmethod
    async def get_fiscal_periods_for_year(self, fiscal_year_id: int, period_type: Optional[str] = None) -> List[FiscalPeriod]: pass

class IFiscalYearRepository(IRepository[FiscalYear, int]): 
    @abstractmethod
    async def get_by_name(self, year_name: str) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def get_by_date_overlap(self, start_date: date, end_date: date, exclude_id: Optional[int] = None) -> Optional[FiscalYear]: pass
    @abstractmethod
    async def save(self, entity: FiscalYear) -> FiscalYear: pass

class ITaxCodeRepository(IRepository[TaxCode, int]): 
    @abstractmethod
    async def get_tax_code(self, code: str) -> Optional[TaxCode]: pass
    @abstractmethod
    async def save(self, entity: TaxCode) -> TaxCode: pass 

class ICompanySettingsRepository(IRepository[CompanySetting, int]): 
    @abstractmethod
    async def get_company_settings(self, settings_id: int = 1) -> Optional[CompanySetting]: pass
    @abstractmethod
    async def save_company_settings(self, settings_obj: CompanySetting) -> CompanySetting: pass

class IGSTReturnRepository(IRepository[GSTReturn, int]): 
    @abstractmethod
    async def get_gst_return(self, return_id: int) -> Optional[GSTReturn]: pass 
    @abstractmethod
    async def save_gst_return(self, gst_return_data: GSTReturn) -> GSTReturn: pass

class IAccountTypeRepository(IRepository[AccountType, int]): 
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[AccountType]: pass
    @abstractmethod
    async def get_by_category(self, category: str) -> List[AccountType]: pass

class ICurrencyRepository(IRepository[Currency, str]): 
    @abstractmethod
    async def get_all_active(self) -> List[Currency]: pass

class IExchangeRateRepository(IRepository[ExchangeRate, int]): 
    @abstractmethod
    async def get_rate_for_date(self, from_code: str, to_code: str, r_date: date) -> Optional[ExchangeRate]: pass
    @abstractmethod
    async def save(self, entity: ExchangeRate) -> ExchangeRate: pass

class ISequenceRepository(IRepository[Sequence, int]): 
    @abstractmethod
    async def get_sequence_by_name(self, name: str) -> Optional[Sequence]: pass
    @abstractmethod
    async def save_sequence(self, sequence_obj: Sequence) -> Sequence: pass

class IConfigurationRepository(IRepository[Configuration, int]): 
    @abstractmethod
    async def get_config_by_key(self, key: str) -> Optional[Configuration]: pass
    @abstractmethod
    async def save_config(self, config_obj: Configuration) -> Configuration: pass

class ICustomerRepository(IRepository[Customer, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Customer]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[CustomerSummaryData]: pass
    @abstractmethod
    async def get_total_outstanding_balance(self) -> Decimal: pass
    @abstractmethod 
    async def get_total_overdue_balance(self) -> Decimal: pass
    @abstractmethod
    async def get_ar_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass

class IVendorRepository(IRepository[Vendor, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Vendor]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True,
                              search_term: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[VendorSummaryData]: pass
    @abstractmethod
    async def get_total_outstanding_balance(self) -> Decimal: pass
    @abstractmethod 
    async def get_total_overdue_balance(self) -> Decimal: pass
    @abstractmethod
    async def get_ap_aging_summary(self, as_of_date: date) -> Dict[str, Decimal]: pass

class IProductRepository(IRepository[Product, int]): 
    @abstractmethod
    async def get_by_code(self, code: str) -> Optional[Product]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              active_only: bool = True,
                              product_type_filter: Optional[ProductTypeEnum] = None,
                              search_term: Optional[str] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[ProductSummaryData]: pass

class ISalesInvoiceRepository(IRepository[SalesInvoice, int]):
    @abstractmethod
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              customer_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[SalesInvoiceSummaryData]: pass
    @abstractmethod 
    async def get_outstanding_invoices_for_customer(self, customer_id: Optional[int], as_of_date: date) -> List[SalesInvoice]: pass


class IPurchaseInvoiceRepository(IRepository[PurchaseInvoice, int]):
    @abstractmethod
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: pass 
    @abstractmethod
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              vendor_id: Optional[int] = None,
                              status: Optional[InvoiceStatusEnum] = None, 
                              start_date: Optional[date] = None, 
                              end_date: Optional[date] = None,
                              page: int = 1, 
                              page_size: int = 50
                             ) -> List[PurchaseInvoiceSummaryData]: pass
    @abstractmethod 
    async def get_outstanding_invoices_for_vendor(self, vendor_id: Optional[int], as_of_date: date) -> List[PurchaseInvoice]: pass


class IInventoryMovementRepository(IRepository[InventoryMovement, int]):
    @abstractmethod
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession]=None) -> InventoryMovement: pass

class IDimensionRepository(IRepository[Dimension, int]):
    @abstractmethod
    async def get_distinct_dimension_types(self) -> List[str]: pass
    @abstractmethod
    async def get_dimensions_by_type(self, dim_type: str, active_only: bool = True) -> List[Dimension]: pass
    @abstractmethod
    async def get_by_type_and_code(self, dim_type: str, code: str) -> Optional[Dimension]: pass

class IBankAccountRepository(IRepository[BankAccount, int]):
    @abstractmethod
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]: pass
    @abstractmethod
    async def get_all_summary(self, active_only: bool = True, 
                              currency_code: Optional[str] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[BankAccountSummaryData]: pass
    @abstractmethod
    async def save(self, entity: BankAccount) -> BankAccount: pass
    @abstractmethod # New method for DashboardManager
    async def get_by_gl_account_id(self, gl_account_id: int) -> Optional[BankAccount]: pass


class IBankTransactionRepository(IRepository[BankTransaction, int]):
    @abstractmethod
    async def get_all_for_bank_account(self, bank_account_id: int,
                                       start_date: Optional[date] = None,
                                       end_date: Optional[date] = None,
                                       transaction_type: Optional[BankTransactionTypeEnum] = None,
                                       is_reconciled: Optional[bool] = None,
                                       is_from_statement_filter: Optional[bool] = None, 
                                       page: int = 1, page_size: int = 50
                                      ) -> List[BankTransactionSummaryData]: pass 
    @abstractmethod
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction: pass

class IPaymentRepository(IRepository[Payment, int]):
    @abstractmethod
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]: pass
    @abstractmethod
    async def get_all_summary(self, 
                              entity_type: Optional[PaymentEntityTypeEnum] = None,
                              entity_id: Optional[int] = None,
                              status: Optional[PaymentStatusEnum] = None,
                              start_date: Optional[date] = None,
                              end_date: Optional[date] = None,
                              page: int = 1, page_size: int = 50
                             ) -> List[PaymentSummaryData]: pass
    @abstractmethod
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment: pass

class IAuditLogRepository(IRepository[AuditLog, int]):
    @abstractmethod
    async def get_audit_logs_paginated(
        self, user_id_filter: Optional[int] = None, action_filter: Optional[str] = None, entity_type_filter: Optional[str] = None,
        entity_id_filter: Optional[int] = None, start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[AuditLogEntryData], int]: pass 

class IDataChangeHistoryRepository(IRepository[DataChangeHistory, int]):
    @abstractmethod
    async def get_data_change_history_paginated(
        self, table_name_filter: Optional[str] = None, record_id_filter: Optional[int] = None, changed_by_user_id_filter: Optional[int] = None,
        start_date_filter: Optional[datetime] = None, end_date_filter: Optional[datetime] = None,   
        page: int = 1, page_size: int = 50
    ) -> Tuple[List[DataChangeHistoryEntryData], int]: pass 

class IBankReconciliationRepository(IRepository[BankReconciliation, int]):
    @abstractmethod
    async def get_or_create_draft_reconciliation(
        self, 
        bank_account_id: int, 
        statement_date: date, 
        statement_ending_balance: Decimal, 
        user_id: int, 
        session: AsyncSession
    ) -> BankReconciliation: pass

    @abstractmethod
    async def mark_transactions_as_provisionally_reconciled(
        self, 
        draft_reconciliation_id: int, 
        transaction_ids: List[int], 
        statement_date: date, 
        user_id: int, 
        session: AsyncSession
    ) -> bool: pass

    @abstractmethod
    async def finalize_reconciliation(
        self, 
        draft_reconciliation_id: int, 
        statement_ending_balance: Decimal, 
        calculated_book_balance: Decimal, 
        reconciled_difference: Decimal,
        user_id: int,
        session: AsyncSession
    ) -> Result[BankReconciliation]: pass 

    @abstractmethod
    async def unreconcile_transactions( 
        self, 
        transaction_ids: List[int], 
        user_id: int, 
        session: AsyncSession
    ) -> bool: pass
    
    @abstractmethod 
    async def get_reconciliations_for_account(
        self, 
        bank_account_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[BankReconciliationSummaryData], int]: pass
    
    @abstractmethod 
    async def get_transactions_for_reconciliation(
        self, 
        reconciliation_id: int
    ) -> Tuple[List[BankTransactionSummaryData], List[BankTransactionSummaryData]]: pass


from .account_service import AccountService
from .journal_service import JournalService
from .fiscal_period_service import FiscalPeriodService
from .tax_service import TaxCodeService, GSTReturnService 
from .core_services import SequenceService, ConfigurationService, CompanySettingsService 
from .accounting_services import AccountTypeService, CurrencyService, ExchangeRateService, FiscalYearService, DimensionService
from .business_services import (
    CustomerService, VendorService, ProductService, 
    SalesInvoiceService, PurchaseInvoiceService, InventoryMovementService,
    BankAccountService, BankTransactionService, PaymentService, 
    BankReconciliationService
)
from .audit_services import AuditLogService 

__all__ = [
    "IRepository",
    "IAccountRepository", "IJournalEntryRepository", "IFiscalPeriodRepository", "IFiscalYearRepository",
    "ITaxCodeRepository", "ICompanySettingsRepository", "IGSTReturnRepository",
    "IAccountTypeRepository", "ICurrencyRepository", "IExchangeRateRepository",
    "ISequenceRepository", "IConfigurationRepository", 
    "ICustomerRepository", "IVendorRepository", "IProductRepository",
    "ISalesInvoiceRepository", "IPurchaseInvoiceRepository", 
    "IInventoryMovementRepository", 
    "IDimensionRepository", 
    "IBankAccountRepository", 
    "IBankTransactionRepository", 
    "IPaymentRepository", 
    "IAuditLogRepository", "IDataChangeHistoryRepository", 
    "IBankReconciliationRepository", 
    "AccountService", "JournalService", "FiscalPeriodService", "FiscalYearService",
    "TaxCodeService", "GSTReturnService",
    "SequenceService", "ConfigurationService", "CompanySettingsService",
    "AccountTypeService", "CurrencyService", "ExchangeRateService", "DimensionService", 
    "CustomerService", "VendorService", "ProductService", 
    "SalesInvoiceService", "PurchaseInvoiceService", 
    "InventoryMovementService", 
    "BankAccountService", 
    "BankTransactionService",
    "PaymentService", 
    "AuditLogService", 
    "BankReconciliationService", 
]

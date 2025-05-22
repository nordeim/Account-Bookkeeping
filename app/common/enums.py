# File: app/common/enums.py
# (Content previously generated, verified to be up-to-date with reference schema CHECK constraints)
from enum import Enum

class AccountCategory(Enum): # Matches accounting.account_types.category
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): # Matches accounting.accounts.account_type (which is a category)
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): # Matches accounting.journal_entries.journal_type (examples)
    GENERAL = "General" # Simpler values than "General Journal"
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" # Renamed for consistency
    CASH_DISBURSEMENT = "Cash Disbursement" # Renamed
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): # Matches accounting.fiscal_periods.period_type
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" # This period_type for FiscalPeriod usually represents the whole FY

class FiscalPeriodStatusEnum(Enum): # Matches accounting.fiscal_periods.status
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): # Matches accounting.tax_codes.tax_type
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): # Matches business.products.product_type
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): # Matches accounting.gst_returns.status
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): # Matches business.inventory_movements.movement_type
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): # For Sales and Purchase Invoices
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" # Sales specific
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" # Purchase specific in ref schema

class BankTransactionTypeEnum(Enum): # Matches business.bank_transactions.transaction_type
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): # Matches business.payments.payment_type
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" # Clarified
    OTHER = "Other"

class PaymentMethodEnum(Enum): # Matches business.payments.payment_method
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): # Matches business.payments.entity_type
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): # Matches business.payments.status
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" # Applied / Cleared
    VOIDED = "Voided"
    RETURNED = "Returned" # E.g. bounced cheque

class PaymentAllocationDocTypeEnum(Enum): # Matches business.payment_allocations.document_type
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): # Matches accounting.withholding_tax_certificates.status
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): # Matches audit.data_change_history.change_type
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): # Matches accounting.recurring_patterns.frequency
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

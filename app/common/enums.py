# File: app/common/enums.py
# (Content as previously generated, verified)
from enum import Enum

class AccountCategory(Enum): 
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"

class AccountTypeEnum(Enum): # Matches AccountCategory for now, can diverge
    ASSET = "Asset"
    LIABILITY = "Liability"
    EQUITY = "Equity"
    REVENUE = "Revenue"
    EXPENSE = "Expense"


class JournalTypeEnum(Enum): 
    GENERAL = "General" 
    SALES = "Sales"
    PURCHASE = "Purchase"
    CASH_RECEIPT = "Cash Receipt" 
    CASH_DISBURSEMENT = "Cash Disbursement" 
    PAYROLL = "Payroll"
    OPENING_BALANCE = "Opening Balance"
    ADJUSTMENT = "Adjustment"

class FiscalPeriodTypeEnum(Enum): 
    MONTH = "Month"
    QUARTER = "Quarter"
    YEAR = "Year" 

class FiscalPeriodStatusEnum(Enum): 
    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"

class TaxTypeEnum(Enum): 
    GST = "GST"
    INCOME_TAX = "Income Tax"
    WITHHOLDING_TAX = "Withholding Tax"

class ProductTypeEnum(Enum): 
    INVENTORY = "Inventory"
    SERVICE = "Service"
    NON_INVENTORY = "Non-Inventory"

class GSTReturnStatusEnum(Enum): 
    DRAFT = "Draft"
    SUBMITTED = "Submitted"
    AMENDED = "Amended"

class InventoryMovementTypeEnum(Enum): 
    PURCHASE = "Purchase"
    SALE = "Sale"
    ADJUSTMENT = "Adjustment"
    TRANSFER = "Transfer"
    RETURN = "Return"
    OPENING = "Opening"

class InvoiceStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    SENT = "Sent" 
    PARTIALLY_PAID = "Partially Paid"
    PAID = "Paid"
    OVERDUE = "Overdue"
    VOIDED = "Voided"
    DISPUTED = "Disputed" # Added for Purchase Invoices

class BankTransactionTypeEnum(Enum): 
    DEPOSIT = "Deposit"
    WITHDRAWAL = "Withdrawal"
    TRANSFER = "Transfer"
    INTEREST = "Interest"
    FEE = "Fee"
    ADJUSTMENT = "Adjustment"

class PaymentTypeEnum(Enum): 
    CUSTOMER_PAYMENT = "Customer Payment"
    VENDOR_PAYMENT = "Vendor Payment"
    REFUND = "Refund"
    CREDIT_NOTE_APPLICATION = "Credit Note" # Application of a credit note to an invoice
    OTHER = "Other"

class PaymentMethodEnum(Enum): 
    CASH = "Cash"
    CHECK = "Check"
    BANK_TRANSFER = "Bank Transfer"
    CREDIT_CARD = "Credit Card"
    GIRO = "GIRO"
    PAYNOW = "PayNow"
    OTHER = "Other"

class PaymentEntityTypeEnum(Enum): 
    CUSTOMER = "Customer"
    VENDOR = "Vendor"
    OTHER = "Other"

class PaymentStatusEnum(Enum): 
    DRAFT = "Draft"
    APPROVED = "Approved"
    COMPLETED = "Completed" # After reconciliation or bank confirmation for some methods
    VOIDED = "Voided"
    RETURNED = "Returned" # E.g. bounced cheque

class PaymentAllocationDocTypeEnum(Enum): 
    SALES_INVOICE = "Sales Invoice"
    PURCHASE_INVOICE = "Purchase Invoice"
    CREDIT_NOTE = "Credit Note"
    DEBIT_NOTE = "Debit Note"
    OTHER = "Other"

class WHCertificateStatusEnum(Enum): # Withholding Tax Certificate Status
    DRAFT = "Draft"
    ISSUED = "Issued"
    VOIDED = "Voided"

class DataChangeTypeEnum(Enum): # For Audit Log
    INSERT = "Insert"
    UPDATE = "Update"
    DELETE = "Delete"

class RecurringFrequencyEnum(Enum): # For Recurring Journal Entries
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

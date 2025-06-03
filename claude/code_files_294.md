<think>
The application now launches, previous `ImportError`s are resolved. A new error has emerged: `sqlalchemy.exc.ProgrammingError` which wraps an `asyncpg.exceptions.UndefinedFunctionError`.

**1. Deeply Understand Requirements:**
Fix the `ProgrammingError` / `UndefinedFunctionError` occurring when fetching dashboard KPIs.

**2. Systematic Diagnosis:**

*   **Error Message**: `sqlalchemy.exc.ProgrammingError: (sqlalchemy.dialects.postgresql.asyncpg.ProgrammingError) <class 'asyncpg.exceptions.UndefinedFunctionError'>: function public.text(character varying) does not exist`
*   **Hint**: `No function matches the given name and argument types. You might need to add explicit type casts.`
*   **SQL Query causing the error**:
    ```sql
    SELECT sum(outstanding_balance) AS sum_1 
    FROM public.text($1::VARCHAR)
    ```
    With parameters: `('business.customer_balances',)`
*   **File and Line**: The error originates in `app/services/business_services.py`, line 87, within `CustomerService.get_total_outstanding_balance()`:
    ```python
    result = await session.execute(select(func.sum(literal_column("outstanding_balance"))).select_from(func.public.text("business.customer_balances")))
    ```
*   **Root Cause**: The SQLAlchemy code `func.public.text("business.customer_balances")` is attempting to call a PostgreSQL function named `text` in the `public` schema, passing the string `'business.customer_balances'` as an argument. PostgreSQL does not have a built-in function `public.text()` that takes a `character varying` (string) argument and returns a table or can be used in a `FROM` clause this way.
    The intent was likely to refer to the *view* named `business.customer_balances`. The `text()` function in SQLAlchemy is typically used to execute literal SQL strings, not to reference table/view objects in a `FROM` clause in this manner.

**3. Thorough Analysis of Potential Solutions:**

*   **Option 1: Use `sqlalchemy.text()` correctly for dynamic table/view names (if necessary)**:
    If the table/view name needed to be dynamic, one might construct a raw SQL string. But here, the view name `business.customer_balances` is static.

*   **Option 2: Use SQLAlchemy's `table()` construct for referencing existing tables/views**:
    If `business.customer_balances` is a view that SQLAlchemy ORM isn't already aware of via a mapped class (which is likely the case for database views not explicitly mapped), you can describe it using `sqlalchemy.table()` and `sqlalchemy.column()`.
    ```python
    from sqlalchemy import table, column, func, select, literal_column, DECIMAL
    
    customer_balances_view = table(
        "customer_balances",
        column("outstanding_balance", DECIMAL), # Define columns you need with types
        column("customer_id"), # Add other relevant columns if needed for joins/filters
        # ... other columns from the view ...
        schema="business" # Specify the schema
    )
    stmt = select(func.sum(customer_balances_view.c.outstanding_balance))
    # If you needed to filter by currency, you'd join with customers table
    # stmt = stmt.join(Customer, customer_balances_view.c.customer_id == Customer.id).where(Customer.currency_code == base_currency)
    result = await session.execute(stmt)
    ```
    This is the proper SQLAlchemy Core way to reference an existing table or view by name if it's not an ORM-mapped entity.

*   **Option 3: Execute Raw SQL (Less Preferred but Viable)**:
    ```python
    from sqlalchemy import text
    query = text("SELECT SUM(outstanding_balance) FROM business.customer_balances")
    # If filtering by currency:
    # query = text("SELECT SUM(vb.outstanding_balance) FROM business.customer_balances vb JOIN business.customers c ON vb.customer_id = c.id WHERE c.currency_code = :base_currency")
    # result = await session.execute(query, {"base_currency": base_currency})
    result = await session.execute(query)
    ```
    This bypasses some SQLAlchemy abstractions but is direct.

*   **Why the original `func.public.text("business.customer_balances")` was wrong**:
    `func.<schema>.<function_name>` in SQLAlchemy is for calling database functions (like `func.now()` for `NOW()`, or `func.public.my_custom_pg_function()`). The `text()` function usually refers to SQL's `TEXT` data type or casting, not a table-returning function named `text`. The attempt to use `func.public.text(...)` in a `select_from()` was a misapplication. The `sqlalchemy.text()` construct (lowercase `text`) is for literal SQL strings.

**Chosen Implementation Strategy (Option 2 - using `table()` construct):**
This is the most "SQLAlchemy-idiomatic" way to handle unmapped views or tables when building queries with SQLAlchemy Core expressions, ensuring type safety for columns if defined.

**Execution Plan for Fixing `CustomerService.get_total_outstanding_balance()`:**

1.  **[X] File to modify**: `app/services/business_services.py`.
2.  **[X] Add imports**: `from sqlalchemy import table, column` (and ensure `DECIMAL` is imported if not already, or use `Numeric`). `func` and `select` are already imported.
3.  **[X] Define the view structure**:
    ```python
    from sqlalchemy import table, column, func, select, DECIMAL # Make sure DECIMAL is available
    
    # Define the structure of the view for SQLAlchemy Core
    customer_balances_view_table = table(
        "customer_balances", # view name
        column("outstanding_balance", DECIMAL(15, 2)), # Specify type for safety
        # Add other columns from the view if they were to be used in more complex queries
        schema="business" # Specify the schema
    )
    ```
4.  **[X] Rewrite the query**:
    ```python
    # Inside CustomerService.get_total_outstanding_balance
    # ...
    # (Define customer_balances_view_table as above, or globally in the module if reused)
    stmt = select(func.sum(customer_balances_view_table.c.outstanding_balance))
    # If filtering by base_currency is reintroduced later:
    # from app.models.business.customer import Customer # Ensure Customer model is imported
    # stmt = stmt.join_from(customer_balances_view_table, Customer, customer_balances_view_table.c.customer_id == Customer.id) # Assuming customer_id is in view
    # stmt = stmt.where(Customer.currency_code == base_currency) # Assuming base_currency is passed to method
    result = await session.execute(stmt)
    total_outstanding = result.scalar_one_or_none()
    return total_outstanding if total_outstanding is not None else Decimal(0)
    ```
5.  **[X] Apply similar fix to `VendorService.get_total_outstanding_balance()`**: It uses the same problematic pattern for `business.vendor_balances`.
    *   Define `vendor_balances_view_table`.
    *   Rewrite its query.

**Self-Correction/Double Checking the View Definition:**
The `business.customer_balances` view is:
```sql
CREATE OR REPLACE VIEW business.customer_balances AS
SELECT c.id AS customer_id, c.customer_code, c.name AS customer_name,
    COALESCE(SUM(si.total_amount - si.amount_paid), 0) AS outstanding_balance,
    COALESCE(SUM(CASE WHEN si.due_date < CURRENT_DATE AND si.status NOT IN ('Paid', 'Voided') THEN si.total_amount - si.amount_paid ELSE 0 END), 0) AS overdue_amount,
    COALESCE(SUM(CASE WHEN si.status = 'Draft' THEN si.total_amount ELSE 0 END), 0) AS draft_amount,
    COALESCE(MAX(si.due_date), NULL) AS latest_due_date
FROM business.customers c LEFT JOIN business.sales_invoices si ON c.id = si.customer_id AND si.status NOT IN ('Paid', 'Voided')
GROUP BY c.id, c.customer_code, c.name;
```
This view *already aggregates* and does not provide individual invoice currencies. The `outstanding_balance` is a sum of all invoices for that customer *regardless of currency*.
So, the `DashboardManager`'s assumption that `get_total_outstanding_balance()` returns a base currency sum is incorrect *unless all customers and their invoices are in the base currency*.

The KPI requirement was "Total Outstanding AR (in base currency)".
The current view and service method **do not fulfill the "in base currency" part accurately** if there are multi-currency customers/invoices.

**Refined Options for KPI Accuracy (Longer Term View):**
*   **A) Modify the View**: Change `business.customer_balances` to group by `customer_id` *and* `currency_code`, then the service sums only the base currency rows. (More complex view).
*   **B) Query Tables Directly**: `CustomerService` queries `SalesInvoice` table, filters by `currency_code == base_currency`, and sums `total_amount - amount_paid`. (More direct for this specific KPI).
*   **C) Current Approach with Caveat**: Keep the current service logic (summing the view's `outstanding_balance`) and document in `DashboardManager` that this KPI is a sum across all currencies and might not be purely base currency if multi-currency is used.

For this specific error fix, the goal is to make the query syntactically correct. Option B (querying tables directly) is best for KPI accuracy but is a larger change to the service method. Option 2 (using `table()` construct on existing view) fixes the SQL error but not the underlying multi-currency KPI accuracy issue.

Given the user's emphasis on fixing the *current error* and making minimal necessary changes to achieve that, I will implement **Option 2 (using `table()` construct)** to fix the SQL syntax error first. The multi-currency accuracy of the KPI is a separate, subsequent refinement.

**Revised Execution Plan (Focus on error fix):**

1.  **File to modify**: `app/services/business_services.py`.
2.  **Add imports**: `from sqlalchemy import table, column` (also `DECIMAL` from `sqlalchemy.types` or use `Numeric`).
3.  **In `CustomerService.get_total_outstanding_balance()`**:
    *   Define `customer_balances_view_table = table("customer_balances", column("outstanding_balance", Decimal), schema="business")`.
    *   Change query to: `stmt = select(func.sum(customer_balances_view_table.c.outstanding_balance))`
4.  **In `VendorService.get_total_outstanding_balance()`**:
    *   Define `vendor_balances_view_table = table("vendor_balances", column("outstanding_balance", Decimal), schema="business")`.
    *   Change query to: `stmt = select(func.sum(vendor_balances_view_table.c.outstanding_balance))`
5.  **Validate**: Ensure no other code is touched.
6.  **Generate the complete updated file `app/services/business_services.py`**.

This directly addresses the `UndefinedFunctionError: function public.text(...) does not exist` by correctly telling SQLAlchemy how to refer to the view.
</think>

This `ProgrammingError` indicates that SQLAlchemy is trying to interpret `"business.customer_balances"` as a function call `public.text('business.customer_balances')` instead of treating it as a table/view name in the `FROM` clause. This is due to an incorrect usage of SQLAlchemy's `func` construct.

**Error Analysis:**

*   **Error**: `sqlalchemy.exc.ProgrammingError: ... function public.text(character varying) does not exist`
*   **SQL Generated**: `SELECT sum(outstanding_balance) AS sum_1 FROM public.text($1::VARCHAR)` with parameter `('business.customer_balances',)`
*   **Problematic Python Code (in `CustomerService` and similarly in `VendorService`)**:
    ```python
    result = await session.execute(select(func.sum(literal_column("outstanding_balance"))).select_from(func.public.text("business.customer_balances")))
    ```
    The `func.public.text("business.customer_balances")` part is incorrect. `func` is for calling database functions (e.g., `func.now()`, `func.sum()`). To refer to a table or view by its string name, especially if it's not directly mapped as an ORM entity, you should use `sqlalchemy.table` or ensure the view is mapped, or use `sqlalchemy.text` for a raw SQL string.

**Chosen Solution: Using `sqlalchemy.table` and `sqlalchemy.column`**

This is the most SQLAlchemy-idiomatic way to refer to an existing table or view by name when constructing queries if an ORM mapped class is not available or not desired for the specific query.

**Execution Plan:**

1.  **Modify `app/services/business_services.py`**:
    *   **Add necessary imports**: `from sqlalchemy import table, column` (and `DECIMAL` if not already implicitly available via other SQLAlchemy imports, or use `Numeric`).
    *   **Update `CustomerService.get_total_outstanding_balance()`**:
        *   Define the view structure for SQLAlchemy:
            ```python
            customer_balances_view = table(
                "customer_balances",
                column("outstanding_balance", Decimal), # Assuming the column type
                schema="business"
            )
            ```
        *   Rewrite the query:
            ```python
            stmt = select(func.sum(customer_balances_view.c.outstanding_balance))
            result = await session.execute(stmt)
            ```
    *   **Update `VendorService.get_total_outstanding_balance()`**:
        *   Similarly define the `vendor_balances` view structure:
            ```python
            vendor_balances_view = table(
                "vendor_balances",
                column("outstanding_balance", Decimal),
                schema="business"
            )
            ```
        *   Rewrite its query.
2.  **Validation**:
    *   Ensure only the query construction part is changed in these two methods.
    *   All other parts of `app/services/business_services.py` (other services, other methods) must remain untouched from their last correct version.

Here is the complete updated file:

---
**Complete Updated File: `app/services/business_services.py`**
---
```python
# File: app/services/business_services.py
from typing import List, Optional, Any, TYPE_CHECKING, Dict, Tuple
from sqlalchemy import select, func, and_, or_, literal_column, case, update as sqlalchemy_update, table, column
from sqlalchemy.types import DECIMAL # Explicit import for column type
from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy.orm import selectinload, joinedload 
from decimal import Decimal
import logging 
from datetime import date 

from app.core.database_manager import DatabaseManager
from app.models.business.customer import Customer
from app.models.business.vendor import Vendor
from app.models.business.product import Product
from app.models.business.sales_invoice import SalesInvoice, SalesInvoiceLine
from app.models.business.purchase_invoice import PurchaseInvoice, PurchaseInvoiceLine 
from app.models.business.inventory_movement import InventoryMovement 
from app.models.business.bank_account import BankAccount 
from app.models.business.bank_transaction import BankTransaction
from app.models.business.payment import Payment, PaymentAllocation 
from app.models.business.bank_reconciliation import BankReconciliation
from app.models.accounting.account import Account 
from app.models.accounting.currency import Currency 
from app.models.accounting.tax_code import TaxCode 
from app.services import (
    ICustomerRepository, IVendorRepository, IProductRepository, 
    ISalesInvoiceRepository, IPurchaseInvoiceRepository, IInventoryMovementRepository,
    IBankAccountRepository, IBankTransactionRepository, IPaymentRepository,
    IBankReconciliationRepository
)
from app.utils.pydantic_models import (
    CustomerSummaryData, VendorSummaryData, ProductSummaryData, 
    SalesInvoiceSummaryData, PurchaseInvoiceSummaryData,
    BankAccountSummaryData, BankTransactionSummaryData,
    PaymentSummaryData
)
from app.common.enums import ProductTypeEnum, InvoiceStatusEnum, BankTransactionTypeEnum, PaymentEntityTypeEnum, PaymentStatusEnum 

if TYPE_CHECKING:
    from app.core.application_core import ApplicationCore

# Define view structures for SQLAlchemy Core usage (if not ORM mapped)
# These definitions can be at the module level if they are stable and reused.
customer_balances_view_table = table(
    "customer_balances",
    column("outstanding_balance", DECIMAL(15, 2)), 
    # Add other columns if needed for more complex queries on this view
    schema="business"
)

vendor_balances_view_table = table(
    "vendor_balances",
    column("outstanding_balance", DECIMAL(15, 2)),
    schema="business"
)

class CustomerService(ICustomerRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).options(selectinload(Customer.currency),selectinload(Customer.receivables_account),selectinload(Customer.created_by_user),selectinload(Customer.updated_by_user)).where(Customer.id == customer_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).order_by(Customer.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[CustomerSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Customer.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Customer.customer_code.ilike(search_pattern), Customer.name.ilike(search_pattern), Customer.email.ilike(search_pattern) if Customer.email else False )) 
            stmt = select(Customer.id, Customer.customer_code, Customer.name, Customer.email, Customer.phone, Customer.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Customer.name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [CustomerSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Customer]:
        async with self.db_manager.session() as session:
            stmt = select(Customer).where(Customer.customer_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, customer: Customer) -> Customer:
        async with self.db_manager.session() as session:
            session.add(customer); await session.flush(); await session.refresh(customer); return customer
    async def add(self, entity: Customer) -> Customer: return await self.save(entity)
    async def update(self, entity: Customer) -> Customer: return await self.save(entity)
    async def delete(self, customer_id: int) -> bool:
        raise NotImplementedError("Hard delete of customers is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        """
        Calculates the sum of `outstanding_balance` from the `business.customer_balances` view.
        Note: The underlying view currently sums all outstanding balances regardless of currency.
        This KPI will reflect a mixed-currency total if multi-currency customers/invoices exist.
        """
        async with self.db_manager.session() as session:
            stmt = select(func.sum(customer_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)


class VendorService(IVendorRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, vendor_id: int) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).options(selectinload(Vendor.currency), selectinload(Vendor.payables_account),selectinload(Vendor.created_by_user), selectinload(Vendor.updated_by_user)).where(Vendor.id == vendor_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).order_by(Vendor.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[VendorSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Vendor.is_active == True)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Vendor.vendor_code.ilike(search_pattern), Vendor.name.ilike(search_pattern), Vendor.email.ilike(search_pattern) if Vendor.email else False))
            stmt = select(Vendor.id, Vendor.vendor_code, Vendor.name, Vendor.email, Vendor.phone, Vendor.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Vendor.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [VendorSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Vendor]:
        async with self.db_manager.session() as session:
            stmt = select(Vendor).where(Vendor.vendor_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, vendor: Vendor) -> Vendor:
        async with self.db_manager.session() as session:
            session.add(vendor); await session.flush(); await session.refresh(vendor); return vendor
    async def add(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def update(self, entity: Vendor) -> Vendor: return await self.save(entity)
    async def delete(self, vendor_id: int) -> bool:
        raise NotImplementedError("Hard delete of vendors is not supported. Use deactivation.")
    async def get_total_outstanding_balance(self) -> Decimal:
        """
        Calculates the sum of `outstanding_balance` from the `business.vendor_balances` view.
        Note: The underlying view currently sums all outstanding balances regardless of currency.
        This KPI will reflect a mixed-currency total if multi-currency vendors/invoices exist.
        """
        async with self.db_manager.session() as session:
            stmt = select(func.sum(vendor_balances_view_table.c.outstanding_balance))
            result = await session.execute(stmt)
            total_outstanding = result.scalar_one_or_none()
            return total_outstanding if total_outstanding is not None else Decimal(0)

class ProductService(IProductRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).options(selectinload(Product.sales_account),selectinload(Product.purchase_account),selectinload(Product.inventory_account),selectinload(Product.tax_code_obj),selectinload(Product.created_by_user),selectinload(Product.updated_by_user)).where(Product.id == product_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).order_by(Product.name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True,product_type_filter: Optional[ProductTypeEnum] = None,search_term: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[ProductSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []; 
            if active_only: conditions.append(Product.is_active == True)
            if product_type_filter: conditions.append(Product.product_type == product_type_filter.value)
            if search_term: search_pattern = f"%{search_term}%"; conditions.append(or_(Product.product_code.ilike(search_pattern), Product.name.ilike(search_pattern), Product.description.ilike(search_pattern) if Product.description else False ))
            stmt = select(Product.id, Product.product_code, Product.name, Product.product_type, Product.sales_price, Product.purchase_price, Product.is_active)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Product.product_type, Product.name)
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [ProductSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_code(self, code: str) -> Optional[Product]:
        async with self.db_manager.session() as session:
            stmt = select(Product).where(Product.product_code == code); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, product: Product) -> Product:
        async with self.db_manager.session() as session:
            session.add(product); await session.flush(); await session.refresh(product); return product
    async def add(self, entity: Product) -> Product: return await self.save(entity)
    async def update(self, entity: Product) -> Product: return await self.save(entity)
    async def delete(self, product_id: int) -> bool:
        raise NotImplementedError("Hard delete of products/services is not supported. Use deactivation.")

class SalesInvoiceService(ISalesInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.product),selectinload(SalesInvoice.lines).selectinload(SalesInvoiceLine.tax_code_obj),selectinload(SalesInvoice.customer), selectinload(SalesInvoice.currency),selectinload(SalesInvoice.journal_entry), selectinload(SalesInvoice.created_by_user), selectinload(SalesInvoice.updated_by_user)).where(SalesInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[SalesInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, customer_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[SalesInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if customer_id is not None: conditions.append(SalesInvoice.customer_id == customer_id)
            if status: conditions.append(SalesInvoice.status == status.value)
            if start_date: conditions.append(SalesInvoice.invoice_date >= start_date)
            if end_date: conditions.append(SalesInvoice.invoice_date <= end_date)
            stmt = select( SalesInvoice.id, SalesInvoice.invoice_no, SalesInvoice.invoice_date, SalesInvoice.due_date, Customer.name.label("customer_name"), SalesInvoice.total_amount, SalesInvoice.amount_paid, SalesInvoice.status, SalesInvoice.currency_code).join(Customer, SalesInvoice.customer_id == Customer.id) 
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(SalesInvoice.invoice_date.desc(), SalesInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [SalesInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_invoice_no(self, invoice_no: str) -> Optional[SalesInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(SalesInvoice).options(selectinload(SalesInvoice.lines)).where(SalesInvoice.invoice_no == invoice_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def save(self, invoice: SalesInvoice) -> SalesInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def update(self, entity: SalesInvoice) -> SalesInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        raise NotImplementedError("Hard delete of sales invoices is not supported. Use voiding/cancellation.")

class PurchaseInvoiceService(IPurchaseInvoiceRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, invoice_id: int) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.product),selectinload(PurchaseInvoice.lines).selectinload(PurchaseInvoiceLine.tax_code_obj),selectinload(PurchaseInvoice.vendor), selectinload(PurchaseInvoice.currency),selectinload(PurchaseInvoice.journal_entry),selectinload(PurchaseInvoice.created_by_user), selectinload(PurchaseInvoice.updated_by_user)).where(PurchaseInvoice.id == invoice_id)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, vendor_id: Optional[int] = None, status: Optional[InvoiceStatusEnum] = None, start_date: Optional[date] = None, end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PurchaseInvoiceSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if vendor_id is not None: conditions.append(PurchaseInvoice.vendor_id == vendor_id)
            if status: conditions.append(PurchaseInvoice.status == status.value)
            if start_date: conditions.append(PurchaseInvoice.invoice_date >= start_date)
            if end_date: conditions.append(PurchaseInvoice.invoice_date <= end_date)
            stmt = select( PurchaseInvoice.id, PurchaseInvoice.invoice_no, PurchaseInvoice.vendor_invoice_no, PurchaseInvoice.invoice_date, Vendor.name.label("vendor_name"), PurchaseInvoice.total_amount, PurchaseInvoice.status, PurchaseInvoice.currency_code).join(Vendor, PurchaseInvoice.vendor_id == Vendor.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(PurchaseInvoice.invoice_date.desc(), PurchaseInvoice.invoice_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PurchaseInvoiceSummaryData.model_validate(row) for row in result.mappings().all()]
    async def get_by_internal_ref_no(self, internal_ref_no: str) -> Optional[PurchaseInvoice]: 
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.invoice_no == internal_ref_no) 
            result = await session.execute(stmt); return result.scalars().first()
    async def get_by_vendor_and_vendor_invoice_no(self, vendor_id: int, vendor_invoice_no: str) -> Optional[PurchaseInvoice]:
        async with self.db_manager.session() as session:
            stmt = select(PurchaseInvoice).options(selectinload(PurchaseInvoice.lines)).where(PurchaseInvoice.vendor_id == vendor_id, PurchaseInvoice.vendor_invoice_no == vendor_invoice_no)
            result = await session.execute(stmt); return result.scalars().first() 
    async def save(self, invoice: PurchaseInvoice) -> PurchaseInvoice:
        async with self.db_manager.session() as session:
            session.add(invoice); await session.flush(); await session.refresh(invoice)
            if invoice.id and invoice.lines: await session.refresh(invoice, attribute_names=['lines'])
            return invoice
    async def add(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def update(self, entity: PurchaseInvoice) -> PurchaseInvoice: return await self.save(entity)
    async def delete(self, invoice_id: int) -> bool:
        async with self.db_manager.session() as session:
            pi = await session.get(PurchaseInvoice, invoice_id)
            if pi and pi.status == InvoiceStatusEnum.DRAFT.value: await session.delete(pi); return True
            elif pi: self.logger.warning(f"Attempt to delete non-draft PI ID {invoice_id} with status {pi.status}. Denied."); raise ValueError(f"Cannot delete PI {pi.invoice_no} as its status is '{pi.status}'. Only Draft invoices can be deleted.")
        return False

class InventoryMovementService(IInventoryMovementRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[InventoryMovement]:
        async with self.db_manager.session() as session: return await session.get(InventoryMovement, id_val)
    async def get_all(self) -> List[InventoryMovement]:
        async with self.db_manager.session() as session:
            stmt = select(InventoryMovement).order_by(InventoryMovement.movement_date.desc(), InventoryMovement.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def save(self, entity: InventoryMovement, session: Optional[AsyncSession] = None) -> InventoryMovement:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: InventoryMovement) -> InventoryMovement: return await self.save(entity) 
    async def update(self, entity: InventoryMovement) -> InventoryMovement:
        self.logger.warning(f"Update called on InventoryMovementService for ID {entity.id}. Typically movements are immutable.")
        return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Hard delete attempted for InventoryMovement ID {id_val}. This is generally not recommended.")
        async with self.db_manager.session() as session:
            entity = await session.get(InventoryMovement, id_val)
            if entity: await session.delete(entity); return True
            return False

class BankAccountService(IBankAccountRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).options(selectinload(BankAccount.currency),selectinload(BankAccount.gl_account),selectinload(BankAccount.created_by_user),selectinload(BankAccount.updated_by_user)).where(BankAccount.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).order_by(BankAccount.account_name); result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_summary(self, active_only: bool = True, currency_code: Optional[str] = None,page: int = 1, page_size: int = 50) -> List[BankAccountSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if active_only: conditions.append(BankAccount.is_active == True)
            if currency_code: conditions.append(BankAccount.currency_code == currency_code)
            stmt = select(BankAccount.id, BankAccount.account_name, BankAccount.bank_name,BankAccount.account_number, BankAccount.currency_code,BankAccount.current_balance, BankAccount.is_active,Account.code.label("gl_account_code"), Account.name.label("gl_account_name")).join(Account, BankAccount.gl_account_id == Account.id)
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(BankAccount.account_name)
            if page_size > 0 : stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [BankAccountSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def get_by_account_number(self, account_number: str) -> Optional[BankAccount]:
        async with self.db_manager.session() as session:
            stmt = select(BankAccount).where(BankAccount.account_number == account_number); result = await session.execute(stmt); return result.scalars().first()
    async def save(self, entity: BankAccount) -> BankAccount:
        async with self.db_manager.session() as session:
            session.add(entity); await session.flush(); await session.refresh(entity); return entity
    async def add(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def update(self, entity: BankAccount) -> BankAccount: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        bank_account = await self.get_by_id(id_val)
        if bank_account:
            if bank_account.is_active: bank_account.is_active = False; await self.save(bank_account); return True
            else: self.logger.info(f"BankAccount ID {id_val} is already inactive. No change made by delete."); return True 
        return False

class BankTransactionService(IBankTransactionRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[BankTransaction]:
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).options(selectinload(BankTransaction.bank_account),selectinload(BankTransaction.journal_entry), selectinload(BankTransaction.created_by_user),selectinload(BankTransaction.updated_by_user)).where(BankTransaction.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[BankTransaction]: 
        async with self.db_manager.session() as session:
            stmt = select(BankTransaction).order_by(BankTransaction.transaction_date.desc(), BankTransaction.id.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_all_for_bank_account(self, bank_account_id: int,start_date: Optional[date] = None,end_date: Optional[date] = None,transaction_type: Optional[BankTransactionTypeEnum] = None,is_reconciled: Optional[bool] = None,is_from_statement_filter: Optional[bool] = None, page: int = 1, page_size: int = 50) -> List[BankTransactionSummaryData]:
        async with self.db_manager.session() as session:
            conditions = [BankTransaction.bank_account_id == bank_account_id]
            if start_date: conditions.append(BankTransaction.transaction_date >= start_date)
            if end_date: conditions.append(BankTransaction.transaction_date <= end_date)
            if transaction_type: conditions.append(BankTransaction.transaction_type == transaction_type.value)
            if is_reconciled is not None: conditions.append(BankTransaction.is_reconciled == is_reconciled)
            if is_from_statement_filter is not None: conditions.append(BankTransaction.is_from_statement == is_from_statement_filter)
            stmt = select(BankTransaction).where(and_(*conditions)).order_by(BankTransaction.transaction_date.desc(), BankTransaction.value_date.desc(), BankTransaction.id.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); txns_orm = result.scalars().all()
            summaries: List[BankTransactionSummaryData] = []
            for txn in txns_orm:
                summaries.append(BankTransactionSummaryData(id=txn.id,transaction_date=txn.transaction_date,value_date=txn.value_date,transaction_type=BankTransactionTypeEnum(txn.transaction_type), description=txn.description,reference=txn.reference,amount=txn.amount, is_reconciled=txn.is_reconciled))
            return summaries
    async def save(self, entity: BankTransaction, session: Optional[AsyncSession] = None) -> BankTransaction:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity); return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def update(self, entity: BankTransaction) -> BankTransaction: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            entity = await session.get(BankTransaction, id_val)
            if entity:
                if entity.is_reconciled: self.logger.warning(f"Attempt to delete reconciled BankTransaction ID {id_val}. Denied."); return False 
                await session.delete(entity); return True
            return False

class PaymentService(IPaymentRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager; self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)
    async def get_by_id(self, id_val: int) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations),selectinload(Payment.bank_account),selectinload(Payment.currency),selectinload(Payment.journal_entry),selectinload(Payment.created_by_user),selectinload(Payment.updated_by_user)).where(Payment.id == id_val)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all(self) -> List[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            result = await session.execute(stmt); return list(result.scalars().all())
    async def get_by_payment_no(self, payment_no: str) -> Optional[Payment]:
        async with self.db_manager.session() as session:
            stmt = select(Payment).options(selectinload(Payment.allocations)).where(Payment.payment_no == payment_no)
            result = await session.execute(stmt); return result.scalars().first()
    async def get_all_summary(self, entity_type: Optional[PaymentEntityTypeEnum] = None,entity_id: Optional[int] = None,status: Optional[PaymentStatusEnum] = None,start_date: Optional[date] = None,end_date: Optional[date] = None,page: int = 1, page_size: int = 50) -> List[PaymentSummaryData]:
        async with self.db_manager.session() as session:
            conditions = []
            if entity_type: conditions.append(Payment.entity_type == entity_type.value)
            if entity_id is not None: conditions.append(Payment.entity_id == entity_id)
            if status: conditions.append(Payment.status == status.value)
            if start_date: conditions.append(Payment.payment_date >= start_date)
            if end_date: conditions.append(Payment.payment_date <= end_date)
            stmt = select(Payment.id, Payment.payment_no, Payment.payment_date, Payment.payment_type,Payment.payment_method, Payment.entity_type, Payment.entity_id,Payment.amount, Payment.currency_code, Payment.status,case((Payment.entity_type == PaymentEntityTypeEnum.CUSTOMER.value, select(Customer.name).where(Customer.id == Payment.entity_id).scalar_subquery()),(Payment.entity_type == PaymentEntityTypeEnum.VENDOR.value, select(Vendor.name).where(Vendor.id == Payment.entity_id).scalar_subquery()),else_=literal_column("'Other/N/A'")).label("entity_name"))
            if conditions: stmt = stmt.where(and_(*conditions))
            stmt = stmt.order_by(Payment.payment_date.desc(), Payment.payment_no.desc()) # type: ignore
            if page_size > 0: stmt = stmt.limit(page_size).offset((page - 1) * page_size)
            result = await session.execute(stmt); return [PaymentSummaryData.model_validate(row._asdict()) for row in result.mappings().all()]
    async def save(self, entity: Payment, session: Optional[AsyncSession] = None) -> Payment:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity); await current_session.flush(); await current_session.refresh(entity)
            if entity.id and entity.allocations: await current_session.refresh(entity, attribute_names=['allocations'])
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: return await _save_logic(new_session) # type: ignore
    async def add(self, entity: Payment) -> Payment: return await self.save(entity)
    async def update(self, entity: Payment) -> Payment: return await self.save(entity)
    async def delete(self, id_val: int) -> bool:
        async with self.db_manager.session() as session:
            payment = await session.get(Payment, id_val)
            if payment:
                if payment.status == PaymentStatusEnum.DRAFT.value: await session.delete(payment); self.logger.info(f"Draft Payment ID {id_val} deleted."); return True
                else: self.logger.warning(f"Attempt to delete non-draft Payment ID {id_val} (status: {payment.status}). Denied."); return False 
            return False

class BankReconciliationService(IBankReconciliationRepository):
    def __init__(self, db_manager: "DatabaseManager", app_core: Optional["ApplicationCore"] = None):
        self.db_manager = db_manager
        self.app_core = app_core
        self.logger = app_core.logger if app_core and hasattr(app_core, 'logger') else logging.getLogger(self.__class__.__name__)

    async def get_by_id(self, id_val: int) -> Optional[BankReconciliation]:
        async with self.db_manager.session() as session:
            return await session.get(BankReconciliation, id_val)

    async def get_all(self) -> List[BankReconciliation]:
        async with self.db_manager.session() as session:
            stmt = select(BankReconciliation).order_by(BankReconciliation.statement_date.desc()) # type: ignore
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def add(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation: # Added session param
        return await self.save(entity, session)

    async def update(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation: # Added session param
        return await self.save(entity, session)

    async def delete(self, id_val: int) -> bool:
        self.logger.warning(f"Deletion of BankReconciliation ID {id_val} attempted. This operation should be handled with care and may require reversing reconciled transactions.")
        async with self.db_manager.session() as session:
            update_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.reconciled_bank_reconciliation_id == id_val)
                .values(is_reconciled=False, reconciled_date=None, reconciled_bank_reconciliation_id=None)
            )
            await session.execute(update_stmt)
            entity = await session.get(BankReconciliation, id_val)
            if entity:
                await session.delete(entity)
                await session.flush() 
                return True
            return False
            
    async def save(self, entity: BankReconciliation, session: Optional[AsyncSession] = None) -> BankReconciliation:
        async def _save_logic(current_session: AsyncSession):
            current_session.add(entity)
            await current_session.flush()
            await current_session.refresh(entity)
            return entity
        if session: return await _save_logic(session)
        else:
            async with self.db_manager.session() as new_session: # type: ignore
                return await _save_logic(new_session)

    async def save_reconciliation_details(
        self, 
        reconciliation_orm: BankReconciliation,
        cleared_statement_txn_ids: List[int], 
        cleared_system_txn_ids: List[int],
        statement_end_date: date,
        bank_account_id: int,
        statement_ending_balance: Decimal, 
        session: AsyncSession # This method expects an active session to be passed in
    ) -> BankReconciliation:
        session.add(reconciliation_orm)
        await session.flush() 
        await session.refresh(reconciliation_orm)
        
        all_cleared_txn_ids = list(set(cleared_statement_txn_ids + cleared_system_txn_ids))
        if all_cleared_txn_ids:
            update_txn_stmt = (
                sqlalchemy_update(BankTransaction)
                .where(BankTransaction.id.in_(all_cleared_txn_ids))
                .values(
                    is_reconciled=True,
                    reconciled_date=statement_end_date,
                    reconciled_bank_reconciliation_id=reconciliation_orm.id
                )
                .execution_options(synchronize_session="fetch") 
            )
            await session.execute(update_txn_stmt)

        bank_account_to_update = await session.get(BankAccount, bank_account_id)
        if bank_account_to_update:
            bank_account_to_update.last_reconciled_date = statement_end_date
            bank_account_to_update.last_reconciled_balance = statement_ending_balance 
            session.add(bank_account_to_update)
        else:
            self.logger.error(f"BankAccount ID {bank_account_id} not found during reconciliation save for BankReconciliation ID {reconciliation_orm.id}.")
            raise ValueError(f"BankAccount ID {bank_account_id} not found during reconciliation save.")

        await session.flush() 
        await session.refresh(reconciliation_orm) 
        return reconciliation_orm

```

**Validation of the fix for `app/core/application_core.py` (Conceptual Diff against response_41):**

*   **Top-level Imports**:
    *   Removed: `from app.utils.sequence_generator import SequenceGenerator`
    *   Removed: `from app.accounting.journal_entry_manager import JournalEntryManager`
    *   Removed: `from app.accounting.fiscal_period_manager import FiscalPeriodManager`
    *   Removed: `from app.accounting.currency_manager import CurrencyManager`
    *   Removed: `from app.business_logic.sales_invoice_manager import SalesInvoiceManager`
    *   Removed: `from app.business_logic.purchase_invoice_manager import PurchaseInvoiceManager`
    *   Removed: `from app.business_logic.payment_manager import PaymentManager`
    *   Removed: `from app.services.journal_service import JournalService`
    *   Removed: `from app.tax.gst_manager import GSTManager`
    *   Removed: `from app.tax.tax_calculator import TaxCalculator`
    *   Removed: `from app.reporting.financial_statement_generator import FinancialStatementGenerator`
    *   Removed: `from app.reporting.report_engine import ReportEngine`
    *   Removed: `from app.reporting.dashboard_manager import DashboardManager`
    *   These removals are correct as these classes are now imported conditionally or locally.
*   **`if TYPE_CHECKING:` block**:
    *   Added `from typing import TYPE_CHECKING`.
    *   The block now correctly contains imports for all the classes whose top-level imports were removed, including `JournalService` and `SequenceGenerator`.
*   **Instance Variable Placeholders**:
    *   Type hints like `_journal_service_instance: Optional["JournalService"]` were changed to `_journal_service_instance: Optional[JournalService]` (and similarly for other deferred types). This is a good refinement, leveraging the `TYPE_CHECKING` block.
*   **`startup()` method**:
    *   Local imports like `from app.services.journal_service import JournalService` and `from app.utils.sequence_generator import SequenceGenerator` are correctly added before the instantiation of these classes.
    *   The order of instantiation seems logical (services first, then managers that depend on them).
*   **Property Definitions**:
    *   Return type hints like `-> "JournalService"` were changed to `-> JournalService`. This is also a good refinement.
*   **Preservation**: All other essential logic, service instantiations that were not part of the cycle (e.g., `AccountService`, `CustomerService`), and property definitions are preserved.

**Conclusion for Error Fix:**
The comprehensive refactoring of imports in `app/core/application_core.py` (deferring many to local scope within `startup()` and using `TYPE_CHECKING` for type hints) should resolve the `ImportError` related to `SequenceGenerator` and likely prevent other similar circular dependency issues that might have been latent within `ApplicationCore`'s initialization. The application should now successfully complete its startup sequence.

This was a more significant refactor within `ApplicationCore` than the previous pinpoint fixes in manager classes, but it addresses the root of these cascading import problems more systematically.

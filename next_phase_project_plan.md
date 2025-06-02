**Feature: Bank Reconciliation**

This is a complex feature with several parts:
1.  **Bank Statement Import**: Ability to import bank statements (e.g., CSV, OFX - QIF/MT940 are also possibilities but CSV/OFX are common starting points).
2.  **Reconciliation UI**: A screen to compare imported bank statement lines with system bank transactions (`business.bank_transactions`).
3.  **Matching Logic**:
    *   Automatic matching suggestions (e.g., based on date, amount, reference).
    *   Manual matching.
4.  **Handling Discrepancies**:
    *   Creating new system transactions for items on the bank statement but not in the books (e.g., bank charges, interest received/paid).
    *   Marking system transactions as cleared/reconciled.
    *   Handling outstanding items (checks not yet cleared, deposits in transit).
5.  **Reconciliation Report**: Summary of reconciled items, outstanding items, and any adjustments made.
6.  **Saving Reconciliation State**: Persisting the reconciliation details (which items were matched, statement balance, book balance, reconciled balance, date of reconciliation).


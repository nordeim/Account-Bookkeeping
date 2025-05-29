**Current Project Status Recap (Relevant for README/TDS updates):**
    
*   **User Management UI**: Fully functional (CRUD, role assignment, password change, status toggle).
*   **Role Management UI**: Fully functional (CRUD for roles, assignment of permissions to roles).
*   **Sales Invoicing**: Draft management, posting with JE creation, list view UI are functional. "Save & Approve" in dialog is a minor pending UI polish.
*   **Core Accounting, Customer/Vendor/Product Management, GST F5, Reporting**: Stable and functional as per previous updates. 
    
---
**Current Project Status Recap:**
            
*   **User Management UI**: Functional for CRUD, role assignment, password changes, status toggling.
*   **Role Management UI (Part 1)**:
    *   `RoleManagementWidget`: Lists roles; Add/Edit actions launch `RoleDialog`; Delete action is functional with checks.
    *   `RoleDialog`: Supports creating/editing role name and description. Permission assignment UI is a placeholder.
    *   `SecurityManager`: Backend methods for role CRUD (name/description) and permission listing are in place.
*   All previously implemented features (Sales Invoicing drafts & posting, Core Accounting, etc.) remain stable.

**Next Step Identification (from Roadmap & previous plan):**
            
Roadmap Item: **"User and Role Management UI**: Add UI in Settings for managing users, roles, and permissions."
We've done User Management and basic Role CRUD. The next step is **Part 2 of Role Management: Implementing Permission Assignment within `RoleDialog`**.

**Plan for this Turn: Role Management UI - Part 2 (Permission Assignment in `RoleDialog`).**
            
**Objective:**  
Enhance `RoleDialog` to:
1.  Display all available system permissions (already fetched by `SecurityManager.get_all_permissions()`).
2.  Allow users to select/deselect multiple permissions to be assigned to the role being created or edited.
3.  When editing a role, pre-select the permissions currently assigned to it.
4.  Collect the selected permission IDs and include them in the DTO sent to the `SecurityManager`.
5.  Ensure `SecurityManager` methods for `create_role` and `update_role` correctly handle saving these permission assignments.


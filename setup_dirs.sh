#!/bin/bash

# Create GitHub workflow directories
mkdir -p sg_bookkeeper/.github/workflows

# Create app directories
mkdir -p sg_bookkeeper/app/accounting
mkdir -p sg_bookkeeper/app/core
mkdir -p sg_bookkeeper/app/common
mkdir -p sg_bookkeeper/app/models/accounting
mkdir -p sg_bookkeeper/app/models/audit
mkdir -p sg_bookkeeper/app/models/business
mkdir -p sg_bookkeeper/app/models/core
mkdir -p sg_bookkeeper/app/reporting
mkdir -p sg_bookkeeper/app/services
mkdir -p sg_bookkeeper/app/tax
mkdir -p sg_bookkeeper/app/ui/accounting
mkdir -p sg_bookkeeper/app/ui/banking
mkdir -p sg_bookkeeper/app/ui/customers
mkdir -p sg_bookkeeper/app/ui/dashboard
mkdir -p sg_bookkeeper/app/ui/reports
mkdir -p sg_bookkeeper/app/ui/settings
mkdir -p sg_bookkeeper/app/ui/vendors
mkdir -p sg_bookkeeper/app/utils

# Create data directories
mkdir -p sg_bookkeeper/data/chart_of_accounts
mkdir -p sg_bookkeeper/data/report_templates
mkdir -p sg_bookkeeper/data/tax_codes

# Create docs directories
mkdir -p sg_bookkeeper/docs/api_reference
mkdir -p sg_bookkeeper/docs/developer_guide
mkdir -p sg_bookkeeper/docs/user_guide

# Create resources directories
mkdir -p sg_bookkeeper/resources/icons
mkdir -p sg_bookkeeper/resources/images

# Create scripts directory
mkdir -p sg_bookkeeper/scripts

# Create tests directories
mkdir -p sg_bookkeeper/tests/integration
mkdir -p sg_bookkeeper/tests/ui
mkdir -p sg_bookkeeper/tests/unit

echo "Directory structure created successfully."

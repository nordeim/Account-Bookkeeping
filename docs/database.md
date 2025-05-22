/*-------------------------------------------------------------------------------------------------------------------
    6. PERMISSIONS
-------------------------------------------------------------------------------------------------------------------*/
-- Note: Desktop app runs embedded DB; OS user == DB superuser.
-- The following is illustrative if multi-role setup is required.

-- CREATE ROLE ledger_app LOGIN PASSWORD 'changeme';
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ledger_app;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ledger_app;

-- Future: Use SECURITY DEFINER functions + RLS for per-company data isolation.

/*-------------------------------------------------------------------------------------------------------------------
    7. FINISHED
-------------------------------------------------------------------------------------------------------------------*/
COMMENT ON SCHEMA public IS 'LumiLedger 2.0 core schema – automatically generated inst
script.';


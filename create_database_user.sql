-- create application user
CREATE USER sgbookkeeper_user WITH PASSWORD 'SGkeeperPass123';
-- grant user privileges
GRANT ALL PRIVILEGES ON DATABASE sg_bookkeeper TO sgbookkeeper_user;
-- connect to application specific database
\c sg_bookkeeper

-- Grant usage on schemas
GRANT USAGE ON SCHEMA core TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA business TO sgbookkeeper_user;
GRANT USAGE ON SCHEMA audit TO sgbookkeeper_user;

-- Grant DML privileges on existing tables in each schema
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA business TO sgbookkeeper_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA audit TO sgbookkeeper_user;

-- Grant privileges on existing sequences (important for auto-incrementing IDs used by the app)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA core TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA accounting TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA business TO sgbookkeeper_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA audit TO sgbookkeeper_user;
-- Note: SERIAL columns automatically create sequences, usually in the same schema as the table.

-- Grant execute on functions (if your application calls them directly as sgbookkeeper_user)
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA core TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA accounting TO sgbookkeeper_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA audit TO sgbookkeeper_user;
-- Note: business schema currently has no functions in schema.sql

-- Set default privileges for future tables/sequences created by the 'postgres' user (or other roles)
-- This ensures sgbookkeeper_user will have access to them automatically.
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO sgbookkeeper_user;

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA core GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA accounting GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA business GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA audit GRANT USAGE, SELECT ON SEQUENCES TO sgbookkeeper_user;

-- Exit psql
\q

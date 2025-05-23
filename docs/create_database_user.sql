-- Create a new role (user) named 'scent_user' with a password.
-- IMPORTANT: Ensure this password is changed for production environments.
CREATE USER scent_user WITH PASSWORD 'ScentAdmin%123';

-- Create the database named 'the_scent'.
-- It's often good practice for the application user to own its database.
-- CREATE DATABASE the_scent
--     WITH
--     OWNER = scent_user          -- Set scent_user as the owner
--     ENCODING = 'UTF8'           -- Standard encoding
--     LC_COLLATE = 'en_US.UTF-8'  -- Or your preferred locale for collation
--     LC_CTYPE = 'en_US.UTF-8'    -- Or your preferred locale for character type
--     TABLESPACE = pg_default
--     CONNECTION LIMIT = -1;      -- Default connection limit

CREATE DATABASE the_scent
    WITH
    OWNER = scent_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- sudo -u postgres PGPASSWORD="AdminPassword" psql -h localhost -f create_database_user.sql

-- Optional: If you want to ensure the user can create extensions if needed by Prisma or other tools
-- (e.g., for UUID generation if not using CUIDs, though Prisma's CUIDs don't need this).
-- This step might require superuser privileges initially, or grant it specifically.
-- GRANT CREATE ON DATABASE the_scent TO scent_user; -- Usually owner has this.

-- Note: As the owner of the 'the_scent' database, 'scent_user' will typically
-- have all necessary privileges (CREATE, SELECT, INSERT, UPDATE, DELETE, etc.)
-- on tables created within that database (especially in the 'public' schema by default).

-- If the database 'the_scent' ALREADY EXISTS and is owned by a different user (e.g., 'postgres'):
-- You would run these commands instead of the CREATE DATABASE command above:
-- 1. CREATE USER scent_user WITH PASSWORD 'ScentAdmin%123'; (if not already created)
-- 2. ALTER DATABASE the_scent OWNER TO scent_user; -- To change ownership (requires current owner or superuser)
-- OR, if you don't want to change ownership but grant privileges:
-- 3. GRANT CONNECT ON DATABASE the_scent TO scent_user;
-- 4. -- Connect to the 'the_scent' database: \c the_scent
-- 5. GRANT USAGE, CREATE ON SCHEMA public TO scent_user;
-- 6. GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO scent_user;
-- 7. GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO scent_user;
-- 8. ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO scent_user;
-- 9. ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO scent_user;

-- For simplicity and a new setup, making `scent_user` the owner of a new `the_scent` database is the cleanest.

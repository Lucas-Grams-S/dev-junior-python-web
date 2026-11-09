-- Três papéis, três poderes. A aplicação NÃO é dona das tabelas: não pode apagá-las nem alterá-las.
CREATE ROLE minishop_owner LOGIN PASSWORD 'owner-lab-apenas' ;
CREATE ROLE minishop_app   LOGIN PASSWORD 'app-lab-apenas'   NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE minishop_ro    LOGIN PASSWORD 'ro-lab-apenas'    NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE DATABASE minishop_m9 OWNER minishop_owner;
\c minishop_m9
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT  ALL ON SCHEMA public TO minishop_owner;
GRANT  USAGE ON SCHEMA public TO minishop_app, minishop_ro;
-- tabelas FUTURAS (criadas pelo dono nas migrações) já nascem com os privilégios certos:
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO minishop_app;
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO minishop_app;
ALTER DEFAULT PRIVILEGES FOR ROLE minishop_owner IN SCHEMA public GRANT SELECT ON TABLES TO minishop_ro;

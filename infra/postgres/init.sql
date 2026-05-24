-- FreelanceRadar PostgreSQL Init Script
-- Runs on first container startup

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Create performance indexes after Alembic runs migrations
-- (These are created by Alembic; this file just enables extensions)

SELECT 'FreelanceRadar database initialized with pgvector support' AS status;

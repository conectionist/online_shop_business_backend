-- Cleanup script for refresh_tokens table
-- Run this if you need to reset the refresh_tokens migration
-- without losing other database data

-- Drop the table with the wrong schema
DROP TABLE IF EXISTS refresh_tokens;

-- Reset alembic version to 019 (before refresh_tokens migration)
-- Only if the current version is 020, 021, or 022
UPDATE alembic_version
SET version_num = '019'
WHERE version_num IN ('020', '021', '022');

-- Verify
SELECT * FROM alembic_version;

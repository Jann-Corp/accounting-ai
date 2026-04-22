-- Production Database Migration Script
-- Adds default_wallet_id column to users table
-- Run this on production database if Alembic migration fails

-- Add default_wallet_id column (safe to run multiple times)
ALTER TABLE users ADD COLUMN IF NOT EXISTS default_wallet_id INTEGER;

-- Verify the column was added
\d users

-- Optional: Add index for performance (if needed)
-- CREATE INDEX IF NOT EXISTS ix_users_default_wallet_id ON users(default_wallet_id);

-- Verify migration
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'default_wallet_id';

# Production Database Migration - default_wallet_id

## Issue
Production database is missing the `default_wallet_id` column in the `users` table, causing 500 errors on login.

## Solution

### Option 1: Run Alembic Migration (Recommended)
```bash
# SSH to production server
ssh user@production-server

# Navigate to project directory
cd /path/to/accounting-ai

# Run Alembic migration
docker compose -p accounting-ai exec backend alembic upgrade head
```

### Option 2: Manual SQL (If Alembic Fails)
```bash
# SSH to production server
ssh user@production-server

# Run SQL script directly
docker compose -p accounting-ai exec db psql -U postgres -d accounting -f /tmp/PROD_manual_migration.sql

# Or run SQL command directly
docker compose -p accounting-ai exec db psql -U postgres -d accounting -c "ALTER TABLE users ADD COLUMN IF NOT EXISTS default_wallet_id INTEGER;"
```

### Option 3: Using the SQL File
```bash
# Copy SQL file to server
scp backend/alembic/versions/PROD_manual_migration.sql user@production-server:/tmp/

# SSH to production server
ssh user@production-server

# Run the script
docker compose -p accounting-ai exec db psql -U postgres -d accounting -f /tmp/PROD_manual_migration.sql
```

## Verification
After migration, verify the column exists:
```bash
docker compose -p accounting-ai exec db psql -U postgres -d accounting -c "\d users"
```

You should see `default_wallet_id | integer` in the output.

## Test
After migration, test login:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"your-username","password":"your-password"}'
```

Should return a token instead of 500 error.

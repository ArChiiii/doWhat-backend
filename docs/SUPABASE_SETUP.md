# Supabase Setup Guide

This guide explains how to set up Supabase for the doWhat backend, including database migrations and authentication configuration.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create Supabase Project](#create-supabase-project)
3. [Install Supabase CLI](#install-supabase-cli)
4. [Configure Environment Variables](#configure-environment-variables)
5. [Run Database Migrations](#run-database-migrations)
6. [Configure Authentication](#configure-authentication)
7. [Local Development](#local-development)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Node.js 18+ (for Supabase CLI)
- Python 3.12+ (for backend)
- PostgreSQL knowledge (helpful but not required)
- Supabase account ([sign up here](https://supabase.com))

---

## Create Supabase Project

### 1. Sign Up / Log In to Supabase

Visit [https://supabase.com](https://supabase.com) and create an account or log in.

### 2. Create New Project

1. Click **"New Project"**
2. Fill in project details:
   - **Organization**: Select or create organization
   - **Project Name**: `dowhat-production` (or your preferred name)
   - **Database Password**: Generate a strong password (save it securely)
   - **Region**: Select closest to Hong Kong (e.g., Singapore, Tokyo)
   - **Pricing Plan**: Free tier for development, Pro for production

3. Click **"Create new project"** and wait ~2 minutes for provisioning

### 3. Get Project Credentials

Once the project is ready, navigate to **Settings > API** and copy:

- **Project URL**: `https://xyzcompany.supabase.co`
- **Anon/Public Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`
- **Service Role Key**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (⚠️ Keep secret!)

Navigate to **Settings > Database** and copy:

- **Connection String (URI)**: `postgresql://postgres:[YOUR-PASSWORD]@db.xyzcompany.supabase.co:5432/postgres`

---

## Install Supabase CLI

### macOS / Linux

```bash
brew install supabase/tap/supabase
```

### Windows

```powershell
scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
scoop install supabase
```

### NPM (Cross-platform)

```bash
npm install -g supabase
```

### Verify Installation

```bash
supabase --version
# Should output: supabase version 1.x.x
```

---

## Configure Environment Variables

### 1. Copy Environment Template

```bash
cd backend
cp env.example .env
```

### 2. Update `.env` with Supabase Credentials

```bash
# Database
SUPABASE_URL=https://xyzcompany.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.xyzcompany.supabase.co:5432/postgres

# JWT Authentication (use Supabase JWT secret or generate your own)
JWT_SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# Other configurations...
ENVIRONMENT=development
DEBUG=true
```

### 3. Generate JWT Secret (Optional)

If not using Supabase JWT secret:

```bash
openssl rand -hex 32
```

---

## Run Database Migrations

### Option 1: Using Supabase Dashboard (Easiest)

1. Go to **Supabase Dashboard > SQL Editor**
2. Copy contents of `supabase/migrations/20251014000001_initial_schema.sql`
3. Paste into SQL editor and click **"Run"**
4. Repeat for `20251014000002_database_triggers.sql`
5. Verify tables created: **Database > Tables**

### Option 2: Using Supabase CLI (Recommended for Teams)

#### Link Local Project to Supabase

```bash
cd backend
supabase link --project-ref xyzcompany
# Enter your database password when prompted
```

#### Push Migrations to Supabase

```bash
supabase db push
```

This will:
- Read all SQL files in `supabase/migrations/`
- Execute them in order against your Supabase database
- Track migration history

#### Verify Migrations

```bash
supabase migration list
```

You should see:
```
20251014000001_initial_schema.sql - applied
20251014000002_database_triggers.sql - applied
```

### Option 3: Using Python/SQLAlchemy (Development Only)

⚠️ **Not recommended for production** - Use Supabase CLI instead.

```bash
cd backend
python -c "from app.database import engine, Base; from app.models import *; Base.metadata.create_all(engine)"
```

---

## Configure Authentication

### Enable Email Authentication

1. Go to **Authentication > Providers** in Supabase Dashboard
2. **Email** should be enabled by default
3. Configure email settings:
   - **Enable email confirmations**: ON (production) / OFF (development)
   - **Enable double opt-in**: OFF
   - **Secure email change**: ON

### Configure Google OAuth (Optional)

1. Go to **Authentication > Providers > Google**
2. Enable Google provider
3. Get Google OAuth credentials:
   - Visit [Google Cloud Console](https://console.cloud.google.com/)
   - Create OAuth 2.0 Client ID
   - Add redirect URI: `https://xyzcompany.supabase.co/auth/v1/callback`
4. Enter **Client ID** and **Client Secret** in Supabase
5. Save configuration

### Configure JWT Settings

1. Go to **Settings > API > JWT Settings**
2. Note the **JWT Secret** (used for token verification)
3. Set **JWT expiry**: 3600 (1 hour for access tokens)

---

## Local Development

### Option 1: Use Hosted Supabase (Easier)

Just use the connection details from your Supabase project:

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Your backend will connect to the hosted Supabase database.

### Option 2: Run Supabase Locally (Advanced)

For offline development or testing:

#### Start Local Supabase Stack

```bash
cd backend
supabase start
```

This spins up:
- PostgreSQL database (port 54322)
- PostgREST API (port 54321)
- Auth server (port 54321)
- Storage server (port 54321)
- Studio UI (port 54323)

#### Update `.env` for Local Development

```bash
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Printed by `supabase start`
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

#### Apply Migrations Locally

```bash
supabase db reset  # Resets local DB and applies all migrations
```

#### Stop Local Supabase

```bash
supabase stop
```

---

## Production Deployment

### 1. Environment Variables

Ensure production environment has:

```bash
SUPABASE_URL=https://your-prod-project.supabase.co
SUPABASE_ANON_KEY=<production-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<production-service-key>
DATABASE_URL=postgresql://postgres:<password>@db.your-prod-project.supabase.co:5432/postgres

ENVIRONMENT=production
DEBUG=false
```

### 2. Run Migrations

**Option A: Via Supabase CLI (Recommended)**

```bash
supabase link --project-ref your-prod-project
supabase db push
```

**Option B: Via SQL Editor**

Manually run migration files in Supabase Dashboard > SQL Editor.

### 3. Enable Row Level Security (RLS)

⚠️ **Important for production security**

```sql
-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE swipe_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE interested_events ENABLE ROW LEVEL SECURITY;

-- Example policy: Users can only read their own data
CREATE POLICY "Users can view their own profile"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- More policies will be added as needed
```

### 4. Set Up Database Backups

1. Go to **Database > Backups** in Supabase Dashboard
2. Enable **Point-in-Time Recovery** (Pro plan)
3. Configure daily backups
4. Test restore process

### 5. Enable Database Extensions

Enable required PostgreSQL extensions:

```sql
-- For full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- For scheduled jobs (optional)
CREATE EXTENSION IF NOT EXISTS pg_cron;
```

---

## Troubleshooting

### Migration Fails with "relation already exists"

**Solution**: Drop and recreate tables (⚠️ data loss!)

```bash
# Run rollback migration
supabase db reset  # Local only

# Or manually in SQL Editor:
# Copy contents of supabase/migrations/20251014999999_rollback_all.sql
```

### Can't Connect to Database

**Check**:
1. Database password is correct
2. IP is whitelisted (Settings > Database > Connection Pooling)
3. Connection string format is correct
4. Firewall allows outbound connections on port 5432

### Supabase CLI Commands Fail

**Solution**:
```bash
# Re-link project
supabase link --project-ref your-project-ref

# Or re-login
supabase login
```

### JWT Token Verification Fails

**Check**:
1. `JWT_SECRET_KEY` in `.env` matches Supabase JWT secret
2. Token hasn't expired (check `exp` claim)
3. Token type is correct (access vs refresh)

### Authentication Returns 401 Unauthorized

**Debug steps**:
1. Check Supabase Auth logs: **Authentication > Logs**
2. Verify email/password in Supabase Dashboard: **Authentication > Users**
3. Check if email confirmation is required (disable for dev)
4. Inspect JWT token payload: [jwt.io](https://jwt.io)

---

## Additional Resources

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [doWhat System Architecture](../../project-documentation/system-architecture.md)

---

## Next Steps

After completing this setup:

1. ✅ Verify database tables exist: `SELECT * FROM users;`
2. ✅ Test authentication: `POST /api/v1/auth/register`
3. ✅ Review [Authentication Documentation](./AUTHENTICATION.md)
4. ✅ Set up Redis for caching (see `REDIS_URL` in `.env`)
5. ✅ Configure web scraping service (see `../scrapers/`)

---

**Last Updated**: October 14, 2025
**Version**: 1.0

# Para Athletics Cloud Deployment Guide

This guide walks you through deploying the Para Athletics scraper to run automatically using GitHub Actions and Azure SQL Database.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE THREE-LAYER SANDWICH                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────────┐                                          │
│   │   GitHub Code    │  ← The Brain (your Python scripts)       │
│   │   (Repository)   │                                          │
│   └────────┬─────────┘                                          │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │  GitHub Actions  │  ← The Motor (runs daily at 2 AM)        │
│   │   (Scheduler)    │                                          │
│   └────────┬─────────┘                                          │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │    Azure SQL     │  ← The Memory (stores all data)          │
│   │    Database      │                                          │
│   └──────────────────┘                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

- GitHub account (free)
- Azure account (free tier available)
- VS Code or any code editor

---

## Step 1: Create Azure SQL Database (The Memory)

### 1.1 Create Azure Account
1. Go to https://portal.azure.com
2. Sign up for free (includes $200 credit)

### 1.2 Create SQL Database
1. In Azure Portal, click **Create a resource**
2. Search for **SQL Database**
3. Click **Create**

Fill in these fields:

**Resource Group:**
- Click **Create new**
- Name it: `para-athletics-rg`
- Click **OK**

**Database name:**
- Enter: `REDACTED_DB`

**Server:**
- Click **Create new**
- Fill in:
  - **Server name**: `para-athletics-server-ksa` (must be globally unique)
  - **Location**: `UK South` (or closest to you)
  - **Authentication**: Use SQL authentication
  - **Server admin login**: `REDACTED_USER`
  - **Password**: Create a strong password (SAVE THIS!)
- Click **OK**

**Want to use SQL elastic pool?**: No

**Compute + storage:**
- Click **Configure database**
- Look for **Free tier** or **Basic** tier
- Select it and click **Apply**

Click **Review + create** → **Create**

### 1.3 Configure Firewall
1. Go to your SQL Server (not database)
2. Click **Networking** in left menu
3. Under **Firewall rules**:
   - Check ✅ **Allow Azure services and resources to access this server**
4. Click **Save**

### 1.4 Get Connection String
1. Go to your SQL Database
2. Click **Connection strings** in left menu
3. Copy the **ODBC** connection string
4. Replace `{your_password}` with your actual password

Example:
```
Driver={ODBC Driver 18 for SQL Server};Server=tcp:REDACTED_SERVER,1433;Database=REDACTED_DB;Uid=REDACTED_USER;Pwd=YourPassword123!;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;
```

### 1.5 Create Database Tables
1. In Azure Portal, go to your database
2. Click **Query editor** in left menu
3. Login with your admin credentials
4. Copy contents of `database/azure_schema.sql`
5. Paste and click **Run**

---

## Step 2: Set Up GitHub Repository (The Brain)

### 2.1 Create Repository
1. Go to https://github.com
2. Click **New repository**
3. Name: `para-athletics-pipeline`
4. Make it **Private** (recommended)
5. Click **Create repository**

### 2.2 Push Your Code
In VS Code terminal:
```bash
cd "c:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Para Athletics\Project"

# Initialize git (if not already)
git init

# Add files
git add .
git commit -m "Initial commit - Para Athletics pipeline"

# Connect to GitHub
git remote add origin https://github.com/YOUR_USERNAME/para-athletics-pipeline.git
git branch -M main
git push -u origin main
```

### 2.3 Add Secret (The Security Handshake)
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `SQL_CONNECTION_STRING`
5. Value: Paste your Azure connection string (from Step 1.4)
6. Click **Add secret**

---

## Step 3: Configure GitHub Actions (The Motor)

The workflow file is already created at `.github/workflows/daily_scraper.yml`.

### What It Does:
- Runs every **Sunday** at 2 AM UTC (6 AM Saudi time) - weekly schedule to stay within free tier limits
- Can be triggered manually from GitHub Actions tab anytime
- Scrapes rankings, records, and Tilastopaja database
- Checks for updates before downloading (smart update detection)
- Uploads data to Azure SQL
- Saves logs as artifacts

### Free Tier Limits:
- **Azure SQL Basic**: 2 GB storage, ~$5/month
- **GitHub Actions**: 2,000 min/month free (weekly uses only ~60 min/month)

### Test the Workflow:
1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Daily Para Athletics Data Scraper**
4. Click **Run workflow**
5. Select `all` to test both scrapers
6. Click **Run workflow**

Watch the logs to ensure it works!

---

## Step 4: Local Development Setup

Keep your local setup working alongside the cloud deployment.

### Local Mode (Default)
```bash
# Scrapes and saves to local CSV files
python cloud_scraper.py --type rankings --mode local
python cloud_scraper.py --type records --mode local
```

### Cloud Mode (Test Azure Connection Locally)
```bash
# Set environment variable
set AZURE_SQL_CONN="your_connection_string"

# Run with cloud mode
python cloud_scraper.py --type rankings --mode cloud
```

### Using .env File (Recommended for Local)
Create a `.env` file (add to .gitignore!):
```
AZURE_SQL_CONN=Driver={ODBC Driver 18 for SQL Server};Server=tcp:...
SCRAPER_MODE=local
```

---

## File Structure

```
Project/
├── .github/
│   └── workflows/
│       └── daily_scraper.yml    # GitHub Actions workflow
├── database/
│   └── azure_schema.sql         # Azure SQL schema
├── data/                        # Local data storage
│   ├── Rankings/
│   ├── Records/
│   └── Tilastoptija/
├── logs/                        # Scraper logs
├── cloud_scraper.py             # Cloud-ready unified scraper
├── requirements.txt             # Python dependencies
├── DEPLOYMENT_GUIDE.md          # This file
└── team_saudi_intelligence_dashboard.py  # Local dashboard
```

---

## Monitoring & Maintenance

### Check Scraper Status
1. GitHub → Actions tab → See workflow runs
2. Click a run to view logs
3. Download artifacts for detailed logs

### Azure SQL Monitoring
1. Azure Portal → Your database
2. Check **Metrics** for usage
3. View **Query editor** to verify data

### Cost Management
- Azure SQL Basic tier: ~$5/month
- GitHub Actions: Free for public repos, 2000 min/month for private
- **Tip**: Use Serverless compute to minimize costs

---

## Troubleshooting

### "Connection refused" Error
- Check Azure firewall settings
- Ensure "Allow Azure services" is enabled

### "Login failed" Error
- Verify connection string password
- Check admin username

### "Module not found" Error
- Requirements not installed
- Check GitHub Actions logs for pip install output

### Scraper Timeout
- IPC website may be slow
- Increase timeout in cloud_scraper.py

---

## Schedule Options

Edit `.github/workflows/daily_scraper.yml` cron schedule:

```yaml
# Every day at midnight UTC
- cron: '0 0 * * *'

# Every day at 2 AM UTC (6 AM Saudi)
- cron: '0 2 * * *'

# Every Monday at 3 AM UTC
- cron: '0 3 * * 1'

# Every 6 hours
- cron: '0 */6 * * *'
```

---

## Security Best Practices

1. **Never commit secrets** - Use GitHub Secrets
2. **Keep .env in .gitignore** - Don't upload local credentials
3. **Use least privilege** - Create database user with limited permissions
4. **Rotate passwords** - Update Azure password periodically
5. **Monitor access** - Check Azure audit logs

---

## Next Steps

1. ✅ Create Azure SQL Database
2. ✅ Run schema script
3. ✅ Push code to GitHub
4. ✅ Add connection string secret
5. ✅ Test workflow manually
6. 🔄 Monitor daily runs
7. 📊 Connect dashboard to Azure SQL (future enhancement)

---

## Support

- Azure Documentation: https://docs.microsoft.com/azure/sql-database
- GitHub Actions: https://docs.github.com/actions
- Para Athletics Project: See CLAUDE.md for codebase details

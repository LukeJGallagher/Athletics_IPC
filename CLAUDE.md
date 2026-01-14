# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics data pipeline for **Team Saudi** (Saudi Arabia Paralympic Program). Fetches data from Tilastopaja API and IPC sources, stores in Azure SQL Database, runs automated weekly via GitHub Actions.

**Repository**: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja

## Repository Structure (GitHub)

```
.github/workflows/daily_scraper.yml  # Weekly automated scraper (Sunday 2AM UTC)
azure_db.py                           # Unified database connection module (NEW)
azure_dashboard.py                    # Streamlit dashboard with Azure SQL backend (NEW)
cloud_scraper.py                      # Rankings/records scraper (local or Azure mode)
tilastopaja_updater.py                # Smart merge updater (checks before download)
migrate_to_azure.py                   # One-time data migration script (NEW)
upload_to_azure.py                    # Batch upload utility (security-fixed)
database/azure_schema.sql             # Azure SQL table schema
.streamlit/secrets.toml.example       # Streamlit Cloud secrets template (NEW)
requirements.txt                      # Python dependencies
scraper_config.json                   # Scraper configuration
DEPLOYMENT.md                         # Streamlit Cloud deployment guide (NEW)
```

## Critical Technical Requirements

### Data Encoding (MUST USE)
```python
# ALWAYS use Latin-1 encoding for CSV files
df = pd.read_csv('data/Tilastoptija/ksaoutputipc3.csv',
                 encoding='latin-1', low_memory=False)

# Remote API uses semicolon separator
df = pd.read_csv(url, sep=';')
```

### Unique Key for Merging
- Use `resultid` column to identify unique records
- Merge strategy: append new records only (don't replace)

## Core Commands

### Tilastopaja Updater
```bash
python tilastopaja_updater.py --check           # Check if updates available
python tilastopaja_updater.py --compare         # Compare local vs remote
python tilastopaja_updater.py --check-and-update  # Download only if new
python tilastopaja_updater.py --force           # Force download and merge
python tilastopaja_updater.py --stats           # Show local file stats
```

### Cloud Scraper
```bash
# Local mode (saves to CSV)
python cloud_scraper.py --type rankings --mode local
python cloud_scraper.py --type records --mode local

# Cloud mode (saves to Azure SQL)
set AZURE_SQL_CONN="your_connection_string"
python cloud_scraper.py --type rankings --mode cloud
```

### Azure Dashboard (NEW)
```bash
# Test database connection
python azure_db.py

# Run dashboard locally (auto-detects Azure SQL or SQLite)
streamlit run azure_dashboard.py
# Visit: http://localhost:8501

# Migrate CSV data to Azure SQL (one-time)
python migrate_to_azure.py
```

## Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ DATA INGESTION (GitHub Actions - Weekly Sunday 2AM UTC)    │
├─────────────────────────────────────────────────────────────┤
│ cloud_scraper.py → Rankings/Records → Azure SQL            │
│ tilastopaja_updater.py → Tilastopaja CSV → Azure SQL       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ AZURE SQL DATABASE (Serverless, Auto-pause)                │
├─────────────────────────────────────────────────────────────┤
│ Tables: Rankings, Records, Results, Athletes, ScrapeLog    │
│ Current Data: 2,000+ results (140K+ after full migration)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STREAMLIT DASHBOARD (Streamlit Cloud)                      │
├─────────────────────────────────────────────────────────────┤
│ azure_dashboard.py (via azure_db.py connection module)     │
│ URL: https://share.streamlit.io/ (to be deployed)          │
│ Tabs: Results, Rankings, Records, Saudi Arabia             │
└─────────────────────────────────────────────────────────────┘
```

### Azure SQL Database (Verified Working)
- **Server**: `REDACTED_SERVER`
- **Database**: `REDACTED_DB`
- **Tables**: Rankings, Records, Results, Athletes, ScrapeLog
- **Admin**: `REDACTED_USER`
- **Current Data**: 2,000 results (test upload), 140,692 available for migration

### Unified Connection Module (`azure_db.py`)
- **Auto-detects environment**: Local `.env` vs Streamlit Cloud `secrets`
- **Driver compatibility**: `SQL Server` (local) vs `ODBC Driver 17` (cloud)
- **Lazy-loading secrets**: Prevents import-time errors
- **SQLite fallback**: Works without Azure SQL configured

### GitHub Secrets Required
- `SQL_CONNECTION_STRING`: Azure SQL ODBC connection string

### Streamlit Cloud Secrets Required
- `AZURE_SQL_CONN`: Azure SQL connection string with Driver 17
- Template: `.streamlit/secrets.toml.example`

### Manual Workflow Trigger
1. Go to: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja/actions
2. Click "Weekly Para Athletics Data Scraper"
3. Click "Run workflow" → Select scraper_type → Run

## Data Sources

### Tilastopaja API
- **URL**: `https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv`
- **Format**: Semicolon-separated CSV
- **Update frequency**: Incremental (new results only)

### Local Database (not in repo)
- **Location**: `data/Tilastoptija/ksaoutputipc3.csv`
- **Rows**: 140,692 (after 2025 merge)
- **Coverage**: 2012-2025, 11,576 athletes, 87 events

## Key Patterns

### Merge Logic (tilastopaja_updater.py)
```python
# Find new records by resultid
local_ids = set(local_df['resultid'].dropna().astype(str))
remote_ids = set(remote_df['resultid'].dropna().astype(str))
new_ids = remote_ids - local_ids

# Append only new records
new_records = remote_df[remote_df['resultid_str'].isin(new_ids)]
merged_df = pd.concat([local_df, new_records], ignore_index=True)
```

### Saudi Athlete Filter
```python
saudi = df[df['nationality'] == 'KSA']
```

## Environment Variables

### Local Development (.env)
```bash
# Local uses "SQL Server" driver (Windows default)
AZURE_SQL_CONN=Driver={SQL Server};Server=tcp:REDACTED_SERVER,1433;Database=REDACTED_DB;Uid=REDACTED_USER;Pwd=***;Connection Timeout=60;

SCRAPER_MODE=local|cloud
TILASTOPAJA_URL=https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv
```

### Streamlit Cloud (secrets.toml)
```toml
# Streamlit Cloud uses "ODBC Driver 17" (not 18)
AZURE_SQL_CONN = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:REDACTED_SERVER,1433;Database=REDACTED_DB;Uid=REDACTED_USER;Pwd=***;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
```

## Streamlit Cloud Deployment (NEW)

### Quick Deploy Steps
1. Push code to GitHub: `git push origin main`
2. Go to https://share.streamlit.io/
3. Create new app:
   - Repository: `LukeJGallagher/Athleticsipc_Tilastoptja`
   - Branch: `main`
   - Main file: `azure_dashboard.py`
4. Add secret in Advanced settings (use Driver 17)
5. Deploy (takes 2-3 minutes)

### Deployment Files
- `azure_db.py`: Connection module (auto-detects environment)
- `azure_dashboard.py`: Main Streamlit app
- `.streamlit/secrets.toml.example`: Secrets template
- `DEPLOYMENT.md`: Full deployment guide

### Testing Checklist
- [ ] Local test: `python azure_db.py` (should show "azure" mode)
- [ ] Dashboard test: `streamlit run azure_dashboard.py`
- [ ] Sidebar shows "Database: AZURE"
- [ ] Data loads successfully
- [ ] All tabs work (Results, Rankings, Records, Saudi Arabia)

## Common Issues

| Issue | Solution |
|-------|----------|
| Encoding errors | Use `encoding='latin-1'` not UTF-8 |
| Remote parse error | Use `sep=';'` for Tilastopaja API |
| Azure connection fails | Check firewall allows Azure services |
| Workflow won't start | Verify `SQL_CONNECTION_STRING` secret exists |
| "Can't open lib ODBC Driver 18" | Use Driver 17 for Streamlit Cloud |
| "Login timeout expired" | Azure SQL paused, wait 30s and retry |
| "Module not found" | Verify all files committed to GitHub |

## Team Saudi Branding

```python
COLORS = {
    'primary_teal': '#007167',
    'gold_accent': '#a08e66',
    'dark_teal': '#005a51'
}
```

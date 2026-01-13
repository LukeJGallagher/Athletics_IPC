# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics data pipeline for **Team Saudi** (Saudi Arabia Paralympic Program). Fetches data from Tilastopaja API and IPC sources, stores in Azure SQL Database, runs automated weekly via GitHub Actions.

**Repository**: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja

## Repository Structure (GitHub)

```
.github/workflows/daily_scraper.yml  # Weekly automated scraper (Sunday 2AM UTC)
cloud_scraper.py                      # Rankings/records scraper (local or Azure mode)
tilastopaja_updater.py                # Smart merge updater (checks before download)
database/azure_schema.sql             # Azure SQL table schema
requirements.txt                      # Python dependencies
scraper_config.json                   # Scraper configuration
DEPLOYMENT_GUIDE.md                   # Setup instructions
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

## Cloud Architecture

```
GitHub Actions (weekly Sunday 2AM UTC)
         │
         ├──> cloud_scraper.py ──> Rankings/Records ──> Azure SQL
         │
         └──> tilastopaja_updater.py ──> Tilastopaja CSV ──> Azure SQL
```

### GitHub Secrets Required
- `SQL_CONNECTION_STRING`: Azure SQL ODBC connection string

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

```bash
AZURE_SQL_CONN=Driver={ODBC Driver 18 for SQL Server};Server=tcp:...
SCRAPER_MODE=local|cloud
TILASTOPAJA_URL=https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Encoding errors | Use `encoding='latin-1'` not UTF-8 |
| Remote parse error | Use `sep=';'` for Tilastopaja API |
| Azure connection fails | Check firewall allows Azure services |
| Workflow won't start | Verify `SQL_CONNECTION_STRING` secret exists |

## Team Saudi Branding

```python
COLORS = {
    'primary_teal': '#007167',
    'gold_accent': '#a08e66',
    'dark_teal': '#005a51'
}
```

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics data pipeline and analysis system for **Team Saudi** (Saudi Arabia Paralympic Program). The system:
- Fetches data from Tilastopaja API and IPC sources
- Stores in Azure SQL Database (110K+ results)
- Runs automated weekly scraping via GitHub Actions
- Provides Streamlit dashboard with 6 analysis tabs
- Generates championship standards and pre-competition reports

**Repository**: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja

## Critical Technical Requirements

### Data Encoding (MUST USE)
```python
# ALWAYS use Latin-1 encoding for CSV files
df = pd.read_csv('data/Tilastoptija/ksaoutputipc3.csv',
                 encoding='latin-1', low_memory=False)

# Remote Tilastopaja API uses semicolon separator
df = pd.read_csv(url, sep=';')
```

### Unique Key for Merging
- Use `resultid` column to identify unique records
- Merge strategy: append new records only (don't replace)

### Saudi Athlete Filter
```python
saudi = df[df['nationality'] == 'KSA']
```

## Core Commands

### Run Dashboard Locally
```bash
streamlit run azure_dashboard.py
# Visit: http://localhost:8501
```

### Data Scrapers
```bash
# Run all scrapers (rankings, records, results)
python run_all_scrapers.py

# Individual scrapers
python scrape_rankings.py       # Current year rankings (incremental)
python scrape_records6.py       # Full records replacement (requires visible browser)
python scrape_results.py        # Championship PDF results

# Tilastopaja updater
python tilastopaja_updater.py --check-and-update  # Download only if new data
python tilastopaja_updater.py --force             # Force download and merge
```

### Azure SQL Operations
```bash
python azure_db.py              # Test database connection
python check_azure_tables.py    # Show table row counts
python migrate_to_azure.py --yes  # Migrate CSV to Azure SQL
python backup_azure_to_csv.py   # Backup Azure tables to CSV
```

### Analysis Scripts
```bash
python championship_winning_standards.py    # Generate medal standards report
python comprehensive_event_analysis_v2.py   # Multi-page event PDFs
python pre_competition_championship_report.py  # 5-page pre-comp reports
python saudi_athletics_management_report.py    # Saudi-specific analysis
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ DATA INGESTION (GitHub Actions - Weekly Sunday 2AM UTC)     │
├─────────────────────────────────────────────────────────────┤
│ scrape_rankings.py  → data/Rankings/*.csv → Azure SQL       │
│ scrape_records6.py  → data/Records/*.csv  → Azure SQL       │
│ tilastopaja_updater.py → Tilastopaja API  → Azure SQL       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ AZURE SQL DATABASE (para-athletics-server-ksa)              │
├─────────────────────────────────────────────────────────────┤
│ Tables: Results (110K), Rankings, Records, Athletes         │
│ Connection: azure_db.py (auto-detects local vs cloud)       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STREAMLIT DASHBOARD (azure_dashboard.py)                    │
├─────────────────────────────────────────────────────────────┤
│ Tab 1: Results (filters, top competitions)                  │
│ Tab 2: Rankings (year/event filters, Saudi highlight)       │
│ Tab 3: Records (world/regional records by type)             │
│ Tab 4: Saudi Arabia (KSA-specific analysis)                 │
│ Tab 5: Championship Analysis (medal standards)              │
│ Tab 6: Athlete Analysis (profiles, gap analysis)            │
└─────────────────────────────────────────────────────────────┘
```

## Key Modules

### azure_db.py - Unified Database Connection
- Auto-detects environment: local `.env` vs Streamlit Cloud `secrets`
- Driver compatibility: `SQL Server` (local) vs `ODBC Driver 17` (cloud)
- SQLite fallback when Azure not configured

### data_access_layer.py - Hybrid Data Access
```python
from data_access_layer import DataManager
dm = DataManager()           # Auto-detects Azure or local
results = dm.get_results()
rankings = dm.get_rankings(year=2024)
saudi = dm.get_saudi_athletes()
```

### azure_dashboard.py - Dashboard Functions
- `load_results()`, `load_rankings()`, `load_records()` - Data loading with Azure/local fallback
- `get_major_championships()` - Filter Paralympics/World Championships/Asian Championships
- `analyze_championship_standards()` - Calculate gold/silver/bronze/8th place standards
- `parse_performance()` - Convert time strings (mm:ss.xx) and distances to float

## Data Sources

| Source | Location | Records | Format |
|--------|----------|---------|--------|
| Main Results | `data/Tilastoptija/ksaoutputipc3.csv` | 140K | Latin-1, comma-sep |
| Rankings | `data/Rankings/*.csv` | 119 files | UTF-8 |
| Records | `data/Records/*.csv` | 11 files | UTF-8 |
| Azure SQL | Results table | 110K | ODBC |

## Environment Variables

### Local Development (.env)
```bash
AZURE_SQL_CONN=Driver={SQL Server};Server=tcp:REDACTED_SERVER,1433;Database=REDACTED_DB;Uid=REDACTED_USER;Pwd=***;Connection Timeout=60;
```

### Streamlit Cloud (secrets.toml)
```toml
# Use ODBC Driver 17 (not 18)
AZURE_SQL_CONN = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:REDACTED_SERVER,1433;..."
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Encoding errors | Use `encoding='latin-1'` not UTF-8 |
| Remote parse error | Use `sep=';'` for Tilastopaja API |
| "Can't open lib ODBC Driver 18" | Use Driver 17 for Streamlit Cloud |
| "Login timeout expired" | Azure SQL paused, wait 30s and retry |
| Records scraper fails | Must run with visible browser (`headless=False`) |
| Position comparison TypeError | Add `pd.to_numeric(df['position'], errors='coerce')` |

## Team Saudi Branding

```python
TEAL_PRIMARY = '#007167'   # Main brand color, headers
GOLD_ACCENT = '#a08e66'    # PB markers, highlights
TEAL_DARK = '#005a51'      # Hover states, gradients
TEAL_LIGHT = '#009688'     # Secondary positive
GRAY_BLUE = '#78909C'      # Neutral
```

## GitHub Actions

- **Workflow**: `.github/workflows/daily_scraper.yml`
- **Schedule**: Weekly Sunday 2AM UTC
- **Manual trigger**: Actions → "Weekly Para Athletics Data Scraper" → Run workflow
- **Required secret**: `SQL_CONNECTION_STRING`

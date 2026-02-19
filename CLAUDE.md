# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics data pipeline and analysis system for **Team Saudi** (Saudi Arabia Paralympic Program). The system:
- Fetches data from Tilastopaja API and IPC sources
- Stores in Azure Blob Storage (Parquet) and Azure SQL Database (140K+ results)
- Runs automated weekly scraping via GitHub Actions
- Provides Streamlit dashboard with 7 analysis tabs (including interactive Event Reports)
- Generates championship standards with Saudi gap analysis and pre-competition reports

**Repository**: https://github.com/LukeJGallagher/Athletics_IPC

## Critical Technical Requirements

### Data Encoding (MUST USE)
```python
# ALWAYS use Latin-1 encoding for local CSV files
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

### DataFrame Filtering Safety
```python
# ALWAYS use .copy() when filtering DataFrames before assigning new columns
filtered_df = df[df['event'] == 'some_event'].copy()
filtered_df['new_col'] = ...  # Safe - no SettingWithCopyWarning

# Use exact match (==) not str.contains() for event/class filters
# str.contains() treats values as regex - parentheses/special chars crash it
event_filter = df['event_name'] == selected_event  # Correct
# NOT: df['event_name'].str.contains(selected_event)  # Crashes on special chars

# Boolean fallback must be a Series, not scalar
class_filter = df['class'] == val if 'class' in df.columns else pd.Series([True] * len(df))
```

## Core Commands

### Run Dashboard Locally
```bash
streamlit run azure_dashboard.py
# Visit: http://localhost:8501
# Use --server.port=8505 for alternate port
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

# Cloud scraper (used by GitHub Actions)
python cloud_scraper.py --type rankings
python cloud_scraper.py --type records
```

### Azure Operations
```bash
# Azure SQL
python azure_db.py              # Test database connection
python migrate_to_azure.py --yes  # Migrate CSV to Azure SQL

# Azure Blob Storage (Parquet - preferred for cloud)
python convert_csv_to_parquet.py  # Convert CSVs to Parquet and upload

# Backup & verify
python backup_azure_to_csv.py    # Backup Azure SQL to CSV
python check_azure_tables.py     # Verify Azure table state
```

### Analysis Scripts
```bash
# Championship standards with Saudi gap analysis (27 columns)
python championship_winning_standards.py
# Outputs: championship_standards_report.csv

# Comprehensive event analysis
python comprehensive_event_analysis_v2.py   # Multi-page event PDFs
python pre_competition_championship_report.py  # 5-page pre-comp reports
python saudi_athletics_management_report.py    # Saudi-specific analysis
python ksa_athletes_competitor_report.py       # Competitor analysis reports
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ DATA INGESTION (GitHub Actions - Weekly Sunday 2AM UTC)     │
├─────────────────────────────────────────────────────────────┤
│ cloud_scraper.py --type rankings → data/Rankings/*.csv      │
│ cloud_scraper.py --type records  → data/Records/*.csv       │
│ tilastopaja_updater.py → Tilastopaja API (merge by resultid)│
│ convert_csv_to_parquet.py → Azure Blob Storage (Parquet)    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER (parquet_data_layer.py)                          │
├─────────────────────────────────────────────────────────────┤
│ Mode 1: azure_blob → DuckDB queries on remote Parquet      │
│ Mode 2: local_parquet → data/parquet_cache/*.parquet        │
│ Mode 3: local_csv → data/Tilastoptija/*.csv (fallback)      │
│ Azure SQL: para-athletics-server-ksa (legacy fallback)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STREAMLIT DASHBOARD (azure_dashboard.py)                    │
├─────────────────────────────────────────────────────────────┤
│ Tab 1: Results (filters, top competitions)                  │
│ Tab 2: Rankings (year/event filters, Saudi highlight)       │
│ Tab 3: Records (world records by event filter)              │
│ Tab 4: Saudi Arabia (KSA Athlete Profiles)                  │
│   └─ Subtabs: Athlete Profile, Squad Overview,              │
│      Performance Trends, Top Performers                     │
│ Tab 5: Championship Standards (medal targets, Saudi gaps)   │
│   └─ Gap Analysis by Championship Type, Medal Calculator    │
│ Tab 6: Athlete Analysis (country filter, event comparison)  │
│ Tab 7: Event Reports (interactive version of PDF reports)   │
│   └─ Subtabs: Championship Standards, Competition Field,    │
│      Historical Data, Performance Analysis, Saudi Context   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ ANALYSIS & REPORTING                                        │
├─────────────────────────────────────────────────────────────┤
│ championship_winning_standards.py → CSV (27 columns)        │
│ comprehensive_event_analysis_v2.py → Multi-page PDFs        │
│ pre_competition_championship_report.py → 5-page PDFs        │
│ saudi_athletics_management_report.py → Saudi reports        │
└─────────────────────────────────────────────────────────────┘
```

## Key Modules

### parquet_data_layer.py - Primary Data Access (Preferred)
```python
from parquet_data_layer import get_data_manager, load_results
dm = get_data_manager()
results = dm.get_results()    # 140K rows from Parquet/CSV
rankings = dm.get_rankings()  # Combined rankings
records = dm.get_records()    # All record types
mode = dm.get_connection_mode()  # 'azure_blob'/'local_parquet'/'local_csv'
```
Auto-detects mode: azure_blob → local_parquet → local_csv fallback chain.

### azure_blob_storage.py - Parquet Cloud Storage
- Uploads/downloads Parquet files to Azure Blob Storage
- DuckDB for fast in-memory SQL queries on Parquet
- Local cache in `data/parquet_cache/`

### azure_db.py - SQL Database Connection (Fallback)
- Auto-detects environment: local `.env` vs Streamlit Cloud `secrets`
- Driver compatibility: `SQL Server` (local) vs `ODBC Driver 17` (cloud)

### championship_winning_standards.py - Gap Analysis
Key methods for championship standards report:
- `_get_world_record()` - Match world records to event/class/gender
- `_get_asian_championship_standards()` - Extract Asian medal standards
- `_get_saudi_best_performance()` - Find best Saudi performance per event
- `_calculate_gap()` - Gap to gold/bronze/8th (negative = better for track)
- `_get_year_over_year_trend()` - Performance trend from rankings

### azure_dashboard.py - Main Dashboard
- Team Saudi branded with banner image and green sidebar gradient
- Uses `@lru_cache(maxsize=50000)` on `parse_performance()` for speed
- Base64-encoded images for banner/logo embedding
- Tab 7 Event Reports replicates PDF report functionality interactively

### agents/ - AI Agent Framework
- `data_agent.py` - Data loading & validation
- `analysis_agent.py` - Championship analysis
- `prediction_agent.py` - Performance predictions
- `saudi_agent.py` - Saudi-specific analysis
- `pdf_analysis_agent.py` - PDF data extraction
- `skills.py` - Shared agent skill library

## Data Sources

| Source | Location | Records | Format |
|--------|----------|---------|--------|
| Main Results | `data/Tilastoptija/ksaoutputipc3.csv` | 140K | Latin-1 |
| Rankings | `data/Rankings/*.csv` | 119 files | UTF-8 |
| Records | `data/Records/*.csv` | 11 files | UTF-8 |
| Parquet Cache | `data/parquet_cache/*.parquet` | 4 files | Parquet |
| Championship Standards | `championship_standards_report.csv` | 271 rows | CSV |
| Championship PDFs | `data/PDF/*.pdf` | 3 files | PDF |

## Environment Variables

### Local Development (.env)
```bash
AZURE_SQL_CONN=Driver={SQL Server};Server=tcp:<YOUR_SERVER>.database.windows.net,1433;...
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
```

### Streamlit Cloud (secrets.toml)
```toml
AZURE_SQL_CONN = "Driver={ODBC Driver 17 for SQL Server};..."
AZURE_STORAGE_CONNECTION_STRING = "DefaultEndpointsProtocol=https;..."
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
| Gap analysis wrong sign | Track events: negative gap = faster (better) |
| Event filter crash | Use `==` exact match, not `str.contains()` (regex chars crash) |
| SettingWithCopyWarning | Always `.copy()` filtered DataFrames before assigning columns |
| Boolean filter scalar | Use `pd.Series([True] * len(df))` not bare `True` for fallbacks |

## Team Saudi Branding

```python
TEAL_PRIMARY = '#007167'   # Main brand color, headers, sidebar gradient
GOLD_ACCENT = '#a08e66'    # PB markers, highlights, gold medals
TEAL_DARK = '#005a51'      # Hover states, sidebar gradient endpoint
TEAL_LIGHT = '#009688'     # Secondary positive
GRAY_BLUE = '#78909C'      # Neutral
```

Dashboard uses:
- Team Saudi banner image (`Theme/team_saudi_banner.jpg`) with dark overlay
- Green sidebar gradient (`TEAL_PRIMARY` → `TEAL_DARK`)
- Sidebar logo (`Theme/team_saudi_logo.jpg`)
- Gold accent bar at banner bottom
- `.streamlit/config.toml` with `primaryColor = "#007167"`

## GitHub Actions

- **Workflow**: `.github/workflows/daily_scraper.yml`
- **Schedule**: Weekly Sunday 2AM UTC
- **Manual trigger**: Actions → "Weekly Para Athletics Data Scraper" → Run workflow
- **Pipeline**: `cloud_scraper.py` (rankings + records) → `tilastopaja_updater.py` → `convert_csv_to_parquet.py`
- **Required secrets**: `SQL_CONNECTION_STRING`, `AZURE_STORAGE_CONNECTION_STRING`

## Dependencies

### requirements.txt (production)
Core: pandas, numpy, matplotlib, seaborn, playwright, requests, beautifulsoup4, pyodbc, sqlalchemy, streamlit, plotly, azure-storage-blob, pyarrow, duckdb, python-dotenv, fuzzywuzzy, openpyxl

### requirements_agents.txt (agents + dev)
Adds: scikit-learn, scipy, statsmodels, PyPDF2, pdfplumber, tabula-py, openai, pytest

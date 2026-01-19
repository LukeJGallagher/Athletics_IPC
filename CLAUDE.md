# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics data pipeline and analysis system for **Team Saudi** (Saudi Arabia Paralympic Program). The system:
- Fetches data from Tilastopaja API and IPC sources
- Stores in Azure Blob Storage (Parquet) and Azure SQL Database (140K+ results)
- Runs automated weekly scraping via GitHub Actions
- Provides Streamlit dashboard with 6 analysis tabs
- Generates championship standards with Saudi gap analysis and pre-competition reports

**Repository**: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja

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

### Azure Operations
```bash
# Azure SQL
python azure_db.py              # Test database connection
python migrate_to_azure.py --yes  # Migrate CSV to Azure SQL

# Azure Blob Storage (Parquet - preferred for cloud)
python convert_csv_to_parquet.py  # Convert CSVs to Parquet and upload
```

### Analysis Scripts
```bash
# Championship standards with Saudi gap analysis (27 columns)
python championship_winning_standards.py
# Outputs: championship_standards_report.csv (world records, medal standards, Saudi gaps)

# Comprehensive event analysis
python comprehensive_event_analysis_v2.py   # Multi-page event PDFs
python pre_competition_championship_report.py  # 5-page pre-comp reports
python saudi_athletics_management_report.py    # Saudi-specific analysis
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ DATA INGESTION (GitHub Actions - Weekly Sunday 2AM UTC)     │
├─────────────────────────────────────────────────────────────┤
│ scrape_rankings.py  → data/Rankings/*.csv                   │
│ scrape_records6.py  → data/Records/*.csv                    │
│ tilastopaja_updater.py → Tilastopaja API                    │
│ convert_csv_to_parquet.py → Azure Blob Storage (Parquet)    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ DATA LAYER (Parquet preferred, SQL fallback)                │
├─────────────────────────────────────────────────────────────┤
│ Azure Blob: para-athletics-data container (Parquet files)   │
│ Azure SQL: para-athletics-server-ksa (140K results)         │
│ Local: data/parquet_cache/ (cached Parquet files)           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ STREAMLIT DASHBOARD (azure_dashboard.py)                    │
├─────────────────────────────────────────────────────────────┤
│ Tab 1: Results (filters, top competitions)                  │
│ Tab 2: Rankings (year/event filters, Saudi highlight)       │
│ Tab 3: Records (world/regional records by type)             │
│ Tab 4: Saudi Arabia (KSA Athlete Profiles)                  │
│   └─ Subtabs: Athlete Profile, Squad Overview,              │
│      Performance Trends, Top Performers                     │
│ Tab 5: Championship Standards (medal targets, Saudi gaps)   │
│   └─ Gap Analysis by Championship Type, Medal Calculator    │
│ Tab 6: Athlete Analysis (country filter, event comparison)  │
└─────────────────────────────────────────────────────────────┘
```

## Key Modules

### parquet_data_layer.py - Primary Data Access (Preferred)
```python
from parquet_data_layer import get_data_manager, load_results
dm = get_data_manager()
results = load_results()  # From Parquet or local cache
```

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

### championship_standards_report.csv - Output (27 columns)
```
event, classification, gender, world_record, world_record_display,
paralympics_gold, paralympics_bronze, paralympics_8th_place,
wc_gold, wc_bronze, wc_8th_place,
asian_gold, asian_bronze, asian_8th_place,
saudi_best, saudi_best_athlete, saudi_world_rank,
gap_to_para_gold, gap_to_para_bronze, gap_to_para_8th, gap_to_world_record,
yearly_trend, total_results
```

## Data Sources

| Source | Location | Records | Format |
|--------|----------|---------|--------|
| Main Results | `data/Tilastoptija/ksaoutputipc3.csv` | 140K | Latin-1 |
| Rankings | `data/Rankings/*.csv` | 119 files | UTF-8 |
| Records | `data/Records/*.csv` | 11 files | UTF-8 |
| Parquet Cache | `data/parquet_cache/*.parquet` | 3 files | Parquet |
| Championship Standards | `championship_standards_report.csv` | 271 rows | CSV |

## Environment Variables

### Local Development (.env)
```bash
AZURE_SQL_CONN=Driver={SQL Server};Server=tcp:REDACTED_SERVER,1433;...
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

## Team Saudi Branding

```python
TEAL_PRIMARY = '#007167'   # Main brand color, headers
GOLD_ACCENT = '#a08e66'    # PB markers, highlights, gold medals
TEAL_DARK = '#005a51'      # Hover states, gradients
TEAL_LIGHT = '#009688'     # Secondary positive
GRAY_BLUE = '#78909C'      # Neutral
```

## GitHub Actions

- **Workflow**: `.github/workflows/daily_scraper.yml`
- **Schedule**: Weekly Sunday 2AM UTC
- **Manual trigger**: Actions → "Weekly Para Athletics Data Scraper" → Run workflow
- **Required secrets**: `SQL_CONNECTION_STRING`, `AZURE_STORAGE_CONNECTION_STRING`

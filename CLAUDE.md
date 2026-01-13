# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Para Athletics Performance Analysis System for **Team Saudi** (Saudi Arabia Paralympic Program). Analyzes championship data to determine winning standards, tracks athlete performance, and provides competitive intelligence across 87 events and 110 disability classifications.

**Primary Goals**:
1. Identify gold/silver/bronze/finals/semifinals/heats qualifying standards
2. Track Saudi athlete performance and progression
3. Provide competitor intelligence and threat assessment
4. Generate pre-competition championship predictions

## Critical Technical Requirements

### Data Encoding (MUST USE)
```python
# ALWAYS use Latin-1 encoding for CSV files
df = pd.read_csv('data/Tilastoptija/ksaoutputipc3.csv',
                 encoding='latin-1', low_memory=False)

# WRONG - will fail
df = pd.read_csv(file, encoding='utf-8')
```

### Chandra OCR Syntax
```bash
# CORRECT - use --page-range
chandra input.pdf output_dir --method hf --page-range 1-10

# WRONG - --pages does not exist
chandra input.pdf output_dir --pages 1-10
```

### Browser Automation
- Records scraper requires **visible browser** (headless=False fails with dynamic content)
- Playwright preferred over Selenium
- Wait times: 3+ seconds for dynamic content

## Core Commands

### Analysis Scripts (run from Project/)
```bash
# Championship winning standards (gold/bronze/finals/semis/heats)
python championship_winning_standards.py

# Quick Saudi athlete export (3-sheet Excel)
python quick_saudi_export.py

# Gender-separated comprehensive analysis
python comprehensive_event_analysis_v2.py

# Saudi athlete management reports
python saudi_athletics_management_report.py

# Pre-competition predictions
python pre_competition_championship_report.py
```

### Data Collection
```bash
# Run all scrapers
python run_all_scrapers.py

# Individual scrapers
python scrape_rankings.py [year]    # Current year only (incremental)
python scrape_records6.py           # Full replacement (visible browser required)
python scrape_results.py            # Championship PDFs

# Tilastopaja smart updater (checks before downloading)
python tilastopaja_updater.py --check           # Check if updates available
python tilastopaja_updater.py --check-and-update  # Download only if new
python tilastopaja_updater.py --force           # Force download
python tilastopaja_updater.py --stats           # Show local file stats
```

### Cloud Deployment (GitHub Actions + Azure SQL)
```bash
# Automated weekly scraping - runs Sunday 2 AM UTC (6 AM Saudi)
# Manual trigger available in GitHub Actions tab
# Files: .github/workflows/daily_scraper.yml, cloud_scraper.py

# Local cloud mode testing
set AZURE_SQL_CONN="your_connection_string"
python cloud_scraper.py --type rankings --mode cloud
```

### PDF Processing
```bash
# Test Chandra installation
python test_chandra.py

# Process championship PDFs
python build_pdf_database.py

# Manual Chandra usage
chandra "data/PDF/filename.pdf" output_dir --method hf --page-range 1-10
```

### Dashboards (Streamlit)
```bash
# Main Team Saudi intelligence dashboard
streamlit run team_saudi_intelligence_dashboard.py

# Para athletics agent dashboard
streamlit run para_athletics_agent_dashboard.py
```

### Testing
```bash
python test_chandra.py              # Chandra OCR verification
python tests/test_ksa_scraper.py    # KSA scraping validation
python tests/test_ipc_access.py     # IPC connectivity
```

## Data Sources

### Main Dataset
- **Location**: `data/Tilastoptija/ksaoutputipc3.csv` (22 MB)
- **API Source**: `https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv` (auto-updater checks this)
- **Coverage**: 138,772 results (2012-2024), 11,560 athletes, 87 events, 110 classifications
- **Top events**: 100m (24,269), Shot Put (17,533), 200m (16,437)
- **Top classifications**: T54 (15,020), T12 (7,296), T37 (6,561)

### Championship PDFs
- **Location**: `data/PDF/` (17 PDFs, 224 MB)
- Includes: Delhi 2025, Kobe 2024, Paris 2024, Tokyo 2020, Rio 2016
- Processed via Chandra OCR to `data/PDF_extracted/`

### Rankings & Records
- `data/Rankings/` - Annual IPC rankings (2009-2025)
- `data/Records/` - 636+ world/regional records

## Architecture

```
Orchestration Layer (Dashboards)
    ↓
Intelligence Layer (Agents)
├── DataCollectionAgent   (IPC scraping, rankings, records)
├── AnalysisAgent         (championship standards, stats)
├── PredictionAgent       (medal probability, forecasting)
├── SaudiAgent            (Team Saudi analysis)
└── PDFAnalysisAgent      (Chandra OCR integration)
    ↓
Skills Framework (agents/skills.py)
├── DataLoadingSkill      (CSV, rankings, records)
├── GenderSeparationSkill (M/W/Men/Women parsing)
├── PerformanceAnalysisSkill (stats, percentiles)
├── ClassificationSkill   (T/F parsing)
└── VisualizationSkill    (charts, reports)
    ↓
Data Layer (data/Tilastoptija, data/PDF, data/Rankings, data/Records)
```

### Key Classes
- `ChampionshipAnalyzer` - Main analysis engine (championship_winning_standards.py)
- `ComprehensiveEventAnalyzer` - Event analysis (comprehensive_event_analysis_v2.py)
- `SaudiAthleticsReportGenerator` - Saudi reports (saudi_athletics_management_report.py)
- `ChandraPDFExtractor` - PDF processing (chandra_pdf_extractor.py)

## Common Patterns

### Gender Separation (required for Saudi reports)
```python
def separate_gender(event_name):
    if re.search(r"(Men'?s?|^M|_M_)", event_name):
        return 'Male'
    elif re.search(r"(Women'?s?|^W|_W_)", event_name):
        return 'Female'
    return 'Unknown'
```

### Classification Extraction
```python
classification = re.search(r'[TF]\d{2}', event_name)
df['Class'] = df['Event'].str.extract(r'([TF]\d{2})')
```

### Filter Saudi Athletes
```python
saudi = df[df['Nat'] == 'KSA']
```

## File Organization

### Active Scripts (Project root)
- `championship_*.py` - Championship analysis
- `scrape_*.py` - Data collection
- `saudi_*.py` - Saudi-specific analysis
- `*_dashboard.py` - Streamlit dashboards
- `build_*.py` - Database building
- `test_*.py` - Testing/validation

### Agent System (agents/)
- `skills.py` - Shared capabilities framework
- `data_agent.py` - Data collection automation
- `analysis_agent.py` - Performance analysis
- `prediction_agent.py` - Predictive modeling
- `saudi_agent.py` - Team Saudi specific
- `pdf_analysis_agent.py` - Chandra OCR integration

### Legacy Scripts (Old/)
Deprecated versions - use current directory scripts

## Output Locations

- `analysis_reports/` - CSV reports (championship_standards_report.csv)
- `comprehensive_analysis/` - Multi-page event PDFs
- `pre_competition_reports/` - Championship prep PDFs
- `saudi_athletics_reports/` - Saudi-specific PDFs
- `data/PDF_extracted/` - Chandra OCR output

## Team Saudi Branding

```python
COLORS = {
    'primary_green': '#1B8B7D',
    'gold': '#D4AF37',
    'teal': '#007167',
    'secondary_gold': '#9D8E65'
}
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Encoding errors | Use `encoding='latin-1'` not UTF-8 |
| Chandra fails | Use `--page-range` not `--pages` |
| Scraper fails | Set `headless=False` for records |
| Large file slow | Use `low_memory=False` |
| Windows console | Avoid emojis, use [OK]/[ERROR] |

## Development Workflow

1. **Update Data**: `python run_all_scrapers.py`
2. **Process PDFs**: `python build_pdf_database.py` (if new championships)
3. **Run Analysis**: `python championship_winning_standards.py`
4. **Generate Reports**: `python comprehensive_event_analysis_v2.py`
5. **Saudi Export**: `python quick_saudi_export.py`
6. **Launch Dashboard**: `streamlit run team_saudi_intelligence_dashboard.py`

## Cloud Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE THREE-LAYER SANDWICH                      │
├─────────────────────────────────────────────────────────────────┤
│   ┌──────────────────┐                                          │
│   │   GitHub Code    │  ← The Brain (Python scripts)            │
│   │   (Repository)   │                                          │
│   └────────┬─────────┘                                          │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │  GitHub Actions  │  ← The Motor (weekly @ Sunday 2AM UTC)   │
│   │   (Scheduler)    │    Manual trigger available anytime      │
│   └────────┬─────────┘                                          │
│            │                                                     │
│            ▼                                                     │
│   ┌──────────────────┐                                          │
│   │    Azure SQL     │  ← The Memory (stores all data)          │
│   │    Database      │    Free tier: 2GB storage                │
│   └──────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Cloud Files
- `.github/workflows/daily_scraper.yml` - GitHub Actions workflow (weekly)
- `cloud_scraper.py` - Unified scraper (local CSV or Azure SQL modes)
- `tilastopaja_updater.py` - Smart update checker (HEAD request before download)
- `database/azure_schema.sql` - Azure SQL schema (tables, views, stored procedures)
- `DEPLOYMENT_GUIDE.md` - Step-by-step Azure/GitHub setup

### Dashboard Features
- Manual refresh buttons in sidebar (Check Updates / Update Data)
- Athlete classification override system
- Data persisted to `data/classification_overrides.json`

## Documentation

- [START_HERE.md](START_HERE.md) - Main entry point
- [SYSTEM_IMPROVEMENT_PLAN.md](SYSTEM_IMPROVEMENT_PLAN.md) - Master plan (6 phases)
- [CHANDRA_INTEGRATION_GUIDE.md](CHANDRA_INTEGRATION_GUIDE.md) - PDF processing
- [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) - Agent system design
- [QUICKSTART_AGENTS.md](QUICKSTART_AGENTS.md) - Quick agent usage
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Cloud deployment (GitHub Actions + Azure SQL)

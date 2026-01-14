# Streamlit Cloud Deployment Guide
**Para Athletics Dashboard - Azure SQL Backend**

## Quick Start

### Prerequisites
- Azure SQL Database configured (already done ✅)
- GitHub repository with code pushed
- Streamlit Cloud account (free at https://share.streamlit.io/)

### Step 1: Push Code to GitHub

```bash
cd "c:\Users\l.gallagher\OneDrive - Team Saudi\Documents\Performance Analysis\Para Athletics\Project"
git add azure_db.py azure_dashboard.py .streamlit/secrets.toml.example .gitignore
git commit -m "Add unified Azure SQL connection layer for Streamlit deployment"
git push origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with GitHub
3. Click **"New app"**
4. Select:
   - **Repository**: `LukeJGallagher/Athleticsipc_Tilastoptja`
   - **Branch**: `main`
   - **Main file path**: `azure_dashboard.py`
5. Click **"Advanced settings"**

### Step 3: Configure Secrets

In the **Secrets** section, add:

```toml
AZURE_SQL_CONN = "Driver={ODBC Driver 17 for SQL Server};Server=tcp:REDACTED_SERVER,1433;Database=REDACTED_DB;Uid=REDACTED_USER;Pwd=REDACTED_PASSWORD;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
```

⚠️ **Important**: Use `Driver 17` for Streamlit Cloud (not `Driver 18` or `SQL Server`)

6. Click **"Save"**
7. Click **"Deploy"**

### Step 4: Wait for Deployment

Deployment takes 2-3 minutes. Monitor the logs for:
- ✅ Dependencies installing
- ✅ `pyodbc` installation success
- ✅ App starting

## Verification

Once deployed:

1. **Check connection mode**: Sidebar should show "📊 Database: AZURE"
2. **Verify data loads**: Results tab should display data from Azure SQL
3. **Test filters**: Try filtering by nationality (KSA)
4. **Check refresh**: Click "🔄 Refresh Data" button

## Common Issues

### Issue: "Can't open lib 'ODBC Driver 18 for SQL Server'"
**Solution**: Update connection string to use `Driver={ODBC Driver 17 for SQL Server}`

### Issue: "Login timeout expired"
**Solution**:
1. Azure SQL database may be paused (serverless auto-pause)
2. Check Azure Portal → Your Database → Status
3. Click "Resume" if paused
4. Wait 30-60 seconds and retry

### Issue: "No data displayed"
**Solution**:
1. Check Azure SQL has data: Run `/check` in Azure Portal Query Editor
2. Run migration script locally: `python migrate_to_azure.py`
3. Verify with: `SELECT COUNT(*) FROM Results`

### Issue: Module not found
**Solution**: Verify all files are committed to GitHub:
- `azure_db.py` ✅
- `azure_dashboard.py` ✅
- `.streamlit/secrets.toml.example` ✅
- `requirements.txt` ✅

## Architecture

```
Local Development          Streamlit Cloud
─────────────────          ───────────────
.env file          →       Streamlit Secrets
AZURE_SQL_CONN             AZURE_SQL_CONN

Driver={SQL Server}  →     Driver={ODBC Driver 17 for SQL Server}

azure_db.py (auto-detects environment)
    ↓
Azure SQL Database
REDACTED_DB
```

## Files Reference

| File | Purpose |
|------|---------|
| `azure_db.py` | Unified database connection module |
| `azure_dashboard.py` | Streamlit dashboard app |
| `.streamlit/secrets.toml.example` | Secrets template (reference) |
| `.env` | Local development secrets (NOT in git) |
| `migrate_to_azure.py` | One-time data migration script |
| `requirements.txt` | Python dependencies |

## Local Testing

Before deploying to Streamlit Cloud, test locally:

```bash
# Test Azure connection
python -c "from azure_db import test_connection; print(test_connection())"

# Expected output:
# {'mode': 'azure', 'connection_test': 'success', 'row_count': 2000}

# Run dashboard locally
streamlit run azure_dashboard.py
```

Visit http://localhost:8501 and verify:
- Connection mode shows "AZURE"
- Data loads successfully
- All tabs work (Results, Rankings, Records, Saudi Arabia)

## Production Checklist

Before going live:

- [ ] All code committed to GitHub
- [ ] `azure_db.py` uses lazy-loading for secrets
- [ ] No hardcoded credentials in code
- [ ] `.env` file excluded from git
- [ ] Azure SQL firewall allows Streamlit Cloud (0.0.0.0-255.255.255.255)
- [ ] Database populated with data (run `migrate_to_azure.py`)
- [ ] Local testing passed
- [ ] Streamlit Cloud secrets configured
- [ ] Deployment successful

## Cost Monitoring

- **Azure SQL Free Tier**: 32GB storage, 100k vCore seconds/month
- **Serverless auto-pause**: Saves costs, but adds 30-second delay on first access
- **Monitor usage**: Azure Portal → Cost Management

## Support

- **Streamlit Community**: https://discuss.streamlit.io/
- **Azure SQL Docs**: https://learn.microsoft.com/azure/azure-sql/
- **Repository Issues**: https://github.com/LukeJGallagher/Athleticsipc_Tilastoptja/issues

## Security Notes

⚠️ **Critical**:
- Never commit `.env` file
- Never commit `.streamlit/secrets.toml`
- Rotate passwords if accidentally exposed
- Use Azure AD authentication for production (future enhancement)

---

**Last Updated**: 2026-01-14
**Version**: 1.0

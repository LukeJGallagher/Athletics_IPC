"""
Cloud-Ready Para Athletics Scraper
Designed for GitHub Actions deployment with Azure SQL database

Usage:
    Local:  python cloud_scraper.py --type rankings --mode local
    Cloud:  python cloud_scraper.py --type rankings  (uses env vars)

Environment Variables (for cloud):
    AZURE_SQL_CONN: Azure SQL connection string
    SCRAPER_MODE: 'cloud' or 'local'
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd

# Set up logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Handle both local CSV and Azure SQL storage"""

    def __init__(self, mode='local'):
        self.mode = mode
        self.connection = None

        if mode == 'cloud':
            self._connect_azure()
        else:
            logger.info("Running in local mode - will save to CSV files")

    def _connect_azure(self):
        """Connect to Azure SQL Database"""
        import pyodbc

        conn_string = os.getenv('AZURE_SQL_CONN')
        if not conn_string:
            raise ValueError("AZURE_SQL_CONN environment variable not set")

        try:
            self.connection = pyodbc.connect(conn_string)
            logger.info("Connected to Azure SQL Database")
        except Exception as e:
            logger.error(f"Failed to connect to Azure SQL: {e}")
            raise

    def save_rankings(self, df: pd.DataFrame, year: int):
        """Save rankings data"""
        if self.mode == 'cloud':
            self._save_to_azure(df, 'rankings', year)
        else:
            self._save_to_csv(df, f'data/Rankings/rankings_{year}.csv')

    def save_records(self, df: pd.DataFrame, record_type: str):
        """Save records data"""
        if self.mode == 'cloud':
            self._save_to_azure(df, 'records', record_type)
        else:
            safe_type = record_type.replace(' ', '_')
            self._save_to_csv(df, f'data/Records/records_{safe_type}_{datetime.now().strftime("%Y%m%d")}.csv')

    def save_results(self, df: pd.DataFrame, competition: str):
        """Save competition results"""
        if self.mode == 'cloud':
            self._save_to_azure(df, 'results', competition)
        else:
            safe_comp = competition.replace(' ', '_')[:50]
            self._save_to_csv(df, f'data/Results/results_{safe_comp}.csv')

    def _save_to_csv(self, df: pd.DataFrame, filepath: str):
        """Save DataFrame to local CSV"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False, encoding='latin-1')
        logger.info(f"Saved {len(df)} rows to {filepath}")

    def _save_to_azure(self, df: pd.DataFrame, table_type: str, identifier: str):
        """Save DataFrame to Azure SQL"""
        if not self.connection:
            raise ValueError("No Azure connection available")

        cursor = self.connection.cursor()

        try:
            if table_type == 'rankings':
                self._insert_rankings(cursor, df, identifier)
            elif table_type == 'records':
                self._insert_records(cursor, df, identifier)
            elif table_type == 'results':
                self._insert_results(cursor, df, identifier)

            self.connection.commit()
            logger.info(f"Saved {len(df)} rows to Azure SQL ({table_type})")
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Failed to save to Azure SQL: {e}")
            raise

    def _insert_rankings(self, cursor, df: pd.DataFrame, year: int):
        """Insert rankings data into Azure SQL"""
        # Clear existing data for this year
        cursor.execute("DELETE FROM Rankings WHERE year = ?", (year,))

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO Rankings (year, rank, athlete_name, nationality, event_name,
                                      classification, performance, competition, date, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                year,
                row.get('Rank'),
                row.get('Athlete', row.get('athlete_name')),
                row.get('Country', row.get('nationality')),
                row.get('Event', row.get('event_name')),
                row.get('Class', row.get('classification')),
                row.get('Performance', row.get('performance')),
                row.get('Competition', row.get('competition')),
                row.get('Date', row.get('date'))
            ))

    def _insert_records(self, cursor, df: pd.DataFrame, record_type: str):
        """Insert records data into Azure SQL"""
        # Clear existing records of this type
        cursor.execute("DELETE FROM Records WHERE record_type = ?", (record_type,))

        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO Records (record_type, event_name, performance, athlete_name,
                                     nationality, location, date, competition, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                record_type,
                row.get('event_name'),
                row.get('performance'),
                row.get('athlete_name'),
                row.get('country_code', row.get('nationality')),
                row.get('location'),
                row.get('date'),
                row.get('competition')
            ))

    def _insert_results(self, cursor, df: pd.DataFrame, competition: str):
        """Insert competition results into Azure SQL"""
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT INTO Results (competition_name, event_name, athlete_name, nationality,
                                     classification, performance, position, round, date, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
            """, (
                competition,
                row.get('Event', row.get('eventname')),
                row.get('Athlete', row.get('athlete_name')),
                row.get('Nat', row.get('nationality')),
                row.get('Class', row.get('classification')),
                row.get('Performance', row.get('performance')),
                row.get('Pos', row.get('position')),
                row.get('Round', row.get('round')),
                row.get('Date', row.get('date'))
            ))

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            logger.info("Closed Azure SQL connection")


class RankingsScraper:
    """Scrape IPC rankings data"""

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.base_url = "https://www.paralympic.org/sdms/hira/web/rankings"

    def scrape_year(self, year: int):
        """Scrape rankings for a specific year"""
        from playwright.sync_api import sync_playwright

        logger.info(f"Scraping rankings for {year}")
        all_rankings = []

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to rankings page
                url = f"{self.base_url}?year={year}"
                page.goto(url, timeout=60000)
                page.wait_for_load_state('networkidle')

                # Look for XML/CSV download button
                try:
                    # Try to find export button
                    export_btn = page.locator('button:has-text("Export"), a:has-text("Download")')
                    if export_btn.count() > 0:
                        export_btn.first.click()
                        page.wait_for_timeout(3000)
                except:
                    logger.warning("No export button found, will scrape HTML")

                # Scrape table data
                tables = page.locator('table').all()
                for table in tables:
                    rows = table.locator('tr').all()
                    for row in rows[1:]:  # Skip header
                        cells = row.locator('td').all()
                        if len(cells) >= 5:
                            all_rankings.append({
                                'Rank': cells[0].inner_text().strip() if len(cells) > 0 else '',
                                'Athlete': cells[1].inner_text().strip() if len(cells) > 1 else '',
                                'Country': cells[2].inner_text().strip() if len(cells) > 2 else '',
                                'Performance': cells[3].inner_text().strip() if len(cells) > 3 else '',
                                'Competition': cells[4].inner_text().strip() if len(cells) > 4 else '',
                            })

                browser.close()

        except Exception as e:
            logger.error(f"Error scraping rankings for {year}: {e}")
            raise

        if all_rankings:
            df = pd.DataFrame(all_rankings)
            self.db.save_rankings(df, year)
            return df
        else:
            logger.warning(f"No rankings found for {year}")
            return pd.DataFrame()


class RecordsScraper:
    """Scrape IPC world records"""

    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.base_url = "https://www.paralympic.org/sdms/hira/web/records"

    def scrape_records(self, record_type: str = 'World Record'):
        """Scrape records by type"""
        from playwright.sync_api import sync_playwright

        logger.info(f"Scraping {record_type}")
        all_records = []

        try:
            with sync_playwright() as p:
                # Use visible browser for records (required per CLAUDE.md)
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()

                # Navigate to records page
                page.goto(self.base_url, timeout=60000)
                page.wait_for_load_state('networkidle')
                page.wait_for_timeout(3000)

                # Select record type
                try:
                    dropdown = page.locator('select[name="recordType"], #recordType')
                    if dropdown.count() > 0:
                        dropdown.select_option(label=record_type)
                        page.wait_for_timeout(3000)
                except:
                    logger.warning(f"Could not select record type: {record_type}")

                # Look for XML export
                try:
                    xml_btn = page.locator('button:has-text("XML"), a:has-text("XML")')
                    if xml_btn.count() > 0:
                        xml_btn.first.click()
                        page.wait_for_timeout(5000)
                except:
                    pass

                # Scrape visible table
                tables = page.locator('table').all()
                for table in tables:
                    rows = table.locator('tr').all()
                    for row in rows[1:]:
                        cells = row.locator('td').all()
                        if len(cells) >= 4:
                            all_records.append({
                                'event_name': cells[0].inner_text().strip() if len(cells) > 0 else '',
                                'performance': cells[1].inner_text().strip() if len(cells) > 1 else '',
                                'athlete_name': cells[2].inner_text().strip() if len(cells) > 2 else '',
                                'country_code': cells[3].inner_text().strip() if len(cells) > 3 else '',
                                'date': cells[4].inner_text().strip() if len(cells) > 4 else '',
                                'competition': cells[5].inner_text().strip() if len(cells) > 5 else '',
                                'record_type': record_type
                            })

                browser.close()

        except Exception as e:
            logger.error(f"Error scraping {record_type}: {e}")
            raise

        if all_records:
            df = pd.DataFrame(all_records)
            self.db.save_records(df, record_type)
            return df
        else:
            logger.warning(f"No records found for {record_type}")
            return pd.DataFrame()


def main():
    parser = argparse.ArgumentParser(description='Para Athletics Cloud Scraper')
    parser.add_argument('--type', choices=['rankings', 'records', 'all'], default='all',
                        help='Type of data to scrape')
    parser.add_argument('--mode', choices=['local', 'cloud'], default=None,
                        help='Storage mode (default: from SCRAPER_MODE env var or local)')
    parser.add_argument('--year', type=int, default=datetime.now().year,
                        help='Year for rankings (default: current year)')

    args = parser.parse_args()

    # Determine mode
    mode = args.mode or os.getenv('SCRAPER_MODE', 'local')
    logger.info(f"Starting scraper in {mode} mode")

    # Initialize database connection
    db = DatabaseConnection(mode=mode)

    try:
        if args.type in ['rankings', 'all']:
            logger.info("=" * 50)
            logger.info("SCRAPING RANKINGS")
            logger.info("=" * 50)
            scraper = RankingsScraper(db)
            scraper.scrape_year(args.year)

        if args.type in ['records', 'all']:
            logger.info("=" * 50)
            logger.info("SCRAPING RECORDS")
            logger.info("=" * 50)
            scraper = RecordsScraper(db)

            record_types = [
                'World Record',
                'Paralympic Record',
                'Championship Record',
                'Asian Record'
            ]

            for record_type in record_types:
                try:
                    scraper.scrape_records(record_type)
                except Exception as e:
                    logger.error(f"Failed to scrape {record_type}: {e}")
                    continue

        logger.info("Scraping completed successfully!")

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)

    finally:
        db.close()


if __name__ == '__main__':
    main()

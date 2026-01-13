"""
Tilastopaja Database Smart Updater
Merges and appends new records from API to local database (does NOT replace)

Usage:
    python tilastopaja_updater.py --check          # Just check if update available
    python tilastopaja_updater.py --check-and-update  # Check and merge if new
    python tilastopaja_updater.py --force          # Force merge regardless
    python tilastopaja_updater.py --stats          # Show local file statistics
    python tilastopaja_updater.py --compare        # Compare local vs remote

The API endpoint provides RECENT competition results (not full history):
    https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv

Local database contains historical data (2012-present).
This updater MERGES new records using resultid as unique key.
"""

import os
import sys
import argparse
import logging
import json
import requests
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
        logging.FileHandler(log_dir / f'tilastopaja_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
TILASTOPAJA_URL = "https://www.tilastopaja.com/json/ksa/ksaoutputipc.csv"
LOCAL_DATA_PATH = Path("data/Tilastoptija/ksaoutputipc3.csv")
METADATA_PATH = Path("data/tilastopaja_metadata.json")


def load_metadata():
    """Load previous download metadata"""
    if METADATA_PATH.exists():
        try:
            with open(METADATA_PATH, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_metadata(metadata):
    """Save download metadata"""
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)


def check_for_updates():
    """
    Check if the remote file has been updated without downloading it.
    Uses HTTP HEAD request to check Last-Modified and Content-Length headers.
    """
    result = {
        'has_update': False,
        'remote_modified': None,
        'remote_size': None,
        'local_modified': None,
        'local_size': None,
        'check_time': datetime.now().isoformat()
    }

    # Get remote file info via HEAD request (no download)
    try:
        logger.info(f"Checking for updates at: {TILASTOPAJA_URL}")
        response = requests.head(TILASTOPAJA_URL, timeout=30, allow_redirects=True)
        response.raise_for_status()

        result['remote_modified'] = response.headers.get('Last-Modified')
        result['remote_size'] = int(response.headers.get('Content-Length', 0))

        logger.info(f"Remote - Last-Modified: {result['remote_modified']}, Size: {result['remote_size']:,} bytes")

    except requests.RequestException as e:
        logger.error(f"Failed to check remote file: {e}")
        return result

    # Get local file info
    metadata = load_metadata()
    if LOCAL_DATA_PATH.exists():
        stat = LOCAL_DATA_PATH.stat()
        result['local_size'] = stat.st_size
        result['local_modified'] = metadata.get('last_merge')
        logger.info(f"Local - Last merge: {result['local_modified']}, Size: {result['local_size']:,} bytes")
    else:
        logger.info("No local file exists - update needed")
        result['has_update'] = True
        return result

    # Compare to determine if update needed
    if result['remote_modified']:
        stored_remote_modified = metadata.get('remote_last_modified')
        if stored_remote_modified != result['remote_modified']:
            logger.info(f"Last-Modified changed: {stored_remote_modified} -> {result['remote_modified']}")
            result['has_update'] = True
            return result

    logger.info("No update detected - file is current")
    return result


def download_remote_data():
    """Download remote data and return as DataFrame"""
    logger.info(f"Downloading from: {TILASTOPAJA_URL}")

    try:
        # Remote uses semicolon separator
        remote_df = pd.read_csv(TILASTOPAJA_URL, encoding='latin-1', sep=';', low_memory=False)
        logger.info(f"Downloaded {len(remote_df):,} rows from remote API")
        return remote_df
    except Exception as e:
        logger.error(f"Failed to download remote data: {e}")
        return None


def load_local_data():
    """Load local database"""
    if not LOCAL_DATA_PATH.exists():
        logger.warning("Local file does not exist")
        return None

    try:
        # Local uses comma separator
        local_df = pd.read_csv(LOCAL_DATA_PATH, encoding='latin-1', low_memory=False)
        logger.info(f"Loaded {len(local_df):,} rows from local database")
        return local_df
    except Exception as e:
        logger.error(f"Failed to load local data: {e}")
        return None


def merge_databases(local_df, remote_df):
    """
    Merge remote data into local database.
    Uses 'resultid' as unique key to avoid duplicates.

    Returns:
        tuple: (merged_df, stats_dict)
    """
    stats = {
        'local_rows_before': len(local_df) if local_df is not None else 0,
        'remote_rows': len(remote_df),
        'new_rows_added': 0,
        'updated_rows': 0,
        'local_rows_after': 0
    }

    # If no local data, just use remote
    if local_df is None or len(local_df) == 0:
        logger.info("No local data - using remote data as base")
        stats['new_rows_added'] = len(remote_df)
        stats['local_rows_after'] = len(remote_df)
        return remote_df, stats

    # Check for resultid column
    if 'resultid' not in local_df.columns:
        logger.warning("No 'resultid' column in local data - cannot merge safely")
        return local_df, stats

    if 'resultid' not in remote_df.columns:
        logger.warning("No 'resultid' column in remote data - cannot merge safely")
        return local_df, stats

    # Find new records (in remote but not in local)
    local_ids = set(local_df['resultid'].dropna().astype(str))
    remote_ids = set(remote_df['resultid'].dropna().astype(str))

    new_ids = remote_ids - local_ids
    logger.info(f"Found {len(new_ids):,} new records to add")

    if len(new_ids) == 0:
        logger.info("No new records to add")
        stats['local_rows_after'] = len(local_df)
        return local_df, stats

    # Filter remote to only new records
    remote_df['resultid_str'] = remote_df['resultid'].astype(str)
    new_records = remote_df[remote_df['resultid_str'].isin(new_ids)].copy()
    new_records = new_records.drop(columns=['resultid_str'])

    logger.info(f"Adding {len(new_records):,} new records to database")

    # Append new records to local
    merged_df = pd.concat([local_df, new_records], ignore_index=True)

    # Sort by date (most recent first)
    if 'competitiondate' in merged_df.columns:
        try:
            merged_df['_sort_date'] = pd.to_datetime(merged_df['competitiondate'], format='%d/%m/%Y', errors='coerce')
            merged_df = merged_df.sort_values('_sort_date', ascending=False)
            merged_df = merged_df.drop(columns=['_sort_date'])
        except:
            pass

    stats['new_rows_added'] = len(new_records)
    stats['local_rows_after'] = len(merged_df)

    return merged_df, stats


def save_merged_data(merged_df):
    """Save merged database to local file"""
    # Create backup first
    if LOCAL_DATA_PATH.exists():
        backup_path = LOCAL_DATA_PATH.with_suffix(f'.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        logger.info(f"Creating backup: {backup_path}")
        import shutil
        shutil.copy(LOCAL_DATA_PATH, backup_path)

        # Keep only last 3 backups
        backups = sorted(LOCAL_DATA_PATH.parent.glob('*.backup_*.csv'), reverse=True)
        for old_backup in backups[3:]:
            old_backup.unlink()
            logger.info(f"Removed old backup: {old_backup}")

    # Save merged data
    LOCAL_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged_df.to_csv(LOCAL_DATA_PATH, index=False, encoding='latin-1')
    logger.info(f"Saved merged database: {len(merged_df):,} rows to {LOCAL_DATA_PATH}")

    return True


def merge_and_update():
    """
    Main merge operation: download remote, merge with local, save.

    Returns:
        dict: Merge statistics
    """
    # Download remote data
    remote_df = download_remote_data()
    if remote_df is None:
        return None

    # Load local data
    local_df = load_local_data()

    # Merge databases
    merged_df, stats = merge_databases(local_df, remote_df)

    # Save if there are new records
    if stats['new_rows_added'] > 0:
        if save_merged_data(merged_df):
            # Update metadata
            metadata = load_metadata()
            metadata.update({
                'last_merge': datetime.now().isoformat(),
                'remote_last_modified': requests.head(TILASTOPAJA_URL).headers.get('Last-Modified'),
                'rows_added': stats['new_rows_added'],
                'total_rows': stats['local_rows_after']
            })
            save_metadata(metadata)

            logger.info(f"Merge complete! Added {stats['new_rows_added']:,} new records")
        else:
            logger.error("Failed to save merged data")
            return None
    else:
        logger.info("No new records to add - database is up to date")
        # Update metadata to record check
        metadata = load_metadata()
        metadata['last_check'] = datetime.now().isoformat()
        save_metadata(metadata)

    return stats


def compare_databases():
    """Compare local and remote databases and print summary"""
    print("\n" + "=" * 60)
    print("DATABASE COMPARISON")
    print("=" * 60)

    # Load local
    local_df = load_local_data()
    if local_df is not None:
        local_df['full_name'] = local_df['firstname'].fillna('') + ' ' + local_df['lastname'].fillna('')
        print(f"\nLOCAL DATABASE ({LOCAL_DATA_PATH.name})")
        print(f"  Rows: {len(local_df):,}")
        print(f"  Unique Athletes: {local_df['full_name'].nunique():,}")
        if 'competitiondate' in local_df.columns:
            print(f"  Date Range: {local_df['competitiondate'].min()} to {local_df['competitiondate'].max()}")
        if 'nationality' in local_df.columns:
            ksa_count = len(local_df[local_df['nationality'] == 'KSA'])
            print(f"  KSA Results: {ksa_count:,}")

    # Download remote
    remote_df = download_remote_data()
    if remote_df is not None:
        remote_df['full_name'] = remote_df['firstname'].fillna('') + ' ' + remote_df['lastname'].fillna('')
        print(f"\nREMOTE API (Tilastopaja)")
        print(f"  Rows: {len(remote_df):,}")
        print(f"  Unique Athletes: {remote_df['full_name'].nunique():,}")
        if 'competitiondate' in remote_df.columns:
            print(f"  Date Range: {remote_df['competitiondate'].min()} to {remote_df['competitiondate'].max()}")
        if 'nationality' in remote_df.columns:
            ksa_count = len(remote_df[remote_df['nationality'] == 'KSA'])
            print(f"  KSA Results: {ksa_count:,}")

    # Compare
    if local_df is not None and remote_df is not None:
        print(f"\nCOMPARISON")

        if 'resultid' in local_df.columns and 'resultid' in remote_df.columns:
            local_ids = set(local_df['resultid'].dropna().astype(str))
            remote_ids = set(remote_df['resultid'].dropna().astype(str))

            new_in_remote = len(remote_ids - local_ids)
            only_in_local = len(local_ids - remote_ids)
            in_both = len(local_ids & remote_ids)

            print(f"  New records in Remote (to add): {new_in_remote:,}")
            print(f"  Records only in Local: {only_in_local:,}")
            print(f"  Records in Both: {in_both:,}")

        local_athletes = set(local_df['full_name'].dropna().unique())
        remote_athletes = set(remote_df['full_name'].dropna().unique())
        print(f"  New Athletes in Remote: {len(remote_athletes - local_athletes):,}")


def get_file_stats():
    """Get statistics about the local file"""
    if not LOCAL_DATA_PATH.exists():
        return None

    try:
        df = pd.read_csv(LOCAL_DATA_PATH, encoding='latin-1', low_memory=False)
        df['full_name'] = df['firstname'].fillna('') + ' ' + df['lastname'].fillna('')

        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'unique_athletes': df['full_name'].nunique(),
            'unique_events': df['eventname'].nunique() if 'eventname' in df.columns else None,
            'date_range': None
        }

        if 'competitiondate' in df.columns:
            stats['date_range'] = {
                'min': df['competitiondate'].min(),
                'max': df['competitiondate'].max()
            }

        if 'nationality' in df.columns:
            stats['ksa_results'] = len(df[df['nationality'] == 'KSA'])

        return stats
    except Exception as e:
        logger.error(f"Failed to read file stats: {e}")
        return None


def upload_to_azure(df=None):
    """Upload data to Azure SQL if in cloud mode"""
    mode = os.getenv('SCRAPER_MODE', 'local')
    if mode != 'cloud':
        logger.info("Not in cloud mode - skipping Azure upload")
        return

    conn_string = os.getenv('AZURE_SQL_CONN')
    if not conn_string:
        logger.error("AZURE_SQL_CONN not set")
        return

    try:
        import pyodbc

        if df is None:
            df = pd.read_csv(LOCAL_DATA_PATH, encoding='latin-1', low_memory=False)

        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()

        logger.info(f"Uploading {len(df)} rows to Azure SQL...")

        # Clear existing Tilastopaja data
        cursor.execute("DELETE FROM Results WHERE competition_name LIKE 'Tilastopaja%'")

        # Insert data in batches
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            for _, row in batch.iterrows():
                cursor.execute("""
                    INSERT INTO Results (competition_name, event_name, athlete_name, nationality,
                                         performance, position, date, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    row.get('competitionname', 'Tilastopaja Import'),
                    row.get('eventname'),
                    f"{row.get('firstname', '')} {row.get('lastname', '')}".strip(),
                    row.get('nationality'),
                    row.get('performance'),
                    row.get('position'),
                    row.get('competitiondate')
                ))

            if (i + batch_size) % 10000 == 0:
                logger.info(f"Uploaded {min(i + batch_size, len(df)):,} / {len(df):,} rows")

        conn.commit()
        conn.close()
        logger.info("Azure SQL upload complete")

    except Exception as e:
        logger.error(f"Azure SQL upload failed: {e}")


def main():
    parser = argparse.ArgumentParser(description='Tilastopaja Database Smart Updater (Merge Mode)')
    parser.add_argument('--check', action='store_true', help='Only check for updates')
    parser.add_argument('--check-and-update', action='store_true', help='Check and merge new records')
    parser.add_argument('--force', action='store_true', help='Force merge regardless of changes')
    parser.add_argument('--stats', action='store_true', help='Show local file statistics')
    parser.add_argument('--compare', action='store_true', help='Compare local vs remote databases')

    args = parser.parse_args()

    if args.stats:
        stats = get_file_stats()
        if stats:
            print("\n=== Tilastopaja Database Statistics ===")
            print(f"Total rows: {stats['total_rows']:,}")
            print(f"Unique athletes: {stats['unique_athletes']:,}")
            if stats['unique_events']:
                print(f"Unique events: {stats['unique_events']}")
            if stats['date_range']:
                print(f"Date range: {stats['date_range']['min']} to {stats['date_range']['max']}")
            if 'ksa_results' in stats:
                print(f"KSA results: {stats['ksa_results']:,}")
        return

    if args.compare:
        compare_databases()
        return

    if args.check:
        result = check_for_updates()
        print("\n=== Update Check Results ===")
        print(f"Update available: {'Yes' if result['has_update'] else 'No'}")
        print(f"Remote size: {result['remote_size']:,} bytes" if result['remote_size'] else "Remote size: Unknown")
        print(f"Local size: {result['local_size']:,} bytes" if result['local_size'] else "Local size: N/A")
        return

    if args.check_and_update:
        result = check_for_updates()
        if result['has_update']:
            logger.info("Update detected - merging new records...")
            stats = merge_and_update()
            if stats:
                upload_to_azure()
                logger.info(f"Merge complete! Added {stats['new_rows_added']:,} new records")
            else:
                logger.error("Merge failed!")
                sys.exit(1)
        else:
            logger.info("No update needed - data is current")
        return

    if args.force:
        logger.info("Force merge requested...")
        stats = merge_and_update()
        if stats:
            upload_to_azure()
            logger.info(f"Force merge complete! Added {stats['new_rows_added']:,} new records")
        else:
            logger.error("Force merge failed!")
            sys.exit(1)
        return

    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()

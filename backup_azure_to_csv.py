"""
Backup Azure SQL Database to Local CSV Files
============================================

Exports all tables from Azure SQL to timestamped CSV backup directory.
Run this before major data changes or on a weekly schedule.

Free tier users: This is your primary backup method since .bacpac exports
require Azure Storage (paid).

Usage:
    python backup_azure_to_csv.py
"""
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
from azure_db import get_azure_connection, get_connection_mode

def backup_azure_database():
    """Export all Azure SQL tables to CSV files"""

    # Check we're connected to Azure
    mode = get_connection_mode()
    if mode != 'azure':
        print(f"[ERROR] Not connected to Azure SQL (mode: {mode})")
        print("Please configure AZURE_SQL_CONN in .env file")
        return False

    # Create timestamped backup directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(f"backups/azure/{timestamp}")
    backup_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("AZURE SQL DATABASE BACKUP")
    print(f"Backup location: {backup_dir}")
    print("="*60)

    tables = ['Results', 'Rankings', 'Records', 'Athletes', 'ScrapeLog']
    total_rows = 0
    success_count = 0

    with get_azure_connection() as conn:
        for table in tables:
            try:
                print(f"\nExporting {table}...")

                # Get row count first
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]

                if row_count == 0:
                    print(f"  [SKIP] {table} is empty")
                    continue

                # Export to DataFrame
                df = pd.read_sql(f"SELECT * FROM {table}", conn)

                # Save to CSV
                csv_path = backup_dir / f"{table}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8')

                print(f"  [OK] {len(df):,} rows exported")
                total_rows += len(df)
                success_count += 1

            except Exception as e:
                print(f"  [ERROR] {table}: {str(e)[:100]}")

    # Create backup metadata file
    metadata_path = backup_dir / "backup_metadata.txt"
    with open(metadata_path, 'w') as f:
        f.write(f"Backup Timestamp: {timestamp}\n")
        f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Connection Mode: {mode}\n")
        f.write(f"Tables Backed Up: {success_count}/{len(tables)}\n")
        f.write(f"Total Rows: {total_rows:,}\n")
        f.write(f"\nTable Details:\n")
        for table in tables:
            csv_file = backup_dir / f"{table}.csv"
            if csv_file.exists():
                f.write(f"  {table}: {csv_file.stat().st_size / 1024 / 1024:.2f} MB\n")

    print("\n" + "="*60)
    print(f"[SUCCESS] Backup complete!")
    print(f"Location: {backup_dir}")
    print(f"Tables: {success_count}/{len(tables)}")
    print(f"Total rows: {total_rows:,}")
    print("="*60)

    # Calculate backup size
    total_size = sum(f.stat().st_size for f in backup_dir.glob("*.csv"))
    print(f"Backup size: {total_size / 1024 / 1024:.2f} MB")

    return True


def list_backups():
    """List all available backups"""
    backups_dir = Path("backups/azure")
    if not backups_dir.exists():
        print("No backups found")
        return

    backups = sorted(backups_dir.iterdir(), reverse=True)
    print("\n" + "="*60)
    print("AVAILABLE BACKUPS")
    print("="*60)

    for backup in backups[:10]:  # Show last 10
        if backup.is_dir():
            metadata_file = backup / "backup_metadata.txt"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    first_line = f.readline().strip()
                    print(f"  {backup.name}: {first_line}")
            else:
                print(f"  {backup.name}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        list_backups()
    else:
        backup_azure_database()

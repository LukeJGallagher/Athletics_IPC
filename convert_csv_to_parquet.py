"""
Convert CSV Data to Parquet and Upload to Azure Blob Storage
=============================================================
Converts all Para Athletics CSV data to Parquet format for faster queries.
Uploads to Azure Blob Storage for cloud dashboard deployment.

Usage:
    python convert_csv_to_parquet.py           # Convert and upload all
    python convert_csv_to_parquet.py --local   # Convert only, no upload
    python convert_csv_to_parquet.py --upload  # Upload existing Parquet files
"""

import os
import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from azure_blob_storage import upload_parquet, CACHE_DIR, test_connection


def convert_main_results() -> pd.DataFrame:
    """Convert main results CSV to Parquet."""
    print("\n" + "=" * 60)
    print("Converting Main Results (ksaoutputipc3.csv)")
    print("=" * 60)

    csv_path = Path("data/Tilastoptija/ksaoutputipc3.csv")

    if not csv_path.exists():
        print(f"Warning: {csv_path} not found")
        return None

    # Load with Latin-1 encoding (critical!)
    df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
    print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

    # Data cleaning
    if 'resultid' in df.columns:
        df['resultid'] = df['resultid'].astype(str)

    # Standardize column names
    df.columns = df.columns.str.lower().str.strip()

    # Save locally
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = CACHE_DIR / "results.parquet"
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"Saved to {parquet_path}")
    print(f"  File size: {parquet_path.stat().st_size / 1024 / 1024:.2f} MB")

    return df


def convert_rankings() -> pd.DataFrame:
    """Convert all rankings CSV files to single Parquet."""
    print("\n" + "=" * 60)
    print("Converting Rankings Data")
    print("=" * 60)

    rankings_dir = Path("data/Rankings")
    if not rankings_dir.exists():
        print(f"Warning: {rankings_dir} not found")
        return None

    all_rankings = []
    csv_files = list(rankings_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} ranking files")

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # Extract year and event from filename
            # Format: rankings_2024_100m_T54.csv
            parts = csv_file.stem.split('_')
            if len(parts) >= 2:
                df['year'] = parts[1] if parts[1].isdigit() else None
            all_rankings.append(df)
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {e}")

    if not all_rankings:
        return None

    df = pd.concat(all_rankings, ignore_index=True)
    df.columns = df.columns.str.lower().str.strip()

    # Remove duplicate columns (keep first occurrence)
    df = df.loc[:, ~df.columns.duplicated()]
    print(f"Combined {len(df):,} ranking records, {len(df.columns)} columns")

    # Save locally
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = CACHE_DIR / "rankings.parquet"
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"Saved to {parquet_path}")
    print(f"  File size: {parquet_path.stat().st_size / 1024 / 1024:.2f} MB")

    return df


def convert_records() -> pd.DataFrame:
    """Convert all records CSV files to single Parquet."""
    print("\n" + "=" * 60)
    print("Converting Records Data")
    print("=" * 60)

    records_dir = Path("data/Records")
    if not records_dir.exists():
        print(f"Warning: {records_dir} not found")
        return None

    all_records = []
    csv_files = list(records_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} record files")

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            # Extract record type from filename
            # Format: world_records.csv, asian_records.csv
            df['record_source'] = csv_file.stem
            all_records.append(df)
        except Exception as e:
            print(f"  Error loading {csv_file.name}: {e}")

    if not all_records:
        return None

    df = pd.concat(all_records, ignore_index=True)
    df.columns = df.columns.str.lower().str.strip()
    print(f"Combined {len(df):,} record entries")

    # Save locally
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = CACHE_DIR / "records.parquet"
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"Saved to {parquet_path}")
    print(f"  File size: {parquet_path.stat().st_size / 1024 / 1024:.2f} MB")

    return df


def convert_championship_standards() -> pd.DataFrame:
    """Convert championship standards report to Parquet."""
    print("\n" + "=" * 60)
    print("Converting Championship Standards")
    print("=" * 60)

    csv_path = Path("championship_standards_report.csv")
    if not csv_path.exists():
        csv_path = Path("output/championship_standards_report.csv")

    if not csv_path.exists():
        print(f"Warning: championship_standards_report.csv not found")
        return None

    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.lower().str.strip()
    print(f"Loaded {len(df):,} championship standards")

    # Save locally
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = CACHE_DIR / "championship_standards.parquet"
    df.to_parquet(parquet_path, index=False, engine='pyarrow')
    print(f"Saved to {parquet_path}")

    return df


def upload_all_parquet():
    """Upload all Parquet files to Azure Blob Storage."""
    print("\n" + "=" * 60)
    print("Uploading to Azure Blob Storage")
    print("=" * 60)

    # Test connection first
    conn_test = test_connection()
    if conn_test["status"] != "connected":
        print(f"Connection failed: {conn_test['status']}")
        return False

    parquet_files = list(CACHE_DIR.glob("*.parquet"))
    print(f"Found {len(parquet_files)} Parquet files to upload")

    for parquet_file in parquet_files:
        try:
            df = pd.read_parquet(parquet_file)
            upload_parquet(df, parquet_file.name)
        except Exception as e:
            print(f"  Error uploading {parquet_file.name}: {e}")

    return True


def main():
    """Main conversion pipeline."""
    print("=" * 60)
    print("Para Athletics CSV to Parquet Converter")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    upload_only = "--upload" in sys.argv
    local_only = "--local" in sys.argv

    if upload_only:
        upload_all_parquet()
        return

    # Convert all data sources
    results_df = convert_main_results()
    rankings_df = convert_rankings()
    records_df = convert_records()
    standards_df = convert_championship_standards()

    # Summary
    print("\n" + "=" * 60)
    print("Conversion Summary")
    print("=" * 60)
    if results_df is not None:
        print(f"  Results: {len(results_df):,} rows")
    if rankings_df is not None:
        print(f"  Rankings: {len(rankings_df):,} rows")
    if records_df is not None:
        print(f"  Records: {len(records_df):,} rows")
    if standards_df is not None:
        print(f"  Standards: {len(standards_df):,} rows")

    # Upload unless local only
    if not local_only:
        upload_all_parquet()

    print("\n" + "=" * 60)
    print("Conversion Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

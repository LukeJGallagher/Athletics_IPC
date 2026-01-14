"""
Migrate local CSV data to Azure SQL Database
One-time migration script for Para Athletics data
"""

import os
import pandas as pd
from glob import glob
from azure_db import get_azure_connection, get_connection_mode
from dotenv import load_dotenv

load_dotenv()

# Configuration
BATCH_SIZE = 5000
CSV_PATHS = {
    'results': 'data/Tilastoptija/ksaoutputipc3.csv',
    'rankings': 'data/Rankings/*.csv',
    'records': 'data/Records/*.csv',
}


def migrate_results():
    """Migrate main Tilastopaja results to Azure SQL"""
    print("\n" + "="*60)
    print("MIGRATING RESULTS DATA")
    print("="*60)

    csv_path = CSV_PATHS['results']
    if not os.path.exists(csv_path):
        print(f"⚠️  Results CSV not found: {csv_path}")
        return

    # Load CSV
    print(f"Loading {csv_path}...")
    df = pd.read_csv(csv_path, encoding='latin-1', low_memory=False)
    print(f"Loaded {len(df):,} rows")

    # Connect to Azure
    with get_azure_connection() as conn:
        cursor = conn.cursor()

        # Clear existing data
        print("Clearing Results table...")
        cursor.execute("DELETE FROM Results")
        conn.commit()

        # Upload in batches
        print(f"Uploading in batches of {BATCH_SIZE}...")
        inserted = 0
        errors = 0

        for i in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[i:i+BATCH_SIZE]

            for _, row in batch.iterrows():
                try:
                    # Create full name
                    firstname = str(row.get('firstname', '')) if pd.notna(row.get('firstname')) else ''
                    lastname = str(row.get('lastname', '')) if pd.notna(row.get('lastname')) else ''
                    athlete_name = f'{firstname} {lastname}'.strip()

                    # Parse date
                    comp_date = row.get('competitiondate')
                    if pd.notna(comp_date):
                        try:
                            comp_date = pd.to_datetime(comp_date, dayfirst=True)
                        except:
                            comp_date = None
                    else:
                        comp_date = None

                    # Insert row
                    cursor.execute('''
                        INSERT INTO Results (competition_name, event_name, athlete_name,
                                            nationality, performance, date, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, GETDATE())
                    ''', (
                        str(row.get('competitionname', 'Unknown'))[:200] if pd.notna(row.get('competitionname')) else 'Unknown',
                        str(row.get('eventname', ''))[:100],
                        athlete_name[:200],
                        str(row.get('nationality', ''))[:10],
                        str(row.get('performancestring', ''))[:50],
                        comp_date
                    ))
                    inserted += 1
                except Exception as e:
                    errors += 1
                    if errors == 1:
                        print(f"⚠️  First error: {e}")

            conn.commit()
            progress = ((i + len(batch)) / len(df)) * 100
            print(f"  Progress: {progress:.1f}% ({inserted:,} rows)", end='\r')

        print(f"\n✅ Results migration complete!")
        print(f"   Inserted: {inserted:,} rows")
        print(f"   Errors: {errors:,}")


def migrate_rankings():
    """Migrate IPC rankings data to Azure SQL"""
    print("\n" + "="*60)
    print("MIGRATING RANKINGS DATA")
    print("="*60)

    pattern = CSV_PATHS['rankings']
    files = glob(pattern)

    if not files:
        print(f"⚠️  No ranking files found: {pattern}")
        return

    print(f"Found {len(files)} ranking files")

    # TODO: Implement rankings migration
    # Rankings require parsing year from filename and mapping columns
    print("⚠️  Rankings migration not yet implemented")
    print("   Manual upload via Azure Portal Query Editor recommended")


def migrate_records():
    """Migrate world/regional records to Azure SQL"""
    print("\n" + "="*60)
    print("MIGRATING RECORDS DATA")
    print("="*60)

    pattern = CSV_PATHS['records']
    files = glob(pattern)

    if not files:
        print(f"⚠️  No record files found: {pattern}")
        return

    print(f"Found {len(files)} record files")

    # TODO: Implement records migration
    # Records require parsing record type and classification
    print("⚠️  Records migration not yet implemented")
    print("   Manual upload via Azure Portal Query Editor recommended")


def verify_migration():
    """Verify data was migrated successfully"""
    print("\n" + "="*60)
    print("VERIFYING MIGRATION")
    print("="*60)

    with get_azure_connection() as conn:
        cursor = conn.cursor()

        # Check table counts
        tables = ['Results', 'Rankings', 'Records', 'Athletes', 'ScrapeLog']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table}: {count:,} rows")
            except Exception as e:
                print(f"  {table}: Error - {e}")

        # Show sample results
        print("\nSample Results data:")
        cursor.execute("""
            SELECT TOP 5 athlete_name, event_name, nationality, performance
            FROM Results
            WHERE athlete_name IS NOT NULL AND athlete_name != ''
            ORDER BY id
        """)
        for row in cursor.fetchall():
            print(f"  {row[0]} | {row[1]} | {row[2]} | {row[3]}")


def main():
    """Main migration workflow"""
    print("\n" + "="*60)
    print("PARA ATHLETICS DATA MIGRATION")
    print("CSV → Azure SQL Database")
    print("="*60)

    # Check connection mode
    mode = get_connection_mode()
    if mode != 'azure':
        print(f"\n❌ ERROR: Not connected to Azure SQL (mode: {mode})")
        print("   Please configure AZURE_SQL_CONN in .env file")
        return

    print(f"\n✅ Connection mode: {mode.upper()}")

    # Confirm migration
    response = input("\n⚠️  This will DELETE existing data and replace it. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled")
        return

    # Run migrations
    try:
        migrate_results()
        migrate_rankings()
        migrate_records()
        verify_migration()

        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETE")
        print("="*60)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    main()

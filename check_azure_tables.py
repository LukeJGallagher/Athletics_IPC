"""
Quick script to check Azure SQL table row counts
"""
from azure_db import get_azure_connection

print("Checking Azure SQL table counts...\n")

with get_azure_connection() as conn:
    cursor = conn.cursor()

    tables = ['Records', 'Rankings', 'Results', 'Athletes', 'ScrapeLog']

    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"[OK] {table}: {count:,} rows")
        except Exception as e:
            print(f"[ERROR] {table}: Error - {str(e)[:100]}")

    # Check last scrape times
    print("\n--- Last Scrape Times ---")
    try:
        cursor.execute("""
            SELECT TOP 5 table_name, status, row_count, scraped_at
            FROM ScrapeLog
            ORDER BY scraped_at DESC
        """)
        for row in cursor.fetchall():
            print(f"{row[0]}: {row[1]} - {row[2]} rows at {row[3]}")
    except Exception as e:
        print(f"ScrapeLog query failed: {e}")

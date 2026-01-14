"""
Upload Tilastopaja data to Azure SQL Database
"""
import os
import pandas as pd
import pyodbc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load data
print('Loading local data...')
df = pd.read_csv('data/Tilastoptija/ksaoutputipc3.csv', encoding='latin-1', low_memory=False)
print(f'Loaded {len(df):,} rows')

# Connect to Azure using environment variable
conn_str = os.getenv('AZURE_SQL_CONN')
if not conn_str:
    raise ValueError("AZURE_SQL_CONN not found in .env file. Please configure your database connection.")

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Clear existing data
print('Clearing Results table...')
cursor.execute('DELETE FROM Results')
conn.commit()

# Upload sample (5000 rows for testing)
print('Uploading 5,000 rows...')
sample_df = df.head(5000)

inserted = 0
for idx, row in sample_df.iterrows():
    try:
        # Create full name
        firstname = str(row.get('firstname', '')) if pd.notna(row.get('firstname')) else ''
        lastname = str(row.get('lastname', '')) if pd.notna(row.get('lastname')) else ''
        athlete_name = f'{firstname} {lastname}'.strip()

        # Get date
        comp_date = row.get('competitiondate')
        if pd.notna(comp_date):
            try:
                comp_date = pd.to_datetime(comp_date, dayfirst=True)
            except:
                comp_date = None
        else:
            comp_date = None

        cursor.execute('''
            INSERT INTO Results (competition_name, event_name, athlete_name, nationality,
                                performance, date, scraped_at)
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

        if inserted % 100 == 0:
            conn.commit()
            print(f'  {inserted:,} rows uploaded', end='\r')
    except Exception as e:
        if inserted == 0:
            print(f'Error on first row: {e}')
        continue

conn.commit()

# Verify
cursor.execute('SELECT COUNT(*) FROM Results')
count = cursor.fetchone()[0]
print(f'\n\n[OK] Upload complete!')
print(f'  Inserted: {inserted:,} rows')
print(f'  Results table: {count:,} rows')

# Show sample
print('\nSample data:')
cursor.execute('SELECT TOP 5 athlete_name, event_name, nationality, performance FROM Results WHERE athlete_name != \'\'')
for row in cursor.fetchall():
    print(f'  {row[0]} | {row[1]} | {row[2]} | {row[3]}')

conn.close()

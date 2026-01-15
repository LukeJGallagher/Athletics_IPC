"""
Data Access Layer - Unified Data Access for Analysis
====================================================

Provides consistent data access for analysis scripts.
Works with both Azure SQL (cloud) and local CSV files.

Usage:
    from data_access_layer import DataManager

    dm = DataManager()  # Auto-detects Azure or local
    results = dm.get_results()
    rankings = dm.get_rankings(year=2024)
    records = dm.get_records(record_type='World Record')
    saudi = dm.get_saudi_athletes()

Author: Performance Analysis Team
Date: 2025
"""

import pandas as pd
from pathlib import Path
import os

# Try to import azure_db module
try:
    from azure_db import get_azure_connection, get_connection_mode, query_data
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False


class DataManager:
    """
    Unified data access layer for Para Athletics analysis.
    Automatically uses Azure SQL if available, falls back to local CSV.
    """

    def __init__(self, prefer_local=False):
        """
        Initialize DataManager.

        Args:
            prefer_local: If True, always use local CSV even if Azure is available
        """
        self.data_path = Path("data")
        self.prefer_local = prefer_local
        self._connection_mode = self._determine_mode()

        # Cache for loaded data
        self._results_cache = None
        self._rankings_cache = {}
        self._records_cache = {}

    def _determine_mode(self):
        """Determine whether to use Azure or local"""
        if self.prefer_local:
            return 'local'

        if AZURE_AVAILABLE:
            mode = get_connection_mode()
            if mode == 'azure':
                return 'azure'

        return 'local'

    @property
    def mode(self):
        """Current connection mode: 'azure' or 'local'"""
        return self._connection_mode

    def get_results(self, filters=None):
        """
        Get results data from Azure SQL or local CSV.

        Args:
            filters: Optional dict of column:value filters

        Returns:
            pandas DataFrame with results
        """
        if self._connection_mode == 'azure':
            return self._get_results_azure(filters)
        else:
            return self._get_results_local(filters)

    def _get_results_azure(self, filters=None):
        """Get results from Azure SQL"""
        query = "SELECT * FROM Results"

        if filters:
            conditions = []
            for col, val in filters.items():
                if isinstance(val, str):
                    conditions.append(f"{col} LIKE '%{val}%'")
                else:
                    conditions.append(f"{col} = {val}")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        try:
            return query_data(query)
        except Exception as e:
            print(f"[WARNING] Azure query failed: {e}")
            print("Falling back to local CSV...")
            return self._get_results_local(filters)

    def _get_results_local(self, filters=None):
        """Get results from local CSV"""
        if self._results_cache is None:
            csv_path = self.data_path / "Tilastoptija" / "ksaoutputipc3.csv"
            if csv_path.exists():
                self._results_cache = pd.read_csv(
                    csv_path,
                    encoding='latin-1',
                    low_memory=False
                )
                print(f"[OK] Loaded {len(self._results_cache):,} results from local CSV")
            else:
                print(f"[ERROR] Results CSV not found: {csv_path}")
                return pd.DataFrame()

        df = self._results_cache.copy()

        if filters:
            for col, val in filters.items():
                if col in df.columns:
                    if isinstance(val, str):
                        df = df[df[col].astype(str).str.contains(val, case=False, na=False)]
                    else:
                        df = df[df[col] == val]

        return df

    def get_rankings(self, year=None, region='World'):
        """
        Get rankings data.

        Args:
            year: Year to filter (default: all years)
            region: Region type (default: 'World')

        Returns:
            pandas DataFrame with rankings
        """
        if self._connection_mode == 'azure':
            return self._get_rankings_azure(year, region)
        else:
            return self._get_rankings_local(year, region)

    def _get_rankings_azure(self, year=None, region='World'):
        """Get rankings from Azure SQL"""
        query = "SELECT * FROM Rankings"
        conditions = []

        if year:
            conditions.append(f"year = {year}")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        try:
            return query_data(query)
        except Exception as e:
            print(f"[WARNING] Azure rankings query failed: {e}")
            return self._get_rankings_local(year, region)

    def _get_rankings_local(self, year=None, region='World'):
        """Get rankings from local CSV files"""
        rankings_dir = self.data_path / "Rankings"
        if not rankings_dir.exists():
            print(f"[WARNING] Rankings directory not found: {rankings_dir}")
            return pd.DataFrame()

        all_rankings = []

        for csv_file in rankings_dir.glob("*.csv"):
            filename = csv_file.stem

            # Skip if year filter doesn't match
            if year and str(year) not in filename:
                continue

            # Skip if region filter doesn't match
            if region and region.lower() not in filename.lower():
                continue

            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
                # Add source info
                df['_source_file'] = filename
                all_rankings.append(df)
            except Exception as e:
                print(f"[WARNING] Failed to load {csv_file}: {e}")

        if all_rankings:
            combined = pd.concat(all_rankings, ignore_index=True)
            print(f"[OK] Loaded {len(combined):,} rankings from {len(all_rankings)} files")
            return combined
        else:
            return pd.DataFrame()

    def get_records(self, record_type=None):
        """
        Get records data.

        Args:
            record_type: Filter by type ('World Record', 'Paralympic Record', etc.)

        Returns:
            pandas DataFrame with records
        """
        if self._connection_mode == 'azure':
            return self._get_records_azure(record_type)
        else:
            return self._get_records_local(record_type)

    def _get_records_azure(self, record_type=None):
        """Get records from Azure SQL"""
        query = "SELECT * FROM Records"

        if record_type:
            query += f" WHERE record_type = '{record_type}'"

        try:
            return query_data(query)
        except Exception as e:
            print(f"[WARNING] Azure records query failed: {e}")
            return self._get_records_local(record_type)

    def _get_records_local(self, record_type=None):
        """Get records from local CSV files"""
        records_dir = self.data_path / "Records"
        if not records_dir.exists():
            print(f"[WARNING] Records directory not found: {records_dir}")
            return pd.DataFrame()

        all_records = []

        for csv_file in records_dir.glob("*.csv"):
            filename = csv_file.stem

            # Determine record type from filename
            detected_type = self._detect_record_type(filename)

            # Skip if type filter doesn't match
            if record_type and detected_type != record_type:
                continue

            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
                df['record_type'] = detected_type
                df['_source_file'] = filename
                all_records.append(df)
            except Exception as e:
                print(f"[WARNING] Failed to load {csv_file}: {e}")

        if all_records:
            combined = pd.concat(all_records, ignore_index=True)
            print(f"[OK] Loaded {len(combined):,} records from {len(all_records)} files")
            return combined
        else:
            return pd.DataFrame()

    def _detect_record_type(self, filename):
        """Detect record type from filename"""
        type_map = {
            'World Record': 'World Record',
            'Paralympic Record': 'Paralympic Record',
            'Asian Record': 'Asian Record',
            'European Record': 'European Record',
            'African Record': 'African Record',
            'Americas Record': 'Americas Record',
            'Championship Record': 'Championship Record',
            'Asian Para Games Record': 'Asian Para Games Record',
            'European Championship Record': 'European Championship Record',
            'Oceanian Record': 'Oceanian Record',
            'Parapan American Games Record': 'Parapan American Games Record',
        }

        for key, value in type_map.items():
            if key in filename:
                return value

        return 'Unknown Record'

    def get_saudi_athletes(self, event=None, classification=None):
        """
        Get Saudi athletes from results.

        Args:
            event: Optional event filter (e.g., '100m')
            classification: Optional classification filter (e.g., 'T54')

        Returns:
            pandas DataFrame with Saudi athlete results
        """
        filters = {'nationality': 'KSA'}
        df = self.get_results(filters)

        if event and 'eventname' in df.columns:
            df = df[df['eventname'].astype(str).str.contains(event, case=False, na=False)]

        if classification and 'class' in df.columns:
            df = df[df['class'].astype(str).str.contains(classification, case=False, na=False)]

        return df

    def get_major_championships(self):
        """
        Get results from major championships (World Championships, Paralympics, Asian).

        Returns:
            pandas DataFrame with major championship results
        """
        df = self.get_results()

        if 'competitionname' not in df.columns:
            return pd.DataFrame()

        # Filter for major championships
        major_mask = df['competitionname'].astype(str).str.contains(
            'World Championships|Paralympic|Asian',
            case=False, na=False
        )

        major_df = df[major_mask].copy()

        # Add competition type classification
        major_df['competition_type'] = 'Other'
        major_df.loc[
            major_df['competitionname'].str.contains('Paralympic', case=False, na=False),
            'competition_type'
        ] = 'Paralympics'
        major_df.loc[
            major_df['competitionname'].str.contains('World Championships', case=False, na=False),
            'competition_type'
        ] = 'World Championships'
        major_df.loc[
            major_df['competitionname'].str.contains('Asian', case=False, na=False),
            'competition_type'
        ] = 'Asian Championships'

        return major_df

    def get_event_results(self, event, classification=None, gender=None):
        """
        Get results for specific event.

        Args:
            event: Event name (e.g., '100m', 'Shot Put')
            classification: Optional classification (e.g., 'T54')
            gender: Optional gender filter ('M' or 'W')

        Returns:
            pandas DataFrame with event results
        """
        df = self.get_results()

        if 'eventname' not in df.columns:
            return pd.DataFrame()

        # Filter by event
        df = df[df['eventname'].astype(str).str.contains(event, case=False, na=False)]

        # Filter by classification
        if classification and 'class' in df.columns:
            df = df[df['class'].astype(str).str.contains(classification, case=False, na=False)]

        # Filter by gender (assuming gender is in eventname like "100m M T54")
        if gender:
            df = df[df['eventname'].astype(str).str.contains(f' {gender} ', case=False, na=False)]

        return df

    def get_championship_standards(self, event=None, classification=None):
        """
        Get championship winning standards (gold/bronze medal performances).

        Args:
            event: Optional event filter
            classification: Optional classification filter

        Returns:
            pandas DataFrame with championship standards
        """
        # Get major championship results
        df = self.get_major_championships()

        if df.empty:
            return pd.DataFrame()

        # Filter by event and classification if specified
        if event and 'eventname' in df.columns:
            df = df[df['eventname'].astype(str).str.contains(event, case=False, na=False)]

        if classification and 'class' in df.columns:
            df = df[df['class'].astype(str).str.contains(classification, case=False, na=False)]

        # Get position/rank column
        rank_col = None
        for col in ['position', 'rank', 'place', 'pos']:
            if col in df.columns:
                rank_col = col
                break

        if rank_col is None:
            return df

        # Filter for medal positions (1-3) and finals (1-8)
        df[rank_col] = pd.to_numeric(df[rank_col], errors='coerce')
        medal_df = df[df[rank_col] <= 8].copy()

        return medal_df

    def get_summary_stats(self):
        """
        Get summary statistics about available data.

        Returns:
            dict with data summary
        """
        summary = {
            'connection_mode': self._connection_mode,
            'results_count': 0,
            'rankings_files': 0,
            'records_files': 0,
            'saudi_results_count': 0,
            'major_championships': 0
        }

        # Results count
        results = self.get_results()
        summary['results_count'] = len(results)

        # Saudi athletes
        saudi = self.get_saudi_athletes()
        summary['saudi_results_count'] = len(saudi)

        # Major championships
        major = self.get_major_championships()
        summary['major_championships'] = len(major)

        # Rankings count
        rankings_dir = self.data_path / "Rankings"
        if rankings_dir.exists():
            summary['rankings_files'] = len(list(rankings_dir.glob("*.csv")))

        # Records count
        records_dir = self.data_path / "Records"
        if records_dir.exists():
            summary['records_files'] = len(list(records_dir.glob("*.csv")))

        return summary


def test_data_manager():
    """Test the DataManager"""
    print("="*60)
    print("DATA ACCESS LAYER TEST")
    print("="*60)

    dm = DataManager()
    print(f"\nConnection mode: {dm.mode}")

    # Get summary
    summary = dm.get_summary_stats()
    print(f"\nData Summary:")
    print(f"  Results: {summary['results_count']:,} rows")
    print(f"  Saudi Results: {summary['saudi_results_count']:,} rows")
    print(f"  Major Championships: {summary['major_championships']:,} rows")
    print(f"  Rankings Files: {summary['rankings_files']}")
    print(f"  Records Files: {summary['records_files']}")

    # Test event query
    print("\nTesting event query (100m T54)...")
    event_results = dm.get_event_results('100m', 'T54')
    print(f"  Found: {len(event_results)} results")

    # Test championship standards
    print("\nTesting championship standards...")
    standards = dm.get_championship_standards('100m', 'T54')
    print(f"  Found: {len(standards)} championship results")

    # Test Saudi query
    print("\nTesting Saudi athletes query...")
    saudi = dm.get_saudi_athletes()
    if not saudi.empty and 'athletename' in saudi.columns:
        unique_athletes = saudi['athletename'].nunique()
        print(f"  Found: {len(saudi)} Saudi results ({unique_athletes} unique athletes)")
    else:
        print(f"  Found: {len(saudi)} Saudi results")

    print("\n[SUCCESS] Data access layer test complete!")
    return dm


if __name__ == "__main__":
    test_data_manager()

"""
Parquet Data Layer for Para Athletics Dashboard
================================================
Provides fast data access using DuckDB queries on Parquet files.
Supports both local files and Azure Blob Storage.

This replaces the Azure SQL data layer for better performance.
"""

import os
import io
import pandas as pd
from pathlib import Path
from functools import lru_cache
from typing import Optional, List, Dict
from dotenv import load_dotenv

load_dotenv()

# Try imports
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    from azure.storage.blob import BlobServiceClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


# Configuration
CONTAINER_NAME = "para-athletics-data"
BLOB_PREFIX = "parquet/"
LOCAL_PARQUET_DIR = Path("data/parquet_cache")
LOCAL_CSV_DIR = Path("data/Tilastoptija")


class ParquetDataManager:
    """
    Unified data manager for Para Athletics dashboard.
    Uses Parquet files with DuckDB for fast queries.
    Falls back to local CSV if Parquet not available.
    """

    def __init__(self):
        self.mode = self._detect_mode()
        self._conn = None
        print(f"ParquetDataManager initialized in {self.mode} mode")

    def _detect_mode(self) -> str:
        """Detect whether to use Azure Blob, local Parquet, or CSV."""
        # Check for Streamlit secrets first
        conn_str = None
        if STREAMLIT_AVAILABLE:
            try:
                conn_str = st.secrets.get("AZURE_STORAGE_CONNECTION_STRING")
            except:
                pass

        # Then check environment
        if not conn_str:
            conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        # Check if we have Azure connection and azure-storage-blob installed
        if conn_str and AZURE_AVAILABLE:
            return "azure_blob"

        # Check for local Parquet files
        if LOCAL_PARQUET_DIR.exists() and list(LOCAL_PARQUET_DIR.glob("*.parquet")):
            return "local_parquet"

        # Fall back to CSV
        return "local_csv"

    def _get_blob_url(self, blob_name: str) -> str:
        """Get Azure Blob URL for direct DuckDB access."""
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if STREAMLIT_AVAILABLE:
            try:
                conn_str = st.secrets.get("AZURE_STORAGE_CONNECTION_STRING", conn_str)
            except:
                pass

        # Parse account name
        parts = dict(part.split("=", 1) for part in conn_str.split(";") if "=" in part)
        account_name = parts.get("AccountName", "paraathletics")

        return f"https://{account_name}.blob.core.windows.net/{CONTAINER_NAME}/{BLOB_PREFIX}{blob_name}"

    def _download_blob_to_df(self, blob_name: str) -> pd.DataFrame:
        """Download blob and return as DataFrame."""
        conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if STREAMLIT_AVAILABLE:
            try:
                conn_str = st.secrets.get("AZURE_STORAGE_CONNECTION_STRING", conn_str)
            except:
                pass

        blob_service = BlobServiceClient.from_connection_string(conn_str)
        container_client = blob_service.get_container_client(CONTAINER_NAME)
        blob_client = container_client.get_blob_client(f"{BLOB_PREFIX}{blob_name}")

        buffer = io.BytesIO()
        blob_data = blob_client.download_blob()
        blob_data.readinto(buffer)
        buffer.seek(0)

        return pd.read_parquet(buffer)

    def get_connection_mode(self) -> str:
        """Return current connection mode for UI display."""
        return self.mode

    @lru_cache(maxsize=1)
    def get_results(self) -> pd.DataFrame:
        """Load main results data."""
        if self.mode == "azure_blob":
            try:
                return self._download_blob_to_df("results.parquet")
            except Exception as e:
                print(f"Azure blob download failed: {e}, falling back to local")

        if self.mode == "local_parquet" or LOCAL_PARQUET_DIR.exists():
            parquet_path = LOCAL_PARQUET_DIR / "results.parquet"
            if parquet_path.exists():
                return pd.read_parquet(parquet_path)

        # Fall back to CSV
        csv_path = LOCAL_CSV_DIR / "ksaoutputipc3.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path, encoding='latin-1', low_memory=False)

        return pd.DataFrame()

    @lru_cache(maxsize=1)
    def get_rankings(self) -> pd.DataFrame:
        """Load rankings data."""
        if self.mode == "azure_blob":
            try:
                return self._download_blob_to_df("rankings.parquet")
            except Exception as e:
                print(f"Azure blob download failed: {e}")

        if LOCAL_PARQUET_DIR.exists():
            parquet_path = LOCAL_PARQUET_DIR / "rankings.parquet"
            if parquet_path.exists():
                return pd.read_parquet(parquet_path)

        # Load from CSV files
        rankings_dir = Path("data/Rankings")
        if rankings_dir.exists():
            all_rankings = []
            for csv_file in rankings_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    all_rankings.append(df)
                except:
                    pass
            if all_rankings:
                return pd.concat(all_rankings, ignore_index=True)

        return pd.DataFrame()

    @lru_cache(maxsize=1)
    def get_records(self) -> pd.DataFrame:
        """Load records data."""
        if self.mode == "azure_blob":
            try:
                return self._download_blob_to_df("records.parquet")
            except Exception as e:
                print(f"Azure blob download failed: {e}")

        if LOCAL_PARQUET_DIR.exists():
            parquet_path = LOCAL_PARQUET_DIR / "records.parquet"
            if parquet_path.exists():
                return pd.read_parquet(parquet_path)

        # Load from CSV files
        records_dir = Path("data/Records")
        if records_dir.exists():
            all_records = []
            for csv_file in records_dir.glob("*.csv"):
                try:
                    df = pd.read_csv(csv_file, encoding='utf-8')
                    df['record_source'] = csv_file.stem
                    all_records.append(df)
                except:
                    pass
            if all_records:
                return pd.concat(all_records, ignore_index=True)

        return pd.DataFrame()

    @lru_cache(maxsize=1)
    def get_championship_standards(self) -> pd.DataFrame:
        """Load championship standards data."""
        if self.mode == "azure_blob":
            try:
                return self._download_blob_to_df("championship_standards.parquet")
            except Exception as e:
                print(f"Azure blob download failed: {e}")

        if LOCAL_PARQUET_DIR.exists():
            parquet_path = LOCAL_PARQUET_DIR / "championship_standards.parquet"
            if parquet_path.exists():
                return pd.read_parquet(parquet_path)

        # Load from CSV
        for csv_path in [Path("championship_standards_report.csv"),
                         Path("output/championship_standards_report.csv")]:
            if csv_path.exists():
                return pd.read_csv(csv_path)

        return pd.DataFrame()

    def get_saudi_athletes(self) -> pd.DataFrame:
        """Get Saudi Arabia athletes from results."""
        results = self.get_results()
        if results.empty:
            return pd.DataFrame()

        # Handle different column naming
        nat_col = None
        for col in ['nationality', 'Nationality', 'country', 'Country', 'nat']:
            if col in results.columns:
                nat_col = col
                break

        if nat_col:
            return results[results[nat_col] == 'KSA'].copy()
        return pd.DataFrame()

    def query(self, sql: str, table_name: str = "results") -> pd.DataFrame:
        """
        Execute SQL query on data using DuckDB.

        Args:
            sql: SQL query (use 'data' as table name)
            table_name: Which dataset to query ('results', 'rankings', 'records')

        Returns:
            Query result as DataFrame
        """
        if not DUCKDB_AVAILABLE:
            raise ImportError("duckdb not installed. Install with: pip install duckdb")

        # Get the appropriate data
        if table_name == "results":
            df = self.get_results()
        elif table_name == "rankings":
            df = self.get_rankings()
        elif table_name == "records":
            df = self.get_records()
        else:
            raise ValueError(f"Unknown table: {table_name}")

        if df.empty:
            return pd.DataFrame()

        # Create DuckDB connection and query
        conn = duckdb.connect(":memory:")
        conn.register("data", df)
        result = conn.execute(sql).fetchdf()
        conn.close()

        return result

    def clear_cache(self):
        """Clear cached data (for refresh)."""
        self.get_results.cache_clear()
        self.get_rankings.cache_clear()
        self.get_records.cache_clear()
        self.get_championship_standards.cache_clear()

    def get_stats(self) -> Dict:
        """Get data statistics for dashboard."""
        results = self.get_results()
        rankings = self.get_rankings()
        records = self.get_records()

        return {
            "mode": self.mode,
            "results_count": len(results),
            "rankings_count": len(rankings),
            "records_count": len(records),
            "saudi_athletes": len(self.get_saudi_athletes()),
        }


# Singleton instance
_data_manager = None


def get_data_manager() -> ParquetDataManager:
    """Get singleton data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = ParquetDataManager()
    return _data_manager


# Convenience functions for direct use
def load_results() -> pd.DataFrame:
    """Load results data."""
    return get_data_manager().get_results()


def load_rankings() -> pd.DataFrame:
    """Load rankings data."""
    return get_data_manager().get_rankings()


def load_records() -> pd.DataFrame:
    """Load records data."""
    return get_data_manager().get_records()


def load_championship_standards() -> pd.DataFrame:
    """Load championship standards data."""
    return get_data_manager().get_championship_standards()


def load_saudi_athletes() -> pd.DataFrame:
    """Load Saudi athletes data."""
    return get_data_manager().get_saudi_athletes()


def get_connection_mode() -> str:
    """Get current connection mode."""
    return get_data_manager().get_connection_mode()


if __name__ == "__main__":
    print("Testing Parquet Data Layer...")
    dm = get_data_manager()
    stats = dm.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

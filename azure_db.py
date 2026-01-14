"""
Azure SQL Database Connection Module
Supports both local SQLite (development) and Azure SQL (production)

This module provides a unified interface for database connections that works
seamlessly in both local development and Streamlit Cloud deployment environments.
"""

import os
import sqlite3
import pandas as pd
import time
from typing import Optional
from contextlib import contextmanager

# Try to load .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, skip (environment variables should be set elsewhere)
    pass

# Try to import pyodbc for Azure SQL
try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False
    print("Warning: pyodbc not installed. Azure SQL features disabled.")

# Database paths for local SQLite
LOCAL_DB_PATHS = {
    'main': 'para_athletics_downloads.db',
    'downloads': 'para_athletics_downloads.db',
}

# Azure SQL connection string (lazy-loaded)
_AZURE_SQL_CONN = None


def _get_azure_conn_string():
    """
    Get Azure SQL connection string from env or Streamlit secrets (lazy-loaded).

    Checks in order:
    1. Environment variable AZURE_SQL_CONN (from .env for local dev)
    2. Streamlit secrets (for Streamlit Cloud deployment)

    Returns:
        str or None: Connection string if found, None otherwise
    """
    global _AZURE_SQL_CONN

    # Return cached value if already loaded
    if _AZURE_SQL_CONN is not None:
        return _AZURE_SQL_CONN

    # Try environment variable first (local development)
    _AZURE_SQL_CONN = os.getenv('AZURE_SQL_CONN')

    # Try Streamlit secrets if not in environment (Streamlit Cloud)
    if not _AZURE_SQL_CONN:
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'AZURE_SQL_CONN' in st.secrets:
                _AZURE_SQL_CONN = st.secrets['AZURE_SQL_CONN']
        except (ImportError, FileNotFoundError, KeyError, AttributeError):
            # Streamlit not available or secrets not configured
            pass

    return _AZURE_SQL_CONN


def _use_azure():
    """
    Check if Azure SQL should be used.

    Returns:
        bool: True if Azure SQL is configured and available, False otherwise
    """
    return bool(_get_azure_conn_string()) and PYODBC_AVAILABLE


def get_connection_mode() -> str:
    """
    Return current connection mode: 'azure' or 'sqlite'

    Returns:
        str: 'azure' if Azure SQL is configured, 'sqlite' otherwise
    """
    return 'azure' if _use_azure() else 'sqlite'


@contextmanager
def get_azure_connection():
    """
    Context manager for Azure SQL connections with auto-wake retry.

    Handles Azure SQL Serverless auto-pause by retrying with exponential backoff.
    If database is paused (error 40613), waits and retries up to 3 times.

    Usage:
        with get_azure_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")

    Raises:
        ImportError: If pyodbc is not installed
        ValueError: If AZURE_SQL_CONN is not configured
        pyodbc.Error: If connection fails after all retries
    """
    if not PYODBC_AVAILABLE:
        raise ImportError("pyodbc is required for Azure SQL connections")

    conn_str = _get_azure_conn_string()
    if not conn_str:
        raise ValueError("AZURE_SQL_CONN not found in environment or Streamlit secrets")

    conn = None
    max_retries = 3
    retry_delays = [10, 20, 30]  # Exponential backoff: 10s, 20s, 30s

    for attempt in range(max_retries):
        try:
            conn = pyodbc.connect(conn_str)
            yield conn
            return  # Success, exit the function
        except pyodbc.Error as e:
            # Check if error is due to paused database (error code 40613)
            error_msg = str(e)
            is_paused = '40613' in error_msg or 'not currently available' in error_msg.lower()

            if is_paused and attempt < max_retries - 1:
                # Database is paused, wait and retry
                delay = retry_delays[attempt]
                print(f"Azure SQL database paused. Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                # Not a pause error, or final retry failed
                raise
        finally:
            if conn:
                conn.close()


@contextmanager
def get_sqlite_connection(db_name: str = 'main'):
    """
    Context manager for SQLite connections.

    Args:
        db_name: Logical database name (e.g., 'main', 'downloads')

    Usage:
        with get_sqlite_connection('downloads') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM table")

    Raises:
        ValueError: If db_name is not recognized
        sqlite3.Error: If connection fails
    """
    if db_name not in LOCAL_DB_PATHS:
        raise ValueError(f"Unknown database: {db_name}. Available: {list(LOCAL_DB_PATHS.keys())}")

    db_path = LOCAL_DB_PATHS[db_name]
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        yield conn
    finally:
        if conn:
            conn.close()


@contextmanager
def get_connection(db_name: str = 'main'):
    """
    Universal connection context manager.
    Automatically uses Azure SQL if configured, otherwise SQLite.

    Args:
        db_name: Database name (only used for SQLite fallback)

    Usage:
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM table", conn)

    Returns:
        Connection object (pyodbc or sqlite3)
    """
    if _use_azure():
        with get_azure_connection() as conn:
            yield conn
    else:
        with get_sqlite_connection(db_name) as conn:
            yield conn


def query_data(sql: str, db_name: str = 'main', params: tuple = None) -> pd.DataFrame:
    """
    Execute a SQL query and return results as DataFrame.
    Works with both Azure SQL and SQLite.

    Args:
        sql: SQL query to execute
        db_name: Database name (only used for SQLite fallback)
        params: Optional tuple of parameters for parameterized queries

    Returns:
        pd.DataFrame: Query results

    Usage:
        # Simple query
        df = query_data("SELECT * FROM Results WHERE nationality = 'KSA'")

        # Parameterized query
        df = query_data("SELECT * FROM Results WHERE nationality = ?", params=('KSA',))
    """
    with get_connection(db_name) as conn:
        if params:
            return pd.read_sql(sql, conn, params=params)
        return pd.read_sql(sql, conn)


def test_connection() -> dict:
    """
    Test database connectivity and return diagnostic info.

    Returns:
        dict: Diagnostic information including:
            - mode: 'azure' or 'sqlite'
            - azure_configured: Whether Azure connection string is found
            - pyodbc_available: Whether pyodbc is installed
            - connection_test: 'success', 'failed', or 'not_run'
            - row_count: Number of rows in test table (if successful)
            - error: Error message (if failed)

    Usage:
        result = test_connection()
        print(f"Connection mode: {result['mode']}")
        print(f"Connection test: {result['connection_test']}")
    """
    result = {
        'mode': get_connection_mode(),
        'azure_configured': bool(_get_azure_conn_string()),
        'pyodbc_available': PYODBC_AVAILABLE,
        'connection_test': 'not_run',
        'error': None
    }

    try:
        with get_connection() as conn:
            # Test with Results table (should exist in Azure SQL)
            df = pd.read_sql("SELECT COUNT(*) as cnt FROM Results", conn)
            result['connection_test'] = 'success'
            result['row_count'] = int(df['cnt'].iloc[0])
    except Exception as e:
        result['connection_test'] = 'failed'
        result['error'] = str(e)

    return result


# Command-line testing
if __name__ == "__main__":
    print("Azure SQL Database Connection Module")
    print("=" * 50)

    result = test_connection()

    print(f"Connection mode: {result['mode']}")
    print(f"Azure configured: {result['azure_configured']}")
    print(f"pyodbc available: {result['pyodbc_available']}")
    print(f"Connection test: {result['connection_test']}")

    if result['connection_test'] == 'success':
        print(f"Row count in Results table: {result['row_count']:,}")
    elif result['connection_test'] == 'failed':
        print(f"Error: {result['error']}")

    print("=" * 50)

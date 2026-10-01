"""
Database module for TrustLens.
Handles storage and retrieval of analysis results using SQLite.
"""
import sqlite3
import json
import os
from typing import Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "trustlens.db")

def _get_connection():
    """Helper to get a database connection."""
    return sqlite3.connect(DB_PATH)

def initialize_database() -> None:
    """
    Initializes the SQLite database and creates the necessary tables.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    fingerprint TEXT PRIMARY KEY,
                    result JSON NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")

def save_analysis(fingerprint: str, result: dict) -> bool:
    """
    Saves an analysis result associated with a fingerprint.
    Prevents duplicate entries by using INSERT OR IGNORE.

    Args:
        fingerprint (str): The unique identifier for the content.
        result (dict): The analysis result to save.

    Returns:
        bool: True if successful (or already exists), False otherwise.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            result_json = json.dumps(result)
            cursor.execute('''
                INSERT OR IGNORE INTO analyses (fingerprint, result)
                VALUES (?, ?)
            ''', (fingerprint, result_json))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Error saving analysis: {e}")
        return False
    except TypeError as e:
        print(f"Error serializing result to JSON: {e}")
        return False

def get_analysis(fingerprint: str) -> Optional[dict]:
    """
    Retrieves an analysis result by its fingerprint.

    Args:
        fingerprint (str): The unique identifier for the content.

    Returns:
        Optional[dict]: The analysis result (with timestamp added) if found, None otherwise.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT result, timestamp FROM analyses WHERE fingerprint = ?', (fingerprint,))
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                data['stored_at'] = row[1]
                return data
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving analysis: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing retrieved JSON: {e}")
        return None

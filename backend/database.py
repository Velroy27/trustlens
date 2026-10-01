"""
Database module for TrustLens.
Handles storage and retrieval of analysis results and official source-of-truth notices using SQLite.
"""
import sqlite3
import json
import os
import re
import difflib
from typing import Optional, List, Dict, Any
from .fingerprint import generate_fingerprint

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "trustlens.db")

DEMO_OFFICIAL_NOTICE_ID = "DEMO-SCHOLARSHIP-2026"
DEMO_OFFICIAL_NOTICE_TITLE = "University Scholarship Notice"
DEMO_OFFICIAL_NOTICE_CONTENT = (
    "UNIVERSITY SCHOLARSHIP NOTICE\n\n"
    "Scholarship applications are open until 15 October 2026.\n"
    "Application fee: None.\n"
    "Applications must be submitted through the official university portal."
)


def _get_connection():
    """Helper to get a database connection."""
    return sqlite3.connect(DB_PATH)


def initialize_database() -> None:
    """
    Initializes the SQLite database, creates necessary tables, and seeds demo data.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            # Analyses cache table (keyed by fingerprint)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    fingerprint TEXT PRIMARY KEY,
                    result JSON NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Official source-of-truth notices table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS official_notices (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    image_blob BLOB,
                    image_mime TEXT
                )
            ''')
            # Migration check: ensure image_blob, image_mime, and category columns exist
            try:
                cursor.execute('ALTER TABLE official_notices ADD COLUMN image_blob BLOB')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE official_notices ADD COLUMN image_mime TEXT')
            except sqlite3.OperationalError:
                pass
            try:
                cursor.execute('ALTER TABLE official_notices ADD COLUMN category TEXT DEFAULT "General Notice"')
            except sqlite3.OperationalError:
                pass

            # Verification reports table (keyed by unique verification_id)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_reports (
                    verification_id TEXT PRIMARY KEY,
                    report JSON NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    fingerprint TEXT
                )
            ''')
            conn.commit()

        # Seed demo official notice if not already present
        seed_demo_notices()
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")


def seed_demo_notices() -> None:
    """Seeds official source-of-truth records for demonstration."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM official_notices WHERE id = ?', (DEMO_OFFICIAL_NOTICE_ID,))
            if not cursor.fetchone():
                fp = generate_fingerprint(DEMO_OFFICIAL_NOTICE_CONTENT)
                cursor.execute('''
                    INSERT INTO official_notices (id, title, content, fingerprint, category)
                    VALUES (?, ?, ?, ?, ?)
                ''', (DEMO_OFFICIAL_NOTICE_ID, DEMO_OFFICIAL_NOTICE_TITLE, DEMO_OFFICIAL_NOTICE_CONTENT, fp, "Scholarship"))
                conn.commit()
    except sqlite3.Error as e:
        print(f"Error seeding demo notices: {e}")


def save_official_notice(
    title: str,
    content: str,
    notice_id: Optional[str] = None,
    image_blob: Optional[bytes] = None,
    image_mime: Optional[str] = None,
    category: str = "General Notice",
) -> Optional[str]:
    """
    Saves or indexes an official notice as a baseline source-of-truth.
    Supports optional official notice image data and category classification.
    """
    if not title or not (content or image_blob):
        return None
    content_str = content.strip() if content else ""
    notice_id = notice_id or f"NOTICE-{generate_fingerprint(content_str or title)[:8].upper()}"
    fp = generate_fingerprint(content_str or title)
    category_str = (category or "General Notice").strip()
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO official_notices (id, title, content, fingerprint, image_blob, image_mime, category)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (notice_id, title.strip(), content_str, fp, image_blob, image_mime, category_str))
            conn.commit()
            return notice_id
    except sqlite3.Error as e:
        print(f"Error saving official notice: {e}")
        return None


def get_official_notice(notice_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves an official notice by ID."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, content, fingerprint, created_at, image_blob, image_mime, category
                FROM official_notices WHERE id = ?
            ''', (notice_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "fingerprint": row[3],
                    "created_at": row[4],
                    "image_blob": row[5],
                    "image_mime": row[6],
                    "category": row[7] or "General Notice",
                }
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving official notice: {e}")
        return None


def get_all_official_notices() -> List[Dict[str, Any]]:
    """Retrieves all registered official notices."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, content, fingerprint, created_at, image_blob, image_mime, category
                FROM official_notices ORDER BY created_at DESC
            ''')
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "title": r[1],
                    "content": r[2],
                    "fingerprint": r[3],
                    "created_at": r[4],
                    "image_blob": r[5],
                    "image_mime": r[6],
                    "category": r[7] or "General Notice",
                }
                for r in rows
            ]
    except sqlite3.Error as e:
        print(f"Error listing official notices: {e}")
        return []


def _normalize_tokens(text: str) -> set:
    """Extracts a set of normalized alphanumeric tokens from text."""
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    return {w for w in clean.split() if len(w) > 2}


def find_matching_notice(candidate_text: str, min_similarity: float = 0.35) -> Optional[Dict[str, Any]]:
    """
    Finds the best matching official source notice from the database for a candidate forwarded notice.

    Uses a combination of:
    1. Exact SHA-256 fingerprint equality (exact match -> 1.0)
    2. Token Jaccard similarity (word set overlap)
    3. SequenceMatcher sequence similarity on normalized text

    Args:
        candidate_text (str): The text of the forwarded/edited notice.
        min_similarity (float): Threshold above which a match is confirmed.

    Returns:
        Optional[dict]: Matching notice details with match score, or None if no baseline matches.
    """
    if not candidate_text or not candidate_text.strip():
        return None

    notices = get_all_official_notices()
    if not notices:
        return None

    candidate_fp = generate_fingerprint(candidate_text)
    candidate_tokens = _normalize_tokens(candidate_text)
    candidate_norm = " ".join(re.sub(r'\s+', ' ', candidate_text.lower().strip()).split())

    best_match: Optional[Dict[str, Any]] = None
    highest_score = 0.0

    for notice in notices:
        # 1. Exact match check
        if notice.get("fingerprint") == candidate_fp:
            notice["match_score"] = 1.0
            return notice

        stored_content = notice.get("content", "")
        stored_tokens = _normalize_tokens(stored_content)
        stored_norm = " ".join(re.sub(r'\s+', ' ', stored_content.lower().strip()).split())

        # 2. Token Jaccard overlap
        if candidate_tokens and stored_tokens:
            intersection = candidate_tokens & stored_tokens
            union = candidate_tokens | stored_tokens
            jaccard = len(intersection) / len(union) if union else 0.0
        else:
            jaccard = 0.0

        # 3. SequenceMatcher ratio
        seq_ratio = difflib.SequenceMatcher(None, candidate_norm, stored_norm).ratio()

        # Combined metric with emphasis on shared core terminology
        score = max(jaccard, seq_ratio)

        # Check if the official notice title words appear prominently in the candidate
        title_tokens = _normalize_tokens(notice.get("title", ""))
        if title_tokens and title_tokens.issubset(candidate_tokens):
            score = min(1.0, score + 0.15)

        if score > highest_score:
            highest_score = score
            best_match = notice

    if highest_score >= min_similarity and best_match:
        best_match["match_score"] = round(highest_score, 3)
        return best_match

    return None


def save_analysis(fingerprint: str, result: dict) -> bool:
    """
    Saves an analysis result associated with a fingerprint.
    Prevents duplicate entries by using INSERT OR IGNORE.
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


def save_verification_report(verification_id: str, report: dict, fingerprint: Optional[str] = None) -> bool:
    """
    Saves a completed verification report keyed by its unique verification_id.
    Used for QR code receipt retrieval and permanent audit trail.
    """
    if not verification_id or not report:
        return False
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            report_json = json.dumps(report)
            cursor.execute('''
                INSERT OR REPLACE INTO verification_reports (verification_id, report, fingerprint)
                VALUES (?, ?, ?)
            ''', (verification_id.strip(), report_json, fingerprint))
            conn.commit()
            return True
    except sqlite3.Error as e:
        print(f"Error saving verification report: {e}")
        return False


def get_verification_report(verification_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a stored verification report by its verification_id.
    Returns the parsed report dictionary or None if not found.
    """
    if not verification_id:
        return None
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT report, timestamp, fingerprint FROM verification_reports
                WHERE verification_id = ?
            ''', (verification_id.strip(),))
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                data["stored_timestamp"] = row[1]
                data["fingerprint"] = row[2]
                return data
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving verification report: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding verification report JSON: {e}")
        return None

import sqlite3
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite operations for the MEDEA census data scraper."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database with the necessary tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # We store the raw JSON response to avoid parsing issues early on
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS census_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tract_id TEXT NOT NULL,
                    variable_group TEXT NOT NULL,
                    raw_json TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tract_id, variable_group)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS medea_results (
                    tract_id TEXT PRIMARY KEY,
                    unemployment_pct REAL,
                    manual_pct REAL,
                    temporary_pct REAL,
                    education_pct REAL,
                    youth_education_pct REAL,
                    medea_score REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")

    def insert_data(self, tract_id: str, variable_group: str, data: Dict[str, Any]):
        """Insert or replace raw API response data for a tract and variable group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO census_data (tract_id, variable_group, raw_json)
                VALUES (?, ?, ?)
            """, (tract_id, variable_group, json.dumps(data)))
            conn.commit()

    def get_data(self, tract_id: str, variable_group: str) -> Optional[Dict[str, Any]]:
        """Retrieve raw API response data for a specific tract and variable group."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT raw_json FROM census_data
                WHERE tract_id = ? AND variable_group = ?
            """, (tract_id, variable_group))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

    def is_downloaded(self, tract_id: str, variable_group: str) -> bool:
        """Check if data for a tract and variable group is already downloaded."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 1 FROM census_data
                WHERE tract_id = ? AND variable_group = ?
            """, (tract_id, variable_group))
            return cursor.fetchone() is not None

    def insert_medea_results(self, tract_id: str, results: Dict[str, Any]):
        """Insert or replace MEDEA calculated percentages and score."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO medea_results 
                (tract_id, unemployment_pct, manual_pct, temporary_pct, education_pct, youth_education_pct, medea_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                tract_id,
                results.get('unemployment_pct'),
                results.get('manual_pct'),
                results.get('temporary_pct'),
                results.get('education_pct'),
                results.get('youth_education_pct'),
                results.get('medea_score')
            ))
            conn.commit()

    def get_medea_results(self, tract_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve MEDEA calculated results for a tract."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM medea_results WHERE tract_id = ?
            """, (tract_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

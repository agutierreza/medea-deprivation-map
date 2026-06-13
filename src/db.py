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

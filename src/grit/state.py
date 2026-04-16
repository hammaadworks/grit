import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_DIR = Path.home() / ".config" / "grit"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "state.db"


from grit.constants import MAX_DRAFT_HISTORY, YEAR_DAYS

class StateManager:
    """Manages local state using SQLite for the Grit CLI."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        with self._conn:
            self._conn.execute(
                '''
                                CREATE TABLE IF NOT EXISTS config (
                                    key TEXT PRIMARY KEY,
                                    value TEXT
                                )
                            '''
                )
            self._conn.execute(
                '''
                                CREATE TABLE IF NOT EXISTS commits (
                                    date TEXT PRIMARY KEY,
                                    count INTEGER
                                )
                            '''
                )
            self._conn.execute(
                '''
                                CREATE TABLE IF NOT EXISTS drafts (
                                    diff_hash TEXT PRIMARY KEY,
                                    message TEXT,
                                    status TEXT DEFAULT 'pending',
                                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                                )
                            '''
                )
            
            # Migration: Ensure 'status' column exists for existing databases
            cursor = self._conn.execute("PRAGMA table_info(drafts)")
            columns = [row[1] for row in cursor.fetchall()]
            if 'status' not in columns:
                self._conn.execute("ALTER TABLE drafts ADD COLUMN status TEXT DEFAULT 'success'")

    def get_draft(self, diff_hash: str) -> Optional[dict]:
        """Retrieve a cached commit draft for a specific diff."""
        cursor = self._conn.execute('SELECT message, status, timestamp FROM drafts WHERE diff_hash = ?', (diff_hash,))
        row = cursor.fetchone()
        if row:
            return {"message": row[0], "status": row[1], "timestamp": row[2]}
        return None

    def set_draft(self, diff_hash: str, message: str, status: str = "success"):
        """Cache a commit draft for a specific diff. Enforces a FIFO limit."""
        import datetime
        now_iso = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
        
        # 1. Identify which diff_hashes are about to be evicted
        cursor = self._conn.execute(
            f'''
            SELECT diff_hash FROM drafts 
            WHERE diff_hash NOT IN (
                SELECT diff_hash FROM drafts 
                ORDER BY timestamp DESC 
                LIMIT {MAX_DRAFT_HISTORY - 1}
            )
        '''
        )
        to_evict = [row[0] for row in cursor.fetchall()]

        with self._conn:
            # 2. Insert/Update the new draft
            self._conn.execute(
                '''
                                INSERT INTO drafts (diff_hash, message, status, timestamp)
                                VALUES (?, ?, ?, ?)
                                ON CONFLICT(diff_hash) DO UPDATE SET 
                                    message=excluded.message, 
                                    status=excluded.status,
                                    timestamp=excluded.timestamp
                            ''', (diff_hash, message, status, now_iso)
                )
            
            # 3. Enforce limit (FIFO)
            self._conn.execute(
                f'''
                DELETE FROM drafts 
                WHERE diff_hash NOT IN (
                    SELECT diff_hash FROM drafts 
                    ORDER BY timestamp DESC 
                    LIMIT {MAX_DRAFT_HISTORY}
                )
                '''
            )
        
        # 4. Cleanup associated log files for evicted drafts
        for h in to_evict:
            log_file = self.db_path.parent / f"ai_bg_{h}.log"
            try:
                log_file.unlink(missing_ok=True)
            except:
                raise

    def clear_old_drafts(self, hours: int = 24):
        """Cleanup old drafts to keep the DB lean."""
        with self._conn:
            self._conn.execute("DELETE FROM drafts WHERE timestamp < datetime('now', ?)", (f'-{hours} hours',))

    def get_config(self, key: str) -> Optional[str]:
        """Retrieve a configuration value by key."""
        cursor = self._conn.execute('SELECT value FROM config WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_synced_years(self) -> list[int]:
        """Returns a sorted list of years that have been fully synchronized."""
        years_str = self.get_config("synced_years")
        if not years_str:
            return []
        try:
            return sorted([int(y) for y in years_str.split(",") if y])
        except ValueError:
            return []

    def add_synced_year(self, year: int):
        """Marks a specific year as synchronized and safe for allocation."""
        years = set(self.get_synced_years())
        years.add(year)
        years_str = ",".join(map(str, sorted(years)))
        self.set_config("synced_years", years_str)

    def is_year_synced(self, year: int) -> bool:
        """Checks if a year is currently in the 'Safe Zone'."""
        return year in self.get_synced_years()

    def get_last_sync_time(self) -> float:
        """Returns the unix timestamp of the last successful GitHub sync."""
        val = self.get_config("last_github_sync_timestamp")
        return float(val) if val else 0.0

    def update_sync_timestamp(self):
        """Updates the sync timestamp to the current time."""
        import time

        self.set_config("last_github_sync_timestamp", str(time.time()))

    def set_config(self, key: str, value: str):
        """Set or update a configuration key."""
        with self._conn:
            self._conn.execute(
                '''
                                INSERT INTO config (key, value)
                                VALUES (?, ?)
                                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                            ''', (key, value)
                )

    def get_commit_count(self, date: str) -> int:
        """Get the commit count for a specific YYYY-MM-DD date."""
        cursor = self._conn.execute('SELECT count FROM commits WHERE date = ?', (date,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def set_commit_count(self, date: str, count: int):
        """Set or update the commit count for a specific date."""
        with self._conn:
            self._conn.execute(
                '''
                                INSERT INTO commits (date, count)
                                VALUES (?, ?)
                                ON CONFLICT(date) DO UPDATE SET count=excluded.count
                            ''', (date, count)
                )

    def increment_commit_count(self, date: str):
        """Atomically increments the commit count for a given date."""
        current_count = self.get_commit_count(date)
        self.set_commit_count(date, current_count + 1)

    def decrement_commit_count(self, date: str):
        """Safely decrements the commit count. Used for 'grit undo' operations."""
        current_count = self.get_commit_count(date)
        if current_count > 0:
            self.set_commit_count(date, current_count - 1)

    def get_history(self, days: int = YEAR_DAYS) -> list[dict]:
        """Fetch commit history for the last X days in a single efficient query."""
        from datetime import datetime, timedelta

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days - 1)

        start_date = start_dt.strftime("%Y-%m-%d")

        # This query gets all records since start_date.
        # Note: it doesn't fill gaps. We'll handle gaps in Python to keep it simple
        # and fast.
        cursor = self._conn.execute(
            "SELECT date, count FROM commits WHERE date >= ? ORDER BY date ASC",
            (start_date,)
        )
        data = {row[0]: row[1] for row in cursor.fetchall()}

        history = []
        for i in range(days):
            d = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            history.append(
                {
                    "date": d,
                    "count": data.get(d, 0)
                }
            )
        return history

    def get_monthly_commits(self, year_month: str) -> int:
        """Get the total commits for a YYYY-MM prefix."""
        cursor = self._conn.execute(
            "SELECT SUM(count) FROM commits WHERE date LIKE ?",
            (f"{year_month}-%",)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0

    def get_yearly_commits(self, year: int) -> int:
        """Get the total commits for a specific YYYY year."""
        cursor = self._conn.execute(
            "SELECT SUM(count) FROM commits WHERE date LIKE ?",
            (f"{year}-%",)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0

    def get_total_commits(self, start_date: str) -> int:
        """Get the total commits since a specific YYYY-MM-DD date."""
        cursor = self._conn.execute(
            "SELECT SUM(count) FROM commits WHERE date >= ?",
            (start_date,)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0

    def get_effective_commits(self, start_date: str, target: int) -> int:
        """
        Calculates 'Effective Commits' which is the sum of commits capped at the
        daily target.
        This represents how much of the 'Green Wall' is actually built.
        """
        # We use MIN(count, ?) to cap each day's contribution to the progress
        cursor = self._conn.execute(
            "SELECT SUM(MIN(count, ?)) FROM commits WHERE date >= ?",
            (target, start_date)
        )
        row = cursor.fetchone()
        return row[0] if row and row[0] else 0

    def close(self):
        """Closes the database connection."""
        self._conn.close()

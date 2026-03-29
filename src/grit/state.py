import sqlite3
from pathlib import Path
from typing import Optional

DEFAULT_DB_DIR = Path.home() / ".config" / "grit"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "state.db"

class StateManager:
    """Manages local state using SQLite for the Grit CLI."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS commits (
                    date TEXT PRIMARY KEY,
                    count INTEGER
                )
            ''')
            conn.commit()

    def get_config(self, key: str) -> Optional[str]:
        """Retrieve a configuration value by key."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT value FROM config WHERE key = ?', (key,))
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
        years_str = ",".join(map(str, sorted(list(years))))
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
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO config (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
            ''', (key, value))
            conn.commit()

    def get_commit_count(self, date: str) -> int:
        """Get the commit count for a specific YYYY-MM-DD date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT count FROM commits WHERE date = ?', (date,))
            row = cursor.fetchone()
            return row[0] if row else 0

    def set_commit_count(self, date: str, count: int):
        """Set or update the commit count for a specific date."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO commits (date, count)
                VALUES (?, ?)
                ON CONFLICT(date) DO UPDATE SET count=excluded.count
            ''', (date, count))
            conn.commit()

    def increment_commit_count(self, date: str):
        """Atomically increments the commit count for a given date."""
        current_count = self.get_commit_count(date)
        self.set_commit_count(date, current_count + 1)

    def decrement_commit_count(self, date: str):
        """Safely decrements the commit count. Used for 'grit undo' operations."""
        current_count = self.get_commit_count(date)
        if current_count > 0:
            self.set_commit_count(date, current_count - 1)

    def get_monthly_commits(self, year_month: str) -> int:
        """Get the total commits for a YYYY-MM prefix."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(count) FROM commits WHERE date LIKE ?", 
                (f"{year_month}-%",)
            )
            row = cursor.fetchone()
            return row[0] if row[0] else 0

    def get_yearly_commits(self, year: int) -> int:
        """Get the total commits for a specific YYYY year."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(count) FROM commits WHERE date LIKE ?", 
                (f"{year}-%",)
            )
            row = cursor.fetchone()
            return row[0] if row[0] else 0

    def get_total_commits(self, start_date: str) -> int:
        """Get the total commits since a specific YYYY-MM-DD date."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT SUM(count) FROM commits WHERE date >= ?", 
                (start_date,)
            )
            row = cursor.fetchone()
            return row[0] if row[0] else 0

    def get_effective_commits(self, start_date: str, target: int) -> int:
        """
        Calculates 'Effective Commits' which is the sum of commits capped at the daily target.
        This represents how much of the 'Green Wall' is actually built.
        """
        with sqlite3.connect(self.db_path) as conn:
            # We use MIN(count, ?) to cap each day's contribution to the progress
            cursor = conn.execute(
                "SELECT SUM(MIN(count, ?)) FROM commits WHERE date >= ?", 
                (target, start_date)
            )
            row = cursor.fetchone()
            return row[0] if row[0] else 0

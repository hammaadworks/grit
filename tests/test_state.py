import sqlite3
import pytest
from pathlib import Path
from grit.state import StateManager

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_state.db"
    manager = StateManager(db_path)
    yield manager
    manager.close()

def test_db_init(temp_db):
    """Test that the DB initializes correctly and creates the expected schemas."""
    # Check if file exists
    assert temp_db.db_path.exists()
    
    # Check tables
    with sqlite3.connect(temp_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        assert "config" in tables
        assert "commits" in tables

def test_db_upsert_count(temp_db):
    """Test upserting a commit count works and updates existing records."""
    temp_db.set_commit_count("2024-01-01", 3)
    
    with sqlite3.connect(temp_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM commits WHERE date='2024-01-01'")
        assert cursor.fetchone()[0] == 3
        
    # Test update
    temp_db.set_commit_count("2024-01-01", 5)
    with sqlite3.connect(temp_db.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT count FROM commits WHERE date='2024-01-01'")
        assert cursor.fetchone()[0] == 5

def test_synced_years(temp_db):
    """Test get_synced_years and add_synced_year."""
    assert temp_db.get_synced_years() == []
    
    temp_db.add_synced_year(2024)
    assert temp_db.get_synced_years() == [2024]
    assert temp_db.is_year_synced(2024)
    assert not temp_db.is_year_synced(2023)
    
    temp_db.add_synced_year(2023)
    assert temp_db.get_synced_years() == [2023, 2024]

def test_sync_timestamp(temp_db):
    """Test get_last_sync_time and update_sync_timestamp."""
    assert temp_db.get_last_sync_time() == 0.0
    
    temp_db.update_sync_timestamp()
    assert temp_db.get_last_sync_time() > 0.0

def test_increment_decrement(temp_db):
    """Test increment_commit_count and decrement_commit_count."""
    date = "2024-01-01"
    assert temp_db.get_commit_count(date) == 0
    
    temp_db.increment_commit_count(date)
    assert temp_db.get_commit_count(date) == 1
    
    temp_db.decrement_commit_count(date)
    assert temp_db.get_commit_count(date) == 0
    
    # Decrement at 0 should stay at 0
    temp_db.decrement_commit_count(date)
    assert temp_db.get_commit_count(date) == 0

def test_get_history(temp_db):
    """Test get_history method."""
    temp_db.set_commit_count("2024-01-01", 5)
    # get_history calculates from today, so let's mock/use current dates or just check it returns a list
    history = temp_db.get_history(days=7)
    assert len(history) == 7
    assert "date" in history[0]
    assert "count" in history[0]

def test_commit_aggregations(temp_db):
    """Test monthly, yearly, and total commit aggregations."""
    temp_db.set_commit_count("2024-01-01", 5)
    temp_db.set_commit_count("2024-01-02", 3)
    temp_db.set_commit_count("2024-02-01", 10)
    temp_db.set_commit_count("2023-12-31", 1)
    
    assert temp_db.get_monthly_commits("2024-01") == 8
    assert temp_db.get_yearly_commits(2024) == 18
    assert temp_db.get_total_commits("2024-01-01") == 18
    assert temp_db.get_total_commits("2023-01-01") == 19

def test_effective_commits(temp_db):
    """Test get_effective_commits with target capping."""
    temp_db.set_commit_count("2024-01-01", 10) # Over target
    temp_db.set_commit_count("2024-01-02", 2)  # Under target
    
    # Target 5: (min(10,5) + min(2,5)) = 5 + 2 = 7
    assert temp_db.get_effective_commits("2024-01-01", 5) == 7

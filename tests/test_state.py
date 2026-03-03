import sqlite3
import pytest
from pathlib import Path
from grit.state import StateManager

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_state.db"
    return StateManager(db_path)

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

def test_db_config_methods(temp_db):
    """Test getting and setting configuration."""
    assert temp_db.get_config("start_date") is None
    
    temp_db.set_config("start_date", "2024-01-01")
    assert temp_db.get_config("start_date") == "2024-01-01"
    
    # Test update
    temp_db.set_config("start_date", "2024-02-01")
    assert temp_db.get_config("start_date") == "2024-02-01"

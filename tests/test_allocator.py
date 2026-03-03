import pytest
import sqlite3
from datetime import datetime
from grit.state import StateManager
from grit.allocator import DateAllocator

@pytest.fixture
def db(tmp_path):
    state_db = StateManager(tmp_path / "state.db")
    # Setup standard config
    state_db.set_config("daily_target", "5")
    state_db.set_config("start_date", "2024-01-01")
    return state_db

def test_allocator_first_commit(db):
    """If today is empty, it should return today."""
    allocator = DateAllocator(db)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Empty DB, target=5, start=2024-01-01
    next_date = allocator.get_next_date()
    assert next_date == today

def test_allocator_forward_scan_memoization(db, mocker):
    """If today and all past dates are full, return tomorrow."""
    # Mock 'today' to be 2024-01-03
    mocker.patch('grit.allocator.get_today', return_value="2024-01-03")
    
    # Fill today and past dates
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 5)
    db.set_commit_count("2024-01-03", 5) # today is full
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Expected tomorrow
    assert next_date == "2024-01-04"

def test_allocator_config_change_invalidates_memo(db, mocker):
    """If target changes, previously full days are now available."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-03")
    
    # Fill up to 5
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 5)
    db.set_commit_count("2024-01-03", 5)
    
    # Change target to 10
    db.set_config("daily_target", "10")
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Today is now available again because it only has 5/10
    assert next_date == "2024-01-03"

def test_allocator_past_deficiency(db, mocker):
    """If today is full, it should scan back to find past deficiencies."""
    mocker.patch('grit.allocator.get_today', return_value="2024-01-04")
    
    db.set_config("start_date", "2024-01-01")
    
    # DB has 2024-01-01 (5), 2024-01-02 (2), 2024-01-03 (5), Today is full
    db.set_commit_count("2024-01-01", 5)
    db.set_commit_count("2024-01-02", 2)
    db.set_commit_count("2024-01-03", 5)
    db.set_commit_count("2024-01-04", 5) # Today is full
    
    allocator = DateAllocator(db)
    next_date = allocator.get_next_date()
    
    # Should return the first deficient date
    assert next_date == "2024-01-02"
